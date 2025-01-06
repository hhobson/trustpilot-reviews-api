from datetime import datetime
from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from ..database import Session
from ..utils import OPERATOR_MAPPING
from .models import Review, ReviewCreate, ReviewResponce, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/", response_model=List[ReviewResponce])
def get_reviews(
    session: Session,
    rating: Annotated[
        str | None,
        Query(
            title="Rating",
            description="Filter reviews by there rating. Either by providing exact rating value or by providing a valid operator followed by a rating value. Valid operators are `eq:`, `gt:`, `gte:`, `lt:` and `lte:`.",
            pattern="^((eq|gte?|lte?):)?[1-5]$",
        ),
    ] = None,
    date: Annotated[
        str | None,
        Query(
            title="Created Date",
            description="Filter reviews by there date they were created. Either by providing exact date value or by providing a valid operator followed by a rating value. This is a date in [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format: `YYYY-MM-DD`. Valid operators are `eq:`, `gt:`, `gte:`, `lt:` and `lte:`. To filter for a specific date range, provide multiple parameters, one using `gt`/`gte` operator and the other using `lt`/`lte` operator.",
            pattern="((eq|gte?|lte?):)?(19|20)\d{2}-(0[1-9]|1[0,1,2])-(0[1-9]|[12][0-9]|3[01])$",
        ),
    ] = None,
    reviewer_id: Annotated[
        int | None,
        Query(
            title="Reviewer Id",
            description="Filter reviews by a specific user.",
            alias="ReviewerId",
            gt=0,
        ),
    ] = None,
):
    """## Retrieve all reviews

    Reviews can be filtered by there rating, creation date and/or the user who wrote them.

    ![Fetch](https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExM2k3bmV1dmhvajYzODRwd3p1MDR4Z2twcno1bXZxM20zeGhmNTRpMCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/klPeFHrWqzPDW/giphy.gif)
    """
    query = select(Review)
    if rating:
        if ":" in rating:
            op, _, value = rating.partition(":")
            operator = OPERATOR_MAPPING.get(op)
            query = query.where(operator(Review.rating, value))
        else:
            query = query.where(Review.rating == int(rating))

    if date:
        if ":" in date:
            op, _, value = date.partition(":")
            operator = OPERATOR_MAPPING.get(op)
            query_date = datetime.strptime(value, "%Y-%m-%d")
            query = query.where(operator(Review.created_at, query_date))
        else:
            query_date = datetime.strptime(date, "%Y-%m-%d")
            query = query.where(Review.created_at == query_date)

    if reviewer_id:
        query = query.where(Review.reviewer_id == reviewer_id)

    reviews = session.exec(query).all()
    return reviews


@router.post("/", response_model=ReviewResponce, status_code=status.HTTP_201_CREATED)
def create_review(review: ReviewCreate, session: Session):
    """## Create a new review"""
    db_review = Review.model_validate(review)
    session.add(db_review)
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reviewer not found")
    session.refresh(db_review)
    return db_review


@router.get("/{review_id}", response_model=ReviewResponce)
def get_review(review_id: int, session: Session):
    """## Retrieve a specific review"""
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


@router.patch("/{review_id}", response_model=ReviewResponce)
def update_review(review_id: int, review: ReviewUpdate, session: Session):
    """## Update a specific review

    The reviews title, rating and content can be updated. The request body only needs to contain fields that should be changed.
    """
    db_review = session.get(Review, review_id)
    if not db_review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    review_update = review.model_dump(exclude_unset=True)
    db_review.sqlmodel_update(review_update)
    Review.model_validate(db_review)
    session.add(db_review)
    session.commit()
    session.refresh(db_review)
    return db_review


@router.delete("/{review_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, session: Session):
    """## Delete a review


    ![Delete This](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOG50NDI3Y3dwMmtvZnQxd3dvNm9tY2w5ejJwYWJoMnNuc2Q5aG10eiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/xULW8N9O5WD32L5052/giphy.gif)
    """
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    session.delete(review)
    session.commit()
