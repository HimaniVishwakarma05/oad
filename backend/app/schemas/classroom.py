from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClassroomBase(BaseModel):
    course_code: str = Field(..., min_length=2, max_length=50)
    course_name: str = Field(..., min_length=2, max_length=150)
    section: str | None = Field(default=None, max_length=50)
    academic_year: str | None = Field(default=None, max_length=30)
    semester: str | None = Field(default=None, max_length=30)


class ClassroomCreate(ClassroomBase):
    teacher_id: int


class ClassroomCreateForTeacher(ClassroomBase):
    pass


class ClassroomUpdate(BaseModel):
    course_code: str | None = Field(default=None, min_length=2, max_length=50)
    course_name: str | None = Field(default=None, min_length=2, max_length=150)
    section: str | None = Field(default=None, max_length=50)
    academic_year: str | None = Field(default=None, max_length=30)
    semester: str | None = Field(default=None, max_length=30)
    teacher_id: int | None = None


class ClassroomRead(ClassroomBase):
    id: int
    teacher_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassroomEnrollmentCreate(BaseModel):
    student_pk: int = Field(ge=1)


class ClassroomEnrollmentRead(BaseModel):
    student_pk: int
    student_id: str
    full_name: str
    enrolled_at: datetime
