from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate
from app.schemas.classroom import ClassroomCreate, ClassroomRead, ClassroomUpdate
from app.schemas.attendance_session import AttendanceSessionCreate, AttendanceSessionRead, AttendanceSessionUpdate
from app.schemas.attendance_record import AttendanceRecordCreate, AttendanceRecordRead, AttendanceRecordUpdate

__all__ = [
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "StudentCreate",
    "StudentRead",
    "StudentUpdate",
    "ClassroomCreate",
    "ClassroomRead",
    "ClassroomUpdate",
    "AttendanceSessionCreate",
    "AttendanceSessionRead",
    "AttendanceSessionUpdate",
    "AttendanceRecordCreate",
    "AttendanceRecordRead",
    "AttendanceRecordUpdate",
]
