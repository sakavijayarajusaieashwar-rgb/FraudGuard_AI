# FraudGuard AI — Architectural Documentation

This document explains the architecture, components, data flows, and AI integration mechanisms of FraudGuard AI.

---

## 1. System Components Overview

FraudGuard AI is designed as a hybrid system that combines **deterministic financial ledger rules** with **asynchronous agentic cognitive reasoning**.

```
  Data Input (Invoice)
         │
         ▼
 ┌───────────────────────────────────┐
 │   Deterministic Evidence Engines  │
 │   - Purchase Order Verification   │
 │   - Goods Receipt Verification    │
 │   - Vendor historical checks      │
 │   - Graph Risk Network            │
 │   - Document Forensics            │
 └─────────────────┬─────────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │   Agentic AI Cascade   │
       │   - Risk Agent         │
       │   - Decision Agent     │
       │   - Critic Agent       │
       └───────────┬────────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  Final AP Decision  │
        │  (Approve / Reject) │
        └─────────────────────┘
```

---

## 2. Core Modules & Engines

### A. Deterministic Evidence Engines
- **Purchase Order (PO) Matching**: Searches the ledger for the PO reference on the invoice.
- **Goods Receipt (GR) Verification**: Compares ordered quantities against warehouse received records.
- **Three-Way Procurement Matching**: Computes discrepancies in quantity and price.
- **Document Forensics**: Checks document fingerprint duplicates, file mismatches, and bank details.
- **Fraud Relationship Graph**: Maps connections between current metadata and previously flagged fraud records.

### B. Agentic AI Cascade
1. **Extraction Agent**: Extracts invoice metadata.
2. **Risk Agent**: Evaluates structural risk based on database profiles.
3. **Decision Agent**: Synthesizes a preliminary approval or rejection verdict.
4. **Critic Agent**: Reviews the decision against governance overrides.

---

## 3. Database Schema

The database model is defined in `backend/app/models.py`:
- **User**: Scopes all invoice documents, historical bank accounts, and procurement orders to prevent cross-tenant data leaks.
- **Invoice**: Holds details, risk score, decision, critic notes, and tenant owner ID.
- **Vendor**: Maintains global verified identity and historical average billing amounts.
- **PurchaseOrder** & **GoodsReceipt**: Store authoritative procurement logs.
- **PaymentLedger**: Simulates outbound payments.
- **CriticOverride**: Stores custom auditor overrides.
