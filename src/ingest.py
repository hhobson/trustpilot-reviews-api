import csv
import logging
from datetime import datetime

import sqlalchemy
from pycountry import countries
from pydantic import ValidationError

# from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from .database import SessionLocal
from .reviewers.models import Reviewer, ReviewerCreate
from .reviews.models import Review, ReviewCreate

log = logging.getLogger(__name__)

# Add "UK" as an alternative code for United Kingdom
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
    """Get ISO-3166 three-letter country code for a country

    Uses a fuzzy matched approach, so can accept a country name, two or three letter code
    """
    matched_country = countries.search_fuzzy(country)[0]
    return matched_country.alpha_3


def populate_database_from_csv(file_path: str):
    with SessionLocal() as session:
        log.info(f"Loading data from csv {file_path}")
        with open(file_path, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row_no, row in enumerate(reader):
                iso_country_code = get_iso_country_code(row["Country"])
                try:
                    reviewer = ReviewerCreate(
                        email=row["Email Address"],
                        name=row["Reviewer Name"],
                        country=iso_country_code,
                    )
                    db_reviewer = Reviewer.model_validate(
                        {
                            **reviewer.model_dump(),
                            "created_at": None,  # CSV doesn't have a reviewer created value
                        }
                    )
                    session.add(db_reviewer)
                    session.commit()
                except ValidationError as err:
                    # If invalid reviewer then skip record
                    log.warning(f"Reviewer Validation error on row {row_no}: {err}")
                    log.warning(f"Invalid Reviewer data, skipping row {row_no}")
                    continue
                # except IntegrityError:
                except sqlalchemy.exc.IntegrityError:
                    # If reviewer already exists in database then continue using existing reviewer record
                    log.warning(f"Reviewer from row {row_no} already exists")
                    log.info("Continuing to load review with existing reviewer")
                    session.rollback()
                    reviewer_id = session.exec(select(Reviewer.id).where(Reviewer.email == row["Email Address"])).first()
                    db_reviewer = session.get(Reviewer, reviewer_id)
                else:
                    session.refresh(db_reviewer)


                try:
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
                except ValidationError as err:
                    # If invalid review then skip review
                    log.warning(f"Review Validation error on row {row}: {err}")
                    log.warning(f"Invalid Review data, skipping review from row {row_no}")
                    continue
                session.add(db_review)
                session.commit()
