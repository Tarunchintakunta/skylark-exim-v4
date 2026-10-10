# reefer.blend: art pass, final (issue #75, COLOR_SCRIPT row 01)

- **Output:** assets-src/render/reefer/0001-0192.png, 192/192 frames, 1920x1080, EEVEE 32 spp. The before frames are kept in render/before/reefer.
- **Speed:** avg 4.3 s/frame, max 8.4 s. Render wall time 13 min (30 min including the wait for the shared lock).
- **Sheets:**
  - before/after: docs/renders/reefer-before-after.jpg. Rows top to bottom are f1, f19, f45, f96, f140, f173, f192; each row is before | after at 960 px.
  - contact sheet: docs/renders/reefer-art-sheet.jpg
- **Rounds:** docs/reviews/reefer-art-r1.md

## What changed (build/reefer.py, reproducible by rebuild)

### World and lights
- **World:** dusk. `sklib.sky_world(8, 260)`, sun recoloured to `#ff8c4a`. The physical sky is mixed 0.6 with an eased gradient from horizon `#e8825a` to zenith `#1b2a4a` (TexCoord Generated Z mapped 0-0.6). This is `dusk_world()`.
- **Exterior fill:** sun `#3a5b8c`, 0.6, elevation 35 / azimuth 80, angle 20°, with shadow.
- **BRIDGE_FROST (f1):** softbox `#e6f2ff` 3 W, plus a warm kick area light `#ffb46b` 0.6 W at 0.6 m on the -X side. Frost albedo tinted toward `#cfe6f2`.
- **Interior lights:** LEDs `#d9ecff`. Ice rim `#9fd8ff` 60 W from the bulkhead behind the load, with shadow. Cool fill `#3a5b8c` 25 W from the doors.

### Interior materials
- Cold mist volume `#cfe6f2`.
- Liner is cool blue-white (0.60/0.68/0.76) with wear 0.4 and streaks 0.35.
- Carton tape is marigold `#e2a03a`.

### Sea
- **Body:** deep (0.010, 0.036, 0.095), shallow (0.040, 0.140, 0.220).
- **Distance haze:** in the water shader, 1 - exp(-0.0008 d) toward `#c98a7a` at emission 0.35.
- **Warm sun glitter:** pow(max(N·L_sun, 0), 4) × a noise sparkle mask × 60, colour `#ff8c4a`.
- **No world fog:** a world volume blacked out sky and sun (r1).

### Grade
- `look.apply(s, 'reefer')` with AgX Punchy, then `look.grade`:
  - lift `#3a5b8c` at 0.012 (cool, per §3 complementary)
  - gain `#ff9a5c` at 0.015
  - saturation 1.10, contrast 2.0, bloom 0.15, vignette 0.10
- Exposure +0.9 to stay at or above the old frame brightness indoors.

## Luma (full frames)

| Frame | Before (mean/sd) | After (mean/sd) | Result |
|---|---|---|---|
| f1 BRIDGE_FROST | 177/23 | 110/33 | ok |
| f19 (10 %) | 141/28 | 115/30 | ok |
| f45 | 157/31 | 130/30 | ok |
| f96 (50 %) | 190/21 | 131/32 | ok |
| f140 | 174/62 | 108/54 | ok |
| f173 (90 %) | 55/28 | 53/15 | ok |
| f192 BRIDGE_SEA | 54/18 | 58/13 | ok |

Interior means are lower than before, which was blown-out white. They now have colour and an sd of 30 or more. f173 and f192 sit at sd 13-15, above the floor but under the 20 aim.

## G-SCENE

| Gate | Result | Note |
|---|---|---|
| 1 Realism | PASS | PBR + grime; liner no longer flat white |
| 2 Not toy-like | PASS (minor) | deck pass f105-118 roofs pale/flat (pre-existing) |
| 3 Busy | PASS | |
| 4 Clipping | PASS | camera unchanged, 0 clearance warnings |
| 5 Water | PASS | deep blue, glitter, wake intact |
| 8 Light / no overlay | PASS | colour from lights/world; grade tint ≤ 0.015, vignette 0.10 |
| 10 Camera | PASS | camera, lens and frames unchanged; f1-3 sharp (no start-smear) |
| 11 Continuity | f1 frost spec / f192 BRIDGE_SEA dusk | port f1 must match (below) |

## Port f1 must match (BRIDGE_SEA)
- Use `dusk_world()` as above: sun 8°/260° `#ff8c4a`, sky mix 0.6 with gradient `#e8825a` → `#1b2a4a`.
- Ocean seed 41 at time 8.0, with the same deep/shallow colours, glitter and haze.
- Grade with exposure +0.9.

## Known issues
- **f140-170:** the ship is backlit by the low sun and reads dark. The hull rim is faint.
- **f192:** the sea is calmer in contrast (sd 13) than before, because the foam is dimmer under dusk light.
- **Grade bloom:** contrast and bloom are look.py defaults and were not tuned further.
