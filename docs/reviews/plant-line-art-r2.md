# plant-line art pass — round 2

Stills: assets-src/blender/stills/plant-line/art-r2/. Fog lowered (0.0002–0.001), tile 8, rims ×2–2.5, fills ×1.5, hall key ×0.8.

Luma: f1 163/23, f96 174/29, f287 144/45, f478 149/47, f669 154/55, f765 38/36.

Verdict: FAIL. The dock is still black/blocky even at 0.0004, which confirms the cause: EEVEE treats a world volume as infinite
and absorbs the sky behind the door. Interiors are still creamy and warm-grey: the 5000 K key plus the warm gain cancels
the blue walls. Next: an interior fog box instead of the world volume, a cool #eef4ff key (5500 K in the wash bay), more grade contrast.
