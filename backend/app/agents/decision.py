from typing import Dict, Any
from ..llm.provider import llm_provider


class DecisionAgent:
    SYSTEM_PROMPT = """
You are the Decision Agent for FraudGuard AI.
Your responsibility is to evaluate aggregated risk signals and synthesize a preliminary verdict.

CRITICAL INSTRUCTIONS:
1. Verdict MUST be one of: "APPROVE", "ESCALATE", "REJECT".
2. Rule Guidelines:
   - Risk Score <= 25.0 AND no Critical/High flags -> "APPROVE"
   - Risk Score between 25.0 and 65.0 OR medium flags -> "ESCALATE"
   - Risk Score > 65.0 OR duplicate invoice flag OR typosquatting -> "REJECT"

Output schema:
{
  "verdict": "APPROVE" | "ESCALATE" | "REJECT",
  "confidence": float (0.0 to 1.0),
  "verdict_summary": "string"
}
"""

    async def decide(
        self, extracted_data: Dict[str, Any], risk_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = (
            f"Extracted Invoice:\n{extracted_data}\n\n"
            f"Risk Analysis:\n{risk_analysis}"
        )

        result = await llm_provider.generate_json(
            system_instruction=self.SYSTEM_PROMPT,
            user_prompt=prompt
        )

        score = float(risk_analysis.get("calculated_risk_score", 0.0))
        signals = risk_analysis.get("risk_signals", [])
        has_critical = any(s.get("severity") in ["CRITICAL", "HIGH"] for s in signals)

        verdict = result.get("verdict", "ESCALATE").upper()
        if score > 65.0 or (has_critical and score > 40.0):
            verdict = "REJECT"
        elif score <= 25.0 and not has_critical:
            verdict = "APPROVE"

        confidence = result.get("confidence")
        if confidence is None:
            if verdict == "APPROVE":
                confidence = 0.92 if score <= 15 and not has_critical else 0.78
            elif verdict == "ESCALATE":
                confidence = 0.62 if score < 55 else 0.52
            else:
                confidence = 0.94 if has_critical or score >= 75 else 0.78

        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.90

        return {
            "verdict": verdict,
            "confidence": confidence,
            "verdict_summary": result.get("verdict_summary") or f"Verdict [{verdict}] issued based on risk score {score}/100."
        }
