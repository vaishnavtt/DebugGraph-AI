# DebugGraph AI — 5–7 Minute Live Demonstration Script

A structured, rehearsed walkthrough designed for hackathon judges, technical hiring managers, and portfolio presentations.

---

## Demo Overview & Timing Breakdown

| Timestamp | Phase / Section | Core Focus | Visual Asset / View |
| :---: | :--- | :--- | :--- |
| **00:00 - 01:00** | **1. The Hook & The Problem** | Alert storm cognitive overload & traditional log search failure | Operations Dashboard |
| **01:00 - 02:15** | **2. Intelligent Log Ingestion & Hybrid Search** | Dense BGE vectors + Technical BM25 + CrossEncoder reranker | Log Explorer |
| **02:15 - 04:00** | **3. The Multi-Agent Investigation** | 7-agent LangGraph execution & Anti-Hallucination Gate | Investigation Workspace & 7-Agent Trace |
| **04:00 - 05:00** | **4. Topology & Blast Radius** | Neo4j service dependency traversal & cascade risk scoring | Service Dependency Graph (React Flow) |
| **05:00 - 06:00** | **5. GitHub Commit Correlation** | Linking runtime stack traces with recent git commit regressions | GitHub Intelligence Diff Viewer |
| **06:00 - 07:00** | **6. Benchmarks, Metrics & Conclusion** | 100% Recall@5, 0% hallucinations, 132 tests, wrap-up | Evaluation Benchmarks (Recharts) |

---

## Step-by-Step Walkthrough

### Part 1: The Hook & The Problem (00:00 – 01:00)
**View**: `http://localhost:5173/` (Operations Dashboard)  
**Screenshot Reference**: `docs/screenshots/01_operations_dashboard.png`

- **Action [What to Do]**:
  1. Open the browser to the main dashboard.
  2. Point out the real-time telemetry cards: Uploaded Logs, Indexed Evidence Chunks, Knowledge Graph Nodes.
  3. Highlight the "Production Incident Scenarios" quick-launch cards.
- **Narrative [What to Say]**:
  > *"Imagine it's 3 AM, and your on-call pager explodes. Your payments pipeline is failing, customers are abandoning checkouts, and your log aggregator is flooded with tens of thousands of error lines. 
  > Finding the root cause manually takes hours of stressful grep-ing. If you search for 'timeout', you get 5,000 irrelevant hits. If you feed the logs to a generic ChatGPT prompt, it hallucinates fake line numbers.
  > This is **DebugGraph AI**—an agentic AI platform that automates root-cause analysis using a hybrid retrieval engine, a 7-agent LangGraph workflow, and microservice topology reasoning."*

---

### Part 2: Intelligent Log Ingestion & Hybrid Search (01:00 – 02:15)
**View**: Click **"Log Explorer"** in the sidebar  
**Screenshot References**: `docs/screenshots/04_log_explorer.png`, `docs/screenshots/05_hybrid_search_results.png`

- **Action [What to Do]**:
  1. In the sidebar, click on **"Log Explorer"**.
  2. Show the drag-and-drop log ingestion dropzone.
  3. Scroll down to the **"Hybrid Log Search"** section.
  4. In the search input, type: `ConnectionTimeoutError in stripe_client` and click **"Search Logs"**.
  5. Expand the top retrieved result to reveal the three retrieval scores: Reranker score, Dense score, and BM25 score.
- **Narrative [What to Say]**:
  > *"Let's see how DebugGraph AI ingests and indexes telemetry. Engineers can drop raw logs, JSON, or stack traces directly into this dropzone. Our parser automatically normalizes timestamps, services, and severity levels, indexing them into Qdrant using BGE embeddings alongside a custom BM25 index.
  > Notice what happens when we execute a technical search for 'ConnectionTimeoutError in stripe_client'. 
  > Unlike pure vector search, which often confuses similar-sounding errors, our two-stage engine uses Reciprocal Rank Fusion followed by a Cross-Encoder reranker. Here, you can see the joint cross-attention score evaluating exact function names and stack traces with sub-100ms latency."*

---

### Part 3: The Multi-Agent Investigation & Anti-Hallucination Gate (02:15 – 04:00)
**View**: Click **"Investigations"** in the sidebar  
**Screenshot References**: `docs/screenshots/02_investigations_workspace.png`, `docs/screenshots/03_multi_agent_timeline.png`

- **Action [What to Do]**:
  1. Click **"Investigations"** in the sidebar.
  2. Point out the mode toggle: **"7 Agents (LangGraph)"** vs **"Single-Pass (Standard Gemini)"**. Keep "7 Agents" selected.
  3. Ensure the query reads: `Why is payment-service throwing ConnectionTimeoutError during Stripe transactions?`
  4. Click the prominent purple button: **"Execute Multi-Agent RCA"**.
  5. As the results load, click the **"7-Agent Trace"** tab.
  6. Walk through the execution sequence: Supervisor $\to$ Log Evidence $\to$ Graph $\to$ Git $\to$ Hypothesis $\to$ Evidence Validator $\to$ Remediation.
  7. Switch back to the **"Summary"** tab and show the ranked root cause and ground-truth cited chunk badges.
