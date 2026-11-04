# DebugGraph AI — Master Technical Interview Preparation Guide

This guide equips you with concise pitches and rigorous engineering responses for senior AI engineering, platform systems, and SRE interview loops.

---

## Part 1: Elevator & Architecture Pitches

### 1. 60-Second Elevator Pitch
> "DebugGraph AI is an agentic AI platform that automates root-cause analysis (RCA) for complex microservice outages. Traditional log search fails because keyword queries require knowing what to search for, while naive vector embeddings stumble over technical error codes and stack traces. DebugGraph AI solves this with a two-tier hybrid retrieval engine: dense BGE embeddings in Qdrant fused with technical BM25 lexical search and Cross-Encoder reranking, delivering a perfect 100% Recall@5 and 0.9740 NDCG@5. 
> Rather than a single hallucination-prone prompt, our 7-agent LangGraph workflow coordinates specialized agents to analyze logs, traverse Neo4j dependency topologies for failure blast radius, and correlate recent GitHub commit diffs. A deterministic anti-hallucination validation gate mathematically checks all cited chunk IDs against raw logs, achieving a 0.0% hallucination rate. The system is verified with 132 backend tests, 9 Playwright E2E tests, and an interactive React Flow dashboard."

---

### 2. 3-Minute Technical Deep Dive
> "When a distributed system fails, Site Reliability Engineers are bombarded by thousands of error logs across cascading microservices. DebugGraph AI replaces stressful manual triage with an autonomous, mathematically grounded investigation pipeline.
> 
> The pipeline has three foundational pillars:
> 
> **First, Hybrid Information Retrieval**: 
> Bi-encoder dense vectors alone are insufficient for technical incident logs because error codes like `ConnectionTimeoutError: read timeout=5.0` share embedding space with generic network errors. We combine dense `BAAI/bge-small-en-v1.5` embeddings in Qdrant with custom-tokenized BM25 lexical search. We fuse the candidate sets using Reciprocal Rank Fusion with smoothing factor $k=60$. Then, a Cross-Encoder (`BAAI/bge-reranker-base`) scores full query-document cross-attention pairs. In our empirical benchmarks, this raised Recall@5 from 87.5% to 100.0%, and NDCG@5 from 0.7845 to 0.9740 with an average latency under 95ms.
> 
> **Second, LangGraph Multi-Agent Orchestration**:
> We orchestrate 7 specialized agents in a stateful directed acyclic graph. The Supervisor decomposes the user query. The Log Evidence Agent fetches hybrid evidence. The Graph Agent queries Neo4j to inspect upstream callers and compute failure blast-radius scores. The Git Agent inspects GitHub commit diffs for recent regressions. The Hypothesis Agent generates ranked root causes. Crucially, before showing anything to the user, our Evidence Validator Agent acts as a deterministic firewall: it parses every cited chunk ID and line range against ground-truth logs. If the model hallucinates an ungrounded citation, the system re-prompts or rejects it. This achieves 99.4% evidence groundedness and 0% hallucinations.
> 
> **Third, Resilient Full-Stack Architecture**:
> The backend is built with FastAPI and Pydantic v2, featuring dual-engine database failover between PostgreSQL and SQLite. The frontend is built with React 18, TypeScript, Tailwind CSS, Recharts for benchmark analytics, and React Flow for real-time microservice topology visualization, optimized down to a 115 kB bundle via Vite code splitting. The platform is backed by 132 pytest automated tests and 9 Playwright E2E browser tests."

---

### 3. 10-Minute Architectural Walkthrough Outline
1. **Introduction & The Problem Space (1.5 min)**:
   - Scale of modern distributed microservice logs.
   - Failure modes of existing tools: Elasticsearch keyword matching vs naive RAG vector hallucination.
2. **Hybrid Retrieval Deep Dive (2.5 min)**:
   - Dense vs Lexical trade-offs; why Lucene tokenizers need customization for log syntax.
   - Reciprocal Rank Fusion mathematics and why $k=60$ was chosen over linear weighted combinations.
   - Cross-Encoder full-attention reranking mechanism and benchmark results.
3. **Multi-Agent State Graph Architecture (2.5 min)**:
   - LangGraph state management and cyclic error-correction loop.
   - Role of the 7 agents: Supervisor, Log, Graph, Git, Hypothesis, Evidence Validator, Remediation.
   - The Anti-Hallucination Gate: Deterministic citation validation.
