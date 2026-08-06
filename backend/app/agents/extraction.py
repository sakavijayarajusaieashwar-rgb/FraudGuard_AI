from typing import Dict, Any
from ..llm.provider import llm_provider


class ExtractionAgent:
    SYSTEM_PROMPT = """
You are the Extraction Agent for FraudGuard AI.
Your ONLY responsibility is to read raw invoice text and extract structured financial fields into valid JSON.

CRITICAL INSTRUCTIONS:
1. Extract ONLY information explicitly supported by the invoice text inside <invoice_text>.
2. Never guess or invent missing values. If a field is missing, return null (None).
3. Normalize dates to YYYY-MM-DD format if possible.
4. Convert currency amounts to numeric float values (e.g., "$1,450.00" -> 1450.0).
5. Do NOT perform any fraud analysis, risk assessment, or decision making.

Output schema:
{
  "vendor_name": "string or null",
  "invoice_number": "string or null",
  "amount": float or null,
  "invoice_date": "YYYY-MM-DD or null",
  "line_items": ["string"],
  "tax_id": "string or null",
  "po_number": "string or null"
}
"""

    async def extract(self, invoice_text: str) -> Dict[str, Any]:
        result = await llm_provider.generate_json(
            system_instruction=self.SYSTEM_PROMPT,
            user_prompt=invoice_text
        )
        return {
            "vendor_name": result.get("vendor_name"),
            "invoice_number": result.get("invoice_number"),
            "amount": float(result["amount"]) if result.get("amount") is not None else None,
            "invoice_date": result.get("invoice_date"),
            "line_items": result.get("line_items") if isinstance(result.get("line_items"), list) else [],
            "tax_id": result.get("tax_id"),
            "po_number": result.get("po_number"),
        }
