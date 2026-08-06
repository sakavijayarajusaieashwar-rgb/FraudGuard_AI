from typing import Dict, Optional, List
from .base import BaseWorkflow
from .invoice_fraud import InvoiceFraudWorkflow
from .expense_approval import ExpenseApprovalWorkflow
from .vendor_onboarding import VendorOnboardingWorkflow
from .customer_order import CustomerOrderWorkflow

_registry: Dict[str, BaseWorkflow] = {}


def register_workflow(workflow: BaseWorkflow) -> None:
    _registry[workflow.workflow_type] = workflow


def get_workflow(workflow_type: Optional[str] = None) -> BaseWorkflow:
    if not workflow_type or workflow_type not in _registry:
        return _registry["invoice_fraud"]
    return _registry[workflow_type]


def list_workflows() -> List[Dict[str, str]]:
    return [
        {
            "workflow_type": wf.workflow_type,
            "display_name": wf.display_name,
            "description": wf.description,
            "item_label": wf.item_label,
            "queue_label": wf.queue_label,
        }
        for wf in _registry.values()
    ]


# Register standard workflows
register_workflow(InvoiceFraudWorkflow())
register_workflow(ExpenseApprovalWorkflow())
register_workflow(VendorOnboardingWorkflow())
register_workflow(CustomerOrderWorkflow())
