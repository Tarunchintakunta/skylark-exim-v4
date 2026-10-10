# sea.blend (v-sea, f1-264, dawn): full render, final review

The full render is complete: 264/264 frames in assets-src/render/sea/0001-0264.png at 1920x1080, EEVEE 64 spp, AgX, motion blur (shutter 0.3), from the .blend's saved settings. It took 37 min of wall time, about 8.4 s/frame on the shared GPU (a quiet GPU gives 5-7 s/frame). The contact sheet is docs/renders/sea-full-sheet.jpg.

**The one change since r4:** I raised the EEVEE screen-trace thickness from 0.1 to 0.5, in the .blend and in build/sea.py. At full res the tyre fenders reflected in the sea as white rings (sky fallback), visible at f264 and in the f60-90 approach. Thickness 2.0 smeared the hull and crew reflections, and turning off the tyres' visible_glossy had no effect. Nothing else was rebuilt, and the camera path, bridge frame and frame range are unchanged.

**Checks:** I looked at the full sheet and at frames 150 and 264. The tyre rings are gone, the reflections are clean, the drips are present and the crew reads well.

| Gate | Result | Frames |
|---|---|---|
| G-SCENE-1 Realism | PASS | 132, 200, 264 |
| G-SCENE-2 Not toy-like | PASS (minor: plain wheelhouse box) | 264 |
| G-SCENE-3 Busy | PASS | 132, 238, 264 |
| G-SCENE-4 No clipping | PASS (visual). At f178-196 the net/bag passes close to the lens, soft and out of focus | 185 |
| G-SCENE-5 Water | PASS (tyre reflection fix) | 66-90, 264 |
| G-SCENE-6 People | PASS (faces at mid distance) | 238, 264 |
| G-SCENE-7 Fish | PASS | 200 |
| G-SCENE-8 Light | PASS (pale peach dawn rather than deep marigold) | 1, 27 |
| G-SCENE-9 Setting | PASS | 264 |
| G-SCENE-10 Camera | PASS (the f1-80 approach is fast) | - |
| G-SCENE-11 Continuity | f1 = BRIDGE_HORIZON, unchanged | 1 |
| G-SCENE-12 Story | PASS | 200, 264 |

Luma (mean / sd) on the full frames, all `ok`:

| Frame | Role | Mean | SD |
|---|---|---|---|
| f1 | first frame | 224 | 19 |
| f27 | 10 % | 223 | 21 |
| f132 | 50 % | 131 | 50 |
| f238 | 90 % | 137 | 56 |
| f264 | last frame | 165 | 77 |

**Known issues left (minor):**
- f1 and f27 have sd 19-21: the bridge horizon shot is a bright, soft dawn.
- The wheelhouse is simple.
- The approach is fast.
- The net crosses close to the lens around f185.
