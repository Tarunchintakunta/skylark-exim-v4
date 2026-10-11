# table — art round 1 (issue #75, COLOR_SCRIPT row 00)
Changes: walnut table/chairs (kitchen_wood scan tinted 0.16/0.075/0.04), umber stoneware plate (was near-white), marigold napkins, darker warm plaster; key L_key 2900 K #ffb46b area camera-left high (260 W), window → cool fill #5b7da6 (70 W), rim L_rim_A/B #ff8a3d behind the plates, candle #ff8a3d 3 W, ceiling/front fills cut to 22–40 W; world ambient #1d2433; BRIDGE_FROST light #e6f2ff + L_frost_kick #ffb46b 2.5 W; look.apply('table') (lift #3a1f14, gain #ffb46b) + world fog 0.002.
Stills f1/31/95/160/203/216: luma 96/48, 92/49, 74/50, 57/53, 166/29, 168/30 (all ok). 4.0–12.0 s/frame.
Verdict: FAIL. Whole frame orange/red (a full-frame cast, G-SCENE-8 spirit), prawns read candy-pink, frost frame tinted brown.
Cause found in r2: the compositor (warm lift + bloom size 0.5 spreading warm highlights) — the ungraded render is already warm enough.
