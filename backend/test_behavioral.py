import os
import time
import httpx
from datetime import datetime

BASE = "http://127.0.0.1:8000"

def run_test():
    with httpx.Client() as client:
        # 1. Login
        user = {
            "email": f"test_beh_{int(datetime.utcnow().timestamp())}@fraudguard.local",
            "password": "password123",
            "full_name": "Test User"
        }
        res = client.post(f'{BASE}/api/auth/register', json=user)
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Trigger preset
        print("Triggering behavioral_anomaly preset...")
        res = client.post(f'{BASE}/api/invoices/preset', json={"workflow_type": "invoice_fraud", "preset_type": "behavioral_anomaly"}, headers=headers)
        invoice = res.json()
        inv_id = invoice["id"]
        print(f"Created Invoice ID: {inv_id}")

        # 3. Analyze
        print("Analyzing...")
        an = client.get(f'{BASE}/api/invoices/{inv_id}/analyze/stream?token={token}', headers=headers, timeout=60.0)
        print(f"Stream HTTP Status: {an.status_code}")

        # 4. Check results
        final = client.get(f'{BASE}/api/invoices/{inv_id}', headers=headers).json()
        print(f"Final Verdict: {final['status']}")
        print(f"Risk Score: {final['risk_score']}")
        print(f"Flags: {final['flags_json']}")
        
        extra = final.get("extra_data", {})
        print(f"Category Scores: {extra.get('category_scores')}")

if __name__ == "__main__":
    run_test()
