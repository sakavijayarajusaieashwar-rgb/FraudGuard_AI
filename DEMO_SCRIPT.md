# FraudGuard AI — Hackathon Demo Script (3 Minutes)

This script walks judges through FraudGuard's features, highlighting its Hybrid Deterministic-AI safety model.

---

### **0:00 - 0:25 | The Problem**
- **Action**: Open the FraudGuard home dashboard.
- **Script**: *"Accounts payable fraud costs businesses billions. Sophisticated scammers manipulate invoice metadata, bank accounts, or quantities, which look completely legitimate if analyzed in isolation. Most software uses a single risk score. FraudGuard uses a team of specialized AI agents working alongside deterministic financial checks to verify evidence before the money moves."*

---

### **0:25 - 1:15 | Scenario 1: Procurement Overbilling**
- **Action**: Select the **Procurement Overbilling Attack** preset in the simulator, click **Run FraudGuard**, and view the streaming agent trace.
- **Script**: *"Let's look at a procurement overbilling attack. The invoice vendor and bank account look normal, but the invoice quantity is 100 units while the warehouse Goods Receipt shows only 80 units were actually received. FraudGuard's Three-Way Match Engine immediately flags a mismatch, displaying the exact unsupported quantity (20 units) and overbilled amount ($20,000.00). The Decision and Critic agents reject the transaction, protecting our budget."*

---

### **1:15 - 2:05 | Scenario 2: Payment Instruction Tampering**
- **Action**: Select the **Payment Instruction Tampering** preset, click **Run FraudGuard**, and open the **Document Forensics** view.
- **Script**: *"Next, a payment instruction tampering scenario. Scammers compromise a real vendor's invoice email and swap the bank details. FraudGuard's Document Forensics cross-references the invoice with our historical vendor bank ledger. It flags that the account ending in 4418 does not match the verified historical account ending in 9271. It also highlights that this bank account was previously linked to a rejected invoice on our Fraud Graph. The Critic agent enforces a hard governance block."*

---

### **2:05 - 2:40 | The AI Investigator**
- **Action**: Type into the investigator search box: *"How many units were received?"* Show that it answers **80 units** from database records with `DETERMINISTIC` source (0 Gemini calls).
- **Script**: *"If an auditor needs to double check, they don't have to look through raw logs. They can use the AI Investigator. Common questions are answered deterministically directly from database records without wasting AI tokens or hallucinating. If we ask 'Why was this blocked?', the AI uses the deterministic evidence to explain the audit trail in plain English."*

---

### **2:40 - 3:00 | Business Impact & Wrap Up**
- **Action**: Click the **Business Impact** tab.
- **Script**: *"Finally, our Business Impact view shows actual exposure, preventing double counting of multi-risk invoices. In summary, FraudGuard does not ask AI to guess whether a transaction is fraudulent. It verifies financial evidence deterministically, and uses AI to explain the findings."*
