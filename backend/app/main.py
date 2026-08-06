import os
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Body, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_user_from_header_or_query,
    get_user_by_email,
    get_password_hash,
)
from .database import engine, Base, get_db, ensure_db_schema
from .models import Invoice, Vendor, User
from .schemas import (
    InvoiceResponse,
    HealthResponse,
    Token,
    UserCreate,
    UserResponse,
)
from .services.heuristics import compute_deterministic_risk_flags, build_vendor_network
from .services.cache import get_cached_preset
from .agents.extraction import ExtractionAgent
from .agents.risk import RiskAgent
from .agents.decision import DecisionAgent
from .agents.critic import CriticAgent

# Ensure database tables exist
Base.metadata.create_all(bind=engine)
ensure_db_schema()

app = FastAPI(
    title="FraudGuard AI - Autonomous Multi-Agent Invoice Fraud Detection API",
    description="Autonomous 4-agent invoice risk reasoning backend.",
    version="1.0.0",
)

@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )

# CORS Middleware enabling Vite frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent Instances
extraction_agent = ExtractionAgent()
risk_agent = RiskAgent()
decision_agent = DecisionAgent()
critic_agent = CriticAgent()


# Request Schemas
class ExtractRequest(BaseModel):
    invoice_text: str


class AnalyzeRequest(BaseModel):
    invoice_text: str
    invoice_id: Optional[int] = None


class OverrideRequest(BaseModel):
    override: str  # APPROVED, REJECTED, ESCALATED
    reason: Optional[str] = "Manual human override"


class PresetRequest(BaseModel):
    preset_type: str


class CreateInvoiceRequest(BaseModel):
    vendor_name: str
    invoice_number: Optional[str] = None
    total_amount: float
    raw_content: Optional[str] = None
    invoice_date: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


