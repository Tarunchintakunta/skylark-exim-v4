import { test, expect } from '@playwright/test'
import { ready, wheelThrough } from './helpers'

// G-SITE-6 / TRD §9: transferred bytes before the first scroll and for a whole scroll.
test('initial and full-scroll transfer within budget', async ({ page }, info) => {
  const mobile = info.project.name === 'mobile'
  const cdp = await page.context().newCDPSession(page)
  await cdp.send('Network.enable')
  let bytes = 0
  cdp.on('Network.loadingFinished', (e) => (bytes += e.encodedDataLength))
  await ready(page)
  await page.waitForTimeout(1500)
  const initial = bytes
  await wheelThrough(page, 500, 60)
  await page.waitForTimeout(1500)
  const mb = (b: number) => +(b / 1048576).toFixed(2)
  console.log(info.project.name, 'initial MB', mb(initial), 'full scroll MB', mb(bytes))
  expect(mb(initial)).toBeLessThanOrEqual(mobile ? 1.5 : 3)
  expect(mb(bytes)).toBeLessThanOrEqual(mobile ? 14 : 32)
})
