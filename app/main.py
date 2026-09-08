from fastapi import FastAPI

from .database import engine, Base
from .routers import applications, auth


app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(applications.router)
app.include_router(auth.router)


@app.get("/")
def home():
    return {"message": "Hello, World!"}


@app.get("/about")
def about():
    return {"message": "This is my Job Tracker API"}