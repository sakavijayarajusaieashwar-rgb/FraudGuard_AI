import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "fraudguard.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
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
        result = conn.execute(text("PRAGMA table_info(invoices);"))
        columns = [row[1] for row in result.fetchall()]
        if "owner_id" not in columns:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN owner_id INTEGER REFERENCES users(id);"))
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
