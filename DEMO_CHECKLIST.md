# FraudGuard AI — Demo Readiness Checklist

This checklist confirms that FraudGuard is configured and verified for live demo delivery.

---

### **Pre-Demo Services Check**
- [ ] Backend running (`uvicorn app.main:app --reload --port 8002`)
- [ ] Frontend running (`npm run dev` in `/frontend`)
- [ ] Database seeded and migrated to SQLite schema
- [ ] Logged in as Demo User (`demo@fraudguard.ai` / `demo1234`)

---

### **Core Scenario Verifications**
- [ ] **Clean Scenario**: Verified as `APPROVE` with low risk score.
- [ ] **Procurement Overbilling Scenario**: Verified as `REJECT`, showing ordered: 100, received: 80, invoiced: 100, unsupported quantity: 20, unsupported amount: $20,000.00.
- [ ] **Payment Instruction Tampering Scenario**: Verified as `REJECT`, showing bank account mismatch (`****4418` vs `****9271`) and previous risk link.

---

### **AI Fallback & Offline Plan**
- If Gemini API quota is exhausted or slow, the system automatically degrades gracefully.
- The UI will display a banner: *"AI explanation temporarily unavailable. Verified FraudGuard evidence remains available."*
- Deterministic matching calculations, PO verification, document forensics, Fraud Graph visual links, and deterministic queries (like *"How many units were received?"*) continue to function with zero disruption.
