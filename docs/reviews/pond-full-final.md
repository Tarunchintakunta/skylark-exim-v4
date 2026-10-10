# pond.blend: full render, final review

Full render: 216/216 frames, 1920x1080, 32 spp, motion blur, AgX, in assets-src/render/pond/0001-0216.png. Wall time 42 min on the shared GPU (4-6 other renders running). Measured render time: 11.9 s/frame on average, 22.8 s at most (f40-180 low pass). Contact sheet: docs/renders/pond-full-sheet.jpg.

Sheet check: aerial over the field patchwork, coconut rows and hamlets, with long aerator wakes in every pond. Then the low pass over murky, rippled green water with aerators churning, the harvest crew with the seine float line in the water, the bag lift, and the f216 sea horizon. I saw no clipping, pops or uniform frames.

Luma (full frames): f1 136/22, f22 139/25, f108 186/47, f194 180/53, f216 203/27. All ok.

Gates: same as pond-full-r1.md. All PASS. Minor points: the far houses are simple, and the pullers stand a little stiffly.

Continuity WARNING (BRIDGE_COAST): truck f216 (assets-src/render/truck/0216.png) has the coast about 250 m closer and diagonal, with a beach, a casuarina belt, a road and a plantation. Pond f1-f2 still use the old layout: the shoreline runs across at about 1/3 frame height and there is no beach or casuarina belt. If the lead swaps truck f216 into pond f1, the cut to pond f2 will jump. Fix: rebuild pond's coast to match truck, then re-render roughly f1-45. That range is the aerial and renders at about 7 s/frame.

Known: the sea is static. The ocean time driver clamps to 0 across the whole shot, which f216 needs for the bridge, so I left it.

## Round 2: BRIDGE_COAST matched to truck f216 (lead request)
Truck's f216 camera (260, -110, 300) maps onto ours (-560, -60, 300), so truck's coast x = 900 + 0.5y becomes x = 55 + 0.5y here.
- **Coast:** pond.py `shore_x` now follows that diagonal everywhere except a window around the farm (`coast_b`: y -60..10 kept, blended out by y = 170 / -160). The end shot (f150-216) and BRIDGE_HORIZON need open sea right off the east bund, so the farm keeps its old shoreline. I worked out the f216 frustum: no land enters it.
- **Added, as in truck:**
  - an 80 m pale sand beach, with 4 broken surf bands;
  - a 5-row casuarina shelter belt (1156 trees, dark cones);
  - an asphalt farm road with gravel shoulders (truck has it at y -10; here it is at y -45, south of the shed and bike);
  - a coconut orchard south of the road (179 palms).
- **Fields:** smaller fields (28 x 40 m), with more red-brown bare plots.
- **Rendered:** all 216 frames again (FORCE=1, 40 min, 11.1 s/frame on average, 20.6 s at most).
  - The changed coast, road and casuarinas are visible in every frame up to f194, so re-rendering only f1-45 would have caused a pop.
  - The new casuarina belt now shows behind the crew in f160-190.
- **Checks:**
  - f216 is pixel-identical to round 1 (SSIM 1.000), so BRIDGE_HORIZON is unchanged.
  - f172 vs round 1: SSIM 0.92 (only the background trees changed).
  - Frame-to-frame continuity f1 -> f2: SSIM 0.985.
- **SSIM of new f1 vs truck/0216.png: 0.529** (it was 0.545 before). The structure now matches: diagonal coast, beach + casuarina belt top-left and right, road, orchard right of the road, pond grid left. The number did not go up because SSIM here is dominated by texture and colour differences:
  - truck's sea is brighter and lighter blue;
  - its fields are smaller and redder;
  - its ponds are teal;
  - there is a ~65 m "bay" where our farm keeps its shoreline.
  - Expect a visible but not structural change if truck 0216 replaces our f1. A short cross-dissolve over f1-4 at the equalising step would hide it.
- **Luma:** f1 137/23, f22 139/26, f108 186/47, f194 180/53, f216 203/27 (all ok).
