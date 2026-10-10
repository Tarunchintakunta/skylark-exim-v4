// Projection of the Blender markets-map still (docs/SCENES.md §S9): plain equirectangular,
// lon −20…150 → x 0…W, lat 65…−10 → y 0…H, W:H = 170:75. The SVG overlay uses the same viewBox.
export const MAP = { lon0: -20, lon1: 150, lat0: 65, lat1: -10, W: 1920, H: 847 }

export function project(lat: number, lon: number): [number, number] {
  return [
    ((lon - MAP.lon0) / (MAP.lon1 - MAP.lon0)) * MAP.W,
    ((MAP.lat0 - lat) / (MAP.lat0 - MAP.lat1)) * MAP.H,
  ]
}

const rad = Math.PI / 180
/** Great-circle arc as an SVG path in map pixels. */
export function arcPath(a: { lat: number; lon: number }, b: { lat: number; lon: number }, steps = 48) {
  const v = (p: { lat: number; lon: number }) => [
    Math.cos(p.lat * rad) * Math.cos(p.lon * rad),
    Math.cos(p.lat * rad) * Math.sin(p.lon * rad),
    Math.sin(p.lat * rad),
  ]
  const A = v(a)
  const B = v(b)
  const d = Math.acos(Math.min(1, A[0] * B[0] + A[1] * B[1] + A[2] * B[2]))
  const pts: string[] = []
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    const s = d < 1e-6 ? 0 : Math.sin(d)
    const k1 = s ? Math.sin((1 - t) * d) / s : 1 - t
    const k2 = s ? Math.sin(t * d) / s : t
    const x = k1 * A[0] + k2 * B[0]
    const y = k1 * A[1] + k2 * B[1]
    const z = k1 * A[2] + k2 * B[2]
    const lat = Math.atan2(z, Math.hypot(x, y)) / rad
    const lon = Math.atan2(y, x) / rad
    const [px, py] = project(lat, lon)
    pts.push(`${i ? 'L' : 'M'}${px.toFixed(1)} ${py.toFixed(1)}`)
  }
  return pts.join('')
}
