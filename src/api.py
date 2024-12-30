import csv
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pycountry import countries
from pydantic import ValidationError
from sqlmodel import Session as SQLModelSession
from sqlmodel import SQLModel

from .config import DATABASE, ENVIRONMENT, LOG_FORMAT, LOG_LEVEL, PROJECT_NAME
from .database import engine
from .reviewers.models import Reviewer, ReviewerCreate
from .reviewers.router import router as reviewers_router
from .reviews.models import Review, ReviewCreate
from .reviews.router import router as reviews_router

log = logging.getLogger(__name__)

console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logging.basicConfig(level=LOG_LEVEL, handlers=[console_handler])

# region Data Ingestion
# Configure countries
countries.add_entry(
    alt_code="UK",
    alpha_2="GB",
    alpha_3="GBR",
    flag="🇬🇧",
    name="United Kingdom",
    numeric="826",
    official_name="United Kingdom of Great Britain and Northern Ireland",
)


def get_iso_country_code(country: str) -> str:
    matched_country = countries.search_fuzzy(country)[0]
    return matched_country.alpha_3


def ingest_csv(file_path: str):
    with SQLModelSession(engine) as session:
        with open(file_path, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                reviewer_country = get_iso_country_code(row["Country"])
                # If invalid email (or other reviewer vaildation issue) skip record
                try:
                    reviewer = ReviewerCreate(
                        email=row["Email Address"],
                        name=row["Reviewer Name"],
                        country=reviewer_country,
                    )
                    db_reviewer = Reviewer.model_validate(
                        {
                            **reviewer.model_dump(),
                            "created_at": None,
                        }
                    )
                except ValidationError:
                    continue
                session.add(db_reviewer)
                session.commit()
                session.refresh(db_reviewer)

                review = ReviewCreate(
                    reviewer_id=db_reviewer.id,
                    title=row["Review Title"],
                    rating=int(row["Review Rating"]),
                    content=row["Review Content"],
                )
                db_review = Review.model_validate(
                    {
                        **review.model_dump(),
                        "created_at": datetime.strptime(row["Review Date"], "%Y-%m-%d"),
                    }
                )
                session.add(db_review)
                # session.commit()
            session.commit()


# endregion


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DATABASE.is_file():
        log.info("Database file doesn't exist")
        SQLModel.metadata.create_all(engine)
        log.info("Created Database")
        ingest_csv("./data/dataops_tp_reviews.csv")
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
