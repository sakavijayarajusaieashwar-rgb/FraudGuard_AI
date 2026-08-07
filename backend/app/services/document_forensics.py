import json
import hashlib
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from ..models import Invoice, PurchaseOrder, GoodsReceipt, Vendor

def calculate_arithmetic_mismatch(line_items: List[Any], invoice_amount: float) -> Dict[str, Any]:
    """
    Deterministically computes line item quantity * unit price, subtotals,
    and checks if they match invoice amount and individual item totals.
    """
    errors = []
    calculated_sum = 0.0
    has_items = False

    for idx, item in enumerate(line_items):
        if not item:
            continue
        
        qty = None
        price = None
        claimed_total = None
        desc = ""

        if isinstance(item, dict):
            qty_val = item.get("quantity")
            price_val = item.get("unit_price")
            total_val = item.get("total")
            desc = item.get("description", f"Item {idx + 1}")

            try:
                if qty_val is not None:
                    qty = float(qty_val)
                if price_val is not None:
                    price = float(price_val)
                if total_val is not None:
                    claimed_total = float(total_val)
            except Exception:
                pass
        elif isinstance(item, str):
            desc = item
            # Look for pattern like "10 x $100.00" or "5 * 50"
            # Support diverse currency symbols
            match = re.search(r'(\d+)\s*(?:x|X|×|\*)\s*(?:[$\u20A8\u20B9\xA3\u20AC])?\s*([0-9,]+(?:\.[0-9]+)?)', item)
            if match:
                try:
                    qty = float(match.group(1))
                    price = float(match.group(2).replace(",", ""))
                except Exception:
                    pass
            
            # Look for claimed total at the end of string or after "="
            tot_match = re.search(r'(?:=|\bfor\b)\s*(?:[$\u20A8\u20B9\xA3\u20AC])?\s*([0-9,]+(?:\.[0-9]+)?)$', item)
            if tot_match:
                try:
                    claimed_total = float(tot_match.group(1).replace(",", ""))
                except Exception:
                    pass
            else:
                # Fallback: extract last number in the string
                all_nums = re.findall(r'([0-9,]+(?:\.[0-9]+)?)', item)
                if all_nums:
                    try:
                        claimed_total = float(all_nums[-1].replace(",", ""))
                    except Exception:
                        pass

        if qty is not None and price is not None:
            has_items = True
            expected_total = qty * price
            calculated_sum += expected_total

            if claimed_total is not None and abs(claimed_total - expected_total) > 0.01:
                errors.append(
                    f"Line '{desc[:30]}...': product ({qty} x {price} = {expected_total}) does not match claimed total ({claimed_total})"
                )
        elif claimed_total is not None:
            has_items = True
            calculated_sum += claimed_total

    # Compare calculated sum against claimed invoice total
    discrepancy = 0.0
    if has_items and invoice_amount is not None:
        discrepancy = abs(calculated_sum - invoice_amount)
        if discrepancy > 1.0: # Allow small rounding tolerance
            errors.append(
                f"Sum of line items (${calculated_sum:,.2f}) does not match invoice total (${invoice_amount:,.2f}). Discrepancy: ${discrepancy:,.2f}"
            )

    return {
        "has_items": has_items,
        "calculated_sum": calculated_sum,
        "discrepancy": discrepancy,
        "errors": errors
    }

