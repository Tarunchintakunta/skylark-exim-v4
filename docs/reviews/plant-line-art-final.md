# plant-line art pass: final (issue #75), 765/765 frames in assets-src/render/plant-line/

Build: assets-src/blender/build/plant-line.py, rebuilt. Before-after: docs/renders/plant-line-before-after.jpg. The rows are,
top to bottom: f1, f96, f287, f478, f669, f765, with the before frame on the left and the after frame on the right.
Contact sheet: docs/renders/plant-line-art-sheet.jpg. Rounds r1–r4: docs/reviews/plant-line-art-r1..r4.md, stills in assets-src/blender/stills/plant-line/art-r*/.

## What changed
- **Materials**
  - PUF walls are cool blue-white (0.56/0.64/0.75), with grime, streaks and ±14 % macro hue/value variation. They were paper-white.
  - Epoxy floor is blue-grey (0.30/0.40/0.47). Lab floor is 0.42/0.50/0.58. Cabinets and trays are cool.
  - Crate set is blue / red / **marigold** / blue. Marigold replaced the green.
- **Lights.** The key is the overhead LED: `#eef4ff`, or 5500 K in the wash bay, at 0.8× the previous energy. Per chapter, coloured fill comes from the side and warm rim from ahead:
  - **Lab:** fill `#7f9fd0` 50 W. Rim `#ffc27a` 90 W at the bench and 220 W at the QC shelf. Task lamp `#f0b04a` 40 W, with a warm LED ring.
  - **Grade:** fill `#7090c8` 450 W. Rim `#ffd59a` 1200 W.
  - **Peel:** fills `#6c8cc0` 450 W and 200 W. Rim `#ffc890` 2000 W from the partition.
  - **Wash:** fill `#5d86b0` 250 W. Dock spill `#ffc078` 1100 W. `L_dock_fill` is `#ffd08a`. Sun is `#ffc98a` at 20°/100° (BRIDGE_DOCK).
- **World.** Interior ambient is multiplied by `#8fb0e6` (cool) from f40 to f660, then returns to the plain morning sky by f740.
- **Fog.** An interior volume box `fog_interior` (`#cfe3ee`), keyed per chapter:

  | Frame | Density |
  | --- | --- |
  | f1 | 0.0015 |
  | lab | 0.0002 |
  | line | 0.0007 |
  | hall | 0.0006 |
  | wash | 0.0010 |
  | f765 | 0.0008 |

  Volumetric tile is 8, with 24 samples, ending at 80 m. There is no world volume: it absorbed the sky and turned the dock black in r1–r2, as in the lead's note.
- **Grade.** `look.apply(scene,'plant-line')` sets AgX Medium High Contrast. Then `look.grade(lift #2a4a6e 0.025, gain #ffd59a 0.035, sat 1.14, contrast 8, bloom 0.15, vignette 0.10)`.
  - This is complementary per §3: a cool lift, with warmth from the lamp and the door.
  - It is one grade for the whole blend. The only exception is f1–40, where Lift and Gain ease from plant-cold's grade (lift `#1e2a4f` 0.008, gain `#cfe0ff` 0.012, plus a white balance of 0.78/0.91/1.0) to ours. Joins 192, 383 and 574 are untouched.
- **BRIDGE_BELT rig.** The copied plant-cold key `L_pc_bridge` is now `#d6ecff`. Added `L_pc_rim`, a cyan `#a8f0ff` grazing rim at 240 W from the freezer side, a copy of ART_belt_rim. Both fade out over f1–40. Opening exposure is −2.35.

## Measurements
- **BRIDGE_BELT f1 vs plant-cold/0574.png (art render)**
  - Full-res SSIM is **0.918**; 320 px SSIM is 0.858. Before the opening re-render it was 0.709.
  - Mean RGB: ours 179/185/186, theirs 170/182/187.
  - Luma: ours 180/20, theirs 176/18.
  - What remains: plant-cold's frame falls off darker toward the right edge.
- **Opening re-render seam.** f1–64 was re-rendered after the bridge tweak. At 320 px, f64→f65 scores 0.80 and the neighbouring step f63→f64 scores 0.77, so there is no pop.
- **Render time.** 765 frames in 62 min, about 4.9 s per frame on the shared GPU. The maximum was 16.7 s (f343), and f342 took 15.2 s; all other frames were ≤ 14.1 s. Build time is about 4 min.

| Frame | Luma (mean/sd) |
| --- | --- |
| f1 | 180/20 |
| f20 | 211/17 |
| f96 | 176/30 |
| f173 | 184/35 |
| f192 | 186/33 |
| f211 | 186/28 |
| f287 | 148/49 |
| f364 | 149/42 |
| f383 | 144/44 |
| f402 | 142/45 |
| f478 | 151/48 |
| f555 | 144/49 |
| f574 | 139/50 |
| f593 | 141/40 |
| f669 | 158/50 |
| f746 | 161/55 |
| f765 | 161/60 |

All pass. Every frame is at or above its "before" luma.

## G-SCENE
| Gate | Result |
| --- | --- |
| G-SCENE-1..7, 9, 10, 12 | PASS. Content, camera, lens and frame range are unchanged from the r5 build. |
| G-SCENE-8 (no overlay, vignette ≤ 12 %, luma floor) | PASS. Colour comes from the lights and the world; vignette is 0.10. |
| G-SCENE-11 (bridges) | BRIDGE_BELT SSIM 0.918 vs plant-cold f574. BRIDGE_DOCK is to spec (interior 5500 K, sun `#ffc98a` 20°/100°). The lead equalises both. |

## Known issues
- Two frames, f342 and f343 (the overhead reveal), went over 15 s on the shared GPU: 15.2 s and 16.7 s.
- The opening brightness rise is still there: f20 has luma 211. It passes, but it is the brightest frame.
- The white PPE takes on the blue cast in the halls. Warm counterpoints are skin, crates, rims, the lamp and the door spill.
- The bright floor spill at the dock door clips (it is the sunlit patch).
- `L_hall_-3` and `L_hall_4` keep their pre-art 700 W, because the bridge fade owns their energy keys.
