# truck art pass: final r6 (issue #75, COLOR_SCRIPT row 10 v-truck, complementary grade with a gold key)

Full render: assets-src/render/truck/0001-0216.png, 216/216 frames at 1920x1080, r6 re-render with FORCE=1, wall time 13 min (about 3.6 s per frame; the stills ran 3.0-4.7 s per frame).
Contact sheet: docs/renders/truck-art-sheet.jpg. Before/after: docs/renders/truck-before-after.jpg (rows f1, 22, 58, 108, 194, 216; before on the left).

Changes are listed in truck-art-r1..r4.md: sun #ffc98a, fill #8fb8e0, rim #ffd59a, sky tinted from horizon #ffd7a0 to zenith #5f93c8, warm material haze #e8d2b0 in place of the world fog (the world volume blacks out EEVEE), teal sea, warmer concrete, blue-white PUF walls, AgX Punchy. r5 and r6 changed only grade and light: lift #2f6f8a (0.012), gain #ffc98a (0.06, cap raised by the lead in r6), sun #ffb870 (r6, warmer than row 10's #ffc98a), sat 1.14, vignette 0.10, sun energy 7.5, exposure -0.3 at f1 (BRIDGE_DOCK), +0.6 at f18, +0.35 from f60 to f110, +0.3 at f190, +0.2 at f216. The r4 gold lift read as a sepia wash; r5 then read as cool teal. See truck-art-r5.md and truck-art-r6.md.

Luma (mean/sd) on the full frames: f1 70/44, f22 (10 %) 96/42, f58 111/34, f108 (50 %) 106/35, f194 (90 %) 96/31, f216 110/42. All ok.

| Gate | Result | Frames |
|---|---|---|
| G-SCENE-1 Realism | PASS | PBR and grime unchanged; light is now warm and directional |
| G-SCENE-2 Not toy-like | PASS | f90-f130 |
| G-SCENE-3 Busy | PASS | f90-f216 |
| G-SCENE-4 No clipping | PASS | sheet |
| G-SCENE-5 Water | PASS | f150-f216 |
| G-SCENE-8 No overlay, vignette ≤ 12 % | PASS | the grade is a colour balance, vignette 0.10 |
| Readability (luma) | PASS | see above |
| Rich colour, not grey | PASS | warm-gold facade, cab and fields against cool blue shadows, teal sea, gold-peach sun sheen |
| Speed ≤ 15 s/frame | PASS | about 3.6 s |

Known issues: there is no world volumetric fog (EEVEE limitation, same as sea). The box interior from f22 to f40 is now cool steel-blue and plain. f216 uses sun #ffb870 rather than the BRIDGE_COAST #ffc98a, so the lead's equalisation should take that into account.
