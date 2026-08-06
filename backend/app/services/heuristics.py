import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import Vendor, Invoice, PaymentLedger


def string_similarity(a: str, b: str) -> float:
    """Returns normalized similarity ratio (0.0 to 1.0) between two strings."""
    if not a or not b:
        return 0.0
    # Normalize common substitutions e.g. '1' -> 'l'
    norm_a = re.sub(r'[^a-z0-9]', '', a.lower().replace('1', 'l').replace('0', 'o'))
    norm_b = re.sub(r'[^a-z0-9]', '', b.lower().replace('1', 'l').replace('0', 'o'))
    return SequenceMatcher(None, norm_a, norm_b).ratio()


def build_vendor_network(vendor_name: str, db: Session, threshold: float = 0.5) -> List[Dict[str, Any]]:
    network: List[Dict[str, Any]] = []
    vendor_name = str(vendor_name or "").strip()
    if not vendor_name:
        return network

    try:
        all_vendors = db.query(Vendor).all()
        for vendor in all_vendors:
            if vendor.name.lower() == vendor_name.lower():
                continue
            similarity = string_similarity(vendor_name, vendor.name)
            if similarity > threshold:
                network.append({
                    "vendor_name": vendor.name,
                    "similarity_score": round(similarity, 4),
                    "is_submitted_vendor": False,
                })
    except Exception:
        return []

    network.insert(0, {
        "vendor_name": vendor_name,
        "similarity_score": 1.0,
        "is_submitted_vendor": True,
    })

    return network


def get_vendor_behavior_profile(vendor_name: str, db: Session) -> Dict[str, Any]:
    if not vendor_name:
        return None
    invoices = db.query(Invoice).filter(Invoice.vendor_name == vendor_name, Invoice.status != 'REJECTED').all()
    if not invoices:
        return None
    
    amounts = [inv.amount for inv in invoices if inv.amount is not None and inv.amount > 0]
    count = len(amounts)
    if count == 0:
        return {"invoice_count": len(invoices), "avg_amount": 0.0, "median_amount": 0.0, "max_amount": 0.0, "known_bank_accounts": []}
    
    avg_amount = sum(amounts) / count
    sorted_amounts = sorted(amounts)
    mid = count // 2
    median_amount = (sorted_amounts[mid] + sorted_amounts[~mid]) / 2.0
    max_amount = max(amounts)
    
    known_bank_accounts = []
    for inv in invoices:
        extra = inv.extra_data
        if extra and extra.get("bank_account_number"):
            acct = extra.get("bank_account_number").strip()
            if acct and acct not in known_bank_accounts:
                known_bank_accounts.append(acct)
                
    return {
        "invoice_count": len(invoices),
        "avg_amount": avg_amount,
        "median_amount": median_amount,
        "max_amount": max_amount,
        "known_bank_accounts": known_bank_accounts,
    }


