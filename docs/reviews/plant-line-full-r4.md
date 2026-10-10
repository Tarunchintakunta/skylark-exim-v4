# plant-line full-render round r4 (stills: assets-src/blender/stills/plant-line/pl_r4c_f*.png, pl_r4d_f*.png; 1920x1080, .blend settings)

First impression: now reads as a real working plant photographed under LED light, not a white CG void. Grey-white PUF walls with seams and grime, darker epoxy floor, stainless reads as metal, people stand out from the walls.

## Root causes found and fixed
- **Washed-out white:** EEVEE had no baked volume probe, so the closed interior was ambient-lit by the sky world (plus a bright below-horizon ground colour). Lowering lights barely moved luma. Fix: world strength keyed 0.06 inside (f1-640), easing back to the sky_world default 0.3 by f740 as the camera reaches the open dock. Also AgX Medium High Contrast (set after sklib.finish), darker wall/floor/lab albedos and more wear.
- **QC technician in jeans and orange shoes:** people.py `lab_coat` = street trousers + shoes. Runtime patch (lib untouched): `lab_coat` now uses the ppe_plant clothes minus the apron. White trousers, white gumboots, white coat to the knee, hairnet, mask, blue gloves.
- **Blank frames at v-qc 10 % / v-grade 10 %:** camera re-planned. f1-64 is a slow tilt up from the belt (f20 = belt rows of shrimp, little blur). f172-205 frames the technician 3/4 from behind at mid distance with bench, balance, lamp and glassware, backing out. The turn to the grading hall now happens through the east door f205-245 (f211 = technician + bench).
- **Frame time (r3 ~65-100 s):** (1) people.py stacks re-solidified and re-decimated every person on every frame, three times with motion blur. All non-armature modifiers are now baked in rest pose (vertex groups kept), giving a per-frame floor of 18 s -> 3.6 s. (2) Automatic frustum culling (`auto_vis`) keys hide_render for every mesh, instance, light and probe outside the widened camera frustum: 3.7k keys, sampled every 3 frames, dilated one sample, merged with the existing keys. (3) 22 hall area lights replaced by 8 large ones, shadowless outside the lab zone; the battens stay emissive. (4) Sun only from f590 (dock end). (5) Ice-bed chunks 2500 -> 1000 per segment (larger chunks, same look). (6) 24 spp: compared with 32 and 16 at f480, no visible noise difference.

## Luma (r4c full-res, 32 spp; f20 from r4d)
f1 168/16 · f20 189/20 · f96 149/23 · f173 172/30 · f192 172/29 · f211 174/26 · f287 138/34 · f364 138/29 · f402 136/28 · f478 151/30 · f555 143/31 · f593 144/26 · f669 153/40 · f746 160/58 · f765 158/61. All ok.

## Four questions
Empty? No. Toy-like? Coat hems still look a bit fluffy (people.py shell), acceptable at distance. Fake? Belt macro still slightly graphic. Clipping? None seen; the camera passes the lab east door with about 0.45 m clearance.

| Gate | r4 | Notes |
|---|---|---|
| G-SCENE-1 Realism | PASS | PBR + grime on every hard surface; darker albedos read less CG |
| G-SCENE-2 Not toy-like | PASS (minor) | coat hem fluff (lib) |
| G-SCENE-3 Busy | PASS | 1 tech, 6 grading, 24 peeling, 3 receiving (f478: 18+ in frame) |
| G-SCENE-4 Clipping | PASS (eyeballed) | f205-245 door pass checked on f211 |
| G-SCENE-5 Water | PASS | f669 tank, stream inside tank, overflow to gutter |
| G-SCENE-6 People | PASS | technician now full PPE (f173/f192/f211) |
| G-SCENE-7 Shrimp | PASS | CC0 scans only |
| G-SCENE-8 Light | PASS | no overlay; contrast restored; means 136-189 |
| G-SCENE-9 Setting | PASS | no text |
| G-SCENE-10 Camera | PASS | slower opening tilt; lab exit turn about 90 deg over 40 f |
| G-SCENE-11 Continuity | for lead | BRIDGE_BELT f1 now darker/contrastier than r3 (world ambient + look); BRIDGE_DOCK f765 world back at 0.3, exposure -0.3, sun 20/100 |
| G-SCENE-12 Story | PASS | |

Frame time (shared GPU, 2-3 other renders running): peel hall steady state 13-14 s; lab 6-10 s; grader/wash 10-15 s.
