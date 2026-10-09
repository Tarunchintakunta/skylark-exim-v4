# QUALITY_GATES.md — hard pass/fail gates (Tarun is asleep: you are the picky reviewer)

A scene, asset or PR is DONE only when every applicable gate passes. Record each gate result (PASS/FAIL + evidence path) in the PR body and in NIGHT_LOG.md. "Mostly passes" = FAIL.

## Self-critique procedure (every scene, every asset, every section)
1. Render the 960×540 preview (`scripts/render-scene.sh <blend> preview`) → `docs/renders/<blend>-preview.mp4` + 12-frame contact sheet `docs/renders/<blend>-sheet.jpg`.
2. Also export 3 full-size stills at the busiest frames + every boundary frame (`scripts/contact-sheet.sh --still`).
3. Open the sheet and stills with your image viewer/Read tool and LOOK. Critique as a picky human PM who has seen v3 fail: write a numbered critique in `docs/reviews/<blend>-rN.md` — first impression in one sentence ("does this look like a real photo or a game?"), then every gate below with PASS/FAIL and the frame number.
4. Fix every FAIL, re-render the preview, repeat. **Max 4 rounds per scene** (r1–r4). If it still fails at r4: write the remaining issues in the PR as "Known issues for Tarun", keep the best round wired in, move on, come back if time allows.
5. Only a scene whose latest round passes all G-SCENE gates is "self-approved" and may be full-rendered.
6. Ask yourself the four Tarun questions at the end of every round: *Is it empty? Is it toy-like? Does anything look fake (people, fish, water)? Is anything clipping?* Any "yes" = FAIL.

## G-SCENE — every Blender shot
| Gate | Pass criterion (checkable) |
|---|---|
| G-SCENE-1 Realism | No object uses a flat untextured material. Every hard surface has a PBR texture set (albedo + roughness + normal) and at least one wear layer (dirt/rust/scuffs/grime) via a mask. Check: `blender/scene_audit.py` reports 0 "flat material" objects in camera view. |
| G-SCENE-2 Not toy-like | Bevels on all hard edges (no razor-sharp CG edges); real-world scale (container 12.19 × 2.44 × 2.59 m, truck cab ~2.5 m wide, people 1.50–1.85 m); no primitive-looking shapes (cubes/cylinders without detail) in the frame centre. |
| G-SCENE-3 Busy, lived-in | The density list in SCENES.md for the shot is met (people count, vehicles, props). Port: ≥ 3 STS cranes, ≥ 200 containers visible in the yard/ship, ≥ 6 people, ≥ 3 vehicles moving. No empty quay, no bare floor areas > 20 % of frame. |
| G-SCENE-4 No clipping | `scene_audit.py --intersections` reports 0 intersections between named hero objects (containers, hulls, trucks, people, nets, crates, forklift, pallets) on every 6th frame. Containers sit on corner castings; hulls never overlap hulls or quays; feet touch the ground (no floating, no sinking > 1 cm). |
| G-SCENE-5 Water physics | Water only in sea/ponds/tanks/hoses/wet surfaces; no overflowing ice/foam over edges; no foam on dry land or bunds; sun glint is a surface highlight, never a vertical pillar; drips are particle droplets with motion blur, never static rods; nets sit IN the water with refraction and murk (pond water not fully transparent); a ship casts no hard "floor" shadow on the sea; bow wave + wake foam present for moving hulls; spray falls downward under gravity. |
| G-SCENE-6 People | Every person: MPFB/MakeHuman-based or equivalent realistic body, varied face, skin tone, age, body type; real clothing as separate meshes with folds (cloth sim or sculpted), no skin-tight suits; natural weight-bearing pose (no T/A-pose, no straight locked arms); hands gripping objects make contact; plant staff in full PPE (white coat, hairnet, mask, gloves, boots); faces never in extreme close-up; no two identical people within one frame. |
| G-SCENE-7 Fish & shrimp | Only CC0 scans (ASSETS.md) or the carefully modelled swordfish; never lofted/cartoon fish; heaps follow physics (rigid-body settled, inside crates, on ice); no fused bodies; species shown match CONTENT.md §6 (or unlabelled filler). |
| G-SCENE-8 Light | Natural daylight / practical interior light; mean luma above the floor in `check-clip.sh`; no full-frame colour overlay, vignette > 15 %, or tint (the v3 "dark blue overlay" = automatic FAIL); consistent sun direction across the shot. |
| G-SCENE-9 Setting | Indian setting where the story is in India: Vizag port/coast, Indian truck cab, Indian boat, Indian plant staff. No EU sockets, no European roads, no foreign plates, no readable fake text (BANNED_CLAIMS §8). |
| G-SCENE-10 Camera | The planned move from STORYBOARD.md; smooth (Bezier eased, no jerks, no sudden FOV jumps); the type zone stays calm; subject never cut by frame edges at the mobile crop (`object-position`). |
| G-SCENE-11 Continuity | `scripts/boundary-check.sh` OK for both joins of the clip (SSIM ≥ 0.99 PNG). Hero carton present (chapters 00–07) and identical model. |
| G-SCENE-12 Story | The viewer understands the step in 2 seconds without reading the caption. |