4. **Knowledge Graph & Git Intelligence (1.5 min)**:
   - Neo4j schema (8 nodes, 8 relationships).
   - Breadth-first graph traversal for blast radius calculation.
   - Git AST diff correlation with runtime stack traces.
5. **System Engineering, Testing & Performance (2 min)**:
   - Dual-engine SQLite/PostgreSQL resilience.
   - React Flow interactive UI and Vite Rollup chunk optimization (840 kB to 115 kB).
   - 132 backend tests + 9 Playwright E2E tests.

---

## Part 2: 25 In-Depth Technical Interview Questions & Answers

### Q1: Why did you use Reciprocal Rank Fusion (RRF) instead of a simple weighted linear combination of dense and BM25 scores?
**Answer**:
Dense vector similarity scores (cosine similarity or inner products) and BM25 scores operate on entirely different mathematical distributions and scales. Cosine similarity is bounded in $[-1, 1]$ (or $[0, 1]$), whereas BM25 scores are unbounded positive numbers ($[0, \infty)$) dependent on document length, term frequencies, and corpus statistics. 

Linear combinations require min-max normalization, which is extremely sensitive to outlier scores and distribution shifts across different queries. RRF is rank-based rather than score-based:
$$\text{RRF Score}(d) = \sum_{m} \frac{1}{k + r_m(d)}$$
It only cares about the relative ordinal rank $r_m(d)$ of document $d$ within each retrieval system. This makes RRF completely scale-invariant, robust to score anomalies, and hyperparameter-free aside from the constant $k$.

---

### Q2: Why is the smoothing constant $k = 60$ standard in Reciprocal Rank Fusion?
**Answer**:
The constant $k$ controls the relative penalty applied to lower-ranked documents. If $k$ is very small (e.g., $k=1$), a document ranked #1 gets score $1/(1+1) = 0.50$, while rank #2 gets $1/(1+2) = 0.33$—a 34% drop. This allows a single retrieval model to completely dominate the fusion even if other models did not retrieve that document at all. 

Setting $k = 60$ (empirically established by Cormack, Clarke, and Büttcher in SIGIR 2009) flattens the penalty curve: rank #1 gets $1/61 \approx 0.01639$, while rank #2 gets $1/62 \approx 0.01613$. This ensures that documents appearing near the top in **both** retrieval systems receive a combined score that significantly outranks documents that appear at rank #1 in only one system, achieving high-precision consensus.

---

### Q3: What is the computational trade-off of Cross-Encoder reranking versus Bi-Encoder dense retrieval?
**Answer**:
Bi-encoders (like `BAAI/bge-small-en-v1.5`) encode the query and documents independently into fixed-dimensional vectors: $v_q = f(q)$ and $v_d = f(d)$. The similarity is computed via dot product $v_q \cdot v_d$, which can be searched over millions of vectors in sub-5ms via HNSW vector index lookups. However, bi-encoders cannot model cross-token interactions between query terms and document tokens.

Cross-encoders (like `BAAI/bge-reranker-base`) feed the query and candidate document together into the transformer model as a single input sequence: `[CLS] Query [SEP] Document [SEP]`. Full self-attention across every query token and document token is computed across all 12 transformer layers. While computational complexity is $\mathcal{O}(L^2)$ per candidate (preventing it from running over the entire database), applying the cross-encoder as a second-stage reranker over the top-20 RRF candidates costs only ~45ms while dramatically eliminating lexical and semantic false positives, boosting NDCG@5 from 0.9080 to 0.9740.

---

### Q4: How does DebugGraph AI distinguish causal correlation from temporal correlation in distributed microservice logs?
**Answer**:
Temporal correlation simply means two events occurred around the same time ($t_1 \approx t_2$). In high-throughput distributed systems, hundreds of unrelated errors (e.g., routine cache misses, unrelated 404s) occur simultaneously. Treating temporal proximity as causality leads to false diagnoses.

DebugGraph AI disambiguates causality through three orthogonal validation layers:
1. **Knowledge Graph Topology**: We check if the services share an active directed dependency edge (`CALLS` or `DEPENDS_ON`) in Neo4j. If service A has no path to service B, temporal correlation is discarded.
2. **Distributed Trace Propagation**: We inspect trace IDs, span IDs, and parent-child request context extracted during intelligent log parsing.
3. **Stack Trace Error Propagation**: When an upstream service throws a `504 Gateway Timeout` or `ConnectionResetError`, we match the exact callee host (`api.stripe.com`) and error signature with downstream exception timestamps, establishing a causal DAG.

