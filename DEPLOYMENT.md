# FraudGuard AI — Single-Service Render Deployment Guide

This document describes how to deploy FraudGuard AI as a single Render Web Service.

---

## 1. Architecture Overview
- **Deployment Platform**: Render (Web Service)
- **Frontend & Backend**: Bundled together. React is compiled to static assets (`frontend/dist`) and served directly by FastAPI.
- **Database**: SQLite database file (`fraudguard.db`) stored on a persistent Render volume.

---

## 2. Render Web Service Configuration

### A. Environment Variables
Configure the following in the Render environment settings:
- `GEMINI_API_KEY`: *Your Google Gemini API Key*
- `LLM_PROVIDER`: `gemini` (or `heuristic` for fallback test)
- `JWT_SECRET_KEY`: *A strong random secret key (e.g. generated via `openssl rand -hex 32`)*
- `ALLOWED_ORIGINS`: `https://your-service.onrender.com`
- `DATABASE_URL`: `sqlite:////var/data/fraudguard.db`
- `ENABLE_DEMO_RESET`: `true`

### B. Persistent Disk Volume
Mount a persistent disk on Render:
- **Mount Path**: `/var/data`
- **Size**: `1 GiB` (more than enough for SQLite logs and records)

### C. Build & Start Commands
- **Build Command**:
  ```bash
  pip install -r backend/requirements.txt && cd frontend && npm install && npm run build
  ```
- **Start Command**:
  ```bash
  cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

### D. Health Check
- **Path**: `/health` (returns 200 immediately without hitting database or LLMs)