## G-PROD — product models (live GLB)
| Gate | Criterion |
|---|---|
| G-PROD-1 | `public/models/<name>.glb` ≤ 500 KB, `EXT_meshopt_compression` present, WebP textures ≤ 1024² (2048 only for the hero carton if it still fits). |
| G-PROD-2 | Photoreal at 100 % zoom on a 1440 px screen: no ragged/stringy fins, no holes, no floating specks, no colour-checker remnants, no red blotches; eyes intact. |
| G-PROD-3 | Correct proportions vs reference photos of the species; scale consistent between models. |
| G-PROD-4 | Looks right under the site's HDRI from all angles of its turntable (turntable stills at 0/90/180/270° in the PR). |
| G-PROD-5 | Licence recorded in docs/LICENSES.md (aniljaco credited if that prawn is used). |

## G-MEDIA — encoded media
`scripts/check-clip.sh` clean for every clip: 1920/1280/960 tiers each ≤ 2,250 KB; GOP ≤ 6, no B-frames, faststart, no audio, frame count exact; 5 WebP posters per clip within budget; `scripts/check-media-refs.mjs` 0 missing; `scripts/path-weight.sh` within budget. No frame-image sequences anywhere in `public/`.

## G-SITE — the website (tested on the DEPLOYED Vercel preview, not only localhost)
| Gate | Criterion |
|---|---|
| G-SITE-1 No dashboard | No start screen, HUD, rails, pills, chips, progress bars, "chapter x/y", monospace, boxed info panels or placeholder/"awaiting" tags anywhere (Playwright test greps DOM for `placeholder|awaiting|coming soon|TODO` and class names `hud|rail|pill|chip`). |
| G-SITE-2 One headline | At every 2 % of scroll, at most one element with `data-headline` has opacity > 0.05 (Playwright samples 50 positions × desktop/mobile). Headlines never overlap each other or overflow the viewport at 360, 390, 768, 1280, 1440, 1920 px widths. |
| G-SITE-3 Fonts | Fraunces + Hanken Grotesk self-hosted, OFL files committed, no FOIT > 300 ms, no layout shift from font swap (CLS < 0.05). |
| G-SITE-4 Every chapter has real media | Every film chapter shows its Blender clip (full or preview-grade) with posters; never a grey frame, black frame or empty frame — Playwright screenshots each chapter at 10/50/90 % on desktop and mobile, scrolling DOWN and then back UP, and fails on any screenshot with mean luma < 30 or > 245 or standard deviation < 12 (blank). |
| G-SITE-5 Smoothness | On the deployed preview, Chromium 1440×900: 0 long tasks > 50 ms during a scripted full scroll after load; rAF p95 ≤ 20 ms; video stalls (app-reported `window.__v4.stalls`, TRD §6) = 0. Mobile emulation (Moto G Power profile, 4× CPU, Fast 4G 9 Mbps/170 ms): stalls ≤ 2 over the whole scroll, no chapter showing a frozen frame > 300 ms while scrolling. |
| G-SITE-6 Loading | Initial transfer ≤ 3 MB desktop / ≤ 1.5 MB mobile; no clip requested before the first scroll; at most 3 clips (prev/current/next) attached at once; clips 2+ chapters away unloaded. |
| G-SITE-7 Lighthouse | Mobile on the deployed preview, 3 runs median: performance ≥ 90, accessibility ≥ 95, best practices ≥ 95, SEO ≥ 95; LCP < 2.5 s, CLS < 0.05, TBT < 200 ms. Never loosen a budget to pass. |
| G-SITE-8 Reduced motion | `prefers-reduced-motion: reduce`: no Lenis, no scrubbing, posters as static images with captions, no SplitText; everything readable. |
| G-SITE-9 Content | `tests/content.spec.ts` passes (BANNED_CLAIMS); every caption traced to CONTENT.md in `src/config/copy.ts` comments (`// CONTENT §5.8`). |
| G-SITE-10 RFQ | Form validates, composes a correct `mailto:` (subject + body with all fields), prefill from product "Enquire" works, works with keyboard only. |
| G-SITE-11 SEO/OG | Title, meta description (C1), canonical, OG/Twitter tags with `/og/og-image.jpg` 1200×630 (Blender still), JSON-LD Organization, robots.txt, sitemap.xml. |
| G-SITE-12 Mobile | 390×844 and 360×800: tap targets ≥ 44 px, no horizontal scroll, sticky RFQ button doesn't cover captions, every chapter subject visible in the crop. |
| G-SITE-13 a11y | axe-core 0 serious/critical on load, B2, B6; skip link; focus visible (lagoon ring); all posters have alt text from STORYBOARD.md. |

## G-GIT — process
No commit on `main` after the initial README commit; no merges by Claude; every commit references an issue; every PR < ~400 changed lines excluding assets/lockfiles; CI green before asking for review; Vercel deploys ≤ 6 per night (DEPLOY.md).
