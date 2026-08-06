import time
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ts = int(time.time())
user = {'email': f'test_order_{ts}@fraudguard.local', 'password':'Secret123!', 'full_name':'Test User'}
res = client.post('/api/auth/register', json=user)
print('Register:', res.status_code)
token = res.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

presets = [
    'clean_order',
    'fake_payment',
    'partial_payment',
    'reused_transaction',
    'wrong_order',
    'wrong_beneficiary',
    'unsettled_payment'
]

for p in presets:
    rr = client.post('/api/invoices/preset', json={'preset_type': p, 'workflow_type': 'customer_order'}, headers=headers)
    print(f'Preset {p}:', rr.status_code)

    inv_id = rr.json()['id']
    invoice_text = rr.json().get('invoice_text') or ''
    print(f"Running analysis for invoice ID {inv_id}")

    an = client.post('/api/analyze', json={'invoice_text': invoice_text, 'workflow_type': 'customer_order'}, headers=headers)
    print(f'Analysis HTTP Status:', an.status_code)

    time.sleep(1)
    inv_res = client.get(f'/api/invoices/{inv_id}', headers=headers)
    inv = inv_res.json()
    print(f"Verdict for {p}: {inv.get('status')} - {inv.get('verdict_summary')}")
    print("-" * 50)
