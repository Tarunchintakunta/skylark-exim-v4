# plant-cold art pass r2
Luma: f1 103/31, f96 119/49, f192 156/35, f288 168/41, f383 173/63, f479 152/47, f574 170/19 (all ok). Max 15.2 s/frame (f96, f192).
Verdict: FAIL. Fog/light changes helped little; still a uniform blue cast. A/B at f96 (compositor on/off) shows the cast is the
preset grade (lift #1e2a4f at 0.025 -> strong blue lift), i.e. a full-frame tint (G-SCENE-8). Ungraded keeps kraft + marigold.
Fix r3: look.grade with the same hues at lift_amt 0.008 / gain_amt 0.012, sat 1.15; exposure -0.3 for deeper fields; sun az 165 (grazing).
