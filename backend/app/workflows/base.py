from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session


class BaseWorkflow(ABC):
    workflow_type: str = "base"
    display_name: str = "Base Workflow"
    description: str = "Base workflow interface"
    item_label: str = "Item"
    queue_label: str = "Accounts Queue"

    @abstractmethod
    def get_extraction_prompt(self) -> str:
        pass

    @abstractmethod
    def parse_extraction_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def compute_heuristics(
        self, extracted_data: Dict[str, Any], db: Session, current_record_id: Optional[int] = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_risk_prompt(self) -> str:
        pass

    @abstractmethod
    def get_decision_prompt(self) -> str:
        pass

    @abstractmethod
    def get_critic_prompt(self) -> str:
        pass

    @abstractmethod
    def get_presets(self) -> Dict[str, Dict[str, Any]]:
        pass

    def on_approved(self, record: Any, extracted_data: Dict[str, Any], db: Session) -> None:
        """Optional hook executed when a record is approved (by pipeline or human override)."""
        pass
