from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Query, status
from pydantic_extra_types.country import CountryAlpha3
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from ..database import Session
from .models import Reviewer, ReviewerCreate, ReviewerResponce, ReviewerUpdate

router = APIRouter(prefix="/reviewers", tags=["reviewers"])


@router.get("/", response_model=List[ReviewerResponce])
def get_reviewers(
    session: Session,
    country: Annotated[
        CountryAlpha3 | None,
        Query(
            title="Country Code",
            description="Filter reviewers from a specific country, using valid [ISO 3166 three letter country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3)",
        ),
    ] = None,
):
    query = select(Reviewer)
    if country:
        query = query.where(Reviewer.country == country)

    reviewers = session.exec(query).all()
    return reviewers


@router.post("/", response_model=ReviewerResponce, status_code=status.HTTP_201_CREATED)
def create_reviewer(reviewer: ReviewerCreate, session: Session):
    db_reviewer = Reviewer.model_validate(reviewer)
    session.add(db_reviewer)
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reviewer email already in use")
    session.refresh(db_reviewer)
    return db_reviewer


@router.get("/{reviewer_id}", response_model=ReviewerResponce)
def get_reviewer(reviewer_id: int, session: Session):
    reviewer = session.get(Reviewer, reviewer_id)
    if not reviewer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reviewer not found")
    return reviewer


@router.patch("/{reviewer_id}", response_model=ReviewerResponce)
def update_reviewer(reviewer_id: int, reviewer: ReviewerUpdate, session: Session):
    db_reviewer = session.get(Reviewer, reviewer_id)
    if not db_reviewer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reviewer not found")
    reviewer_update = reviewer.model_dump(exclude_unset=True)
    db_reviewer.sqlmodel_update(reviewer_update)
    Reviewer.model_validate(db_reviewer)
    session.add(db_reviewer)
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reviewer email already in use")
    session.refresh(db_reviewer)
    return db_reviewer


@router.delete("/{reviewer_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_reviewer(reviewer_id: int, session: Session):
    reviewer = session.get(Reviewer, reviewer_id)
    if not reviewer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reviewer not found")
    session.delete(reviewer)
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Reviewer can't be deleted if it has reviews"
        )
