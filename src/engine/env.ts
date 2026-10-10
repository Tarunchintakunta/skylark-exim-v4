// Device facts decided once at load (TRD §5: tier never changes per frame).
const mq = (q: string) => typeof matchMedia === 'function' && matchMedia(q).matches

export const reducedMotion = mq('(prefers-reduced-motion: reduce)')
export const touch = mq('(pointer: coarse)') || 'ontouchstart' in window
export const isMobile = mq('(max-width: 767px)')

type Conn = { saveData?: boolean; effectiveType?: string }

export type Tier = 1920 | 1280 | 960

export function pickTier(): Tier {
  const c = (navigator as Navigator & { connection?: Conn }).connection
  // TRD §5: CSS width × DPR; phones always get the 960 tier (STORYBOARD mobile crop, 14 MB full-scroll budget).
  if (isMobile || c?.saveData || /(^|-)(2g|3g)$/.test(c?.effectiveType ?? '')) return 960
  const px = window.innerWidth * Math.min(window.devicePixelRatio || 1, 2)
  return px >= 1600 ? 1920 : px >= 1000 ? 1280 : 960
}
