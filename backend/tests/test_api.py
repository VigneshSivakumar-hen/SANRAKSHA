"""
End-to-end API tests using FastAPI's TestClient against a real (temp
file) SQLite database per test — exercises the actual app, routing, and
middleware, not just individual functions.

Uses FastAPI's dependency_overrides for DB isolation (the standard
pattern) rather than reloading modules, which avoids a real bug that
approach has: other already-imported modules (e.g. app.services.
imd_service, which does `from app.core.config import settings` at
import time) keep referencing the pre-reload objects, so reloading
app.core.config later doesn't actually reach them.
"""

import os
import tempfile
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.services import prediction_service


@pytest.fixture()
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    # Seed the same way the real app does on startup.
    seed_db = TestSessionLocal()
    try:
        prediction_service.seed_if_empty(seed_db)
    finally:
        seed_db.close()

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Cleanup after TestClient has completely shut down.
    app.dependency_overrides.clear()
    engine.dispose()

    # Windows can briefly retain the SQLite file handle.
    try:
        os.unlink(db_path)
    except PermissionError:
        time.sleep(0.1)
        os.unlink(db_path)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_dashboard_seeds_and_returns_locations(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200

    data = resp.json()

    assert len(data) == 5

    assert {loc["location_id"] for loc in data} == {
        "munnar-01",
        "wayanad-02",
        "nilgiris-03",
        "darjeeling-04",
        "shimla-05",
    }


def test_predict_valid_reading(client):
    resp = client.post(
        "/api/predict",
        json={
            "rainfall_mm_24h": 150,
            "soil_moisture_pct": 80,
            "slope_deg": 35,
        },
    )

    assert resp.status_code == 200

    body = resp.json()

    assert body["risk_level"] in {
        "LOW",
        "MODERATE",
        "HIGH",
        "CRITICAL",
    }

    assert 0 <= body["risk_score"] <= 100


def test_predict_rejects_invalid_input(client):
    resp = client.post(
        "/api/predict",
        json={
            "rainfall_mm_24h": -5,
            "soil_moisture_pct": 80,
            "slope_deg": 35,
        },
    )

    assert resp.status_code == 422


def test_sync_requires_admin_key(client):
    resp = client.post("/api/sync/run")

    assert resp.status_code == 401


def test_sync_rejects_wrong_admin_key(client):
    resp = client.post(
        "/api/sync/run",
        headers={
            "X-Admin-Key": "wrong",
        },
    )

    assert resp.status_code == 401


def test_sync_accepts_correct_admin_key(client):
    resp = client.post(
        "/api/sync/run",
        headers={
            "X-Admin-Key": "test-admin-key",
        },
    )

    assert resp.status_code == 200


def test_predict_rate_limit(client):
    """
    20/minute limit on /api/predict — the 21st call in quick succession
    should be rejected.
    """

    payload = {
        "rainfall_mm_24h": 50,
        "soil_moisture_pct": 40,
        "slope_deg": 20,
    }

    statuses = [
        client.post(
            "/api/predict",
            json=payload,
        ).status_code
        for _ in range(25)
    ]

    assert statuses.count(200) <= 20
    assert 429 in statuses


def test_ingest_requires_valid_token(client):
    resp = client.post(
        "/api/ingest",
        json={
            "location_id": "munnar-01",
            "rainfall_mm_24h": 20,
            "soil_moisture_pct": 60,
            "token": "wrong-token",
        },
    )

    assert resp.status_code == 401


def test_ingest_accepts_valid_token(client):
    resp = client.post(
        "/api/ingest",
        json={
            "location_id": "munnar-01",
            "rainfall_mm_24h": 20,
            "soil_moisture_pct": 60,
            "token": "dev-ingest-token",
        },
    )

    assert resp.status_code == 200


def test_history_endpoint(client):
    resp = client.get(
        "/api/locations/munnar-01/history"
    )

    assert resp.status_code == 200
    assert len(resp.json()) >= 1
