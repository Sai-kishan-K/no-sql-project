from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.config import settings
from app.database import check_database_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    check_database_connection()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {
        "application": settings.app_name,
        "message": "Campus Events Manager API is running",
    }


@app.get("/health")
def health_check():
    try:
        check_database_connection()
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB connection failed",
        ) from exc