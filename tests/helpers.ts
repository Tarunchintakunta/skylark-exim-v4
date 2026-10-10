import type { Page } from '@playwright/test'

export async function ready(page: Page) {
  await page.goto('/')
  await page.waitForSelector('.loader.is-done', { state: 'attached', timeout: 10_000 })
}

export async function jump(page: Page, y: number) {
  await page.evaluate((y) => window.__v4jump(y), y)
}

export async function scrollHeight(page: Page) {
  return page.evaluate(() => document.documentElement.scrollHeight - innerHeight)
}

/** Scroll the whole page with wheel steps so every chapter, caption and lazy section is visited. */
export async function wheelThrough(page: Page, step = 400, pause = 40) {
  const h = await scrollHeight(page)
  await page.mouse.move(200, 200)
  for (let y = 0; y < h; y += step) {
    await page.mouse.wheel(0, step)
    await page.waitForTimeout(pause)
  }
}

declare global {
  interface Window {
    __v4jump: (y: number) => void
  }
}

export async function scrollToSection(page: Page, sel: string) {
  const y = await page.evaluate((s) => {
    const el = document.querySelector(s)
    return el ? el.getBoundingClientRect().top + scrollY : 0
  }, sel)
  await page.mouse.wheel(0, 10)
  await jump(page, y)
  await page.waitForTimeout(900)
}
