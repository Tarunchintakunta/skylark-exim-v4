# port.blend art pass, final (issue #75, COLOR_SCRIPT row 02 v-port: dusk harbour)

Full render (v2, after the lead's crushed-front-faces fix): assets-src/render/port/0001-0264.png (264/264), 1920x1080 EEVEE 32 spp, 13 min wall, 3.05 s/frame average and 5.9 s max (shared GPU, one-slot lock).
Sheet: docs/renders/port-art-sheet.jpg. Before/after: docs/renders/port-before-after.jpg (rows f1, f27, f132, f204, f238, f264). Rounds: port-art-r1.md.
Code: assets-src/blender/build/port_art.py, exec'd by port.py after sklib.finish (the rebuild reproduces it).

What changed
- Key: sun elev 8 deg, az 260 deg, #ff8c4a, energy 6.0 (was a 52 -> 40 deg midday sun at az 135). Rim: sun #ffb06b 2.5 (el 14 deg, az 235 deg, shadows). Fill: #4b4a8c 4.0 sun from the east, no shadow (violet shadows).
- World: the same as reefer dusk_world(): sky_world(8, 260) mixed 0.6 with an EASE gradient from horizon #e8825a to zenith #1b2a4a. These are the lead's reefer values for the BRIDGE_SEA match, not the row's #f29a5e / #262457.
- Sea (also from reefer.py): deep (0.010, 0.036, 0.095), shallow (0.040, 0.140, 0.220), warm #ff8c4a glints, haze toward #c98a7a at 0.0008/m. Land/ridge aerial haze: #c98a7a (ridge #9a6f86) instead of day blue.
- No world fog: a world volume blacked out the frames (luma 9-19).
- Sodium accents #ffd28a: 8 light-tower spots (60 kW), 6 crane floodlights (25 kW), lamp lenses emissive at 40.
- BRIDGE_DOOR: area light #ff9a5c 3500 W from camera-left (-Y), grazing the truck reefer doors, plus the violet fill.
- Materials: large-scale warm/cool value drift on the quay concrete, asphalt, crane paints, galvanised steel and white containers/cab.
- Grade: look.apply('port') (AgX Punchy), then the reefer grade: lift #3a5b8c 0.012, gain #ff9a5c 0.015, sat 1.10, bloom 0.15, vignette 0.10, exposure +0.9.

| Gate | Result |
|---|---|
| G-SCENE-1..6, 9, 10, 12 | PASS (geometry unchanged since port-full-final; no new clipping) |
| G-SCENE-8 (no overlay, vignette <= 12 %) | PASS (0.10; colour comes from the lights and world) |
| G-SCENE-11 bridges | PASS: f1 vs reefer 0192 SSIM 0.971, luma 58/14 vs 58/13; f264 = warm side-lit white doors + violet fill, ready for plant-cold |
| Luma (luma.py) | f1 58/14, f27 (10 %) 108/32, f132 (50 %) 115/54, f204 134/69, f238 (90 %) 129/57, f264 137/19: all ok |
| Speed <= 15 s/frame | PASS (3.05 s avg) |

v2 fix (lead: in f132/f204 the camera-facing boxes crushed to navy). Mid-shot only, both bridge ranges untouched:
- Violet fill #4b4a8c rises from 4 to 9, and a sky bounce #8a7fb0 is added: a no-shadow sun, energy 2.0, parented to the camera so it lights whatever faces the camera. I used a camera-parented sun instead of the large area light you suggested, because one fixed area cannot follow the 92 m -> 1 m camera move.
- Exposure is +0.9 at f1-12, eases to +1.45 by f30, holds to f240, and returns to +0.9 by f256.
- Keys: f12 / f30 / f240 / f256 (Bezier).
- The red containers at f132 and the red/teal/blue stacks at f204 now read with their own hue.
- f264 is pixel-identical to the accepted v1 frame (PSNR inf, SSIM 1.0). f1 matches v1 at PSNR 102 dB and reefer 0192 at SSIM 0.971.

Known issues: the faces toward the camera still lean violet-blue in the backlit shots (that is the dusk look); the sky uses the reefer's navy/orange gradient rather than the row's violet #262457.
