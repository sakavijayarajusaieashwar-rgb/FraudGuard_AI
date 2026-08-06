import asyncio
import json
from app.workflows.invoice_fraud import InvoiceFraudWorkflow
from app.agents.extraction import ExtractionAgent

async def test():
    wf = InvoiceFraudWorkflow()
    presets = wf.get_presets()
    clean = presets['clean']

    raw_text = (
        f"From/Subject: {clean['vendor_name']}\n"
        f"Reference Number: {clean['invoice_number']}\n"
        f"Date: {clean['invoice_date']}\n"
        f"Total Amount: ${clean['amount']:,.2f}\n"
        f"Details:\n{clean['reasoning']}"
    )

    print("=== 1. EXACT RAW INVOICE TEXT ===")
    print(raw_text)
    print("\n=== 2. SYSTEM EXTRACTION PROMPT ===")
    print(wf.get_extraction_prompt())

    print("\n=== 3. RUNNING EXTRACTION AGENT ===")
    extracted = await ExtractionAgent().extract(raw_text, workflow_type="invoice_fraud")
    print("Extracted Data:", json.dumps(extracted, indent=2))

if __name__ == "__main__":
    asyncio.run(test())