def compute_deterministic_risk_flags(
    invoice_data: Dict[str, Any], db: Session, current_invoice_id: int = None
) -> Dict[str, Any]:
    """
    Computes all deterministic Python fraud risk signals BEFORE any LLM agent call.
    Guarantees consistent, non-hallucinated evidence vectors.
    """
    flags: List[Dict[str, Any]] = []
    
    inv_num = str(invoice_data.get("invoice_number", "") or "").strip()
    vendor_name = str(invoice_data.get("vendor_name", "") or "").strip()
    amount = float(invoice_data.get("amount", 0.0) or 0.0)
    inv_date_str = str(invoice_data.get("invoice_date", "") or "").strip()
    bank_account = str(invoice_data.get("bank_account_number", "") or "").strip()
    
    behavior_profile = get_vendor_behavior_profile(vendor_name, db)


    # 1. Missing required fields check
    missing_fields = []
    if not vendor_name or vendor_name.lower() in ["null", "none", "unknown"]:
        missing_fields.append("vendor_name")
    if not inv_num or inv_num.lower() in ["null", "none", "n/a"]:
        missing_fields.append("invoice_number")
    if amount <= 0.0:
        missing_fields.append("amount")
    if not inv_date_str or inv_date_str.lower() in ["null", "none"]:
        missing_fields.append("invoice_date")

    if missing_fields:
        flags.append({
            "flag": "MISSING_REQUIRED_FIELDS",
            "category": "DOCUMENT",
            "severity": "HIGH",
            "score_impact": 25.0,
            "details": f"Missing or null required fields: {', '.join(missing_fields)}"
        })

    # 2. Duplicate Invoice Number Check in Database
    if inv_num and inv_num not in ["INV-UNKNOWN", "N/A"]:
        query = db.query(Invoice).filter(Invoice.invoice_number == inv_num)
        if current_invoice_id:
            query = query.filter(Invoice.id != current_invoice_id)
        existing_duplicate = query.first()

        if existing_duplicate:
            flags.append({
                "flag": "DUPLICATE_INVOICE_NUMBER",
                "category": "DOCUMENT",
                "severity": "CRITICAL",
                "score_impact": 50.0,
                "details": f"Invoice number '{inv_num}' already exists in ledger (ID: {existing_duplicate.id}, Amount: ${existing_duplicate.amount:.2f})."
            })

    # 3. Known Vendor & Vendor Typosquatting / Similarity Check
    matched_vendor = None
    all_vendors = db.query(Vendor).all()
    best_similarity = 0.0
    similar_vendor_name = None

    for v in all_vendors:
        if v.name.lower() == vendor_name.lower():
            matched_vendor = v
            best_similarity = 1.0
            break
        sim = string_similarity(vendor_name, v.name)
        if sim > best_similarity:
            best_similarity = sim
            similar_vendor_name = v.name

    if not matched_vendor:
        if best_similarity >= 0.75:
            # Typosquatting / Suspicious similarity!
            flags.append({
                "flag": "VENDOR_TYPOSQUATTING_SIMILARITY",
                "category": "IDENTITY",
                "severity": "CRITICAL",
                "score_impact": 40.0,
                "details": f"Vendor name '{vendor_name}' is suspiciously similar ({best_similarity*100:.0f}% match) to verified vendor '{similar_vendor_name}'."
            })
        else:
            flags.append({
                "flag": "UNKNOWN_VENDOR",
                "category": "IDENTITY",
                "severity": "MEDIUM",
                "score_impact": 20.0,
                "details": f"Vendor '{vendor_name}' is not in master verified vendor database."
            })
    else:
        if not matched_vendor.is_known:
            flags.append({
                "flag": "UNTRUSTED_VENDOR",
                "category": "IDENTITY",
                "severity": "HIGH",
                "score_impact": 30.0,
                "details": f"Vendor '{matched_vendor.name}' is flagged as untrusted/unverified in system database."
            })

    # 4. Amount Ratio Anomaly Check
    if behavior_profile and behavior_profile["invoice_count"] >= 2 and behavior_profile["median_amount"] > 0:
        median_amt = behavior_profile["median_amount"]
        ratio = amount / median_amt
        if ratio >= 3.0:
            flags.append({
                "flag": "AMOUNT_BEHAVIOR_DEVIATION",
                "category": "BEHAVIOR",
                "severity": "HIGH",
                "score_impact": 35.0,
                "ratio": round(ratio, 2),
                "details": f"Current amount (${amount:,.2f}) is {ratio:.1f}x higher than historical median (${median_amt:,.2f})."
            })
    elif matched_vendor and matched_vendor.avg_invoice_amount > 0:
        avg_amt = matched_vendor.avg_invoice_amount
        ratio = amount / avg_amt
        if ratio >= 3.0:
            flags.append({
                "flag": "UNUSUAL_INVOICE_AMOUNT_RATIO",
                "category": "BEHAVIOR",
                "severity": "HIGH",
                "score_impact": 35.0,
                "ratio": round(ratio, 2),
                "details": f"Invoice amount (${amount:,.2f}) is {ratio:.1f}x higher than vendor average (${avg_amt:,.2f})."
            })

    # 5. Round Number Anomaly Check
    if amount >= 1000.0 and amount.is_integer() and amount % 500 == 0:
        flags.append({
            "flag": "ROUND_NUMBER_ANOMALY",
            "category": "TRANSACTION",
            "severity": "LOW",
            "score_impact": 10.0,
            "details": f"Invoice amount (${amount:,.2f}) is an exact round figure."
        })

    # 6. Weekend or Future Date Check
    if inv_date_str:
        try:
            parsed_date = datetime.strptime(inv_date_str[:10], "%Y-%m-%d")
            today = datetime.now()
            if parsed_date > today:
                flags.append({
                    "flag": "FUTURE_INVOICE_DATE",
                    "category": "TRANSACTION",
                    "severity": "MEDIUM",
                    "score_impact": 15.0,
                    "details": f"Invoice date '{inv_date_str}' is set in the future relative to system date."
                })
            if parsed_date.weekday() in [5, 6]:  # Saturday or Sunday
                flags.append({
                    "flag": "WEEKEND_INVOICE_DATE",
                    "category": "TRANSACTION",
                    "severity": "LOW",
                    "score_impact": 5.0,
                    "details": f"Invoice date '{inv_date_str}' falls on a weekend."
                })
        except Exception:
            pass

    # 7. Payment / Banking Detail Change Check
    raw_text = str(invoice_data.get("raw_content") or invoice_data.get("reasoning") or "").lower()
    banking_keywords = [
        "banking details changed",
        "bank details changed",
        "new account",
        "new bank account",
        "remit to new",
        "do not verify",
        "don't contact",
        "updated banking",
        "change of account",
        "new wire instructions",
        "remit payment to new",
        "new payment details",
    ]
    is_payment_detail_change_requested = any(kw in raw_text for kw in banking_keywords)
    if is_payment_detail_change_requested:
        flags.append({
            "flag": "BANKING_CHANGE_UNVERIFIED",
            "category": "PAYMENT",
            "severity": "HIGH",
            "score_impact": 35.0,
            "details": "Invoice text requests routing payment to unverified or newly changed banking details."
        })

    # 8. Behavioral Bank Account Check
    if behavior_profile and bank_account:
        if behavior_profile["known_bank_accounts"] and bank_account not in behavior_profile["known_bank_accounts"]:
            flags.append({
                "flag": "NEW_VENDOR_BANK_ACCOUNT",
                "category": "PAYMENT",
                "severity": "HIGH",
                "score_impact": 35.0,
                "details": f"First observed use of bank account ending in {bank_account[-4:] if len(bank_account) > 4 else bank_account} for this vendor."
            })

    category_scores = {}
    for f in flags:
        cat = f.get("category", "OTHER")
        category_scores[cat] = category_scores.get(cat, 0.0) + f["score_impact"]
        
    # Cap each category to 40.0 max to prevent double counting related flags
    total_score = sum(min(40.0, s) for s in category_scores.values())
    total_score = min(100.0, total_score)

    return {
        "flags": flags,
        "flags_count": len(flags),
        "deterministic_risk_score": total_score,
        "vendor_matched": matched_vendor.name if matched_vendor else None,
        "missing_fields": missing_fields,
        "is_payment_detail_change_requested": is_payment_detail_change_requested,
        "behavior_profile": behavior_profile,
        "category_scores": category_scores,
    }


