# pond art pass: rounds 1 and 2 (issue #75, COLOR_SCRIPT row 11)

Frames (before|after rows): f1, f22, f108, f160, f194, f216. Sheet: docs/renders/pond-art-r2-before-after.jpg.

## Round 1
- Changes: sky tint, sun colour keys, fill and rim suns, teal water, warm haze, marigold floats and paddles, `look.apply(s, 'pond')`.
- Result: every frame black (luma 7–15, FAIL).
- Cause: the world volume from `look.fog`. EEVEE treats a world volume as infinite, so it absorbs the sky and the sun. The probe confirmed it: no compositor + fog gave mean 1; removing the fog gave mean 176.
- Fix: no world fog. The pond mist is now a bounded volume slab (`SK_POND_MIST`): #f4e2c0, density 0.004 at the water fading to 15 % by 9 m, anisotropy 0.55. It only shows inside the 60 m volumetric range.

## Round 2 (+ the 5x5 probe)
- In the probe, two hard-edged ghost discs showed up on the sea (f1 top right, f216 right). They were specular glints from the new fill and rim suns (0.2 rad angle). Fix: `specular_factor = 0` on both.
- The fields looked a little neon at sat 1.12. Fix: sat 1.08.
- After the lead note, the grade is now complementary: lift is the cool zenith blue #3f6f9a (0.02), gain is #ffcf7a (0.03).
- Result: rich teal-green water, warm peach horizon, cool shadows, marigold float line. Not grey, no clipping, no toy look beyond the existing scene.
- Remaining issue: frames were darker than before (f1 109 vs 143, f22 113 vs 139, f160 122 vs 142). Round 3: exposure +0.35 and rim 1.1 → 1.6.

Luma r2 (full res): f1 109/29, f22 113/33, f108 176/52, f160 122/59, f194 167/55, f216 192/31. All ok.
