from typing import Dict, Any, Optional
from ..llm.provider import llm_provider
from ..workflows import get_workflow


class ExtractionAgent:
    async def extract(self, input_text: str, workflow_type: Optional[str] = "invoice_fraud") -> Dict[str, Any]:
        workflow = get_workflow(workflow_type)
        system_prompt = workflow.get_extraction_prompt()
        result = await llm_provider.generate_json(
            system_instruction=system_prompt,
            user_prompt=input_text
        )
        return workflow.parse_extraction_result(result)
