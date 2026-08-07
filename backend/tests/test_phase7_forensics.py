import json
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed_database
from seed_payment_ledger import seed_ledger
from app.models import Invoice, PurchaseOrder, GoodsReceipt, User

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


def test_clean_document_forensics_verification():
    headers = get_auth_header("demo@fraudguard.ai")
    res = client.post(
        "/api/invoices/preset",
        json={"preset_type": "clean_three_way", "workflow_type": "invoice_fraud"},
        headers=headers,
    )
    assert res.status_code == 200
    inv_id = res.json()["id"]

    # Retrieve evidence and check forensics
    res_ev = client.get(f"/api/invoices/{inv_id}/evidence", headers=headers)
    assert res_ev.status_code == 200
    body = res_ev.json()
    
    forensics = body["document_forensics"]
    assert forensics is not None
    assert forensics["forensic_status"] == "CONSISTENT"
    assert forensics["comparison_vendor"] == "MATCH"
    assert forensics["comparison_amount"] == "MATCH"
    assert len(forensics["forensic_signals"]) == 0


def test_bank_account_tampering_hero_scenario():
    headers = get_auth_header("demo@fraudguard.ai")
    
    # 1. Create a bank instruction tampering preset invoice
    res = client.post(
        "/api/invoices/preset",
        json={"preset_type": "payment_tampering", "workflow_type": "invoice_fraud"},
        headers=headers,
    )
    assert res.status_code == 200
    inv_id = res.json()["id"]

    # 2. Get evidence
    res_ev = client.get(f"/api/invoices/{inv_id}/evidence", headers=headers)
    assert res_ev.status_code == 200
    body = res_ev.json()
    
    forensics = body["document_forensics"]
    assert forensics is not None
    # Historical bank account in seed is 123459271 (ending in 9271)
    # Tampered bank account requests payment to 123454418 (ending in 4418)
    assert forensics["claimed_bank"] == "****4418"
    assert forensics["verified_bank"] == "****9271"
    assert forensics["comparison_bank"] == "MISMATCH"
    assert "INVOICE_BANK_ACCOUNT_MISMATCH" in forensics["forensic_signals"]
    
    # Linked to previous rejected entity (INV-REJ-999 seeds 123454418 as rejected)
    assert "ENTITY_LINK_TO_PREVIOUS_RISK" in forensics["forensic_signals"]
    assert forensics["forensic_status"] == "HIGH_RISK"
    assert "HOLD" in forensics["recommended_action"]


def test_arithmetic_manipulation_detection():
    headers = get_auth_header("demo@fraudguard.ai")
    res = client.post(
        "/api/invoices/preset",
        json={"preset_type": "arithmetic_manipulation", "workflow_type": "invoice_fraud"},
        headers=headers,
    )
    assert res.status_code == 200
    inv_id = res.json()["id"]

    res_ev = client.get(f"/api/invoices/{inv_id}/evidence", headers=headers)
    assert res_ev.status_code == 200
    body = res_ev.json()
    
    forensics = body["document_forensics"]
    assert forensics is not None
    assert "INVOICE_TOTAL_ARITHMETIC_MISMATCH" in forensics["forensic_signals"]
    assert len(forensics["metadata"]["arithmetic_errors"]) > 0
    assert forensics["forensic_status"] == "REVIEW"


def test_po_vendor_mismatch_detection():
    headers = get_auth_header("demo@fraudguard.ai")
    res = client.post(
        "/api/invoices/preset",
        json={"preset_type": "po_vendor_mismatch", "workflow_type": "invoice_fraud"},
        headers=headers,
    )
    assert res.status_code == 200
    inv_id = res.json()["id"]

    res_ev = client.get(f"/api/invoices/{inv_id}/evidence", headers=headers)
    assert res_ev.status_code == 200
    body = res_ev.json()
    
    forensics = body["document_forensics"]
    assert forensics is not None
    assert "PO_VENDOR_MISMATCH" in forensics["forensic_signals"]
    assert forensics["comparison_vendor"] == "MISMATCH"
    assert forensics["forensic_status"] == "HIGH_RISK"


