# Phased Development Roadmap & Implementation Plan
## AI-Powered Personalized Learning & Career Development Platform

**Document Version:** 1.0.0  
**Methodology:** Iterative Agile / Test-Driven Development (TDD)  
**Total Estimated Timeline:** 12 Phases / 24 Sprints (48 Weeks)  

---

## 1. High-Level Phased Roadmap Overview

```mermaid
gantt
    title Platform Engineering Roadmap
    dateFormat  YYYY-MM-DD
    section Foundation & Arch
    Phase 1: Architecture & Requirements (Current) :done, p1, 2026-11-01, 2026-11-15
    Phase 2: Environment & Docker Scaffolding       :active, p2, 2026-11-16, 2026-11-30
    section Core Backend & Data
    Phase 3: Database Models, pgvector & Seed Data :p3, 2026-12-01, 2026-12-15
    Phase 4: Authentication, RBAC & Profiles       :p4, 2026-12-16, 2026-12-31
    section AI & Multi-Agent Swarm
    Phase 5: Profiler & Skill Extraction Agent    :p5, 2027-01-01, 2027-01-20
    Phase 6: Career Benchmarking & Gap Analyzer    :p6, 2027-01-21, 2027-02-10
    Phase 7: LangGraph Roadmap Architect Agent     :p7, 2027-02-11, 2027-03-05
    Phase 8: pgvector Resource Curation Engine    :p8, 2027-03-06, 2027-03-25
    section Evaluation & Adaptation
    Phase 9: Assessment & Adaptive Replanning Agent:p9, 2027-03-26, 2027-04-15
    Phase 10: Career Coach & Mock Interview Engine :p10, 2027-04-16, 2027-05-05
    section Portals & Polishing
    Phase 11: Mentor & Org Admin Portals           :p11, 2027-05-06, 2027-05-25
    Phase 12: End-to-End Testing & Hardening       :p12, 2027-05-26, 2027-06-15
```

---

## 2. Granular Phase Breakdown

### Phase 1: Project Foundation, Requirements & Architecture (CURRENT)
- **Status:** Complete / Final Review
- **Key Deliverables:**
  - Software Requirement Specification (SRS) with complete user stories.
  - Multi-tier system architecture and module dependencies.
  - Multi-agent AI orchestration design (LangGraph + Ollama).
  - PostgreSQL 16 + pgvector schema design with HNSW indexes.
  - Security, privacy, and prompt injection defense specifications.
  - Technology stack justification (FOSS, zero paid APIs).

### Phase 2: Environment Setup, Scaffolding & Containerization
- **Objectives:**
  - Configure root project structure, Python 3.11 virtual environment, and Node 20 workspace.
  - Create multi-container `docker-compose.yml` for PostgreSQL (`pgvector`), Redis, and Ollama.
  - Set up FastAPI app skeleton with CORS, settings management, and structured logging.
  - Set up Vite + React + TypeScript + Tailwind CSS skeleton with routing and layout shell.
  - Configure pre-commit hooks: Ruff, Black, ESLint, Prettier.

### Phase 3: Database Models, Alembic Migrations & Seed Taxonomies
- **Objectives:**
  - Implement SQLAlchemy 2.0 async models for all tables (Users, Skills, Roadmaps, Milestones, Resources, Assessments).
  - Generate baseline Alembic migrations and verify forward/backward migration integrity.
  - Seed canonical Skill Taxonomy (500+ standard tech skills with prerequisite graphs).
  - Pre-compute and load 768-dimensional `bge-base-en-v1.5` embeddings for canonical skills.
  - Seed initial Career Role Benchmarks (e.g., *Frontend Engineer*, *MLOps Specialist*, *Backend Engineer*).

### Phase 4: Authentication, RBAC & Profile Management
- **Objectives:**
  - Implement JWT authentication with Argon2id password hashing and refresh token rotation.
  - Build RBAC middleware enforcing Student, Mentor, Org Admin, and Sys Admin permissions.
  - Create learner profile onboarding endpoints with file upload for resumes.
  - Implement React authentication views (Login, Signup, Role redirection, Protected Routes).

