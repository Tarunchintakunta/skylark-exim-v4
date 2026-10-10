# A-PROD-SWORDFISH — final review (4 rounds) — **FAIL → keep swordfish as a text entry**

Build: `assets-src/blender/build/swordfish.py` (procedural, no scans / AI / stock). Lofted body (superellipse sections, flat lens-edged bill, lateral caudal keel), 7 solid tapered fins from 2-D outlines (constrained Delaunay), 2 eyeballs; 51k tris. Position/normal/fin-coordinate maps baked to UV, albedo + height + rough/metal painted in numpy; height -> tangent normal map in numpy. T = 2.30 m.

Outputs: `assets-src/models/swordfish.glb` (1.78 MB, 2K maps), `assets-src/models/swordfish-web.glb` (340 KB, EXT_meshopt_compression, WebP 1024², KHR_mesh_quantization, KHR_materials_clearcoat). Not written to public/.
Evidence: `docs/renders/swordfish-turntable-sheet.jpg` (web GLB, 0/90/180/270°, studio_small_09, 1920×1080 stills in `assets-src/blender/stills/swordfish/web-*.jpg`); rounds r1–r4 in the same folder.

| Gate | Result | Evidence |
|---|---|---|
| G-PROD-1 | PASS (technical) | 340 KB ≤ 500 KB, meshopt present, 3 × WebP 1024² |
| G-PROD-2 | **FAIL** | No holes/specks/ragged fins/red blotches; eyes intact. But at 100 % it reads as a clean CG render, not a photo: airbrushed-smooth symmetric skin (myomere/denticle detail mostly lost at 1024²), fins uniform near-black with hard intersection seams at every root (no fillet), caudal reads as a black blade stuck onto a grey peduncle, eye is a glossy bead. |
| G-PROD-3 | PASS | Bill ≈ 0.27 T beyond lower jaw (≈ ⅓ of body), tall rigid falcate 1st dorsal over the gill cover, tiny 2nd dorsal/2nd anal near the keel, falcate 1st anal, no pelvics, low long pectorals, deep lunate caudal with keeled peduncle, max depth 0.14 T, round→keel cross-section. |
| G-PROD-4 | **FAIL** | Consistent from all four angles (no broken geometry, head-on egg section + flat broad bill read correctly), but the same CG look as G-PROD-2 at every angle. |
| G-PROD-5 | n/a | Fully procedural; only the existing CC0 studio_small_09 HDRI used for review. |

Rounds: r1 plastic black (coat too high, normal map flat — image bump does not bake); r2 baked attribute maps clamped negatives (fixed with +10 offset), numpy normal map; r3 UV layout (body locked, fins packed around it), fin-ray patches overlapping body fixed, gill/mouth grooves, eye; r4 tail junction, softer keel, denticles, roughness breakup, colour contrast. Remaining gap to photoreal needs sculpted fin-root fillets, a hand-sculpted head/eye socket and photographic skin detail — beyond a procedural build.

Decision: prod-swordfish.blend / full render **not built** (gated on PASS). Site keeps swordfish as a text entry.