def test_duplicate_reference_and_hash_duplicate():
    headers = get_auth_header("demo@fraudguard.ai")

    import io
    
    with patch("app.main.extraction_agent.extract", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = {
            "invoice_number": "INV-APEX-DUP",
            "vendor_name": "Apex Cloud Infrastructure Inc",
            "amount": 1520.00,
            "invoice_date": "2026-08-01",
            "bank_account_number": "123459271",
            "routing_number": "998877665",
            "line_items": [
                "Kubernetes Dedicated Cluster Nodes: $1,100.00",
                "Bandwidth Egress & Network Load Balancer: $420.00"
            ]
        }
        res1 = client.post(
            "/api/invoices/upload-document",
            files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 mock pdf contents"), "application/pdf")},
            data={"workflow_type": "invoice_fraud"},
            headers=headers,
        )
        assert res1.status_code == 200
        inv_id1 = res1.json()["id"]

        res2 = client.post(
            "/api/invoices/upload-document",
            files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 mock pdf contents"), "application/pdf")},
            data={"workflow_type": "invoice_fraud"},
            headers=headers,
        )
        assert res2.status_code == 200
        inv_id2 = res2.json()["id"]

    # Verify that the second document raises DOCUMENT_HASH_DUPLICATE
    res_ev2 = client.get(f"/api/invoices/{inv_id2}/evidence", headers=headers)
    assert res_ev2.status_code == 200
    body2 = res_ev2.json()
    
    forensics2 = body2["document_forensics"]
    assert forensics2 is not None
    assert "DOCUMENT_HASH_DUPLICATE" in forensics2["forensic_signals"]
    assert forensics2["forensic_status"] == "HIGH_RISK"


def test_false_positive_safety():
    headers = get_auth_header("demo@fraudguard.ai")
    
    # 1. New legitimate invoice number does NOT trigger duplicate
    res1 = client.post(
        "/api/invoices/create",
        json={"vendor_name": "Acme Corp", "total_amount": 100.0, "invoice_number": "INV-NEW-UNIQUE-1"},
        headers=headers,
    )
    res2 = client.post(
        "/api/invoices/create",
        json={"vendor_name": "Acme Corp", "total_amount": 100.0, "invoice_number": "INV-NEW-UNIQUE-2"},
        headers=headers,
    )
    
    ev_res = client.get(f"/api/invoices/{res2.json()['id']}/evidence", headers=headers)
    assert "DUPLICATE_INVOICE_REFERENCE" not in ev_res.json()["document_forensics"]["forensic_signals"]
    
    # 2. Missing metadata alone does not trigger high risk/fraud
    # Custom create has no metadata
    assert ev_res.json()["document_forensics"]["forensic_status"] != "HIGH_RISK"


def test_deterministic_investigator_questions_require_zero_llm_calls():
    headers = get_auth_header("demo@fraudguard.ai")
    res = client.post(
        "/api/invoices/preset",
        json={"preset_type": "payment_tampering", "workflow_type": "invoice_fraud"},
        headers=headers,
    )
    assert res.status_code == 200
    inv_id = res.json()["id"]

    # Test "What bank account is on the invoice?"
    q_res = client.post(
        f"/api/invoices/{inv_id}/investigate",
        json={"query": "What bank account is on the invoice?"},
        headers=headers,
    )
    assert q_res.status_code == 200
    body = q_res.json()
    assert body["response_source"] == "DETERMINISTIC"
    assert "****4418" in body["answer"]

    # Test "What bank account was previously verified?"
    q_res2 = client.post(
        f"/api/invoices/{inv_id}/investigate",
        json={"query": "What bank account was previously verified?"},
        headers=headers,
    )
    assert q_res2.status_code == 200
    body2 = q_res2.json()
    assert body2["response_source"] == "DETERMINISTIC"
    assert "****9271" in body2["answer"]

    # Test "Did the bank account change?"
    q_res3 = client.post(
        f"/api/invoices/{inv_id}/investigate",
        json={"query": "Did the bank account change?"},
        headers=headers,
    )
    assert q_res3.status_code == 200
    body3 = q_res3.json()
    assert body3["response_source"] == "DETERMINISTIC"
    assert "Yes" in body3["answer"]


def test_tenant_isolation_restrictions():
    headers_a = get_auth_header("demo@fraudguard.ai")
    headers_b = get_auth_header("demo2@fraudguard.ai")
    
    # Tenant A creates invoice
    res_a = client.post(
        "/api/invoices/preset",
        json={"preset_type": "payment_tampering", "workflow_type": "invoice_fraud"},
        headers=headers_a,
    )
    assert res_a.status_code == 200
    inv_id_a = res_a.json()["id"]

    # Tenant B attempts to fetch Tenant A's forensics evidence -> 404
    res_ev_b = client.get(f"/api/invoices/{inv_id_a}/evidence", headers=headers_b)
    assert res_ev_b.status_code == 404

    # Tenant B attempts to run investigator query -> 404
    res_q_b = client.post(
        f"/api/invoices/{inv_id_a}/investigate",
        json={"query": "Did the bank account change?"},
        headers=headers_b,
    )
    assert res_q_b.status_code == 404


def test_tenant_po_isolation():
    headers_b = get_auth_header("demo2@fraudguard.ai")
    
    # Tenant B submits invoice referencing Tenant A's PO (PO-APEX-992)
    res = client.post(
        "/api/invoices/create",
        json={
            "vendor_name": "Apex Cloud Infrastructure Inc",
            "invoice_number": "INV-ISOLATION-PO",
            "total_amount": 1450.00,
            "invoice_date": "2026-07-05",
            "workflow_type": "invoice_fraud",
            "extra_data": {
                "po_number": "PO-APEX-992"
            }
        },
        headers=headers_b,
    )
    assert res.status_code == 200
    inv_id = res.json()["id"]

    res_ev = client.get(f"/api/invoices/{inv_id}/evidence", headers=headers_b)
    assert res_ev.status_code == 200
    body = res_ev.json()
    
    # It should say MISSING_PURCHASE_ORDER since Tenant B cannot see Tenant A's PO!
    # And there shouldn't be three_way_match
    assert body["document_forensics"] is not None
    assert "MISSING_PURCHASE_ORDER" in body["document_forensics"]["forensic_signals"]
    assert body["document_forensics"]["three_way_match"] is None
