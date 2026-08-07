import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "fraudguard.db")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_db_schema():
    """Apply lightweight schema updates for missing SQLite columns."""
    with engine.connect() as conn:
        # Check invoices table
        result = conn.execute(text("PRAGMA table_info(invoices);"))
        columns = [row[1] for row in result.fetchall()]
        if "owner_id" not in columns:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN owner_id INTEGER REFERENCES users(id);"))
            conn.commit()
        if "workflow_type" not in columns:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN workflow_type VARCHAR(50) DEFAULT 'invoice_fraud';"))
            conn.commit()
        if "extra_data_json" not in columns:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN extra_data_json TEXT;"))
            conn.commit()
        if "risk_score" not in columns:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN risk_score FLOAT DEFAULT 0.0;"))
            conn.commit()
        if "critic_notes" not in columns:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN critic_notes TEXT;"))
            conn.commit()
        if "risk_signals_json" not in columns:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN risk_signals_json TEXT;"))
            conn.commit()
        if "confidence" not in columns:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN confidence FLOAT DEFAULT 0.0;"))
            conn.commit()

        # Check purchase_orders table
        po_result = conn.execute(text("PRAGMA table_info(purchase_orders);"))
        po_columns = [row[1] for row in po_result.fetchall()]
        if "owner_id" not in po_columns:
            conn.execute(text("ALTER TABLE purchase_orders ADD COLUMN owner_id INTEGER REFERENCES users(id);"))
            conn.commit()

        # Check goods_receipts table
        gr_result = conn.execute(text("PRAGMA table_info(goods_receipts);"))
        gr_columns = [row[1] for row in gr_result.fetchall()]
        if "owner_id" not in gr_columns:
            conn.execute(text("ALTER TABLE goods_receipts ADD COLUMN owner_id INTEGER REFERENCES users(id);"))
            conn.commit()
        if "line_items_json" not in gr_columns:
            conn.execute(text("ALTER TABLE goods_receipts ADD COLUMN line_items_json TEXT;"))
            conn.commit()

