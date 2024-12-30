from typing import List

import emoji
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from src.reviews.models import Review, ReviewCreate

from ..conftest import REVIEWERS_COUNT, REVIEWS_COUNT

ROUTE_URL = "/reviews"


# GET /reviews
def test_get_reviews(test_client: TestClient):
    response = test_client.get(ROUTE_URL)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == REVIEWS_COUNT


# POST /reviews
@pytest.mark.parametrize(
    "reviewer_id, title, rating, content",
    [
        (5, "A Dream Come True", 5, "I woke up this morning and my wildest dream was real"),
        (10, "Nothing Nice 2 Say", 1, "If you have nothing nice to say, say nothing!! 🙈🙉🙊"),
        (10, "OK", 3, "🤷🏾 Could have been better, could have been worse"),
    ],
)
def test_post_reviews(test_client: TestClient, reviewer_id: int, title: str, rating: int, content: str):
    body = {"reviewer_id": reviewer_id, "title": title, "rating": rating, "content": content}
    response = test_client.post(ROUTE_URL, json=body)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["id"] == REVIEWS_COUNT + 1
    assert data["title"] == title
    assert data["rating"] == rating
    assert data["content"] == emoji.demojize(content)


@pytest.mark.parametrize(
    "reviewer_id, title, rating, content, expected_status",
    [
        (REVIEWERS_COUNT + 1, "A Dream Come True", 5, "My wildest dream has come true", status.HTTP_404_NOT_FOUND),
        (5, "A Dream Come True", 6, "My wildest dream has come true", status.HTTP_422_UNPROCESSABLE_ENTITY),
        (10, "Nothing Nice 2 Say", 0, "If you have nothing nice to say, say nothing!! 🙈🙉🙊", status.HTTP_422_UNPROCESSABLE_ENTITY),
        (5, "A Dream Come True", 5, "", status.HTTP_422_UNPROCESSABLE_ENTITY),
        (10, "", 1, "If you have nothing nice to say, say nothing!! 🙈🙉🙊", status.HTTP_422_UNPROCESSABLE_ENTITY),
    ]
)  # fmt: skip
def test_post_reviews_error(
    test_client: TestClient, reviewer_id: int, title: str, rating: int, content: str, expected_status: int
):
    body = {"reviewer_id": reviewer_id, "title": title, "rating": rating, "content": content}
    response = test_client.post(ROUTE_URL, json=body)

    assert response.status_code == expected_status


# GET /reviews/{id}
def test_get_review(test_client: TestClient, reviews_data: List[ReviewCreate]):
    id = 1
    expected_data = reviews_data[0]

    response = test_client.get(f"{ROUTE_URL}/{id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == id
    assert data["reviewer_id"] == expected_data.reviewer_id
    assert data["title"] == expected_data.title
    assert data["rating"] == expected_data.rating
    assert data["content"] == expected_data.content


def test_get_review_error(test_client: TestClient):
    id = REVIEWS_COUNT + 1
    response = test_client.get(f"{ROUTE_URL}/{id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# PATCH /reviews/{id}
@pytest.mark.parametrize(
    "id, body",
    [
        (4, {"title": "Better?"}),
        (1, {"rating": 4}),
        (8, {"content": "Superfragilistic alidocious"}),
        (4, {"title": "Better?", "content": "Superfragilistic alidocious"}),
        (7, {"rating": 4, "title": "Better?"}),
        (1, {"rating": 4, "content": "Superfragilistic alidocious"}),
        (12, {"title": "Better?", "rating": 4, "content": "Superfragilistic alidocious"}),
    ],
)
def test_update_review(test_client: TestClient, reviews_data: List[ReviewCreate], id: int, body: dict):
    expected_data = reviews_data[id - 1].model_dump()
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
        (REVIEWS_COUNT + 1, {"title": "Better?"}, status.HTTP_404_NOT_FOUND),
        (1, {"rating": 0}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (1, {"rating": 6}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (1, {"title": None}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (1, {"title": ""}, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
def test_update_review_error(test_client: TestClient, id: int, body: dict, expected_status: int):
    response = test_client.patch(f"{ROUTE_URL}/{id}", json=body)
    assert response.status_code == expected_status


# DELETE /reviews/{id}
def test_delete_review(test_client: TestClient, session: Session):
    del_records = 4
    for id in range(1, del_records + 1):
        response = test_client.delete(f"{ROUTE_URL}/{id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.text == ""

    review_count = session.exec(select(func.count(Review.id))).first()
    assert review_count == REVIEWS_COUNT - del_records


def test_delete_review_error(test_client: TestClient):
    id = REVIEWS_COUNT + 1
    response = test_client.delete(f"{ROUTE_URL}/{id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
