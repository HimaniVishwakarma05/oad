from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    CLOSED = "closed"


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[SessionStatus] = mapped_column(SqlEnum(SessionStatus), default=SessionStatus.SCHEDULED, nullable=False)
    qr_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="sessions")
    created_by_user: Mapped["User"] = relationship("User", back_populates="sessions")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        "AttendanceRecord",
        back_populates="session",
        cascade="all, delete-orphan",
    )
