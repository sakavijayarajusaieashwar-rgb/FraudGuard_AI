import os
import sys

# Add backend directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import PaymentLedger

def seed_ledger():
    print("Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Wipe existing
    db.query(PaymentLedger).delete()
    db.commit()

    print("Seeding Payment Ledger...")
    payments = [
        PaymentLedger(
            transaction_reference="REF-A123",
            order_reference="ORD-12345",
            amount=250.00,
            status="SETTLED",
            beneficiary_name="FraudGuard Corp"
        ),
        PaymentLedger(
            transaction_reference="REF-PARTIAL",
            order_reference="ORD-PARTIAL",
            amount=47000.00,
            status="SETTLED",
            beneficiary_name="FraudGuard Corp"
        ),
        PaymentLedger(
            transaction_reference="REF-EVE",
            order_reference="ORD-ACTUAL",
            amount=250.00,
            status="SETTLED",
            beneficiary_name="FraudGuard Corp"
        ),
        PaymentLedger(
            transaction_reference="REF-FRANK",
            order_reference="ORD-WRONG-BEN",
            amount=1000.00,
            status="SETTLED",
            beneficiary_name="Attacker Inc"
        ),
        PaymentLedger(
            transaction_reference="REF-PENDING",
            order_reference="ORD-PENDING",
            amount=2000.00,
            status="PENDING",
            beneficiary_name="FraudGuard Corp"
        )
    ]
    
    db.add_all(payments)
    db.commit()
    db.close()
    print("Successfully seeded Payment Ledger.")

if __name__ == "__main__":
    seed_ledger()

