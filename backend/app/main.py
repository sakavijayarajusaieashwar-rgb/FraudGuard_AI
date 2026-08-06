import os
import io
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Body, Request, status, File, UploadFile, Form
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
from .workflows import get_workflow, list_workflows

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
    workflow_type: Optional[str] = "invoice_fraud"


class AnalyzeRequest(BaseModel):
    invoice_text: str
    invoice_id: Optional[int] = None
    workflow_type: Optional[str] = "invoice_fraud"


class OverrideRequest(BaseModel):
    override: str  # APPROVED, REJECTED, ESCALATED
    reason: Optional[str] = "Manual human override"


class PresetRequest(BaseModel):
    preset_type: str
    workflow_type: Optional[str] = "invoice_fraud"


class CreateInvoiceRequest(BaseModel):
    vendor_name: str
    invoice_number: Optional[str] = None
    total_amount: float
    raw_content: Optional[str] = None
    invoice_date: Optional[str] = None
    workflow_type: Optional[str] = "invoice_fraud"
    extra_data: Optional[Dict[str, Any]] = None


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


@app.get("/workflows")
@app.get("/api/workflows")
def get_workflows_endpoint():
    return list_workflows()


@app.post("/invoices/preset")
@app.post("/api/invoices/preset")
def create_preset_invoice(req: PresetRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    wf_type = (req.workflow_type or "invoice_fraud").strip().lower()
    workflow = get_workflow(wf_type)
    presets = workflow.get_presets()
    preset_type = req.preset_type.strip().lower()

    if preset_type not in presets:
        raise HTTPException(status_code=400, detail=f"Unknown preset_type '{req.preset_type}' for workflow '{wf_type}'.")

    data = presets[preset_type]
    extra = data.get("extra_data", {})
    inv_num = data["invoice_number"]

    # For non-duplicate presets in invoice_fraud, ensure a unique invoice number so clean preset doesn't collide with historical ledger items
    if "duplicate" not in preset_type and wf_type != "customer_order":
        existing_dup = db.query(Invoice).filter(Invoice.invoice_number == inv_num).first()
        if existing_dup:
            suffix = int(datetime.utcnow().timestamp()) % 10000
            inv_num = f"{data['invoice_number']}-{suffix}"
    else:
        # Ensure at least one prior invoice exists in ledger for duplicate preset testing
        existing_count = db.query(Invoice).filter(Invoice.invoice_number == inv_num).count()
        if existing_count == 0:
            prior = Invoice(
                owner_id=current_user.id,
                workflow_type=wf_type,
                invoice_number=inv_num,
                vendor_name=data["vendor_name"],
                amount=data["amount"],
                invoice_date="2026-07-10",
                status="APPROVED",
                reasoning="Original processed invoice in ledger."
            )
            db.add(prior)
            db.commit()

    invoice = Invoice(
        owner_id=current_user.id,
        workflow_type=data.get("workflow_type", wf_type),
        invoice_number=inv_num,
        vendor_name=data["vendor_name"],
        amount=data["amount"],
        invoice_date=data["invoice_date"],
        status="PENDING",
        reasoning=data.get("reasoning", "Preset demo invoice created."),
        extra_data_json=json.dumps(extra) if extra else None,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@app.post("/invoices/create")
@app.post("/api/invoices/create")
def create_custom_invoice(req: CreateInvoiceRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    wf_type = (req.workflow_type or "invoice_fraud").strip().lower()
    invoice_date = req.invoice_date or datetime.now().strftime("%Y-%m-%d")
    prefix = "INV" if wf_type == "invoice_fraud" else ("EXP" if wf_type == "expense_approval" else "VEN")
    invoice_number = req.invoice_number or f"{prefix}-{int(datetime.utcnow().timestamp())}"
    invoice = Invoice(
        owner_id=current_user.id,
        workflow_type=wf_type,
        invoice_number=invoice_number,
        vendor_name=req.vendor_name.strip() or "Custom Item",
        amount=req.total_amount,
        invoice_date=invoice_date,
        status="PENDING",
        reasoning=req.raw_content or "Custom submission created for analysis.",
        extra_data_json=json.dumps(req.extra_data) if req.extra_data else None,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@app.post("/invoices/upload-document")
@app.post("/api/invoices/upload-document")
async def upload_invoice_document(
    file: UploadFile = File(...),
    workflow_type: Optional[str] = Form("invoice_fraud"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Accepts uploaded document files (.pdf, .txt, .json, .csv, .md, .png, .jpg),
    extracts document text, runs Extraction Agent to structure metadata, and
    saves the invoice ready for immediate streaming analysis.
    """
    wf_type = (workflow_type or "invoice_fraud").strip().lower()
    filename = file.filename or "uploaded_document"
    contents = await file.read()
    extracted_text = ""

    # 1. Document text extraction based on file extension
    if filename.lower().endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(contents))
            page_texts = [page.extract_text() for page in reader.pages if page.extract_text()]
            extracted_text = "\n".join(page_texts).strip()
        except Exception as e:
            print(f"[PDF Extraction Warning]: {e}")
            extracted_text = contents.decode("utf-8", errors="ignore")
    elif filename.lower().endswith((".json", ".txt", ".csv", ".md", ".log")):
        extracted_text = contents.decode("utf-8", errors="ignore").strip()
    else:
        extracted_text = f"Uploaded Document File: {filename}\nFile Size: {len(contents)} bytes"

    if not extracted_text:
        extracted_text = f"Uploaded Document: {filename}"

    # 2. Run Extraction Agent to structure vendor, invoice number, amount, date
    extracted_metadata = {}
    try:
        extracted_metadata = await extraction_agent.extract(extracted_text, workflow_type=wf_type)
    except Exception as e:
        print(f"[Document Extraction Agent Error]: {e}")

    item_ref = extracted_metadata.get("invoice_number") or extracted_metadata.get("claim_number") or extracted_metadata.get("application_id")
    vendor_ref = extracted_metadata.get("vendor_name") or extracted_metadata.get("employee_name") or extracted_metadata.get("company_name")
    amount_val = float(extracted_metadata.get("amount") or 0.0)
    date_val = extracted_metadata.get("invoice_date") or datetime.now().strftime("%Y-%m-%d")

    prefix = "INV" if wf_type == "invoice_fraud" else ("EXP" if wf_type == "expense_approval" else "VEN")
    invoice_number = item_ref or f"{prefix}-DOC-{int(datetime.utcnow().timestamp())}"
    vendor_name = vendor_ref or f"Doc: {filename}"

    invoice = Invoice(
        owner_id=current_user.id,
        workflow_type=wf_type,
        invoice_number=invoice_number,
        vendor_name=vendor_name,
        amount=amount_val,
        invoice_date=date_val,
        status="PENDING",
        reasoning=f"Uploaded Document File: {filename}\n\nExtracted Content:\n{extracted_text}",
        extra_data_json=json.dumps(extracted_metadata) if extracted_metadata else None,
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
def list_invoices(
    workflow_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Invoice).filter(Invoice.owner_id == current_user.id)
    if workflow_type and workflow_type != "all":
        query = query.filter(Invoice.workflow_type == workflow_type)
    return query.order_by(Invoice.id.desc()).all()


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
    """Standalone Extraction Agent endpoint converting raw text to structured JSON."""
    if not req.invoice_text or not req.invoice_text.strip():
        raise HTTPException(status_code=400, detail="invoice_text cannot be empty.")
    
    try:
        result = await extraction_agent.extract(req.invoice_text, workflow_type=req.workflow_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


async def _run_live_pipeline(invoice_text: str, db: Session, owner_id: Optional[int] = None, workflow_type: Optional[str] = "invoice_fraud") -> Dict[str, Any]:
    """Runs live 4-agent autonomous execution pipeline."""
    wf_type = workflow_type or "invoice_fraud"
    workflow = get_workflow(wf_type)
    trace = []

    # Step 1: Extraction Agent
    extracted = await extraction_agent.extract(invoice_text, workflow_type=wf_type)
    item_ref = extracted.get("invoice_number") or extracted.get("claim_number") or extracted.get("application_id")
    name_ref = extracted.get("vendor_name") or extracted.get("employee_name") or extracted.get("company_name") or "Unknown"
    amount_val = float(extracted.get("amount") or 0.0)

    trace.append({
        "agent": "Extraction Agent",
        "step": "Document Extraction",
        "status": "SUCCESS" if name_ref != "Unknown" else "WARNING",
        "thought": f"Extracted '{name_ref}', amount ${amount_val}, ref #{item_ref}.",
        "data": extracted
    })

    # Save/Update invoice record in SQLite DB
    inv_num = item_ref or f"REC-GEN-{db.query(Invoice).count()+1}"
    
    invoice = Invoice(
        owner_id=owner_id,
        workflow_type=wf_type,
        invoice_number=inv_num,
        vendor_name=name_ref,
        amount=amount_val,
        invoice_date=extracted.get("invoice_date") or datetime.now().strftime("%Y-%m-%d"),
        status="ANALYZING",
        extra_data_json=json.dumps(extracted)
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Step 2: Compute Deterministic Risk Signals BEFORE Risk Agent
    deterministic_signals = workflow.compute_heuristics(extracted, db, current_record_id=invoice.id)
    try:
        vendor_network = build_vendor_network(name_ref, db)
    except Exception:
        vendor_network = []

    # Step 3: Risk Agent
    risk_output = await risk_agent.analyze_risk(extracted, deterministic_signals, workflow_type=wf_type)
    trace.append({
        "agent": "Risk Agent",
        "step": "Risk & Anomaly Analysis",
        "status": "WARNING" if risk_output["calculated_risk_score"] > 30 else "SUCCESS",
        "thought": risk_output.get("thoughts", ""),
        "data": risk_output
    })

    # Step 4: Decision Agent
    decision_output = await decision_agent.decide(extracted, risk_output, workflow_type=wf_type)
    trace.append({
        "agent": "Decision Agent",
        "step": "Verdict Synthesis",
        "status": "INFO",
        "thought": decision_output.get("verdict_summary", ""),
        "data": decision_output
    })

    # Step 5: Critic Agent
    critic_output = await critic_agent.audit(extracted, risk_output, decision_output, workflow_type=wf_type)
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

    if final_verdict == "APPROVE":
        workflow.on_approved(invoice, extracted, db)

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
        f"From/Subject: {invoice.vendor_name}",
        f"Reference Number: {invoice.invoice_number}",
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

    wf_type = invoice.workflow_type or "invoice_fraud"
    workflow = get_workflow(wf_type)
    invoice_text = _build_invoice_text(invoice)

    async def event_generator():
        try:
            extracted = await extraction_agent.extract(invoice_text, workflow_type=wf_type)
            name_ref = extracted.get("vendor_name") or extracted.get("employee_name") or extracted.get("company_name") or invoice.vendor_name
            yield _format_sse_event({
                "agent_name": "Extraction Agent",
                "step_name": "Document Extraction",
                "status": "SUCCESS" if name_ref else "WARNING",
                "thought_process": f"Extracted '{name_ref}', amount ${extracted.get('amount') or invoice.amount}.",
                "output_data": extracted,
            })

            invoice_record = invoice
            invoice_record.status = "ANALYZING"
            invoice_record.invoice_number = extracted.get("invoice_number") or extracted.get("claim_number") or extracted.get("application_id") or invoice.invoice_number
            invoice_record.vendor_name = name_ref
            invoice_record.amount = float(extracted.get("amount") or invoice.amount or 0.0)
            invoice_record.invoice_date = extracted.get("invoice_date") or invoice.invoice_date
            if extracted:
                invoice_record.extra_data_json = json.dumps(extracted)
            db.commit()
            db.refresh(invoice_record)

            deterministic_signals = workflow.compute_heuristics(extracted, db, current_record_id=invoice_record.id)
            risk_output = await risk_agent.analyze_risk(extracted, deterministic_signals, workflow_type=wf_type)
            yield _format_sse_event({
                "agent_name": "Risk Agent",
                "step_name": "Risk & Anomaly Analysis",
                "status": "WARNING" if risk_output["calculated_risk_score"] > 30 else "SUCCESS",
                "thought_process": risk_output.get("thoughts", ""),
                "output_data": risk_output,
            })

            decision_output = await decision_agent.decide(extracted, risk_output, workflow_type=wf_type)
            yield _format_sse_event({
                "agent_name": "Decision Agent",
                "step_name": "Verdict Synthesis",
                "status": "INFO",
                "thought_process": decision_output.get("verdict_summary", ""),
                "output_data": decision_output,
            })

            critic_output = await critic_agent.audit(extracted, risk_output, decision_output, workflow_type=wf_type)
            final_verdict = critic_output.get("final_verdict", "ESCALATE")
            invoice_record.status = final_verdict
            invoice_record.flags_json = json.dumps([s.get("rule") for s in risk_output.get("risk_signals", [])])
            invoice_record.reasoning = decision_output.get("verdict_summary")
            invoice_record.critic_notes = critic_output.get("critic_notes")
            invoice_record.risk_signals_json = json.dumps(risk_output.get("risk_signals", []))
            invoice_record.confidence = float(decision_output.get("confidence") or 0.0)
            invoice_record.risk_score = float(risk_output.get("calculated_risk_score", 0.0))
            db.commit()

            if final_verdict == "APPROVE":
                workflow.on_approved(invoice_record, extracted, db)

            yield _format_sse_event({
                "agent_name": "Critic Agent",
                "step_name": "Governance Audit",
                "status": "SUCCESS" if final_verdict == "APPROVE" else "WARNING",
                "thought_process": critic_output.get("critic_notes", ""),
                "output_data": critic_output,
            })

            try:
                vendor_network = build_vendor_network(invoice_record.vendor_name, db)
            except Exception:
                vendor_network = []

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
        return await asyncio.wait_for(_run_live_pipeline(req.invoice_text, db, owner_id=current_user.id, workflow_type=req.workflow_type), timeout=8.0)
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

    if req.override.upper() in ["APPROVE", "APPROVED"]:
        workflow = get_workflow(invoice.workflow_type)
        workflow.on_approved(invoice, invoice.extra_data, db)

    return {
        "message": f"Invoice {invoice_id} human override applied: [{req.override}]",
        "invoice_id": invoice.id,
        "new_status": invoice.status,
        "human_override": invoice.human_override
    }
