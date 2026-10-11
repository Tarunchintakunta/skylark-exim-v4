# sea art pass r1 (issue #75, COLOR_SCRIPT row 12)

Stills: assets-src/blender/stills/sea/r1_f{001,027,132,196,238,264}.png (1920x1080, 32 spp).

Changes: sun key #ffb070, cool sun fill #4f8fa8 from the west (no shadow), warm area rim #ffcf8a east of the boat,
physical sky multiplied by a horizon #ffbf7a -> zenith #24496b gradient, sea body #0f3d4a, weathered warm white
wheelhouse, new sunrise-orange life ring, look.apply('sea') + AgX Medium High Contrast + grade(lift #0f3d4a, gain #ffb070, sat 1.12).

Verdict: FAIL.
- Black sky, no sun in every frame (f1 luma mean 31 / sd 11 FAIL). Cause: look.fog puts a Principled Volume on the
  world output, and EEVEE then treats the world as fully absorbed, so the sky behind is lost.
- The area rim's specular reflects in the sea as a bright rectangle (f132, f264).
Fix for r2: sea mist goes into a bounded volume box (SK_MIST); rim specular_factor 0.
