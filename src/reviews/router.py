from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from ..database import Session
from .models import Review, ReviewCreate, ReviewResponce, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/", response_model=List[ReviewResponce])
def get_reviews(session: Session):
    reviews = session.exec(select(Review)).all()
    return reviews


@router.post("/", response_model=ReviewResponce, status_code=status.HTTP_201_CREATED)
def create_review(review: ReviewCreate, session: Session):
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
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


@router.patch("/{review_id}", response_model=ReviewResponce)
def update_review(review_id: int, review: ReviewUpdate, session: Session):
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
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    session.delete(review)
    session.commit()
