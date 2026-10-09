import { useEffect, useRef } from 'react'
import { SplitText } from 'gsap/SplitText'
import { chapters } from '../config/chapters'
import { filmCopy, MINUS18, MINUS20 } from '../config/copy'
import { gsap, onTick } from '../engine/clock'
import { scrollStore } from '../engine/scrollStore'
import './captions.css'

gsap.registerPlugin(SplitText)

const IN = 0.08
const OUT = 0.88

/** Keeps "−18 °C" in a nowrap span (one SplitText word: its spaces are NBSP). */
function withTemps(text: string) {
  const parts = text.split(new RegExp(`(${MINUS18}|${MINUS20})`))
  return parts.map((p, i) =>
    p === MINUS18 || p === MINUS20 ? (
      <span key={i} className="nowrap">
        {p}
      </span>
    ) : (
      p
    ),
  )
}

/**
 * One caption visible at a time (QUALITY_GATES G-SITE-2): the outgoing caption finishes leaving before the
 * incoming one starts, and only elements with data-headline count as headlines.
 */
export default function Captions() {
  const root = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const blocks = [...root.current!.querySelectorAll<HTMLElement>('.cap')]
    const splits = blocks.map((b) => {
      const h = b.querySelector('[data-headline]')!
      return SplitText.create(h, { type: 'lines,words', mask: 'lines', autoSplit: true })
    })
    const numerals = [...root.current!.querySelectorAll<HTMLElement>('.countdown-num')]
    gsap.set(blocks, { autoAlpha: 0 })
    let shown = -1
    let busy = false
    let shownNum = ''
    const closing = blocks[blocks.length - 1].querySelector<HTMLElement>('.cap-closing')

    const show = (i: number) => {
      const b = blocks[i]
      const words = splits[i].words
      const rest = b.querySelectorAll('.cap-eyebrow, .cap-line, .cap-hint')
      gsap.set(b, { autoAlpha: 1 })
      gsap.fromTo(words, { yPercent: 110 }, { yPercent: 0, duration: 0.9, ease: 'power3.out', stagger: 0.03 })
      gsap.fromTo(
        rest,
        { autoAlpha: 0, y: 12 },
        { autoAlpha: 1, y: 0, duration: 0.8, ease: 'power3.out', delay: 0.2 },
      )
    }

    const roll = (num: string) => {
      if (num === shownNum) return
      const prev = numerals.find((n) => n.dataset.num === shownNum)
      const next = numerals.find((n) => n.dataset.num === num)
      const dir = scrollStore.direction
      if (prev) gsap.to(prev, { yPercent: -100 * dir, autoAlpha: 0, duration: 0.7, ease: 'power3.inOut' })
      if (next)
        gsap.fromTo(
          next,
          { yPercent: 100 * dir, autoAlpha: 0 },
          { yPercent: 0, autoAlpha: 1, duration: 0.7, ease: 'power3.inOut' },
        )
      shownNum = num
    }

    const off = onTick(() => {
      const { chapter, progress, inFilm } = scrollStore
      const first = chapter === 0
      const last = chapter === chapters.length - 1
      const active = inFilm && progress >= (first ? 0 : IN) && (last || progress < OUT)
      const target = active ? chapter : -1
      roll(inFilm ? (chapters[chapter].countdown ?? '') : '')
      const el = root.current!
      if (el.dataset.zone !== chapters[chapter].typeZone) el.dataset.zone = chapters[chapter].typeZone
      if (scrollStore.started && !el.classList.contains('started')) el.classList.add('started')
      if (closing) gsap.set(closing, { autoAlpha: last && progress >= 0.85 ? 1 : 0 })
      if (target === shown || busy) return
      if (shown === -1) {
        shown = target
        show(target)
        return
      }
      busy = true
      const leaving = blocks[shown]
      gsap.to(leaving, {
        autoAlpha: 0,
        duration: 0.3,
        ease: 'power2.in',
        onComplete: () => {
          shown = -1
          busy = false
        },
      })
    })
    return () => {
      off()
      splits.forEach((s) => s.revert())
    }
  }, [])

  const nums = [...new Set(chapters.map((c) => c.countdown).filter(Boolean))] as string[]

  return (
    <div ref={root} className="captions">
      {nums.map((n) => (
        <div key={n} className="countdown-num" data-num={n} aria-hidden="true">
          {n}
        </div>
      ))}
      {chapters.map((c, i) => {
        const copy = filmCopy[c.id]
        const H = i === 0 ? 'h1' : 'h2'
        return (
          <div key={c.id} className={`cap zone-${c.typeZone}`} data-chapter={c.id}>
            {copy.eyebrow && <p className="cap-eyebrow eyebrow">{copy.eyebrow}</p>}
            <H
              className={`cap-headline display${copy.headline.length > 18 ? ' is-long' : ''}`}
              data-headline=""
            >
              {withTemps(copy.headline)}
            </H>
            {copy.line && <p className="cap-line lede">{copy.line}</p>}
            {copy.closing && <p className="cap-closing h2">{copy.closing}</p>}
            {copy.hint && (
              <p className="cap-hint eyebrow" aria-hidden="true">
                <span className="cap-hint-line" />
                {copy.hint}
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}
