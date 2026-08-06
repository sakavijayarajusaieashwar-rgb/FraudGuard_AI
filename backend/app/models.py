import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    tax_id = Column(String(100), nullable=True)
    avg_invoice_amount = Column(Float, default=0.0)
    first_seen_date = Column(String(50), nullable=True)
    is_known = Column(Boolean, default=True)


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    invoice_number = Column(String(100), index=True, nullable=False)
    vendor_name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    invoice_date = Column(String(50), nullable=False)
    status = Column(String(50), default="PENDING")
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    flags_json = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    human_override = Column(Text, nullable=True)
    critic_notes = Column(Text, nullable=True)
    risk_signals_json = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)

    @property
    def risk_signals(self):
        if not self.risk_signals_json:
            return []
        try:
            return json.loads(self.risk_signals_json)
        except Exception:
            return []

    @property
    def verdict_summary(self):
        return self.reasoning


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
