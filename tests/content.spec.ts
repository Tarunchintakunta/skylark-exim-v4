import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { ready, wheelThrough } from './helpers'

// docs/BANNED_CLAIMS.md "Banned strings": whole word/phrase, case-insensitive, on user-visible text only.
const doc = readFileSync('docs/BANNED_CLAIMS.md', 'utf8')
const line = doc.split('\n').find((l) => l.startsWith('Bay of Bengal'))!
const banned = line
  .split(' · ')
  .map((s) => s.replace(/\s*\(.*\)\s*$/, '').trim())
  .filter(Boolean)
const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
// \b only works next to word characters; phrases starting/ending with symbols use lookarounds instead.
const rx = (s: string) => new RegExp(`(?<![\\w])${esc(s)}(?![\\w])`, 'i')

test('no banned claims in visible text, alt, aria, title, meta or JSON-LD', async ({ page }) => {
  await ready(page)
  await wheelThrough(page, 900, 20)
  const text = await page.evaluate(() => {
    const attrs = [...document.querySelectorAll('[alt],[aria-label],[title]')].flatMap((e) =>
      ['alt', 'aria-label', 'title'].map((a) => e.getAttribute(a) ?? ''),
    )
    const metas = [...document.querySelectorAll('meta[content]')].map((m) => m.getAttribute('content'))
    const ld = [...document.querySelectorAll('script[type="application/ld+json"]')].map((s) => s.textContent)
    return [document.body.innerText, document.title, ...attrs, ...metas, ...ld].join('\n')
  })
  const hits = banned.filter((b) => rx(b).test(text) && !(b === 'capacity of' && /700 pallets/.test(text)))
  expect(hits, `banned phrases found: ${hits.join(', ')}`).toEqual([])
})

test('no placeholder or dashboard class names in the DOM (G-SITE-1)', async ({ page }) => {
  await ready(page)
  const bad = await page.evaluate(() => {
    const html = document.body.innerHTML
    const words = /placeholder|awaiting|coming soon|TODO/i.test(document.body.innerText)
    const attrs = document.querySelectorAll('[placeholder]').length
    const classes = [...document.querySelectorAll('[class]')]
      .map((e) => e.getAttribute('class')!)
      .filter((c) => /(^|[\s-])(hud|rail|pill|chip)($|[\s-])/.test(c))
    return { words, attrs, classes, len: html.length }
  })
  expect(bad.words).toBe(false)
  expect(bad.attrs).toBe(0)
  expect(bad.classes).toEqual([])
})
