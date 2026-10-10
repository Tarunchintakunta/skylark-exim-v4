# sea.blend (v-sea, f1-264, dawn): art pass final (issue #75, COLOR_SCRIPT row 12)

Full render: 264/264 frames in assets-src/render/sea/ (1920x1080, EEVEE 32 spp, motion blur 0.3, screen-trace thickness 0.5 kept).
Final render (r8, after the lead review) took 10 min wall time, about 2.3 s/frame. All 264 frames were re-rendered, see below. Contact sheet: docs/renders/sea-art-sheet.jpg. Before/after: docs/renders/sea-before-after.jpg
(rows f1, f27, f132, f196, f238, f264, before on the left). Rounds: sea-art-r1..r5.md.

## What changed (all in assets-src/blender/build/sea.py)
- Key: the sun stays at 4° (f1) rising to 6° (f264), az 95, and its colour is now #ffb070.
- Fill: a cool sun from the west (camera side), #4f8fa8, energy 3.0, elev 35°, az 275°, no shadow.
- Rim: a warm area light #ffcf8a (3600 W, 5 m) east of the boat, lighting the crew, net and wheelhouse. Specular is off, because its reflection showed in the sea.
- World: the physical sky is multiplied by a dawn gradient, horizon #ffbf7a to zenith #24496b (mix 0.85, reaching the zenith colour by z 0.24).
- Sea mist #f0c9a0 density 0.0006 is a bounded volume box, SK_MIST, 1.2 km x 60 m. World fog absorbed the whole sky in r1. Volumetric tile 16, 16 samples.
- Materials: sea body deep teal #0f3d4a (shallow 0.03/0.15/0.16). The wheelhouse is a weathered warm white (0.72/0.69/0.62, more streaks).
  New sunrise-orange life ring on the aft wheelhouse wall beside the door.
- Grade: AgX - Medium High Contrast, exposure +0.25. look.grade(lift #0f3d4a 0.025, gain #ffb070 0.03, sat 1.12, contrast 2,
  bloom 0.15, vignette 0.10). This is complementary per §3: teal shadows against gold highlights. No full-frame tint and no grain.
- Unchanged: the camera, lens, frame range, f1 BRIDGE_HORIZON framing (sun 4°/az 95 #ffb070, horizon #ffbf7a) and the ocean seed.

## r8 fix (lead review: cyan cast on the deck close-ups f150-245)
- Diagnosis: with the compositor off, f196 already shows warm skin, white ice and brown wood. The cyan comes from the grade's teal lift
  (look._tint at 0.025 pushes green/blue strongly in the shadows and mids), not from the light. A 20x deck key barely changed it.
- Light: new SK_DeckKey sun #ffcf8a from the sunrise side (az 100, elev 32, 8° soft, specular 0 so there is no second glint in the sea).
  Energy is keyed 0 -> 2.6 over f140-160, held, then 2.6 -> 0 over f240-255. The cool fill SK_Fill is keyed 3.0 -> 1.3 over the same ramps.
- Grade: the Color Balance lift strength is keyed 0.025 -> 0.008 over the same ramps (still one grade node tree for the blend).
  The deck now reads warm-brown skin, silver fish, white ice and brown wood against the teal sea.
- Why the whole clip was re-rendered: the lead's look.py update (glare threshold 1.0 -> 1.5) changes every sun frame, so rendering only
  f132-258 would have popped at the range edges. f1-139 and f256-264 differ from the previous render only through that threshold.
- Pop check: per-frame mean luma f134-164 and f234-260 moves by at most 5 per frame. The steady +5/frame at f236-240 is the camera
  pulling out into the bright sky (the before frames climb +3/frame over the same range), not the light ramp.

## Luma (full frames, r8)
| Frame | Role | Before | After |
|---|---|---|---|
| f1 | BRIDGE_HORIZON | 203/27 | 223/24 ok |
| f27 | 10 % | 223/21 | 219/31 ok |
| f132 | 50 % | 131/50 | 113/53 ok |
| f140 / f160 | deck ramp in | - | 108/44, 104/41 ok |
| f196 | deck beat | 116/43 | 88/52 ok |
| f238 | 90 % | 137/56 | 116/74 ok |
| f255 | deck ramp out | - | 159/85 ok |
| f264 | last / poster | 165/77 | 161/82 ok |

## G-SCENE
| Gate | Result | Frames |
|---|---|---|
| G-SCENE-1 Realism | PASS: believable sunrise, gold horizon over a teal sea | 1, 132, 264 |
| G-SCENE-2 Not toy-like | PASS (wheelhouse still simple) | 238 |
| G-SCENE-3 Busy | PASS | 132, 238 |
| G-SCENE-4 No clipping | PASS (sun disc and glitter only; net close to lens f178-196 as before) | 185 |
| G-SCENE-5 Water | PASS: no rim or tyre reflections in the sea | 60-132, 264 |
| G-SCENE-6 People | PASS: warm rims; backlit at f264 | 238, 264 |
| G-SCENE-7 Fish | PASS | 196 |
| G-SCENE-8 Light/grade | PASS: no overlay, vignette 0.10, luma all ok | all |
| G-SCENE-9 Setting | PASS | 264 |
| G-SCENE-10 Camera | unchanged | - |
| G-SCENE-11 Continuity | f1 = BRIDGE_HORIZON per §2; the lead equalises against pond's f216 | 1 |
| G-SCENE-12 Story | PASS | 196, 264 |

## Known issues
- Mean luma at f132-f238 is 18-28 levels below before (accepted by the lead). The sea is now deep teal (the row's dominant colour) where it used to be a pale grey reflection.
  The subjects are as bright as before. More exposure would wash out f1 and f27 (222-224).
- f1 and f27 have sd 24-31. They are bright, soft horizon frames, and the top-left zone stays calm for the type.
- The f264 crew are backlit into blue-violet silhouettes with a sun flare (poster intent).
- The pond f216 bridge must use the same sky tint (horizon #ffbf7a, zenith #24496b) for a clean match.
- At f238 the farthest crew still pick up some cool fill. The deck beat f196 is fully warm.
