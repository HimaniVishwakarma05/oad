from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SessionRoster(Base):
    __tablename__ = "attendance_session_roster"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_session_roster_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("attendance_sessions.id"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