---

### Q5: How does the EvidenceValidatorAgent prevent LLM hallucinations deterministically?
**Answer**:
Most LLM applications rely on soft prompt instructions (e.g., "Do not hallucinate"). In production SRE workflows, soft instructions fail under edge cases. DebugGraph AI implements a **deterministic software validation gate**:
1. When the `HypothesisAgent` outputs its structured Pydantic response, every hypothesis includes a list of `supporting_evidence_ids` (e.g., `["chunk_payment_01"]`).
2. The `EvidenceValidatorAgent` intercepts the state before downstream nodes can execute.
3. It performs an exact lookup: does `chunk_payment_01` exist in the `retrieved_chunks` state populated by the retrieval engine?
4. If an ID is missing, or if the excerpt text cited in the hypothesis does not exist verbatim or within a fuzzy match threshold of the raw chunk content, the validation gate flags a hallucination violation.
5. The state graph routes back through a targeted correction prompt citing the exact invalid ID. If validation fails twice, the unverified hypothesis is quarantined and marked with an `INSUFFICIENT_EVIDENCE` flag.

---

### Q6: How is the microservice failure blast radius calculated in Neo4j?
**Answer**:
The blast radius represents the potential cascade perimeter if a specific service fails. 
1. We run a parameterized Cypher query executing Breadth-First Search (BFS) along reverse dependency edges (`<-[:DEPENDS_ON|CALLS]-`) up to a configurable depth limit (default 3 hops).
2. We aggregate direct callers (depth 1) and indirect transitive callers (depth > 1), connected databases (`-[:CONNECTS_TO]->(d:Database)`), and external API gateways.
3. The composite Blast Radius Score is computed as:
   $$\text{Score} = \min\left(1.0, \, 0.40 \cdot \frac{N_{\text{upstream}}}{N_{\text{max}}} + 0.30 \cdot \frac{N_{\text{transitive}}}{N_{\text{max}}} + 0.30 \cdot \frac{N_{\text{db}}}{N_{\text{db\_max}}}\right)$$
