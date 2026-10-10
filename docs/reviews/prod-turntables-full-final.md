# S10 product turntables: full render review (prod-tuna, prod-prawn)

Build: `assets-src/blender/build/prod_turntable_scene.py -- tuna|prawn|both [--stills <tag>]` builds `assets-src/blender/prod-tuna.blend` and `prod-prawn.blend`.
- Product: the live site GLBs, `assets-src/models/tuna.glb` / `prawn.glb`, unmodified.
- Plinth (A-PROD-PLINTH): a chipped, cloudy, wet ice slab with a crushed-ice bed on top. The bed is a height field ray-cast to the product's underside, so the product rests on ice and no chunk vertex rises above the product surface.
- Studio: Poly Haven `studio_small_09` (CC0) via `sklib.hdri`, plus 4 area lights and a dark slate sweep to match the B2 `sec-dark` section.
- Motion: one linear 360° turn. f1 = 0° and f121 = 360°, so the 120 frames loop.
- Render: `sklib.finish(name, 'ext')` (EEVEE, 1920×1080, 24 fps, AgX Medium High Contrast). After that the motion-blur shutter is set to 0.15 so the near end of the slab stays sharp.

Full render: 120/120 frames each, written to `assets-src/render/prod-tuna/` and `assets-src/render/prod-prawn/`.
- Render time: 5.6 s/frame (tuna) and 5.5 s/frame (prawn). The two renders ran at the same time, each took 11 min.
- Contact sheets: `docs/renders/prod-tuna-full-sheet.jpg`, `docs/renders/prod-prawn-full-sheet.jpg`.
- Self-review stills (0/90/180/270°, 1920×1080): `assets-src/blender/stills/prod-{tuna,prawn}/r1..r5-*.png`. r5 is final.

Luma (`luma.py`, all 240 frames): 0 FAIL. Typical frame: mean 113–116, sd 61–63.

## Gates
| Gate | tuna | prawn | Notes |
|---|---|---|---|
| G-PROD-2 photoreal at 100 % | PASS | PASS | No specks, holes or blotches. Eyes intact. Crushed ice reads as angular white or clear ice at 100 % (r5 crop). Remaining: a small dark hollow in the bed under the tuna's pelvic fin (side view around f61). The scan texture's softness is a property of the GLB, not this scene. |
| G-PROD-3 proportions | PASS | PASS | Shipped GLBs at true scale (tuna 1.19 m, prawn 0.25 m). Each scene is framed to its own product, so the relative scale between them is not visible in the clips. |
| G-PROD-4 all angles | PASS | PASS | The sheets cover every 30°. No floating (product rests on the ice bed), no clipping, no frame-edge cuts. The slab's near end stays inside the frame end-on. |
| G-SCENE-8 light | PASS | PASS | Studio key, fill and rim plus HDRI. No overlay, tint or vignette. Luma passes on every frame. |

## Known limits
- 16:9 mobile centre crop (about 32 % of the width): at side-on angles a centre crop shows only the middle of the body, because both products are long and thin. End-on angles fit fully. Use `object-position: center` or letterbox on mobile if the whole product must show.
- Frame 120 to frame 1 is a continuous 3° step, so the clip loops seamlessly.
