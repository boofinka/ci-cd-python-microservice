from datetime import datetime, timezone

from fastapi.testclient import TestClient
from app.main import app, is_shaas_window

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_index_html():
    response = client.get("/")
    assert response.status_code == 200
    assert response.text


def test_is_shaas_window_inside_window():
    assert is_shaas_window(datetime(2026, 7, 3, 15, 30, tzinfo=timezone.utc)) is True


def test_is_shaas_window_outside_window():
    assert is_shaas_window(datetime(2026, 7, 4, 16, 1, tzinfo=timezone.utc)) is False


def test_shaas_endpoint_returns_yes(monkeypatch):
    monkeypatch.setattr("app.main.is_shaas_window", lambda now: True)
    response = client.get("/shaas")
    assert response.status_code == 200
    assert response.text == "Yes"


def test_shaas_endpoint_returns_no(monkeypatch):
    monkeypatch.setattr("app.main.is_shaas_window", lambda now: False)
    response = client.get("/shaas")
    assert response.status_code == 200
    assert response.text == "No"