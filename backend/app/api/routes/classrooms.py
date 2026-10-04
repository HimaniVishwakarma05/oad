from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.routes.auth import get_current_user
from app.models.classroom import Classroom
from app.models.classroom_enrollment import ClassroomEnrollment
from app.models.student import Student
from app.models.user import User
from app.schemas.classroom import (
    ClassroomCreateForTeacher,
    ClassroomEnrollmentCreate,
    ClassroomEnrollmentRead,
    ClassroomRead,
)

router = APIRouter(prefix="/api/classrooms", tags=["classrooms"])


def _get_owned_classroom(db: Session, classroom_id: int, teacher_id: int) -> Classroom:
    classroom = db.get(Classroom, classroom_id)
    if classroom is None or classroom.teacher_id != teacher_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    return classroom


def _enrollment_read(enrollment: ClassroomEnrollment, student: Student) -> ClassroomEnrollmentRead:
    return ClassroomEnrollmentRead(
        student_pk=student.id,
        student_id=student.student_id,
        full_name=student.full_name,
        enrolled_at=enrollment.enrolled_at,
    )


@router.get("", response_model=list[ClassroomRead])
def list_classrooms(
    db: Session = Depends(get_db),
    teacher: User = Depends(get_current_user),
) -> list[Classroom]:
    query = (
        select(Classroom)
        .where(Classroom.teacher_id == teacher.id)
        .order_by(Classroom.course_code, Classroom.section)
    )
    return list(db.scalars(query).all())


@router.post("", response_model=ClassroomRead, status_code=status.HTTP_201_CREATED)
def create_classroom(
    payload: ClassroomCreateForTeacher,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_current_user),
) -> Classroom:
    classroom = Classroom(**payload.model_dump(), teacher_id=teacher.id)
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


@router.get(
    "/{classroom_id}/enrollments",
    response_model=list[ClassroomEnrollmentRead],
)
def list_enrollments(
    classroom_id: int,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_current_user),
) -> list[ClassroomEnrollmentRead]:
    _get_owned_classroom(db, classroom_id, teacher.id)
    query = (
        select(ClassroomEnrollment, Student)
        .join(Student, Student.id == ClassroomEnrollment.student_id)
        .where(
            ClassroomEnrollment.classroom_id == classroom_id,
            ClassroomEnrollment.is_active.is_(True),
        )
        .order_by(Student.full_name, Student.student_id)
    )
    return [
        _enrollment_read(enrollment, student)
        for enrollment, student in db.execute(query).all()
    ]


@router.post(
    "/{classroom_id}/enrollments",
    response_model=ClassroomEnrollmentRead,
    status_code=status.HTTP_201_CREATED,
)
def enroll_student(
    classroom_id: int,
    payload: ClassroomEnrollmentCreate,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_current_user),
) -> ClassroomEnrollmentRead:
    _get_owned_classroom(db, classroom_id, teacher.id)
    student = db.get(Student, payload.student_pk)
    if student is None or not student.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active student not found")

    enrollment = db.scalar(
        select(ClassroomEnrollment).where(
            ClassroomEnrollment.classroom_id == classroom_id,
            ClassroomEnrollment.student_id == student.id,
        )
    )
    if enrollment is None:
        enrollment = ClassroomEnrollment(
            classroom_id=classroom_id,
            student_id=student.id,
            is_active=True,
        )
        db.add(enrollment)
    elif enrollment.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already enrolled in this classroom",
        )
    else:
        enrollment.is_active = True
        enrollment.enrolled_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already enrolled in this classroom",
        ) from exc
    db.refresh(enrollment)
    return _enrollment_read(enrollment, student)


@router.delete("/{classroom_id}/enrollments/{student_pk}", status_code=status.HTTP_204_NO_CONTENT)
def unenroll_student(
    classroom_id: int,
    student_pk: int,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_current_user),
) -> Response:
    _get_owned_classroom(db, classroom_id, teacher.id)
    enrollment = db.scalar(
        select(ClassroomEnrollment).where(
            ClassroomEnrollment.classroom_id == classroom_id,
            ClassroomEnrollment.student_id == student_pk,
            ClassroomEnrollment.is_active.is_(True),
        )
    )
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active enrollment not found")
    enrollment.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
