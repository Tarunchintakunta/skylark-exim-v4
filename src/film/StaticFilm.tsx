import { chapters } from '../config/chapters'
import { filmCopy } from '../config/copy'
import { posterUrl } from '../config/media'
import type { Tier } from '../engine/env'

/** prefers-reduced-motion: posters as still images with their captions; no scrubbing, no smooth scroll, no SplitText. */
export default function StaticFilm({ tier }: { tier: Tier }) {
  return (
    <section id="story" className="static-film">
      {chapters.map((c, i) => {
        const copy = filmCopy[c.id]
        const H = i === 0 ? 'h1' : 'h2'
        return (
          <article key={c.id} className="static-chapter">
            <img
              src={posterUrl(c.id, tier)}
              alt={c.alt}
              width={1920}
              height={1080}
              loading={i === 0 ? 'eager' : 'lazy'}
              decoding="async"
              style={{ objectPosition: c.objectPosition }}
            />
            <div className="static-cap">
              {c.countdown && (
                <p className="static-num" aria-hidden="true">
                  {c.countdown}
                </p>
              )}
              {copy.eyebrow && <p className="eyebrow">{copy.eyebrow}</p>}
              <H className="display static-headline" data-headline="">
                {copy.headline}
              </H>
              {copy.line && <p className="lede">{copy.line}</p>}
              {copy.closing && <p className="h2">{copy.closing}</p>}
            </div>
          </article>
        )
      })}
    </section>
  )
}
