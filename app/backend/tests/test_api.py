"""API smoke tests for LocalMES."""

from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# Isolate DB before importing app
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["MES_DATABASE_PATH"] = _tmp.name
os.environ["MES_DEV"] = "1"
os.environ["MES_SECRET_KEY"] = "test-secret"

from main import app  # noqa: E402
from database import init_db  # noqa: E402


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["app"] == "LocalMES"


def test_login_and_me(client):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})
    assert r.status_code == 200
    assert r.json()["username"] == "admin"
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200


def test_customers_crud(client):
    client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})
    r = client.post(
        "/api/v1/customers",
        json={"company_name": "Acme", "customer_code": "ACM", "external_id": "ext-1"},
    )
    assert r.status_code == 200
    cid = r.json()["id"]
    # upsert by external_id
    r2 = client.post(
        "/api/v1/customers",
        json={"company_name": "Acme Updated", "customer_code": "ACM", "external_id": "ext-1"},
    )
    assert r2.status_code == 200
    assert r2.json()["id"] == cid
    assert r2.json()["company_name"] == "Acme Updated"
    lst = client.get("/api/v1/customers")
    assert lst.status_code == 200
    body = lst.json()
    rows = body["items"] if isinstance(body, dict) else body
    assert any(x["id"] == cid for x in rows)


def test_unauthenticated_denied(client):
    # fresh client without login cookies
    with TestClient(app) as c:
        r = c.get("/api/v1/customers")
        assert r.status_code == 401