def run_document_forensics(invoice: Invoice, db: Session) -> Dict[str, Any]:
    """
    Assembles deterministic forensic result for the invoice.
    Safely respects tenant isolation: only compares records owned by the same user.
    """
    extra = invoice.extra_data or {}
    
    # 1. Base Identifiers
    doc_id = invoice.id
    doc_type = extra.get("file_metadata", {}).get("file_type", "TXT").upper()
    
    claimed_vendor = invoice.vendor_name
    claimed_amount = invoice.amount
    claimed_po = extra.get("po_number")
    claimed_bank = extra.get("bank_account_number") or extra.get("bank_account")
    
    forensic_signals = []
    
    # Masking helpers
    def mask_acct(a):
        return f"****{a[-4:]}" if a and len(a) >= 4 else "****"

    masked_claimed_bank = mask_acct(claimed_bank) if claimed_bank else None

    # 2. Duplicate Document & Fingerprint Check
    doc_hash = extra.get("doc_hash")
    duplicate_hash_found = False
    if doc_hash:
        # Tenant Isolation: owner_id == invoice.owner_id is mandatory
        dup = db.query(Invoice).filter(
            Invoice.id != invoice.id,
            Invoice.owner_id == invoice.owner_id,
            Invoice.extra_data_json.like(f"%{doc_hash}%")
        ).first()
        if dup:
            duplicate_hash_found = True
            forensic_signals.append("DOCUMENT_HASH_DUPLICATE")

    # Duplicate Invoice Number / Reference Check
    dup_ref = db.query(Invoice).filter(
        Invoice.id != invoice.id,
        Invoice.owner_id == invoice.owner_id,
        Invoice.vendor_name == invoice.vendor_name,
        Invoice.invoice_number == invoice.invoice_number
    ).first()
    if dup_ref:
        forensic_signals.append("DUPLICATE_INVOICE_REFERENCE")

    # 3. File Type Validation
    filename = extra.get("file_metadata", {}).get("filename", "")
    if filename.lower().endswith(".pdf") and doc_type != "PDF":
        forensic_signals.append("DOCUMENT_TYPE_MISMATCH")

    # 4. Authoritative Procurement (PO) Comparison
    verified_po_vendor = None
    verified_po_amount = None
    comparison_vendor = "MATCH"
    comparison_amount = "MATCH"
    
    po = None
    gr = None
    if claimed_po:
        # Tenant Isolation: PO comparison is tenant-safe since PO table holds master data,
        # but we must verify that it matches PO record
        po_query = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == claimed_po)
        if invoice.owner_id:
            po_query = po_query.filter((PurchaseOrder.owner_id == invoice.owner_id) | (PurchaseOrder.owner_id == None))
        po = po_query.first()
        if po:
            verified_po_vendor = po.vendor_name
            verified_po_amount = po.amount

            if claimed_vendor and po.vendor_name and claimed_vendor.lower() != po.vendor_name.lower():
                comparison_vendor = "MISMATCH"
                forensic_signals.append("PO_VENDOR_MISMATCH")
            if claimed_amount is not None and po.amount is not None and abs(claimed_amount - po.amount) > 0.01:
                comparison_amount = "MISMATCH"
                forensic_signals.append("PO_AMOUNT_MISMATCH")
            
            gr_query = db.query(GoodsReceipt).filter(GoodsReceipt.po_number == claimed_po)
            if invoice.owner_id:
                gr_query = gr_query.filter((GoodsReceipt.owner_id == invoice.owner_id) | (GoodsReceipt.owner_id == None))
            gr = gr_query.first()
        else:
            comparison_vendor = "MISMATCH"
            comparison_amount = "MISMATCH"
            forensic_signals.append("MISSING_PURCHASE_ORDER")

    # 5. Trusted Vendor & Bank Account Comparison
    verified_bank = None
    comparison_bank = "MATCH"
    
    # Lookup historical approved invoices for this vendor to find verified bank accounts
    # Tenant Isolation: filter by owner_id to prevent leaking other tenants' bank details
    historical_approved_invoices = db.query(Invoice).filter(
        Invoice.vendor_name == claimed_vendor,
        Invoice.status.in_(["APPROVED", "APPROVE", "RELEASE"]),
        Invoice.id != invoice.id,
        Invoice.owner_id == invoice.owner_id
    ).all()

    known_banks = []
    for hist_inv in historical_approved_invoices:
        h_extra = hist_inv.extra_data or {}
        h_bank = h_extra.get("bank_account_number") or h_extra.get("bank_account")
        if h_bank and h_bank not in known_banks:
            known_banks.append(h_bank)

    if known_banks:
        verified_bank = mask_acct(known_banks[0]) # Primary historical bank account
        if claimed_bank:
            if claimed_bank not in known_banks:
                comparison_bank = "MISMATCH"
                forensic_signals.append("INVOICE_BANK_ACCOUNT_MISMATCH")
    else:
        # If no historical verified bank account exists, check if new bank is link to risk
        if claimed_bank:
            comparison_bank = "MATCH" # Default to MATCH if no baseline, but check graph below

    # 6. Graph Risk Correlation
    # Check if the bank account matches any previously rejected invoices for this user
    if claimed_bank:
        # Tenant Isolation: owner_id == invoice.owner_id is mandatory
        rejected_with_bank = db.query(Invoice).filter(
            Invoice.owner_id == invoice.owner_id,
            Invoice.status.in_(["REJECT", "HOLD", "REJECTED"]),
            Invoice.id != invoice.id,
            Invoice.extra_data_json.like(f"%{claimed_bank}%")
        ).first()

        if rejected_with_bank:
            forensic_signals.append("ENTITY_LINK_TO_PREVIOUS_RISK")

    # 7. Arithmetic Verification
    line_items = extra.get("line_items") or []
    arith_result = calculate_arithmetic_mismatch(line_items, claimed_amount)
    if arith_result["errors"]:
        forensic_signals.append("INVOICE_TOTAL_ARITHMETIC_MISMATCH")

    # 8. Determine Forensic Status
    # Categorical statuses: CONSISTENT, REVIEW, HIGH_RISK
    if "ENTITY_LINK_TO_PREVIOUS_RISK" in forensic_signals or "DOCUMENT_HASH_DUPLICATE" in forensic_signals:
        forensic_status = "HIGH_RISK"
    elif "INVOICE_BANK_ACCOUNT_MISMATCH" in forensic_signals or "PO_VENDOR_MISMATCH" in forensic_signals:
        forensic_status = "HIGH_RISK"
    elif len(forensic_signals) > 0:
        forensic_status = "REVIEW"
    else:
        forensic_status = "CONSISTENT"

    # Action recommendations
    if forensic_status == "HIGH_RISK":
        recommended_action = "HOLD PAYMENT. Verify payment instruction change through previously verified vendor contact information."
    elif forensic_status == "REVIEW":
        recommended_action = "REQUEST REVIEW. Inspect the document arithmetic and verify PO matching details manually."
    else:
        recommended_action = "APPROVE PAYMENT. Document metrics are consistent with verified company and procurement ledger records."

    three_way_match = compute_three_way_match_details(invoice, po, gr, extra)

    # Return structured result
    return {
        "document_id": doc_id,
        "document_type": doc_type,
        "forensic_status": forensic_status,
        "claimed_vendor": claimed_vendor,
        "claimed_bank": masked_claimed_bank,
        "claimed_amount": claimed_amount,
        "claimed_po": claimed_po,
        "verified_bank": verified_bank,
        "verified_po_vendor": verified_po_vendor,
        "verified_po_amount": verified_po_amount,
        "comparison_vendor": comparison_vendor,
        "comparison_amount": comparison_amount,
        "comparison_bank": comparison_bank,
        "forensic_signals": list(set(forensic_signals)),
        "recommended_action": recommended_action,
        "metadata": {
            "file_size": extra.get("file_metadata", {}).get("file_size"),
            "page_count": extra.get("file_metadata", {}).get("page_count"),
            "pdf_producer": extra.get("file_metadata", {}).get("pdf_producer"),
            "pdf_creator": extra.get("file_metadata", {}).get("pdf_creator"),
            "creation_date": extra.get("file_metadata", {}).get("creation_date"),
            "sha256_hash": doc_hash,
            "arithmetic_errors": arith_result["errors"]
        },
        "three_way_match": three_way_match
    }


