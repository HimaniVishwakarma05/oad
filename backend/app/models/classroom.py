from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_code: Mapped[str] = mapped_column(String(50), nullable=False)
    course_name: Mapped[str] = mapped_column(String(150), nullable=False)
    section: Mapped[str | None] = mapped_column(String(50), nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String(30), nullable=True)
    semester: Mapped[str | None] = mapped_column(String(30), nullable=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    teacher: Mapped["User"] = relationship("User", back_populates="classrooms")
    sessions: Mapped[list["AttendanceSession"]] = relationship("AttendanceSession", back_populates="classroom")