@app.post("/api/auth/register", response_model=Token)
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, req.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=req.email.lower().strip(),
        full_name=req.full_name,
        hashed_password=get_password_hash(req.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/login", response_model=Token)
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.post("/invoices/preset")
@app.post("/api/invoices/preset")
def create_preset_invoice(req: PresetRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    preset_type = req.preset_type.strip().lower()
    presets = {
        "clean": {
            "invoice_number": "INV-APEX-1001",
            "vendor_name": "Apex Cloud Infrastructure Inc",
            "amount": 1450.00,
            "invoice_date": "2026-07-01",
            "reasoning": "Line Items:\n- Kubernetes Dedicated Cluster Nodes: $1,000.00\n- Bandwidth Egress: $450.00\nTax ID: US-EIN-98421049",
        },
        "duplicate": {
            "invoice_number": "INV-DUP-9901",
            "vendor_name": "Global Office Supplies Co",
            "amount": 3200.00,
            "invoice_date": "2026-07-28",
            "reasoning": "Line Items:\n- Executive Ergonomic Chairs: $3,200.00\nTax ID: US-EIN-88120491",
        },
        "suspicious_amount": {
            "invoice_number": "INV-VORTEX-771",
            "vendor_name": "Vortex Digital Marketing Consultants",
            "amount": 65000.00,
            "invoice_date": "2026-07-29",
            "reasoning": "Line Items:\n- Brand Strategy Retainer (Urgent Wire Required): $65,000.00\nTax ID: US-EIN-77219401",
        },
        "suspicious_math": {
            "invoice_number": "INV-NEXUS-881",
            "vendor_name": "Nexus Logistics & Express",
            "amount": 12500.00,
            "invoice_date": "2026-07-20",
            "reasoning": "Line Items:\n- Freight Shipping Charges: 5 shipments @ $1,000.00 each = $5,000.00\nBilled Total Amount: $12,500.00\nNote: Billed total $12,500 mismatch with line items sum $5,000.",
        },
        "typosquat": {
            "invoice_number": "INV-APEX-2004",
            "vendor_name": "Apex C1oud Infrastructure Inc",
            "amount": 1450.00,
            "invoice_date": "2026-08-01",
            "reasoning": "Line Items:\n- Server Hosting: $1,450.00",
        },
    }

    if preset_type not in presets:
        raise HTTPException(status_code=400, detail=f"Unknown preset_type '{req.preset_type}'.")

    data = presets[preset_type]
    invoice = Invoice(
        owner_id=current_user.id,
        invoice_number=data["invoice_number"],
        vendor_name=data["vendor_name"],
        amount=data["amount"],
        invoice_date=data["invoice_date"],
        status="PENDING",
        reasoning=data.get("reasoning", "Preset demo invoice created."),
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@app.post("/invoices/create")
@app.post("/api/invoices/create")
def create_custom_invoice(req: CreateInvoiceRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    invoice_date = req.invoice_date or datetime.now().strftime("%Y-%m-%d")
    invoice_number = req.invoice_number or f"INV-{int(datetime.utcnow().timestamp())}"
    invoice = Invoice(
        owner_id=current_user.id,
        invoice_number=invoice_number,
        vendor_name=req.vendor_name.strip() or "Custom Vendor",
        amount=req.total_amount,
        invoice_date=invoice_date,
        status="PENDING",
        reasoning=req.raw_content or "Custom invoice created for analysis.",
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@app.delete("/invoices/{invoice_id}")
@app.delete("/api/invoices/{invoice_id}")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice ID {invoice_id} not found.")
    if invoice.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this invoice.")
    db.delete(invoice)
    db.commit()
    return {"message": f"Invoice {invoice_id} deleted."}


@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "FraudGuard AI Backend",
        "message": "FraudGuard AI Autonomous Multi-Agent API is active."
    }


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        message="FraudGuard AI Backend & 4 Autonomous Agents Ready."
    )


@app.get("/invoices", response_model=List[InvoiceResponse])
@app.get("/api/invoices", response_model=List[InvoiceResponse])
def list_invoices(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return db.query(Invoice).filter(Invoice.owner_id == current_user.id).order_by(Invoice.id.desc()).all()


@app.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
@app.get("/api/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice ID {invoice_id} not found.")
    if invoice.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this invoice.")
    return invoice


@app.get("/invoices/{invoice_id}/why/{flag_index}")
@app.get("/api/invoices/{invoice_id}/why/{flag_index}")
def explain_flag(invoice_id: int, flag_index: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Deep-dive explainability endpoint for specific risk flags."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice ID {invoice_id} not found.")
    if invoice.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this invoice.")

    flags = []
    if invoice.flags_json:
        try:
            flags = json.loads(invoice.flags_json)
        except Exception:
            flags = [invoice.flags_json]

    if flag_index < 0 or flag_index >= len(flags):
        raise HTTPException(
            status_code=404,
            detail=f"Flag index {flag_index} out of bounds. Invoice has {len(flags)} flag(s)."
        )

    flag_name = flags[flag_index]
    explanations = {
        "DUPLICATE_INVOICE_NUMBER": "Critical Risk: An invoice with this identical invoice number already exists in the financial database.",
        "UNUSUAL_INVOICE_AMOUNT": "High Risk: Invoice total amount significantly deviates from historical vendor average.",
        "UNUSUAL_INVOICE_AMOUNT_RATIO": "High Risk: Invoice total amount is several multiples higher than vendor baseline average.",
        "UNKNOWN_VENDOR": "Medium Risk: Vendor is not registered in the master verified vendor database.",
        "TYPOSQUATTING_TYPO_SIMILARITY": "Critical Risk: Vendor name closely matches a known vendor name with minor character substitutions.",
        "VENDOR_TYPOSQUATTING_SIMILARITY": "Critical Risk: Vendor name closely matches a known vendor name with minor character substitutions.",
        "ROUND_NUMBER_ANOMALY": "Low Risk: Invoice total is an exact round number, frequently seen in manual or fraudulent invoices.",
        "MISSING_REQUIRED_FIELDS": "High Risk: Crucial invoice fields (vendor, invoice number, date, or total) are missing or null."
    }

    return {
        "invoice_id": invoice.id,
        "flag_index": flag_index,
        "flag_name": flag_name,
        "explanation": explanations.get(flag_name, f"Risk flag '{flag_name}' detected during multi-agent audit."),
        "reasoning_summary": invoice.reasoning
    }


@app.post("/extract")
async def extract_invoice_endpoint(req: ExtractRequest):
    """Standalone Extraction Agent endpoint converting raw text to structured invoice JSON."""
    if not req.invoice_text or not req.invoice_text.strip():
        raise HTTPException(status_code=400, detail="invoice_text cannot be empty.")
    
    try:
        result = await extraction_agent.extract(req.invoice_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


async def _run_live_pipeline(invoice_text: str, db: Session, owner_id: Optional[int] = None) -> Dict[str, Any]:
    """Runs live 4-agent autonomous execution pipeline."""
    trace = []

    # Step 1: Extraction Agent
    extracted = await extraction_agent.extract(invoice_text)
    trace.append({
        "agent": "Extraction Agent",
        "step": "Document Extraction",
        "status": "SUCCESS" if extracted.get("vendor_name") else "WARNING",
        "thought": f"Extracted vendor '{extracted.get('vendor_name')}', amount ${extracted.get('amount')}, inv #{extracted.get('invoice_number')}.",
        "data": extracted
    })

    # Save/Update invoice record in SQLite DB
    inv_num = extracted.get("invoice_number") or f"INV-GEN-{db.query(Invoice).count()+1}"
    amount_val = float(extracted.get("amount") or 0.0)
    
    invoice = Invoice(
        owner_id=owner_id,
        invoice_number=inv_num,
        vendor_name=extracted.get("vendor_name") or "Unknown Vendor",
        amount=amount_val,
        invoice_date=extracted.get("invoice_date") or "2026-08-05",
        status="ANALYZING"
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Step 2: Compute Deterministic Risk Signals BEFORE Risk Agent
    deterministic_signals = compute_deterministic_risk_flags(extracted, db, current_invoice_id=invoice.id)
    try:
        vendor_network = build_vendor_network(extracted.get("vendor_name"), db)
    except Exception:
        vendor_network = []

    # Step 3: Risk Agent
    risk_output = await risk_agent.analyze_risk(extracted, deterministic_signals)
    trace.append({
        "agent": "Risk Agent",
        "step": "Risk & Anomaly Analysis",
        "status": "WARNING" if risk_output["calculated_risk_score"] > 30 else "SUCCESS",
        "thought": risk_output.get("thoughts", ""),
        "data": risk_output
    })

    # Step 4: Decision Agent
    decision_output = await decision_agent.decide(extracted, risk_output)
    trace.append({
        "agent": "Decision Agent",
        "step": "Verdict Synthesis",
        "status": "INFO",
        "thought": decision_output.get("verdict_summary", ""),
        "data": decision_output
    })

    # Step 5: Critic Agent
    critic_output = await critic_agent.audit(extracted, risk_output, decision_output)
    trace.append({
        "agent": "Critic Agent",
        "step": "Governance Audit",
        "status": "SUCCESS" if critic_output["final_verdict"] == "APPROVE" else "WARNING",
        "thought": critic_output.get("critic_notes", ""),
        "data": critic_output
    })

    # Update Invoice status & flags in DB
    final_verdict = critic_output.get("final_verdict", "ESCALATE")
    invoice.status = final_verdict
    invoice.flags_json = json.dumps([s.get("rule") for s in risk_output.get("risk_signals", [])])
    invoice.reasoning = decision_output.get("verdict_summary")
    invoice.critic_notes = critic_output.get("critic_notes")
    invoice.risk_signals_json = json.dumps(risk_output.get("risk_signals", []))
    invoice.confidence = float(decision_output.get("confidence") or 0.0)
    invoice.risk_score = float(risk_output.get("calculated_risk_score", 0.0))
    db.commit()

    return {
        "invoice_id": invoice.id,
        "trace": trace,
        "vendor_network": vendor_network,
        "final_decision": {
            "verdict": final_verdict,
            "risk_score": risk_output.get("calculated_risk_score", 0.0),
            "confidence": float(decision_output.get("confidence") or 0.0),
            "summary": decision_output.get("verdict_summary"),
            "critic_stamp": critic_output.get("critic_stamp"),
            "critic_notes": critic_output.get("critic_notes"),
            "risk_signals": risk_output.get("risk_signals", []),
            "human_override": invoice.human_override
        }
    }


def _format_sse_event(data: Dict[str, Any]) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _build_invoice_text(invoice: Invoice) -> str:
    text_lines = [
        f"From: {invoice.vendor_name}",
        f"Invoice Number: {invoice.invoice_number}",
        f"Date: {invoice.invoice_date}",
        f"Total Amount: ${invoice.amount:,.2f}",
    ]
    if invoice.reasoning:
        text_lines.append(f"Details:\n{invoice.reasoning}")
    return "\n".join(text_lines)


@app.get("/invoices/{invoice_id}/analyze/stream")
@app.get("/api/invoices/{invoice_id}/analyze/stream")
def analyze_invoice_stream(invoice_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_header_or_query)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice ID {invoice_id} not found.")
    if invoice.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this invoice.")

    invoice_text = _build_invoice_text(invoice)

    async def event_generator():
        try:
            extracted = await extraction_agent.extract(invoice_text)
            yield _format_sse_event({
                "agent_name": "Extraction Agent",
                "step_name": "Document Extraction",
                "status": "SUCCESS" if extracted.get("vendor_name") else "WARNING",
                "thought_process": f"Extracted vendor '{extracted.get('vendor_name')}', amount ${extracted.get('amount')}, inv #{extracted.get('invoice_number')}.",
                "output_data": extracted,
            })

            invoice_record = invoice
            invoice_record.status = "ANALYZING"
            invoice_record.invoice_number = extracted.get("invoice_number") or invoice.invoice_number
            invoice_record.vendor_name = extracted.get("vendor_name") or invoice.vendor_name
            invoice_record.amount = float(extracted.get("amount") or invoice.amount or 0.0)
            invoice_record.invoice_date = extracted.get("invoice_date") or invoice.invoice_date
            db.commit()
            db.refresh(invoice_record)

            deterministic_signals = compute_deterministic_risk_flags(extracted, db, current_invoice_id=invoice_record.id)
            risk_output = await risk_agent.analyze_risk(extracted, deterministic_signals)
            yield _format_sse_event({
                "agent_name": "Risk Agent",
                "step_name": "Risk & Anomaly Analysis",
                "status": "WARNING" if risk_output["calculated_risk_score"] > 30 else "SUCCESS",
                "thought_process": risk_output.get("thoughts", ""),
                "output_data": risk_output,
            })

            decision_output = await decision_agent.decide(extracted, risk_output)
            yield _format_sse_event({
                "agent_name": "Decision Agent",
                "step_name": "Verdict Synthesis",
                "status": "INFO",
                "thought_process": decision_output.get("verdict_summary", ""),
                "output_data": decision_output,
            })

            critic_output = await critic_agent.audit(extracted, risk_output, decision_output)
            final_verdict = critic_output.get("final_verdict", "ESCALATE")
            invoice_record.status = final_verdict
            invoice_record.flags_json = json.dumps([s.get("rule") for s in risk_output.get("risk_signals", [])])
            invoice_record.reasoning = decision_output.get("verdict_summary")
            invoice_record.critic_notes = critic_output.get("critic_notes")
            invoice_record.risk_signals_json = json.dumps(risk_output.get("risk_signals", []))
            invoice_record.confidence = float(decision_output.get("confidence") or 0.0)
            invoice_record.risk_score = float(risk_output.get("calculated_risk_score", 0.0))
            db.commit()
            yield _format_sse_event({
                "agent_name": "Critic Agent",
                "step_name": "Governance Audit",
                "status": "SUCCESS" if final_verdict == "APPROVE" else "WARNING",
                "thought_process": critic_output.get("critic_notes", ""),
                "output_data": critic_output,
            })

            yield _format_sse_event({
                "agent_name": "FraudGuard Orchestrator",
                "step_name": "Pipeline Execution Finished",
                "status": "SUCCESS",
                "thought_process": "Pipeline execution finished successfully.",
                "output_data": {
                    "invoice_id": invoice_record.id,
                    "final_verdict": final_verdict,
                    "risk_score": risk_output.get("calculated_risk_score", 0.0),
                    "verdict_summary": decision_output.get("verdict_summary"),
                    "critic_notes": critic_output.get("critic_notes"),
                    "risk_signals": risk_output.get("risk_signals", []),
                    "vendor_network": vendor_network,
                },
            })
        except Exception as exc:
            # On live LLM failures during SSE, optionally emit cached demo preset traces
            use_cache_fallback = os.getenv("USE_DEMO_CACHE", "true").strip().lower() == "true"
            if use_cache_fallback:
                try:
                    cached = get_cached_preset(invoice_text)
                    if cached:
                        # Stream cached trace events for UI parity
                        for step in cached.get("trace", []):
                            yield _format_sse_event({
                                "agent_name": step.get("agent", "Agent"),
                                "step_name": step.get("step", "Step"),
                                "status": step.get("status", "INFO"),
                                "thought_process": step.get("thought", ""),
                                "output_data": step.get("data", {}),
                            })

                        # Final orchestrator event with final_decision payload
                        yield _format_sse_event({
                            "agent_name": "FraudGuard Orchestrator",
                            "step_name": "Pipeline Execution Finished",
                            "status": "SUCCESS",
                            "thought_process": "Served demo cached preset due to live LLM failure.",
                            "output_data": {
                                "invoice_id": invoice.id,
                                "final_decision": cached.get("final_decision", {}),
                                "vendor_network": cached.get("vendor_network", []),
                            },
                        })
                        return
                except Exception:
                    # Fall through to emitting the error event below
                    pass

            yield _format_sse_event({
                "agent_name": "FraudGuard Orchestrator",
                "step_name": "Pipeline Execution Finished",
                "status": "ERROR",
                "thought_process": str(exc),
                "output_data": {},
            })

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/analyze")
@app.post("/api/analyze")
async def analyze_invoice_endpoint(req: AnalyzeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Executes full 4-agent autonomous pipeline.
    ALWAYS attempts live LLM execution first.
    If live API call fails or times out (>8s) AND USE_DEMO_CACHE=true, serves safety-net demo cache.
    """
    if not req.invoice_text or not req.invoice_text.strip():
        raise HTTPException(status_code=400, detail="invoice_text cannot be empty.")

    use_cache_fallback = os.getenv("USE_DEMO_CACHE", "true").strip().lower() == "true"

    try:
        # 1. ALWAYS attempt live call first with an 8-second timeout safety net
        return await asyncio.wait_for(_run_live_pipeline(req.invoice_text, db, owner_id=current_user.id), timeout=8.0)
    except Exception as e:
        print(f"[Analyze Endpoint] Live LLM pipeline exception or timeout: {e}")
        if use_cache_fallback:
            cached_result = get_cached_preset(req.invoice_text)
            if cached_result:
                print("[LLM MODE] live (demo-cache fallback)")
                print("[LLM RESULT] model=cached-demo-preset")
                return cached_result
        raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {str(e)}")


@app.post("/override/{invoice_id}")
@app.post("/api/override/{invoice_id}")
def override_invoice_decision(invoice_id: int, req: OverrideRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Human compliance override endpoint."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice ID {invoice_id} not found.")
    if invoice.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to override this invoice.")

    invoice.human_override = f"{req.override}: {req.reason}"
    invoice.status = req.override
    db.commit()
    db.refresh(invoice)

    return {
        "message": f"Invoice {invoice_id} human override applied: [{req.override}]",
        "invoice_id": invoice.id,
        "new_status": invoice.status,
        "human_override": invoice.human_override
    }
