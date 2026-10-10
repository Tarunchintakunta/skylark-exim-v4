import { test, expect } from '@playwright/test'
import { buildMailto, rfqSchema } from '../src/sections/rfq'

test('mailto has subject + every filled field and caps the body', () => {
  const r = rfqSchema.parse({
    name: 'Ann Lee',
    company: 'Blue Co',
    country: 'Japan',
    email: 'ann@blue.example',
    category: 'Shrimps',
    species: 'Vannamei',
    message: 'x'.repeat(2000),
  })
  const m = buildMailto(r)
  expect(m.startsWith('mailto:info@skylarkexim.com?subject=')).toBe(true)
  const u = new URL(m)
  expect(u.searchParams.get('subject')).toBe('RFQ — Blue Co — Vannamei')
  const body = u.searchParams.get('body')!
  expect(body).toContain('Country: Japan')
  expect(body.length).toBeLessThanOrEqual(1800)
  expect(body.endsWith('…')).toBe(true)
})

test('schema rejects a bad email', () => {
  expect(rfqSchema.safeParse({ name: 'Al', company: 'Co', country: 'UAE', email: 'nope' }).success).toBe(false)
})
