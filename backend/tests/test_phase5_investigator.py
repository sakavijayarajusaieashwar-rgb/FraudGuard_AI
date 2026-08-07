import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed_database

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


def _find_invoice_id_by_number(headers, invoice_number):
    res = client.get("/api/invoices", headers=headers)
    assert res.status_code == 200
    invoices = res.json()
    for inv in invoices:
        if inv["invoice_number"] == invoice_number:
            return inv["id"]
    pytest.skip(f"Invoice {invoice_number} not found in seeded data")


def test_investigator_returns_deterministic_risk_score():
    headers = get_auth_header("demo@fraudguard.ai")
    invoice_id = _find_invoice_id_by_number(headers, "INV-EST-001")

    res = client.post(
        f"/api/invoices/{invoice_id}/investigate",
        json={"query": "What is the risk score for this invoice?"},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["response_source"] == "DETERMINISTIC"
    assert "risk score" in body["answer"].lower()
    assert body["confidence_basis"] == "Deterministic database record"
    assert body["evidence"] == [f"Risk score: {int(body['answer'].split()[-1].split('/')[0])}" or body["evidence"]]


def test_investigator_rejects_unsupported_entity_lookup():
    headers = get_auth_header("demo@fraudguard.ai")
    invoice_id = _find_invoice_id_by_number(headers, "INV-EST-001")

    res = client.post(
        f"/api/invoices/{invoice_id}/investigate",
        json={"query": "What is the vendor's headquarters address?"},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["response_source"] == "DETERMINISTIC"
    assert "does not currently have sufficient evidence" in body["answer"]
    assert body["confidence_basis"] == "Unsupported investigator query"
    assert body["evidence"] == []


def test_investigator_trust_profile_is_phase5_deterministic():
    headers = get_auth_header("demo@fraudguard.ai")
    invoice_id = _find_invoice_id_by_number(headers, "INV-EST-001")

    res = client.post(
        f"/api/invoices/{invoice_id}/investigate",
        json={"query": "Show me the entity trust profile for the vendor."},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["response_source"] == "DETERMINISTIC"
    assert "trust rating" in body["answer"].lower()
    assert "Entity Trust Profile" in body["recommended_human_checks"][0]
