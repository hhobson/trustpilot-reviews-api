from typing import Tuple

import pytest
from sqlmodel import Session

from src.ingest import load_row

from .conftest import FIXED_REVIEWER_EMAIL


def test_load_database_from_csv():
    pass


@pytest.mark.parametrize(
    "row_number, row, expected_result",
    [
        (  # Valid reviewer and review
            1,
            {
                "Email Address": "valid@example.com",
                "Reviewer Name": "John Doe",
                "Country": "United States",
                "Review Title": "Great Product",
                "Review Rating": "5",
                "Review Content": "Loved it! ❤️ 💖",
                "Review Date": "2023-01-01",
            },
            (True, True),
        ),
        (  # Reviewer already exists in the database
            2,
            {
                "Email Address": FIXED_REVIEWER_EMAIL,
                "Reviewer Name": "Jane Doe",
                "Country": "UK",
                "Review Title": "Good Product",
                "Review Rating": "4",
                "Review Content": "Quite satisfied!",
                "Review Date": "2023-01-01",
            },
            (False, True),
        ),
        (  # Invalid reviewer email
            3,
            {
                "Email Address": "invalid-email",
                "Reviewer Name": "John Doe",
                "Country": "Spain",
                "Review Title": "Nice Product",
                "Review Rating": "4",
                "Review Content": "Great!",
                "Review Date": "2023-01-01",
            },
            (False, False),
        ),
        (  # Invalid reviewer name
            42,
            {
                "Email Address": "valid@example.com",
                "Reviewer Name": "",
                "Country": "Denmark",
                "Review Title": "Nice Product",
                "Review Rating": "4",
                "Review Content": "Great!",
                "Review Date": "2023-01-01",
            },
            (False, False),
        ),
        (  # Invalid review rating
            88,
            {
                "Email Address": "valid@example.com",
                "Reviewer Name": "John Doe",
                "Country": "Mexico",
                "Review Title": "Bad Product",
                "Review Rating": 10,
                "Review Content": "Disappointed!",
                "Review Date": "2023-01-01",
            },
            (True, False),
        ),
        (  # Invalid review date
            999,
            {
                "Email Address": "valid@example.com",
                "Reviewer Name": "John Doe",
                "Country": "USA",
                "Review Title": "Bad Product",
                "Review Rating": "2",
                "Review Content": "It was okay!",
                "Review Date": "08/08/2004",
            },
            (True, False),
        ),
    ],
)
def test_load_row(session: Session, row_number: int, row: dict, expected_result: Tuple[bool]):
    result = load_row(row_number, row, session)
    assert result == expected_result
