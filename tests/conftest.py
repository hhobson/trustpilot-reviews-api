import random
from datetime import datetime
from typing import List

import pycountry
import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from src.api import app
from src.database import get_session
from src.reviewers.models import Reviewer, ReviewerCreate
from src.reviews.models import Review, ReviewCreate

SQLITE_DATABASE_URL = "sqlite:///"

REVIEWERS_COUNT = 50
REVIEWS_COUNT = 120


FAKER = Faker()

FIX_COUNTRY = "JEY"
COUNTY_CODES = [country.alpha_3 for country in pycountry.countries]
SAMPLED_COUNTRY_CODES = FAKER.random_sample(elements=COUNTY_CODES, length=49)
SAMPLED_COUNTRY_CODES.append(FIX_COUNTRY)
# Weighting to prioritise the fixed country
COUNTRY_WEIGHTS = [2 if code == FIX_COUNTRY else 1 for code in SAMPLED_COUNTRY_CODES]

FIXED_REVIEWER_EMAIL = "nice.to.meet@you.xxx"


@pytest.fixture(scope="session")
def reviewers_data():
    """Generate a list of ReviewerCreate objects with unique emails and varied country codes"""
    reviewers = []
    # Add one reviewer with a fixed email so we can use this in tests
    reviewers.append(
        ReviewerCreate(
            email=FIXED_REVIEWER_EMAIL, name=FAKER.name(), country=random.choice(SAMPLED_COUNTRY_CODES)
        )
    )

    for i in range(1, REVIEWERS_COUNT):
        email = FAKER.unique.email()
        name = FAKER.name()
        country = random.choices(SAMPLED_COUNTRY_CODES, weights=COUNTRY_WEIGHTS, k=1)[0]

        reviewers.append(ReviewerCreate(email=email, name=name, country=country))

        random.shuffle(reviewers)

    yield reviewers


@pytest.fixture(scope="session")
def reviews_data():
    """Generate a list of ReviewCreate objects"""
    reviews = []

    # Caluclate what reviewer ids will be when added to the database
    # Excluding any that are multiples of 10, to ensure that some known reviewers don't have any reviews
    reviewer_ids = [n for n in range(1, REVIEWERS_COUNT) if n % 10 != 0]

    for _ in range(REVIEWS_COUNT):
        reviewer_id = random.choice(reviewer_ids)
        title = FAKER.sentence(nb_words=6)
        rating = random.randint(1, 5)

        content = FAKER.paragraph(nb_sentences=3)
        num_emojis = random.randint(0, 5)
        emoji_positions = sorted(random.sample(range(len(content)), min(num_emojis, len(content))))
        for pos in emoji_positions:
            emoji = FAKER.emoji()
            content = content[:pos] + emoji + content[pos:]

        reviews.append(ReviewCreate(reviewer_id=reviewer_id, title=title, rating=rating, content=content))

    yield reviews

    # data = generate_reviews(REVIEWS_COUNT, reviewer_ids)
    # yield data


@pytest.fixture(scope="function", name="engine")
def database(reviewers_data: List[ReviewerCreate], reviews_data: List[ReviewCreate]):
    """Create and populate test database"""
    engine = create_engine(
        SQLITE_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        db_reviewers = [Reviewer.model_validate(reviewer) for reviewer in reviewers_data]
        session.add_all(db_reviewers)
        session.commit()

        start_date = datetime(2024, 1, 1, 0, 0, 00, 000000)
        end_date = datetime(2025, 1, 1, 0, 0, 00, 000000)
        db_reviews = [
            Review.model_validate(
                {**review.model_dump(), "created_at": FAKER.date_between(start_date, end_date)}
            )
            for review in reviews_data
        ]
        session.add_all(db_reviews)
        session.commit()
    yield engine


@pytest.fixture(scope="function")
def session(engine: Engine):
    """Create a new database session with a rollback at the end of the test."""
    TestingSessionLocal = sessionmaker(class_=Session, autocommit=False, autoflush=False, bind=engine)

    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_client(session: Session):
    """Create a test client that uses the override_get_db fixture to return a session."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
