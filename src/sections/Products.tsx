import { useEffect, useRef } from 'react'
import { marineFish, shrimpForms, shrimps, states, type Category } from '../config/products'
import { onTick, scrollToEl } from '../engine/clock'
import { reducedMotion } from '../engine/env'
import { onScreen, stickyProgress } from '../engine/progress'
import { stage3d, type ModelId } from '../three/store'
import { prefillQuote } from './rfq'

interface Stage {
  model: ModelId
  word: string
  category: Category
  eyebrow: string
  species?: string
}

// Swordfish is only staged if public/models/swordfish.glb passed G-PROD (see PR); otherwise it stays a list entry.
const productStages: Stage[] = [
  { model: 'tuna', word: 'Tuna', category: 'Marine fish', eyebrow: 'Marine fish', species: 'Tuna' },
  { model: 'prawn', word: 'Shrimps', category: 'Shrimps', eyebrow: 'Shrimps' },
]

function enquire(category: Category, species?: string) {
  prefillQuote(category, species)
  scrollToEl(document.getElementById('quote'))
}

/** B2 · Products — live model in front of a giant outlined name (Zoi layering), full lists from CONTENT §6. */
export default function Products() {
  const ref = useRef<HTMLElement>(null)
  useEffect(() => {
    if (reducedMotion) return
    const blocks = [...ref.current!.querySelectorAll<HTMLElement>('.prod-stage')]
    const off = onTick(() => {
      const i = blocks.findIndex(onScreen)
      if (i < 0) {
        if (stage3d.model && stage3d.model !== 'carton') stage3d.visible = 0
        return
      }
      // When two blocks overlap the viewport, the one covering more of it wins.
      let best = i
      if (
        blocks[i + 1] &&
        onScreen(blocks[i + 1]) &&
        blocks[i + 1].getBoundingClientRect().top < innerHeight / 2
      )
        best = i + 1
      const p = stickyProgress(blocks[best])
      stage3d.model = productStages[best].model
      stage3d.progress = p
      stage3d.visible = Math.min(1, p * 8 + 0.15, (1 - p) * 8)
    })
    return off
  }, [])

  return (
    <section ref={ref} id="products" className="sec-dark products" aria-labelledby="products-title">
      <div className="sec-inner prod-intro">
        <p className="eyebrow">Products</p>
        <h2 id="products-title" className="h2 sec-title">
          Raw fresh · chilled · frozen
        </h2>
      </div>
      {productStages.map((s) => (
        <div key={s.model} className="prod-stage">
          <div className="prod-sticky">
            <p className="prod-word" aria-hidden="true">
              {s.word}
            </p>
            <div className="prod-meta">
              <p className="eyebrow">{s.eyebrow}</p>
              <h3 className="h2">{s.word}</h3>
              <button type="button" className="prod-enquire" onClick={() => enquire(s.category, s.species)}>
                Enquire about this
              </button>
            </div>
          </div>
        </div>
      ))}
      <div className="sec-inner prod-lists">
        <div>
          <h3 className="eyebrow">Marine fish</h3>
          <ul className="prod-list">
            {marineFish.map((f) => (
              <li key={f}>
                <span>{f}</span>
                <button
                  type="button"
                  onClick={() => enquire('Marine fish', f)}
                  aria-label={`Enquire about ${f}`}
                >
                  Enquire
                </button>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="eyebrow">Shrimps</h3>
          <ul className="prod-list">
            {shrimps.map((f) => (
              <li key={f}>
                <span>{f}</span>
                <button type="button" onClick={() => enquire('Shrimps', f)} aria-label={`Enquire about ${f}`}>
                  Enquire
                </button>
              </li>
            ))}
          </ul>
          <p className="prod-species">
            Species offered: <i>Litopenaeus vannamei</i> (Vannamei) &amp; <i>Penaeus monodon</i> (Black tiger)
          </p>
          <table className="prod-forms">
            <caption className="eyebrow">Shrimp forms</caption>
            <thead>
              <tr>
                <th scope="col">Form</th>
                <th scope="col">Options</th>
              </tr>
            </thead>
            <tbody>
              {shrimpForms.map((f) => (
                <tr key={f.form}>
                  <th scope="row">{f.form}</th>
                  <td>{f.options}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="prod-states">{states.join(' · ')}</p>
        </div>
      </div>
    </section>
  )
}
