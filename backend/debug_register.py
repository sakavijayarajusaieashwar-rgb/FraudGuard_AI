import sys, traceback
sys.path.insert(0, r'c:\Users\Sarvan\Downloads\Fraudguard-ai-main\Fraudguard-ai-main')
from backend.app.database import SessionLocal
from backend.app.main import register_user, RegisterRequest

db = SessionLocal()
try:
    req = RegisterRequest(email='saieashwar2007@gmail.com', password='testpass', full_name='sai')
    print(register_user(req, db=db))
except Exception:
    traceback.print_exc()
finally:
    db.close()