def compute_three_way_match_details(invoice, po, gr, extra_data) -> Optional[Dict[str, Any]]:
    # If no po, return None
    if not po:
        return None
        
    # Get line items from invoice
    inv_lines = extra_data.get("line_items") or []
    po_lines = po.line_items or []
    gr_lines = gr.line_items if gr else []

    # Let's map PO lines, GR lines, and Invoice lines to compare them
    def parse_lines_to_structured(items):
        structured = []
        for idx, item in enumerate(items):
            if not item:
                continue
            if isinstance(item, dict):
                qty = item.get("quantity") or item.get("qty")
                price = item.get("unit_price") or item.get("price")
                desc = item.get("description") or f"Item {idx+1}"
                try:
                    structured.append({
                        "description": desc.strip(),
                        "qty": float(qty) if qty is not None else 1.0,
                        "price": float(price) if price is not None else 0.0
                    })
                except:
                    pass
            elif isinstance(item, str):
                # Pattern like "Enterprise Cloud Servers: 100 x $1000.00"
                qty = 1.0
                price = 0.0
                # Look for x/X/×/* multiplication pattern
                match = re.search(r'(\d+)\s*(?:x|X|×|\*)\s*(?:[$\u20A8\u20B9\xA3\u20AC])?\s*([0-9,]+(?:\.[0-9]+)?)', item)
                if match:
                    try:
                        qty = float(match.group(1))
                        price = float(match.group(2).replace(",", ""))
                    except:
                        pass
                else:
                    # Look for any number (price)
                    all_nums = re.findall(r'([0-9,]+(?:\.[0-9]+)?)', item)
                    if all_nums:
                        try:
                            price = float(all_nums[-1].replace(",", ""))
                        except:
                            pass
                structured.append({
                    "description": item.split(":")[0].strip(),
                    "qty": qty,
                    "price": price
                })
        return structured

    struct_inv = parse_lines_to_structured(inv_lines)
    struct_po = parse_lines_to_structured(po_lines)
    struct_gr = parse_lines_to_structured(gr_lines)

    match_items = []
    # If there's only 1 line item in each, match them directly!
    if len(struct_inv) == 1 and len(struct_po) == 1:
        inv_item = struct_inv[0]
        po_item = struct_po[0]
        gr_item = struct_gr[0] if struct_gr else {"qty": 0.0, "price": po_item["price"]}
        
        ord_qty = po_item["qty"]
        rec_qty = gr_item["qty"]
        inv_qty = inv_item["qty"]
        po_pr = po_item["price"]
        inv_pr = inv_item["price"]
        
        unsup_qty = max(0.0, inv_qty - rec_qty)
        unsup_amt = (unsup_qty * inv_pr) + (inv_qty * max(0.0, inv_pr - po_pr))
        
        is_qty_match = abs(inv_qty - rec_qty) <= 0.01 and abs(inv_qty - ord_qty) <= 0.01
        is_pr_match = abs(inv_pr - po_pr) <= 0.01
        status = "MATCH" if (is_qty_match and is_pr_match) else "MISMATCH"
        
        match_items.append({
            "description": inv_item["description"],
            "ordered_qty": ord_qty,
            "received_qty": rec_qty,
            "invoiced_qty": inv_qty,
            "po_price": po_pr,
            "invoice_price": inv_pr,
            "unsupported_qty": unsup_qty,
            "unsupported_amount": unsup_amt,
            "status": status
        })
    else:
        # Match by description overlap
        for inv_item in struct_inv:
            best_po = None
            for p in struct_po:
                if inv_item["description"].lower() in p["description"].lower() or p["description"].lower() in inv_item["description"].lower():
                    best_po = p
                    break
            if not best_po and struct_po:
                best_po = struct_po[0]
                
            best_gr = None
            if best_po:
                for g in struct_gr:
                    if best_po["description"].lower() in g["description"].lower() or g["description"].lower() in best_po["description"].lower():
                        best_gr = g
                        break
            if not best_gr and struct_gr:
                best_gr = struct_gr[0]
                
            ord_qty = best_po["qty"] if best_po else 0.0
            rec_qty = best_gr["qty"] if best_gr else 0.0
            inv_qty = inv_item["qty"]
            po_pr = best_po["price"] if best_po else 0.0
            inv_pr = inv_item["price"]
            
            unsup_qty = max(0.0, inv_qty - rec_qty)
            unsup_amt = (unsup_qty * inv_pr) + (inv_qty * max(0.0, inv_pr - po_pr))
            
            is_qty_match = abs(inv_qty - rec_qty) <= 0.01 and abs(inv_qty - ord_qty) <= 0.01
            is_pr_match = abs(inv_pr - po_pr) <= 0.01
            status = "MATCH" if (is_qty_match and is_pr_match) else "MISMATCH"
            
            match_items.append({
                "description": inv_item["description"],
                "ordered_qty": ord_qty,
                "received_qty": rec_qty,
                "invoiced_qty": inv_qty,
                "po_price": po_pr,
                "invoice_price": inv_pr,
                "unsupported_qty": unsup_qty,
                "unsupported_amount": unsup_amt,
                "status": status
            })

    total_unsupported_qty = sum(item["unsupported_qty"] for item in match_items)
    total_unsupported_amount = sum(item["unsupported_amount"] for item in match_items)
    overall_status = "MATCH" if all(item["status"] == "MATCH" for item in match_items) else "MISMATCH"
    
    return {
        "po_number": po.po_number,
        "grn_number": gr.grn_number if gr else "n/a",
        "status": overall_status,
        "items": match_items,
        "total_unsupported_qty": total_unsupported_qty,
        "total_unsupported_amount": total_unsupported_amount
    }
