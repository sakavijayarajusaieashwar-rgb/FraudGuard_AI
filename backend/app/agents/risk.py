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
            f"Pre-computed Deterministic Risk Signals (including Behavioral Context):\n{deterministic_signals}"
        )
        
        result = await llm_provider.generate_json(
            system_instruction=system_prompt,
            user_prompt=prompt
        )

        final_score = float(deterministic_signals.get("deterministic_risk_score", 0.0))

        signals = result.get("risk_signals") or []
        det_flags = deterministic_signals.get("flags") or []
        
        # Merge deterministic flags into risk signals list if missing
        for df in det_flags:
            if not any(s.get("rule") == df.get("flag") for s in signals):
                signals.append({
                    "rule": df.get("flag"),
                    "category": df.get("category", "OTHER"),
                    "severity": df.get("severity"),
                    "description": df.get("details")
                })

        return {
            "calculated_risk_score": final_score,
            "risk_signals": signals,
            "category_scores": deterministic_signals.get("category_scores", {}),
            "thoughts": result.get("thoughts") or f"Synthesized {len(signals)} risk signals with deterministic score {final_score}/100."
        }