- **Narrative [What to Say]**:
  > *"Now for the core intelligence: rather than sending an unstructured prompt to an LLM, we click 'Execute Multi-Agent RCA'. This launches a stateful LangGraph workflow powered by Google Gemini 3.5.
  > Let's inspect the '7-Agent Trace' tab. Look at how the agents collaborate:
  > - The **Supervisor Agent** plans the investigation.
  > - The **Log Evidence Agent** pulls the reranked evidence.
  > - The **Graph Agent** checks topology dependencies in Neo4j.
  > - The **Git Agent** inspects recent commits.
  > - The **Hypothesis Agent** synthesizes the diagnosis.
  > - But most importantly, look at the **Evidence Validator Agent**. This is a deterministic software gate. It checks every cited chunk ID and line number against the actual logs. If the model hallucinates a reference, the gate flags it immediately. In our benchmarks, this eliminated hallucinations completely—bringing the hallucination rate to 0.0%."*

---

### Part 4: Service Topology & Blast Radius Analysis (04:00 – 05:00)
**View**: Click **"Service Graph"** in the sidebar  
**Screenshot References**: `docs/screenshots/06_service_dependency_graph.png`, `docs/screenshots/07_blast_radius_analysis.png`

- **Action [What to Do]**:
  1. Click **"Service Graph"** in the sidebar.
  2. Pan/zoom slightly on the interactive **React Flow** canvas to demonstrate real-time node rendering.
  3. Click on the node labeled **`payment-service`**.
  4. Point out the details panel on the right showing upstream callers (`checkout-service`), downstream dependencies (`auth-service`), and storage (`payments-db`).
  5. Click the button: **"Calculate Blast Radius"**.
  6. Observe the highlighted cascade ring and the computed Blast Radius Score.
- **Narrative [What to Say]**:
  > *"Incidents don't happen in a vacuum. A failure in one microservice triggers cascading failures across the cluster.
  > Here in the Service Graph, powered by Neo4j and React Flow, we map our entire service topology. When we click on `payment-service` and click 'Calculate Blast Radius', our algorithm executes a breadth-first graph traversal.
  > It immediately reveals that while `payment-service` is timing out on the external Stripe gateway, it is directly impacting the upstream `checkout-service`, putting order processing at critical risk. This gives SREs an instant view of the failure perimeter."*

---

### Part 5: GitHub Intelligence & Commit Diff Correlation (05:00 – 06:00)
**View**: Click **"GitHub Intelligence"** in the sidebar  
**Screenshot Reference**: `docs/screenshots/08_github_diff_viewer.png`

- **Action [What to Do]**:
  1. Click **"GitHub Intelligence"** in the sidebar.
  2. Show the registered repository and the commit history list.
  3. Select a commit to open the syntax-highlighted code diff viewer.
  4. Point to the changed lines modifying the HTTP socket timeout parameter.
- **Narrative [What to Say]**:
  > *"Logs tell you what broke; Git tells you who broke it and why.
  > In the GitHub Intelligence view, DebugGraph AI correlates runtime stack traces with recent code changes. By inspecting recent commits to `payment-service`, the system spotted that commit 3f8a91c reduced the socket read timeout from 30 seconds down to 5 seconds.
  > When Stripe experienced a temporary 6-second latency spike, our service aborted immediately, causing the outage. The system connects the code diff directly with the runtime exception."*

---

### Part 6: Evaluation Benchmarks & Conclusion (06:00 – 07:00)
**View**: Click **"Evaluation & Benchmarks"** in the sidebar  
**Screenshot Reference**: `docs/screenshots/09_evaluation_benchmarks.png`

- **Action [What to Do]**:
  1. Click **"Evaluation & Benchmarks"** in the sidebar.
  2. Highlight the Recharts bar charts comparing Dense, BM25, Hybrid, and Cross-Encoder.
  3. Show the **100% Recall@5** and **0.9740 NDCG@5** metrics.
  4. Switch to the **"Multi-Agent vs Standard"** tab showing 99.4% evidence groundedness.
  5. Deliver the concluding wrap-up sentence.
- **Narrative [What to Say]**:
  > *"We didn't just build this system—we rigorously benchmarked it across 38 real-world production incident scenarios.
  > As you can see in these benchmark results:
  > - Standalone dense vector search achieved 87.5% Recall@5.
  > - Our Hybrid + Cross-Encoder architecture achieved **100.0% Recall@5** and **0.9740 NDCG@5**.
  > - Our LangGraph multi-agent workflow achieved **99.4% evidence groundedness** with **0% hallucinations**, backed by **132 automated backend tests** and **9 Playwright E2E tests**.
  > DebugGraph AI transforms incident triage from hours of blind guessing into verified, automated, mathematical precision. Thank you!"*

---

## Live Demo Fail-Safe Cheat Sheet

| Potential Scenario | Fail-Safe Action |
| :--- | :--- |
| **External WiFi / Network drops** | The local backend automatically switches to SQLite fallback (`debuggraph_local.db`) and local Qdrant disk storage; all search and graph features run 100% offline. |
| **Gemini LLM API rate limit / slow** | The system automatically fails over from `gemini-3.5-flash-lite` to `gemini-3.5-flash`. If offline, use the cached mock investigation result. |
| **Demo time runs short (3 minutes)** | Skip Log Upload and GitHub Diff; jump directly from Dashboard $\to$ Multi-Agent Investigation $\to$ Service Graph Blast Radius $\to$ Benchmark Results. |

