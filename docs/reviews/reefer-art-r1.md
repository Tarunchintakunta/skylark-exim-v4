# reefer.blend: art pass rounds (issue #75), half-res stills f1/19/45/96/140/173/192

Rounds 1-7 were all rendered at 50 %. Grids are in /tmp/claude-501/sk/rfa/r1..r7.jpg (before | after per row).

- **r1**: every frame came out navy-black (luma 13-19). The cause was the world volume from look.apply (SK_FOG). EEVEE treats a world volume as infinite, so it absorbs the sun and the sky (f45: 96 without fog, 4 with it). Fix: no world fog. The interior keeps its bounded cold-mist volume (now #cfe6f2), and the sea gets a distance haze inside the water shader (1 - exp(-0.0008 d) toward #c98a7a).
- **r2**: no grade yet (the build crashed after finish). Interior colour is good: cool blue-white liner with grime, marigold tape, ice rim. The dusk sky and horizon read well. The top-down sea is too dark and flat (mean 34, sd 8).
- **r3**: grade on with the preset lift #123a5a at 0.025, which gave a full-frame teal cast. FAIL (G-SCENE-8 spirit).
- **r4**: lift cut to 0.006, then changed to cool fill #3a5b8c (§3 complementary rule), gain #ff9a5c. Added sun glints (N·L toward the dusk sun). They were too broad: pink blobs on the swell looked fake.
- **r5**: glints at power 10, which was invisible. Exposure +0.5.
- **r6**: exposure +0.9, so the interior is brighter (129 at f45). The sea was still flat (sd 9).
- **r7**: glints broken into glitter with a fine noise mask (power 4, strength 60), and the crest/body contrast raised. f173 52/15 and f192 58/13 now pass. The sea is deep blue with warm sparkles.

Four questions on r6/r7:
- Empty? No.
- Toy-like? The deck containers at f140 read dark and backlit, but plausible.
- Fake? The r4 glints were fake and are now fixed.
- Clipping? None.
