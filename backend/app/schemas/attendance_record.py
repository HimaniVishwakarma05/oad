from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.attendance_record import AttendanceStatus


class AttendanceRecordBase(BaseModel):
    status: AttendanceStatus = AttendanceStatus.ABSENT
    checked_in_at: datetime | None = None
    check_method: str | None = Field(default=None, max_length=30)
    notes: str | None = Field(default=None, max_length=255)


class AttendanceRecordCreate(AttendanceRecordBase):
    session_id: int
    student_id: int


class AttendanceRecordUpdate(BaseModel):
    status: AttendanceStatus | None = None
    checked_in_at: datetime | None = None
    check_method: str | None = Field(default=None, max_length=30)
    notes: str | None = Field(default=None, max_length=255)


class AttendanceRecordRead(AttendanceRecordBase):
    id: int
    session_id: int
    student_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
