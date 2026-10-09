import { useEffect, useRef } from 'react'
import { onTick, scrollToEl } from '../engine/clock'
import { scrollStore } from '../engine/scrollStore'

/** Mobile only: appears after v-port, hides once the quote section is on screen. */
export default function StickyRfq() {
  const ref = useRef<HTMLAnchorElement>(null)
  useEffect(() => {
    let inQuote = false
    const q = document.getElementById('quote')
    const io = new IntersectionObserver(([e]) => (inQuote = e.isIntersecting))
    if (q) io.observe(q)
    let on = false
    const off = onTick(() => {
      const v = !inQuote && (!scrollStore.inFilm || scrollStore.chapter >= 3)
      if (v !== on) {
        on = v
        ref.current!.classList.toggle('is-on', v)
      }
    })
    return () => {
      off()
      io.disconnect()
    }
  }, [])
  return (
    <a
      ref={ref}
      href="#quote"
      className="sticky-rfq btn-quote"
      onClick={(e) => {
        e.preventDefault()
        scrollToEl(document.getElementById('quote'))
      }}
    >
      Request a quote
    </a>
  )
}
