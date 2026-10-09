import { useEffect, useRef } from 'react'
import { arcPath, MAP, project } from '../config/map'
import { markets, origin } from '../config/markets'
import { company } from '../config/site'
import { gsap } from '../engine/clock'
import { reducedMotion } from '../engine/env'

const [ox, oy] = project(origin.lat, origin.lon)

/** B4 · Markets — Blender relief map; 16 marigold great-circle routes draw on with scroll. */
export default function Markets() {
  const ref = useRef<HTMLElement>(null)
  useEffect(() => {
    const root = ref.current!
    const paths = [...root.querySelectorAll<SVGPathElement>('.route')]
    const items = [...root.querySelectorAll<HTMLElement>('.market')]
    const lens = paths.map((p) => p.getTotalLength())
    paths.forEach((p, i) => {
      p.style.strokeDasharray = `${lens[i]}`
      p.style.strokeDashoffset = reducedMotion ? '0' : `${lens[i]}`
    })
    if (reducedMotion) {
      items.forEach((i) => i.classList.add('is-on'))
      return
    }
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: { trigger: root, start: 'top top', end: '+=200%', pin: '.markets-stage', scrub: 0.6 },
      })
      paths.forEach((p, i) => {
        tl.to(p, { strokeDashoffset: 0, duration: 1, ease: 'none' }, i * 0.6)
      })
      tl.eventCallback('onUpdate', () => {
        const t = tl.time()
        items.forEach((el, i) => el.classList.toggle('is-on', t >= i * 0.6 + 0.5))
      })
    }, root)
    return () => ctx.revert()
  }, [])

  return (
    <section ref={ref} id="markets" className="sec-dark markets" aria-labelledby="markets-title">
      <div className="markets-stage">
        <div className="markets-copy">
          <p className="eyebrow">Markets</p>
          <h2 id="markets-title" className="h2 sec-title">
            {company.c7}
          </h2>
          <p className="markets-lede">Our market places, as listed by Skylark Exim.</p>
          <p className="markets-count">
            <span className="markets-count-n">16</span> markets
          </p>
          <ol className="market-list">
            {markets.map((m) => (
              <li key={m.name} className="market">
                {m.name}
              </li>
            ))}
          </ol>
        </div>
        <figure className="markets-map">
          <picture>
            <source media="(max-width: 767px)" srcSet="/media/markets-map_960.webp" />
            <img
              src="/media/markets-map_1920.webp"
              alt="Relief map from Europe to Japan with routes from Visakhapatnam to Skylark Exim's 16 market places."
              width={MAP.W}
              height={MAP.H}
              loading="lazy"
              decoding="async"
            />
          </picture>
          <svg viewBox={`0 0 ${MAP.W} ${MAP.H}`} aria-hidden="true" preserveAspectRatio="xMidYMid meet">
            {markets.map((m) => (
              <path key={m.name} className="route" d={arcPath(origin, m)} />
            ))}
            {markets.map((m) => {
              const [x, y] = project(m.lat, m.lon)
              return <circle key={m.name} className="route-end" cx={x} cy={y} r={4} />
            })}
            <circle className="origin" cx={ox} cy={oy} r={7} />
          </svg>
        </figure>
      </div>
    </section>
  )
}
