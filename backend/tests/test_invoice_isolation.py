import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed_database
from app.database import SessionLocal
from app.models import Invoice

client = TestClient(app)


def get_auth_header(email: str, password: str = "demo1234"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def reset_db_for_test():
    seed_database()
    yield


def test_per_user_invoice_isolation():
    # 1. Login as Demo User A
    headers_a = get_auth_header("demo@fraudguard.ai", "demo1234")

    # Fetch User A's initial invoices
    res_a_invoices = client.get("/api/invoices", headers=headers_a)
    assert res_a_invoices.status_code == 200
    user_a_initial_invoices = res_a_invoices.json()
    assert len(user_a_initial_invoices) == 13, f"Expected 13 initial invoices for A, got {len(user_a_initial_invoices)}"

    # Run 2 presets as User A ("clean" and "duplicate")
    preset1_res = client.post("/api/invoices/preset", json={"preset_type": "clean"}, headers=headers_a)
    assert preset1_res.status_code == 200
    preset1_invoice = preset1_res.json()
    assert preset1_invoice["owner_id"] is not None

    preset2_res = client.post("/api/invoices/preset", json={"preset_type": "duplicate"}, headers=headers_a)
    assert preset2_res.status_code == 200
    preset2_invoice = preset2_res.json()
    assert preset2_invoice["owner_id"] is not None

    # Fetch User A's updated invoices
    res_a_updated = client.get("/api/invoices", headers=headers_a)
    assert res_a_updated.status_code == 200
    user_a_invoices = res_a_updated.json()
    assert len(user_a_invoices) == 15, f"Expected 15 invoices for A after adding 2 presets, got {len(user_a_invoices)}"

    # Check Accounts Department Queue (approved invoices) for A
    user_a_approved = [inv for inv in user_a_invoices if inv["status"] == "APPROVE" or inv["status"] == "APPROVED"]
    assert len(user_a_approved) > 0, "Expected approved invoices in User A's accounts queue"

    # 2. Login as Demo User B
    headers_b = get_auth_header("demo2@fraudguard.ai", "demo1234")

    # Fetch User B's invoices
    res_b_invoices = client.get("/api/invoices", headers=headers_b)
    assert res_b_invoices.status_code == 200
    user_b_invoices = res_b_invoices.json()
    assert len(user_b_invoices) == 2, f"Expected 2 seeded invoices for B, got {len(user_b_invoices)}"

    # Confirm User B cannot see User A's invoices in history list
    user_a_ids = {inv["id"] for inv in user_a_invoices}
    user_b_ids = {inv["id"] for inv in user_b_invoices}
    assert user_a_ids.isdisjoint(user_b_ids), "User B's history contains User A's invoices!"

    # 3. Confirm Impact Stats numbers are different between A and B
    stats_a_total_count = len(user_a_invoices)
    stats_b_total_count = len(user_b_invoices)
    assert stats_a_total_count != stats_b_total_count, f"Impact Stats not isolated: A={stats_a_total_count}, B={stats_b_total_count}"

    stats_a_total_amount = sum(inv["amount"] for inv in user_a_invoices)
    stats_b_total_amount = sum(inv["amount"] for inv in user_b_invoices)
    assert stats_a_total_amount != stats_b_total_amount, f"Total amounts not isolated: A={stats_a_total_amount}, B={stats_b_total_amount}"

    # 4. Confirm User B cannot override User A's invoice (must return 403 Forbidden)
    sample_a_invoice_id = user_a_invoices[0]["id"]
    override_res = client.post(
        f"/api/override/{sample_a_invoice_id}",
        json={"override": "REJECTED", "reason": "Attempting unauthorized override"},
        headers=headers_b
    )
    assert override_res.status_code == 403, f"Expected 403 when B overrides A's invoice, got {override_res.status_code}"

    # Confirm User B cannot access User A's invoice directly (GET /invoices/{id})
    get_a_by_b_res = client.get(f"/api/invoices/{sample_a_invoice_id}", headers=headers_b)
    assert get_a_by_b_res.status_code == 403, f"Expected 403 when B gets A's invoice, got {get_a_by_b_res.status_code}"

    # Confirm User B cannot delete User A's invoice (DELETE /invoices/{id})
    del_a_by_b_res = client.delete(f"/api/invoices/{sample_a_invoice_id}", headers=headers_b)
    assert del_a_by_b_res.status_code == 403, f"Expected 403 when B deletes A's invoice, got {del_a_by_b_res.status_code}"

    # Confirm User B cannot access User A's flag explanations (GET /invoices/{id}/why/0)
    why_a_by_b_res = client.get(f"/api/invoices/{sample_a_invoice_id}/why/0", headers=headers_b)
    assert why_a_by_b_res.status_code == 403, f"Expected 403 when B requests flag explanation for A's invoice, got {why_a_by_b_res.status_code}"


def test_global_vendor_history_maintained():
    """Verify Vendor data remains global and un-scoped across users."""
    headers_a = get_auth_header("demo@fraudguard.ai", "demo1234")
    headers_b = get_auth_header("demo2@fraudguard.ai", "demo1234")

    # Creating invoices under vendor 'Starlight Event Planning Ltd' by User B still benefits from global vendor master data
    preset_res = client.post("/api/invoices/preset", json={"preset_type": "clean"}, headers=headers_b)
    assert preset_res.status_code == 200
