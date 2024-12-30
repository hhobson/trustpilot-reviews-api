import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlmodel import SQLModel

from .config import DATABASE, ENVIRONMENT, LOG_FORMAT, LOG_LEVEL, PROJECT_NAME
from .database import engine
from .ingest import populate_database_from_csv
from .reviewers.router import router as reviewers_router
from .reviews.router import router as reviews_router

log = logging.getLogger(__name__)

console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logging.basicConfig(level=LOG_LEVEL, handlers=[console_handler])

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DATABASE.is_file():
        log.info("Database file doesn't exist")
        SQLModel.metadata.create_all(engine)
        log.info("Created Database")
        populate_database_from_csv("./data/dataops_tp_reviews.csv")
    yield


# FastAPI application
app = FastAPI(
    title=f"{PROJECT_NAME}-{ENVIRONMENT}",
    root_path="/api/v1",
    lifespan=lifespan,
)

app.include_router(reviewers_router)
app.include_router(reviews_router)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()[0]},
    )
