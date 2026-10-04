from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserRead


class TeacherSetup(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr = Field(max_length=150)
    password: str = Field(min_length=12, max_length=72)

    @field_validator("full_name", mode="before")
    @classmethod
    def strip_full_name(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("password")
    @classmethod
    def limit_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be no more than 72 UTF-8 bytes")
        return value


class LoginRequest(BaseModel):
    email: EmailStr = Field(max_length=150)
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("password")
    @classmethod
    def limit_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be no more than 72 UTF-8 bytes")
        return value


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
