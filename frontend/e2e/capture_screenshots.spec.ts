import { test, expect } from '@playwright/test';
import path from 'path';

const SCREENSHOT_DIR = path.resolve('..', 'docs', 'screenshots');

test.describe('DebugGraph AI — Capture High-Resolution Portfolio Screenshots', () => {
  test.use({ viewport: { width: 1600, height: 1000 } });

  test('Capture all 10 release & portfolio screenshots', async ({ page }) => {
    // ------------------------------------------------------------------------
    // 01. Operations Dashboard
    // ------------------------------------------------------------------------
    await page.goto('/');
    await expect(page.getByText('Operations Dashboard')).toBeVisible();
    await expect(page.getByText('Production Ready')).toBeVisible();
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '01_operations_dashboard.png'),
      fullPage: false,
    });
    console.log('Saved: 01_operations_dashboard.png');

    // ------------------------------------------------------------------------
    // 04. Log Explorer (Clean state / dropzone)
    // ------------------------------------------------------------------------
    await page.getByRole('button', { name: /Log Explorer/i }).click();
    await expect(page.getByText('Log Ingestion & Hybrid Explorer')).toBeVisible();
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '04_log_explorer.png'),
      fullPage: false,
    });
    console.log('Saved: 04_log_explorer.png');

    // ------------------------------------------------------------------------
    // 05. Hybrid Search Results
    // ------------------------------------------------------------------------
    const searchInput = page.getByPlaceholder(/Enter search query/i);
    await searchInput.fill('ConnectionTimeoutError in stripe_client');
    await page.getByRole('button', { name: /Search Logs/i }).click();
    await expect(page.getByText(/Reranker:/i).first()).toBeVisible({ timeout: 20000 });
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '05_hybrid_search_results.png'),
      fullPage: false,
    });
    console.log('Saved: 05_hybrid_search_results.png');

    // ------------------------------------------------------------------------
    // 02. Incident Investigation Workspace (Input view)
    // ------------------------------------------------------------------------
    await page.getByRole('button', { name: /Investigations/i }).click();
    await expect(page.getByText('Incident Investigation Workspace')).toBeVisible();
    await expect(page.getByRole('button', { name: /Execute Multi-Agent RCA/i })).toBeVisible();
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '02_investigations_workspace.png'),
      fullPage: false,
    });
    console.log('Saved: 02_investigations_workspace.png');

    // ------------------------------------------------------------------------
    // 03. Multi-Agent Timeline & Investigation Results
    // ------------------------------------------------------------------------
    // Intercept agentic investigation call with high-fidelity realistic response
    await page.route('**/api/v1/analysis/investigate/agentic', async (route) => {
      const jsonResponse = {
        investigation_id: 'inv_live_agentic_stripe_01',
        query: 'Why is payment-service throwing ConnectionTimeoutError during Stripe transactions?',
        incident_summary: 'Critical payment pipeline degradation caused by external API connection timeout in stripe_client.py after commit 3f8a91c reduced socket timeout from 30s to 5s during peak latency spikes.',
        affected_services: ['payment-service', 'checkout-service', 'order-service'],
        severity_assessment: 'CRITICAL',
        key_observations: [
          {
            observation: 'stripe_client.py encountered socket connection timeout after exactly 5000ms',
            category: 'Network / Latency',
            is_fact: true,
            affected_service: 'payment-service',
            evidence_chunk_ids: ['chunk_payment_01', 'chunk_payment_03']
          },
          {
            observation: 'Downstream checkout-service cascade failure resulting in 504 Gateway Timeouts',
            category: 'Cascading Dependency',
            is_fact: true,
            affected_service: 'checkout-service',
            evidence_chunk_ids: ['chunk_payment_04']
          }
        ],
        potential_root_causes: [
          {
            rank: 1,
            hypothesis: 'Premature socket connection timeout in Stripe payment gateway adapter',
            reasoning: 'Commit 3f8a91c reduced HTTP client timeout from 30000ms to 5000ms. Concurrent p99 Stripe API latency of 6200ms triggered immediate ConnectionTimeoutError across all synchronous checkout requests.',
            confidence: 'HIGH',
            confidence_reasoning: 'Direct log stack trace correlation with socket timeout exceptions and recent git commit parameter modification.',
            supporting_evidence_ids: ['chunk_payment_01', 'chunk_payment_03']
          }
        ],
        supporting_evidence: [
          {
            chunk_id: 'chunk_payment_01',
            source_filename: 'payment-service.log',
            source_line_start: 142,
            source_line_end: 158,
            timestamp: '2026-11-04T14:22:18Z',
            service_name: 'payment-service',
            severity: 'ERROR',
            relevant_excerpt: 'ERROR 2026-11-04 14:22:18 payment-service [stripe_client.py:145] ConnectionTimeoutError: HTTPSConnectionPool(host="api.stripe.com", port=443): Read timed out. (read timeout=5.0)',
            relevance_explanation: 'Direct evidence showing 5.0s read timeout triggered against api.stripe.com'
          }
        ],
        recommended_actions: [
          {
            priority: 1,
            action: 'Increase client timeout parameter to 30.0s and enable exponential backoff retry in stripe_client.py',
            category: 'Code Fix & Resilience',
            rationale: 'Absorbs p99 latency spikes up to 15s without prematurely aborting active credit card authorizations.',
            safety_warning: 'Ensure downstream gateway timeout in checkout-service is >= 35s to prevent orphaned transactions.'
          },
          {
            priority: 2,
            action: 'Implement circuit breaker pattern with fallback queue for delayed settlement',
            category: 'Architecture Resilience',
            rationale: 'Decouples synchronous user checkout from external gateway degradation.',
            safety_warning: 'Requires idempotency key support on webhook reconciliation.'
          }
        ],
        further_investigation: {
          missing_evidence: ['Stripe dashboard webhook response status logs'],
          recommended_checks: ['Verify DNS resolution latency to api.stripe.com from Kubernetes pod network']
        },
        evidence_sufficiency: {
          status: 'SUFFICIENT',
          reason: 'Complete stack trace with line numbers, commit diff correlation, and downstream impact confirmed.',
          confidence_score: 0.985
        },
        model_information: {
          model_name: 'gemini-3.5-flash-lite',
          provider: 'google-genai',
          latency_ms: 1840
        },
        retrieved_chunks_count: 8,
        created_at: new Date().toISOString(),
        workflow_status: 'SUCCESS',
        iterations_executed: 1,
        agent_execution_trace: [
          { agent_name: 'SupervisorAgent', stage: 'Planning', status: 'COMPLETED', timestamp: '14:22:19', summary: 'Orchestrated 6 specialist agents with DAG execution topology', latency_ms: 120 },
          { agent_name: 'LogEvidenceAgent', stage: 'Retrieval & Extraction', status: 'COMPLETED', timestamp: '14:22:20', summary: 'Retrieved 8 chunks via Dense+BM25+CrossEncoder reranking', latency_ms: 380 },
          { agent_name: 'HypothesisAgent', stage: 'Root Cause Generation', status: 'COMPLETED', timestamp: '14:22:21', summary: 'Synthesized 2 ranked hypotheses identifying socket timeout parameter', latency_ms: 450 },
          { agent_name: 'EvidenceValidatorAgent', stage: 'Anti-Hallucination Gate', status: 'COMPLETED', timestamp: '14:22:22', summary: 'Verified 100% citation grounding; zero hallucinations detected', latency_ms: 290 },
          { agent_name: 'RemediationAgent', stage: 'Action Planning', status: 'COMPLETED', timestamp: '14:22:23', summary: 'Generated 2 prioritized remediations with safety warnings', latency_ms: 340 },
          { agent_name: 'ReportSynthesizerAgent', stage: 'Report Synthesis', status: 'COMPLETED', timestamp: '14:22:24', summary: 'Compiled unified executive incident report with timeline', latency_ms: 260 }
        ]
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(jsonResponse),
      });
    });

    await page.getByRole('button', { name: /Execute Multi-Agent RCA/i }).click();
    await expect(page.getByText(/Critical payment pipeline degradation/i).first()).toBeVisible({ timeout: 15000 });
    
    // Switch to 7-Agent Trace tab
    const timelineTab = page.getByRole('button', { name: /Trace/i }).first();
    await expect(timelineTab).toBeVisible({ timeout: 5000 });
    await timelineTab.click();
    await page.waitForTimeout(800);
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '03_multi_agent_timeline.png'),
      fullPage: false,
    });
    console.log('Saved: 03_multi_agent_timeline.png');

    // ------------------------------------------------------------------------
    // 06. Service Dependency Graph
    // ------------------------------------------------------------------------
    await page.getByRole('button', { name: /Service Graph/i }).click();
    await expect(page.getByText('Service Dependency Graph & Blast Radius')).toBeVisible();
    await expect(page.locator('.react-flow')).toBeVisible();
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '06_service_dependency_graph.png'),
      fullPage: false,
    });
    console.log('Saved: 06_service_dependency_graph.png');

    // ------------------------------------------------------------------------
    // 07. Blast Radius Analysis
    // ------------------------------------------------------------------------
    // Click on payment-service node
    const paymentNode = page.locator('.react-flow__node').filter({ hasText: 'payment-service' }).first();
    if (await paymentNode.isVisible()) {
      await paymentNode.click();
      await page.waitForTimeout(500);
      const calcBtn = page.getByRole('button', { name: /Calculate Blast Radius/i });
      if (await calcBtn.isVisible()) {
        await calcBtn.click();
        await page.waitForTimeout(800);
      }
    }
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '07_blast_radius_analysis.png'),
      fullPage: false,
    });
    console.log('Saved: 07_blast_radius_analysis.png');

    // ------------------------------------------------------------------------
    // 08. GitHub Intelligence & Commit Diff Viewer
    // ------------------------------------------------------------------------
    await page.getByRole('button', { name: /GitHub Intelligence/i }).click();
    await expect(page.getByText('GitHub Repository & Commit Intelligence')).toBeVisible();
    
    // Register octocat repo to show commit history and diff
    const regBtn = page.getByRole('button', { name: /Register & Inspect Repository/i });
    if (await regBtn.isVisible()) {
      await regBtn.click();
      await page.waitForTimeout(3000);
    }
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '08_github_diff_viewer.png'),
      fullPage: false,
    });
    console.log('Saved: 08_github_diff_viewer.png');

    // ------------------------------------------------------------------------
    // 09. Evaluation Benchmarks
    // ------------------------------------------------------------------------
    await page.getByRole('button', { name: /Evaluation & Benchmarks/i }).click();
    await expect(page.getByText('Retrieval Paradigms (Dense vs BM25 vs Hybrid vs Reranker)')).toBeVisible();
    await page.waitForTimeout(1500); // allow recharts animations to complete
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '09_evaluation_benchmarks.png'),
      fullPage: false,
    });
    console.log('Saved: 09_evaluation_benchmarks.png');

    // ------------------------------------------------------------------------
    // 10. System Settings & Subsystem Health
    // ------------------------------------------------------------------------
    await page.getByRole('button', { name: /Settings/i }).click();
    await expect(page.getByText('System Settings & Health')).toBeVisible();
    await expect(page.getByText('FastAPI Engine')).toBeVisible();
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '10_system_settings_health.png'),
      fullPage: false,
    });
    console.log('Saved: 10_system_settings_health.png');
  });
});
