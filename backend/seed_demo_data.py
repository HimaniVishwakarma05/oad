"""Add repeatable, clearly labeled demo students and a demo classroom."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.database import SessionLocal
from app.models.classroom import Classroom
from app.models.classroom_enrollment import ClassroomEnrollment
from app.models.student import Student
from app.models.user import User, UserRole

DEMO_CLASSROOM = {
    "course_code": "DEMO101",
    "course_name": "Attendance Demo Lab",
    "section": "DEMO",
    "academic_year": "2026-2027",
    "semester": "Demo",
}
DEMO_STUDENTS = (
    {
        "student_id": "DEMO001",
        "full_name": "Demo Student One",
        "email": "demo001@example.com",
        "program": "MCA (Demo)",
        "year": "Demo",
    },
    {
        "student_id": "DEMO002",
        "full_name": "Demo Student Two",
        "email": "demo002@example.com",
        "program": "MCA (Demo)",
        "year": "Demo",
    },
    {
        "student_id": "DEMO003",
        "full_name": "Demo Student Three",
        "email": "demo003@example.com",
        "program": "MCA (Demo)",
        "year": "Demo",
    },
)


def seed_demo_data() -> None:
    with SessionLocal() as db:
        teachers = list(
            db.scalars(
                select(User).where(
                    User.is_active.is_(True),
                    User.role == UserRole.TEACHER,
                )
            ).all()
        )
        if len(teachers) != 1:
            raise RuntimeError(
                f"Expected exactly one active teacher account; found {len(teachers)}. "
                "Refusing to guess which account should own the demo classroom."
            )
        teacher = teachers[0]

        classroom_matches = list(
            db.scalars(
                select(Classroom).where(
                    Classroom.teacher_id == teacher.id,
                    Classroom.course_code == DEMO_CLASSROOM["course_code"],
                )
            ).all()
        )
        if len(classroom_matches) > 1:
            raise RuntimeError("Multiple DEMO101 classrooms exist; refusing to modify data.")
        classroom = classroom_matches[0] if classroom_matches else None
        if classroom is None:
            classroom = Classroom(**DEMO_CLASSROOM, teacher_id=teacher.id)
            db.add(classroom)
            db.flush()
            print(f"Created demo classroom {DEMO_CLASSROOM['course_code']}.")
        elif any(
            getattr(classroom, field) != value
            for field, value in DEMO_CLASSROOM.items()
        ):
            raise RuntimeError(
                "A non-demo classroom already uses DEMO101; refusing to change it."
            )
        else:
            print(f"Demo classroom {DEMO_CLASSROOM['course_code']} already exists.")

        for data in DEMO_STUDENTS:
            student = db.scalar(
                select(Student).where(Student.student_id == data["student_id"])
            )
            if student is None:
                email_owner = db.scalar(
                    select(Student).where(Student.email == data["email"])
                )
                if email_owner is not None:
                    raise RuntimeError(
                        f"{data['email']} is already used by another student; "
                        "refusing to modify that account."
                    )
                student = Student(**data, is_active=True)
                db.add(student)
                db.flush()
                print(f"Created active demo student {data['student_id']}.")
            elif (
                student.full_name != data["full_name"]
                or student.email not in (data["email"], f"{data['student_id'].lower()}@example.test")
                or student.program != data["program"]
                or student.year != data["year"]
                or not student.is_active
            ):
                raise RuntimeError(
                    f"Student ID {data['student_id']} already exists but does not match "
                    "the active demo record; refusing to change it."
                )
            else:
                if student.email != data["email"]:
                    student.email = data["email"]
                    print(f"Updated the demo-only email for {data['student_id']}.")
                print(f"Demo student {data['student_id']} already exists.")

            enrollment = db.scalar(
                select(ClassroomEnrollment).where(
                    ClassroomEnrollment.classroom_id == classroom.id,
                    ClassroomEnrollment.student_id == student.id,
                )
            )
            if enrollment is None:
                db.add(
                    ClassroomEnrollment(
                        classroom_id=classroom.id,
                        student_id=student.id,
                        is_active=True,
                    )
                )
                print(f"Enrolled {data['student_id']} in {DEMO_CLASSROOM['course_code']}.")
            elif not enrollment.is_active:
                raise RuntimeError(
                    f"{data['student_id']} is currently unenrolled from "
                    f"{DEMO_CLASSROOM['course_code']}; refusing to change that."
                )
            else:
                print(f"{data['student_id']} is already enrolled.")

        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise RuntimeError(
                "Could not add the demo records because of a database uniqueness conflict."
            ) from exc

    print(
        "Demo data is ready. Students: DEMO001, DEMO002, DEMO003. "
        "These records are sample data and must not be used for real attendance."
    )


if __name__ == "__main__":
    seed_demo_data()
