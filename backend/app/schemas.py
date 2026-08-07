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


class DashboardMetricsResponse(BaseModel):
    transactions_protected: int
    fraud_blocked: int
    potential_loss_prevented: float
    money_out_prevented: float
    goods_out_prevented: float
    transactions_escalated: int
    approval_rate: float
    fraud_type_breakdown: dict


class InvestigationRequest(BaseModel):
    query: str


class InvestigationResponse(BaseModel):
    answer: str
    evidence: List[str]
    confidence_basis: str
    recommended_human_checks: List[str]
    response_source: str


class PaymentEvidence(BaseModel):
    transaction_reference: Optional[str] = None
    order_reference: Optional[str] = None
    ledger_status: Optional[str] = None
    ledger_amount: float = 0.0
    beneficiary_name: Optional[str] = None
    verified: bool = False
    ledger_match_found: bool = False


class TrustProfileResponse(BaseModel):
    entity_name: str
    entity_type: str
    total_transactions: int
    approved_count: int
    escalated_count: int
    rejected_count: int
    avg_amount: float
    known_bank_accounts: List[str]
    risk_level: str


class DocumentForensicsMetadata(BaseModel):
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    pdf_producer: Optional[str] = None
    pdf_creator: Optional[str] = None
    creation_date: Optional[str] = None
    sha256_hash: Optional[str] = None
    arithmetic_errors: List[str] = []


class ThreeWayMatchItem(BaseModel):
    description: str
    ordered_qty: float
    received_qty: float
    invoiced_qty: float
    po_price: float
    invoice_price: float
    unsupported_qty: float
    unsupported_amount: float
    status: str


class ThreeWayMatchDetails(BaseModel):
    po_number: str
    grn_number: str
    status: str
    items: List[ThreeWayMatchItem] = []
    total_unsupported_qty: float
    total_unsupported_amount: float


class DocumentForensicsResult(BaseModel):
    document_id: int
    document_type: str
    forensic_status: str
    claimed_vendor: Optional[str] = None
    claimed_bank: Optional[str] = None
    claimed_amount: Optional[float] = None
    claimed_po: Optional[str] = None
    verified_bank: Optional[str] = None
    verified_po_vendor: Optional[str] = None
    verified_po_amount: Optional[float] = None
    comparison_vendor: str
    comparison_amount: str
    comparison_bank: str
    forensic_signals: List[str] = []
    recommended_action: str
    metadata: Optional[DocumentForensicsMetadata] = None
    three_way_match: Optional[ThreeWayMatchDetails] = None


class InvoiceEvidenceResponse(BaseModel):
    invoice_id: int
    invoice_number: str
    vendor_name: str
    amount: float
    invoice_date: str
    status: str
    workflow_type: str
    risk_score: float
    risk_level: str
    risk_signals: List[RiskSignal] = []
    primary_findings: List[str] = []
    related_edges: List[str] = []
    payment_evidence: Optional[PaymentEvidence] = None
    vendor_behavior: Optional[dict] = None
    trust_profile: Optional[TrustProfileResponse] = None
    recommended_action: str
    document_forensics: Optional[DocumentForensicsResult] = None

