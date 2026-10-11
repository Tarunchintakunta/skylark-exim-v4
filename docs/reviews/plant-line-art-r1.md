# plant-line art pass — round 1 (issue #75)

Stills (full res): assets-src/blender/stills/plant-line/art-r1/{0001,0096,0287,0478,0669,0765}.png

Changes: cool blue-white PUF walls with grime + hue/value variation, blue-grey epoxy floor, marigold crates (replaced the green),
warm task lamp #f0b04a, per-zone cool fill / warm rim area lights (rows 06-09), dock spill #ffc078, sun #ffc98a,
cool interior world tint #8fb0e6, look.apply(scene, 'plant-line') + fog keyed per chapter (world volume).

Luma: f1 163/23, f96 158/31, f287 131/41, f478 150/40, f669 160/45, f765 74/32 (all pass).

Verdict: FAIL.
- Clipping/fake: the world-volume fog absorbs the sky, so the dock door and BRIDGE_DOCK read as a dark blocky checker pattern.
- Not empty or toy-like, but milky: 0.0015–0.003 fog over a 66 m hall flattens everything to a creamy grey. Warm rims too weak to read.
