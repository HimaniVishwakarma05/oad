from getpass import getpass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.user import User, UserRole


def update_teacher_password(db: Session, email: str, password: str) -> bool:
    teacher = db.scalar(
        select(User).where(
            User.email == email.strip().lower(),
            User.role == UserRole.TEACHER,
        )
    )
    if teacher is None:
        return False

    teacher.password_hash = hash_password(password)
    db.commit()
    return True


def main() -> int:
    with SessionLocal() as db:
        teachers = list(
            db.scalars(
                select(User)
                .where(User.role == UserRole.TEACHER)
                .order_by(User.email)
            ).all()
        )
        if not teachers:
            print("No teacher accounts were found.")
            return 1

        print("Teacher accounts:")
        for teacher in teachers:
            state = "active" if teacher.is_active else "inactive"
            print(f"- {teacher.email} ({state})")

        email = input("Email of the teacher account to reset: ").strip().lower()
        teacher = db.scalar(
            select(User).where(
                User.email == email,
                User.role == UserRole.TEACHER,
            )
        )
        if teacher is None:
            print("No teacher account matches that email.")
            return 1

        confirmation = input(f"Type {teacher.email} to confirm the reset: ").strip().lower()
        if confirmation != teacher.email.lower():
            print("Confirmation did not match. Password was not changed.")
            return 1

        password = getpass("New password (at least 12 characters): ")
        if len(password) < 12 or len(password.encode("utf-8")) > 72:
            print("Password must be at least 12 characters and no more than 72 UTF-8 bytes.")
            return 1
        if password != getpass("Confirm new password: "):
            print("Passwords did not match. Password was not changed.")
            return 1

        update_teacher_password(db, teacher.email, password)
        print("Teacher password updated.")
        print("Existing access tokens remain valid until they expire.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
