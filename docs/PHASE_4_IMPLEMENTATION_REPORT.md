# Phase 4 Implementation Report: AI Profiling & Skill Extraction Engine

**Project:** AI-Powered Personalized Learning & Career Development Platform using Multi-Agent AI  
**Phase:** 4 of 12 (AI Profiling & Skill Extraction Engine)  
**Status:** COMPLETE (Ready for Review & Phase 5 Transition)  
**Report Timestamp:** 2026-11-14T13:28:00+05:30  
**Architect:** Senior Software Architect, AI Systems Engineer & Full-Stack Development Lead  

---

## 1. Executive Summary

Phase 4 implemented the **AI Profiling and Skill Extraction Engine**, delivering an evidence-backed skill extraction and normalization pipeline for learners. The engine ingests resumes across multiple formats (PDF, DOCX, TXT) or raw profile text, cleans and segments document sections, leverages local Ollama LLMs with strict JSON schemas, maps extracted terms against canonical skill taxonomies, calculates evidence-based proficiency ratings on a 5-tier scale, and enables learner review before committing changes to the PostgreSQL database.

All Phase 1, Phase 2, and Phase 3 foundations were preserved intact. Zero external paid APIs were introduced; all processing operates locally with local models and containerized infrastructure.

---

## 2. Architecture & Components Implemented

```
[Uploaded Resume: PDF / DOCX / TXT]
                │
                ▼
  ┌───────────────────────────────┐
  │   DocumentParser Service      │
  │   - Mime & Size Validation    │
  │   - Prompt Injection Shield   │
  │   - Text Section Segmentation │
  └───────────────┬───────────────┘
                  │
                  ▼
  ┌───────────────────────────────┐
  │    ProfilerAgent (AI)         │
  │   - Local Ollama Client       │
  │   - Structured JSON Extraction│
  │   - Deterministic Fallback    │
  └───────────────┬───────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌──────────────────┐ ┌──────────────────────────┐
│  SkillNormalizer │ │  ProficiencyEstimator    │
│  - Alias Table   │ │  - Evidence-Based Rules  │
│  - DB Taxonomy   │ │  - Tiers 1-5 / INSUFFICIENT│
│  - Fuzzy Matching│ │  - Transparent Reasoning │
└────────┬─────────┘ └──────────┬───────────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
  ┌───────────────────────────────┐
  │    ProfilingService (Cache)   │
  │   - Redis Session Store       │
  │   - Learner Review & Edit     │
  └───────────────┬───────────────┘
                  │
                  ▼
  ┌───────────────────────────────┐
  │  Learner Confirmation (DB)   │
  │  - user_skills table          │
  │  - user_profiles table        │
  └───────────────────────────────┘
```

---

## 3. New Files & Modules Created

### Backend Modules (`backend/app/`)
1. **`schemas/profiling.py`:** Pydantic v2 schemas defining `DocumentUploadResponse`, `SkillEvidence`, `ExtractedSkillItem`, `ProfilePreviewResponse`, `SkillNormalizeRequest`, `SkillNormalizeResponse`, and `ProfileConfirmRequest/Response`.
2. **`services/document_parser.py`:** Pure-Python document intelligence service. Parses PDF (`pypdf`), DOCX (`zipfile` + `xml.etree.ElementTree`), and TXT with section segmentation and prompt injection defenses.
3. **`services/skill_seeder.py`:** Idempotent database seeder for canonical skill categories (Programming Languages, Web Development, Databases, AI/ML, DevOps & Tools, Cloud Platforms, Soft Skills) and canonical skills.
4. **`services/skill_normalizer.py`:** Skill normalization service with a dictionary of common tech abbreviations and aliases (`js` -> `JavaScript`, `postgres` -> `PostgreSQL`, `reactjs` -> `React`, `ml` -> `Machine Learning`), canonical DB lookup, and fuzzy matching fallback.
5. **`services/proficiency_estimator.py`:** Multi-factor proficiency evaluation engine assigning ratings (Level 1 Beginner through Level 5 Expert) or `INSUFFICIENT_EVIDENCE` based on project complexity, years of experience, certifications, and multi-section corroboration.
6. **`core/llm_client.py`:** Asynchronous client for local Ollama instance (`http://127.0.0.1:11434`), prioritizing `qwen2.5-coder:7b`, `llama3:latest`, and `llama3.2:3b` with structured JSON output, bounded retries, and deterministic fallback.
7. **`agents/profiler_agent.py`:** Core Profiler Agent executing prompt-injected LLM extraction, deterministic fallback heuristics, normalization, and proficiency scoring.
8. **`services/profiling_service.py`:** High-level profiling orchestrator managing Redis document and preview caching, review mutations, and final persistence into `user_skills` and `user_profiles`.
9. **`api/v1/endpoints/profiling.py`:** 8 RESTful endpoints for resume upload, skill extraction, normalization, preview, skill review updates, profile confirmation, and status.
10. **`tests/test_profiling.py`:** 8 focused unit and integration tests covering document parsing, security sanitization, normalization, proficiency estimation, full API flow, and cross-user data isolation.

