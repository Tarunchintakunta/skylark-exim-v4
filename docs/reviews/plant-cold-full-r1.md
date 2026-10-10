# plant-cold full r1 (1920x1080 stills f1 20 96 173 192 211 288 364 383 402 479 555 574)
First impression (preview before fixes): believable plant, but washed-out white; f211 stared at a blank PUF wall (luma 195/10 FAIL); f574 top-down belt nearly white (236/13).

Fixes this round
- Contrast: AgX Medium High Contrast (own override of sklib.LOOKS in the build script), interior area lights x0.6, world fill 0.35->0.2, PUF albedo 0.80->0.66 with grime/streaks, cold floor 0.58->0.40, packing floor darker green-grey epoxy.
- Camera f150-230 re-planned: f192 'high view' lowered to 4.8 m looking down the aisle at the glazed door, new key f211 2-3 m from the opening so the packing hall (PPE staff, tables, cartons) fills the doorway; yellow frosted bollards + threshold at the door.
- Faces: carrier P-PLANT-1 turned away from the camera (-x); close packing frames crop heads at the top edge; faces only at >= 3.5-4 m.
- Mist/vapour densities halved (door 0.12->0.07, IQF 0.3/0.22->0.16/0.12).
- BRIDGE_BELT moved to x=-47.4 (out of the mouth vapour), belt albedo darker, exposure ramps 0 -> -1.9 over f520-574 (the frame-filling belt under four hall lights clipped at mean 243 even with lights soloed).
- Perf: 32 spp, volumetric 16 samples, shadow_resolution_scale 0.25 (shadow maps over 442 pallets were ~half the frame; A/B crops identical).

| Gate | Result | Notes |
|---|---|---|
| G-SCENE-1 Realism | PASS | PBR + grime on walls/floor/racks; frost on cold surfaces only |
| G-SCENE-2 Not toy-like | PASS (watch) | reach truck chassis boxy but bevelled, at distance |
| G-SCENE-3 Busy | PASS | 442 pallets, 10 bays x 5 levels, 10 PPE staff + operator |
| G-SCENE-4 Clipping | PASS | no intersections seen in stills |
| G-SCENE-5 Water | PASS | spray falls down; vapour reduced; wet floor only near IQF |
| G-SCENE-6 People | PASS | full PPE; no close faces (f288 faces ~4 m, f364/383 heads cropped) |
| G-SCENE-7 Shrimp | PASS (watch) | CC0 scans; on the f574 top-down the pale scans read faintly through the mesh pattern |
| G-SCENE-8 Light | PASS | luma all ok, no overlay |
| G-SCENE-9 Setting | PASS | only allowed text |
| G-SCENE-10 Camera | PASS | f211 now frames the hall through the door |
| G-SCENE-11 Continuity | PASS f1 / NOTE f574 | BRIDGE_BELT exposure/position changed: lead must re-equalise plant-line f1 |
| G-SCENE-12 Story | PASS | cold store -> packing -> IQF read at a glance |
Four questions: empty? no. toy-like? no. fake? shrimp scans pale on the top-down (minor). clipping? no.
