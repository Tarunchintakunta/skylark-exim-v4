# PLAN.md — Skylark Exim v4 overnight plan (10 Oct 2026)

Repo `Tarunchintakunta/skylark-exim-v4` (private). Every task = one issue → one branch → micro commits → one PR. Nothing is merged by Claude. Merge order lives in `docs/STACK.md`.

## Issues
| # | Title | Milestone | Depends on | Est. |
|---|---|---|---|---|
| 1 | docs: handoff pack, PLAN, NIGHT_LOG | M1 | — | 20 min |
| 2 | infra: Vite + React + TS scaffold, lint, hooks, vercel.json | M1 | 1 | 20 min |
| 3 | engine: tokens + self-hosted fonts | M1 | 2 | 20 min |
| 4 | engine: one clock (ticker, Lenis, ScrollTrigger, store) | M1 | 2 | 15 min |
| 5 | engine: Stage, 3-video pool, posters, seeking, `__v4` | M1 | 4 | 45 min |
| 6 | content: chapters, copy.ts, captions, countdown | M1 | 5 | 30 min |
| 7 | section: header, menu, loader, sticky RFQ | M1 | 6 | 25 min |
| 8 | a11y: reduced motion, skip links, focus | M1 | 7 | 15 min |
| 9 | infra: tests, CI, media manifest, check-media-refs | M1 | 6 | 40 min |
| 10 | asset: Blender asset library v1 | M1 | 1 | 60 min |
| 11 | asset: product scans fetched/cleaned/optimised + carton GLB | M1 | 10 | 40 min |
| 12 | scene S1 table → v-table | M2 | 10 | 45 min |
| 13 | scene S2 port → v-port | M2 | 10 | 60 min |
| 14 | scene S3 reefer → v-reefer | M2 | 13 | 40 min |
| 15 | scene S4 sea → v-sea | M2 | 10 | 45 min |
| 16 | scene S5 pond → v-pond | M2 | 10 | 45 min |
| 17 | scene S6 truck → v-truck | M2 | 10 | 40 min |
| 18 | scene S7 plant-cold → v-cold/v-pack/v-freeze | M2 | 10 | 50 min |
| 19 | scene S8 plant-line → v-qc/v-grade/v-peel/v-wash | M2 | 18 | 50 min |
| 20 | scene: bridges + boundary checks | M2 | 12–19 | 30 min |
| 21 | B1 Now forward | M3 | 11 | 35 min |
| 22 | B2 Products | M3 | 11 | 45 min |
| 23 | B3 Quality & facility | M3 | 18,19 | 20 min |
| 24 | B4 Markets (map still + SVG) | M3 | 10 | 40 min |
| 25 | B5 People | M3 | 15 | 15 min |
| 26 | B6 RFQ + contact + PDF | M3 | 22 | 35 min |
| 27 | footer, /licenses, 404 | M3 | 26 | 20 min |
| 28 | SEO / OG | M3 | 12 | 15 min |
| 29 | mobile pass | M3 | 27 | 25 min |
| 30 | preview deploys + perf/Lighthouse on deployed URL | M3 | 29 | 30 min |
| 31 | full render queue + media swap | M4 | 12–19 | background |
| 32 | polish + morning report | M5 | all | 45 min |

## Branch / PR stack
Because every preview deploy must contain everything built so far (DEPLOY.md §3 "from the TOP of the stack"), the PRs form one linear stack in issue order. GIT_WORKFLOW §5 prefers ≤ 5 levels; a linear stack is deeper — logged as a judgement call in NIGHT_LOG. Merge bottom first, "Create a merge commit".

## Render queue (priority order, RENDER_PIPELINE §5)
1. v-table (table) · 2. v-port (port) · 3. v-reefer (reefer) · 4. v-sea (sea) · 5. v-pond (pond) · 6. v-truck (truck) · 7. v-cold/v-pack/v-freeze (plant-cold) · 8. v-qc/v-grade/v-peel/v-wash (plant-line) · stills: markets-map, og-image.
Previews (960×540, 16 samples) for every scene first; full 1080p one at a time in the background. Re-estimated after the first measured frame (see NIGHT_LOG).

## Hour plan (IST, adapted to measured render speed in NIGHT_LOG)
- 00:25–01:30 M1: repo, docs, scaffold, engine, tokens, config, tests/CI, asset library v1.
- 01:30–04:00 M2: scenes in priority order; previews in the background; preview-grade masters wired as soon as each preview lands.
- 04:00–05:00 M3: B1–B6, footer, SEO, mobile; deploy preview #2; perf + Lighthouse on the deployed URL.
- all night M4: full renders in priority order, swapped in as they finish.
- 06:00–07:00 M5: gates on the deployed preview, fixes, final deploy, REPORT.
