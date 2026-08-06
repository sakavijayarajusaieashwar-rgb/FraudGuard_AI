import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed_database
from app.workflows import get_workflow, list_workflows

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


def test_list_workflows_endpoint():
    res = client.get("/api/workflows")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    wf_keys = [w["workflow_type"] for w in data]
    assert "invoice_fraud" in wf_keys


def test_preset_creation_default_workflow_type():
    headers = login_headers()
    res = client.post("/api/invoices/preset", json={"preset_type": "clean"}, headers=headers)
    assert res.status_code == 200
    inv = res.json()
    assert inv["workflow_type"] == "invoice_fraud"
    assert inv["vendor_name"] == "Apex Cloud Infrastructure Inc"


def test_list_invoices_with_workflow_filter():
    headers = login_headers()
    # List all
    res_all = client.get("/api/invoices", headers=headers)
    assert res_all.status_code == 200
    all_invs = res_all.json()
    assert len(all_invs) == 13

    # Filter invoice_fraud
    res_filtered = client.get("/api/invoices?workflow_type=invoice_fraud", headers=headers)
    assert res_filtered.status_code == 200
    filtered = res_filtered.json()
    assert len(filtered) == 13