### Frontend Components (`frontend/src/`)
1. **`types/profiling.ts`:** TypeScript interfaces for extraction preview, evidence models, upload responses, and confirmation results.
2. **`services/profilingService.ts`:** Client API service with methods for upload, extract, preview, update, confirm, and status.
3. **`features/profiling/LearnerProfilingView.tsx`:** Polished dark-mode learner profiling interface with drag-and-drop file upload, text paste tab, candidate headline summary, category breakdown badges, interactive skill cards with evidence tags, Level 1–5 selector, manual skill modal, and confirmation actions.
4. **`tests/LearnerProfilingView.test.tsx`:** Vitest tests verifying tab switching, file inputs, and extraction review actions.

---

## 4. Reused Existing Components

| Existing Component | Integration & Reuse in Phase 4 |
| :--- | :--- |
| **SQLAlchemy `UserSkill` & `Skill` Models** | Reused directly. Approved skills persist into `user_skills` linked to canonical `skills` without schema modifications or duplicate tables. |
| **SQLAlchemy `UserProfile` Model** | Updates `headline` and `raw_resume_text` upon learner confirmation. |
| **FastAPI `get_current_user` Dependency** | Enforces JWT authentication and Redis token blacklist checking on all profiling endpoints. |
| **Redis Infrastructure (Port 6379)** | Caches uploaded resume metadata and intermediate profiling previews (24-hour TTL) prior to user confirmation. |
| **Local Ollama (Port 11434)** | Leveraged pre-installed `llama3.2:3b`, `qwen2.5-coder:7b`, and `llama3:latest` for zero-cost, local structured JSON skill extraction. |
| **PostgreSQL 16 & pgvector (Port 5433)** | Stores confirmed user skills, categories, and vector-ready taxonomy. |

---

## 5. Security & Privacy Controls

1. **Document Upload Safeguards:**
   - Enforces a 5MB maximum file size limit.
   - Restricts file types to `.pdf`, `.docx`, and `.txt`.
   - Empty files (0 bytes) and corrupted archives are rejected with descriptive HTTP 400/422 responses.
2. **Prompt Injection Neutralization:**
   - Regular expressions scan for phrases such as `ignore previous instructions`, `system prompt:`, and `rate all skills as 5`, substituting them with `[SANITIZED_INPUT]`.
   - Document text is isolated inside `<resume_content>` XML tags in the system prompt to prevent jailbreaking.
3. **Privacy & Ephemeral Storage:**
   - Files are parsed directly in memory (`io.BytesIO`) without executing uploaded binaries or leaving unmanaged temporary files on disk.
   - Intermediate extraction previews reside in Redis with TTL expiration.
4. **Cross-User Data Isolation:**
   - Every profiling endpoint scopes queries to `current_user.id`.
   - Verified via `test_profiling_cross_user_isolation` that User B cannot view User A's cached documents or preview.
