import os
import httpx
import time
from datetime import datetime

BASE = "http://127.0.0.1:8000"

def run_test():
    with httpx.Client() as client:
        # 1. Login/Register
        user = {
            "email": f"test_graph_{int(datetime.utcnow().timestamp())}@fraudguard.local",
            "password": "password123",
            "full_name": "Graph Test User"
        }
        print("Registering user...")
        res = client.post(f'{BASE}/api/auth/register', json=user)
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Reset state to seed Vendor A and Vendor C (rejected invoice with bank 9948201)
        print("Resetting demo state to seed baseline...")
        client.post(f'{BASE}/api/demo/reset', headers=headers)
        
        # 3. Create preset connected_fraud (Suspicious Vendor B using account 9948201)
        print("Creating connected_fraud invoice preset...")
        res = client.post(f'{BASE}/api/invoices/preset', json={"workflow_type": "invoice_fraud", "preset_type": "connected_fraud"}, headers=headers)
        invoice = res.json()
        inv_id = invoice["id"]
        
        # 4. Trigger analysis stream (to calculate deterministic flags)
        print("Running analyze stream...")
        client.get(f'{BASE}/api/invoices/{inv_id}/analyze/stream?token={token}', headers=headers, timeout=60.0)
        
        # 5. Fetch updated invoice details and verify flags
        print("Verifying risk signals on connected_fraud invoice...")
        updated = client.get(f'{BASE}/api/invoices/{inv_id}', headers=headers).json()
        
        print(f"Final Status: {updated['status']}")
        print(f"Risk Score: {updated['risk_score']}")
        
        flags = updated.get("flags_json", "[]")
        print(f"Heuristic Flags: {flags}")
        
        assert "SHARED_BANK_ACCOUNT_ACROSS_VENDORS" in flags, "Missing SHARED_BANK_ACCOUNT_ACROSS_VENDORS flag"
        assert "ENTITY_LINK_TO_PREVIOUS_RISK" in flags, "Missing ENTITY_LINK_TO_PREVIOUS_RISK flag"
        
        # 6. Fetch Graph details
        print("Verifying Graph construction API...")
        graph = client.get(f'{BASE}/api/graph', headers=headers).json()
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        
        print(f"Total Nodes: {len(nodes)}")
        print(f"Total Edges: {len(edges)}")
        
        # We expect a bank account node with mask for 9948201
        bank_node = next((n for n in nodes if n["type"] == "BANK_ACCOUNT" and n["label"] == "****8201"), None)
        assert bank_node is not None, "Bank node for ****8201 missing"
        assert bank_node["risk_level"] == "HIGH", "Bank node for ****8201 should be marked HIGH risk"
        
        print("ALL GRAPH RELATIONSHIP AND RISKS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    run_test()
