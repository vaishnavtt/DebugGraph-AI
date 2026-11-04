# DebugGraph AI — Resume-Ready Bullet Points & Experience Entries

Tailored, impact-driven bullet points for software engineering, AI engineering, and full-stack developer resumes.

---

## 1. Role-Specific Resume Entries

### Option A: For AI Engineer / LLM Systems Engineer Roles

**DebugGraph AI — Agentic AI-Powered Production Incident RCA Platform**  
*Lead AI Systems Architect & Full-Stack Developer* | `Python`, `LangGraph`, `FastAPI`, `Qdrant`, `Gemini`, `Neo4j`, `React`, `TypeScript`  
- Designed and engineered a production incident root-cause analysis (RCA) platform leveraging a **7-agent LangGraph workflow**, cutting mean time to detect (MTTD) by automating evidence retrieval, hypothesis ranking, and remediation planning.
- Built a multi-stage **hybrid retrieval engine** combining `BAAI/bge-small-en-v1.5` dense embeddings in Qdrant with custom technical Lucene BM25 lexical search, reciprocal rank fusion (RRF, $k=60$), and `BAAI/bge-reranker-base` cross-encoder reranking, achieving **100.0% Recall@5** and **0.9740 NDCG@5** (+19.9% lift over standalone lexical search).
- Architected a deterministic **anti-hallucination verification gate** within LangGraph that mathematically validates cited chunk IDs and line numbers against ground-truth logs, eliminating hallucinations (**0.0% hallucination rate** vs 11.8% in single-pass LLM baselines).
- Integrated Google Gemini 3.5 LLMs via the official `google-genai` SDK with asynchronous streaming, token budgeting, multi-model candidate failover, and structured Pydantic schema validation.
- Authored **132 automated backend unit and integration tests** and **9 Playwright E2E browser tests**, validating end-to-end reliability across log ingestion, vector search, multi-agent execution, and graph traversal.

---

### Option B: For Full-Stack Platform / SRE / Observability Engineer Roles

**DebugGraph AI — Distributed Systems Incident Investigation & Topology Platform**  
*Platform & Systems Engineer* | `FastAPI`, `PostgreSQL`, `Neo4j`, `Docker`, `React 18`, `Tailwind CSS`, `React Flow`, `Vite`  
- Developed an observability investigation platform correlating distributed microservice logs, Git commit diffs, and Neo4j dependency graphs to automate failure cascade analysis.
- Modeled complex cloud topologies in **Neo4j** (8 node entities, 8 directed relationships) and implemented a graph traversal algorithm calculating real-time **microservice blast radius scores** and upstream dependency risk.
- Implemented an automated **GitHub Intelligence service** using REST API v3 to correlate runtime exception stack traces with AST commit diffs and pull requests.
- Engineered a high-performance **React 18 + TypeScript** operations dashboard featuring interactive dependency graph visualization using **React Flow**, telemetry charts with **Recharts**, and modular code splitting that reduced the initial client bundle from **840 kB to 115 kB** (23.4 kB gzip).
- Implemented production-grade resilient backend storage with seamless dual-engine compatibility, automatically failing over between PostgreSQL/SQLAlchemy and zero-config local SQLite.

---

## 2. Standalone Metrics & Impact Highlights (For Quick Copy-Paste)

- **100% Recall@5 & 0.9740 NDCG@5**: Outperformed standalone vector search (87.5% Recall@5, 0.7845 NDCG) and BM25 (87.5% Recall@5, 0.8120 NDCG) via Reciprocal Rank Fusion ($k=60$) and Cross-Encoder reranking.
- **99.4% Evidence Groundedness**: Reduced diagnostic hallucination from 11.8% to 0.0% using deterministic LangGraph agentic validation gates.
- **132 Automated Backend Tests**: 100% test pass rate across unit, integration, and API boundary test suites using `pytest` and `httpx`.
- **9 Automated Playwright E2E Tests**: Fully verified end-to-end user workflows across real browser channels on Microsoft Edge and Google Chrome.
- **86% Bundle Size Reduction**: Optimized frontend asset delivery via Vite Rollup manualChunks configuration, shrinking the primary JavaScript bundle from 840 kB to 115.69 kB.
- **7-Agent DAG Architecture**: Coordinated Supervisor, Log Evidence, Graph Evidence, Git Correlation, Hypothesis, Evidence Validator, and Remediation agents in a unified state graph.

---

## 3. Technology Stack Summary (For Resume Skills Section)

- **AI & Agentic Orchestration**: LangGraph, LangChain Core, Google GenAI SDK (Gemini 3.5), Sentence-Transformers, Cross-Encoder, Reciprocal Rank Fusion (RRF), Lucene BM25, Prompt Engineering.
- **Vector & Graph Databases**: Qdrant Vector DB, Neo4j Graph Database (Cypher), HNSW Indexing, Dense Embedding Space (`BAAI/bge-small-en-v1.5`).
- **Backend Architecture**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0, PostgreSQL, SQLite, Uvicorn, Pytest, HTTPX.
- **Frontend & Visualization**: React 18, TypeScript, Vite, Tailwind CSS, React Flow (@xyflow/react), Recharts, Lucide Icons.
- **DevOps, Testing & Quality**: Docker, Docker Compose, Playwright E2E, Git, GitHub API v3, Security Secret Auditing.

