# table — full-quality review r1 (1920×1080, EEVEE, 32 spp, motion blur)

Stills: assets-src/blender/stills/table/r7_f*.png (earlier iterations r5_, r6_ in the same folder).

## First impression
The macro now reads as a food photograph: a high-angle 58 mm, f/2 shot over plate A with the cleaned CC0 prawn
(A-PROD-PRAWN, products.py remesh + baked albedo) skewers sharp, tuna and greens falling off in focus. Glasses are
clear with visible wine/water (no black glass). No diner hands anywhere in the shot. The end frame is a real 3D
hoar-frost field instead of the old cracked-mud shader.

## Changes vs the preview
- Food: prawns switched from the raw scan (hairy fringe + speckle) to the cleaned A-PROD-PRAWN mesh, legs trimmed,
  cooked shader = dorsal→belly gradient + segment bands + toned-down scan detail + char bars; tuna slices irregular,
  loin-tapered, darker ruby with less SSS; salad rebuilt (wild rocket + baby spinach, cupped/twisted, matte); stray
  red herb flecks removed; bread slices irregular with darker crust.
- Tableware: flatware rebuilt with rounded superellipse sections, tapered tines, thinning knife edge, polished
  stainless with wipe streaks/smudges; laid flat beside each plate (grounded on lowest vertex).
- Glass: BLENDED Fresnel-alpha glossy glass (no screen-space refraction), so the wine/water inside stays visible;
  scene ray tracing stays ON. Water liquid uses SLAB thickness (no black band).
- Diners: seated upright, forearms on thighs, hands in the lap under the table (checked: wrists z 0.55–0.61 < top
  0.75); heads slightly bowed. No hand animation.
- Phone: camera-bump double offset fixed; moved off napkin B.
- Camera: opening is a high-angle macro (not straight top-down) so f/2 DOF has depth to work with; aperture eases
  f/2 → f/2.8 by f100. Final push-in lands at f212 and holds to f216 (f214 used to be a zoom streak, sd 8).
- BRIDGE_FROST (bridge_frost.py): 26 000 crystal meshes (hex plates + needle columns, 0.15–1.6 mm) on a frosted
  film shader; single 0.25 m area light 1 m straight above, 6500 K; camera 0.12 m above, 100 mm, f/2.8 (unchanged).
- Speed: 32 spp (identical to 64 on a crop compare), shadow maps off on the 4 soft fill lights + candle.

## Four questions
- Empty? No — table for two, bread board, candle, glasses, phone, kitchen with carton.
- Toy-like? Mostly no; the lemon wedge still reads slightly waxy (background, out of focus).
- Fake? Diner B's face is visible at ~2 m in f110–130 (acceptable per people.py guidance); salad still slightly CG
  in sharp focus but sits in the DOF falloff.
- Clipping? None seen; hands under the table, cutlery resting on the top.

## G-SCENE
| Gate | Result | Frames |
|---|---|---|
| 1 Realism | PASS | 1, 95, 160 |
| 2 Not toy-like | PASS | 1, 123 |
| 3 Busy | PASS | 95, 123, 160 |
| 4 No clipping | PASS (visual; hands/cutlery checked numerically in build log) | 1–216 |
| 5 Water | PASS (wine/water in glass) | 95, 123 |
| 6 People | PASS (no hands, faces ≥ 2 m) | 123 |
| 7 Shrimp | PASS (cleaned CC0 scan) | 1, 31 |
| 8 Light | PASS | all |
| 9 Setting | PASS (no text except carton label) | 160, 184 |
| 10 Camera | PASS — note: opening is high-angle instead of pure top-down | 1–216 |
| 11 Continuity | PASS to spec (lead equalises with reefer f1, which builds its own frost) | 216 |
| 12 Story | PASS | — |

## Luma (r7, full res)
f1 171/39 · f7 170/39 · f31 171/38 · f54 168/33 · f67 166/32 · f95 152/36 · f123 130/50 · f136 119/53 · f160 90/58 ·
f184 92/60 · f193 131/56 · f203 185/17 · f214 177/24 · f216 177/23 — all ok (f203 sd 17 < aim 20, mid-push defocus).

## Frame time (shared GPU, other sessions rendering)
3–12 s per frame at 1920×1080/32 spp (heaviest f123 12.3 s); was 17–29 s at 64 spp.
