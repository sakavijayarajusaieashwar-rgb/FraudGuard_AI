import os
import time
import httpx
from datetime import datetime

BASE = 'http://127.0.0.1:8003'
client = httpx.Client()

# Unique user
ts = int(time.time())
user = {'email': f'userA{ts}@fraudguard.local', 'password':'Secret123!', 'full_name':'User A'}
res = client.post(f'{BASE}/api/auth/register', json=user)
print('register A', res.status_code)
token = res.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

presets = [
    ('clean', 'From: Apex Cloud Infrastructure Inc\nInvoice Number: INV-APEX-1001\nDate: 2026-07-01\nTotal Amount: $1450.00', 'APPROVE'),
    ('duplicate', 'From: Global Office Supplies Co\nInvoice Number: INV-DUP-9901\nDate: 2026-07-28\nTotal Amount: $3200.00', 'REJECT'),
    ('suspicious_amount', 'From: Vortex Digital Marketing Consultants\nInvoice Number: INV-VORTEX-771\nDate: 2026-07-29\nTotal Amount: $65000.00', 'ESCALATE'),
    ('typosquat', 'From: Apex C1oud Infrastructure Inc\nInvoice Number: INV-APEX-2004\nDate: 2026-08-01\nTotal Amount: $1450.00', 'ESCALATE')
]

results = []
for key, text, expected in presets:
    # Create preset entry
    rr = client.post(f'{BASE}/api/invoices/preset', json={'preset_type': key}, headers=headers)
    print('preset create', key, rr.status_code)
    # Run analysis
    an = client.post(f'{BASE}/api/analyze', json={'invoice_text': text}, headers=headers, timeout=20.0)
    fd = an.json().get('final_decision', {})
    print('analyze', key, an.status_code, fd.get('verdict'), fd.get('confidence'), fd.get('risk_score'))
    ok = fd.get('verdict') == expected
    results.append((key, fd.get('verdict'), fd.get('confidence'), fd.get('risk_score'), ok))
    time.sleep(0.5)

# Check invoices list for approved invoices
inv_list = client.get(f'{BASE}/api/invoices', headers=headers).json()
approved = [i for i in inv_list if i.get('status')=='APPROVE']
print('approved count', len(approved))

# Re-run trace test: pick first invoice id
if inv_list:
    inv_id = inv_list[0]['id']
    an2 = client.post(f'{BASE}/api/analyze', json={'invoice_text': f"From: {inv_list[0]['vendor_name']}\nInvoice Number: {inv_list[0]['invoice_number']}\nDate: {inv_list[0]['invoice_date']}\nTotal Amount: ${inv_list[0]['amount']}"}, headers=headers, timeout=20.0)
    print('re-run trace', an2.status_code, an2.json().get('final_decision'))

# Login as user B
userb = {'email': f'userB{ts}@fraudguard.local', 'password':'Secret123!', 'full_name':'User B'}
resb = client.post(f'{BASE}/api/auth/register', json=userb)
print('register B', resb.status_code)
tokenb = resb.json().get('access_token')
headersb = {'Authorization': f'Bearer {tokenb}'}
inv_list_b = client.get(f'{BASE}/api/invoices', headers=headersb).json()
print('user A invoices', len(inv_list), 'user B invoices', len(inv_list_b))

print('\nRESULTS:')
for r in results:
    print(r)

print('approved sample:', [ (i['id'], i['invoice_number'], i['status']) for i in approved[:5] ])
