import time
import json
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

login_res = client.post('/api/auth/login', json={'email': 'demo@fraudguard.ai', 'password': 'demo1234'})
assert login_res.status_code == 200, login_res.text
headers = {'Authorization': f"Bearer {login_res.json()['access_token']}"}

print('=== BACKEND HEALTH ===')
for path in ['/api/health', '/docs', '/openapi.json']:
    resp = client.get(path, headers=headers if path.startswith('/api/') else None)
    print(path, resp.status_code)
    if path == '/api/health':
        print('health body', resp.json())
    if path == '/openapi.json':
        openapi = resp.json()
        print('has /api/analyze', '/api/analyze' in openapi['paths'])
        print('has /api/invoices', '/api/invoices' in openapi['paths'])
        print('has /api/override/{invoice_id}', any('/api/override/{invoice_id}' == p for p in openapi['paths']))

print('\n=== DB COUNTS ===')
db_path = Path('fraudguard.db')
print('db path', db_path.resolve())
print('exists', db_path.exists())
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('SELECT count(*) FROM vendors')
print('vendors count', c.fetchone()[0])
c.execute('SELECT count(*) FROM invoices')
print('invoices count', c.fetchone()[0])
conn.close()

cases = [
    ('clean', 'Invoice From: Acme Software Solutions LLC\nInvoice Number: INV-ACME-999\nDate: 2026-07-20\nTotal Amount: $5,000.00\nLine Items:\n- Annual Software Maintenance'),
    ('fraud', 'Invoice From: Acme Corp.\nInvoice Number: INV-ACME-9999\nDate: 2026-07-20\nTotal Amount: $75,000.00\nLine Items:\n- Enterprise software license'),
    ('duplicate', 'Invoice From: Global Office Supplies Co\nInvoice Number: INV-DUP-9901\nDate: 2026-07-28\nTotal Amount: $3,200.00\nLine Items:\n- Executive chairs'),
]

print('\n=== ANALYZE TEST CASES ===')
for name, text in cases:
    t0 = time.perf_counter()
    resp = client.post('/api/analyze', json={'invoice_text': text}, headers=headers)
    duration = time.perf_counter() - t0
    print('\nCASE', name, 'status', resp.status_code, 'duration', f'{duration:.2f}s')
    try:
        data = resp.json()
    except Exception as e:
        print('JSON error', e, resp.text)
        continue
    print('final_decision', data.get('final_decision'))
    trace = data.get('trace')
    print('trace length', len(trace) if trace else None)
    if trace:
        for entry in trace:
            print('  entry:', entry.get('agent'), entry.get('step'), entry.get('status'))
    print('full json keys', list(data.keys()))

print('\n=== ERROR HANDLING ===')
for desc, payload in [('empty', {'invoice_text': ''}), ('garbled', {'invoice_text': 'asdflkj qwer poiuz 12345 !!! ???'})]:
    resp = client.post('/api/analyze', json=payload, headers=headers)
    print(desc, 'status', resp.status_code)
    print(resp.text)

print('\n=== OVERRIDE CHECK ===')
list_resp = client.get('/api/invoices', headers=headers)
print('list status', list_resp.status_code)
invoices = list_resp.json()
print('invoice count', len(invoices))
if invoices:
    inv_id = invoices[0]['id']
    print('using invoice id', inv_id)
    override_resp = client.post(f'/api/override/{inv_id}', json={'override': 'REJECTED', 'reason': 'Automated test override'}, headers=headers)
    print('override status', override_resp.status_code)
    print('override body', override_resp.json())
    after = client.get(f'/api/invoices/{inv_id}', headers=headers)
    print('updated invoice status', after.json().get('status'))
else:
    print('no invoices available to override')
