# reefer.blend — full-quality round 1 (stills: assets-src/blender/stills/reefer/full_r1_*, full_r2_*; 1920x1080, saved settings, 32 spp, motion blur)

First impression: reads as a real cold-chain shot now. The frost macro has crisp crystal texture, the camera pulls off the
frosted hero lid by f20 to show the carton and the 18 pallets, the interior has contrast (no white-out), then the
feeder underway and the top-down sea.

Changes this round (build/reefer.py):
- Frost: coverage ramp widened 0.44-0.56 -> 0.40-0.60, crystal grain 0.45 -> 0.25 (f1 sd 31 vs 19 before).
- Camera f1-30: new keys f10 (0.30 m, 85 mm) and f22 (45 deg pitch, 45 mm, lid + neighbours); focus locked to the
  lid plane along the view axis up to f22, blended to the keyed focus by f30 (the old f10-20 soft white-out is gone).
- Ship motion for the camera bake evaluated at the true frame (the clamp made f1 smear under motion blur).
- World (sky) strength 0.06 while inside the box (f1-55) -> 0.3 by f100: the sky leaked in as flat fill and washed
  the interior out (mean 210 -> 157 at f45).
- Ocean time runs forwards: time = SEA_T0 + (f-192)/24 with SEA_T0 = 8.0. The Ocean modifier clamps time >= 0
  (RNA hard_min 0, verified), so negative times are not possible; f192 therefore has time 8.0, not 0.
  **port.blend f1 must use the same state: port.py `sklib.ocean(..., time=8.0 - 1/24.0, animate=True)`.**
- EEVEE samples 64 -> 32 (no visible noise at full res; interior 16 s -> 8-11 s).

Four questions: empty? no (18 pallets, ~250 boxes on deck). Toy-like? deck pass container roofs still a little flat
(f110-118). Fake? no. Clipping? no (camera clearance check 0 warnings).

| Gate | Result | Evidence |
|---|---|---|
| G-SCENE-1 Realism | PASS | sklib PBR + wear on all hard surfaces; procedural frost/mist |
| G-SCENE-2 Not toy-like | PASS (minor) | real metres, bevels; top-tier roofs read flat f110-118 |
| G-SCENE-3 Busy | PASS | f45: 18 pallets + hero carton; f130: feeder with ~250 boxes |
| G-SCENE-4 No clipping | PASS | camera clearance check per frame (0 WARN) |
| G-SCENE-5 Water | PASS | wake + bow wave f130; no shadow floor; sea runs forwards now |
| G-SCENE-6 People | n/a | |
| G-SCENE-7 Fish | n/a | |
| G-SCENE-8 Light | PASS | f45 mean 157 sd 31, f75 178/28, f96 190/21 (was 210/18) |
| G-SCENE-9 Setting | PASS | only carton print text |
| G-SCENE-10 Camera | PASS | baked monotone-cubic path, no jerks |
| G-SCENE-11 Continuity | PASS f1 / CHECK f192 | f1 BRIDGE_FROST exact (100 mm, 0.12 m, f/2.8); f192 cam/lens/sky exact, ocean time 8.0 -> port must match |
| G-SCENE-12 Story | PASS | |

Luma (full res): f1 138/31, f10 143/16, f20 143/28, f45 157/31, f75 178/28, f96 190/21, f130 169/63, f173 55/28, f192 54/18 — all ok.
Frame time (32 spp + MB, shared GPU): interior f45 11.0 s, f75 10.8 s, f96 11.6 s; frost 5-8 s; exterior 5-9 s.
