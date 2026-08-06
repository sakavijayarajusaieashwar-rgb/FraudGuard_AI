from typing import Dict, Any
from ..llm.provider import llm_provider


class CriticAgent:
    SYSTEM_PROMPT = """
You are the Critic Agent for FraudGuard AI.
Your responsibility is to audit the Decision Agent's preliminary verdict against all evidence, enforcing governance boundaries and false-positive protection.

CRITICAL BOUNDARY INSTRUCTIONS:
1. If a DUPLICATE_INVOICE_NUMBER or VENDOR_TYPOSQUATTING flag exists, the verdict MUST be REJECT. Overriding to APPROVE is forbidden.
2. Evaluate if the Decision Agent was overly lenient (e.g., approving a borderline suspicious invoice with changed bank details or unusual PO format) or overly aggressive.
3. If you disagree with Decision Agent's proposal, set "agrees": false and set "final_verdict" to the corrected verdict ("ESCALATE" or "REJECT"), setting "critic_stamp": "OVERRIDDEN".

Output schema:
{
  "agrees": boolean,
  "final_verdict": "APPROVE" | "ESCALATE" | "REJECT",
  "critic_stamp": "VERIFIED" | "OVERRIDDEN",
  "critic_notes": "string"
}
"""

    async def audit(
        self,
        extracted_data: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        decision_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = (
            f"Extracted Invoice:\n{extracted_data}\n\n"
            f"Risk Analysis:\n{risk_analysis}\n\n"
            f"Decision Agent Proposal:\n{decision_output}"
        )

        result = await llm_provider.generate_json(
            system_instruction=self.SYSTEM_PROMPT,
            user_prompt=prompt
        )

        signals = risk_analysis.get("risk_signals", [])
        proposed = decision_output.get("verdict", "ESCALATE")
        has_hard_rule = any(s.get("rule") in ["DUPLICATE_INVOICE_NUMBER", "VENDOR_TYPOSQUATTING_SIMILARITY"] for s in signals)

        final_verdict = result.get("final_verdict") or proposed
        critic_stamp = result.get("critic_stamp") or "VERIFIED"
        critic_notes = result.get("critic_notes") or "Audit completed."

        if has_hard_rule and final_verdict != "REJECT":
            final_verdict = "REJECT"
            critic_stamp = "OVERRIDDEN"
            critic_notes = "Critic Override: Hard governance constraint (duplicate/typosquatting) mandates rejection."

        agrees = (final_verdict == proposed) and (critic_stamp == "VERIFIED")

        return {
            "agrees": agrees,
            "final_verdict": final_verdict,
            "critic_stamp": "VERIFIED" if agrees else "OVERRIDDEN",
            "critic_notes": critic_notes
        }
