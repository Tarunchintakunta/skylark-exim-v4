# plant-cold art pass r1 (frames 1 96 192 288 383 479 574, 1920x1080, 32 spp)
Changes: COLOR_SCRIPT rows 03-05 lights (cold key #cfe0ff, pack #f2f6ff, IQF/belt #d6ecff), violet fill #6b5fb5, cyan rack rims #9fe3ff,
pack fill #8fb4e8 + warm rim #ffcf8a, IQF fill #4f6fa8 + spray backlight #a8f0ff, belt rim; dusk door (sun #ff9a5c elev 8 az 150, violet world #4b4a8c 1.0);
interior world keyed #0f1630 -> #1a2433 -> #0d1a26; PUF walls cool blue-white + grime; blue epoxy floors; marigold tape in the hall;
look.apply('plant-cold'); fog keyed 0.006 / 0.0015 / 0.008.
Luma: f1 107/29, f96 104/36, f192 137/34, f288 165/41, f383 171/63, f479 145/37, f574 174/20 (all ok).
Verdict: FAIL on look. Whole frame reads blue-washed (kraft cartons, yellow reach truck lose colour), hazy; f1 door magenta
(violet sky too strong vs the sun); blotchy volumetric patterns on walls (tile 16). Fix: sky 0.3, sun 5, fill 0.45x, rim 1.3x, fog 0.0025/0.004, tile 8.
