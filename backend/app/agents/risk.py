from typing import Dict, Any, Optional
from ..llm.provider import llm_provider
from ..workflows import get_workflow


class RiskAgent:
    async def analyze_risk(
        self,
        extracted_data: Dict[str, Any],
        deterministic_signals: Dict[str, Any],
        workflow_type: Optional[str] = "invoice_fraud"
    ) -> Dict[str, Any]:
        workflow = get_workflow(workflow_type)
        system_prompt = workflow.get_risk_prompt()

        prompt = (
            f"Extracted Data:\n{extracted_data}\n\n"
            f"Pre-computed Deterministic Risk Signals:\n{deterministic_signals}"
        )
        
        result = await llm_provider.generate_json(
            system_instruction=system_prompt,
            user_prompt=prompt
        )

        det_score = float(deterministic_signals.get("deterministic_risk_score", 0.0))
        llm_score = float(result.get("calculated_risk_score") or det_score)
        final_score = min(100.0, max(det_score, llm_score))

        signals = result.get("risk_signals") or []
        det_flags = deterministic_signals.get("flags") or []
        
        # Merge deterministic flags into risk signals list if missing
        for df in det_flags:
            if not any(s.get("rule") == df.get("flag") for s in signals):
                signals.append({
                    "rule": df.get("flag"),
                    "severity": df.get("severity"),
                    "description": df.get("details")
                })

        return {
            "calculated_risk_score": final_score,
            "risk_signals": signals,
            "thoughts": result.get("thoughts") or f"Synthesized {len(signals)} risk signals with deterministic score {det_score}/100."
        }
