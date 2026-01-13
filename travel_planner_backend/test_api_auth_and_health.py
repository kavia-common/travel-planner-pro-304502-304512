from fastapi.testclient import TestClient

from src.api.main import app


def test_health_check_ok() -> None:
    with TestClient(app) as client:
        res = client.get("/")
        assert res.status_code == 200
        assert res.json() == {"message": "Healthy"}


def test_docs_help_ok() -> None:
    with TestClient(app) as client:
        res = client.get("/docs/help")
        assert res.status_code == 200
        body = res.json()
        assert "message" in body
        assert "POST /auth/login" in body["message"]


def test_protected_endpoint_requires_bearer_token() -> None:
    with TestClient(app) as client:
        res = client.get("/trips")
        assert res.status_code == 401
        assert res.json()["detail"] == "Missing Bearer token"


def test_invalid_token_rejected() -> None:
    with TestClient(app) as client:
        res = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert res.status_code == 401
        assert res.json()["detail"] == "Invalid or expired token"


def test_login_invalid_credentials() -> None:
    with TestClient(app) as client:
        res = client.post("/auth/login", json={"email": "demo@example.com", "password": "wrong"})
        assert res.status_code == 401
        assert res.json()["detail"] == "Invalid credentials"


def test_register_then_duplicate_email_conflict() -> None:
    # Uses a unique email to avoid flakiness if DB is persisted across local runs.
    email = "pytest_user_unique@example.com"
    with TestClient(app) as client:
        first = client.post("/auth/register", json={"email": email, "password": "secret12", "full_name": None})
        assert first.status_code == 201
        body = first.json()
        assert "access_token" in body and body["access_token"]
        assert body["user"]["email"] == email

        dup = client.post("/auth/register", json={"email": email, "password": "secret12", "full_name": None})
        assert dup.status_code == 409
        assert dup.json()["detail"] == "Email already registered"
