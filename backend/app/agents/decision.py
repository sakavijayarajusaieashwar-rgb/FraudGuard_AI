from typing import Dict, Any, Optional
from ..llm.provider import llm_provider
from ..workflows import get_workflow


class DecisionAgent:
    async def decide(
        self,
        extracted_data: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        workflow_type: Optional[str] = "invoice_fraud"
    ) -> Dict[str, Any]:
        workflow = get_workflow(workflow_type)
        system_prompt = workflow.get_decision_prompt()

        score = float(risk_analysis.get("calculated_risk_score", 0.0))
        signals = risk_analysis.get("risk_signals", [])

        user_prompt = (
            f"Extracted Data:\n{extracted_data}\n\n"
            f"Calculated Risk Score: {score} / 100.0\n"
            f"Detected Risk Signals:\n{signals}\n"
            f"Risk Agent Rationale:\n{risk_analysis.get('thoughts', '')}"
        )

        result = await llm_provider.generate_json(
            system_instruction=system_prompt,
            user_prompt=user_prompt
        )

        # 1. Use the LLM's own verdict directly if valid
        raw_verdict = str(result.get("verdict") or "").strip().upper()
        if raw_verdict in ["APPROVE", "ESCALATE", "REJECT", "RELEASE", "HOLD"]:
            verdict = raw_verdict
        else:
            # Fallback only if model output is missing or invalid
            has_critical = any(s.get("severity") in ["CRITICAL", "HIGH"] for s in signals)
            if score > 65.0 or (has_critical and score > 40.0):
                verdict = "REJECT"
            elif score <= 25.0 and not has_critical:
                verdict = "RELEASE" if workflow_type == "customer_order" else "APPROVE"
            else:
                verdict = "HOLD" if workflow_type == "customer_order" else "ESCALATE"

        # 2. Extract or infer confidence score
        confidence = result.get("confidence")
        if confidence is None:
            if verdict in ["APPROVE", "RELEASE"]:
                confidence = 0.95 if score <= 15 else 0.85
            elif verdict in ["ESCALATE", "HOLD"]:
                confidence = 0.70
            else:
                confidence = 0.92
        else:
            try:
                confidence = float(confidence)
            except Exception:
                confidence = 0.88

        # 3. Build rich dynamic reasoning prose if model summary is missing or templated
        verdict_summary = result.get("verdict_summary")
        if not verdict_summary or "based on risk evaluation (score:" in str(verdict_summary):
            vendor = extracted_data.get("vendor_name") or "submitted entity"
            inv_num = extracted_data.get("invoice_number") or "document"
            amt = float(extracted_data.get("amount") or 0.0)
            amt_str = f"${amt:,.2f}" if amt > 0 else "unspecified amount"
            
            if workflow_type == "customer_order":
                if verdict == "RELEASE":
                    verdict_summary = f"Order {inv_num} for {vendor} ({amt_str}) passed payment verification. Payment matches the expected settled amount in the ledger."
                elif verdict == "REJECT":
                    flag_names = ", ".join(s.get("rule") for s in signals) if signals else "missing payment"
                    verdict_summary = f"Order {inv_num} for {vendor} ({amt_str}) has been REJECTED. Payment verification failed: {flag_names}."
                else:
                    verdict_summary = f"Order {inv_num} for {vendor} ({amt_str}) has been flagged for HOLD due to payment anomalies."
            else:
                if verdict == "APPROVE":
                    verdict_summary = (
                        f"Invoice {inv_num} from {vendor} for {amt_str} passed all automated risk evaluations cleanly. "
                        f"Vendor identity is verified and no duplicate records or unverified payment changes were flagged."
                    )
                elif verdict == "REJECT":
                    flag_names = ", ".join(s.get("rule") for s in signals) if signals else "critical risk thresholds"
                    verdict_summary = (
                        f"Invoice {inv_num} from {vendor} for {amt_str} has been REJECTED. "
                        f"Risk analysis flagged high-severity concerns ({flag_names}) requiring immediate rejection to protect enterprise funds."
                    )
                else:
                    verdict_summary = (
                        f"Invoice {inv_num} from {vendor} for {amt_str} has been flagged for ESCALATION to human accounts review. "
                        f"Risk score of {score}/100 indicates moderate anomalies that require manual audit before approval."
                    )

        return {
            "verdict": verdict,
            "confidence": confidence,
            "verdict_summary": verdict_summary
        }
