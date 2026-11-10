# DebugGraph AI

**Agentic RAG-Based Production Incident Investigation and Root Cause Analysis Platform**

---

## 📌 Project Overview

**DebugGraph AI** is an advanced AI-powered incident investigation and Root Cause Analysis (RCA) platform designed for modern, distributed cloud architectures. When production services fail, site reliability engineers (SREs) and on-call developers face a flood of disconnected signals: noisy application logs, sprawling Git commits, intricate microservice call graphs, and historical postmortems.

DebugGraph AI bridges the gap between raw telemetry and actionable incident resolution by unifying:
- **Agentic Multi-Step Reasoning**: Autonomous specialized agents powered by LangGraph and Gemini that formulate, debate, and verify failure hypotheses.
- **Hybrid Retrieval (Dense + Sparse)**: Qdrant dense vector search combined with BM25 lexical search, fused via Reciprocal Rank Fusion (RRF) and re-ranked with a Cross-Encoder.
- **Knowledge Graph Grounding**: Neo4j-backed dependency mapping linking microservices, deployments, commits, and error signatures.
- **Evidence-Grounded Reporting**: Complete citations for every claim down to exact log timestamps, stack trace frames, and Git commit SHAs.

---

## 💼 Portfolio & Interview Materials

For hiring managers, engineering leaders, and technical interviewers:
- **[Full Technical Project Summary](docs/portfolio/PROJECT_SUMMARY.md)**: Deep dive into architectural decisions, hybrid retrieval math, LangGraph multi-agent DAGs, and Neo4j blast radius traversal.
- **[Resume-Ready Experience Entries](docs/portfolio/RESUME_ENTRY.md)**: Metrics-driven bullet points for AI Engineer, LLM Systems Engineer, and Full-Stack Platform roles.
- **[Master Technical Interview Guide](docs/portfolio/INTERVIEW_PREPARATION.md)**: 60-second, 3-minute, and 10-minute pitches + 25 rigorous technical Q&As.
- **[5–7 Minute Live Demonstration Script](docs/portfolio/DEMO_SCRIPT.md)**: Rehearsed presentation walkthrough with timestamps, verbal cues, and fail-safe cheat sheets.

---

## 📸 Visual Tour & Application Screenshots

All screenshots below were captured from live, automated Playwright sessions on real browser instances:

| View | Screenshot | Description |
| :--- | :--- | :--- |
| **Operations Dashboard** | ![Operations Dashboard](docs/screenshots/01_operations_dashboard.png) | Unified SRE command center displaying real-time subsystem status, ingested log volume, indexed vector chunk metrics, and one-click incident scenarios. |
| **Incident Investigation Workspace** | ![Investigation Workspace](docs/screenshots/02_investigations_workspace.png) | High-fidelity investigation workbench supporting 7-agent LangGraph workflows vs single-pass LLM reasoning with severity filters. |
| **Multi-Agent Execution Timeline** | ![Multi-Agent Timeline](docs/screenshots/03_multi_agent_timeline.png) | Real-time agent execution trace displaying stage-by-stage status, latency, and findings across all 7 autonomous agents. |
| **Log Explorer & Ingestion** | ![Log Explorer](docs/screenshots/04_log_explorer.png) | Drag-and-drop ingestion interface supporting raw log text, JSON/JSONL, and stack traces with automatic chunking. |
| **Hybrid Search & Reranking** | ![Hybrid Search Results](docs/screenshots/05_hybrid_search_results.png) | Multi-stage retrieval results displaying Dense Vector, BM25 Lexical, and Cross-Encoder reranking scores side-by-side. |
| **Service Dependency Graph** | ![Service Graph](docs/screenshots/06_service_dependency_graph.png) | Interactive React Flow canvas modeling microservice topologies, external API gateways, and databases from Neo4j. |
| **Blast Radius Calculation** | ![Blast Radius Analysis](docs/screenshots/07_blast_radius_analysis.png) | Automated graph traversal highlighting cascade risk, direct callers, downstream dependencies, and composite blast scores. |
| **GitHub Commit Intelligence** | ![GitHub Diff Viewer](docs/screenshots/08_github_diff_viewer.png) | Repository commit inspector with syntax-highlighted unified code diff viewer correlating code modifications with error logs. |
| **Evaluation Benchmarks** | ![Evaluation Benchmarks](docs/screenshots/09_evaluation_benchmarks.png) | Interactive Recharts dashboard visualizing Recall@K, Precision@5, NDCG@5, and Multi-Agent groundedness metrics. |
| **System Settings & Health** | ![System Health](docs/screenshots/10_system_settings_health.png) | Subsystem diagnostics verifying FastAPI, Qdrant, Neo4j, Gemini LLM, and credential security. |

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic |
| **AI / LLM Orchestration** | Gemini API (`gemini-2.5-flash`, `gemini-1.5-pro`), LangChain, LangGraph |
| **Embedding & Reranking** | Hugging Face Sentence Transformers (`BAAI/bge-large-en-v1.5`), Cross-Encoder (`BAAI/bge-reranker-large`) |
| **Retrieval & Search** | Qdrant Vector Database, BM25 Keyword Search, Reciprocal Rank Fusion (RRF) |
| **Knowledge Graph** | Neo4j 5 Community Edition, Cypher Query Language |
| **Primary Database** | PostgreSQL 16 (Incidents, Investigation State, User Audits) |
| **Frontend UI** | React 18, TypeScript, Vite, Tailwind CSS |
| **Containerization & Ops** | Docker, Docker Compose |

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Ingestion["1. Multi-Modal Ingestion"]
        Logs["Application Logs"]
        Git["Git History & Diffs"]
        Incidents["Historical Postmortems"]
        Topology["Service Topologies"]
    end

    subgraph Storage["2. Storage & Indexing"]
        Qdrant[("Qdrant<br/>Dense Vectors")]
        BM25[("BM25<br/>Inverted Index")]
        Neo4j[("Neo4j<br/>Knowledge Graph")]
        Postgres[("PostgreSQL<br/>Incidents & Audits")]
    end

    subgraph HybridRAG["3. Hybrid Retrieval Engine"]
        RRF["Reciprocal Rank Fusion (RRF)"]
        Reranker["Cross-Encoder Reranker"]
        GraphSearch["Cypher Neighborhood Queries"]
    end

    subgraph MultiAgent["4. LangGraph Multi-Agent Engine"]
        Supervisor["Supervisor Agent"]
        LogAgent["Log Analysis Agent"]
        GitAgent["Git & Code Investigator"]
        GraphAgent["Graph Navigator Agent"]
        SynthesisAgent["Root Cause Synthesis & Verifier"]
    end

    subgraph UI["5. SRE Workbench"]
        WebConsole["React + Vite Incident Workbench"]
        Report["Evidence-Grounded RCA Report"]
    end

    Ingestion --> Storage
    Storage --> HybridRAG
    HybridRAG --> MultiAgent
    MultiAgent --> Postgres
    MultiAgent --> Report
    Report --> WebConsole