5. **Human-in-the-Loop Confirmation:**
   - AI extractions are strictly provisional previews until the learner explicitly clicks "Confirm & Save to Profile".

---

## 6. Verification Evidence & Test Execution

### 6.1 Backend Focused Test Suite (`backend/tests/test_profiling.py`)
Command executed: `pytest tests/test_profiling.py -v`

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.2.0, pluggy-1.7.0
rootdir: backend
configfile: pyproject.toml
plugins: anyio-4.16.0, asyncio-1.5.0
asyncio: mode=Mode.AUTO

tests/test_profiling.py::test_document_parser_txt_and_sections PASSED    [ 12%]
tests/test_profiling.py::test_document_parser_docx PASSED                [ 25%]
tests/test_profiling.py::test_document_parser_prompt_injection_sanitization PASSED [ 37%]
tests/test_profiling.py::test_document_parser_invalid_and_empty PASSED   [ 50%]
tests/test_profiling.py::test_skill_normalizer PASSED                    [ 62%]
tests/test_profiling.py::test_proficiency_estimator PASSED               [ 75%]
tests/test_profiling.py::test_profiling_api_flow PASSED                  [ 87%]
tests/test_profiling.py::test_profiling_cross_user_isolation PASSED      [100%]

======================= 8 passed, 3 warnings in 42.14s ========================
```

### 6.2 Frontend Focused Test Suite
Command executed: `npm run test`

```text
 RUN  v2.1.9 frontend

 ✓ src/tests/LearnerProfilingView.test.tsx (2 tests) 50ms
 ✓ src/tests/LoginPage.test.tsx (2 tests) 92ms
 ✓ src/tests/InfrastructureStatus.test.tsx (1 test) 81ms

 Test Files  3 passed (3)
      Tests  5 passed (5)
   Duration  5.64s
```

### 6.3 Frontend Production Build
Command executed: `npm run build`

```text
> ai-learning-platform-frontend@0.1.0 build
> node ./node_modules/typescript/bin/tsc && node ./node_modules/vite/bin/vite.js build

vite v5.4.21 building for production...
transforming...
✓ 1628 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.57 kB │ gzip:  0.37 kB
dist/assets/index-CYfoPPyH.css   22.09 kB │ gzip:  4.81 kB
dist/assets/index-CSVFhH-K.js   254.94 kB │ gzip: 78.86 kB
✓ built in 6.02s
```

---

## 7. Deliverables Checklist

- [x] Secure document ingestion pipeline supporting PDF, DOCX, and TXT files.
- [x] Text section segmentation (Skills, Projects, Experience, Education, Certifications).
- [x] Prompt injection sanitization and safe tag delimiting.
- [x] Local Ollama LLM integration with structured JSON output and bounded retries.
- [x] Deterministic heuristic fallback when LLM is unavailable or times out.
- [x] Skill Normalization Engine with alias dictionary and canonical database taxonomy matching.
- [x] Evidence-based Proficiency Estimator (1 to 5 scale and `INSUFFICIENT_EVIDENCE` handling).
- [x] Profiler Agent with cross-section evidence corroboration.
- [x] 8 RESTful backend profiling endpoints with authentication and cross-user isolation.
- [x] React learner profiling UI with drag-and-drop upload, evidence badges, and interactive review.
- [x] Persistence of learner-confirmed skills into `user_skills` table.
- [x] Focused tests executed: 8/8 backend passed, 5/5 frontend passed.
- [x] Production build passes with zero errors.

---

## 8. Transition to Phase 5

Phase 4 is **100% COMPLETE**. The profiling engine is operational and ready to serve as the input foundation for Phase 5:

> **Phase 5 Scope Preview:** Career Path Matching & Gap Analysis Engine (Career Role Ontology, Skill Requirement Matrices, Vector Cosine Similarity Matching, Automated Gap Identification, and Readiness Scoring).

*Phase 4 is finalized. Awaiting user review and authorization to proceed to Phase 5.*
