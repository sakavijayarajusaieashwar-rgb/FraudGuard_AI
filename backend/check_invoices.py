import httpx, time
BASE='http://127.0.0.1:8003'
client=httpx.Client()
email=f'api_check_{int(time.time())}@fraudguard.local'
res=client.post(f'{BASE}/api/auth/register', json={'email':email,'password':'Test1234','full_name':'Checker'})
print('reg', res.status_code)
if res.status_code!=200:
    print(res.text)
    raise SystemExit(1)
token=res.json().get('access_token')
hdr={'Authorization':f'Bearer {token}'}
inv=client.get(f'{BASE}/api/invoices', headers=hdr).json()
print('invoices count', len(inv))
for i in inv[:6]:
    print(i.get('invoice_number'), i.get('vendor_name'), i.get('status'), i.get('confidence'), i.get('risk_score'))
