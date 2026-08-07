import json
from .database import engine, Base, SessionLocal, ensure_db_schema
from .models import Vendor, Invoice, User, PurchaseOrder, GoodsReceipt


def seed_database():
    ensure_db_schema()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(Invoice).delete()
        db.query(PurchaseOrder).delete()
        db.query(GoodsReceipt).delete()
        db.query(Vendor).delete()
        db.query(User).delete()
        db.commit()
        # 1. Create demo users first
        from .auth import get_password_hash

        user_a = User(
            email="demo@fraudguard.ai",
            full_name="Demo User A",
            hashed_password=get_password_hash("demo1234"),
            is_active=True,
        )
        user_b = User(
            email="demo2@fraudguard.ai",
            full_name="Demo User B",
            hashed_password=get_password_hash("demo1234"),
            is_active=True,
        )
        db.add(user_a)
        db.add(user_b)
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)

        # 2. Seed 8 Realistic Vendors
        vendors_data = [
            {
                "name": "Apex Cloud Infrastructure Inc",
                "tax_id": "US-EIN-98421049",
                "avg_invoice_amount": 1450.00,
                "first_seen_date": "2025-01-15",
                "is_known": True,
            },
            {
                "name": "Global Office Supplies Co",
                "tax_id": "US-EIN-88120491",
                "avg_invoice_amount": 3200.00,
                "first_seen_date": "2025-02-10",
                "is_known": True,
            },
            {
                "name": "Vortex Digital Marketing Consultants",
                "tax_id": "US-EIN-77219401",
                "avg_invoice_amount": 8500.00,
                "first_seen_date": "2025-03-01",
                "is_known": True,
            },
            {
                "name": "Nexus Logistics & Express",
                "tax_id": "US-EIN-55912048",
                "avg_invoice_amount": 2500.00,
                "first_seen_date": "2025-04-20",
                "is_known": True,
            },
            {
                "name": "Acme Corp",
                "tax_id": "US-EIN-44102984",
                "avg_invoice_amount": 4500.00,
                "first_seen_date": "2024-01-15",
                "is_known": True,
            },
            {
                "name": "Acme Software Solutions LLC",
                "tax_id": "US-EIN-33910294",
                "avg_invoice_amount": 5000.00,
                "first_seen_date": "2025-05-12",
                "is_known": True,
            },
            {
                "name": "Starlight Event Planning Ltd",
                "tax_id": "US-EIN-11940182",
                "avg_invoice_amount": 4200.00,
                "first_seen_date": "2025-06-01",
                "is_known": True,
            },
            {
                "name": "Titan Heavy Machinery Corp",
                "tax_id": "US-EIN-44910283",
                "avg_invoice_amount": 18000.00,
                "first_seen_date": "2025-07-04",
                "is_known": True,
            },
            {
                "name": "Horizon Telecom Services",
                "tax_id": "US-EIN-66910238",
                "avg_invoice_amount": 950.00,
                "first_seen_date": "2025-08-11",
                "is_known": True,
            },
            {
                "name": "Established Vendor LLC",
                "tax_id": "US-EIN-99999999",
                "avg_invoice_amount": 150000.00,
                "first_seen_date": "2024-01-01",
                "is_known": True,
            },
        ]

        for v_data in vendors_data:
            db.add(Vendor(**v_data))
        db.commit()

        # 3. Seed Procurement Records
        db.query(PurchaseOrder).delete()
        db.query(GoodsReceipt).delete()
        db.commit()

        purchase_orders = [
            PurchaseOrder(
                po_number="PO-APEX-992",
                vendor_name="Apex Cloud Infrastructure Inc",
                amount=1450.00,
                order_date="2026-07-01",
                status="APPROVED",
                owner_id=user_a.id,
                line_items_json=json.dumps([
                    {"description": "Kubernetes Dedicated Cluster Nodes", "quantity": 1.0, "unit_price": 1100.0, "total": 1100.0},
                    {"description": "Bandwidth Egress & Network Load Balancer", "quantity": 1.0, "unit_price": 350.0, "total": 350.0}
                ])
            ),
            PurchaseOrder(
                po_number="PO-OFFICE-88",
                vendor_name="Global Office Supplies Co",
                amount=3200.00,
                order_date="2026-07-10",
                status="APPROVED",
                owner_id=user_a.id,
                line_items_json=json.dumps([
                    "Executive Ergonomic Chairs: $3,200.00"
                ])
            ),
            PurchaseOrder(
                po_number="PO-UNKNOWN-01",
                vendor_name="Phantom Consulting Group",
                amount=9800.00,
                order_date="2026-07-30",
                status="APPROVED",
                owner_id=user_a.id,
                line_items_json=json.dumps([
                    "Consulting Services: $9,800.00"
                ])
            ),
            PurchaseOrder(
                po_number="PO-OVERBILL-001",
                vendor_name="Apex Cloud Infrastructure Inc",
                amount=100000.00,
                order_date="2026-07-15",
                status="APPROVED",
                owner_id=user_a.id,
                line_items_json=json.dumps([
                    {"description": "Enterprise Cloud Servers", "quantity": 100.0, "unit_price": 1000.0, "total": 100000.0}
                ])
            )
        ]
        db.add_all(purchase_orders)
        db.commit()

        goods_receipts = [
            GoodsReceipt(
                grn_number="GRN-APEX-01",
                po_number="PO-APEX-992",
                received_amount=1450.00,
                received_date="2026-07-05",
                status="RECEIVED",
                owner_id=user_a.id,
                notes="Goods receipt for monthly infrastructure services."
            ),
            GoodsReceipt(
                grn_number="GRN-OFFICE-01",
                po_number="PO-OFFICE-88",
                received_amount=3200.00,
                received_date="2026-07-11",
                status="RECEIVED",
                owner_id=user_a.id,
                notes="Goods receipt for office chairs."
            ),
            GoodsReceipt(
                grn_number="GRN-OVERBILL-001",
                po_number="PO-OVERBILL-001",
                received_amount=80000.00,
                received_date="2026-07-20",
                status="RECEIVED",
                owner_id=user_a.id,
                notes="Short shipment: only 80 units received.",
                line_items_json=json.dumps([
                    {"description": "Enterprise Cloud Servers", "quantity": 80.0, "unit_price": 1000.0, "total": 80000.0}
                ])
            )
        ]
        db.add_all(goods_receipts)
        db.commit()

        # 4. Seed Invoices for User A and User B
        invoices_data_user_a = [
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-EST-001",
                "vendor_name": "Established Vendor LLC",
                "amount": 145000.00,
                "invoice_date": "2026-05-01",
                "status": "APPROVED",
                "reasoning": "Historical invoice 1.",
                "extra_data_json": json.dumps({"bank_account_number": "111222333", "routing_number": "000111222"}),
            },
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-EST-002",
                "vendor_name": "Established Vendor LLC",
                "amount": 155000.00,
                "invoice_date": "2026-06-01",
                "status": "APPROVED",
                "reasoning": "Historical invoice 2.",
                "extra_data_json": json.dumps({"bank_account_number": "111222333", "routing_number": "000111222"}),
            },
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-EST-003",
                "vendor_name": "Established Vendor LLC",
                "amount": 150000.00,
                "invoice_date": "2026-07-01",
                "status": "APPROVED",
                "reasoning": "Historical invoice 3.",
                "extra_data_json": json.dumps({"bank_account_number": "111222333", "routing_number": "000111222"}),
            },
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-APEX-1001",
                "vendor_name": "Apex Cloud Infrastructure Inc",
                "amount": 1450.00,
                "invoice_date": "2026-07-01",
                "status": "APPROVED",
                "reasoning": "Standard recurring infrastructure monthly billing.",
                "extra_data_json": json.dumps({"bank_account_number": "123459271", "routing_number": "998877665"}),
            },
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-OFFICE-402",
                "vendor_name": "Global Office Supplies Co",
                "amount": 3200.00,
                "invoice_date": "2026-07-05",
                "status": "REJECTED",
                "reasoning": "Rejected office supplies invoice due to high risk.",
                "extra_data_json": json.dumps({"bank_account_number": "123454418", "routing_number": "998877665"}),
            },
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-DUP-9901",
                "vendor_name": "Global Office Supplies Co",
                "amount": 3200.00,
                "invoice_date": "2026-07-10",
                "status": "APPROVED",
                "reasoning": "Original invoice for executive ergonomics.",
            },
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-DUP-9901",
                "vendor_name": "Global Office Supplies Co",
                "amount": 3200.00,
                "invoice_date": "2026-07-28",
                "status": "PENDING",
                "flags_json": '["DUPLICATE_INVOICE_NUMBER"]',
                "reasoning": "Duplicate invoice number flag raised for review.",
            },
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-VORTEX-771",
                "vendor_name": "Vortex Digital Marketing Consultants",
                "amount": 65000.00,
                "invoice_date": "2026-07-29",
                "status": "PENDING",
                "flags_json": '["UNUSUAL_INVOICE_AMOUNT", "HIGH_VALUE_THRESHOLD"]',
                "reasoning": "Amount $65,000 vastly exceeds vendor average of $8,500.",
            },
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-UNKNOWN-001",
                "vendor_name": "Phantom Consulting Group",
                "amount": 9800.00,
                "invoice_date": "2026-07-30",
                "status": "PENDING",
                "flags_json": '["UNKNOWN_VENDOR"]',
                "reasoning": "Vendor not found in verified master list.",
            },
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-APEX-2004",
                "vendor_name": "Apex C1oud Infrastructure Inc",  # Typosquatting
                "amount": 1450.00,
                "invoice_date": "2026-08-01",
                "status": "PENDING",
                "flags_json": '["TYPOSQUATTING_TYPO_SIMILARITY"]',
                "reasoning": "Vendor name similarity match with known vendor 'Apex Cloud Infrastructure Inc'.",
            },
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-NEXUS-881",
                "vendor_name": "Nexus Logistics & Express",
                "amount": 2480.00,
                "invoice_date": "2026-08-02",
                "status": "APPROVED",
                "reasoning": "Freight shipping invoice verified.",
            },
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-ACME-902",
                "vendor_name": "Acme Software Solutions LLC",
                "amount": 25000.00,
                "invoice_date": "2026-08-03",
                "status": "PENDING",
                "flags_json": '["ROUND_NUMBER_ANOMALY"]',
                "reasoning": "Suspicious exact round amount $25,000.",
            },
            {
                "owner_id": user_a.id,
                "invoice_number": "INV-HORIZON-339",
                "vendor_name": "Horizon Telecom Services",
                "amount": 920.00,
                "invoice_date": "2026-08-04",
                "status": "APPROVED",
                "reasoning": "Standard telecom invoice.",
            },
        ]

        invoices_data_user_b = [
            {
                "owner_id": user_b.id,
                "invoice_number": "INV-DEMOB-101",
                "vendor_name": "Starlight Event Planning Ltd",
                "amount": 4200.00,
                "invoice_date": "2026-08-05",
                "status": "APPROVED",
                "reasoning": "Corporate gala event planning invoice.",
            },
            {
                "owner_id": user_b.id,
                "invoice_number": "INV-DEMOB-102",
                "vendor_name": "Titan Heavy Machinery Corp",
                "amount": 18000.00,
                "invoice_date": "2026-08-06",
                "status": "PENDING",
                "flags_json": '["ROUND_NUMBER_ANOMALY"]',
                "reasoning": "Equipment lease invoice for regional hub.",
            },
        ]

        all_invoices = invoices_data_user_a + invoices_data_user_b
        for inv_data in all_invoices:
            db.add(Invoice(**inv_data))
        db.commit()

        print(f"Successfully seeded {len(vendors_data)} vendors, {len(all_invoices)} invoices across 2 demo users.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
