import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.seed import seed_database
from seed_payment_ledger import seed_ledger
from app.llm.provider import UnifiedLLMProvider

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


def _find_invoice_id_by_number(headers, invoice_number):
    res = client.get("/api/invoices", headers=headers)
    assert res.status_code == 200
    invoices = res.json()
    for inv in invoices:
        if inv["invoice_number"] == invoice_number:
            return inv["id"]
    pytest.skip(f"Invoice {invoice_number} not found in seeded data")


def test_payment_investigation_uses_actual_ledger_evidence_and_deterministic_amounts():
    headers = get_auth_header("demo@fraudguard.ai")

    create_res = client.post(
        "/api/invoices/create",
        json={
            "vendor_name": "FraudGuard Corp",
            "invoice_number": "ORD-PARTIAL",
            "total_amount": 50000.00,
            "invoice_date": "2026-08-07",
            "workflow_type": "customer_order",
            "extra_data": {
                "transaction_reference": "REF-PARTIAL"
            }
        },
        headers=headers,
    )
    assert create_res.status_code == 200, create_res.text
    invoice_id = create_res.json()["id"]

    res = client.post(
        f"/api/invoices/{invoice_id}/investigate",
        json={"query": "Was payment verified?"},
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["response_source"] == "DETERMINISTIC"
    assert body["confidence_basis"] == "Deterministic Payment Ledger matching"
    assert any("Ledger match" in evidence for evidence in body["evidence"])
    assert "settled" in body["answer"].lower()

    res2 = client.post(
        f"/api/invoices/{invoice_id}/investigate",
        json={"query": "How much payment was verified?"},
        headers=headers,
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["response_source"] == "DETERMINISTIC"
    assert "47,000" in body2["answer"].replace("$", "")
    assert "3,000" in body2["answer"].replace("$", "")
    assert "PAYMENT_AMOUNT_MISMATCH" in body2["evidence"]

    res3 = client.post(
        f"/api/invoices/{invoice_id}/investigate",
        json={"query": "Why was dispatch blocked?"},
        headers=headers,
    )
    assert res3.status_code == 200
    body3 = res3.json()
    assert body3["response_source"] == "DETERMINISTIC"
    assert body3["confidence_basis"] == "Deterministic Payment Ledger matching"
    assert "blocked" in body3["answer"].lower()


def test_behavioral_investigation_uses_deterministic_phase2_evidence():
    headers = get_auth_header("demo@fraudguard.ai")
    invoice_id = _find_invoice_id_by_number(headers, "INV-VORTEX-771")

    res = client.post(
        f"/api/invoices/{invoice_id}/investigate",
        json={"query": "Why is this amount abnormal?"},
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["response_source"] == "DETERMINISTIC"
    assert "historical average" in body["answer"].lower() or "higher than" in body["answer"].lower()
    assert "AMOUNT_BEHAVIOR_DEVIATION" in body["evidence"] or body["evidence"] == []
    assert body["confidence_basis"] == "Deterministic vendor behavior profile"


def test_graph_investigation_uses_existing_graph_evidence_and_masks_accounts():
    headers = get_auth_header("demo@fraudguard.ai")
    invoice_id = _find_invoice_id_by_number(headers, "INV-EST-001")

    res = client.post(
        f"/api/invoices/{invoice_id}/investigate",
        json={"query": "Has this bank account appeared before?"},
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["response_source"] == "DETERMINISTIC"
    assert any("Known bank account" in evidence or "NEW_VENDOR_BANK_ACCOUNT" in evidence for evidence in body["evidence"])

    evidence_res = client.get(f"/api/invoices/{invoice_id}/evidence", headers=headers)
    assert evidence_res.status_code == 200
    evidence_body = evidence_res.json()
    assert any("****" in edge for edge in evidence_body["related_edges"])
    assert any("REFERENCES" in edge or "USES" in edge or "RECORDED_IN" in edge or "SETTLES_TO" in edge for edge in evidence_body["related_edges"])


def test_tenant_isolation_blocks_investigation_and_evidence_access():
    headers_a = get_auth_header("demo@fraudguard.ai")
    headers_b = get_auth_header("demo2@fraudguard.ai")
    invoice_id = _find_invoice_id_by_number(headers_a, "INV-EST-001")

    res = client.post(
        f"/api/invoices/{invoice_id}/investigate",
        json={"query": "What is the risk score?"},
        headers=headers_b,
    )
    assert res.status_code == 404

    res2 = client.get(f"/api/invoices/{invoice_id}/evidence", headers=headers_b)
    assert res2.status_code == 404

    res3 = client.post(
        f"/api/invoices/{invoice_id}/investigate",
        json={"query": "Show me the entity trust profile for the vendor."},
        headers=headers_b,
    )
    assert res3.status_code == 404


def test_unsupported_question_refuses_and_does_not_use_gemini():
    headers = get_auth_header("demo@fraudguard.ai")
    invoice_id = _find_invoice_id_by_number(headers, "INV-EST-001")

    with patch("app.main.llm_provider.get_env_vars", return_value=("fake_key", "", "auto", False)):
        with patch("app.main.llm_provider._call_gemini_with_retry", new_callable=AsyncMock) as mock_gemini:
            res = client.post(
                f"/api/invoices/{invoice_id}/investigate",
                json={"query": "Where does the vendor CEO live?"},
                headers=headers,
            )
    assert res.status_code == 200
    body = res.json()
    assert body["response_source"] == "DETERMINISTIC"
    assert "does not currently have sufficient evidence" in body["answer"]
    assert mock_gemini.await_count == 0


@pytest.mark.parametrize("mock_exception", [Exception("429"), asyncio.TimeoutError("timeout"), json.JSONDecodeError("msg", "doc", 0)])
def test_gemini_fallback_resilience(mock_exception):
    headers = get_auth_header("demo@fraudguard.ai")
    invoice_id = _find_invoice_id_by_number(headers, "INV-EST-001")

    async def raise_error(*args, **kwargs):
        raise mock_exception

    with patch("app.main.llm_provider.generate_json", new_callable=AsyncMock, side_effect=raise_error) as mock_generate_json:
        res = client.post(
            f"/api/invoices/{invoice_id}/investigate",
            json={"query": "Summarize the invoice evidence for decision support."},
            headers=headers,
        )
    assert res.status_code == 200
    body = res.json()
    assert body["response_source"] == "FALLBACK"
    assert "AI explanation temporarily unavailable" in body["answer"]
    assert "AI unavailable" in body["confidence_basis"] or "deterministic evidence intact" in body["confidence_basis"].lower()
    assert isinstance(body["evidence"], list)


def test_gemini_call_count_for_deterministic_and_ai_questions():
    headers = get_auth_header("demo@fraudguard.ai")
    invoice_id = _find_invoice_id_by_number(headers, "INV-EST-001")

    with patch("app.main.llm_provider.generate_json", new_callable=AsyncMock, return_value={
        "answer": "Deterministic route should be used for risk score queries.",
        "evidence": ["Risk score: 0"],
        "confidence_basis": "Deterministic database record",
        "recommended_human_checks": ["Review risk category breakdown if score is elevated."]
    }) as mock_generate_json:
        res_det = client.post(
            f"/api/invoices/{invoice_id}/investigate",
            json={"query": "What is the risk score for this invoice?"},
            headers=headers,
        )
    assert res_det.status_code == 200
    assert res_det.json()["response_source"] == "DETERMINISTIC"
    assert mock_generate_json.await_count == 0

    ai_result = {
        "answer": "This is an AI-crafted summary based on provided evidence.",
        "evidence": ["Risk signal summary"],
        "confidence_basis": "AI synthesis from evidence",
        "recommended_human_checks": ["Use the deterministic evidence listed above."]
    }

    with patch("app.main.llm_provider.generate_json", new_callable=AsyncMock, return_value=ai_result) as mock_generate_json:
        res_ai = client.post(
            f"/api/invoices/{invoice_id}/investigate",
            json={"query": "Summarize the invoice evidence for decision support."},
            headers=headers,
        )
    assert res_ai.status_code == 200
    assert res_ai.json()["response_source"] == "AI"
    assert mock_generate_json.await_count == 1


def test_evidence_endpoint_returns_sealed_and_masked_data():
    headers = get_auth_header("demo@fraudguard.ai")
    invoice_id = _find_invoice_id_by_number(headers, "INV-EST-001")

    res = client.get(f"/api/invoices/{invoice_id}/evidence", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["invoice_id"] == invoice_id
    assert "risk_signals" in body
    assert "primary_findings" in body
    assert "related_edges" in body
    assert "recommended_action" in body
    if body["payment_evidence"]:
        assert body["payment_evidence"]["ledger_amount"] is not None
    assert any("****" in edge for edge in body["related_edges"])
    assert any("REFERENCES" in edge or "USES" in edge or "RECORDED_IN" in edge or "SETTLES_TO" in edge for edge in body["related_edges"])
