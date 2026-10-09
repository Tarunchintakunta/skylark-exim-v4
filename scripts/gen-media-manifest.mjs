// Writes src/config/media.json: every concrete media file the app can request (chapters × tiers + posters),
// so scripts/check-media-refs.mjs catches a missing tier before it ships (the v3 empty-frame bug).
import { readFileSync, writeFileSync } from 'node:fs'
const src = readFileSync('src/config/chapters.ts', 'utf8')
const ids = [...src.matchAll(/id: '([^']+)'/g)].map((m) => m[1])
const out = []
for (const id of ids) {
  for (const w of [1920, 1280, 960]) out.push(`/media/${id}_${w}.mp4`, `/media/${id}_${w}.webp`)
  for (const w of [1280, 960]) out.push(`/media/${id}_end_${w}.webp`)
}
const extra = (() => {
  try {
    return JSON.parse(readFileSync('scripts/media-extra.json', 'utf8'))
  } catch {
    return []
  }
})()
writeFileSync('src/config/media.json', JSON.stringify([...out, ...extra], null, 1) + '\n')
console.log(`media.json: ${out.length + extra.length} files`)
