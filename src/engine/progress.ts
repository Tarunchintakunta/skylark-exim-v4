/** 0..1 progress of a tall sticky section: 0 when its top hits the viewport top, 1 when its bottom hits the bottom. */
export function stickyProgress(el: HTMLElement) {
  const r = el.getBoundingClientRect()
  const run = r.height - innerHeight
  return run <= 0 ? (r.top <= 0 ? 1 : 0) : Math.min(1, Math.max(0, -r.top / run))
}
/** True while any part of the element is on screen. */
export function onScreen(el: HTMLElement) {
  const r = el.getBoundingClientRect()
  return r.bottom > 0 && r.top < innerHeight
}
