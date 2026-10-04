from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.attendance import router as attendance_router
from app.api.routes.classrooms import router as classrooms_router
from app.api.routes.students import router as students_router
from app.core.config import settings
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env.lower() == "production" and settings.secret_key == "change-me-in-production":
        raise RuntimeError("Set a strong SECRET_KEY before running in production")
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Attendance management API for IIPS Smart Classroom Attendance System.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(students_router)
app.include_router(auth_router)
app.include_router(classrooms_router)
app.include_router(attendance_router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "app": settings.app_name, "environment": settings.app_env}


@app.get("/")
def root() -> dict:
    return {"message": "IIPS Smart Classroom Attendance Management System API"}
