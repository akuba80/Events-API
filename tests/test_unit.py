import pytest
from app import create_app
from models import db


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# --- Health ---

def test_health_endpoint_unit(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


# --- Auth ---

def test_register_missing_fields(client):
    response = client.post("/api/auth/register", json={})
    assert response.status_code in (400, 422)


def test_register_returns_success_with_valid_data(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "unituser1", "password": "testpass123"},
    )
    assert response.status_code in (200, 201)


def test_login_missing_password(client):
    response = client.post("/api/auth/login", json={"username": "irgendwer"})
    assert response.status_code in (400, 422)


def test_login_unknown_user_fails(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "existiert_nicht", "password": "egal"},
    )
    assert response.status_code == 401


# --- Events ---

def test_get_events_empty_list(client):
    response = client.get("/api/events")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_event_without_token_rejected(client):
    response = client.post(
        "/api/events",
        json={"title": "Test Event", "date": "2026-01-01T10:00:00"},
    )
    assert response.status_code == 401


def test_get_nonexistent_event_returns_404(client):
    response = client.get("/api/events/12345")
    assert response.status_code == 404


# --- RSVPs ---

def test_rsvp_to_nonexistent_event(client):
    response = client.post(
        "/api/rsvps/event/12345", json={"attending": True}
    )
    assert response.status_code in (401, 404)