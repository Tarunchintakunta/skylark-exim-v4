# prod-tuna / prod-prawn art round 1 (stills art1, f1/12/40/60/108/120, 1920x1080)
Changes: navy sweep, HDRI tinted to #0b1424, fill #3a5b8c, rim + new low rim #9fe3ff, wash #3a5b8c, 7 soft glow discs, icier ice albedo, look.apply preset grade.
Verdict: FAIL. Frame washed out and blue (mean ~131): the glossy navy floor reflected the tinted HDRI at grazing angles, and the preset lift (#0f1d33 at 0.25 strength) turned the fish blue. Glow placement ray-cast hit the product, so 4 discs sat in front of the fish (hazed it).
Fix: matte floor (roughness 0.72-0.88, specular 0.25), world tint 1.6 -> 1.0, ray-cast against the sweep only, gentler grade.
