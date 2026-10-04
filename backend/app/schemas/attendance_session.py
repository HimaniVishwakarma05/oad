from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.attendance_session import SessionStatus


class AttendanceSessionBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    session_date: date
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: SessionStatus = SessionStatus.SCHEDULED
    qr_code: str | None = Field(default=None, max_length=255)


class AttendanceSessionCreate(AttendanceSessionBase):
    classroom_id: int
    created_by: int


class AttendanceSessionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    session_date: date | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: SessionStatus | None = None
    qr_code: str | None = Field(default=None, max_length=255)
    classroom_id: int | None = None
    created_by: int | None = None


class AttendanceSessionRead(AttendanceSessionBase):
    id: int
    classroom_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
