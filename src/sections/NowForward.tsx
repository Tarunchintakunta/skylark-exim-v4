import { useEffect, useRef } from 'react'
import { company, steps } from '../config/site'
import { onTick, scrollToEl } from '../engine/clock'
import { isMobile, reducedMotion } from '../engine/env'
import { onScreen, stickyProgress } from '../engine/progress'
import { stage3d } from '../three/store'

/** B1 · Now, forward — the live carton turns and opens while the 9 steps read forwards behind it. */
export default function NowForward() {
  const ref = useRef<HTMLElement>(null)
  useEffect(() => {
    const el = ref.current!
    const lines = [...el.querySelectorAll<HTMLElement>('.nf-step')]
    const copy = el.querySelector<HTMLElement>('.nf-copy')!
    if (reducedMotion) return
    let was = false
    const off = onTick(() => {
      const on = onScreen(el)
      if (!on) {
        if (was && stage3d.model === 'carton') stage3d.visible = 0
        was = false
        return
      }
      was = true
      const p = stickyProgress(el)
      // Only once pinned, so the film's last caption and this headline are never on screen together.
      copy.classList.toggle('is-on', p > 0.01 && p < 0.99)
      stage3d.model = 'carton'
      stage3d.progress = p
      stage3d.visible = Math.min(1, p * 12, (1 - p) * 12 + 0.0001)
      if (isMobile) return
      // One step at a time crosses the screen behind the carton.
      const seg = p * steps.length
      lines.forEach((l, i) => {
        const t = seg - i
        const x = t < 0 || t > 1 ? (t < 0 ? 110 : -110) : 110 - t * 220
        l.style.transform = `translate3d(${x}vw,0,0)`
      })
    })
    return off
  }, [])
  return (
    <section ref={ref} id="now-forward" className="sec-light on-light nf" aria-labelledby="nf-title">
      <div className="nf-stage">
        <ol className="nf-steps" aria-label="Our work flow, forwards">
          {steps.map((s) => (
            <li key={s.n} className="nf-step display">
              <span className="nf-n">{s.n}</span> {s.short}
            </li>
          ))}
        </ol>
        <div className="nf-copy">
          <h2 id="nf-title" className="display nf-title" data-headline="">
            Now, forward.
          </h2>
          <p className="lede">{company.c1Short}</p>
          <a
            href="#workflow"
            className="nf-link"
            onClick={(e) => {
              e.preventDefault()
              scrollToEl(document.getElementById('workflow'))
            }}
          >
            Read our full work flow
          </a>
        </div>
      </div>
    </section>
  )
}
