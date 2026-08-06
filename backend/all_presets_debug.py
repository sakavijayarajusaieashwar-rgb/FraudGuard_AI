import os
import asyncio
import json

# Set LLM_PROVIDER to heuristic for fast, deterministic test validation
os.environ["LLM_PROVIDER"] = "heuristic"
os.environ["GEMINI_API_KEY"] = ""

from app.workflows.invoice_fraud import InvoiceFraudWorkflow
from app.agents.extraction import ExtractionAgent
from app.agents.risk import RiskAgent
from app.agents.decision import DecisionAgent
from app.agents.critic import CriticAgent
from app.database import SessionLocal, Base, engine
from app.models import Invoice, Vendor

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

async def test_preset(preset_key, preset_data, db):
    print(f"\n==================================================")
    print(f" TESTING PRESET: {preset_key.upper()}")
    print(f"==================================================")

    inv_num = preset_data["invoice_number"]
    if preset_key != "duplicate":
        db.query(Invoice).filter(Invoice.invoice_number == inv_num).delete()
        db.commit()
    else:
        existing = db.query(Invoice).filter(Invoice.invoice_number == inv_num).first()
        if not existing:
            prior = Invoice(
                owner_id=1,
                workflow_type="invoice_fraud",
                invoice_number=inv_num,
                vendor_name=preset_data["vendor_name"],
                amount=preset_data["amount"],
                invoice_date="2026-07-10",
                status="APPROVED"
            )
            db.add(prior)
            db.commit()

    v_name = preset_data["vendor_name"]
    if preset_key == "typosquat":
        base_v = "Apex Cloud Infrastructure Inc"
    else:
        base_v = v_name

    existing_v = db.query(Vendor).filter(Vendor.name == base_v).first()
    if not existing_v:
        avg_map = {
            "Apex Cloud Infrastructure Inc": 1450.00,
            "Global Office Supplies Co": 3200.00,
            "Vortex Digital Marketing Consultants": 8500.00,
            "Nexus Logistics & Express": 2500.00,
        }
        db.add(Vendor(
            name=base_v,
            tax_id=preset_data.get("tax_id", "US-EIN-00000000"),
            avg_invoice_amount=avg_map.get(base_v, preset_data["amount"]),
            is_known=True
        ))
        db.commit()

    raw_text = (
        f"From/Subject: {preset_data['vendor_name']}\n"
        f"Reference Number: {preset_data['invoice_number']}\n"
        f"Date: {preset_data['invoice_date']}\n"
        f"Total Amount: ${preset_data['amount']:,.2f}\n"
        f"Details:\n{preset_data['reasoning']}"
    )

    print("RAW INPUT TEXT:")
    print(raw_text)

    # 1. Extraction Agent
    extraction_agent = ExtractionAgent()
    extracted = await extraction_agent.extract(raw_text, workflow_type="invoice_fraud")
    print("\n1. EXTRACTION RESULT:")
    print(json.dumps(extracted, indent=2))

    # 2. Heuristics & Risk Agent
    wf = InvoiceFraudWorkflow()
    temp_inv = Invoice(
        owner_id=1,
        workflow_type="invoice_fraud",
        invoice_number=extracted.get("invoice_number") or preset_data["invoice_number"],
        vendor_name=extracted.get("vendor_name") or preset_data["vendor_name"],
        amount=float(extracted.get("amount") or preset_data["amount"]),
        invoice_date=extracted.get("invoice_date") or preset_data["invoice_date"],
        status="ANALYZING"
    )
    db.add(temp_inv)
    db.commit()
    db.refresh(temp_inv)

    try:
        deterministic_signals = wf.compute_heuristics(extracted, db, current_record_id=temp_inv.id)
        risk_agent = RiskAgent()
        risk_output = await risk_agent.analyze_risk(extracted, deterministic_signals, workflow_type="invoice_fraud")
        print("\n2. RISK AGENT RESULT:")
        print(f"Risk Score: {risk_output.get('calculated_risk_score')}")
        print("Risk Signals:", json.dumps(risk_output.get("risk_signals"), indent=2))

        # 3. Decision Agent
        decision_agent = DecisionAgent()
        decision_output = await decision_agent.decide(extracted, risk_output, workflow_type="invoice_fraud")
        print("\n3. DECISION AGENT RESULT:")
        print(f"Verdict: {decision_output.get('verdict')}")
        print(f"Summary: {decision_output.get('verdict_summary')}")

        # 4. Critic Agent
        critic_agent = CriticAgent()
        critic_output = await critic_agent.audit(extracted, risk_output, decision_output, workflow_type="invoice_fraud")
        print("\n4. CRITIC AGENT RESULT:")
        print(f"Final Verdict: {critic_output.get('final_verdict')}")
        print(f"Critic Stamp: {critic_output.get('critic_stamp')}")
        print(f"Critic Notes: {critic_output.get('critic_notes')}")

        return {
            "preset": preset_key,
            "extracted_vendor": extracted.get("vendor_name"),
            "extracted_inv_num": extracted.get("invoice_number"),
            "risk_score": risk_output.get("calculated_risk_score"),
            "risk_signals": [s.get("rule") for s in risk_output.get("risk_signals", [])],
            "final_verdict": critic_output.get("final_verdict")
        }
    finally:
        db.delete(temp_inv)
        db.commit()

async def main():
    wf = InvoiceFraudWorkflow()
    presets = wf.get_presets()
    db = SessionLocal()

    summary_results = []
    try:
        for p_key, p_data in presets.items():
            res = await test_preset(p_key, p_data, db)
            summary_results.append(res)
    finally:
        db.close()

    print("\n==================================================")
    print(" SUMMARY OF ALL PRESET TESTS")
    print("==================================================")
    for r in summary_results:
        print(f"Preset '{r['preset']}':")
        print(f"  Vendor Extracted: {r['extracted_vendor']}")
        print(f"  Invoice Number:  {r['extracted_inv_num']}")
        print(f"  Risk Score:      {r['risk_score']}")
        print(f"  Risk Flags:      {r['risk_signals']}")
        print(f"  Final Verdict:   {r['final_verdict']}")
        print("--------------------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
