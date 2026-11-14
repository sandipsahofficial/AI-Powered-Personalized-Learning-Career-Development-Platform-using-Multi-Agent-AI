# AI-Powered Personalized Learning & Career Development Platform

A scalable, intelligent, multi-agent enterprise learning ecosystem built with **FastAPI**, **React (TypeScript + Vite)**, **PostgreSQL (pgvector)**, **Redis**, and **LangGraph with Ollama**.

---

## 1. Quick Start Guide

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v25+)
- [Node.js](https://nodejs.org/) (v20+ or v24+)
- [Python](https://www.python.org/) (v3.11+)
- [Ollama](https://ollama.ai/) (for local LLM inference)

### Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
On Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

---

## 2. Infrastructure Services (Docker Compose)

Launch the underlying PostgreSQL (with pgvector), Redis, and Ollama services:

```bash
docker-compose up -d postgres redis ollama
```
Or via Makefile:
```bash
make infra-up
```
Or via PowerShell script:
```powershell
.\infrastructure\scripts\dev.ps1 infra-up
```

### Services & Ports
| Service | Technology | Port | Credentials (Dev) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL** | `pgvector/pgvector:pg16` | `5432` | user: `postgres`<br>pass: `postgres_dev_password`<br>db: `learning_platform_db` | Relational & dense vector store with HNSW indexing |
| **Redis** | `redis:7-alpine` | `6379` | pass: `redis_dev_password` | Session token denylist, caching & task bus |
| **Ollama** | `ollama/ollama:latest` | `11434` | None | Local open-source LLM inference engine |
| **Backend** | FastAPI / Python 3.11 | `8000` | N/A | REST API & Multi-Agent orchestration |
| **Frontend** | React 18 + Vite | `5173` / `3000` | N/A | User interface & infrastructure dashboard |

---

## 3. Running Applications Locally

### Backend (FastAPI)
```bash
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Linux/macOS: source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Interactive API Documentation will be live at:
- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

### Frontend (React + Vite + Tailwind CSS)
```bash
cd frontend
npm install
npm run dev
```
Frontend interface will be live at `http://localhost:5173`.

---

## 4. Verification & Testing

### Health Endpoints
- Overall Health: `http://localhost:8000/api/v1/health`
- Database + pgvector: `http://localhost:8000/api/v1/health/database`
- Redis: `http://localhost:8000/api/v1/health/redis`
- Ollama LLM: `http://localhost:8000/api/v1/health/llm`
- Sanitized System Telemetry: `http://localhost:8000/api/v1/system/info`

### Automated Tests
```bash
# Backend Pytest
cd backend
pytest

# Frontend Vitest
cd frontend
npm run test
```
