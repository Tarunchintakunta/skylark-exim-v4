# plant-line full render — final (r4 build, 765/765 frames, assets-src/render/plant-line/0001-0765.png)

Sheet: docs/renders/plant-line-full-sheet.jpg. Wall time: 150 min on the shared GPU (2–4 other renders running), about 11.8 s per frame on average. The heaviest part (the peel hall) runs at about 13–14 s per frame, measured steady-state.

First impression: a real, lived-in processing plant. Contrast is back, the technician is in full PPE, and every chapter frames working content.

Luma (mean/sd) per chapter at 10/50/90 %:
- v-qc: f20 189/20, f96 150/23, f173 172/30
- v-grade: f211 174/26, f287 138/34, f364 138/29
- v-peel: f402 136/28, f478 151/30, f555 143/31
- v-wash: f593 144/26, f669 154/39, f746 161/58
- Boundary frames: f1 168/16, f192 172/29, f383 134/29, f574 138/34, f765 158/61

All frames pass.

Gates: G-SCENE-1..10 and 12 PASS (details in plant-line-full-r4.md). G-SCENE-11 is for the lead:
- BRIDGE_BELT f1 vs plant-cold/0574.png: SSIM 0.019. Exposure matches (luma 168 vs 169). The mismatch is in the geometry: plant-cold's frame has its shrimp rows running horizontally (it is rotated 90° against this f1, which follows the spec rotation (0,0,−90°)). It also has a different mesh-belt pattern, a left-dark gradient and motion blur.
- BRIDGE_DOCK f765 is built to spec.

Known issues:
- The coat hems look fluffy (comes from the people.py shell).
- The camera exit through the lab door (about f240–260) has strong motion blur.
- The belt macro still looks slightly graphic.

---
# Round 5: matching BRIDGE_BELT to plant-cold's rendered f574 (lead decision: plant-cold's frame wins)

## What changed (assets-src/blender/build/plant-line.py, rebuilt; re-rendered f1–360)
- **Camera at f1:** roll is now (0, 0, +90°), the same as plant-cold. Shrimp rows run horizontally, and the belt moves toward the top of the image (into the freezer). The roll eases back to the r4 path by f64 (about 123° spread over 64 frames). Low-res SSIM between consecutive frames stays between 0.51 and 0.87, with no steps.
- **Belt:** a direct port of plant-cold's balanced-weave mesh belt material.
  - The weave phase is matched: UV mapping offset 0.65 at f1, with the texture moving at plant-cold's 0.10 m/s. BELT_V is now −0.10 (was −0.06).
  - The belt is now a single plane. The old box's mirrored bottom-face UV had laid a second weave over the first, which showed as triangles.
  - A lit stainless bed sits under the mesh, so the holes read light, as in plant-cold's frame.
- **Shrimp:** plant-cold's own scans, raw-shrimp material and Random(574) row layout (9 across, every 0.12 m, lying across the belt). They are tiled over our belt, with f1 aligned to plant-cold's camera point. Every shrimp lands in the same place as in their frame.
- **Light and exposure at the join:**
  - Plant-cold's six lights around its bridge (offsets taken from plant-cold.blend at f574) fade out over f1–40.
  - Our L_belt and the two nearest hall lights fade in over the same frames.
  - World ambient goes from 0.3 at f1 down to 0.06 by f40.
  - Exposure goes from −2.1 at f1 to 0 by f40.
  - Motion-blur shutter goes from 0 at f1 to 0.5 by f30 (plant-cold renders its join frame without blur).

## Measurements
- **New f1 vs plant-cold/0574.png:** full-res SSIM **0.959** (r4 was 0.019). Luma 174/19 vs 169/20.
  - The left-to-right gradient is only approximate. The remaining difference is the soft brightness falloff at the frame edges.
- **plant-cold f574 → our f2:** full-res SSIM 0.021, low-res 0.779.
  - Full-res SSIM is not meaningful here. The fine weave moves about 8 px per frame, so even plant-cold's own f573→f574 scores only 0.223 at full res (0.646 low-res).
- **f1 → f2:** full 0.016, low 0.880.
- **f24 → f25:** full 0.703, low 0.763.
- **Seam at f360 → f361 (new → untouched r4 frames):**
  - New f360 vs the r4 f360: 0.999.
  - f360→f361 scores 0.643, the same as the ordinary step f359→f360 (0.646).
  - So there is no pop where the re-rendered range meets the r4 frames.

## Luma after re-render
f1 174/19 · f20 204/22 · f96 150/23 · f173 172/30 · f192 172/29 · f211 174/26 · f287 138/34 · f354 140/30. All pass. Frames 361–765 are unchanged from r4.

## Known issues (round 5)
- Brightness rises then falls over the opening: luma goes 174 → 204 → 157 between f1 and f40, while the bridge rig, world and exposure cross-fade. The change is smooth but visible.
- Around f36–50 the camera faces mostly floor and belt guard, with motion blur, while the roll unwinds. That stretch still shows real content (sd 36–38).
- The shared frame still differs slightly in edge gradient (SSIM 0.959).

Frames: 765/765. Re-render of f1–360 took 43 min (about 7 s per frame).
