from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class StudentBase(BaseModel):
    student_id: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    program: str | None = Field(default=None, max_length=100)
    year: str | None = Field(default=None, max_length=30)
    qr_code: str | None = Field(default=None, max_length=255)
    rfid_tag: str | None = Field(default=None, max_length=100)
    is_active: bool = True

    @field_validator("student_id", "full_name", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip().lower()
            return value or None
        return value


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    student_id: str | None = Field(default=None, min_length=3, max_length=50)
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    program: str | None = Field(default=None, max_length=100)
    year: str | None = Field(default=None, max_length=30)
    qr_code: str | None = Field(default=None, max_length=255)
    rfid_tag: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None

    @field_validator("student_id", "full_name", mode="before")
    @classmethod
    def strip_optional_required_text(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("This field cannot be null")
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_optional_email(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip().lower()
            return value or None
        return value


class StudentRead(StudentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
