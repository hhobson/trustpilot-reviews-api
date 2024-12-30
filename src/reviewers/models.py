from datetime import datetime, timezone

from pydantic import EmailStr
from pydantic_extra_types.country import CountryAlpha3
from sqlmodel import Field, SQLModel


class ReviewerBase(SQLModel):
    email: EmailStr
    name: str = Field(min_length=2)
    country: CountryAlpha3 = Field(nullable=False)


class Reviewer(ReviewerBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True)
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=True
    )  # Nullable because instantiation data doesn't have reviewer created data, so if null means legacy user
    updated_at: datetime | None = Field(
        default=None, nullable=True, sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )


class ReviewerCreate(ReviewerBase):
    pass


class ReviewerUpdate(SQLModel):
    email: EmailStr | None = None
    name: str | None = Field(default=None, min_length=2)
    country: CountryAlpha3 | None = None


class ReviewerResponce(ReviewerBase):
    id: int
