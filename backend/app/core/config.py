from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # App Settings
    app_name: str = "IIPS Smart Classroom Attendance Management System"
    app_env: str = "development"
    secret_key: str = "change-this-secret-key-to-a-strong-random-value-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # Low Attendance Alert Threshold (Percentage)
    low_attendance_threshold: float = 70.0
    
    # CORS & Frontend URLs
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://10.230.86.249:5173"
    frontend_url: str = "http://10.230.86.249:5173"
    
    # Database Configuration (Defaults to SQLite for local development; MySQL compatible)
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

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
