import { test, expect } from '@playwright/test'
import { ready } from './helpers'

test('loads with one h1 and the first poster only', async ({ page }) => {
  const media: string[] = []
  page.on('request', (r) => {
    if (/\/media\/.+\.mp4/.test(r.url())) media.push(r.url())
  })
  await ready(page)
  await expect(page.locator('h1')).toHaveCount(1)
  await expect(page.locator('h1')).toHaveText('Trace it back.')
  await page.waitForTimeout(800)
  expect(media, 'no clip before the first scroll (G-SITE-6)').toEqual([])
})

test('menu opens, closes with Escape and links land', async ({ page }, info) => {
  await ready(page)
  await page.getByRole('button', { name: /open menu/i }).click()
  await expect(page.locator('#site-menu')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.locator('#site-menu')).toBeHidden()
  test.skip(info.project.name === 'mobile', 'desktop header button')
  await page.locator('.site-header .btn-quote').click()
  await page.waitForTimeout(1800)
  const top = await page.evaluate(() => document.getElementById('quote')?.getBoundingClientRect().top ?? 9999)
  expect(Math.abs(top)).toBeLessThan(200)
})
