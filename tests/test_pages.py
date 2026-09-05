from fastapi.testclient import TestClient

from app.database import database
from app.main import app


client = TestClient(
    app,
    raise_server_exceptions=False,
)


def test_health_endpoint():
    with client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["database"] == "connected"


def test_dashboard_page():
    with client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "Total users" in response.text
    assert "Total events" in response.text


def test_events_page():
    with client:
        response = client.get("/events")

    assert response.status_code == 200
    assert "Search and manage campus events" in response.text
    assert database.events.count_documents({}) > 0


def test_event_search():
    with client:
        response = client.get(
            "/events",
            params={"q": "MongoDB"},
        )

    assert response.status_code == 200
    assert "MongoDB" in response.text


def test_event_category_filter():
    category = database.events.distinct("category")[0]

    with client:
        response = client.get(
            "/events",
            params={"category": category},
        )

    assert response.status_code == 200
    assert category in response.text


def test_event_tag_filter():
    tag = database.events.distinct("tags")[0]

    with client:
        response = client.get(
            "/events",
            params={"tag": tag},
        )

    assert response.status_code == 200
    assert tag in response.text


def test_create_event_page():
    with client:
        response = client.get("/events/new")

    assert response.status_code == 200
    assert "Create Event" in response.text


def test_invalid_event_id_returns_404():
    with client:
        response = client.get(
            "/events/not-a-valid-object-id"
        )

    assert response.status_code == 404
    assert "Page not found" in response.text


def test_users_page():
    with client:
        response = client.get("/users")

    assert response.status_code == 200
    assert "Search and manage campus users" in response.text
    assert database.users.count_documents({}) > 0


def test_user_search():
    user = database.users.find_one(
        {},
        {
            "firstName": 1,
        },
    )

    with client:
        response = client.get(
            "/users",
            params={"q": user["firstName"]},
        )

    assert response.status_code == 200
    assert user["firstName"] in response.text


def test_create_user_page():
    with client:
        response = client.get("/users/new")

    assert response.status_code == 200
    assert "Create User" in response.text


def test_invalid_user_id_returns_404():
    with client:
        response = client.get(
            "/users/not-a-valid-object-id"
        )

    assert response.status_code == 404
    assert "Page not found" in response.text


def test_analytics_page():
    with client:
        response = client.get("/analytics")

    assert response.status_code == 200

    required_analyses = [
        "Registrations by category",
        "Top five most popular events",
        "Users with no registration",
        "Events above average occupancy",
        "Most-used tags",
        "Events by month",
    ]

    for analysis in required_analyses:
        assert analysis in response.text


def test_static_stylesheet():
    with client:
        response = client.get(
            "/static/css/style.css"
        )

    assert response.status_code == 200
    assert "dashboard-card" in response.text


def test_unknown_route_returns_404():
    with client:
        response = client.get(
            "/route-that-does-not-exist"
        )

    assert response.status_code == 404
    assert "Page not found" in response.text
