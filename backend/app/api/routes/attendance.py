import base64
import csv
from datetime import date, datetime, timedelta, timezone
from io import BytesIO, StringIO
from urllib.parse import quote
from uuid import uuid4

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from jose import JWTError, jwt
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.routes.auth import get_current_user
from app.core.config import settings
from app.models.attendance_record import AttendanceRecord, AttendanceStatus
from app.models.attendance_session import AttendanceSession, SessionStatus
from app.models.classroom import Classroom
from app.models.classroom_enrollment import ClassroomEnrollment
from app.models.session_roster import SessionRoster
from app.models.student import Student
from app.models.user import User
from app.schemas.qr_attendance import (
    AttendanceCheckInResult,
    AttendanceEntry,
    AttendanceReportEntry,
    AttendanceSessionCreate,
    AttendanceSessionDetail,
    AttendanceSessionSummary,
    StudentCheckIn,
)

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


def _attendance_report_rows(
    db: Session,
    teacher_id: int,
    classroom_id: int | None,
    date_from: date | None,
    date_to: date | None,
) -> list[AttendanceReportEntry]:
    query = (
        select(AttendanceRecord, Student, AttendanceSession, Classroom)
        .join(Student, AttendanceRecord.student_id == Student.id)
        .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)
        .join(Classroom, AttendanceSession.classroom_id == Classroom.id)
        .where(Classroom.teacher_id == teacher_id)
    )
    if classroom_id is not None:
        query = query.where(Classroom.id == classroom_id)
    if date_from is not None:
        query = query.where(AttendanceSession.session_date >= date_from)
    if date_to is not None:
        query = query.where(AttendanceSession.session_date <= date_to)
    query = query.order_by(
        AttendanceSession.session_date.desc(),
        AttendanceSession.start_time.desc(),
        Student.full_name,
    )

    return [
        AttendanceReportEntry(
            session_id=session.id,
            course_code=classroom.course_code,
            course_name=classroom.course_name,
            session_title=session.title,
            session_date=session.session_date,
            student_id=student.student_id,
            full_name=student.full_name,
            status=record.status,
            checked_in_at=record.checked_in_at,
        )
        for record, student, session, classroom in db.execute(query).all()
    ]


def _csv_cell(value: str) -> str:
    if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return f"'{value}"
    return value


