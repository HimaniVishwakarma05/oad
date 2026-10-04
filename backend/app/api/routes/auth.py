from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import AccessToken, LoginRequest, TeacherSetup
from app.schemas.user import UserRead

router = APIRouter(prefix="/api/auth", tags=["authentication"])
bearer_scheme = HTTPBearer(auto_error=False)


def _create_access_token(user: User) -> AccessToken:
    expires_in = settings.access_token_expire_minutes * 60
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    token = jwt.encode(
        {"sub": str(user.id), "exp": expires_at},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return AccessToken(access_token=token, expires_in=expires_in, user=user)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        subject = payload.get("sub")
        if not subject:
            raise unauthorized
        user_id = int(subject)
    except (JWTError, TypeError, ValueError) as exc:
        raise unauthorized from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


@router.get("/setup-status")
def setup_status(db: Session = Depends(get_db)) -> dict[str, bool]:
    user_exists = db.scalar(select(User.id).limit(1)) is not None
    return {"setup_required": not user_exists}


@router.post("/setup", response_model=AccessToken, status_code=status.HTTP_201_CREATED)
def setup_first_teacher(payload: TeacherSetup, db: Session = Depends(get_db)) -> AccessToken:
    if db.scalar(select(User.id).limit(1)) is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Initial teacher setup is already complete",
        )

    user = User(
        full_name=payload.full_name,
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        role=UserRole.TEACHER,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A teacher account with this email already exists",
        ) from exc
    db.refresh(user)
    return _create_access_token(user)


@router.post("/login", response_model=AccessToken)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AccessToken:
    user = db.scalar(select(User).where(func.lower(User.email) == str(payload.email).lower()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _create_access_token(user)


@router.get("/me", response_model=UserRead)
def read_current_user(user: User = Depends(get_current_user)) -> User:
    return user
