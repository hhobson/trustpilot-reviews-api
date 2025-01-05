from datetime import datetime, timezone

from sqlmodel import Field, SQLModel

from ..utils import DemojizedStr


class ReviewBase(SQLModel):
    reviewer_id: int = Field(gt=0)
    title: str = Field(min_length=2)
    rating: int = Field(ge=1, le=5)
    content: str = Field(min_length=10)


class Review(ReviewBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    reviewer_id: int = Field(foreign_key="reviewer.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(
        default=None, nullable=True, sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )


class ReviewCreate(ReviewBase):
    content: DemojizedStr


class ReviewUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=2)
    rating: int = Field(default=None, ge=1, le=5)
    content: DemojizedStr | None = Field(default=None, min_length=10)


class ReviewResponce(ReviewBase):
    id: int
    created_at: datetime
