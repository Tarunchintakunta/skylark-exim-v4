# port.blend — full-render round 1 (stills r5–r8, 1920×1080, assets-src/blender/stills/port/r8_*.png)

First impression: busy Vizag terminal; the far range now reads as green/brown vegetated hills with ridgelines and haze instead of pale grey cards; crane landing clean, no stripe shadows on the white boxes.

Changes vs r4: procedural hill terrain (ridged fractal, foothill ramp from the plain, forest/scrub/laterite + slope material, aerial haze toward horizon blue); tugs redesigned (tumblehome deckhouse, raked wheelhouse, visor, stacks, bulwark, winch) and moved aft behind the hull (only their hulls peek at f70); truck cab with raked windscreen, rounded roof, visor, tanks/steps, bevel 0.09; crane parts above the portal (girders/boom/stays) cast no sun shadow (they made parallel stripes on the ship boxes), legs/sills keep shadows; sun angle 6°; motion-blur shutter keyed to camera speed (fast pans at f6–66, f140–182, f218–237 were smeared at shutter 0.5); 32 spp; ocean time f1 = 8.0 (matches reefer BRIDGE_SEA).

Four questions: empty? no. toy-like? tugs/cab now small, detailed or hidden. fake? hills OK at distance. clipping? none seen.

| Gate | Result | Frames |
|---|---|---|
| G-SCENE-1 realism | PASS | hills f70/f132 vegetated; PBR + wear unchanged |
| G-SCENE-2 not toy | PASS | tugs f70 (hull only), f205 small far; cab f238/f250 sliver behind reefer |
| G-SCENE-3 density | PASS | 3 STS, 165 ship + 2558 yard boxes, 8 vehicles, 12 people |
| G-SCENE-4 clipping | PASS (visual) | f205 landing on castings |
| G-SCENE-5 water | PASS | f1, f205 |
| G-SCENE-6 people | PASS | f238 desk staff |
| G-SCENE-7 fish | n/a | |
| G-SCENE-8 light | PASS | sun az 135 constant; no stripe shadows f205/f238 |
| G-SCENE-9 setting | PASS | no text |
| G-SCENE-10 camera | PASS | path unchanged; blur readable f27/f132 |
| G-SCENE-11 continuity | PASS (spec) | f1 BRIDGE_SEA ocean t=8.0; f264 BRIDGE_DOOR unchanged |
| G-SCENE-12 story | PASS | reefer landed by STS f205 |

Luma (r8): f1 54/19, f27 131/38, f70 153/51, f132 166/52, f205 168/58, f238 155/52, f250 158/50, f264 201/21 — all ok.
Perf: f205 A/B on shared GPU (7 parallel renders): 64 spp 17–22 s, motion blur ~5 s of it; at 32 spp stills 4–8 s/frame with lighter load.