def _get_owned_session(db: Session, session_id: int, teacher_id: int) -> AttendanceSession:
    session = db.get(AttendanceSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance session not found")
    classroom = db.get(Classroom, session.classroom_id)
    if classroom is None or classroom.teacher_id != teacher_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance session not found")
    return session


def _qr_image(check_in_url: str) -> str:
    image = qrcode.make(check_in_url)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _session_detail(
    db: Session,
    session: AttendanceSession,
    *,
    include_qr: bool = False,
) -> AttendanceSessionDetail:
    classroom = db.get(Classroom, session.classroom_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")

    present_count = db.scalar(
        select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.session_id == session.id,
            AttendanceRecord.status == AttendanceStatus.PRESENT,
        )
    ) or 0
    duration_minutes = 0
    if session.start_time and session.end_time:
        duration_minutes = max(0, int((session.end_time - session.start_time).total_seconds() // 60))

    check_in_url = None
    qr_image = None
    if include_qr and session.status == SessionStatus.ACTIVE and session.qr_code:
        check_in_url = f"{settings.frontend_url.rstrip('/')}/?checkin={quote(session.qr_code, safe='')}"
        qr_image = _qr_image(check_in_url)

    return AttendanceSessionDetail(
        id=session.id,
        classroom_id=session.classroom_id,
        classroom_name=f"{classroom.course_code} · {classroom.course_name}",
        title=session.title,
        session_date=session.session_date,
        start_time=session.start_time,
        end_time=session.end_time,
        status=session.status,
        duration_minutes=duration_minutes,
        present_count=present_count,
        check_in_url=check_in_url,
        qr_image=qr_image,
    )


def _is_expired(dt: datetime | None) -> bool:
    if dt is None:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= dt


def _expire_session_if_needed(db: Session, session: AttendanceSession) -> None:
    if (
        session.status == SessionStatus.ACTIVE
        and session.end_time is not None
        and _is_expired(session.end_time)
    ):
        _close_session_and_mark_absences(db, session)


def _close_session_and_mark_absences(db: Session, session: AttendanceSession) -> None:
    if session.status != SessionStatus.ACTIVE:
        return

    now = datetime.now(timezone.utc)
    session.status = SessionStatus.CLOSED
    session.qr_code = None
    if session.end_time is None or _is_expired(session.end_time):
        session.end_time = now

    enrolled_student_ids = db.scalars(
        select(SessionRoster.student_id).where(SessionRoster.session_id == session.id)
    ).all()
    existing_student_ids = set(
        db.scalars(
            select(AttendanceRecord.student_id).where(
                AttendanceRecord.session_id == session.id,
            )
        ).all()
    )
    for student_id in enrolled_student_ids:
        if student_id not in existing_student_ids:
            db.add(
                AttendanceRecord(
                    session_id=session.id,
                    student_id=student_id,
                    status=AttendanceStatus.ABSENT,
                    checked_in_at=None,
                    check_method="session_close",
                )
            )
    db.commit()


@router.get("/sessions", response_model=list[AttendanceSessionSummary])
def list_sessions(
    db: Session = Depends(get_db),
    teacher: User = Depends(get_current_user),
) -> list[AttendanceSessionDetail]:
    query = (
        select(AttendanceSession)
        .join(Classroom)
        .where(Classroom.teacher_id == teacher.id)
        .order_by(AttendanceSession.created_at.desc())
    )
    sessions = list(db.scalars(query).all())
    for session in sessions:
        _expire_session_if_needed(db, session)
    return [_session_detail(db, session) for session in sessions]


@router.post(
    "/sessions",
    response_model=AttendanceSessionDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    payload: AttendanceSessionCreate,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_current_user),
) -> AttendanceSessionDetail:
    classroom = db.get(Classroom, payload.classroom_id)
    if classroom is None or classroom.teacher_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")

    enrolled_student_ids = db.scalars(
        select(ClassroomEnrollment.student_id).where(
            ClassroomEnrollment.classroom_id == classroom.id,
            ClassroomEnrollment.is_active.is_(True),
        )
    ).all()
    if not enrolled_student_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Enroll at least one active student before starting attendance",
        )

    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(minutes=payload.duration_minutes)
    session = AttendanceSession(
        classroom_id=classroom.id,
        title=payload.title,
        session_date=date.today(),
        start_time=start_time,
        end_time=end_time,
        status=SessionStatus.ACTIVE,
        created_by=teacher.id,
    )
    db.add(session)
    db.flush()
    db.add_all(
        SessionRoster(session_id=session.id, student_id=student_id)
        for student_id in enrolled_student_ids
    )

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=payload.duration_minutes)
    session.qr_code = jwt.encode(
        {
            "sub": str(session.id),
            "purpose": "attendance_check_in",
            "jti": uuid4().hex,
            "exp": expires_at,
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create the attendance session",
        ) from exc
    db.refresh(session)
    return _session_detail(db, session, include_qr=True)


@router.get("/sessions/{session_id}", response_model=AttendanceSessionDetail)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_current_user),
) -> AttendanceSessionDetail:
    session = _get_owned_session(db, session_id, teacher.id)
    _expire_session_if_needed(db, session)
    return _session_detail(
        db,
        session,
        include_qr=session.status == SessionStatus.ACTIVE,
    )


@router.post("/sessions/{session_id}/close", response_model=AttendanceSessionDetail)
def close_session(
    session_id: int,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_current_user),
) -> AttendanceSessionDetail:
    session = _get_owned_session(db, session_id, teacher.id)
    if session.status == SessionStatus.ACTIVE:
        _close_session_and_mark_absences(db, session)
        db.refresh(session)
    return _session_detail(db, session)


@router.get("/sessions/{session_id}/records", response_model=list[AttendanceEntry])
def list_session_records(
    session_id: int,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_current_user),
) -> list[AttendanceEntry]:
    session = _get_owned_session(db, session_id, teacher.id)
    query = (
        select(Student, AttendanceRecord)
        .join(AttendanceRecord, AttendanceRecord.student_id == Student.id)
        .where(
            AttendanceRecord.session_id == session.id,
            AttendanceRecord.status == AttendanceStatus.PRESENT,
        )
        .order_by(AttendanceRecord.checked_in_at)
    )
    return [
        AttendanceEntry(
            student_id=student.student_id,
            full_name=student.full_name,
            checked_in_at=record.checked_in_at,
        )
        for student, record in db.execute(query).all()
        if record.checked_in_at is not None
    ]


