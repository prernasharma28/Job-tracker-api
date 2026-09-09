from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .database import engine, Base
from .routers import applications, auth
from .exceptions import ApplicationNotFoundException

app = FastAPI(
    title="Job Tracker API",
    description="A REST API for managing job applications with authentication, filtering, search, sorting, pagination, statistics, and refresh token authentication.",
    version="1.0.0"
)

@app.exception_handler(ApplicationNotFoundException)
def application_not_found_exception_handler(request: Request, exc: ApplicationNotFoundException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Application not found",
            "status_code": 404
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