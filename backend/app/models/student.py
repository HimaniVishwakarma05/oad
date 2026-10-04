from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(150), unique=True, index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    program: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year: Mapped[str | None] = mapped_column(String(30), nullable=True)
    qr_code: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    rfid_tag: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        "AttendanceRecord",
        back_populates="student",
    )