@router.get("/reports", response_model=list[AttendanceReportEntry])
def get_attendance_report(
    classroom_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_current_user),
) -> list[AttendanceReportEntry]:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from must be on or before date_to",
        )
    active_sessions = db.scalars(
        select(AttendanceSession)
        .join(Classroom)
        .where(
            Classroom.teacher_id == teacher.id,
            AttendanceSession.status == SessionStatus.ACTIVE,
        )
    ).all()
    for session in active_sessions:
        _expire_session_if_needed(db, session)
    return _attendance_report_rows(db, teacher.id, classroom_id, date_from, date_to)


@router.get("/reports/export")
def export_attendance_report(
    classroom_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_current_user),
) -> Response:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from must be on or before date_to",
        )
    active_sessions = db.scalars(
        select(AttendanceSession)
        .join(Classroom)
        .where(
            Classroom.teacher_id == teacher.id,
            AttendanceSession.status == SessionStatus.ACTIVE,
        )
    ).all()
    for session in active_sessions:
        _expire_session_if_needed(db, session)

    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "Course code",
            "Course name",
            "Session",
            "Session date",
            "Student ID",
            "Student name",
            "Attendance status",
            "Checked in at (UTC)",
        ]
    )
    for entry in _attendance_report_rows(db, teacher.id, classroom_id, date_from, date_to):
        writer.writerow(
            [
                _csv_cell(entry.course_code),
                _csv_cell(entry.course_name),
                _csv_cell(entry.session_title),
                entry.session_date.isoformat(),
                _csv_cell(entry.student_id),
                _csv_cell(entry.full_name),
                entry.status,
                entry.checked_in_at.isoformat() if entry.checked_in_at else "",
            ]
        )

    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="attendance-report.csv"'},
    )


@router.post("/check-in", response_model=AttendanceCheckInResult)
def check_in_student(payload: StudentCheckIn, db: Session = Depends(get_db)) -> AttendanceCheckInResult:
    try:
        token_payload = jwt.decode(
            payload.session_token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if token_payload.get("purpose") != "attendance_check_in":
            raise ValueError("Wrong token purpose")
        session_id = int(token_payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This attendance QR code is invalid or expired",
        ) from exc

    session = db.get(AttendanceSession, session_id)
    if (
        session is None
        or session.status != SessionStatus.ACTIVE
        or session.qr_code != payload.session_token
    ):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This attendance session is closed or expired",
        )
    if session.end_time is not None and _is_expired(session.end_time):
        session.status = SessionStatus.CLOSED
        session.qr_code = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This attendance session is closed or expired",
        )

    student = db.scalar(
        select(Student).where(
            func.lower(Student.student_id) == payload.student_id.lower(),
            Student.is_active.is_(True),
        )
    )
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active student matches that student ID",
        )

    roster_entry = db.scalar(
        select(SessionRoster.id).where(
            SessionRoster.session_id == session.id,
            SessionRoster.student_id == student.id,
        )
    )
    if roster_entry is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This student was not enrolled when the attendance session started",
        )

    existing = db.scalar(
        select(AttendanceRecord.id).where(
            AttendanceRecord.session_id == session.id,
            AttendanceRecord.student_id == student.id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance has already been recorded for this student",
        )

    checked_in_at = datetime.now(timezone.utc)
    record = AttendanceRecord(
        session_id=session.id,
        student_id=student.id,
        status=AttendanceStatus.PRESENT,
        checked_in_at=checked_in_at,
        check_method="session_qr",
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance has already been recorded for this student",
        ) from exc

    classroom = db.get(Classroom, session.classroom_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    return AttendanceCheckInResult(
        message="Attendance recorded successfully",
        student_name=student.full_name,
        course_name=classroom.course_name,
        session_title=session.title,
        checked_in_at=checked_in_at,
    )