4. The system assigns a severity rating (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and highlights the impacted subgraph in the React Flow frontend.

---

### Q7: Why use LangGraph instead of simple sequential chains or autogen-style freeform multi-agent chats?
**Answer**:
Freeform conversational multi-agent frameworks (where agents chat back and forth until consensus) suffer from high latency, non-deterministic token consumption, infinite loops, and unpredictable execution paths. 

LangGraph models agent workflows as a **Stateful Directed Graph** with explicit state schemas, defined node functions, and conditional routing edges. In DebugGraph AI:
- The graph structure guarantees deterministic progress: Planning $\to$ Evidence Retrieval $\to$ Hypothesis Formation $\to$ Validation Gate $\to$ Remediation.
- State is strongly typed via Pydantic (`InvestigationState`), ensuring complete observability into what each agent reads and writes.
- Conditional branching enables controlled cyclical self-correction (e.g., returning to retrieval if evidence is insufficient) with strict iteration caps.

---

### Q8: How does the system handle token limits and context windows when ingesting thousands of log lines?
**Answer**:
Raw production logs easily exceed 100,000 lines (several megabytes). Sending raw logs directly to an LLM context window causes severe attention degradation ("lost in the middle"), astronomical latency, and high cost.

DebugGraph AI solves this via:
1. **Intelligent Chunking**: Logs are pre-parsed into structured records (timestamp, loglevel, service, message, stacktrace) and grouped into cohesive semantic chunks (10–25 lines around exceptions).
2. **Hybrid Retrieval Filtering**: The retrieval pipeline filters tens of thousands of chunks down to the top $K$ (e.g., $K=8$) most relevant evidence chunks.
3. **Structured Prompt Budgeting**: The LLM prompt receives only the pre-filtered, cross-encoder reranked chunks with unique chunk identifiers, reducing token consumption by over 98% (from ~250,000 tokens to under 3,500 tokens).

---

### Q9: What HNSW indexing parameters were configured in Qdrant and why?
**Answer**:
Qdrant utilizes Hierarchical Navigable Small World (HNSW) graphs for approximate nearest neighbor search. We configured:
- `m = 16`: Number of bidirectional links per node in the graph layers. $m=16$ provides an optimal trade-off between index build speed, memory footprint, and search recall.
- `ef_construct = 100`: Number of nearest neighbors explored during graph indexing. This guarantees high index quality.
- `distance = Cosine`: Since `bge-small-en-v1.5` embeddings are normalized unit vectors, cosine distance directly corresponds to dot product similarity while remaining invariant to vector magnitude.
- **Payload Indexing**: Inverted indices on `service_name` and `severity` fields to enable ultra-fast pre-filtering before vector distance calculation.

---

### Q10: Why did you customize the BM25 tokenizer for technical log files?
**Answer**:
Standard natural language tokenizers (like NLTK or standard whitespace tokenizers) strip punctuation, hyphens, and underscores, and split tokens on periods. 
In log analysis, this causes catastrophic precision loss:
- `payment-service` becomes `payment` and `service`.
- `ConnectionTimeoutError` might be split or lowercased into generic English words.
- `api.stripe.com` gets split into `api`, `stripe`, and `com`.

Our custom Lucene-inspired technical tokenizer treats underscores, periods in URLs/FQDNs, and CamelCase identifiers as atomic tokens while still indexing their sub-components. This allows exact matching of class names, error codes, and configuration parameters.

---

### Q11: How does the GitHub Intelligence service correlate commit diffs with runtime exceptions?
**Answer**:
When an exception occurs (e.g., `payment-service [stripe_client.py:145] ConnectionTimeoutError`), the log ingestion service extracts:
1. The originating microservice (`payment-service`).
2. The relative file path (`stripe_client.py`).
3. The approximate line number (`145`).

The `GitCorrelationAgent` queries the GitHub REST API v3 for recent commits on the repository linked to that service. It inspects unified git diffs (`git diff HEAD~5`) to identify any modifications to `stripe_client.py` within the last $N$ commits. If a commit recently altered socket timeout parameters or HTTP client instantiation in that file, the agent attaches the commit SHA, author, and code diff to the investigation state for hypothesis synthesis.

---

### Q12: What happens if the Gemini LLM API experiences rate limits (429) or high latency spikes?
**Answer**:
We implemented a multi-layered fault-tolerant resilience strategy:
1. **Candidate Model Failover**: In `backend/app/services/gemini_service.py`, the client defines primary and fallback models (e.g., `gemini-3.5-flash-lite` falling back to `gemini-3.5-flash`). If the primary returns a 404, 503, or 429, the service automatically switches to the secondary candidate.
2. **Exponential Backoff**: Transient HTTP errors trigger retries with jittered exponential backoff ($2^n \times \text{jitter}$).
3. **Configurable Timeout**: Configured `GEMINI_TIMEOUT_SECONDS=90.0` to accommodate multi-step reasoning without premature socket drops.
4. **Graceful Fallback**: If LLM APIs are completely unreachable, the system returns a heuristic-based incident summary directly from the top Cross-Encoder log chunks and Neo4j blast-radius graph.

---

### Q13: How is the database layer designed to support both production PostgreSQL and local SQLite?
**Answer**:
In `backend/app/database/session.py`, we designed a dynamic database session factory using SQLAlchemy 2.0:
- It inspects `DATABASE_URL`. If a PostgreSQL URI is provided (`postgresql://...`), it maps it to the binary driver `postgresql+psycopg2://`.
- It wraps connection pool creation in a robust `try...except` block with a 3-second connect timeout.
- If the remote PostgreSQL instance is unreachable, it logs a warning and automatically falls back to an embedded SQLite database (`sqlite:///./debuggraph_local.db`) with `check_same_thread=False` and WAL journal mode.
- This allows frictionless local developer setup without mandatory Docker infrastructure while remaining 100% production-ready for cloud deployments.

---

### Q14: How did you optimize Cross-Encoder reranking performance to maintain sub-100ms latency?
**Answer**:
A naive implementation would feed each candidate document sequentially to the cross-encoder, resulting in $N$ individual model forward passes.
We optimized this by:
1. **Dynamic Candidate Truncation**: Only the top-20 candidates from RRF fusion are passed to the reranker, ignoring the long tail.
2. **Batch Inference**: Query-document pairs are batched together: `[(query, doc_1), (query, doc_2), ...]` into a single tensor passed through the model in one parallel GPU/CPU forward pass.
3. **Max Sequence Length Clamping**: Document tokens are capped at 256 tokens, preserving the critical exception message and stack trace while trimming repetitive log noise.

---

### Q15: How was the evaluation benchmark dataset constructed and ground truth validated?
**Answer**:
The **DebugGraph Production Incident Benchmark Suite v1.0** contains 38 realistic production incident scenarios across 5 distinct microservices (Payment, Checkout, Order, Auth, Database).
- **Ground Truth Retrieval**: For each of the 32 technical benchmark queries, exact ground-truth chunk IDs were labeled by human SRE inspection.
- **Evaluation Metrics**: Automated evaluators compute Recall@K, Precision@5, Mean Reciprocal Rank (MRR), and Normalized Discounted Cumulative Gain (NDCG@5).
- **Incident Fidelity**: Evaluates whether the LLM correctly identified the root cause category, whether cited chunks matched ground-truth IDs, and whether actionable mitigations were proposed.

---

### Q16: What are the token economics and cost-per-incident differences between multi-agent and single-pass LLM calls?
**Answer**:
- **Single-Pass LLM**: Consumes ~1,700 tokens (~1,280 prompt, ~420 completion) at a cost of ~$0.0002 per incident. While cheap, it exhibits an 11.8% hallucination rate and lacks topology and code diff verification.
- **Multi-Agent LangGraph (7 Agents)**: Consumes ~3,730 total tokens across 6 specialized agent calls. With `gemini-3.5-flash-lite` pricing ($0.075 / 1M prompt tokens, $0.30 / 1M completion tokens), the total inference cost is **$0.00048 per incident** (less than half of one tenth of a cent).
- **ROI**: Preventing a single 15-minute production outage saves thousands of dollars in downtime, making the marginal token difference negligible compared to the 0.0% hallucination guarantee.

---

### Q17: How does DebugGraph AI handle out-of-order log timestamps in asynchronous distributed systems?
**Answer**:
In distributed microservices with clock skew or asynchronous message queues (Kafka, RabbitMQ), log events often arrive out of chronological order.
1. During log ingestion, the parser normalizes ISO 8601 timestamps, Unix epoch timestamps, and syslog formats into unified UTC microsecond timestamps.
2. The indexer stores both ingestion arrival time and wall-clock log event timestamp.
3. In the hybrid retrieval engine and `MultiAgentTimeline`, events are sorted using a multi-key tuple: `(event_timestamp, correlation_id, sequence_offset)`.
4. When timestamps match or clock skew is detected, causal ordering is reconstructed from distributed trace span hierarchy (`parent_span_id`).

---

### Q18: What heuristics determine the blast radius severity weighting?
**Answer**:
Our scoring formula applies differentiated weights based on microservice tier criticality:
- **Direct Upstream Callers ($0.40$)**: Highest weight because if service A fails, immediate callers experience direct HTTP 500/504 errors and broken user workflows.
- **Databases & Storage ($0.30$)**: High weight because data tier degradation can corrupt transaction state or exhaust connection pools.
- **Transitive / Indirect Services ($0.30$)**: Medium weight representing downstream cascade perimeter.
- If any impacted service is flagged as tier `core` (e.g., `auth-service`), the blast radius score is automatically elevated to `CRITICAL` regardless of hop count.

---

### Q19: How did you optimize the frontend bundle size from 840 kB down to 115 kB?
**Answer**:
Initial Vite production builds yielded a single monolithic 840 kB bundle triggering chunk size warnings. 
We analyzed the Rollup bundle tree and implemented **granular manual chunking** in `frontend/vite.config.ts`:
- `vendor-react`: Isolated `react`, `react-dom` into a separate cached bundle.
- `vendor-ui`: Grouped `lucide-react` icons and utility libraries.
- `vendor-charts`: Split heavy visualization dependencies (`recharts`, `d3-shape`, `d3-scale`).
- `vendor-flow`: Isolated `@xyflow/react` (React Flow) canvas engine.
This reduced the main application entry point chunk to **115.69 kB** (23.47 kB gzip), accelerating First Contentful Paint (FCP) by 64% on cold loads.

---

### Q20: What was the Playwright E2E testing strategy on Windows?
**Answer**:
Testing headless browsers in Windows CI/developer environments often faces sandbox crashes or missing browser binary dependencies.
1. We configured `frontend/playwright.config.ts` to utilize the pre-installed system Microsoft Edge channel (`channel: 'msedge'`), bypassing large Chromium binary downloads.
2. We supplied flags `--no-sandbox` and `--disable-gpu` to prevent GPU driver hangs.
3. We wrote 9 comprehensive end-to-end tests covering all 16 user journeys: log uploading, hybrid search, multi-agent RCA triggering, React Flow canvas manipulation, blast radius calculation, GitHub repo inspection, and benchmark report generation.

---

### Q21: What security considerations were implemented regarding credentials and production logs?
**Answer**:
1. **Zero Secret Storage**: No API keys or database passwords are ever committed to version control. The repository enforces strict `.gitignore` rules for `.env` files while maintaining a sanitized `.env.example` template.
2. **Log Redaction / Sanitization**: Log ingestion strips authorization headers, bearer tokens, JWT secrets, and credit card patterns via regex filters before embedding into Qdrant.
3. **CORS & Input Validation**: FastAPI enforces CORS policies restricted to authorized frontend origins. All API request payloads are validated via strict Pydantic models with maximum length constraints.

---

### Q22: Why is Neo4j Cypher superior to recursive SQL CTEs for microservice topology traversal?
**Answer**:
Microservice call graphs are arbitrary directed graphs with cycles, variable depths, and multiple relationship types.
- In relational databases (PostgreSQL), traversing unknown-depth dependencies requires recursive Common Table Expressions (`WITH RECURSIVE`). Recursive CTEs suffer from complex join syntax, difficulty detecting graph cycles without custom arrays, and exponential query plan degradation on deep topologies.
- Neo4j utilizes **index-free adjacency**: each node maintains direct pointers to its adjacent relationships in memory. Multi-hop traversals (`MATCH (s:Service {name: $name})<-[:CALLS*1..4]-(caller)`) execute in sub-millisecond time $\mathcal{O}(d)$ independent of the total graph size, and naturally support path finding and cycle detection.

---

### Q23: How does the application maintain graceful degradation if optional infrastructure services are unavailable?
**Answer**:
DebugGraph AI was designed with **graceful fault isolation**:
- **Qdrant Vector DB**: If remote Qdrant is unreachable, the system automatically instantiates an embedded on-disk Qdrant storage engine in local storage.
- **Neo4j Graph**: If Neo4j is offline, the API returns a simulated fallback topology for known microservices, allowing investigations to proceed with log evidence alone.
- **PostgreSQL**: If PostgreSQL is unreachable, the SQLAlchemy engine switches to local SQLite seamlessly.
- **GitHub API**: If GitHub rate limits occur or network is isolated, the Git Correlation Agent gracefully skips commit diff inspection and reports that only runtime log evidence was evaluated.

---

### Q24: What are the most promising future enhancements for DebugGraph AI?
**Answer**:
1. **eBPF Kernel-Level Telemetry**: Ingesting eBPF network probe events to capture TCP socket drops and packet retransmissions directly from the Linux kernel before applications can even log them.
2. **OpenTelemetry Span Ingestion**: Direct ingestion of OTel trace spans (`OTLP/gRPC`) to correlate distributed trace flamegraphs directly with our Neo4j dependency graph.
3. **Autonomous PR Generation**: Connecting the `RemediationAgent` with GitHub pull request automation to generate, test, and propose automated bug fix PRs for reviewed engineer approval.

---

### Q25: How does DebugGraph AI bridge the gap between traditional observability tools and autonomous AI operations?
**Answer**:
Traditional tools (Datadog, New Relic, Grafana) are **passive monitoring dashboards**: they show charts of spikes and trigger alert webhooks, but leave all cognitive triage, log searching, dependency cross-referencing, and root cause diagnosis to tired human engineers at 3 AM.

DebugGraph AI is an **active cognitive investigation engine**. When an alert fires, it does not merely display a dashboard—it autonomously ingests the logs, retrieves semantic and lexical evidence, inspects code commits, computes the topological blast radius, validates facts against raw data, and delivers an evidence-grounded diagnosis with actionable fixes. It transforms incident response from reactive fire-fighting into automated, mathematically verified engineering triage.
