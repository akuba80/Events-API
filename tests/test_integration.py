import requests
import uuid

BASE_URL = "http://localhost:5001"


def unique_username():
    """Erzeugt einen eindeutigen Usernamen, damit Tests wiederholbar sind."""
    return f"testuser_{uuid.uuid4().hex[:8]}"


# --- Health & Grundgerüst ---

def test_health_check():
    response = requests.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200


def test_swagger_docs_reachable():
    response = requests.get(f"{BASE_URL}/apidocs")
    assert response.status_code == 200


# --- Auth ---

def test_register_new_user():
    payload = {"username": unique_username(), "password": "sicheres_passwort123"}
    response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    assert response.status_code in (200, 201)


def test_register_duplicate_username_fails():
    username = unique_username()
    payload = {"username": username, "password": "sicheres_passwort123"}
    requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    assert response.status_code in (400, 409)


def test_login_with_valid_credentials_returns_token():
    username = unique_username()
    payload = {"username": username, "password": "sicheres_passwort123"}
    requests.post(f"{BASE_URL}/api/auth/register", json=payload)

    response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
    assert response.status_code == 200
    assert "access_token" in response.json() or "token" in response.json()


def test_login_with_wrong_password_fails():
    username = unique_username()
    requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"username": username, "password": "richtiges_passwort"},
    )
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": username, "password": "falsches_passwort"},
    )
    assert response.status_code == 401


# --- Events ---

def test_get_events_list():
    response = requests.get(f"{BASE_URL}/api/events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_event_requires_authentication():
    payload = {
        "title": "Python Meetup",
        "description": "Monthly Python developer meetup",
        "date": "2026-01-15T18:00:00",
        "location": "Tech Hub, Room 101",
        "capacity": 50,
        "is_public": True,
        "requires_admin": False,
    }
    response = requests.post(f"{BASE_URL}/api/events", json=payload)
    assert response.status_code == 401


def test_create_event_with_valid_token():
    username = unique_username()
    creds = {"username": username, "password": "sicheres_passwort123"}
    requests.post(f"{BASE_URL}/api/auth/register", json=creds)
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=creds)
    token = login_response.json().get("access_token") or login_response.json().get("token")

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": "Docker Workshop",
        "description": "Hands-on Docker Session",
        "date": "2026-02-01T10:00:00",
        "location": "Online",
        "capacity": 30,
        "is_public": True,
        "requires_admin": False,
    }
    response = requests.post(f"{BASE_URL}/api/events", json=payload, headers=headers)
    assert response.status_code in (200, 201)


def test_get_single_event_not_found():
    response = requests.get(f"{BASE_URL}/api/events/999999")
    assert response.status_code == 404


# --- RSVPs ---

def test_rsvp_requires_existing_event():
    response = requests.post(
        f"{BASE_URL}/api/rsvps/event/999999", json={"attending": True}
    )
    assert response.status_code in (401, 404)