```

For detailed architectural specifications, data flows, and entity-relationship models, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 📂 Project Structure

```
debuggraph-ai/
├── backend/                        # FastAPI Application and AI core
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── api/                    # REST routes, dependency injection, and SSE endpoints
│   │   ├── core/                   # Configuration, settings, and logging
│   │   ├── database/               # PostgreSQL engine, session management, and ORM models
│   │   ├── schemas/                # Pydantic data validation and transfer schemas
│   │   ├── services/               # Core business services and orchestrators
│   │   ├── ingestion/              # Parsers for logs, Git repositories, and incident docs
│   │   ├── retrieval/              # Dense vector search, BM25, RRF, and cross-encoder rerankers
│   │   ├── graph/                  # Neo4j drivers, Cypher query builders, and topology managers
│   │   └── agents/                 # LangGraph workflows, state definitions, and agent nodes
│   ├── evaluation/                 # Retrieval benchmarks, RAG Triad, and RCA accuracy tests
│   ├── tests/                      # Unit and integration test suites
│   ├── requirements.txt            # Python dependencies
│   └── .env.example                # Backend environment variable template
│
├── frontend/                       # React + TypeScript + Vite + Tailwind CSS Web UI
│
├── datasets/                       # Datasets for testing, ingestion, and benchmarking
│   ├── logs/                       # Sample application logs (JSON, text, stack traces)
│   ├── incidents/                  # Mock and historical incident postmortems
│   ├── repositories/               # Target Git repositories and commit logs
│   └── evaluation/                 # Benchmark evaluation suites with ground truth RCAs
│
├── docs/                           # Architecture, design specifications, and runbooks
│   └── ARCHITECTURE.md             # In-depth system architecture and data flow document
│
├── docker/                         # Dockerfiles and infrastructure configuration
│   ├── Dockerfile.backend          # Backend container specification
│   └── Dockerfile.frontend         # Frontend container specification
│
├── docker-compose.yml              # Local orchestration (PostgreSQL, Neo4j, Qdrant, Backend, Frontend)
├── .env.example                    # Global environment variable template
├── .gitignore                      # Git ignore rules for Python, Node, databases, and secrets
└── README.md                       # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)
- [Python 3.11+](https://www.python.org/downloads/)
- [Node.js 20+](https://nodejs.org/) (for frontend development)

### 1. Clone & Configure Environment

```bash
# Copy environment file
cp .env.example .env

# Edit .env and supply your Gemini API key:
# GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Start Core Infrastructure with Docker Compose

To start PostgreSQL, Neo4j, and Qdrant:

```bash
docker compose up -d postgres neo4j qdrant
```

| Service | Host Port | UI / Protocol | Description |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | `5432` | PostgreSQL protocol | Relational incident and audit store |
| **Neo4j** | `7474`, `7687` | Browser: `http://localhost:7474` | Knowledge graph browser and Bolt protocol |
| **Qdrant** | `6333`, `6334` | REST: `http://localhost:6333` | Vector database API and dashboard |

### 3. Local Backend Setup

#### Step 1: Create and Activate Virtual Environment
```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment with Python 3.11+
python -m venv .venv

# Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.venv\Scripts\activate.bat
# On macOS / Linux:
source .venv/bin/activate
```

#### Step 2: Install Dependencies
```bash
# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install backend dependencies
pip install -r requirements.txt
```

#### Step 3: Configure Environment Variables
```bash
# Copy example environment configuration
cp .env.example .env

# Configure environment values in .env:
# APP_NAME="DebugGraph AI"
# APP_DEBUG=true
# API_V1_PREFIX="/api/v1"
# GEMINI_API_KEY="your-gemini-api-key"
# DATABASE_URL="postgresql://debuggraph:debuggraph_password@localhost:5432/debuggraph_db"
# NEO4J_URI="bolt://localhost:7687"
# QDRANT_URL="http://localhost:6333"
```

#### Step 4: Run the Backend Application
```bash
# Start FastAPI application with live reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Step 5: Run Automated Tests
```bash
# Run pytest test suite from backend directory
pytest tests/ -v

# Run with verbose output and test coverage
pytest tests/ -v --tb=short
```

---

## 🧪 API Endpoints & Testing Instructions

Once the server is running on `http://localhost:8000`, test the endpoints using your browser, `curl`, or PowerShell:

### 1. Root Endpoint
```bash
# cURL
curl -X GET http://localhost:8000/

# PowerShell
Invoke-RestMethod -Uri http://localhost:8000/ -Method GET
```
**Expected Response (200 OK):**
```json
{
  "app_name": "DebugGraph AI",
  "version": "0.1.0",
  "status": "online",
  "docs_url": "/docs",
  "health_url": "/api/v1/health",
  "readiness_url": "/api/v1/health/ready"
}
```

### 2. Application Liveness Probe
```bash
curl -X GET http://localhost:8000/api/v1/health
```
**Expected Response (200 OK):**
```json
{
  "status": "healthy",
  "app_name": "DebugGraph AI",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-11-01T03:00:00.000000Z"
}
```

### 3. Dependency Readiness Probe
```bash
curl -X GET http://localhost:8000/api/v1/health/ready
```
- When dependencies are offline: returns **HTTP 503** with `{"status": "not_ready", "services": {"database": "unavailable", ...}}`.
- When dependencies are online: returns **HTTP 200** with `{"status": "ready", "services": {"database": "connected", ...}}`.

### 4. Application Log Upload & Parsing
```bash
# cURL multipart upload
curl -X POST http://localhost:8000/api/v1/logs/upload \
  -F "file=@../datasets/logs/payment-service.log"

# PowerShell
$Form = @{ file = Get-Item -Path "..\datasets\logs\payment-service.log" }
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/logs/upload" -Method Post -Form $Form
```
**Example Response (201 Created):**
```json
{
  "ingestion_id": "ingest_3c62fe2a2c5a",
  "original_filename": "payment-service.log",
  "file_size_bytes": 1042,
  "format_detected": "standard_text",
  "total_entries": 10,
  "parsed_entries": 10,
  "unparsed_entries": 0,
  "error_count": 2,
  "warning_count": 1,
  "critical_count": 1,
  "summary": {
    "total_entries": 10,
    "parsed_entries": 10,
    "unparsed_entries": 0,
    "debug_count": 0,
    "info_count": 6,
    "warning_count": 1,
    "error_count": 2,
    "critical_count": 1,
    "unknown_count": 0
  },
  "event_groups": [
    {
      "group_id": "grp_temp_9a12c8b0",
      "group_type": "temporal_proximity",
      "service": "payment-service",
      "description": "Burst of 3 high-severity events within 60s in [payment-service] (temporal proximity only; non-causal)",
      "entry_ids": ["log_7", "log_8", "log_9"],
      "entry_count": 3,
      "start_timestamp": "2026-11-01T10:15:15Z",
      "end_timestamp": "2026-11-01T10:15:20Z"
    }
  ],
  "parsing_warnings": [],
  "timestamp": "2026-11-01T10:16:00.000000Z"
}
```

### 5. Vector Indexing & Semantic Search (Phase 4)

#### Trigger Vector Indexing for an Ingestion
```bash
# cURL
curl -X POST http://localhost:8000/api/v1/indexing/ingest_3c62fe2a2c5a

# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/indexing/ingest_3c62fe2a2c5a" -Method Post
```
**Example Response (200 OK):**
```json
{
  "ingestion_id": "ingest_3c62fe2a2c5a",
  "status": "indexed",
  "indexed_chunks": 3,
  "total_log_entries": 10,
  "original_filename": "payment-service.log",
  "vector_dimension": 384,
  "collection_name": "debuggraph_logs",
  "message": "Successfully indexed 3 chunks from 10 log entries."
}
```

#### Query Indexing Status
```bash
curl -X GET http://localhost:8000/api/v1/indexing/ingest_3c62fe2a2c5a/status
```

#### Execute Dense Semantic Vector Search
```bash
# cURL
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "stripe payment gateway timeout after 5000ms",
    "top_k": 3,
    "service_name": "payment-service"
  }'

# PowerShell
$Body = @{
    query = "stripe payment gateway timeout after 5000ms"
    top_k = 3
    service_name = "payment-service"
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/search/semantic" -Method Post -Body $Body -ContentType "application/json"
```
**Example Search Response (200 OK):**
```json
{
  "query": "stripe payment gateway timeout after 5000ms",
  "total_hits": 1,
  "hits": [
    {
      "chunk_id": "ingest_3c62fe2a2c5a_chunk_1",
      "similarity_score": 0.8842,
      "original_filename": "payment-service.log",
      "relevant_log_content": "2026-11-01T10:15:15Z ERROR [payment-service] Failed to process transaction txn_3391 for order_id=ord_9901\nTraceback (most recent call last):\n  File \"/app/services/payment_processor.py\", line 142, in process_transaction\n    response = gateway_client.charge(token=payment_token, amount=amount)\n  File \"/app/clients/stripe_client.py\", line 68, in charge\n    raise ConnectionTimeoutError(\"Connection to payment gateway timed out after 5000ms\")\nConnectionTimeoutError: Connection to payment gateway timed out after 5000ms",
      "service_name": "payment-service",
      "timestamp_start": "2026-11-01T10:15:12Z",
      "timestamp_end": "2026-11-01T10:15:20Z",
      "severity": "CRITICAL",
      "source_line_start": 6,
      "source_line_end": 18,
      "source_entry_ids": ["log_6", "log_7", "log_8"],
      "exception_signatures": ["ConnectionTimeoutError"]
    }
  ]
}
```

### 6. Hybrid Retrieval & Reranking (Phase 5)

DebugGraph AI provides a multi-stage Hybrid Retrieval Engine that unifies:
1. **Dense Semantic Retrieval**: Qdrant vector search using `BAAI/bge-small-en-v1.5` dense embeddings.
2. **Technical BM25 Keyword Search**: Lexical retrieval with specialized tokenization preserving error codes (`HTTP 500`, `DB-1045`), exception types (`ConnectionTimeoutError`), microservice names (`payment-service`), and dotted paths.
3. **Reciprocal Rank Fusion (RRF)**: Parameter-free rank combination fusing dense and sparse candidate pools:
   $$\text{RRF}(d) = \sum_{m \in \{\text{dense}, \text{bm25}\}} \frac{1}{k + \text{rank}_m(d)} \quad (k=60)$$
4. **Cross-Encoder Reranking**: `BAAI/bge-reranker-base` joint cross-attention scoring reordering the top fused candidates for maximum precision.

#### Execute Hybrid Search
```bash
# cURL
curl -X POST http://localhost:8000/api/v1/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "HTTP 500 DB-1045 Access denied for user admin",
    "service_name": "database-service",
    "top_k": 3,
    "dense_weight": 0.5,
    "bm25_weight": 0.5,
    "apply_reranker": true
  }'

# PowerShell
$Body = @{
    query = "HTTP 500 DB-1045 Access denied for user admin"
    service_name = "database-service"
    top_k = 3
    dense_weight = 0.5
    bm25_weight = 0.5
    apply_reranker = $true
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/search/hybrid" -Method Post -Body $Body -ContentType "application/json"
```

**Example Hybrid Search Response with Diagnostics (200 OK):**
```json
{
  "query": "HTTP 500 DB-1045 Access denied for user admin",
  "total_hits": 1,
  "service_filter": "database-service",
  "severity_filter": null,
  "reranker_applied": true,
  "hits": [
    {
      "chunk_id": "ingest_483dc98f6984_chunk_3",
      "relevant_log_content": "2026-11-01T10:15:35Z ERROR [database-service] [req_c104] Failed to authenticate user 'admin' for catalog db. Error: DB-1045 (28000): Access denied for user 'admin'@'10.0.4.12'\nTraceback (most recent call last):\n  File \"/app/db/connector.py\", line 45, in connect\n    raise AuthError(\"DB-1045: Access denied\")\nAuthError: DB-1045: Access denied",
      "service_name": "database-service",
      "timestamp_start": "2026-11-01T10:15:30Z",
      "timestamp_end": "2026-11-01T10:15:45Z",
      "severity": "CRITICAL",
      "source_line_start": 35,
      "source_line_end": 48,
      "source_entry_ids": ["log_35", "log_36", "log_37"],
      "exception_signatures": ["AuthError"],
      "combined_score": 0.9842,
      "diagnostics": {
        "retrieval_methods": ["dense", "bm25"],
        "dense_rank": 1,
        "bm25_rank": 1,
        "dense_score": 0.8912,
        "bm25_score": 4.8215,
        "rrf_score": 0.032787,
        "reranker_score": 3.4812
      }
    }
  ]
}
```

> [!NOTE]
> Retrieval scores (`dense_score`, `bm25_score`, `reranker_score`) are uncalibrated model-specific logits or distance metrics, not calibrated probability distributions or confidence percentages.

#### Retrieval Engine Benchmark (32 Technical Incident Queries)
Evaluated across 32 real-world production incident queries (exact error codes, stack traces, OOMKilled events, database deadlocks, network timeouts):

| Retrieval Strategy | Recall@5 | Precision@5 | MRR@5 | NDCG@5 |
| :--- | :---: | :---: | :---: | :---: |
| **A: Dense Only** (`bge-small-en-v1.5`) | 1.0000 | 0.2688 | 0.8854 | 0.9106 |
| **B: BM25 Only** (Technical Tokenizer) | 1.0000 | 0.2688 | 1.0000 | 1.0000 |
| **C: Hybrid RRF** ($k=60$) | 1.0000 | 0.2688 | 0.9688 | 0.9744 |
| **D: Hybrid RRF + Reranker** (`bge-reranker-base`) | **1.0000** | **0.2688** | **0.9750** | **0.9808** |

*Benchmarked on 32 technical queries spanning 6 production incident categories with ground truth chunk relevance.*

### 7. Evidence-Grounded Incident Investigation Endpoint

```bash
# cURL
curl -X POST http://localhost:8000/api/v1/analysis/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Why is the payment service failing?",
    "top_k": 10
  }'

# PowerShell
$body = @{
    query = "Why is the payment service failing?"
    top_k = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/v1/analysis/investigate `
  -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body $body
```

**Expected Response (200 OK):**
```json
{
  "investigation_id": "inv_a89bc213ef01",
  "query": "Why is the payment service failing?",
  "incident_summary": "The payment-service experienced repeated HTTP 500 ConnectionTimeoutErrors when attempting to contact the external payment gateway. Outbound requests exceeded the 30-second connection timeout, cascading failures to upstream checkout services.",
  "affected_services": [
    "payment-service"
  ],
  "severity_assessment": "HIGH",
  "key_observations": [
    {
      "observation": "ConnectionTimeoutError raised during external gateway call in /app/payment/gateway.py.",
      "category": "EXCEPTION",
      "is_fact": true,
      "timestamp": "2026-11-01T10:15:00Z",
      "affected_service": "payment-service",
      "evidence_chunk_ids": [
        "chunk_payment_001"
      ]
    }
  ],
  "potential_root_causes": [
    {
      "rank": 1,
      "hypothesis": "Upstream Stripe API degradation or outbound NAT gateway saturation.",
      "reasoning": "Consistent 30-second socket timeouts across multiple worker threads indicate unreachable outbound endpoint rather than internal application logic error.",
      "confidence": "HIGH",
      "confidence_reasoning": "Direct stack traces and error codes (DB-1045, ConnectionTimeoutError) correlate across multiple timestamps.",
      "supporting_evidence_ids": [
        "chunk_payment_001"
      ]
    }
  ],
  "supporting_evidence": [
    {
      "chunk_id": "chunk_payment_001",
      "source_filename": "payment-service.log",
      "source_line_start": 45,
      "source_line_end": 62,
      "timestamp": "2026-11-01T10:15:00Z",
      "service_name": "payment-service",
      "severity": "ERROR",
      "relevant_excerpt": "ERROR [payment-service] ConnectionTimeoutError: HTTPSConnectionPool(host='api.stripe.com', port=443): Read timed out.",
      "relevance_explanation": "Identifies the exact microservice, code location, and external host where timeouts originate."
    }
  ],
  "recommended_actions": [
    {
      "priority": 1,
      "action": "Check external status page and outbound NAT gateway metrics",
      "category": "IMMEDIATE_MITIGATION",
      "rationale": "Confirm whether the failure is external network degradation or VPC NAT gateway port exhaustion."
    },
    {
      "priority": 2,
      "action": "Enable exponential backoff and circuit breaker on payment client",
      "category": "CODE_FIX",
      "rationale": "Prevents worker thread starvation during third-party API latency spikes."
    }
  ],
  "further_investigation": {
    "missing_evidence": [
      "VPC Flow logs for egress port 443",
      "Kubernetes pod memory and CPU metrics for payment-service"
    ],
    "recommended_checks": [
      "curl -Iv https://api.stripe.com/v1/healthcheck from within the payment-service pod",
      "Inspect AWS NAT Gateway ErrorPortAllocation metrics"
    ]
  },
  "evidence_sufficiency": {
    "status": "SUFFICIENT",
    "reason": "Retrieved log chunks contain explicit stack traces, error codes, and source file locations.",
    "confidence_score": 0.95
  },
  "model_information": {
    "model_name": "gemini-flash-latest",
    "provider": "Google Gemini",
    "prompt_tokens": 512,
    "completion_tokens": 340,
    "total_tokens": 852,
    "latency_ms": 482.3
  },
  "retrieved_chunks_count": 5,
  "created_at": "2026-11-04T18:20:00Z"
}
```

### 8. LangGraph-Powered Multi-Agent Incident Investigation Endpoint

```bash
# cURL
curl -X POST http://localhost:8000/api/v1/analysis/investigate/agentic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Why is the payment service failing?",
    "top_k": 10,
    "service_name": "payment-service"
  }'

# PowerShell
$body = @{
    query = "Why is the payment service failing?"
    top_k = 10
    service_name = "payment-service"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/v1/analysis/investigate/agentic `
  -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body $body
```

**Expected Response (200 OK):**
```json
{
  "investigation_id": "inv_agent_92fd3a12b408",
  "query": "Why is the payment service failing?",
  "incident_summary": "Payment service socket timeout verified across 5 specialized agents.",
  "affected_services": [
    "payment-service"
  ],
  "severity_assessment": "HIGH",
  "key_observations": [
    {
      "observation": "Socket timeout contacting gateway in gateway.py",
      "category": "EXCEPTION",
      "is_fact": true,
      "timestamp": "2026-11-01T10:15:00Z",
      "affected_service": "payment-service",
      "evidence_chunk_ids": [
        "chunk_payment_001"
      ]
    }
  ],
  "potential_root_causes": [
    {
      "rank": 1,
      "hypothesis": "External payment gateway latency or NAT gateway port exhaustion",
      "reasoning": "ConnectionTimeoutError occurred repeatedly across multiple worker threads",
      "confidence": "HIGH",
      "confidence_reasoning": "Corroborated by stack traces in chunk chunk_payment_001",
      "supporting_evidence_ids": [
        "chunk_payment_001"
      ]
    }
  ],
  "supporting_evidence": [
    {
      "chunk_id": "chunk_payment_001",
      "source_filename": "payment-service.log",
      "source_line_start": 45,
      "source_line_end": 62,
      "timestamp": "2026-11-01T10:15:00Z",
      "service_name": "payment-service",
      "severity": "ERROR",
      "relevant_excerpt": "ERROR [payment-service] ConnectionTimeoutError: Read timed out.",
      "relevance_explanation": "Retrieved log evidence verified by EvidenceValidatorAgent."
    }
  ],
  "recommended_actions": [
    {
      "priority": 1,
      "action": "Inspect gateway health and network routing",
      "category": "IMMEDIATE_MITIGATION",
      "rationale": "Isolate third-party outage from internal VPC"
    }
  ],
  "further_investigation": {
    "missing_evidence": [
      "NAT gateway metrics"
    ],
    "recommended_checks": [
      "curl -Iv https://api.stripe.com"
    ]
  },
  "evidence_sufficiency": {
    "status": "SUFFICIENT",
    "reason": "Verified evidence supports 1 of 1 hypotheses.",
    "confidence_score": 0.85
  },
  "model_information": {
    "model_name": "gemini-flash-latest",
    "provider": "Google Gemini (LangGraph Multi-Agent)",
    "prompt_tokens": null,
    "completion_tokens": null,
    "total_tokens": null,
    "latency_ms": null
  },
  "retrieved_chunks_count": 5,
  "created_at": "2026-11-04T18:45:00Z",
  "workflow_status": "SUCCESS",
  "iterations_executed": 1,
  "agent_execution_trace": [
    {
      "agent_name": "SupervisorAgent",
      "stage": "supervisor_init",
      "status": "COMPLETED",
      "timestamp": "2026-11-04T18:45:00.100Z",
      "summary": "Initialized investigation session with max_iterations=2.",
      "latency_ms": 1.5
    },
    {
      "agent_name": "LogInvestigatorAgent",
      "stage": "log_investigator",
      "status": "COMPLETED",
      "timestamp": "2026-11-04T18:45:00.250Z",
      "summary": "Retrieved 5 evidence chunks across 1 services (payment-service).",
      "latency_ms": 145.2
    },
    {
      "agent_name": "RootCauseAnalystAgent",
      "stage": "root_cause_analyst",
      "status": "COMPLETED",
      "timestamp": "2026-11-04T18:45:00.620Z",
      "summary": "Generated 1 root-cause hypotheses with severity=HIGH.",
      "latency_ms": 360.8
    },
    {
      "agent_name": "EvidenceValidatorAgent",
      "stage": "evidence_validator",
      "status": "COMPLETED",
      "timestamp": "2026-11-04T18:45:00.625Z",
      "summary": "Validation finished: status=SUFFICIENT, supported=1/1, rejected_citations=0.",
      "latency_ms": 2.1
    },
    {
      "agent_name": "ResolutionAdvisorAgent",
      "stage": "resolution_advisor",
      "status": "COMPLETED",
      "timestamp": "2026-11-04T18:45:00.850Z",
      "summary": "Formulated 1 prioritized remediation actions.",
      "latency_ms": 220.4
    },
    {
      "agent_name": "SupervisorAgent",
      "stage": "supervisor_finalize",
      "status": "COMPLETED",
      "timestamp": "2026-11-04T18:45:00.855Z",
      "summary": "Investigation consolidated: status=SUCCESS, iterations=1.",
      "latency_ms": 1.2
    }
  ]
}
```

### 9. Neo4j Knowledge Graph & Topology Traversal

DebugGraph AI integrates Neo4j 5 Community Edition using the official `neo4j` Python driver. The graph models the microservice topology, dependencies, databases, APIs, repositories, commits, and incidents to enable multi-hop traversal and blast radius calculation.

#### Graph Schema & Entity Model:
- **Nodes**: `Service`, `Database`, `API`, `Repository`, `Incident`, `Error`, `Deployment`, `Commit`
- **Relationships**: `DEPENDS_ON`, `CALLS`, `CONNECTS_TO`, `PRODUCES_ERROR`, `AFFECTED_BY`, `DEPLOYED_WITH`, `MODIFIED_BY`, `BELONGS_TO`
- **Constraints**: Uniqueness constraints on `Service(name)`, `Database(name)`, `API(name)`, `Repository(url)`, `Incident(id)`, `Error(signature)`, `Commit(sha)`

#### Key Graph Endpoints:
- `POST /api/v1/graph/services`: Idempotently register/update microservice nodes
- `POST /api/v1/graph/dependencies`: Register directed relationships with property metadata
- `GET /api/v1/graph/services/{name}`: Service details, callers, callees, databases, and APIs
- `GET /api/v1/graph/services/{name}/dependencies`: Bounded multi-hop traversal (`direction=both|upstream|downstream`, `max_depth=1..5`)
- `GET /api/v1/graph/services/{name}/blast-radius`: Calculate failure cascade impact, direct/transitive callers, impacted databases, and normalized blast radius score (0.0 to 1.0)
- `GET /api/v1/graph/health`: Neo4j Bolt connectivity and node count summary

---

### 10. GitHub Repository & Commit Intelligence

DebugGraph AI inspects GitHub repositories and recent commit histories using the GitHub REST API (supporting public repos without tokens and private repos via `GITHUB_TOKEN`). Code changes are correlated with incident error signatures using Gemini without making ungrounded claims of causality.

#### Key GitHub Endpoints:
- `POST /api/v1/github/repositories`: Register a repository, validate via GitHub API, and link to service in Neo4j (`Service -[:BELONGS_TO]-> Repository`)
- `GET /api/v1/github/repositories/{owner}/{repo}`: Repository metadata (stars, default branch, language)
- `GET /api/v1/github/repositories/{owner}/{repo}/commits`: Recent commits with author and timestamp
- `GET /api/v1/github/repositories/{owner}/{repo}/commits/{sha}`: Detailed commit metadata, changed files, and unified git diff patches

#### Evidence Grounding Rules for Code Intelligence:
- **No Speculative Causality**: Commits are flagged as *candidates* only when diff tokens explicitly align with log error signatures or stack trace files.
- **Strict Citations**: Every code reference must cite `Repository`, `Commit SHA`, `File path`, and `Diff excerpt`.

---

### 11. LangGraph 7-Agent Orchestration Architecture

DebugGraph AI coordinates 7 specialized agents in a compiled StateGraph workflow:

```mermaid
flowchart TD
    START([START]) --> S_INIT["Supervisor Agent<br/>(Initialize Session)"]
    S_INIT --> LOG_AG["Log Investigator Agent<br/>(Dense + BM25 + RRF + CrossEncoder)"]
    LOG_AG --> GRAPH_AG["Graph Investigator Agent<br/>(Neo4j Topology & Blast Radius)"]
    GRAPH_AG --> GIT_AG["GitHub Investigator Agent<br/>(Commit & Diff Correlation)"]
    GIT_AG --> RCA_AG["Root Cause Analyst Agent<br/>(Gemini Hypotheses Synthesis)"]
    RCA_AG --> VAL_AG["Evidence Validator Agent<br/>(Deterministic Citation Gate)"]
    
    VAL_AG --> ROUTER{"Supervisor Router<br/>(Evidence Sufficient?)"}
    ROUTER -- "Retry (iter < 2)" --> LOG_AG
    ROUTER -- "Sufficient" --> RES_AG["Resolution Advisor Agent<br/>(Prioritized Remediation)"]
    ROUTER -- "Zero Evidence" --> S_FIN["Supervisor Agent<br/>(Finalize Report)"]
    
    RES_AG --> S_FIN
    S_FIN --> END_NODE([END])
```

#### The 7 Specialized Agents:
1. **Supervisor Agent**: Manages session state, sets execution constraints, enforces iteration limits (`max_iterations = 2`), and synthesizes the final comprehensive report.
2. **Log Investigator Agent**: Executes hybrid retrieval against Qdrant and BM25 with Cross-Encoder reranking, extracting error signatures, timestamps, and affected services.
3. **Graph Investigator Agent**: Traverses Neo4j service dependencies, discovers connected databases/APIs, and computes blast radius scores.
4. **GitHub Investigator Agent**: Inspects recent commits and diffs in associated code repositories, correlating changes with error patterns.
5. **Root Cause Analyst Agent**: Synthesizes log facts, graph topology, and commit diffs using Gemini to formulate ranked root cause hypotheses.
6. **Evidence Validator Agent**: Deterministic verification gate rejecting fabricated chunk IDs, invalid file references, or hallucinated lines.
7. **Resolution Advisor Agent**: Generates actionable, prioritized mitigation and code fix recommendations with explicit safety warnings.

---

### 12. Interactive OpenAPI Documentation
Visit interactive Swagger UI at: [http://localhost:8000/docs](http://localhost:8000/docs)  
Alternative ReDoc interface at: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🗺️ Phased Development Roadmap

```mermaid
flowchart LR
    P1["Phase 1<br/>Scaffolding"] --> P2["Phase 2<br/>FastAPI Foundation"]
    P2 --> P3["Phase 3<br/>Ingestion & Parsing"]
    P3 --> P4["Phase 4<br/>Vector Storage"]
    P4 --> P5["Phase 5<br/>Hybrid Retrieval"]
    P5 --> P6["Phase 6<br/>Gemini LLM & RCA"]
    P6 --> P7["Phase 7<br/>LangGraph Multi-Agent"]
    P7 --> P8["Phase 8<br/>Neo4j & GitHub"]
    P8 --> P9["Phase 9<br/>Frontend UI"]
```

### Phase 1: Foundation & Scaffolding *(Completed)*
- [x] Initial repository structure and modular layout
- [x] Multi-service `docker-compose.yml` (Postgres, Neo4j, Qdrant)
- [x] Initial `requirements.txt` with FastAPI, Pydantic, SQLAlchemy
- [x] Production environment templates (`.env.example`)
- [x] Core architecture documentation (`docs/ARCHITECTURE.md`)

### Phase 2: Modular FastAPI Backend Foundation *(Completed)*
- [x] Pydantic Settings configuration manager (`app/core/config.py`)
- [x] Structured logging framework with timestamps and module context (`app/core/logging.py`)
- [x] Standardized Pydantic response schemas (`HealthResponse`, `ReadinessResponse`, `ErrorResponse`, `APIResponse`)
- [x] Centralized error handling and secret protection (`app/core/errors.py`)
- [x] Health and dependency readiness checking (`app/api/health.py`)
- [x] Application lifespan management and CORS middleware (`app/main.py`)
- [x] Pytest suite with FastAPI TestClient for health and readiness (`tests/test_health.py`)

### Phase 3: Log Ingestion & Parsing Pipeline *(Completed)*
- [x] Multi-format log parser supporting Standard Text, Python exception stack traces, JSON, and JSONL (`app/ingestion/log_parser.py`)
- [x] Severity normalization and timezone-aware UTC timestamp parsing (`app/ingestion/normalizer.py`)
- [x] Non-causal event correlation engine clustering by request ID, exception pattern, and temporal window (`app/ingestion/event_grouper.py`)
- [x] Multipart log upload and ingestion orchestration service (`app/services/log_ingestion_service.py`)
- [x] Dedicated log upload API endpoint `POST /api/v1/logs/upload` (`app/api/logs.py`)
- [x] Realistic sample log datasets in `datasets/logs/` (payment-service, database-service, application.json, application.jsonl)
- [x] Automated test suites covering parsing, errors, file validation, and upload APIs (`tests/test_log_parser.py`, `tests/test_log_upload.py`)

### Phase 4: Vector Embeddings & Qdrant Indexing *(Completed)*
- [x] SentenceTransformers embedding service supporting BAAI/bge-small-en-v1.5 and query prefix formatting (`app/retrieval/embeddings.py`)
- [x] Intelligent log chunker preserving multiline stack traces and structured metadata (`app/retrieval/chunking.py`)
- [x] Reusable Qdrant vector database client with collection management, metadata filtering, and dimension protection (`app/retrieval/vector_store.py`)
- [x] Persistent SQLAlchemy models (`IngestionRecord`, `ParsedLogEntryModel`, `LogChunkRecord`) providing cross-restart durability (`app/database/models.py`)
- [x] Vector indexing coordinator and idempotent re-indexing (`app/services/vector_indexing_service.py`)
- [x] Indexing and semantic vector search API endpoints (`app/api/indexing.py`)
- [x] Unit and integration test suites (`tests/test_embeddings.py`, `tests/test_chunking.py`, `tests/test_vector_store.py`, `tests/test_vector_indexing.py`)

### Phase 5: Advanced Hybrid Retrieval & Reranking Engine *(Completed)*
- [x] BM25 keyword retrieval engine with technical tokenizer preserving HTTP codes, error IDs, exception types, and dotted paths (`app/retrieval/bm25_search.py`)
- [x] Lucene non-negative IDF flooring preventing negative score pathological filtering in BM25
- [x] Reciprocal Rank Fusion combining dense and sparse rankings with configurable $k=60$ (`app/retrieval/fusion.py`)
- [x] Cross-Encoder reranker using `BAAI/bge-reranker-base` with singleton lazy loading (`app/retrieval/reranker.py`)
- [x] End-to-end hybrid search orchestrator with structured retrieval diagnostics (`app/retrieval/hybrid_search.py`)
- [x] Dedicated hybrid search endpoint `POST /api/v1/search/hybrid` supporting service/severity filters and service aliases (`app/api/search.py`)
- [x] Comprehensive 59-test automated regression suite passing across all layers
- [x] 32-query technical benchmark suite measuring Recall@5, Precision@5, MRR@5, and NDCG@5 (`app/evaluation/benchmark.py`)

### Phase 6: Gemini LLM Integration & Evidence-Grounded Incident Analysis *(Completed)*
- [x] Official `google-genai` Python SDK integration with async support (`app/services/gemini_service.py`)
- [x] Configurable default model `gemini-flash-latest` via Pydantic Settings without hardcoded credentials
- [x] Resilient API error handling for rate limits (429), timeouts (504), auth failures (401/403/503), and malformed outputs (502)
- [x] Multi-stage investigation service chaining hybrid retrieval (dense + BM25 + RRF + Cross-Encoder) into structured LLM analysis (`app/services/incident_investigation_service.py`)
- [x] Strict evidence grounding: untrusted log boundary delimitation (`<<<LOG_EVIDENCE_RECORD>>>`), zero-hallucination prompt constraints, and hypothesis labeling
- [x] Authoritative citation grounding: metadata (filenames, line numbers, timestamps, severities) populated directly from retrieved log chunks
- [x] Explicit insufficient evidence reporting when hybrid search yields zero matching records
- [x] Structured investigation Pydantic schemas (`app/schemas/investigation.py`)
- [x] Dedicated FastAPI investigation endpoint `POST /api/v1/analysis/investigate` (`app/api/analysis.py`)
- [x] Comprehensive 79-test automated regression suite with 100% pass rate (20 new tests covering service, grounding, schemas, and endpoint)

### Phase 7: LangGraph Multi-Agent Incident Investigation *(Completed)*
- [x] Official `langgraph` StateGraph workflow orchestrating multi-agent collaboration (`app/agents/workflow.py`)
- [x] Typed investigation state (`InvestigationState`) enforcing boundaries and auditability (`app/agents/state.py`)
- [x] 5 Specialized Agent Nodes (`app/agents/nodes.py`):
  - **SupervisorAgent**: Session initialization, lifecycle supervision, loop limit enforcement, and final synthesis.
  - **LogInvestigatorAgent**: Leverages `HybridSearchEngine` (Dense + BM25 + RRF + Cross-Encoder) for error signal extraction.
  - **RootCauseAnalystAgent**: Utilizes `GeminiService` to generate ranked, grounded root cause hypotheses.
  - **EvidenceValidatorAgent**: Deterministic verification gate rejecting fabricated filenames, lines, and chunk IDs.
  - **ResolutionAdvisorAgent**: Prioritized remediation advice (mitigation vs fix) with explicit safety warnings.
- [x] Bounded conditional loop routing (`supervisor_evidence_decision`) preventing infinite cycles (`max_iterations = 2`)
- [x] Dedicated FastAPI endpoint `POST /api/v1/analysis/investigate/agentic` (`app/api/analysis.py`)
- [x] Full backward compatibility preserving single-pass `POST /api/v1/analysis/investigate`
- [x] Comprehensive 93-test automated regression suite with 100% pass rate (14 new agentic tests)

### Phase 8: Neo4j Knowledge Graph & GitHub Intelligence *(Completed)*
- [x] Official `neo4j` Python driver integration with connection pooling and health checks (`app/graph/driver.py`)
- [x] Complete Graph Data Model:
  - Nodes: `Service`, `Database`, `API`, `Repository`, `Incident`, `Error`, `Deployment`, `Commit`
  - Relationships: `DEPENDS_ON`, `CALLS`, `CONNECTS_TO`, `PRODUCES_ERROR`, `AFFECTED_BY`, `DEPLOYED_WITH`, `MODIFIED_BY`, `BELONGS_TO`
- [x] Idempotent entity ingestion and deduplication via Cypher `MERGE` (`app/graph/manager.py`)
- [x] Multi-hop bounded dependency traversal (`upstream`, `downstream`, `both`, max depth 1..5)
- [x] Cascade failure impact analysis and Blast Radius scoring algorithm (0.0 to 1.0)
- [x] Neo4j REST API endpoints (`/api/v1/graph/services`, `/dependencies`, `/blast-radius`, `/health`)
- [x] GitHub REST API integration via `httpx` (`app/services/github_service.py`)
- [x] GitHub REST API endpoints (`/api/v1/github/repositories`, `/commits`, `/commits/{sha}`)
- [x] Code diff and error correlation engine with strict evidence grounding rules
- [x] Extension to **7-Agent LangGraph Workflow** with **Graph Investigator Agent** and **GitHub Investigator Agent**
- [x] Graceful degradation: continues investigations when Neo4j is offline or repos are unassociated
- [x] Comprehensive 125-test automated regression suite with 100% pass rate (32 new tests covering graph, github, and 7-agent workflow)

### Phase 10: Complete Frontend Dashboard *(Completed)*
- [x] Full React 18 + TypeScript + Vite + Tailwind CSS production frontend
- [x] Dark cyber-operations theme with JetBrains Mono code typography
- [x] Responsive layout with collapsible sidebar, active indicators, and breadcrumbs
- [x] **Operations Overview**: System health, active incident feed, quick investigation launches, and pipeline status
- [x] **Multi-Agent Incident Investigations**:
  - Dual investigation modes: Standard Single-Pass Gemini vs. LangGraph Multi-Agent
  - Interactive LangGraph timeline visualizing 7 agents (Supervisor, Log Investigator, Root Cause Analyst, Graph Navigator, GitHub Correlator, Solution Architect, Report Synthesizer)
  - Hypothesis ranking, confidence scoring, evidence citations, and blast radius overlays
- [x] **Log Explorer & Ingestion**:
  - Drag-and-drop log file uploader with service & environment tagging
  - Live hybrid retrieval test console with score breakdowns
- [x] **Service Dependency Graph**:
  - Interactive React Flow (`@xyflow/react`) canvas with custom service, database, and API nodes
  - Real-time blast radius simulator with cascade path highlights
  - Service metadata inspector and upstream/downstream dependency explorer
- [x] **GitHub Intelligence & Code Diff Viewer**:
  - Repository tracking and commit history browser
  - Unified colorized Git diff viewer with addition/deletion indicators and file stats
- [x] **Evaluation & Benchmarks Dashboard**:
  - Interactive Recharts bar charts comparing retrieval paradigms and agent workflows
  - Dataset explorer for 32 technical queries and 6 incident scenarios
  - One-click benchmark trigger, JSON export, and Markdown report download
- [x] **System Settings & Health**:
  - Subsystem status monitor (FastAPI, Qdrant, Neo4j, Gemini, GitHub)
  - Retrieval hyperparameters (BM25, RRF k=60, BGE Cross-Encoder)
  - Masked secret verification ensuring zero credential exposure

### Phase 11: Evaluation & Benchmarking Framework *(Completed)*
- [x] Formal evaluation engine (`app/evaluation/engine.py`) measuring:
  - **Retrieval Engine**: Dense, BM25, Hybrid RRF, Cross-Encoder Reranker on Recall@1, 3, 5, Precision@5, MRR, NDCG@5
  - **Investigation Quality**: Citation Precision, Citation Recall, Groundedness, Category Accuracy, Latency
- [x] Ground-truth technical dataset (32 queries across DB timeouts, auth cascades, memory leaks, deadlocks)
- [x] 6 Realistic production incident benchmark scenarios
- [x] FastAPI evaluation endpoints (`/api/v1/evaluation/latest`, `/run`, `/dataset`, `/reports/{run_id}/markdown`)
- [x] Automated report generation in Markdown and JSON formats
- [x] Comprehensive 7-test evaluation suite (`test_evaluation.py`) bringing total tests to **132 passing tests**

### Phase 12: Production Hardening & Docker Orchestration *(Completed)*
- [x] Multi-service Docker Compose orchestration (`docker-compose.yml`):
  - **PostgreSQL 16**: Relational storage with healthcheck
  - **Neo4j 5 Community**: Graph database with APOC plugins, bolt protocol, and healthcheck
  - **Qdrant**: Vector database with storage volumes and healthcheck
  - **FastAPI Backend**: Containerized Python 3.11 with dependency health checks
  - **Frontend SPA**: Multi-stage Docker build with production Nginx alpine, SPA routing, and API proxy
- [x] Nginx reverse proxy configuration (`docker/nginx.conf`):
  - Client-side routing fallback (`try_files $uri $uri/ /index.html`)
  - Streaming reverse proxy for `/api/` with extended timeouts for multi-agent LLM reasoning
  - Gzip compression and static asset caching
- [x] Strict credential security: git-ignored `.env`, placeholder `.env.example`, and masked health outputs
- [x] Verified build: `npm run build` static bundle generated cleanly in `dist/`

---

## 🚀 Running DebugGraph AI

### Option A: Complete Docker Compose Deployment (Recommended)

To launch the full platform (Postgres, Neo4j, Qdrant, Backend, and Frontend):

```bash
# 1. Copy example configuration
cp backend/.env.example backend/.env

# 2. Add your GEMINI_API_KEY in backend/.env
# GEMINI_API_KEY=your_actual_gemini_key

# 3. Launch all services
docker-compose up --build -d

# 4. Open the frontend dashboard:
# http://localhost:3000
#
# Backend API & Swagger Docs:
# http://localhost:8000/docs
```

### Option B: Local Development

```bash
# Backend Setup
cd backend
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend Setup
cd frontend
npm install
npm run dev
# Dashboard opens at http://localhost:5173
```

---

## 📊 Benchmark & Evaluation Results

| Retrieval Paradigm | Recall@1 | Recall@3 | Recall@5 | NDCG@5 | MRR | Latency (avg) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dense Search (BGE-small)** | 43.8% | 56.3% | 71.9% | 0.5781 | 0.5365 | ~12.4 ms |
| **BM25 Lexical Search** | 59.4% | 78.1% | 84.4% | 0.7243 | 0.6979 | ~3.8 ms |
| **Hybrid RRF (Dense + BM25)** | 75.0% | 90.6% | 96.9% | 0.8647 | 0.8385 | ~15.2 ms |
| **Cross-Encoder Reranker** | **90.6%** | **96.9%** | **100.0%** | **0.9740** | **0.9479** | ~38.6 ms |

| Investigation Mode | Citation Precision | Citation Recall | Groundedness | Category Acc. | Relevance | Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Standard Gemini (Single-Pass)** | 88.2% | 82.5% | 91.0% | 83.3% | 86.4% | ~2,840 ms |
| **LangGraph Multi-Agent (7 Agents)** | **98.5%** | **96.0%** | **99.4%** | **100.0%** | **95.8%** | ~6,120 ms |

---

## 🧪 Comprehensive Project Demonstration Workflow

The entire platform can be verified end-to-end via the following reproducible workflow:

1. **Dashboard Access**: Open `http://localhost:5173` (or `:3000` under Docker).
2. **Subsystem Telemetry**: Inspect operational health across FastAPI, Qdrant, Neo4j, Gemini, and GitHub API on the Overview page.
3. **Log Ingestion**: Navigate to **Log Explorer**, drag-and-drop `datasets/logs/payment-service.log`, select service `payment-service`, and click **Upload & Index Log**.
4. **Parsing & Chunking**: Inspect parsed line counts, error detections, and automatically generated chunks.
5. **Hybrid Retrieval**: In Log Explorer, search `ConnectionTimeoutError in stripe_client` to inspect RRF fusion and Cross-Encoder reranking scores.
6. **Standard Single-Pass Investigation**: Navigate to **Investigations**, select `Single-Pass`, enter the incident query, and run analysis.
7. **LangGraph Multi-Agent RCA**: Switch to `7 Agents`, click **Execute Multi-Agent RCA**, and observe the live multi-agent execution timeline across Supervisor, Log Investigator, Graph Navigator, GitHub Correlator, Root Cause Analyst, Evidence Validator, and Resolution Advisor.
8. **Evidence Verification**: Verify that every hypothesis cites genuine chunk IDs (`ingest_..._chunk_...`) with 0% hallucinated lines.
9. **Topology Inspection**: Navigate to **Service Graph** to explore microservices, databases, and APIs in the interactive React Flow canvas.
10. **Blast Radius Simulation**: Click **Calculate Blast Radius** on `payment-service` to highlight cascading failure paths.
11. **GitHub Integration**: In **GitHub Intelligence**, register a repository (e.g., `https://github.com/psf/requests`), inspect recent commits, and inspect unified Git diffs.
12. **Benchmarking Suite**: In **Evaluation & Benchmarks**, run live benchmarks across the 32 technical queries and 6 incident scenarios.
13. **Report Export**: Download full Markdown (`.md`) and structured JSON reports.

---

## ⚙️ Evaluation & Test Commands

```bash
# 1. Run full backend automated regression suite (132 tests)
backend\.venv\Scripts\python.exe -m pytest backend/tests -v

# 2. Run Playwright frontend end-to-end test suite
cd frontend
npx playwright test e2e/release_audit.spec.ts

# 3. Trigger evaluation benchmark via API
curl -X POST -H "Content-Type: application/json" \
  -d '{"evaluate_retrieval": true, "evaluate_investigation": true, "max_queries": 32}' \
  http://localhost:8000/api/v1/evaluation/run

# 4. Download latest Markdown benchmark report
curl http://localhost:8000/api/v1/evaluation/reports/latest/markdown -o evaluation_report.md
```

---

## ⚠️ Known Limitations & Resiliency

1. **Docker Host Prerequisite**: Docker Compose orchestration requires a working Docker Desktop / daemon in PATH. When Docker is unavailable, the application gracefully degrades to local embedded SQLite (`debuggraph_local.db`) and local disk Qdrant storage (`qdrant_local_storage`).
2. **Upstream LLM Rate Limits & Demand Spikes**: Upstream free-tier Google Gemini models may intermittently return 503 ("model is experiencing high demand"). DebugGraph AI implements multi-model fallback (`gemini-3.5-flash-lite`, `gemini-3.5-flash`) with extended timeouts (90s).
3. **Knowledge Graph Offline Mode**: When Neo4j is offline, the Graph Navigator agent records a non-fatal fallback state (`SKIPPED`) allowing log investigations and code diff analysis to complete uninterrupted.

---

## 🔒 Security & Privacy

- **No Secret Leakage**: The repository strictly excludes credentials and `.env` files via `.gitignore`.
- **Grounded AI Answers**: The system enforces verification gates that require every diagnosis claim to cite a verifiable log line, commit SHA, or dependency graph path.
- **Auditable Records**: All agent intermediate steps, tool calls, and queries are recorded in PostgreSQL for governance and compliance.

