import { useEffect, useRef, type ReactNode } from 'react'
import { chapters } from '../config/chapters'
import { posterUrl } from '../config/media'
import { onTick } from '../engine/clock'
import { isMobile, pickTier } from '../engine/env'
import { scrollStore } from '../engine/scrollStore'
import { VideoPool } from './VideoPool'
import './film.css'

const tier = pickTier()
const lengths = chapters.map((c) => (isMobile ? (c.mobileVh ?? c.vh * 0.8) : c.vh))
const totalVh = lengths.reduce((a, b) => a + b, 0)

/** Pinned full-bleed stage; scroll maps linearly onto chapter clips (docs/STORYBOARD.md conventions). */
export default function Film({ children }: { children?: ReactNode }) {
  const section = useRef<HTMLElement>(null)
  const poster = useRef<HTMLImageElement>(null)
  const videos = useRef<HTMLVideoElement[]>([])

  useEffect(() => {
    const pool = new VideoPool(
      videos.current,
      poster.current!,
      chapters.map((c) => c.id),
      tier,
    )
    let top = 0
    let vhPx = window.innerHeight / 100
    let width = window.innerWidth
    const measure = () => {
      top = section.current!.getBoundingClientRect().top + window.scrollY
      if (window.innerWidth !== width) {
        width = window.innerWidth
        vhPx = window.innerHeight / 100
      }
    }
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(document.body)

    const start = () => {
      scrollStore.started = true
      for (const e of ['wheel', 'touchstart', 'keydown', 'scroll'] as const) removeEventListener(e, start)
    }
    for (const e of ['wheel', 'touchstart', 'keydown', 'scroll'] as const)
      addEventListener(e, start, { passive: true })

    const stage = poster.current!.parentElement!
    let shownChapter = -1
    let lastY = window.scrollY
    const off = onTick(() => {
      const y = window.scrollY
      if (y !== lastY) scrollStore.direction = y > lastY ? 1 : -1
      lastY = y
      let rel = (y - top) / vhPx // vh scrolled into the film
      scrollStore.inFilm = rel < totalVh + 100
      if (!scrollStore.inFilm) return
      rel = Math.max(0, rel)
      let i = 0
      while (i < lengths.length - 1 && rel >= lengths[i]) rel -= lengths[i++]
      scrollStore.chapter = i
      if (i !== shownChapter) {
        shownChapter = i
        stage.style.setProperty('--obj-pos', isMobile ? chapters[i].objectPosition : '50% 50%')
        poster.current!.alt = chapters[i].alt
      }
      scrollStore.progress = Math.min(1, rel / lengths[i])
      pool.update(i, scrollStore.progress, scrollStore.direction, scrollStore.started)
    })
    return () => {
      off()
      ro.disconnect()
      for (const e of ['wheel', 'touchstart', 'keydown', 'scroll'] as const) removeEventListener(e, start)
    }
  }, [])

  return (
    <section ref={section} id="story" className="film" style={{ height: `${totalVh + 100}vh` }}>
      <div className="stage">
        <img
          ref={poster}
          className="stage-media"
          src={posterUrl(chapters[0].id, tier)}
          alt={chapters[0].alt}
          width={1920}
          height={1080}
          fetchPriority="high"
          decoding="async"
        />
        {[0, 1, 2].map((k) => (
          <video
            key={k}
            ref={(el) => {
              if (el) videos.current[k] = el
            }}
            className="stage-media stage-video"
            muted
            playsInline
            preload="auto"
            aria-hidden="true"
            tabIndex={-1}
          />
        ))}
        {children}
      </div>
    </section>
  )
}
