import { useEffect, useRef } from 'react'
import { chapters } from '../config/chapters'
import { mixColors, palette, sectionsField, type ChapterColors } from '../config/palette'
import { onTick } from '../engine/clock'
import { reducedMotion } from '../engine/env'
import { scrollStore } from '../engine/scrollStore'
import './chroma.css'

const ease = (t: number) => t * t * (3 - 2 * t)

/**
 * Zoi-style colour field (docs/COLOR_SCRIPT.md §4): a fixed gradient with two soft glows behind everything, blended
 * between chapter colours on scroll and settling into navy over the business sections. Only CSS custom properties and
 * transforms change per tick, and only when a value actually changes, so it costs no layout.
 */
export default function Chroma() {
  const root = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const doc = document.documentElement.style
    const g1 = root.current!.querySelector<HTMLElement>('.chroma-glow-1')!
    const g2 = root.current!.querySelector<HTMLElement>('.chroma-glow-2')!
    let last = ''
    const set = (c: ChapterColors) => {
      const key = c.a + c.b + c.accent + c.glow
      if (key === last) return
      last = key
      doc.setProperty('--ch-bg-a', c.a)
      doc.setProperty('--ch-bg-b', c.b)
      doc.setProperty('--ch-accent', c.accent)
      doc.setProperty('--ch-glow', c.glow)
    }
    let story: HTMLElement | null = null
    let lastY = -1
    return onTick(() => {
      story ??= document.getElementById('story')
      const { chapter, progress, inFilm } = scrollStore
      const id = chapters[chapter].id
      const next = chapters[chapter + 1]?.id
      let c = palette[id]
      if (inFilm && next && progress > 0.75) c = mixColors(c, palette[next], ease((progress - 0.75) / 0.25))
      if (!inFilm && story) {
        // After the film: the last chapter's dawn melts into the sections' navy over one viewport.
        const past = (scrollY + innerHeight - story.offsetTop - story.offsetHeight) / innerHeight
        if (past > 0)
          c = mixColors(palette[chapters[chapters.length - 1].id], sectionsField, ease(Math.min(past, 1)))
      }
      set(c)
      // Parallax: the glows drift at different rates (transform only, GPU).
      if (!reducedMotion && scrollY !== lastY) {
        lastY = scrollY
        const y = scrollY
        g1.style.transform = `translate3d(${Math.sin(y / 1400) * 6}vw, ${(-y * 0.04) % 40}vh, 0)`
        g2.style.transform = `translate3d(${Math.cos(y / 1700) * 8}vw, ${(y * 0.03) % 40}vh, 0)`
      }
    })
  }, [])
  return (
    <>
      <div ref={root} className="chroma" aria-hidden="true">
        <div className="chroma-glow chroma-glow-1" />
        <div className="chroma-glow chroma-glow-2" />
      </div>
      <div className="chroma-grain" aria-hidden="true" />
    </>
  )
}
