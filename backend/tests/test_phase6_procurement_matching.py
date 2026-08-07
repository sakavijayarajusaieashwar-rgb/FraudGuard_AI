import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed_database
from seed_payment_ledger import seed_ledger

client = TestClient(app)


def get_auth_header(email: str, password: str = "demo1234"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def reset_db_for_test():
    seed_database()
    seed_ledger()
    yield


def test_procurement_three_way_match_detects_po_and_goods_receipt():
    headers = get_auth_header("demo@fraudguard.ai")

    create_res = client.post(
        "/api/invoices/create",
        json={
            "vendor_name": "Apex Cloud Infrastructure Inc",
            "invoice_number": "INV-APEX-992-TEST",
            "total_amount": 1450.00,
            "invoice_date": "2026-07-05",
            "workflow_type": "invoice_fraud",
            "extra_data": {
                "po_number": "PO-APEX-992",
                "line_items": [
                    "Kubernetes Dedicated Cluster Nodes: $1,100.00",
                    "Bandwidth Egress & Network Load Balancer: $420.00"
                ]
            }
        },
        headers=headers,
    )
    assert create_res.status_code == 200, create_res.text
    invoice_id = create_res.json()["id"]

    res = client.post(
        f"/api/invoices/{invoice_id}/investigate",
        json={"query": "Does this invoice match the purchase order and goods receipt?"},
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["response_source"] == "DETERMINISTIC"
    assert "PURCHASE_ORDER_FOUND" in body["evidence"]
    assert "GOODS_RECEIPT_CONFIRMED" in body["evidence"]
    assert "PO-APEX-992" in body["answer"]


def test_procurement_amount_mismatch_flag_for_invoice_po():
    headers = get_auth_header("demo@fraudguard.ai")

    create_res = client.post(
        "/api/invoices/create",
        json={
            "vendor_name": "Apex Cloud Infrastructure Inc",
            "invoice_number": "INV-APEX-992-MISMATCH",
            "total_amount": 1550.00,
            "invoice_date": "2026-07-05",
            "workflow_type": "invoice_fraud",
            "extra_data": {
                "po_number": "PO-APEX-992",
                "line_items": [
                    "Kubernetes Dedicated Cluster Nodes: $1,100.00",
                    "Bandwidth Egress & Network Load Balancer: $420.00"
                ]
            }
        },
        headers=headers,
    )
    assert create_res.status_code == 200, create_res.text
    invoice_id = create_res.json()["id"]

    res = client.post(
        f"/api/invoices/{invoice_id}/investigate",
        json={"query": "Does the invoice amount match the referenced PO?"},
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["response_source"] == "DETERMINISTIC"
    assert "PO_AMOUNT_MISMATCH" in body["evidence"]
    assert "differs from po amount" in body["answer"].lower()
