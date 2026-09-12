import { defineConfig } from '@playwright/test';
import path from 'node:path';

const python = process.env.PYTHON_BIN || (
  process.platform === 'win32' ? '../.venv/Scripts/python.exe' : '../.venv/bin/python'
);

export default defineConfig({
  testDir: './tests',
  timeout: 60000,
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:8011',
    browserName: 'chromium',
    channel: process.env.PLAYWRIGHT_CHANNEL || (process.platform === 'win32' ? 'msedge' : undefined),
    headless: true,
    viewport: { width: 1440, height: 1000 },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: '"' + python + '" ../backend/tests/e2e_server.py',
    url: 'http://127.0.0.1:8011/api/health',
    reuseExistingServer: false,
    timeout: 30000,
    env: { SODA_DATABASE: path.resolve('../data/e2e/browser-test-' + Date.now() + '.sqlite3') },
  },
});

