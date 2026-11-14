# Technology Stack Selection and Dependency Specification
## AI-Powered Personalized Learning & Career Development Platform

**Document Version:** 1.0.0  
**License Paradigm:** 100% Free and Open-Source Software (FOSS)  
**Zero Mandatory Paid APIs**  

---

## 1. Technology Selection Matrix & Rationale

| Tier | Chosen Technology | Justification & Architectural Value | Alternative Evaluated | Rejection Reason |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend Framework** | **React 18+ (TypeScript)** | Industry standard, mature ecosystem, large component library support, strict type safety with backend schemas. | Vue 3 / Svelte | Smaller ecosystem for specialized AI chat & graph visualization components. |
| **Frontend Build Tool** | **Vite** | Instant server start, Lightning-fast Hot Module Replacement (HMR), optimized Rollup production builds. | Webpack / Create-React-App | Slower build times, bloated bundle configurations, CRA is deprecated. |
| **Styling & Animation** | **Tailwind CSS + Framer Motion** | Utility-first responsive design, zero runtime CSS overhead, smooth fluid milestone transitions and interactive roadmap DAG animations. | Material UI / Chakra UI | Heavy bundle size, harder to deeply customize for modern game-like roadmap interfaces. |
| **Data Visualization** | **Recharts** | Declarative React-native SVG charting; lightweight, high-performance rendering of skill radars, bar charts, and mastery curves. | Chart.js / D3.js | D3 requires imperative DOM manipulation; Chart.js canvas is harder to make accessible. |
| **Backend Framework** | **FastAPI (Python 3.11+)** | High throughput native async/await, automatic OpenAPI/Swagger docs, seamless Pydantic v2 integration, and native Python AI ecosystem compatibility. | Django / Flask / Express | Django is synchronous-first and bulky; Flask lacks native async and Pydantic validation; Node/Express lacks native Python AI/ML ecosystem. |
| **AI Orchestration** | **LangGraph + LangChain** | State-machine graph orchestration, cycles and human-in-the-loop branching support, persistent state checkpointing. | AutoGen / CrewAI | CrewAI/AutoGen lack deterministic graph control and have higher risk of runaway token consumption. |
| **Local LLM Engine** | **Ollama** | Seamless local deployment of open-weights models (`llama3.1:8b`, `qwen2.5:7b`), OpenAI-compatible REST API, zero cost, 100% data privacy. | OpenAI / Anthropic APIs | Paid per-token pricing, vendor lock-in, sensitive learner data transmitted off-premise. |
| **Embedding Engine** | **Sentence Transformers (`bge-base-en-v1.5`)** | State-of-the-art open-source text embeddings (768 dimensions), runs locally on CPU or consumer GPU. | OpenAI `text-embedding-3-small` | Requires paid API key and internet dependency. |
| **Database & Vector** | **PostgreSQL 16 + pgvector** | Unified relational and vector database, ACID guarantees, HNSW indexing for sub-35ms vector search, single operational footprint. | Pinecone / Weaviate / Chroma | Eliminates multi-database synchronization overhead; Pinecone is closed-source/paid. |
| **Caching / Broker** | **Redis** | In-memory key-value store for session caching, token blacklisting, and task queue broker. | Memcached | Lacks pub/sub, persistence, and rich data structures. |
| **Backend Testing** | **Pytest + pytest-asyncio** | Standard Python testing framework with rich plugin ecosystem and native async test execution. | Unittest | Verbose boilerplate, weaker async fixture capabilities. |
| **Frontend Testing** | **Vitest + Playwright** | Fast unit testing with Vite configuration sharing (Vitest), plus full end-to-end browser testing (Playwright). | Jest + Cypress | Jest is slower with ESM/Vite; Cypress has heavier runtime overhead than Playwright. |

---

## 2. Dependency Manifest Specifications

### 2.1 Backend Dependencies (`pyproject.toml` specification)

```toml
[project]
name = "ai-learning-platform-backend"
version = "0.1.0"
description = "FastAPI backend for AI-Powered Learning & Career Development Platform"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    # Core Framework & Async Server
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.8.0",
    "pydantic-settings>=2.4.0",

    # Database & Vector Operations
    "sqlalchemy>=2.0.32",
    "asyncpg>=0.29.0",
    "alembic>=1.13.2",
    "pgvector>=0.3.2",
    "redis>=5.0.8",

    # Authentication & Security
    "passlib[argon2]>=1.7.4",
    "python-jose[cryptography]>=3.3.0",
    "python-multipart>=0.0.9",

    # AI & Multi-Agent Orchestration
    "langgraph>=0.2.20",
    "langchain>=0.3.0",
    "langchain-community>=0.3.0",
    "langchain-ollama>=0.2.0",
    "sentence-transformers>=3.0.1",
    "scikit-learn>=1.5.1",
    "numpy>=1.26.4",

    # File & PDF Parsing
    "pypdf>=4.3.1",
    "python-docx>=1.1.2",

    # Utilities & HTTP Client
    "httpx>=0.27.0",
    "loguru>=0.7.2"
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.2",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "black>=24.8.0",
    "ruff>=0.6.2",
    "mypy>=1.11.2"
]
```

### 2.2 Frontend Dependencies (`package.json` specification)

```json
{
  "name": "ai-learning-platform-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.1",
    "@tanstack/react-query": "^5.52.0",
    "zustand": "^4.5.5",
    "axios": "^1.7.5",
    "lucide-react": "^0.435.0",
    "recharts": "^2.12.7",
    "framer-motion": "^11.3.30",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.2",
    "react-dropzone": "^14.2.3"
  },
  "devDependencies": {
    "@types/react": "^18.3.4",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.4",
    "vite": "^5.4.2",
    "tailwindcss": "^3.4.10",
    "postcss": "^8.4.41",
    "autoprefixer": "^10.4.20",
    "vitest": "^2.0.5",
    "@testing-library/react": "^16.0.0",
    "@playwright/test": "^1.46.1"
  }
}
```

---

## 3. Containerization & Deployment Topology

The entire system is deployed via container orchestration (`docker-compose.yml`), making it 100% reproducible on local developer machines or self-hosted cloud VMs without external dependencies:

```mermaid
flowchart LR
    ClientBrowser[Web Browser] -->|HTTP / HTTPS| Ingress[NGINX / Caddy]
    Ingress -->|Static Bundle| FrontendContainer[Frontend Web Service (React)]
    Ingress -->|/api/v1| BackendContainer[Backend API (FastAPI + Uvicorn)]
    BackendContainer --> PostgresContainer[(PostgreSQL 16 + pgvector)]
    BackendContainer --> RedisContainer[(Redis 7)]
    BackendContainer --> OllamaContainer[Ollama AI Engine (Llama 3.1 / Qwen 2.5)]
```
