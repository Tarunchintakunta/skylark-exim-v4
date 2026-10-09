import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { ready, scrollToSection } from './helpers'

const serious = (v: { impact?: string | null }[]) => v.filter((x) => x.impact === 'serious' || x.impact === 'critical')

for (const where of ['load', '#products', '#quote']) {
  test(`axe: no serious/critical violations at ${where}`, async ({ page }) => {
    await ready(page)
    if (where !== 'load') await scrollToSection(page, where)
    const r = await new AxeBuilder({ page }).analyze()
    expect(serious(r.violations).map((v) => `${v.id}: ${v.help}`)).toEqual([])
  })
}

test('reduced motion: no video, captions readable', async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: 'reduce' })
  const page = await ctx.newPage()
  await page.goto('/')
  expect(await page.locator('video').count()).toBe(0)
  await expect(page.locator('h1')).toHaveText('Trace it back.')
  const r = await new AxeBuilder({ page }).analyze()
  expect(serious(r.violations).map((v) => v.id)).toEqual([])
  await ctx.close()
})
