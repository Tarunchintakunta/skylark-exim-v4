import { test, expect } from '@playwright/test'
import { jump, ready, scrollHeight } from './helpers'

// G-SITE-2: at every 2 % of scroll at most one [data-headline] is visible, and none overflows the viewport.
for (const width of [360, 390, 768, 1280, 1440, 1920]) {
  test(`one headline at a time @${width}`, async ({ page }, info) => {
    test.skip(info.project.name !== 'desktop', 'widths are set explicitly')
    await page.setViewportSize({ width, height: width < 768 ? 800 : 900 })
    await ready(page)
    await page.mouse.wheel(0, 10)
    const h = await scrollHeight(page)
    for (let i = 0; i <= 50; i++) {
      await jump(page, (h * i) / 50)
      await page.waitForTimeout(450)
      const r = await page.evaluate(() => {
        const vis = [...document.querySelectorAll<HTMLElement>('[data-headline]')].filter((el) => {
          let e: HTMLElement | null = el
          while (e) {
            const s = getComputedStyle(e)
            if (+s.opacity <= 0.05 || s.visibility === 'hidden' || s.display === 'none') return false
            e = e.parentElement
          }
          const b = el.getBoundingClientRect()
          return b.bottom > 0 && b.top < innerHeight
        })
        const over = vis.filter((el) => {
          const b = el.getBoundingClientRect()
          return b.right > innerWidth + 1 || b.left < -1
        })
        return { n: vis.length, over: over.length }
      })
      expect(r.n, `${r.n} headlines visible at ${i * 2}%`).toBeLessThanOrEqual(1)
      expect(r.over, `headline overflows at ${i * 2}%`).toBe(0)
    }
  })
}
