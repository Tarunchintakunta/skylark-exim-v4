# sea art pass r2

Stills: assets-src/blender/stills/sea/r2_f*.png. Luma: f1 229/17, f27 228/20, f132 123/56, f196 103/47, f238 134/66, f264 174/74 (all ok).

Better: the sea goes deep teal near camera with a gold horizon glow, the boat is saturated blue/red, the crew have warm rims.
Still wrong:
- f1/f27 horizon shot washes out to peach (sd 17-20): the zenith never reaches #24496b; the mist box (2.4 km wide) milks the far sea.
- f264 portrait flares out around the sun (bloom over a bright sky).
Fix for r3: tint mix 0.55 -> 0.85, zenith gain 0.45, gradient reaches the zenith by z 0.32; mist box 1.2 km; exposure -0.35.
