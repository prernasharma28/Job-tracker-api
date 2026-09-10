from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .database import engine, Base
from .routers import applications, auth
from .exceptions import ApplicationNotFoundException

import logging
import time
from app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Job Tracker API",
    description="A REST API for managing job applications with authentication, filtering, search, sorting, pagination, statistics, and refresh token authentication.",
    version="1.0.0"
)

logger.info("Job Tracker API started")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()

    logger.info(
        "Request: %s %s",
        request.method,
        request.url.path,
    )

    response = await call_next(request)

    process_time = (time.perf_counter() - start_time) * 1000

    logger.info(
        "Response: %s %s %s - %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
    )

    return response


@app.exception_handler(ApplicationNotFoundException)
def application_not_found_exception_handler(
    request: Request,
    exc: ApplicationNotFoundException
):
    logger.warning(
        "Application not found: %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=404,
        content={
            "error": "Application not found",
            "status_code": 404
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unexpected error while processing request: %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )

Base.metadata.create_all(bind=engine)

app.include_router(applications.router)
app.include_router(auth.router)


@app.get("/")
def home():
    return {"message": "Hello, World!"}


@app.get("/about")
def about():
    return {"message": "This is my Job Tracker API"}