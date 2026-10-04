from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models.attendance_record import AttendanceStatus
from app.models.attendance_session import SessionStatus


class AttendanceSessionCreate(BaseModel):
    classroom_id: int
    title: str = Field(min_length=2, max_length=150)
    duration_minutes: int = Field(default=90, ge=1, le=360)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class AttendanceSessionSummary(BaseModel):
    id: int
    classroom_id: int
    classroom_name: str
    title: str
    session_date: date
    start_time: datetime | None
    end_time: datetime | None
    status: SessionStatus
    duration_minutes: int
    present_count: int


class AttendanceSessionDetail(AttendanceSessionSummary):
    check_in_url: str | None = None
    qr_image: str | None = None


class StudentCheckIn(BaseModel):
    student_id: str = Field(min_length=3, max_length=50)
    session_token: str = Field(min_length=20, max_length=512)

    @field_validator("student_id", mode="before")
    @classmethod
    def strip_student_id(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class AttendanceCheckInResult(BaseModel):
    message: str
    student_name: str
    course_name: str
    session_title: str
    checked_in_at: datetime


class AttendanceEntry(BaseModel):
    student_id: str
    full_name: str
    checked_in_at: datetime


class AttendanceReportEntry(BaseModel):
    session_id: int
    course_code: str
    course_name: str
    session_title: str
    session_date: date
    student_id: str
    full_name: str
    status: AttendanceStatus
    checked_in_at: datetime | None
