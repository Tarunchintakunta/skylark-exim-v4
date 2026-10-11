# pond.blend: art pass, final review (issue #75, COLOR_SCRIPT row 11)

## Render
- 216/216 frames at 1920x1080, 32 spp, in assets-src/render/pond/.
- Wall time 14 min, about 3.9 s/frame (the lock had one slot).
- Contact sheet: docs/renders/pond-art-sheet.jpg. Before/after: docs/renders/pond-before-after.jpg.
- Build: assets-src/blender/build/pond.py. The f180–216 exposure ramp was patched into the saved .blend with code identical to `end_ramp()` in pond.py.

## Look
- **Key:** sun colour keyed #ffcf7a (f1) → #ffb070 (f216).
- **Fill:** sun #7fb6c8 from the west, 0.9.
- **Rim:** sun #ffe0a0 from the ENE, 1.6. Fill and rim have no shadows and no specular.
- **Sky:** hue tints over the physical sky, keyed.
  - Camera rays: horizon #ffd98f → zenith #3f6f9a.
  - Lighting rays: horizon #ffd98f → #7fb6c8.
  - At f216 both use sea's gradient, #ffbf7a → #24496b.
- **Mist:** bounded slab #f4e2c0, density 0.004 at the water (no world fog). Distance haze is #f4e2c0.
- **Materials:** water is lagoon green-teal. Floats and paddles are marigold #e2a03a.
- **Grade:** AgX Punchy, exposure 0.35 (→ 1.05 at f216).
  - Lift #3f6f9a at 0.02, gain #ffcf7a at 0.03.
  - Saturation 1.08, bloom 0.15, vignette 0.10.

## Sheet check
- The aerial moves over teal ponds, green and red-brown fields, and the casuarina belt.
- The low pass over the teal pond has a warm sun path and marigold-flecked aerators.
- The crew and tripod are lit warm on the horizon side, with cool teal shadows.
- f216 is a peach sunrise horizon under a blue zenith.
- No grey frames, pops or clipping.

## Luma (full frames, mean/sd)
| Frame | Luma |
|---|---|
| f1 | 122/29 |
| f22 (10 %) | 125/32 |
| f108 (50 %) | 185/48 |
| f160 | 132/58 |
| f194 (90 %) | 167/55 |
| f216 | 191/34 |

All ok.

## Bridges
- **BRIDGE_HORIZON:** SSIM of f216 vs sea/0001.png is 0.918. Sea is still brighter (224) with a whiter horizon glow, so it needs equalising.
- **BRIDGE_COAST:** SSIM of f1 vs truck/0216.png is 0.496 (it was 0.529 before the art pass). The layout matches; the colour now differs because pond is teal/green and truck has its own art-pass look. The lead equalises this frame. A dissolve over f1–4 is recommended.

## G-SCENE
| Gate | Result | Note |
|---|---|---|
| 1 Story beat reads | PASS | Aerial farm → pond → harvest crew → sunrise sea |
| 2 Not empty | PASS | Populated in every frame |
| 3 Not toy-like | PASS | Fields slightly saturated at f1–22 (minor) |
| 4 Not fake | PASS | Colour comes from light and sky, no overlay |
| 5 No clipping | PASS | Sheet and stills |
| 6 Scale / feet on ground | PASS | Unchanged from full-final |
| 7 Camera smooth | PASS | Unchanged path |
| 8 No colour overlay, vignette ≤ 12 % | PASS | Vignette 0.10, grade tints ≤ 0.03 |
| 9 Luma floor | PASS | Table above |
| 10 Type zone calm | PASS | Sky and water fill the top-left and right thirds |
| 11 Bridges | PASS* | *Exact frames left to the lead's equalising step |
| 12 Render budget | PASS | About 3.9 s/frame, ≤ 15 s |

## Known issues
- The aerial f1–22 frames are darker than before (122 vs 143). The old frames were lifted by grey haze. Both pass the gates.
- The far houses are simple (unchanged).
- The sea is static (unchanged).
