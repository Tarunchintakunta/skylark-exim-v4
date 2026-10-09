import { useEffect, useRef, useState } from 'react'
import { categories, shrimpForms, states, type Category } from '../config/products'
import { contact } from '../config/site'
import { buildMailto, rfqSchema } from './rfq'

const FIELDS = ['name', 'company', 'country', 'email', 'phone', 'quantity', 'destination'] as const
const LABEL: Record<(typeof FIELDS)[number], string> = {
  name: 'Name',
  company: 'Company',
  country: 'Country',
  email: 'Email',
  phone: 'Phone',
  quantity: 'Quantity',
  destination: 'Destination',
}
const REQUIRED = new Set(['name', 'company', 'country', 'email'])

/** B6 · Request a quote — composes a mailto (docs/TRD.md §12). */
export default function Quote() {
  const [category, setCategory] = useState<Category | ''>('')
  const [species, setSpecies] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [sent, setSent] = useState(false)
  const form = useRef<HTMLFormElement>(null)

  useEffect(() => {
    const read = () => {
      const q = new URLSearchParams(location.search)
      const c = q.get('category') as Category | null
      if (c && c in categories) {
        setCategory(c)
        const s = q.get('species')
        setSpecies(s && (categories[c] as readonly string[]).includes(s) ? s : '')
      }
    }
    read()
    addEventListener('rfq-prefill', read)
    return () => removeEventListener('rfq-prefill', read)
  }, [])

  const submit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const data = Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>
    if (data.website) return // honeypot
    const r = rfqSchema.safeParse(data)
    if (!r.success) {
      const errs: Record<string, string> = {}
      for (const i of r.error.issues) errs[String(i.path[0])] ??= i.message
      setErrors(errs)
      setSent(false)
      form.current?.querySelector<HTMLElement>(`[name="${Object.keys(errs)[0]}"]`)?.focus()
      return
    }
    setErrors({})
    setSent(true)
    window.location.href = buildMailto(r.data)
  }

  const err = (k: string) =>
    errors[k] ? (
      <span id={`${k}-err`} className="field-err">
        {errors[k]}
      </span>
    ) : null
  const aria = (k: string) => ({
    'aria-invalid': !!errors[k],
    'aria-describedby': errors[k] ? `${k}-err` : undefined,
  })

  return (
    <section id="quote" className="sec sec-light on-light quote" aria-labelledby="quote-title">
      <div className="sec-inner quote-grid">
        <div>
          <p className="eyebrow">Request a quote</p>
          <h2 id="quote-title" className="h2 sec-title">
            Tell us what you need.
          </h2>
          <form ref={form} className="rfq" noValidate onSubmit={submit}>
            <div className="rfq-row">
              {FIELDS.slice(0, 4).map((k) => (
                <label key={k} className="field">
                  <span>
                    {LABEL[k]}
                    {REQUIRED.has(k) && <span aria-hidden="true"> *</span>}
                  </span>
                  <input
                    name={k}
                    type={k === 'email' ? 'email' : 'text'}
                    autoComplete={
                      k === 'name'
                        ? 'name'
                        : k === 'company'
                          ? 'organization'
                          : k === 'country'
                            ? 'country-name'
                            : 'email'
                    }
                    required={REQUIRED.has(k)}
                    {...aria(k)}
                  />
                  {err(k)}
                </label>
              ))}
              <label className="field">
                <span>Phone</span>
                <input name="phone" type="tel" autoComplete="tel" />
              </label>
              <label className="field">
                <span>Category</span>
                <select
                  name="category"
                  value={category}
                  onChange={(e) => {
                    setCategory(e.target.value as Category)
                    setSpecies('')
                  }}
                >
                  <option value="">Choose…</option>
                  {Object.keys(categories).map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Species</span>
                <select
                  name="species"
                  value={species}
                  onChange={(e) => setSpecies(e.target.value)}
                  disabled={!category}
                >
                  <option value="">{category ? 'Choose…' : 'Choose a category first'}</option>
                  {category && categories[category].map((s) => <option key={s}>{s}</option>)}
                </select>
              </label>
              {category === 'Shrimps' && (
                <label className="field">
                  <span>Form</span>
                  <select name="form" defaultValue="">
                    <option value="">Choose…</option>
                    {shrimpForms.map((f) => (
                      <option key={f.form}>{f.form}</option>
                    ))}
                  </select>
                </label>
              )}
              <label className="field">
                <span>State</span>
                <select name="state" defaultValue="">
                  <option value="">Choose…</option>
                  {states.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </label>
              {FIELDS.slice(5).map((k) => (
                <label key={k} className="field">
                  <span>{LABEL[k]}</span>
                  <input name={k} type="text" />
                </label>
              ))}
            </div>
            <label className="field field-wide">
              <span>Message</span>
              <textarea name="message" rows={5} maxLength={2000} {...aria('message')} />
              {err('message')}
            </label>
            <label className="hp" aria-hidden="true">
              Website
              <input name="website" type="text" tabIndex={-1} autoComplete="off" />
            </label>
            <button type="submit" className="btn-quote rfq-submit">
              Compose email
            </button>
            <p className="rfq-note" role="status">
              {sent && (
                <>
                  Your email app has opened with the request. If it didn’t, write to{' '}
                  <a href={`mailto:${contact.email}`}>{contact.email}</a>.
                </>
              )}
            </p>
          </form>
        </div>
        <address className="contact">
          <h3 className="eyebrow">Contact</h3>
          <ul>
            {contact.phones.map((p) => (
              <li key={p.href}>
                <a className="tnum" href={p.href}>
                  {p.label}
                </a>
              </li>
            ))}
            <li>
              <a href={`mailto:${contact.email}`}>{contact.email}</a>
            </li>
          </ul>
          <h3 className="eyebrow">Office</h3>
          <p>{contact.office}</p>
          <h3 className="eyebrow">Processing unit</h3>
          <p>{contact.plant}</p>
          <a className="profile-link" href={contact.profile} download>
            Download company profile (PDF)
          </a>
        </address>
      </div>
    </section>
  )
}
