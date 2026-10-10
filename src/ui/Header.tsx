import { useEffect, useRef, useState } from 'react'
import { nav } from '../config/nav'
import { onTick, scrollToEl } from '../engine/clock'
import { scrollStore } from '../engine/scrollStore'
import Wordmark from './Wordmark'
import './header.css'

/** Minimal header: hides while scrolling down through the film, returns on scroll-up or pointer near the top. */
export default function Header() {
  const ref = useRef<HTMLElement>(null)
  const [open, setOpen] = useState(false)
  const menuBtn = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    let nearTop = false
    const move = (e: PointerEvent) => (nearTop = e.clientY < 96)
    addEventListener('pointermove', move, { passive: true })
    let hidden = false
    const off = onTick(() => {
      const h = scrollStore.inFilm && scrollStore.direction > 0 && window.scrollY > 80 && !nearTop
      if (h !== hidden) {
        hidden = h
        ref.current!.classList.toggle('is-hidden', h)
      }
    })
    return () => {
      off()
      removeEventListener('pointermove', move)
    }
  }, [])

  useEffect(() => {
    if (!open) return
    const key = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    addEventListener('keydown', key)
    const btn = menuBtn.current
    document.querySelector<HTMLElement>('.menu a')?.focus()
    return () => {
      removeEventListener('keydown', key)
      btn?.focus()
    }
  }, [open])

  const go = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault()
    setOpen(false)
    scrollToEl(document.querySelector(href))
    history.replaceState(null, '', href)
  }

  return (
    <header ref={ref} className={`site-header${open ? ' is-open' : ''}`}>
      <a
        href="#story"
        className="site-header-mark"
        onClick={(e) => go(e, '#story')}
        aria-label="Skylark Exim, back to the start"
      >
        <Wordmark />
      </a>
      <div className="site-header-actions">
        <a href="#quote" className="btn-quote" onClick={(e) => go(e, '#quote')}>
          Request a quote
        </a>
        <button
          ref={menuBtn}
          type="button"
          className="menu-btn"
          aria-expanded={open}
          aria-controls="site-menu"
          onClick={() => setOpen((o) => !o)}
        >
          <span className="menu-btn-lines" aria-hidden="true" />
          <span className="sr-only">{open ? 'Close menu' : 'Open menu'}</span>
        </button>
      </div>
      <nav id="site-menu" className="menu" aria-label="Main" hidden={!open}>
        <ul>
          {nav.map((n) => (
            <li key={n.href}>
              <a href={n.href} onClick={(e) => go(e, n.href)} className="menu-link">
                {n.label}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  )
}
