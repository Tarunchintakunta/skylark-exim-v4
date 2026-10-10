import { z } from 'zod'
import type { Category } from '../config/products'

// docs/TRD.md §12: client-only, composes a mailto. No backend, no fake success.
export const rfqSchema = z.object({
  name: z.string().trim().min(2, 'Please enter your name.'),
  company: z.string().trim().min(2, 'Please enter your company.'),
  country: z.string().trim().min(2, 'Please enter your country.'),
  email: z.string().trim().email('Please enter a valid email address.'),
  phone: z.string().trim().optional(),
  category: z.string().optional(),
  species: z.string().optional(),
  form: z.string().optional(),
  state: z.string().optional(),
  quantity: z.string().trim().optional(),
  destination: z.string().trim().optional(),
  message: z.string().trim().max(2000, 'Please keep the message under 2,000 characters.').optional(),
})
export type Rfq = z.infer<typeof rfqSchema>

const LABELS: [keyof Rfq, string][] = [
  ['name', 'Name'],
  ['company', 'Company'],
  ['country', 'Country'],
  ['email', 'Email'],
  ['phone', 'Phone'],
  ['category', 'Category'],
  ['species', 'Species'],
  ['form', 'Form'],
  ['state', 'State'],
  ['quantity', 'Quantity'],
  ['destination', 'Destination'],
]

export function buildMailto(r: Rfq, to = 'info@skylarkexim.com') {
  const subject = `RFQ — ${r.company} — ${r.species || r.category || 'Seafood'}`
  const head = LABELS.filter(([k]) => r[k])
    .map(([k, l]) => `${l}: ${r[k]}`)
    .join('\n')
  let body = `${head}\n\nMessage:\n${r.message ?? ''}`
  if (body.length > 1800) body = body.slice(0, 1799) + '…'
  return `mailto:${to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
}

/** "Enquire about this" in B2 calls this: query params carry the choice, nothing else is lost. */
export function prefillQuote(category: Category, species?: string) {
  const u = new URL(location.href)
  u.searchParams.set('category', category)
  if (species) u.searchParams.set('species', species)
  else u.searchParams.delete('species')
  u.hash = 'quote'
  history.replaceState(null, '', u)
  dispatchEvent(new Event('rfq-prefill'))
}
