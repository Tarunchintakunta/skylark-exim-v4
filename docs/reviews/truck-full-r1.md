# truck.blend — full-render review r1 (stills r4/r5 @ 1920x1080, .blend settings)

Stills: assets-src/blender/stills/truck/r4_f001/022/060_full.png, r5_f090/108/150/175/194/216_full.png.

**First impression.** The city-builder look is mostly gone. The f216 aerial is now clearly a coast: a beach with surf lines, a turquoise-to-deep-blue sea with swell and a sun sheen, a casuarina shelter belt, and boats on the sand and at sea. The fields are now rectangular plots in rotated land holdings instead of voronoi hexes. The yard is busier: a second reefer waiting at the west dock, nine people, crate stacks, blue fish iceboxes, a hose to the drain, wet patches, dust, weeds and saw-cut joints. The cab is a lofted, rounded cab-over with a wrap-around windscreen, a black fascia and grille with chrome bars, corner lamps, a bumper with fog lamps, a blank yellow plate, mirrors on arms, grab rails and tyres with tread. The box now has panel joints, red/white side tape and amber markers.

Four questions
- Empty? No. The yard has 9 people, 3 reefers, stacks and props; the aerial has orchards, groves, villages, ponds, a road with traffic, a beach and boats.
- Toy-like? Less than before. The forklift was removed because it read as a toy. Mid-distance broadleaf trees still read slightly "broccoli" at f150 → fixed in r2: lower, fuller and darker crowns, plus clumpy foliage shading.
- Fake? Some ponds near the sun glared white at f194, and the canopy shader looked like bubble wrap near the coast → r2: rougher pond water, half the canopy bump.
- Clipping? A pond block touched the yard wall at f150 → r2: pond blocks are kept clear of the yard and the road.

| Gate | r1 | Notes (frames) |
|---|---|---|
| G-SCENE-1 Realism | PASS | PBR + grime on truck, yard, walls; new land shader, sea, beach, pond water |
| G-SCENE-2 Not toy-like | PASS (r2 tree fix) | lofted cab with bevels (f90, f108); forklift removed; trees f150 → r2 |
| G-SCENE-3 Busy | PASS | f90/f108 yard; f216 coast with orchards, villages, boats |
| G-SCENE-4 No clipping | FAIL→r2 | pond block on the yard wall (f150) |
| G-SCENE-5 Water | PASS | sea sheen is broken by swell normals; foam stays in the surf zone; pond glare reduced in r2 |
| G-SCENE-6 People | PASS | 9 MPFB people, mid-distance |
| G-SCENE-7 Fish | PASS | prawn scans on ice (f1–f22) |
| G-SCENE-8 Light | PASS | luma ok on every still (mean 109–142, sd 27–53) |
| G-SCENE-9 Setting | PASS | Indian cab-over, blank yellow plate, LHT road, casuarina coast, FRP boats |
| G-SCENE-10 Camera | PASS (r2) | the f150–216 climb now turns steadily toward the coast; shutter 0.3 → 0.15 on the climb |
| G-SCENE-11 Continuity | n/a | BRIDGE_COAST at f216 is to spec (300 m, 24 mm, pitch −35°, heading east, sun 15°/90°); pond.blend f1 needs re-equalising |
| G-SCENE-12 Story | PASS | |

Frame time after the optimisation (32 samples, shadow resolution 0.5, shutter 0.3, aerial-only groves/villages off in the yard, cargo/bay/people off after the climb), with 2 other renders on the GPU: f90 10.5 s, f108 8.3 s, f150 8.0 s, f175 6.6 s, f194 6.0 s, f216 6.8 s. Before: f90 26.8 s, f150 23.1 s.
