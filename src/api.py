"""
### An API enabling CRUD operations on Reviews and Review Authors

![Review time](https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExZmx4MmxpNnlrM3Q0b3VydXZwaTRqbXh0YXhqcXBjaGtibngwYWk4YiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o6Mbeu0pK5JkphN84/giphy.gif)
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlmodel import SQLModel, inspect

from .config import DATABASE, ENVIRONMENT, LOG_FORMAT, LOG_LEVEL, PROJECT_NAME
from .database import engine
from .ingest import load_database_from_csv
from .reviewers.router import router as reviewers_router
from .reviews.router import router as reviews_router

log = logging.getLogger(__name__)

console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logging.basicConfig(level=LOG_LEVEL, handlers=[console_handler])


@asynccontextmanager
async def lifespan(app: FastAPI):
    table_names = inspect(engine).get_table_names()
    if not table_names:
        log.info("Creating Database tables")
        SQLModel.metadata.create_all(engine)
        log.info("Created Database tables")

        load_database_from_csv("./data/dataops_tp_reviews.csv")
    else:
        log.info("Database tables already exist")

    yield


# FastAPI application
app = FastAPI(
    title=f"{PROJECT_NAME}-{ENVIRONMENT}",
    description=__doc__,
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
