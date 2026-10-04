from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.routes.auth import get_current_user
from app.models.student import Student
from app.models.user import User
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate

router = APIRouter(prefix="/api/students", tags=["students"])


def _get_student(db: Session, student_pk: int) -> Student:
    student = db.get(Student, student_pk)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


def _check_unique_fields(
    db: Session,
    values: dict[str, object],
    *,
    exclude_id: int | None = None,
) -> None:
    unique_fields = ("student_id", "email", "qr_code", "rfid_tag")
    for field in unique_fields:
        value = values.get(field)
        if value is None:
            continue
        query = select(Student.id).where(getattr(Student, field) == value)
        if exclude_id is not None:
            query = query.where(Student.id != exclude_id)
        if db.scalar(query) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A student with this {field.replace('_', ' ')} already exists",
            )


@router.get("", response_model=list[StudentRead])
def list_students(
    search: str | None = Query(default=None, max_length=150),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Student]:
    query = select(Student).order_by(Student.full_name, Student.student_id)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Student.student_id.ilike(term),
                Student.full_name.ilike(term),
                Student.email.ilike(term),
                Student.program.ilike(term),
            )
        )
    return list(db.scalars(query).all())


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Student:
    values = payload.model_dump()
    _check_unique_fields(db, values)
    student = Student(**values)
    db.add(student)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with one of these identifiers already exists",
        ) from exc
    db.refresh(student)
    return student


@router.get("/{student_pk}", response_model=StudentRead)
def get_student(
    student_pk: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Student:
    return _get_student(db, student_pk)


@router.patch("/{student_pk}", response_model=StudentRead)
def update_student(
    student_pk: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Student:
    student = _get_student(db, student_pk)
    values = payload.model_dump(exclude_unset=True)
    _check_unique_fields(db, values, exclude_id=student.id)
    for field, value in values.items():
        setattr(student, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with one of these identifiers already exists",
        ) from exc
    db.refresh(student)
    return student
