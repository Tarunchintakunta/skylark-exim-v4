# table — art pass final (issue #75, COLOR_SCRIPT row 00 + BRIDGE_FROST)

Full render: assets-src/render/table/0001–0216.png, 216/216 frames, 1920×1080, EEVEE 32 spp, AgX Medium High Contrast + SK grade.
Round 6 re-render (lead review: pink/magenta f1–95). Wall time 14 min (one-slot lock, 7 threads), avg 3.9 s/frame, max 8.7 s.
Sheet: docs/renders/table-art-sheet.jpg · before/after: docs/renders/table-before-after.jpg (rows f1, f31, f95, f160, f203, f216; left before | right after).
Rounds: table-art-r1..r6.md.

## What changed (assets-src/blender/build/table.py)
- Light: L_key 2900 K amber area, camera-left high (190 W; warm light colours via amber() = midway between linear and seen hex, so #ffb46b -> (1, 0.57, 0.25), not the orange-red (1, 0.46, 0.15) that turned the walnut magenta); window → cool fill #5b7da6 (200 W; shows on plate rims, glassware, shadow side); warm rims L_rim_A/B amber #ffc27a behind the plates (20 W, no shadow); candle amber #ffb46b 2.7 W; pendant amber #ffb46b 145 W; under-cabinet #ffb46b; ceiling/front fills cut to 22–40 W, neutral-warm.
- World: ambient #1d2433 (strength 2.5); window city bokeh kept (blue hour + warm lit windows).
- Haze: no world fog (lead note). Bounded warm haze volume #ffcf9a, density 0.008, anisotropy 0.45, over the dining area only (kitchen/carton/frost outside it).
- Materials: walnut table + chairs (kitchen_wood scan tinted 0.14/0.10/0.042: warm brown, wood-crop R/G f1 1.43 / f31 1.42 / f95 1.29); charcoal stoneware plate (was near-white; umber in r1–r4 read peach); deep-ruby tuna; cream #efe6d6 napkins; warmer darker plaster; cooked-orange prawn ramp.
- Bridge f216: BRIDGE_FROST light #e6f2ff (6500 K softbox), + L_frost_kick #ffb46b 2.5 W from the table side (faint).
- Grade: look.apply('table') then TABLE_GRADE: lift #5b7da6 0.025 (cool shadows), gain #ffb46b 0.015, sat 1.08, contrast 2, bloom 0.2 with Glare size 0.15 / threshold 1.5 (default size 0.5 washed the whole frame orange), vignette 0.10. No grain.

## Luma (full frames, round 6)
| Chapter | 10 % | 50 % | 90 % |
|---|---|---|---|
| Macro f1–60 | f7 129/40 ok | f31 128/40 ok | f54 133/44 ok |
| Crane f60–130 | f67 147/46 ok | f95 126/50 ok | f123 121/56 ok |
| Dolly f130–190 | f136 117/59 ok | f160 80/60 ok | f184 84/63 ok |
| Push f190–216 | f193 124/62 ok | f203 186/20 ok | f214 184/27 ok |
f1 (OG) 130/40 ok · f216 183/26 ok.

## G-SCENE
1 PASS · 2 PASS · 3 PASS · 4 PASS · 5 PASS · 6 PASS · 7 PASS · 8 PASS (colour from lights/world; grade tint within §3 limits, vignette 0.10) · 9 PASS · 10 PASS · 11 PASS to spec (#e6f2ff softbox + faint warm kick; lead equalises with reefer f1) · 12 PASS.

## Known issues
- Prawns still lean pink-salmon rather than deep cooked orange (scan-driven ramp).
- With the less saturated amber key the macro reads warm-neutral; candle warmth is strongest in the wide table shots.
- Carried over: Diner B's face visible at ~2 m around f110–135; frost crystals matte.
