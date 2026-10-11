// Per-chapter colour script for the web layer — docs/COLOR_SCRIPT.md §4 (hex values are the spec).
export interface ChapterColors {
  a: string // gradient field / glow 1
  b: string // glow 2
  accent: string // eyebrow, countdown outline, hint line
  glow: string // soft glow behind the active caption
}

export const palette: Record<string, ChapterColors> = {
  'v-table': { a: '#2a1810', b: '#5a3420', accent: '#e2a03a', glow: '#c8743a' },
  'v-reefer': { a: '#0e2238', b: '#1f4f73', accent: '#9fd8ff', glow: '#6fb7d9' },
  'v-port': { a: '#1d1838', b: '#5a2f4a', accent: '#ffb06b', glow: '#e57a44' },
  'v-cold': { a: '#141c3a', b: '#2c3a73', accent: '#9fe3ff', glow: '#6b5fb5' },
  'v-pack': { a: '#14202e', b: '#28466a', accent: '#e2a03a', glow: '#5f86b8' },
  'v-freeze': { a: '#0d1f2c', b: '#164a5c', accent: '#8fe0f0', glow: '#4f9fb8' },
  'v-qc': { a: '#121c28', b: '#2a4a6e', accent: '#f0b04a', glow: '#3f6fa0' },
  'v-grade': { a: '#101a26', b: '#24456a', accent: '#e2a03a', glow: '#7090c8' },
  'v-peel': { a: '#101a26', b: '#2c4f78', accent: '#e2a03a', glow: '#6c8cc0' },
  'v-wash': { a: '#0f1e28', b: '#245a6e', accent: '#f2c27a', glow: '#2f6e8a' },
  'v-truck': { a: '#1f1a10', b: '#4f5a2c', accent: '#ffc98a', glow: '#d9a256' },
  'v-pond': { a: '#0f2624', b: '#2f6e68', accent: '#f2d27a', glow: '#7fb6c8' },
  'v-sea': { a: '#0b2228', b: '#0f3d4a', accent: '#ffb070', glow: '#f0b35a' },
}

/** Business sections settle into the Zoi navy field (COLOR_SCRIPT §4). */
export const sectionsField: ChapterColors = { a: '#0b1424', b: '#13243b', accent: '#9fd8ff', glow: '#2c4f78' }

const hex = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16))
const toHex = (c: number[]) => '#' + c.map((x) => Math.round(x).toString(16).padStart(2, '0')).join('')

/** Linear blend of two hex colours, t in 0..1. */
export function mix(x: string, y: string, t: number) {
  const a = hex(x)
  const b = hex(y)
  return toHex(a.map((v, i) => v + (b[i] - v) * t))
}

export function mixColors(x: ChapterColors, y: ChapterColors, t: number): ChapterColors {
  return {
    a: mix(x.a, y.a, t),
    b: mix(x.b, y.b, t),
    accent: mix(x.accent, y.accent, t),
    glow: mix(x.glow, y.glow, t),
  }
}
