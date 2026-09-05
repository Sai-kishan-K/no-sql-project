from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import (
    HTTPException as StarletteHTTPException,
)

from app.config import settings
from app.database import check_database_connection, database

from app.routes.analytics import router as analytics_router
from app.routes.events import router as events_router
from app.routes.users import router as users_router


BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    check_database_connection()
    print("Connected to MongoDB.")
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

app.include_router(events_router)
app.include_router(users_router)
app.include_router(analytics_router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    if exc.status_code == 404:
        heading = "Page not found"
        message = (
            "The requested page or database record "
            "could not be found."
        )
    else:
        heading = "Request error"
        message = str(exc.detail)

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "page_title": f"Error {exc.status_code}",
            "active_page": "",
            "status_code": exc.status_code,
            "heading": heading,
            "message": message,
        },
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    print(
        f"Unhandled application error: "
        f"{type(exc).__name__}: {exc}"
    )

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "page_title": "Server Error",
            "active_page": "",
            "status_code": 500,
            "heading": "Unexpected server error",
            "message": (
                "The application encountered an unexpected "
                "error. Please try again."
            ),
        },
        status_code=500,
    )


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    now = datetime.now(timezone.utc)

    total_users = database.users.count_documents({})
    total_events = database.events.count_documents({})
    upcoming_events_count = database.events.count_documents(
        {"startDate": {"$gt": now}}
    )
    past_events_count = database.events.count_documents(
        {"startDate": {"$lt": now}}
    )

    upcoming_events = list(
        database.events.find(
            {"startDate": {"$gt": now}},
            {
                "title": 1,
                "category": 1,
                "startDate": 1,
                "capacity": 1,
                "location": 1,
                "registrations": 1,
            },
        )
        .sort("startDate", 1)
        .limit(5)
    )

    for event in upcoming_events:
        event["registrationCount"] = len(
            event.get("registrations", [])
        )

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page_title": "Dashboard",
            "active_page": "dashboard",
            "total_users": total_users,
            "total_events": total_events,
            "upcoming_events_count": upcoming_events_count,
            "past_events_count": past_events_count,
            "upcoming_events": upcoming_events,
        },
    )


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