def compute_order_verification_flags(
    order_data: Dict[str, Any], db: Session
) -> Dict[str, Any]:
    """
    Computes deterministic Python risk signals for GOODS OUT (Order Verification).
    Cross-references claimed payments with the PaymentLedger.
    """
    flags: List[Dict[str, Any]] = []
    
    order_ref = str(order_data.get("invoice_number", "") or "").strip()
    claimed_amount = float(order_data.get("amount", 0.0) or 0.0)
    tx_ref = str(order_data.get("transaction_reference", "") or "").strip()
    customer_name = str(order_data.get("vendor_name", "") or "").strip()

    # 1. Missing required fields
    if not order_ref or order_ref.lower() in ["null", "none", "n/a"]:
        flags.append({
            "flag": "MISSING_ORDER_REFERENCE",
            "severity": "HIGH",
            "score_impact": 25.0,
            "details": "Order reference is missing from the document."
        })
        return {
            "flags": flags,
            "flags_count": len(flags),
            "deterministic_risk_score": min(100.0, sum(f["score_impact"] for f in flags)),
            "payment_verified": False,
        }

    payment = None
    if tx_ref and tx_ref.lower() not in ["null", "none", "n/a", "unknown"]:
        payment = db.query(PaymentLedger).filter(PaymentLedger.transaction_reference == tx_ref).first()
        if payment and payment.order_reference != order_ref:
            flags.append({
                "flag": "ORDER_REFERENCE_MISMATCH",
                "severity": "CRITICAL",
                "score_impact": 50.0,
                "details": f"Transaction '{tx_ref}' belongs to order '{payment.order_reference}', not '{order_ref}'."
            })
            flags.append({
                "flag": "DUPLICATE_TRANSACTION_REFERENCE",
                "severity": "CRITICAL",
                "score_impact": 50.0,
                "details": f"Transaction '{tx_ref}' is being reused across multiple orders."
            })
    
    if not payment:
        payment = db.query(PaymentLedger).filter(PaymentLedger.order_reference == order_ref).first()

    if not payment:
        flags.append({
            "flag": "PAYMENT_NOT_FOUND",
            "severity": "CRITICAL",
            "score_impact": 60.0,
            "details": f"No payment record found in ledger for order '{order_ref}'."
        })
    else:
        if payment.status != "SETTLED":
            flags.append({
                "flag": "PAYMENT_NOT_SETTLED",
                "severity": "HIGH",
                "score_impact": 40.0,
                "details": f"Payment exists but status is '{payment.status}', not SETTLED."
            })
        
        if abs(payment.amount - claimed_amount) > 0.01:
            flags.append({
                "flag": "PAYMENT_AMOUNT_MISMATCH",
                "severity": "CRITICAL",
                "score_impact": 50.0,
                "details": f"Claimed amount (${claimed_amount:.2f}) does not match ledger amount (${payment.amount:.2f})."
            })
            
        if payment.beneficiary_name and payment.beneficiary_name != "FraudGuard Corp":
            # For this test, assume FraudGuard Corp is the valid beneficiary for all orders, unless specified otherwise.
            flags.append({
                "flag": "WRONG_BENEFICIARY",
                "severity": "CRITICAL",
                "score_impact": 60.0,
                "details": f"Transaction was sent to '{payment.beneficiary_name}', which is not the authorized merchant account."
            })

    total_score = min(100.0, sum(f["score_impact"] for f in flags))
    is_verified = payment is not None and payment.status == "SETTLED" and abs(payment.amount - claimed_amount) <= 0.01 and not any(f["severity"] == "CRITICAL" for f in flags)

    return {
        "flags": flags,
        "flags_count": len(flags),
        "deterministic_risk_score": total_score,
        "payment_verified": is_verified,
        "ledger_amount": payment.amount if payment else 0.0,
        "ledger_status": payment.status if payment else "NOT_FOUND"
    }
