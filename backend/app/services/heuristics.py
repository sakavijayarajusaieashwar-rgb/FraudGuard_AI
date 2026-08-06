import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import Vendor, Invoice


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
                "severity": "CRITICAL",
                "score_impact": 40.0,
                "details": f"Vendor name '{vendor_name}' is suspiciously similar ({best_similarity*100:.0f}% match) to verified vendor '{similar_vendor_name}'."
            })
        else:
            flags.append({
                "flag": "UNKNOWN_VENDOR",
                "severity": "MEDIUM",
                "score_impact": 20.0,
                "details": f"Vendor '{vendor_name}' is not in master verified vendor database."
            })
    else:
        if not matched_vendor.is_known:
            flags.append({
                "flag": "UNTRUSTED_VENDOR",
                "severity": "HIGH",
                "score_impact": 30.0,
                "details": f"Vendor '{matched_vendor.name}' is flagged as untrusted/unverified in system database."
            })

    # 4. Amount Ratio Anomaly Check
    if matched_vendor and matched_vendor.avg_invoice_amount > 0:
        avg_amt = matched_vendor.avg_invoice_amount
        ratio = amount / avg_amt
        if ratio >= 3.0:
            flags.append({
                "flag": "UNUSUAL_INVOICE_AMOUNT_RATIO",
                "severity": "HIGH",
                "score_impact": 35.0,
                "ratio": round(ratio, 2),
                "details": f"Invoice amount (${amount:,.2f}) is {ratio:.1f}x higher than vendor average (${avg_amt:,.2f})."
            })

    # 5. Round Number Anomaly Check
    if amount >= 1000.0 and amount.is_integer() and amount % 500 == 0:
        flags.append({
            "flag": "ROUND_NUMBER_ANOMALY",
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
                    "severity": "MEDIUM",
                    "score_impact": 15.0,
                    "details": f"Invoice date '{inv_date_str}' is set in the future relative to system date."
                })
            if parsed_date.weekday() in [5, 6]:  # Saturday or Sunday
                flags.append({
                    "flag": "WEEKEND_INVOICE_DATE",
                    "severity": "LOW",
                    "score_impact": 5.0,
                    "details": f"Invoice date '{inv_date_str}' falls on a weekend."
                })
        except Exception:
            pass

    total_score = min(100.0, sum(f["score_impact"] for f in flags))

    return {
        "flags": flags,
        "flags_count": len(flags),
        "deterministic_risk_score": total_score,
        "vendor_matched": matched_vendor.name if matched_vendor else None,
        "missing_fields": missing_fields,
    }
