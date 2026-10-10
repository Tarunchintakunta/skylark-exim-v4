# sea.blend (v-sea, f1-264, dawn): full-res review r1

The stills are full res (1920x1080, EEVEE 64 spp, AgX, motion blur, from the .blend's saved settings) at f1, 27, 132, 185, 200, 238 and 264, in assets-src/blender/stills/sea/fullr1_*.png. The scene has a single chapter, so f27, f132 and f238 are its 10 %, 50 % and 90 % frames.

**First impression:** this is the r4 scene, unchanged and still strong. A dawn horizon becomes a blue/white/red trawler with the dripping cod-end, then the gloved sorter over skipjack and prawns on ice, then the crew at the rail with the headland behind.

**The defect I found at full res:** the reflections of the tyre fenders in the sea showed as bright white rings at f264 (also visible around f60-90 in the preview). Cause: the screen-trace thickness was 0.1, so reflection rays missed the tyre undersides and fell back to the sky. I tested three fixes on f264 and f132:
- thickness 2.0 removed the rings but smeared the hull and crew reflections (f60, f132), so I rejected it.
- turning off `visible_glossy` on the tyres had no effect.
- **thickness 0.5 fixed the rings with no smearing.** I applied it to the .blend and to build/sea.py (line after `motion_blur_shutter`).

I did not rebuild anything else.

The four questions:
- **Empty?** No.
- **Toy-like?** Mostly not. The wheelhouse is a simple box.
- **Fake?** No longer, now that the tyre reflection fix is in.
- **Clipping?** None seen.

| Gate | Result | Frames |
|---|---|---|
| G-SCENE-1 Realism | PASS | 132, 200, 264 |
| G-SCENE-2 Not toy-like | PASS (minor: plain wheelhouse) | 264 |
| G-SCENE-3 Busy | PASS | 132, 238, 264 |
| G-SCENE-4 No clipping | PASS (visual). At f185 the net passes close to the lens, soft and out of focus | 185 |
| G-SCENE-5 Water | PASS after the fix (tyre reflections) | 132, 264 |
| G-SCENE-6 People | PASS (faces at mid distance) | 238, 264 |
| G-SCENE-7 Fish | PASS (ffish.asia CC0 scans) | 200 |
| G-SCENE-8 Light | PASS. The dawn sky is pale peach | 1, 27 |
| G-SCENE-9 Setting | PASS | 264 |
| G-SCENE-10 Camera | PASS | path unchanged |
| G-SCENE-11 Continuity | f1 = BRIDGE_HORIZON, unchanged | 1 |
| G-SCENE-12 Story | PASS | 200, 264 |

Luma (mean / sd), all `ok`:

| Frame | Mean | SD |
|---|---|---|
| f1 | 224 | 19 |
| f27 | 223 | 21 |
| f132 | 133 | 48 |
| f185 | 123 | 35 |
| f200 | 115 | 42 |
| f238 | 139 | 55 |
| f264 | 166 | 77 |

Frame time is about 5-7 s/frame on the shared GPU. Spikes reach 9-15 s when other jobs contend for it.
