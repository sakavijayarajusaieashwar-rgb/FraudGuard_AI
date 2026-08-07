from typing import Dict, Any, Optional
from ..llm.provider import llm_provider
from ..workflows import get_workflow


class CriticAgent:
    async def audit(
        self,
        extracted_data: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        decision_output: Dict[str, Any],
        workflow_type: Optional[str] = "invoice_fraud"
    ) -> Dict[str, Any]:
        workflow = get_workflow(workflow_type)
        system_prompt = workflow.get_critic_prompt()

        prompt = (
            f"Extracted Data:\n{extracted_data}\n\n"
            f"Risk Analysis:\n{risk_analysis}\n\n"
            f"Decision Agent Proposal:\n{decision_output}"
        )

        result = await llm_provider.generate_json(
            system_instruction=system_prompt,
            user_prompt=prompt
        )

        signals = risk_analysis.get("risk_signals", [])
        default_verdict = "HOLD" if workflow_type == "customer_order" else "ESCALATE"
        proposed = decision_output.get("verdict", default_verdict)
        has_hard_rule = any(
            s.get("rule") in [
                "DUPLICATE_INVOICE_NUMBER",
                "VENDOR_TYPOSQUATTING_SIMILARITY",
                "DUPLICATE_EXPENSE_CLAIM",
                "VENDOR_NAME_SIMILARITY",
                "PAYMENT_NOT_FOUND",
                "PAYMENT_AMOUNT_MISMATCH",
                "ORDER_REFERENCE_MISMATCH",
                "ENTITY_LINK_TO_PREVIOUS_RISK",
                "DOCUMENT_HASH_DUPLICATE",
                "INVOICE_BANK_ACCOUNT_MISMATCH"
            ]
            for s in signals
        )

        final_verdict = result.get("final_verdict") or proposed
        critic_stamp = result.get("critic_stamp") or "VERIFIED"
        critic_notes = result.get("critic_notes") or "Audit completed."

        if has_hard_rule and final_verdict != "REJECT":
            final_verdict = "REJECT"
            critic_stamp = "OVERRIDDEN"
            critic_notes = "Critic Override: Hard governance constraint mandates rejection."

        agrees = (final_verdict == proposed) and (critic_stamp == "VERIFIED")

        return {
            "agrees": agrees,
            "final_verdict": final_verdict,
            "critic_stamp": "VERIFIED" if agrees else "OVERRIDDEN",
            "critic_notes": critic_notes
        }
