import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath('.'))
from app.main import app

client = TestClient(app)

user = {
    'email': 'verify@fraudguard.local',
    'password': 'Secret123!',
    'full_name': 'Verify User'
}
res = client.post('/api/auth/register', json=user)
print('register', res.status_code, res.text)
if res.status_code != 200:
    raise SystemExit(1)

token = res.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

preset_texts = {
    'clean': 'From: Apex Cloud Infrastructure Inc\nInvoice Number: INV-APEX-1001\nDate: 2026-07-01\nTotal Amount: $1450.00',
    'duplicate': 'From: Global Office Supplies Co\nInvoice Number: INV-DUP-9901\nDate: 2026-07-28\nTotal Amount: $3200.00',
    'suspicious_amount': 'From: Vortex Digital Marketing Consultants\nInvoice Number: INV-VORTEX-771\nDate: 2026-07-29\nTotal Amount: $65000.00',
    'typosquat': 'From: Apex C1oud Infrastructure Inc\nInvoice Number: INV-APEX-2004\nDate: 2026-08-01\nTotal Amount: $1450.00'
}

for name, text in preset_texts.items():
    response = client.post('/api/analyze', json={'invoice_text': text}, headers=headers)
    print('preset', name, 'status', response.status_code)
    data = response.json()
    final = data.get('final_decision', {})
    print('  verdict', final.get('verdict'), 'confidence', final.get('confidence'), 'risk_score', final.get('risk_score'))
    assert final.get('confidence') is not None, f'confidence missing for {name}'
    assert 0.0 <= final.get('confidence', 0) <= 1.0, f'invalid confidence for {name}'
