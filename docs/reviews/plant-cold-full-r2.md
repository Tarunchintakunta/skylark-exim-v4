# plant-cold full r2 (1920x1080, saved settings; stills 1 20 96 173 192 211 288 364 383 402 479 510 545 555 565 574)
First impression: reads as a real, working plant now: grey-white PUF with grime, darker epoxy floors, blue/orange racks, PPE staff, stainless line; no blank frames.

Changes since r1
- Final approach re-planned: f520 arcs over (not through) the glazing spray bar (>= 0.5 m clearance checked every 4 frames), f540 hovers over the infeed looking into the tunnel mouth, eases to the BRIDGE_BELT top-down at f574.
- Focus keyed every 3 frames f522-574 to where the view axis meets the belt (f545-570 were defocused smears).
- Motion blur shutter keyed 0.5 -> 0 from f506 (EEVEE blur on GN-scrolled shrimp instances rendered 'barcode' smears; blur stays on through the glazing spray f440-505).
- Door haze: mist 0.07 -> 0.04, PVC strip alpha 0.16 -> 0.11 (f20 sd 12 -> 15).
- Perf: 32 spp + shadow_resolution_scale 0.25 + volumetric 16 samples.

Luma (mean/sd): f1 202/21, f20 189/15, f96 135/48, f173 135/34, f192 143/33, f211 163/23, f288 163/33, f364 168/56, f383 174/52, f402 148/53, f479 151/42, f555 130/43, f574 169/20 -> all ok.
Frame time (full res, 32 spp, 5-8 other Blender renders sharing the GPU): 7-21 s, median ~10 s; heaviest = cold-store aisle/door f20-f192 (~13-21 s).

| Gate | Result | Notes |
|---|---|---|
| G-SCENE-1 Realism | PASS | PBR + grime everywhere; IQF housing frost still a little blotchy (f545 top edge) |
| G-SCENE-2 Not toy-like | PASS (watch) | reach truck boxy but bevelled, mid-distance |
| G-SCENE-3 Busy | PASS | 442 pallets, 10 bays x 5 levels, 10 PPE staff + operator |
| G-SCENE-4 Clipping | PASS | camera path checked vs spray bar; door pass inside the opening |
| G-SCENE-5 Water | PASS | spray falls; wet floor near IQF only; vapour thinner |
| G-SCENE-6 People | PASS | faces >= ~3.5 m or cropped (f364/383); carrier turned away |
| G-SCENE-7 Shrimp | PASS | CC0 scans in rows; top-down readable at f574 |
| G-SCENE-8 Light | PASS | all ok; exposure eases to -1.9 over f520-574 (frame-filling metal belt) |
| G-SCENE-9 Setting | PASS | only allowed text |
| G-SCENE-10 Camera | PASS | continuous; f192-230 door approach frames the hall |
| G-SCENE-11 Continuity | PASS f1 / NOTE f574 | BRIDGE_BELT now at x=-47.4 with exposure -1.9: lead must re-equalise plant-line f1 |
| G-SCENE-12 Story | PASS | |
Four questions: empty? no. toy-like? no. fake? no (spray droplets f506+ unblurred, small). clipping? no.
