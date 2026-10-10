# table — full render final review

Full render: assets-src/render/table/0001–0216.png (216/216 frames, 1920×1080, EEVEE 32 spp, AgX Base Contrast,
24 fps, motion blur). Wall time 23 min on the shared GPU (~6.4 s/frame average, heaviest stills 12 s).
Contact sheet: docs/renders/table-full-sheet.jpg. Round details: table-full-r1.md.

## Verdict
Self-approved. Macro reads as a food photo (cleaned CC0 prawn skewers in focus, f/2 falloff), no diner hands in any
frame, glasses clear with wine/water visible (ray tracing on, blended Fresnel glass), f196 shows only real motion
blur (no interpolation ghost; every frame rendered), f212–216 hold on the BRIDGE_FROST crystal macro.

## Luma (full frames)
| Chapter | 10 % | 50 % | 90 % |
|---|---|---|---|
| Macro f1–60 | f7 170/39 ok | f31 171/38 ok | f54 168/33 ok |
| Crane f60–130 | f67 166/32 ok | f95 152/36 ok | f123 130/50 ok |
| Dolly f130–190 | f136 119/53 ok | f160 90/58 ok | f184 92/60 ok |
| Push f190–216 | f193 131/56 ok | f203 185/17 ok | f214 177/24 ok |
f1 171/39 ok · f196 143/45 ok · f216 177/23 ok.

## G-SCENE
1 PASS · 2 PASS · 3 PASS · 4 PASS · 5 PASS · 6 PASS · 7 PASS · 8 PASS · 9 PASS · 10 PASS (opening is a high-angle
macro, not pure top-down) · 11 PASS to spec (lead equalises with reefer f1) · 12 PASS.

## Known issues left
- Frost crystals read as matte white hexagonal plates (little specular sparkle); texture is real (sd 23).
- f203 sd 17 (mid-push defocus on the carton blocks), above the 12 floor, below the 20 aim.
- Lemon wedge slightly waxy, salad slightly CG when sharp; both mostly in the DOF falloff.
- Diner B's face visible at ~2 m around f110–135.
