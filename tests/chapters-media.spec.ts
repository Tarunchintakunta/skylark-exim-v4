import { test, expect, type Page } from '@playwright/test'
import { jump, ready } from './helpers'

// G-SITE-4: every film chapter shows real media at 10/50/90 %, scrolling DOWN and then back UP. Fails on a blank,
// black or white frame (mean luma < 30 or > 245, or stddev < 12).
async function lumaStats(page: Page) {
  const png = await page.screenshot({ scale: 'css' })
  return page.evaluate(async (b64) => {
    const img = new Image()
    img.src = 'data:image/png;base64,' + b64
    await img.decode()
    const c = new OffscreenCanvas(160, 90)
    const x = c.getContext('2d')!
    x.drawImage(img, 0, 0, 160, 90)
    const d = x.getImageData(0, 0, 160, 90).data
    let s = 0
    let s2 = 0
    const n = d.length / 4
    for (let i = 0; i < d.length; i += 4) {
      const y = 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2]
      s += y
      s2 += y * y
    }
    const mean = s / n
    return { mean, sd: Math.sqrt(s2 / n - mean * mean) }
  }, png.toString('base64'))
}

test('every chapter shows real media down and up', async ({ page }) => {
  await ready(page)
  await page.mouse.wheel(0, 10)
  const marks = await page.evaluate(() => {
    const film = document.getElementById('story')!
    const top = film.getBoundingClientRect().top + scrollY
    const vh = innerHeight / 100
    const mobile = matchMedia('(max-width: 767px)').matches
    const lens = [...document.querySelectorAll('.cap')].map((c) => c.getAttribute('data-chapter'))
    return { top, vh, mobile, n: lens.length }
  })
  const { chapters } = await import('../src/config/chapters')
  const lengths = chapters.map((c) => (marks.mobile ? (c.mobileVh ?? c.vh * 0.8) : c.vh))
  const positions: { y: number; label: string }[] = []
  let acc = 0
  lengths.forEach((l, i) => {
    for (const p of [0.1, 0.5, 0.9])
      positions.push({ y: marks.top + (acc + l * p) * marks.vh, label: `${chapters[i].id}@${p * 100}%` })
    acc += l
  })
  const failures: string[] = []
  for (const pass of [positions, [...positions].reverse()]) {
    for (const p of pass) {
      await jump(page, p.y)
      await page.waitForTimeout(700)
      const s = await lumaStats(page)
      if (s.mean < 30 || s.mean > 245 || s.sd < 12) failures.push(`${p.label} mean ${s.mean.toFixed(0)} sd ${s.sd.toFixed(0)}`)
    }
  }
  expect(failures).toEqual([])
})
