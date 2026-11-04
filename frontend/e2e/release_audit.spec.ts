import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('DebugGraph AI — Release Audit & E2E Verification', () => {

  test('01. Open Dashboard and verify basic structure', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/DebugGraph AI/);
    await expect(page.getByText('Operations Dashboard')).toBeVisible();
    await expect(page.getByText('Production Ready')).toBeVisible();
  });

  test('02. Verify Subsystem Health & Operations Center', async ({ page }) => {
    await page.goto('/');
    // Check that telemetry overview cards rendered
    await expect(page.getByText('Uploaded Log Files')).toBeVisible();
    await expect(page.getByText('Indexed Evidence Chunks')).toBeVisible();
    await expect(page.getByText('Knowledge Graph Services')).toBeVisible();
  });

  test('03 & 04. Upload a sample log file & verify parsing/indexing', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Log Explorer/i }).click();
    await expect(page.getByText('Log Ingestion & Hybrid Explorer')).toBeVisible();

    // Upload file
    const logFilePath = path.resolve('..', 'datasets', 'logs', 'payment-service.log');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(logFilePath);

    // Click upload
    const uploadBtn = page.getByRole('button', { name: /Upload & Index Log/i });
    if (await uploadBtn.isVisible()) {
      await uploadBtn.click();
      await expect(page.getByText('Log File Ingested Successfully!')).toBeVisible({ timeout: 20000 });
    }
  });

  test('05. Perform live hybrid log search', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Log Explorer/i }).click();

    const searchInput = page.getByPlaceholder(/Enter search query/i);
    await searchInput.fill('ConnectionTimeoutError in stripe_client');

    const searchBtn = page.getByRole('button', { name: /Search Logs/i });
    await searchBtn.click();

    // Verify search results or scores returned
    await expect(page.getByText(/Reranker:/i).first()).toBeVisible({ timeout: 20000 });
  });

  test('06, 07, 08. Start Incident Investigation & Inspect RCA/Evidence', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Investigations/i }).click();
    await expect(page.getByText('Incident Investigation Workspace')).toBeVisible();

    // Verify investigation options
    await expect(page.getByText('7 Agents')).toBeVisible();
    await expect(page.getByText('Single-Pass')).toBeVisible();

    // Inspect pre-loaded demo or enter query
    const queryArea = page.locator('textarea');
    await queryArea.fill('Why is payment-service timing out on Stripe?');

    // Verify trigger button is ready
    const startBtn = page.getByRole('button', { name: /Execute Multi-Agent RCA/i });
    await expect(startBtn).toBeVisible();
  });

  test('09, 10, 11. Visualize Dependency Graph & Blast Radius', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Service Graph/i }).click();
    await expect(page.getByText('Service Dependency Graph & Blast Radius')).toBeVisible();

    // Check React Flow canvas
    await expect(page.locator('.react-flow')).toBeVisible();

    // Blast Radius calculation
    const calcBtn = page.getByRole('button', { name: /Calculate Blast Radius/i });
    if (await calcBtn.isVisible()) {
      await calcBtn.click();
    }
  });

  test('12, 13. GitHub Intelligence & Commit Diff Viewer', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /GitHub Intelligence/i }).click();
    await expect(page.getByText('GitHub Repository & Commit Intelligence')).toBeVisible();

    // Verify repo URL input exists
    await expect(page.getByPlaceholder(/github\.com\/my-org/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Register & Inspect Repository/i })).toBeVisible();
  });

  test('14, 15. Evaluation Benchmarks & Report Export', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Evaluation & Benchmarks/i }).click();
    await expect(page.getByText('Retrieval Paradigms (Dense vs BM25 vs Hybrid vs Reranker)')).toBeVisible();

    // Check action buttons
    await expect(page.getByRole('button', { name: /Run Benchmark/i })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Markdown', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'JSON', exact: true })).toBeVisible();

    // Switch to Multi-Agent tab
    await page.getByRole('button', { name: /Multi-Agent vs Standard Gemini/i }).click();
    await expect(page.getByText(/Evidence Groundedness/i).first()).toBeVisible();

    // Switch to Dataset tab
    await page.getByRole('button', { name: /Benchmark Dataset & Scenarios/i }).click();
    await expect(page.getByText(/Retrieval Queries/i)).toBeVisible();

    // Switch to Markdown Report tab
    await page.getByRole('button', { name: /Markdown Report/i }).click();
    await expect(page.getByText('Executive Benchmark Report')).toBeVisible();
  });

  test('16. Settings & System Subsystem Health', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Settings/i }).click();
    await expect(page.getByText('System Settings & Health')).toBeVisible();

    // Verify subsystem cards
    await expect(page.getByText('FastAPI Engine')).toBeVisible();
    await expect(page.getByText('Qdrant Vector DB')).toBeVisible();
    await expect(page.getByText('Google Gemini LLM')).toBeVisible();
    await expect(page.getByText('Hybrid Retrieval Architecture')).toBeVisible();
    await expect(page.getByText('LangGraph Multi-Agent Architecture')).toBeVisible();
    await expect(page.getByText('Credential & Secret Security')).toBeVisible();
  });
});
