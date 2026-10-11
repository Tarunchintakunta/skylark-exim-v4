# plant-line art pass — round 3

Stills: assets-src/blender/stills/plant-line/art-r3/. Fog is now an interior volume box `fog_interior` (#cfe3ee, keyed 0.0002–0.0015).
The world volume is removed, as in the lead's note. Key is #eef4ff (5500 K in the wash bay). Grade: lift #2a4a6e, gain #ffd59a,
sat 1.14, contrast 8, bloom 0.15, vignette 0.10.

Luma: f1 181/21, f96 179/30, f287 149/49, f478 154/48, f669 168/48, f765 163/58. Render 4–7 s/frame at full res (GPU shared).

Verdict: nearly there. The frames now have blue-white walls with grime, blue shadows, a warm rim and floor glow in the peel hall,
marigold crates, and morning sun through the dock. The bridge sky is back.
- Lab f96 is hot: the ceiling LED and window are near clipping. Lab lights 85→60, fill 70→50.
- At the wash door, the floor spill clips. Dock spill 1800→1100.
- f1 is brighter than plant-cold's f574 (181 vs 169) because of the new grade. Opening exposure −2.1→−2.35.
