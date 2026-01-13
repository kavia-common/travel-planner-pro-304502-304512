from fastapi.testclient import TestClient

from src.api.main import app


def _login_and_get_token(client: TestClient) -> str:
    res = client.post("/auth/login", json={"email": "demo@example.com", "password": "demo123"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token
    return token


def test_trips_create_validates_date_order() -> None:
    with TestClient(app) as client:
        token = _login_and_get_token(client)
        bad = client.post(
            "/trips",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Bad", "description": None, "start_date": "2025-01-02", "end_date": "2025-01-01"},
        )
        assert bad.status_code == 422
        assert bad.json()["detail"] == "end_date cannot be before start_date"


def test_trips_create_validates_name_min_length() -> None:
    with TestClient(app) as client:
        token = _login_and_get_token(client)
        bad = client.post(
            "/trips",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "", "description": None, "start_date": None, "end_date": None},
        )
        assert bad.status_code == 422
        detail = bad.json()["detail"]
        assert isinstance(detail, list)
        assert detail[0]["loc"] == ["body", "name"]


def test_trips_get_not_found() -> None:
    with TestClient(app) as client:
        token = _login_and_get_token(client)
        res = client.get("/trips/999999", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 404
        assert res.json()["detail"] == "Trip not found"


def test_favorites_duplicate_returns_409() -> None:
    with TestClient(app) as client:
        token = _login_and_get_token(client)

        trip = client.post(
            "/trips",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "T1", "description": None, "start_date": None, "end_date": None},
        )
        assert trip.status_code == 201
        trip_id = trip.json()["id"]

        dest = client.post(
            "/destinations",
            headers={"Authorization": f"Bearer {token}"},
            json={"trip_id": trip_id, "name": "Tokyo"},
        )
        assert dest.status_code == 201
        dest_id = dest.json()["id"]

        fav1 = client.post("/favorites", headers={"Authorization": f"Bearer {token}"}, json={"destination_id": dest_id})
        assert fav1.status_code == 201

        fav2 = client.post("/favorites", headers={"Authorization": f"Bearer {token}"}, json={"destination_id": dest_id})
        assert fav2.status_code == 409
        assert fav2.json()["detail"] == "Already favorited"


def test_itinerary_rejects_destination_not_in_trip() -> None:
    with TestClient(app) as client:
        token = _login_and_get_token(client)

        trip = client.post(
            "/trips",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "TripY", "description": None, "start_date": None, "end_date": None},
        )
        assert trip.status_code == 201
        trip_id = trip.json()["id"]

        bad = client.post(
            "/itinerary",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "trip_id": trip_id,
                "destination_id": 999999,
                "title": "Event",
                "description": None,
                "start_time": None,
                "end_time": None,
                "all_day": False,
            },
        )
        assert bad.status_code == 422
        assert bad.json()["detail"] == "destination_id not in trip"


def test_bookings_validates_date_order() -> None:
    with TestClient(app) as client:
        token = _login_and_get_token(client)

        trip = client.post(
            "/trips",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "TripB", "description": None, "start_date": None, "end_date": None},
        )
        assert trip.status_code == 201
        trip_id = trip.json()["id"]

        bad = client.post(
            "/bookings",
            headers={"Authorization": f"Bearer {token}"},
            json={"trip_id": trip_id, "booking_type": "flight", "start_date": "2025-01-02", "end_date": "2025-01-01"},
        )
        assert bad.status_code == 422
        assert bad.json()["detail"] == "end_date cannot be before start_date"
