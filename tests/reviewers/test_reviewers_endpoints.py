from typing import List

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from src.reviewers.models import Reviewer, ReviewerCreate

from ..conftest import COUNTY_CODES, FIX_COUNTRY, FIXED_REVIEWER_EMAIL, REVIEWERS_COUNT

ROUTE_URL = "/reviewers"


# GET /reviewers
def test_get_reviewers(test_client: TestClient):
    response = test_client.get(ROUTE_URL)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == REVIEWERS_COUNT


def test_get_reviewers_country_query_param(test_client: TestClient):
    response = test_client.get(f"{ROUTE_URL}/?country={FIX_COUNTRY}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) < REVIEWERS_COUNT


def test_get_reviewers_error(test_client: TestClient):
    response = test_client.get(f"{ROUTE_URL}/?country=XXX")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# POST /reviewers
@pytest.mark.parametrize(
    "name, email, country",
    [
        ("Oliver Queen", "green.arrow@queen-consolidated.com", "USA"),
        ("Slade Wilson", "deathstroke@asai.com", "aus"),
        ("Shado Yu", "shado@gmail.com", "Chn"),
    ],
)
def test_post_reviewers(test_client: TestClient, name: str, email: str, country: str):
    body = {"name": name, "email": email, "country": country}
    response = test_client.post(ROUTE_URL, json=body)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["id"] == REVIEWERS_COUNT + 1
    assert data["name"] == name
    assert data["email"] == email
    assert data["country"] == country.upper()


@pytest.mark.parametrize(
    "name, email, country, expected_status",
    [
        ("", "the-hood@arrow.com", "USA", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("Oliver Queen", "", "USA", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("Slade Wilson", "deathstroke.com", "AUS", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("Laurel Lance", "laurel@lance.com", "United States of America", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("Ra's al Ghul", "ras@league-of-shadows.xxx", "los", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("Barry Allen", FIXED_REVIEWER_EMAIL, "USA", status.HTTP_409_CONFLICT),
    ],
)  # fmt: skip
def test_post_reviews_error(
    test_client: TestClient, name: str, email: str, country: str, expected_status: int
):
    body = {"name": name, "email": email, "country": country}
    response = test_client.post(ROUTE_URL, json=body)

    assert response.status_code == expected_status


# GET /reviewers/{id}
def test_get_reviewer(test_client: TestClient, reviewers_data: List[ReviewerCreate]):
    id = 1
    expected_data = reviewers_data[0]

    response = test_client.get(f"{ROUTE_URL}/{id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == id
    assert data["name"] == expected_data.name
    assert data["email"] == expected_data.email
    assert data["country"] == expected_data.country
    assert data["country"] in COUNTY_CODES


def test_get_reviewer_error(test_client: TestClient):
    id = REVIEWERS_COUNT + 1
    response = test_client.get(f"{ROUTE_URL}/{id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# PATCH /reviewers/{id}
@pytest.mark.parametrize(
    "id, body",
    [
        (4, {"name": "Shado"}),
        (1, {"email": "call@me.maybe"}),
        (8, {"country": "TJK"}),
        (4, {"name": "Flash", "country": "SXM"}),
        (1, {"email": "call@me.maybe", "name": "Yu"}),
        (7, {"email": "call@me.maybe", "country": "SSD"}),
        (12, {"name": "Deathstroke", "email": "death@stroke.it", "country": "TJK"}),
    ],
)
def test_update_reviewer(test_client: TestClient, reviewers_data: List[ReviewerCreate], id: int, body: dict):
    expected_data = reviewers_data[id - 1].model_dump()
    unchanged_key = set(expected_data.keys()) - set(body.keys())

    response = test_client.patch(f"{ROUTE_URL}/{id}", json=body)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    for key in unchanged_key:
        assert data[key] == expected_data[key]
    for key in body.keys():
        assert data[key] == body[key]


@pytest.mark.parametrize(
    "id, body, expected_status",
    [
        (REVIEWERS_COUNT + 1, {"name": "Deathstroke"}, status.HTTP_404_NOT_FOUND),
        (1, {"email": FIXED_REVIEWER_EMAIL}, status.HTTP_409_CONFLICT),
        (1, {"name": ""}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (1, {"name": None}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (1, {"email": None}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (1, {"country": None}, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
def test_update_reviewer_error(test_client: TestClient, id: int, body: dict, expected_status: int):
    response = test_client.patch(f"{ROUTE_URL}/{id}", json=body)
    assert response.status_code == expected_status


# DELETE /reviewers/{id}
def test_delete_reviewer(test_client: TestClient, session: Session):
    # reviews with id that is multiple of 10, don't have any reviews test data
    deletable_reviewers = [id for id in range(10, REVIEWERS_COUNT + 1, 10)]
    for id in deletable_reviewers:
        response = test_client.delete(f"{ROUTE_URL}/{id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.text == ""

    reviewer_count = session.exec(select(func.count(Reviewer.id))).first()
    assert reviewer_count == REVIEWERS_COUNT - len(deletable_reviewers)


@pytest.mark.parametrize(
    "id, expected_status",
    [
        (REVIEWERS_COUNT + 1, status.HTTP_404_NOT_FOUND),
        (3, status.HTTP_409_CONFLICT),
    ],
)
def test_delete_reviewer_error(test_client: TestClient, id: int, expected_status: int):
    response = test_client.delete(f"{ROUTE_URL}/{id}")
    assert response.status_code == expected_status
