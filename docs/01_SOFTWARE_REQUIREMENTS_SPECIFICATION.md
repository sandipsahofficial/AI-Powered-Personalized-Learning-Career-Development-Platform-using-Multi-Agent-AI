# Software Requirement Specification (SRS)
## AI-Powered Personalized Learning & Career Development Platform

**Document Version:** 1.0.0  
**Status:** Approved for Baseline Design  
**Target Milestone:** Phase 1 Architecture & Foundation  

---

## 1. Executive Summary & Purpose

The **AI-Powered Personalized Learning & Career Development Platform** is an intelligent, multi-agent enterprise learning ecosystem. Traditional Learning Management Systems (LMS) and career portals provide static, one-size-fits-all curricula and siloed job listings. In contrast, this platform actively analyzes individual learner backgrounds, computes dynamic skill gaps against real-world industry career benchmarks, synthesizes adaptive step-by-step learning roadmaps, curates open-source learning resources, and continuously tracks learning velocity through an autonomous multi-agent swarm.

---

## 2. Stakeholders & User Roles (RBAC Matrix)

The system supports four distinct user roles, each equipped with dedicated role-based access control (RBAC), personalized dashboards, and domain-scoped capabilities:

| Role | Description | Key Capabilities |
| :--- | :--- | :--- |
| **Student / Learner** | Primary end-user acquiring skills and seeking career advancement. | - Profile & resume ingestion (skills, experience, ambitions).<br>- Interactive skill diagnostic tests and gap visualization.<br>- Personalized, dynamic learning roadmaps.<br>- Resource recommendations & progress logging.<br>- AI career simulation and mock interviews. |
| **Mentor / Career Coach** | Domain expert or educator supervising and guiding learners. | - Review learner progress, assessments, and flagged roadmaps.<br>- Offer 1-on-1 feedback and customize roadmaps.<br>- Endorse verified skills and review capstone projects.<br>- Host office hours and review AI agent suggestions. |
| **Organization Administrator** | Enterprise/Institution admin managing talent pipelines, cohorts, and learning tracks. | - Manage organization cohorts, licenses, and team skill benchmarks.<br>- View aggregated workforce analytics and organization skill gaps.<br>- Configure organizational career paths and competency frameworks.<br>- Assign customized training tracks across teams. |
| **System Administrator** | Technical administrator managing infrastructure, agents, models, and platform health. | - Platform health, system telemetry, and agent observability.<br>- Local LLM (Ollama) model selection, prompt registry, and fallback rules.<br>- Global taxonomy management (skills, roles, vector indexes).<br>- Audit logs, security compliance, and user identity management. |

---

## 3. High-Level User Stories & Use Cases

### 3.1 Student / Learner
- **US-01:** As a student, I want to upload my resume or connect my GitHub/LinkedIn profile so that the system automatically extracts and catalogs my baseline skills, education, and experience.
- **US-02:** As a student, I want to select a target career role (e.g., *MLOps Engineer*, *Full-Stack Developer*) and view a granular skill gap breakdown (Foundational, Intermediate, Advanced) comparing my current state to industry benchmarks.
- **US-03:** As a student, I want an adaptive, personalized learning roadmap generated into structured milestones, with estimated completion hours and difficulty curves.
- **US-04:** As a student, I want high-quality curated learning resources (articles, open tutorials, interactive repos, video lectures) ranked by relevance, recency, and community rating.
- **US-05:** As a student, I want to take adaptive quizzes and submit practice milestone deliverables, receiving instant feedback from the AI Evaluator Agent.
- **US-06:** As a student, if I struggle with a milestone or fail an assessment, I want the system to dynamically adjust my roadmap, inserting remedial prerequisites without manual intervention.

### 3.2 Mentor
- **US-07:** As a mentor, I want a cohort overview showing student engagement, completion velocity, and flagged students who are falling behind.
- **US-08:** As a mentor, I want to review AI-generated roadmaps and modify milestone objectives or recommended resources based on real-world industry insights.
- **US-09:** As a mentor, I want to conduct qualitative assessment reviews and leave actionable comments on learner project submissions.

### 3.3 Organization Administrator
- **US-10:** As an org admin, I want to define custom organizational role competencies (e.g., *Acme Corp Junior Backend Engineer*) mapping directly to our internal technology stack.
- **US-11:** As an org admin, I want cohort analytics showing aggregate skill growth over time, identifying talent shortages across engineering or product departments.
- **US-12:** As an org admin, I want to manage member invitations, role assignments, and department groupings via CSV or Single Sign-On (SSO).

### 3.4 System Administrator
- **US-13:** As a sys admin, I want to monitor Ollama inference latency, token usage, error rates, and agent state transitions in real time.
- **US-14:** As a sys admin, I want to trigger vector database re-indexing for skills, role benchmarks, and learning materials without downtime.
- **US-15:** As a sys admin, I want full audit logging for compliance, security events, and data export requests.

---

## 4. Functional Requirements (FR)

### Module 1: Authentication & User Management (FR-AUTH)
- **FR-AUTH-01:** Secure user registration and login supporting email/password (Argon2id hashing) and OAuth2 / OpenID Connect (e.g., GitHub, Google).
- **FR-AUTH-02:** Role-Based Access Control (RBAC) enforced across API endpoints via JWT tokens with embedded claims and refresh token rotation.
- **FR-AUTH-03:** Comprehensive profile management including target career goal, time commitment (hours/week), preferred learning modality (video, text, hands-on coding), and language preferences.

