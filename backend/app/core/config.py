from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "IIPS Smart Classroom Attendance Management System"
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    frontend_url: str = "http://localhost:5173"
    database_url: str = f"sqlite:///{(BASE_DIR / 'iips_attendance.db').as_posix()}"
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "iips_attendance"
    db_user: str = "root"
    db_password: str = "your_mysql_password"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
