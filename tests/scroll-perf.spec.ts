import { test, expect } from '@playwright/test'
import { ready, wheelThrough } from './helpers'

// G-SITE-5. Meaningful on the DEPLOYED preview: PERF_URL=<url> npx playwright test tests/scroll-perf.spec.ts
test('scripted full scroll: long tasks, rAF p95, stalls', async ({ page, browserName }, info) => {
  test.skip(browserName !== 'chromium')
  const mobile = info.project.name === 'mobile'
  const cdp = await page.context().newCDPSession(page)
  if (mobile) {
    await cdp.send('Network.enable')
    await cdp.send('Network.emulateNetworkConditions', {
      offline: false,
      latency: 170,
      downloadThroughput: (9 * 1024 * 1024) / 8,
      uploadThroughput: (1.5 * 1024 * 1024) / 8,
    })
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 })
  }
  await ready(page)
  // G-SITE-5 counts long tasks during the scroll AFTER load: wait for an idle period, then only count tasks that start
  // after it (an observer created mid-frame otherwise also receives the last load frame).
  await page.evaluate(() => new Promise((r) => requestIdleCallback(() => r(null), { timeout: 2000 })))
  await page.evaluate(() => {
    const w = window as unknown as { __perf: { long: number[]; frames: number[] } }
    w.__perf = { long: [], frames: [] }
    const t0 = performance.now()
    new PerformanceObserver((l) =>
      l.getEntries().forEach((e) => e.startTime >= t0 && w.__perf.long.push(e.duration)),
    ).observe({
      type: 'longtask',
      buffered: false,
    })
    let last = performance.now()
    const f = (t: number) => {
      w.__perf.frames.push(t - last)
      last = t
      requestAnimationFrame(f)
    }
    requestAnimationFrame(f)
  })
  await wheelThrough(page, mobile ? 220 : 160, mobile ? 60 : 30)
  const r = await page.evaluate(() => {
    const w = window as unknown as { __perf: { long: number[]; frames: number[] }; __v4: { stalls: number } }
    const fr = [...w.__perf.frames].sort((a, b) => a - b)
    return {
      long: w.__perf.long.filter((d) => d > 50).length,
      p95: fr[Math.floor(fr.length * 0.95)],
      stalls: w.__v4?.stalls ?? 0,
    }
  })
  console.log(info.project.name, JSON.stringify(r))
  if (mobile) expect(r.stalls).toBeLessThanOrEqual(2)
  else {
    expect(r.long).toBe(0)
    expect(r.p95).toBeLessThanOrEqual(20)
    expect(r.stalls).toBe(0)
  }
})
