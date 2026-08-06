import json
import hashlib
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import Invoice, PaymentLedger

def get_bank_hash(account_num: str) -> str:
    if not account_num:
        return ""
    # Create a stable short hash to represent the account securely
    return hashlib.sha256(account_num.strip().encode('utf-8')).hexdigest()[:12]

def get_bank_mask(account_num: str) -> str:
    if not account_num:
        return ""
    num = account_num.strip()
    return f"****{num[-4:]}" if len(num) >= 4 else "****" + num

def construct_fraud_graph(db: Session, user_id: int) -> Dict[str, Any]:
    invoices = db.query(Invoice).filter(Invoice.owner_id == user_id).all()
    
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    
    # Track created nodes to prevent duplicates
    seen_nodes = set()
    
    def add_node(node_id: str, node_type: str, label: str, risk_level: str, metadata: Dict[str, Any]):
        if node_id not in seen_nodes:
            nodes.append({
                "id": node_id,
                "type": node_type,
                "label": label,
                "risk_level": risk_level,
                "metadata": metadata
            })
            seen_nodes.add(node_id)
            
    def add_edge(source: str, target: str, relationship: str, evidence: str):
        # Prevent self-loops
        if source == target:
            return
        # Prevent duplicate edges
        edge_key = f"{source}-{target}-{relationship}"
        if not any(f"{e['source']}-{e['target']}-{e['relationship']}" == edge_key for e in edges):
            edges.append({
                "source": source,
                "target": target,
                "relationship": relationship,
                "evidence": evidence
            })

    for inv in invoices:
        inv_id = f"invoice-{inv.id}"
        inv_risk = "HIGH" if inv.status in ["REJECT", "HOLD"] else ("MEDIUM" if inv.status == "ESCALATE" else "LOW")
        
        # Determine if invoice represents customer order or supplier invoice
        is_order = inv.workflow_type == "customer_order"
        node_label = f"Order #{inv.invoice_number}" if is_order else f"Invoice #{inv.invoice_number}"
        node_type = "ORDER" if is_order else "INVOICE"
        
        # Add the Invoice/Order node itself
        add_node(inv_id, node_type, node_label, inv_risk, {
            "amount": inv.amount,
            "status": inv.status,
            "workflow_type": inv.workflow_type
        })
        
        # Extract and add Vendor / Customer node
        entity_name = inv.vendor_name
        entity_id = f"entity-{entity_name.replace(' ', '_').lower()}"
        entity_type = "CUSTOMER" if is_order else "VENDOR"
        add_node(entity_id, entity_type, entity_name, inv_risk if inv_risk == "HIGH" else "LOW", {
            "tax_id": inv.extra_data.get("tax_id") if inv.extra_data else None
        })
        
        # Link entity to invoice/order
        if is_order:
            add_edge(entity_id, inv_id, "PLACED", f"Placed customer order {inv.invoice_number}")
        else:
            add_edge(entity_id, inv_id, "SUBMITTED", f"Submitted invoice {inv.invoice_number}")
            
        # Extract bank account if present (for Money Out)
        bank_account = inv.extra_data.get("bank_account_number") or inv.extra_data.get("bank_account")
        if not bank_account and inv.extra_data_json:
            try:
                extra = json.loads(inv.extra_data_json)
                bank_account = extra.get("bank_account_number") or extra.get("bank_account")
            except:
                pass
                
        if bank_account:
            bank_id = f"bank-{get_bank_hash(bank_account)}"
            bank_mask = get_bank_mask(bank_account)
            
            # Determine bank account risk based on invoice status
            bank_risk = "HIGH" if inv.status in ["REJECT", "HOLD"] else "LOW"
            
            add_node(bank_id, "BANK_ACCOUNT", bank_mask, bank_risk, {
                "masked_account": bank_mask
            })
            
            add_edge(inv_id, bank_id, "REFERENCES", f"Directs payment to {bank_mask}")
            add_edge(entity_id, bank_id, "USES", f"Uses bank account {bank_mask}")
            
        # Extract transaction claimed (for Goods Out)
        tx_ref = inv.extra_data.get("transaction_reference")
        if not tx_ref and inv.extra_data_json:
            try:
                extra = json.loads(inv.extra_data_json)
                tx_ref = extra.get("transaction_reference")
            except:
                pass
                
        if tx_ref:
            tx_id = f"tx-{tx_ref.replace(' ', '_').lower()}"
            add_node(tx_id, "TRANSACTION", f"Txn {tx_ref}", "LOW", {
                "reference": tx_ref
            })
            add_edge(inv_id, tx_id, "PAID_BY", f"Claimed payment transaction {tx_ref}")
            
            # Link transaction to the ledger record if exists
            ledger_txn = db.query(PaymentLedger).filter(PaymentLedger.transaction_reference == tx_ref).first()
            if ledger_txn:
                ledger_node_id = f"ledger-{ledger_txn.id}"
                ledger_label = f"Ledger {ledger_txn.transaction_reference}"
                ledger_risk = "LOW" if ledger_txn.status == "SETTLED" else "MEDIUM"
                add_node(ledger_node_id, "LEDGER_PAYMENT", ledger_label, ledger_risk, {
                    "status": ledger_txn.status,
                    "amount": ledger_txn.amount,
                    "beneficiary": ledger_txn.beneficiary_name,
                })
                add_edge(tx_id, ledger_node_id, "RECORDED_IN", f"Transaction {tx_ref} recorded in payment ledger")
                if ledger_txn.beneficiary_name and bank_account:
                    add_edge(ledger_node_id, bank_id, "SETTLES_TO", f"Ledger payment settles to bank account {bank_mask}")
                elif ledger_txn.beneficiary_name:
                    add_node(f"beneficiary-{ledger_txn.beneficiary_name.replace(' ', '_').lower()}", "BENEFICIARY", ledger_txn.beneficiary_name, "LOW", {})
                    add_edge(ledger_node_id, f"beneficiary-{ledger_txn.beneficiary_name.replace(' ', '_').lower()}", "BENEFICIARY", f"Payment goes to {ledger_txn.beneficiary_name}")
                
    return {
        "nodes": nodes,
        "edges": edges
    }
