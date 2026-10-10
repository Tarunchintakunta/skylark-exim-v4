import { useEffect, useRef } from 'react'
import { endPosterUrl, posterUrl } from '../config/media'
import { quality, steps } from '../config/site'
import { gsap } from '../engine/clock'
import { reducedMotion } from '../engine/env'

/** B3 · Quality & facility — stills from the film with a slow transform-only parallax. */
export default function Quality() {
  const ref = useRef<HTMLElement>(null)
  useEffect(() => {
    if (reducedMotion) return
    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>('.quality-stills img').forEach((img, i) => {
        gsap.fromTo(
          img,
          { yPercent: -8 },
          {
            yPercent: i ? -2 : 0,
            ease: 'none',
            scrollTrigger: { trigger: img.parentElement, start: 'top bottom', end: 'bottom top', scrub: 0.6 },
          },
        )
      })
    }, ref)
    return () => ctx.revert()
  }, [])
  return (
    <section ref={ref} id="quality" className="sec sec-field" aria-labelledby="quality-title">
      <div className="sec-inner">
        <p className="eyebrow">Quality &amp; facility</p>
        <h2 id="quality-title" className="h2 sec-title">
          High professionalism and excellence.
        </h2>
        <div className="quality-stills">
          <figure>
            <img
              src={endPosterUrl('v-qc', 1280)}
              alt="A lab technician checks shrimp samples at the quality-control bench."
              width={1280}
              height={720}
              loading="lazy"
              decoding="async"
            />
          </figure>
          <figure>
            <img
              src={posterUrl('v-cold', 1280)}
              alt="Frosted pallet racks in the cold store at Anandapuram."
              width={1280}
              height={720}
              loading="lazy"
              decoding="async"
            />
          </figure>
        </div>
        <ul className="quality-list">
          {quality.map((q) => (
            <li key={q.title}>
              <h3>{q.title}</h3>
              <p>{q.line}</p>
            </li>
          ))}
        </ul>
        <h3 id="workflow" className="h2">
          Our work flow
        </h3>
        <ol className="flow">
          {steps.map((s) => (
            <li key={s.n}>
              <span className="flow-n" aria-hidden="true">
                {s.n}
              </span>
              <div>
                <h3>{s.title}</h3>
                <p>{s.line}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}
