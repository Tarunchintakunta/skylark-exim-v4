import type { Tier } from '../engine/env'

export const TIERS: Tier[] = [1920, 1280, 960]
// Poster tiers that exist on disk (scripts/make-posters.sh): start 1920/1280/960, end 1280/960.
export const clipUrl = (id: string, t: Tier) => `/media/${id}_${t}.mp4`
export const posterUrl = (id: string, t: Tier) => `/media/${id}_${t}.webp`
export const endPosterUrl = (id: string, t: Tier) => `/media/${id}_end_${t === 1920 ? 1280 : t}.webp`
