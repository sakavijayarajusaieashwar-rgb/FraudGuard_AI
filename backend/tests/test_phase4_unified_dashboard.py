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


def test_unified_dashboard_multi_workflow_stats():
    headers_a = login_headers("demo@fraudguard.ai")
    headers_b = login_headers("demo2@fraudguard.ai")

    # User A creates items across all 3 workflow types
    res_inv = client.post("/api/invoices/preset", json={"preset_type": "clean", "workflow_type": "invoice_fraud"}, headers=headers_a)
    assert res_inv.status_code == 200

    res_exp = client.post("/api/invoices/preset", json={"preset_type": "clean_expense", "workflow_type": "expense_approval"}, headers=headers_a)
    assert res_exp.status_code == 200

    res_ven = client.post("/api/invoices/preset", json={"preset_type": "clean_vendor", "workflow_type": "vendor_onboarding"}, headers=headers_a)
    assert res_ven.status_code == 200

    # Query all records for User A
    res_a_all = client.get("/api/invoices", headers=headers_a)
    assert res_a_all.status_code == 200
    items_a = res_a_all.json()
    assert len(items_a) == 16  # 13 seeded + 3 new

    # Query expense_approval for User A
    res_a_exp = client.get("/api/invoices?workflow_type=expense_approval", headers=headers_a)
    assert res_a_exp.status_code == 200
    assert len(res_a_exp.json()) == 1

    # Verify per-user isolation: User B cannot see User A's expense or vendor items
    res_b_all = client.get("/api/invoices", headers=headers_b)
    assert res_b_all.status_code == 200
    items_b = res_b_all.json()
    assert len(items_b) == 2

    # User B cannot view User A's expense record directly
    exp_id = res_exp.json()["id"]
    res_b_get_exp = client.get(f"/api/invoices/{exp_id}", headers=headers_b)
    assert res_b_get_exp.status_code == 403
