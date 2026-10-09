import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Lenis from 'lenis'
import { reducedMotion, touch } from './env'

// One clock (TRD §2): gsap.ticker drives Lenis, ScrollTrigger and every per-frame subscriber. No other rAF loops.
gsap.registerPlugin(ScrollTrigger)
gsap.ticker.lagSmoothing(0)
ScrollTrigger.config({ ignoreMobileResize: true })

type Tick = (time: number) => void
const subs = new Set<Tick>()

export const lenis =
  reducedMotion || touch
    ? null
    : new Lenis({ autoRaf: false, lerp: 0.09, smoothWheel: true, syncTouch: false })
lenis?.on('scroll', ScrollTrigger.update)

gsap.ticker.add((t) => {
  lenis?.raf(t * 1000)
  for (const fn of subs) fn(t)
})

export function onTick(fn: Tick) {
  subs.add(fn)
  return () => void subs.delete(fn)
}

export function scrollToEl(el: Element | null) {
  if (!el) return
  if (lenis) lenis.scrollTo(el as HTMLElement, { duration: 1.4 })
  else el.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth' })
}

export { gsap, ScrollTrigger }
