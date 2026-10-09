# pond.blend — review r1 (stills r0 + r1, 960x540 32 spp)

First impression: layout and camera move read correctly (coastal aerial -> descent over the pond grid -> low pass over water -> harvest on the sea bund -> sunrise horizon). r0 was washed out, land beige (leafy_grass scan is mostly dead leaves), no sun disc (EEVEE draws no sky sun disc), SE corner of the farm cut by the coast. r1 fixed those; remaining issues below.

| Gate | r1 | Notes / frames |
|---|---|---|
| G-SCENE-1 Realism | FAIL | f172: inner bund slope wet band too glossy (reads as silver scales); bund top orange (beach mask leaked onto the bund because the coast clipped it) |
| G-SCENE-2 Not toy-like | PASS | real scale (ponds 52x38 m, bunds 3-5 m, people 1.6-1.8 m) |
| G-SCENE-3 Busy | PASS | 16 near ponds + 33 far, 24 aerators, 80 palms + 245 grove, 32 trees, 115 shrubs, 3 sheds, bike, 12 sacks, 6 crates, 6 people, 6 egrets |
| G-SCENE-4 Clipping | PASS (visual) | crew stand on the pond bed; crates on the bund |
| G-SCENE-5 Water | FAIL | f110/f150 pond = pure sky mirror, no murk read; net bag hard to read at f172 |
| G-SCENE-6 People | FAIL | all shirts white -> uniform; faces ok at >= 6 m |
| G-SCENE-7 Shrimp | PASS | CC0 greasyback scan (unlabelled filler) in bag + crates |
| G-SCENE-8 Light | PASS | bright dawn, consistent sun az 90-95 |
| G-SCENE-9 Setting | PASS | Andhra coast, lungis, coconut palms, tin sheds |
| G-SCENE-10 Camera | PASS | f1 rot (55,0,-90) 24 mm; f216 (91.33,0,-95) 35 mm, 3 m |
| G-SCENE-11 Continuity | PASS (spec) | f216 horizon at 46 %, sun disc 4 deg in frame, ocean seed 41 |
| G-SCENE-12 Story | PASS | farm -> harvest -> sea |

Fixes queued for r2: green-tinted grass, embankment profile (bund no longer clipped), rougher/greener pond water, matte wet mud, thicker net + more shrimp, shirt/lungi colours, power line.
