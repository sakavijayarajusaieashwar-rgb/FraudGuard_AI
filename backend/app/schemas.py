from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    created_at: datetime


class VendorBase(BaseModel):
    name: str
    tax_id: Optional[str] = None
    avg_invoice_amount: float = 0.0
    first_seen_date: Optional[str] = None
    is_known: bool = True


class VendorResponse(VendorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RiskSignal(BaseModel):
    rule: str
    severity: str
    description: str


class InvoiceBase(BaseModel):
    workflow_type: Optional[str] = "invoice_fraud"
    invoice_number: str
    vendor_name: str
    amount: float
    owner_id: Optional[int] = None
    risk_score: float = 0.0
    confidence: float = 0.0
    invoice_date: str
    status: Optional[str] = "PENDING"
    flags_json: Optional[str] = None
    reasoning: Optional[str] = None
    human_override: Optional[str] = None
    risk_signals: List[RiskSignal] = []
    verdict_summary: Optional[str] = None
    critic_notes: Optional[str] = None
    extra_data_json: Optional[str] = None
    extra_data: Optional[dict] = {}


class InvoiceResponse(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    submitted_at: datetime


class HealthResponse(BaseModel):
    status: str
    message: str