### Phase 5: Profiler & Skill Ingestion Engine
- **Objectives:**
  - Build PDF/DOCX resume text extraction service.
  - Implement **Profiler Agent** using LangChain and Ollama with structured Pydantic schemas.
  - Integrate pgvector semantic matching to link extracted resume keywords to canonical skills.
  - Create interactive Profile & Skill Review UI in React for learners to confirm extracted skills.

### Phase 6: Career Benchmarking & Gap Analysis Engine
- **Objectives:**
  - Implement **Gap Analyzer Agent** calculating deficit scores and prerequisite DAG traversal.
  - Implement topological sort algorithm ensuring foundational prerequisites precede advanced skills.
  - Build Frontend Skill Gap Visualizer with Recharts Radar and Bar charts.

### Phase 7: Multi-Agent Dynamic Roadmap Generation
- **Objectives:**
  - Implement **Roadmap Architect Agent** via LangGraph state graphs.
  - Generate hierarchical milestones structured by phase, deliverable, and estimated study hours.
  - Persist roadmaps and milestones into PostgreSQL with versioning.
  - Build interactive Roadmap visualizer in React with Framer Motion animations.

### Phase 8: Resource Recommendation & Vector Search Engine
- **Objectives:**
  - Seed and index 1,000+ curated open educational resources (OER) in `pgvector`.
  - Implement **Resource Curator Agent** executing hybrid semantic + metadata filtering.
  - Enable link health checking and community rating calculations.
  - Integrate resource drawers into Frontend milestone views.

### Phase 9: Dynamic Assessment & Adaptive Replanning
- **Objectives:**
  - Implement **Assessment & Evaluator Agent** dynamically generating milestone quizzes and scoring deliverables.
  - Implement **Adaptive Replanner Agent** triggering automated remedial milestones on score $< 70\%$.
  - Implement Gamification subsystem (XP points, streak tracker, milestone achievement badges).

### Phase 10: Career Simulation & Mock Interview Subsystem
- **Objectives:**
  - Implement **Career Coach Agent** hosting interactive technical and behavioral mock interview sessions.
  - Integrate real-time streaming chat interface with feedback scoring.

### Phase 11: Mentor & Organization Admin Dashboards
- **Objectives:**
  - Build Mentor Cohort Dashboard: student progress trackers, manual review queue, and roadmap intervention.
  - Build Organization Admin Dashboard: aggregate skill analytics, cohort management, team benchmark assignments.

### Phase 12: End-to-End Testing, Hardening & Production Release
- **Objectives:**
  - Comprehensive Pytest test suite ($> 85\%$ backend test coverage).
  - Vitest component testing and Playwright E2E integration test flows.
  - Load testing with Locust ($> 200\text{ req/s}$ on core API endpoints).
  - Production deployment documentation and automated Docker container orchestration scripts.

---

## 3. Risk Assessment & Mitigation Matrix

| Risk Identified | Impact | Probability | Architectural Mitigation |
| :--- | :---: | :---: | :--- |
| **Local LLM Latency / Hardware Constraints** | High | Medium | Implement quantized 4-bit models (`Q4_K_M`), asynchronous streaming responses via SSE, and deterministic heuristic fallback algorithms if Ollama is overloaded. |
| **AI Hallucinations in Curricula** | High | Medium | Constrain AI agents to curated database entities via Pydantic structured output models and pgvector grounding. |
| **Data Schema Drift / Migration Failures** | Medium | Low | Version control all schema changes strictly through Alembic with automated migration rollback test suites. |
| **Prompt Injection via Uploaded Resumes** | High | Low | Sanitize input text, redact PII, isolate untrusted user data within XML tags, and validate all agent outputs strictly with Pydantic. |
