import time
import httpx
from datetime import datetime

BASE = 'http://127.0.0.1:8000'
client = httpx.Client()

ts = int(time.time())
user = {'email': f'test_order_{ts}@fraudguard.local', 'password':'Secret123!', 'full_name':'Test User'}
res = client.post(f'{BASE}/api/auth/register', json=user)
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
    # Get preset
    rr = client.post(f'{BASE}/api/invoices/preset', json={'preset_type': p, 'workflow_type': 'customer_order'}, headers=headers)
    print(f'Preset {p}:', rr.status_code)
    
    # Run analyze stream API
    inv_id = rr.json()['id']
    print(f"Running analysis for invoice ID {inv_id}")
    
    an = client.get(f'{BASE}/api/invoices/{inv_id}/analyze/stream?token={token}', headers=headers, timeout=30.0)
    print(f'Analysis stream HTTP Status:', an.status_code)
    
    # Check final result by getting invoice details
    time.sleep(1)
    inv_res = client.get(f'{BASE}/api/invoices/{inv_id}', headers=headers)
    inv = inv_res.json()
    print(f"Verdict for {p}: {inv.get('status')} - {inv.get('verdict_summary')}")
    print("-" * 50)
