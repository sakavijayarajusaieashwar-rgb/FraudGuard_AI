import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed_database

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


def test_clean_expense_preset_creation():
    headers = login_headers()
    res = client.post(
        "/api/invoices/preset",
        json={"preset_type": "clean_expense", "workflow_type": "expense_approval"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["workflow_type"] == "expense_approval"
    assert data["vendor_name"] == "Sarah Jenkins"
    assert data["amount"] == 1250.00


def test_overlimit_expense_preset_creation():
    headers = login_headers()
    res = client.post(
        "/api/invoices/preset",
        json={"preset_type": "overlimit_expense", "workflow_type": "expense_approval"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["workflow_type"] == "expense_approval"
    assert data["vendor_name"] == "Marcus Vance"
    assert data["amount"] == 450.00


def test_duplicate_expense_claim_detection():
    headers = login_headers()
    # Post first claim
    res1 = client.post(
        "/api/invoices/preset",
        json={"preset_type": "clean_expense", "workflow_type": "expense_approval"},
        headers=headers,
    )
    assert res1.status_code == 200

    # Post identical second claim
    res2 = client.post(
        "/api/invoices/preset",
        json={"preset_type": "duplicate_expense", "workflow_type": "expense_approval"},
        headers=headers,
    )
    assert res2.status_code == 200
    claim2 = res2.json()

    # Analyze second claim
    analyze_res = client.post(
        "/api/analyze",
        json={"invoice_text": f"Employee: Sarah Jenkins Date: 2026-08-01 Amount: $1250.00 Category: Travel & Lodging Claim #{claim2['invoice_number']}", "workflow_type": "expense_approval"},
        headers=headers,
    )
    assert analyze_res.status_code == 200
    ans_data = analyze_res.json()
    assert "final_decision" in ans_data
    # Should flag duplicate claim
    signals = ans_data["final_decision"]["risk_signals"]
    rules = [s["rule"] for s in signals]
    assert "DUPLICATE_EXPENSE_CLAIM" in rules or ans_data["final_decision"]["verdict"] in ["REJECT", "ESCALATE"]
