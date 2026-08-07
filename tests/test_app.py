import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)

# Snapshot of the original participants lists to restore before each test
_original_participants = {name: list(data["participants"]) for name, data in activities.items()}


@pytest.fixture(autouse=True)
def reset_participants():
    for name, original in _original_participants.items():
        activities[name]["participants"] = list(original)


# --- GET / ---

def test_root_redirects():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"].endswith("/static/index.html")


# --- GET /activities ---

def test_get_activities_returns_all():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(activities)


def test_get_activities_shape():
    response = client.get("/activities")
    data = response.json()
    for name, details in data.items():
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)


# --- POST /activities/{activity_name}/signup ---

def test_signup_success():
    response = client.post("/activities/Chess Club/signup?email=new@mergington.edu")
    assert response.status_code == 200
    assert "new@mergington.edu" in response.json()["message"]
    assert "new@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_unknown_activity():
    response = client.post("/activities/Underwater Basket Weaving/signup?email=new@mergington.edu")
    assert response.status_code == 404


def test_signup_duplicate_email():
    client.post("/activities/Chess Club/signup?email=new@mergington.edu")
    response = client.post("/activities/Chess Club/signup?email=new@mergington.edu")
    assert response.status_code == 400


# --- DELETE /activities/{activity_name}/signup ---

def test_unregister_success():
    response = client.delete("/activities/Chess Club/signup?email=michael@mergington.edu")
    assert response.status_code == 200
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_unknown_activity():
    response = client.delete("/activities/Underwater Basket Weaving/signup?email=michael@mergington.edu")
    assert response.status_code == 404


def test_unregister_email_not_registered():
    response = client.delete("/activities/Chess Club/signup?email=nobody@mergington.edu")
    assert response.status_code == 404
