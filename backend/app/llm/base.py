import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


def clean_json_markdown(text: str) -> str:
    """Strips markdown code blocks like ```json ... ``` from LLM outputs."""
    if not text:
        return "{}"
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_json(
        self, system_instruction: str, user_prompt: str, schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes LLM call with structured JSON output, prompt injection protection,
        and automatic JSON repair / retry logic.
        """
        pass
