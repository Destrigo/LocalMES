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


def test_custom_fields_add_only_and_validation(client):
    client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})

    # Create a required select field on customer
    r = client.post(
        "/api/v1/field-definitions",
        json={
            "entity": "customer",
            "label": "Segment",
            "key": "segment",
            "field_type": "select",
            "required": True,
            "options": ["SME", "Enterprise"],
        },
    )
    assert r.status_code == 200, r.text
    fid = r.json()["id"]
    assert r.json()["key"] == "segment"

    # Cannot hard-delete
    assert client.delete(f"/api/v1/field-definitions/{fid}").status_code == 405

    # Create without required custom field fails
    bad = client.post(
        "/api/v1/customers",
        json={"company_name": "No Segment Co", "customer_code": "NS1"},
    )
    assert bad.status_code == 400

    # Create with valid custom field
    ok = client.post(
        "/api/v1/customers",
        json={
            "company_name": "Segment Co",
            "customer_code": "SEG1",
            "custom_fields": {"segment": "SME"},
        },
    )
    assert ok.status_code == 200
    assert ok.json()["custom_fields"]["segment"] == "SME"
    cid = ok.json()["id"]

    # Options are add-only
    shrink = client.patch(
        f"/api/v1/field-definitions/{fid}",
        json={"options": ["SME"]},
    )
    assert shrink.status_code == 400

    grow = client.patch(
        f"/api/v1/field-definitions/{fid}",
        json={"options": ["SME", "Enterprise", "Public"]},
    )
    assert grow.status_code == 200
    assert "Public" in grow.json()["options"]

    # Deactivate, then cannot write; historical value remains
    client.patch(f"/api/v1/field-definitions/{fid}", json={"active": False})
    blocked = client.patch(
        f"/api/v1/customers/{cid}",
        json={"custom_fields": {"segment": "Public"}},
    )
    assert blocked.status_code == 400
    still = client.get(f"/api/v1/customers/{cid}")
    assert still.json()["custom_fields"]["segment"] == "SME"

    # Unknown key rejected
    unk = client.patch(
        f"/api/v1/customers/{cid}",
        json={"company_name": "Segment Co 2"},
    )
    assert unk.status_code == 200
