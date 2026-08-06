import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import Invoice

client = TestClient(app)


def login_headers():
    res = client.post("/api/auth/login", json={"email": "demo@fraudguard.ai", "password": "demo1234"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def setup_db():
    from app.seed import seed_database
    seed_database()
    yield


def test_healthcheck():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_preset_invoice_creation():
    headers = login_headers()
    response = client.post("/api/invoices/preset", json={"preset_type": "clean"}, headers=headers)
    assert response.status_code == 200
    invoice = response.json()
    assert invoice["vendor_name"] == "Apex Cloud Infrastructure Inc"
    assert invoice["status"] == "PENDING"


def test_duplicate_preset_invoice_creation():
    headers = login_headers()
    response = client.post("/api/invoices/preset", json={"preset_type": "duplicate"}, headers=headers)
    assert response.status_code == 200
    invoice = response.json()
    assert invoice["invoice_number"] == "INV-APEX-1001"


def test_full_agent_pipeline_execution_sync():
    headers = login_headers()
    res = client.post("/api/analyze", json={"invoice_text": "Invoice #INV-TEST-001 from Testing Vendor Ltd amount $55000.00 date 2026-08-05"}, headers=headers)
    assert res.status_code == 200
    res_data = res.json()
    assert "invoice_id" in res_data
    assert "final_decision" in res_data
