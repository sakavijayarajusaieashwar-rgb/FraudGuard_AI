# FraudGuard AI

**Autonomous AI agents that catch invoice fraud before the money moves.**

FraudGuard AI sits at the accounts payable approval gate — the last checkpoint before an invoice gets paid — and replaces a single rushed human review with a coordinated team of specialized AI agents that reason, explain, and even disagree, just like a real finance audit team would.

---

## What It Does

When an invoice comes in, four autonomous agents run in sequence, live:

| Agent | Role |
|---|---|
| **Extraction Agent** | Reads raw invoice text/data and structures it — vendor, amount, invoice number, date, line items |
| **Risk Agent** | Cross-checks against vendor history to catch duplicates, vendor name impersonation (typosquatting), inflated amounts, and line-item math errors |
| **Decision Agent** | Recommends **Approve / Escalate / Reject** with plain-English reasoning and a confidence score |
| **Critic Agent** | Independently reviews the decision and can push back — surfacing genuine agent disagreement rather than a single opaque score |

Every decision is fully transparent — you can watch the agents reason live, see exactly why each flag was raised, and follow approved invoices through to a dedicated **Accounts Department queue** ready for payment.

## Why This Matters

AP (accounts payable) fraud — fake invoices, duplicate payments, vendor impersonation — is a well-documented, costly problem. It's stoppable at the approval step, before payment is ever transferred. Most tools either apply rigid rule-based checks or hide behind an opaque risk score. FraudGuard AI makes the reasoning visible and explainable, like a real financial auditor would.

## Key Features

- 🤖 **Live multi-agent reasoning trace** — watch each agent's analysis stream in real time, not a black-box score
- ⚠️ **Agent disagreement detection** — the Critic Agent can challenge the Decision Agent's call
- 🧠 **Adaptive memory** — learns from human overrides to sharpen future decisions on repeat vendors
- 📊 **Explainable flags** — every red flag comes with a specific, human-readable explanation
- 💰 **Accounts Department queue** — approved invoices are routed to a clear payment-ready view
- 📈 **Impact Stats dashboard** — quantifies invoices reviewed, fraud caught, and dollar amounts protected
- 🔒 **Per-user authentication** — isolated invoice history and data per logged-in user
- 🛡️ **Graceful degradation** — if live LLM calls are rate-limited, the system falls back to cached results seamlessly, with zero visible errors

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **AI**: Google Gemini API (multi-agent reasoning pipeline)
- **Frontend**: React (Vite)
- **Auth**: JWT-based authentication
- Built end-to-end using agentic coding tools: **Antigravity** and **GitHub Copilot**

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Gemini API key ([get one here](https://aistudio.google.com/apikey))

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your real API key + JWT secret
uvicorn app.main:app --reload --port 8002
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173` (frontend) with the backend running at `http://localhost:8002`.

### Demo Accounts
| Email | Password |
|---|---|
| demo@fraudguard.ai | demo1234 |
| demo2@fraudguard.ai | demo1234 |

## Environment Variables

See `backend/.env.example` for the full list. You'll need at minimum:
- `GEMINI_API_KEY` — your Gemini API key
- `LLM_PROVIDER` — `gemini`
- `JWT_SECRET_KEY` — any random secret string

## Live Demo Scenarios

The dashboard includes 4 pre-built demo scenarios for quick evaluation:
1. **Clean Invoice** — expected: Approve
2. **Duplicate Invoice #** — expected: Reject
3. **Inflated Amount & Urgent Wire** — expected: Escalate/Reject
4. **Line Item Math Mismatch** — expected: Reject

## Roadmap / What's Next

- Multi-modal input support (photographed/scanned invoices via image upload)
- Deeper cross-organization learning loop
- Integration with existing AP/ERP systems

## Built For

[Hackathon Name] — Agentic AI & Intelligent Systems track

---

*FraudGuard AI doesn't just flag rules — it reasons, explains, and learns.*
