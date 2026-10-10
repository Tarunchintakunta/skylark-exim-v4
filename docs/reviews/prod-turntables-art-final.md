# prod-tuna / prod-prawn: art pass final (issue #75, COLOR_SCRIPT row P "Zoi studio: navy + ice")

Build: `assets-src/blender/build/prod_turntable_scene.py -- both` (rebuild reproduces everything). Camera, lens, DOF, frames 1-120, loop and 64 samples are unchanged.

## What changed
- **Backdrop:** the dark slate sweep is now a matte navy (`navy_mat`). It drifts slowly between #0b1424, #0f1d33 and #1a3358 (×0.7), with fine value noise. Roughness is 0.72-0.88 and specular 0.25, so there is no grazing sheen.
- **Light glows:** 7 additive soft discs (`GLOWS`/`glows()`), placed through the camera just in front of the sweep and always behind the product. Their emission fades toward the floor, so the sweep never cuts a visible edge. Colours: a large ice #9fd8ff glow behind the product, #3a5b8c side glows, #9fe3ff and #9fd8ff dots, and two marigold #e2a03a dots on the right. The top-left type zone stays clear. No shadows, no reflections.
- **Lights:**
  - KEY: 5600 K softbox, unchanged.
  - FILL: #3a5b8c.
  - RIM: #9fe3ff, 260 W·S².
  - RIM2: new low #9fe3ff rim on the ice slab, 200 W·S².
  - WASH: #3a5b8c.
- **World:** studio_small_09 HDRI (kept for reflections on the silver skin), multiplied by the hue of #0b1424. No world volume or fog.
- **Ice:** albedo shifted icier: slab 0.62/0.82/0.95 to 0.88/0.95/1.0; chunks 0.72/0.88/0.97 to 0.92/0.97/1.0.
- **Grade:** `look.apply` (AgX Medium High Contrast), then `look.grade(lift '#3a5b8c' 0.012, gain '#ffe9d2' 0.025, sat 1.10)`. This is complementary per §3: cool shadows, warm-neutral highlights, so the product colours stay true. Vignette 0.10, bloom 0.15, no grain.

## Process
- Rounds r1-r6 are in `docs/reviews/prod-turntables-art-r1..r6.md`. Stills are in `assets-src/blender/stills/prod-{tuna,prawn}/art6-NNNN.png`.
- Before/after: `docs/renders/prod-tuna-before-after.jpg` and `docs/renders/prod-prawn-before-after.jpg`. Left is before, right is after. Rows top to bottom are frames 1, 12, 40, 60, 108 and 120.

## Full render
| | prod-tuna | prod-prawn |
|---|---|---|
| frames | 120/120 (`assets-src/render/prod-tuna/`) | 120/120 (`assets-src/render/prod-prawn/`) |
| wall time (render only) | 6.5 min (03:52:30-03:58:59) | 6.1 min (03:59:32-04:05:37) |
| s/frame (Blender "Time") | 3.3 | 3.1 |
| luma f12 / f60 / f108 | 93/60, 98/62, 102/63 | 97/61, 98/62, 103/65 |
| luma all 120 frames | 0 FAIL | 0 FAIL |
| contact sheet | `docs/renders/prod-tuna-art-sheet.jpg` | `docs/renders/prod-prawn-art-sheet.jpg` |

## G-SCENE
| Gate | tuna | prawn | Notes |
|---|---|---|---|
| G-PROD-2 photoreal at 100 % | PASS | PASS | Same product, slab and ice geometry as the accepted v4 turntables. The glows read as out-of-focus studio lights. |
| G-PROD-4 all angles | PASS | PASS | Sheets cover every 30°: no floating, no clipping, no hard backdrop lines. |
| G-SCENE-8 light / colour | PASS | PASS | Warm key, cool fill, cyan rim. Colour comes from light, world and backdrop, with no full-frame tint. Grade is within §3 limits (lift ≤ 0.025, gain ≤ 0.035, vignette ≤ 0.12). |
| Readability (luma) | PASS | PASS | Mean 93-103, sd 60-65. The top-left third is the darkest, calmest zone. |
| Speed ≤ 15 s/frame | PASS | PASS | About 3.2 s/frame. |
| Loop | PASS | PASS | f120 to f1 is still a continuous 3° step. Glows and backdrop are static. |

## Known issues
- The near floor has a fine mottled, wet-looking texture (the value noise plus the key's specular). Fine at web size.
- The marigold accents are subtle (dim bokeh at the right edge). The ice slab still reads mostly white; the cyan shows at the rims and edges.
- 16:9 mobile centre-crop limits are as before (see `prod-turntables-full-final.md`).
