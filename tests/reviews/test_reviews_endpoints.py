from datetime import datetime
from typing import List

import emoji
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from src.reviews.models import Review, ReviewCreate
from src.utils import OPERATOR_MAPPING

from ..conftest import REVIEWERS_COUNT, REVIEWS_COUNT

ROUTE_URL = "/reviews"


# GET /reviews
def test_get_reviews(test_client: TestClient):
    response = test_client.get(ROUTE_URL)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == REVIEWS_COUNT


# TODO: Improve performance of this test and add more test cases
@pytest.mark.parametrize(
    "rating_filter, date_filter, reviewer_id_filter",
    [
        ("eq:5", None, None),
        ("gt:3", None, None),
        ("lte:2", None, None),
        (None, "gte:2024-06-01", None),
        (None, "lt:2024-06-01", None),
        (None, None, 5),
        ("eq:4", "gte:2024-01-01", 3),
    ],
)
def test_get_reviews_dynamic(
    test_client: TestClient,
    session: Session,
    rating_filter,
    date_filter,
    reviewer_id_filter,
):
    all_reviews = session.exec(select(Review)).all()

    filtered_reviews = all_reviews
    if rating_filter:
        op, _, value = rating_filter.partition(":")
        operator = OPERATOR_MAPPING[op]
        filtered_reviews = [r for r in filtered_reviews if operator(r.rating, int(value))]

    if date_filter:
        op, _, value = date_filter.partition(":")
        operator = OPERATOR_MAPPING[op]
        filter_date = datetime.strptime(value, "%Y-%m-%d").date()
        filtered_reviews = [r for r in filtered_reviews if operator(r.created_at.date(), filter_date)]

    if reviewer_id_filter:
        filtered_reviews = [r for r in filtered_reviews if r.reviewer_id == reviewer_id_filter]

    params = {}
    if rating_filter:
        params["rating"] = rating_filter
    if date_filter:
        params["date"] = date_filter
    if reviewer_id_filter:
        params["ReviewerId"] = reviewer_id_filter

    response = test_client.get("/reviews", params=params)
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == len(filtered_reviews)

    for review_response in response_data:
        matching_review = next(r for r in filtered_reviews if r.id == review_response["id"])

        if rating_filter:
            op, _, value = rating_filter.partition(":")
            operator = OPERATOR_MAPPING[op]
            assert operator(matching_review.rating, int(value))

        if date_filter:
            op, _, value = date_filter.partition(":")
            operator = OPERATOR_MAPPING[op]
            filter_date = datetime.strptime(value, "%Y-%m-%d").date()
            assert operator(matching_review.created_at.date(), filter_date)

        if reviewer_id_filter:
            assert matching_review.reviewer_id == reviewer_id_filter


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
