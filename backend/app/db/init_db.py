from app.db.database import Base, engine
from app.models import (
    AttendanceRecord,
    AttendanceSession,
    Classroom,
    ClassroomEnrollment,
    SessionRoster,
    Student,
    User,
)


def init_db() -> None:
    """Create all database tables for the attendance system."""
    Base.metadata.create_all(bind=engine)