### Module 2: Skill Ingestion & Profiling Engine (FR-PROF)
- **FR-PROF-01:** Ingest semi-structured resumes (PDF, DOCX) and unstructured text to extract candidate skills, work history, tools, and education using local LLM NER and regex parsers.
- **FR-PROF-02:** Map extracted skills to a standardized Skill Taxonomy (e.g., ESCO/O*NET compatible taxonomy) normalized with dense semantic embeddings.
- **FR-PROF-03:** Maintain a confidence score (0.0 to 1.0) and proficiency level (Beginner, Intermediate, Advanced, Expert) for each learner skill, updated through assessments.

### Module 3: Career Benchmark & Gap Analysis Engine (FR-GAP)
- **FR-GAP-01:** Maintain normalized Career Role Benchmarks containing mandatory, recommended, and optional skill graphs with requisite proficiency thresholds.
- **FR-GAP-02:** Execute multidimensional gap analysis:
  $$\text{Gap}(\text{Learner}, \text{Role}) = \{(s, \Delta p) \mid s \in \text{RoleSkills}, \Delta p = \max(0, p_{\text{required}}(s) - p_{\text{learner}}(s))\}$$
- **FR-GAP-03:** Rank missing skills based on prerequisite dependencies (topological sort of skill DAG) and market demand weight.

### Module 4: Multi-Agent Dynamic Roadmap Generation (FR-ROADMAP)
- **FR-ROADMAP-01:** Multi-agent orchestration via LangGraph coordinating Profiler, Gap Analyzer, Roadmap Architect, Resource Curator, and Evaluator.
- **FR-ROADMAP-02:** Synthesize customized learning paths structured into sequential stages, modules, deliverables, and estimated time allocations.
- **FR-ROADMAP-03:** Dynamically re-plan: when a user’s assessment score is $< 70\%$, trigger the Roadmap Replanner Agent to inject prerequisite micro-modules and adjust downstream deadlines.

### Module 5: Resource Recommendation & Vector Retrieval (FR-RES)
- **FR-RES-01:** Index open educational resources (OER), GitHub repositories, documentation, and tutorials using `pgvector` dense vector embeddings (`all-MiniLM-L6-v2` / `bge-base-en-v1.5`).
- **FR-RES-02:** Hybrid search combining semantic similarity (cosine distance) with metadata filters (skill level, content format, rating, duration).
- **FR-RES-03:** Resource deduplication, link health verification, and freshness scoring.

### Module 6: Assessment, Progress Tracking & Gamification (FR-EVAL)
- **FR-EVAL-01:** Auto-generation of contextual multiple-choice and code-snippet questions dynamically tailored to the learner's current milestone.
- **FR-EVAL-02:** Real-time progress tracking calculation (milestone completion percentage, skill mastery velocity, streak count).
- **FR-EVAL-03:** Gamification subsystem: experience points (XP), skill badges, milestone certifications, and leaderboards.

---

## 5. Non-Functional Requirements (NFR)

### 5.1 Performance & Latency
- **NFR-PERF-01 (API Response Time):** Core transactional CRUD operations (non-AI) must complete with a $P_{95}$ latency of $< 120\text{ ms}$.
- **NFR-PERF-02 (AI Generation Latency):** Asynchronous streaming responses for agent roadmaps and explanations; initial token Time-to-First-Token (TTFT) $< 1.5\text{ s}$ when using optimized Ollama local quantized models (Q4_K_M).
- **NFR-PERF-03 (Vector Search):** Vector similarity search in `pgvector` with HNSW index must execute in $< 35\text{ ms}$ for a corpus of up to 500,000 indexed chunks.

### 5.2 Scalability & Concurrency
- **NFR-SCAL-01:** Stateless FastAPI application instances horizontally scalable behind an NGINX reverse proxy.
- **NFR-SCAL-02:** Asynchronous background job queue (Celery/Redis or FastAPI background tasks) for heavy LLM roadmap generation and resume parsing tasks to prevent thread starvation.
- **NFR-SCAL-03:** Database connection pooling configured via SQLAlchemy `QueuePool` capable of supporting 500 concurrent connections.

### 5.3 Reliability & Availability
- **NFR-REL-01:** Target system availability: $99.9\%$ uptime during business hours.
- **NFR-REL-02 (Agent Fallback):** Robust retry policies with exponential backoff on Ollama LLM requests; circuit breakers to switch to lightweight deterministic heuristic algorithms if LLM inference is temporarily saturated or offline.
- **NFR-REL-03:** Automated database snapshots and transactional write-ahead logging (WAL) ensuring Recovery Point Objective (RPO) $< 1\text{ hour}$ and Recovery Time Objective (RTO) $< 15\text{ minutes}$.

### 5.4 Security & Data Privacy
- **NFR-SEC-01:** Zero plain-text storage of credentials; passwords hashed with Argon2id ($m=65536, t=3, p=4$).
- **NFR-SEC-02:** Transport Layer Security (TLS 1.3) enforced for all external communications.
- **NFR-SEC-03:** OWASP Top 10 mitigation: strict input validation via Pydantic v2, parameterized SQL queries via SQLAlchemy 2.0 ORM, strict CORS headers, and Content Security Policy (CSP).
- **NFR-SEC-04:** Privacy by design: no user PII (names, personal contact info) passed to model inference contexts unnecessarily; anonymized context windows used for LLM prompt generation.

### 5.5 Usability, Accessibility & Portability
- **NFR-USE-01:** Responsive design supporting mobile, tablet, and desktop viewports ($360\text{px}$ to $4\text{K}$).
- **NFR-USE-02:** Compliance with WCAG 2.1 Level AA accessibility guidelines (contrast ratios, keyboard navigation, screen-reader aria attributes).
- **NFR-USE-03:** 100% containerized deployment via Docker and Docker Compose for deterministic deployment across developer workstations and production Linux hosts.
