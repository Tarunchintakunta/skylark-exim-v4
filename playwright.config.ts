import { defineConfig, devices } from '@playwright/test'

// PERF_URL=<deployed preview> runs the suites against Vercel instead of the local build.
const remote = process.env.PERF_URL
export default defineConfig({
  testDir: 'tests',
  timeout: 180_000,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: { baseURL: remote || 'http://localhost:5791' },
  webServer: remote
    ? undefined
    : { command: 'npx vite preview --port 5791 --strictPort', port: 5791, reuseExistingServer: true },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', use: { ...devices['Pixel 7'], viewport: { width: 390, height: 844 } } },
  ],
})
