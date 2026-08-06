import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed_database
from app.database import SessionLocal
from app.models import Vendor

client = TestClient(app)


def login_headers(email="demo@fraudguard.ai", password="demo1234"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def setup_db():
    seed_database()
    yield


def test_clean_vendor_preset_creation():
    headers = login_headers()
    res = client.post(
        "/api/invoices/preset",
        json={"preset_type": "clean_vendor", "workflow_type": "vendor_onboarding"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["workflow_type"] == "vendor_onboarding"
    assert data["vendor_name"] == "Apex CyberSecurity LLC"


def test_cross_workflow_vendor_approval_registers_in_master_db():
    headers = login_headers()
    db = SessionLocal()
    try:
        # Check initial state: "Apex CyberSecurity LLC" is NOT in master Vendor table
        v1 = db.query(Vendor).filter(Vendor.name.ilike("Apex CyberSecurity LLC")).first()
        assert v1 is None

        # Post preset clean_vendor
        res = client.post(
            "/api/invoices/preset",
            json={"preset_type": "clean_vendor", "workflow_type": "vendor_onboarding"},
            headers=headers,
        )
        assert res.status_code == 200
        inv_id = res.json()["id"]

        # Apply human override APPROVE to trigger cross-workflow on_approved hook
        override_res = client.post(
            f"/api/override/{inv_id}",
            json={"override": "APPROVED", "reason": "Verified corporate compliance and tax documentation."},
            headers=headers,
        )
        assert override_res.status_code == 200

        # Verify that "Apex CyberSecurity LLC" is NOW registered in master Vendor database table!
        v2 = db.query(Vendor).filter(Vendor.name.ilike("Apex CyberSecurity LLC")).first()
        assert v2 is not None
        assert v2.is_known is True
        assert v2.tax_id == "US-EIN-99218402"
    finally:
        db.close()
