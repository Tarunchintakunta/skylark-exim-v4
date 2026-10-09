# pond.blend — review r2 (preview docs/renders/pond-preview.mp4 + pond-sheet.jpg, 960x540 16 spp STEP 2)

First impression: reads as a real coastal Andhra shrimp farm at sunrise: green land with field patchwork, 16-pond grid + far pond blocks, sea on the right/far, palms/neem/casuarina, power line, sheds; low pass over mirror-calm ponds with mist and running aerators; harvest crew on the sea bund; ends on a clean sunrise horizon with the sun disc.

| Gate | r2 | Notes / frames |
|---|---|---|
| G-SCENE-1 Realism | PASS (minor) | PBR scans on terrain (leafy_grass tinted, brown_mud_03, muddy_tracks, grass_path_2, damp_sand, mud_cracked_dry_03), bark, tin roof, brick, crates; leaves/foam/mist procedural (organic, not hard surface) |
| G-SCENE-2 Not toy-like | PASS | real scale, bevels on props |
| G-SCENE-3 Busy | PASS | >=12 ponds (16 + 33 far), 24 aerators, 81 palms (6 variants) + 245 grove (LOD), 32 trees, 115 shrubs, grass tufts, 3 sheds, bike, 12 sacks, 6 crates, 6 people, 6 egrets, power line |
| G-SCENE-4 Clipping | PASS (visual) | crew feet on the sloped pond bed (under murky water) |
| G-SCENE-5 Water | PASS (minor) | foam only on pond water inside each pond; drips are particles; ponds read as mirror-calm at grazing angle (murk only visible near the crew) |
| G-SCENE-6 People | PASS (minor) | MPFB, varied age/skin/build, recoloured shirts, plaid lungi on P2; faces >= 6 m from camera |
| G-SCENE-7 Shrimp | PASS | CC0 greasyback scan in bag + 4 crates on ice |
| G-SCENE-8 Light | PASS | bright warm dawn, sun az 90->95, elev 15->4 (bridge specs) |
| G-SCENE-9 Setting | PASS | |
| G-SCENE-10 Camera | PASS (minor) | f188-216 pan to the sea is quick (~14 m in 28 frames) |
| G-SCENE-11 Continuity | PASS (spec) | f1 = BRIDGE_COAST (rot 55/0/-90, 24 mm, 300 m), f216 = BRIDGE_HORIZON (35 mm, 3 m, rot 91.33/0/-95, horizon 46 %, sun disc 4 deg) |
| G-SCENE-12 Story | PASS | |

Known: net bag reads as a pale sack more than a mesh net at preview size; ponds mirror the sky more than they show green murk.
Perf: r2 full frame 99.9 s (f172, incl. shader compile) -> r3 cut grass tufts to the camera corridor, LOD grove palms, decimated shrimp (18.4M -> ~7M tris), volumetrics end 60 m tile 16.
