# 🌐 Cloud & Online Deployment Guide

**Project:** AI-Powered Personalized Learning & Career Development Platform using Multi-Agent AI  
**GitHub Repository:** [https://github.com/sandipsahofficial/AI-Powered-Personalized-Learning-Career-Development-Platform-using-Multi-Agent-AI](https://github.com/sandipsahofficial/AI-Powered-Personalized-Learning-Career-Development-Platform-using-Multi-Agent-AI)

---

## 📋 Architecture Overview for Cloud Deployment

The application consists of three decoupled components:
1. **Frontend:** React 18 + Vite + TypeScript (Single Page App)
2. **Backend API:** FastAPI + Asynchronous SQLAlchemy 2.0 (Python 3.11)
3. **Database & Cache:** PostgreSQL 16 (with `pgvector`) + Redis 7

All cloud dialect collisions (e.g. `postgres://` vs `postgresql+asyncpg://`), SSL mode strings, dynamic `$PORT` bindings, and wildcard CORS policies are handled automatically by the backend.

---

## 🚀 Deployment Options

### Option 1: 1-Click / Blueprint on Render (Recommended)

Render provides free hosting for web services, static sites, and PostgreSQL databases.

#### Step 1: Push Code & Connect to Render
1. Go to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** -> **Blueprint**.
3. Select your GitHub repository: `sandipsahofficial/AI-Powered-Personalized-Learning-Career-Development-Platform-using-Multi-Agent-AI`.
4. Render will read the included `render.yaml` and configure the Backend, Frontend, and PostgreSQL automatically.
5. Click **Apply**.

#### Step 2: Configure Frontend API URL
Once the backend service has deployed and generated a URL (e.g., `https://learning-platform-backend.onrender.com`):
1. In Render, open the **learning-platform-frontend** service.
2. Go to **Environment** tab.
3. Add or update:
   - `VITE_API_BASE_URL` = `https://<YOUR_BACKEND_URL>/api/v1`
4. Click **Save Changes** (Render will trigger a quick rebuild of the frontend).

---

### Option 2: Frontend on Vercel + Backend on Render/Railway

This is the standard modern production setup: Vercel delivers high-speed global edge CDN for React, while Render or Railway runs the Python FastAPI service.

#### Backend on Render (Web Service):
1. Click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Settings:
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install --upgrade pip && pip install .`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Environment Variables:
   - `PORT`: (Auto-injected by Render)
   - `ENVIRONMENT`: `production`
   - `CORS_ORIGINS`: `*` (or your Vercel frontend domain)
   - `DATABASE_URL_OVERRIDE`: `postgresql+asyncpg://...` (from Render Postgres, Neon.tech, or Supabase)
   - `SECRET_KEY`: `generate-a-strong-secret-key-here`
   - `POSTGRES_DB`: `learning_platform`

#### Database on Neon.tech or Supabase (Free PostgreSQL with pgvector):
1. Create a free project at [Neon.tech](https://neon.tech) or [Supabase](https://supabase.com).
2. Copy the Connection String (URI).
3. Paste it directly as `DATABASE_URL_OVERRIDE` in your backend environment variables.
   *(Note: The backend automatically transforms `postgres://` or `sslmode=require` into asyncpg-compatible formats and verifies `CREATE EXTENSION IF NOT EXISTS vector;` on startup).*

#### Frontend on Vercel:
1. Go to [Vercel Dashboard](https://vercel.com/) -> **Add New** -> **Project**.
2. Import `AI-Powered-Personalized-Learning-Career-Development-Platform-using-Multi-Agent-AI`.
3. Configure Project:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
4. Environment Variables:
   - `VITE_API_BASE_URL`: `https://<YOUR_BACKEND_URL>/api/v1`
5. Click **Deploy**. *(The included `frontend/vercel.json` ensures client-side routing works flawlessly on refresh).*

---

### Option 3: Docker Deployment on Railway or Self-Hosted VPS

If deploying using Docker containers (e.g. Railway, DigitalOcean, AWS EC2, or VPS):

1. **Backend Docker:**
   ```bash
   docker build -f infrastructure/docker/Dockerfile.backend -t learning-platform-backend .
   docker run -p 8000:8000 -e DATABASE_URL_OVERRIDE="<YOUR_DB_URL>" learning-platform-backend
   ```
2. **Frontend Docker:**
   ```bash
   docker build -f infrastructure/docker/Dockerfile.frontend -t learning-platform-frontend .
   docker run -p 80:80 learning-platform-frontend
   ```
3. Or deploy via `docker compose`:
   ```bash
   docker compose -f infrastructure/docker/docker-compose.yml up -d
   ```

---

## 🤖 LLM & AI Engine Cloud Behavior

- **Local Development:** Defaults to local Ollama on `http://localhost:11434` with models `llama3:latest` and `qwen2.5-coder:7b`.
- **Cloud Production:**
  - If a remote Ollama instance is available, set `OLLAMA_BASE_URL` to its endpoint.
  - If Ollama is unreachable in the cloud, the platform's **deterministic AI fallback engine** immediately handles skill extraction, career gap analysis, personalized roadmaps, and mentoring responses. The platform never crashes or returns empty responses.

---

## 🔑 Default Credentials & Health Checks

| Resource | Default / Endpoint |
|---|---|
| **Health Check API** | `GET /api/v1/health` |
| **OpenAPI / Swagger Docs** | `GET /docs` |
| **Default Test User** | `student@example.com` / `Password123!` |
| **Default Admin User** | `admin@example.com` / `AdminPassword123!` |
