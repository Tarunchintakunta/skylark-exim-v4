import type { Tier } from '../engine/env'
import { clipUrl, endPosterUrl, posterUrl } from '../config/media'

// The smoothness core (docs/TRD.md §6): three <video> elements hold prev / current / next.
// Everything else is detached. Scroll scrubs currentTime; the poster layer underneath is pixel-identical
// to the shared boundary frames, so a clip that isn't ready yet never shows grey or black.

const FRAME = 1 / 24

interface Slot {
  el: HTMLVideoElement
  idx: number // chapter index, -1 = free
  ready: boolean // a frame has been decoded since attach
  attachedAt: number
  failed: boolean
  pending: number | null
  target: number
}

export interface V4Metrics {
  stalls: number
  seeks: number
  maxSeekMs: number
  attached: string[]
  tier: Tier
}

declare global {
  interface Window {
    __v4: V4Metrics
  }
}

export class VideoPool {
  private slots: Slot[]
  private ids: string[]
  private tier: Tier
  private poster: HTMLImageElement
  private shown: Slot | null = null
  private stalled = false
  private seekStart = new WeakMap<HTMLVideoElement, number>()
  private warmed = new Set<string>()
  metrics: V4Metrics

  constructor(els: HTMLVideoElement[], poster: HTMLImageElement, ids: string[], tier: Tier) {
    this.ids = ids
    this.tier = tier
    this.poster = poster
    this.metrics = window.__v4 = { stalls: 0, seeks: 0, maxSeekMs: 0, attached: [], tier }
    this.slots = els.map((el) => {
      const s: Slot = { el, idx: -1, ready: false, attachedAt: 0, failed: false, pending: null, target: 0 }
      el.muted = true
      el.playsInline = true
      el.preload = 'auto'
      el.disablePictureInPicture = true
      el.addEventListener('seeked', () => this.onSeeked(s))
      el.addEventListener('loadeddata', () => this.markReady(s))
      return s
    })
  }

  private onSeeked(s: Slot) {
    const t0 = this.seekStart.get(s.el)
    if (t0 !== undefined) {
      this.metrics.maxSeekMs = Math.max(this.metrics.maxSeekMs, performance.now() - t0)
      this.seekStart.delete(s.el)
    }
    this.markReady(s)
    if (s.pending !== null) {
      const t = s.pending
      s.pending = null
      this.seek(s, t)
    }
  }

  // Ready = a decoded frame near the target exists (frame 0 of a clip entered from below is not "ready").
  private markReady(s: Slot) {
    if (s.idx >= 0 && s.el.readyState >= 2 && Math.abs(s.el.currentTime - s.target) <= 2 * FRAME)
      s.ready = true
  }

  private detach(s: Slot) {
    s.idx = -1
    s.ready = false
    s.failed = false
    s.pending = null
    s.el.removeAttribute('src')
    s.el.load()
  }

  private attach(s: Slot, idx: number) {
    s.idx = idx
    s.ready = false
    s.failed = false
    s.pending = null
    s.attachedAt = performance.now()
    s.el.src = clipUrl(this.ids[idx], this.tier)
    s.el.load()
  }

  private slotFor(idx: number) {
    return this.slots.find((s) => s.idx === idx)
  }

  private buffered(el: HTMLVideoElement, t: number) {
    const b = el.buffered
    for (let i = 0; i < b.length; i++) if (t >= b.start(i) - 0.001 && t <= b.end(i) + 0.001) return true
    return false
  }

  private seek(s: Slot, t: number) {
    const el = s.el
    s.target = t
    if (el.seeking) {
      s.pending = t
      return
    }
    if (Math.abs(el.currentTime - t) <= FRAME / 2) {
      this.markReady(s)
      return
    }
    if (!this.buffered(el, t)) {
      // Hold the last good frame (never blank) and count one stall per episode.
      if (!this.stalled && s.ready) this.metrics.stalls++
      this.stalled = true
      s.pending = t
      return
    }
    this.stalled = false
    this.metrics.seeks++
    this.seekStart.set(el, performance.now())
    // ponytail: currentTime instead of fastSeek — fastSeek snaps to keyframes (GOP 6) and would break shared frames.
    el.currentTime = t
  }

  private warmPoster(url: string) {
    if (this.warmed.has(url)) return
    this.warmed.add(url)
    const img = new Image()
    img.decoding = 'async'
    img.src = url
    img.decode().catch(() => undefined)
  }

  /** Called every tick while the film is on screen. */
  update(idx: number, progress: number, direction: 1 | -1, started: boolean) {
    const id = this.ids[idx]
    const posterSrc = direction < 0 && progress > 0.5 ? endPosterUrl(id, this.tier) : posterUrl(id, this.tier)
    if (!this.poster.src.endsWith(posterSrc)) this.poster.src = posterSrc
    if (!started) return

    // Desired set: current, next, prev (in priority order). Next waits until current can play through.
    const cur = this.slotFor(idx)
    const want = [idx]
    if (idx + 1 < this.ids.length && cur && cur.el.readyState >= 4) want.push(idx + 1)
    if (idx - 1 >= 0) want.push(idx - 1)
    for (const s of this.slots) if (s.idx !== -1 && s.idx !== idx && Math.abs(s.idx - idx) > 1) this.detach(s)
    for (const w of want) {
      if (this.slotFor(w)) continue
      const free = this.slots.find((s) => s.idx === -1)
      if (free) this.attach(free, w)
    }
    if (idx + 1 < this.ids.length) this.warmPoster(posterUrl(this.ids[idx + 1], this.tier))
    if (idx > 0) this.warmPoster(endPosterUrl(this.ids[idx - 1], this.tier))

    const s = this.slotFor(idx)
    if (s) {
      const d = s.el.duration
      if (!s.ready && !s.failed && performance.now() - s.attachedAt > 1500 && s.el.readyState < 2)
        s.failed = true
      if (Number.isFinite(d) && d > 0) this.seek(s, Math.min(progress, 1) * Math.max(d - FRAME, 0))
    }
    // Show the clip once a frame near the target is decoded; while later seeks run it keeps its last frame.
    const ok = s && s.ready && !s.failed
    const next = ok ? s : null
    if (next !== this.shown) {
      this.shown?.el.classList.remove('is-on')
      next?.el.classList.add('is-on')
      this.shown = next
    }
    this.metrics.attached = this.slots.filter((x) => x.idx >= 0).map((x) => this.ids[x.idx])
  }
}
