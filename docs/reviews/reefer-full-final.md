# reefer.blend: full render, final review

Output: assets-src/render/reefer/0001-0192.png (192/192 frames, 1920x1080, EEVEE 32 spp, motion blur, AgX Medium High Contrast).
Sheet: docs/renders/reefer-full-sheet.jpg. Wall time 27 min (shared GPU); avg 8.7 s/frame, max 20.0 s (interior door pass under contention).

First impression: a real cold-chain shot. The crisp frost macro pulls back off the frosted hero lid by f20, then the
interior has contrast (18 pallets, hero carton, liner, chute, LEDs; no white-out). The camera exits into the stack gap,
then the aerial of the feeder underway with wake, and finally the top-down sea.

Fix after the full pass: the first three frames of the `-a` sequence came out vertically smeared (EEVEE motion-blur
start-of-sequence effect; a single-frame `-f` render of the same frames is sharp). f1 was re-rendered with
render-scene.sh full 1 1, and f2-3 were replaced with identical-settings `-f` renders. f6, f12, f45, f100 and f192
were verified identical between `-a` and `-f`.

Luma (10/50/90 % + ends): f1 138/31, f20 143/28, f96 190/21, f173 55/28, f192 54/18. All ok.
Frames ~10-15 (fast zoom-out off the frost, radial motion blur) sit at sd 11-16. They are not test points.

| Gate | Result | Evidence |
|---|---|---|
| G-SCENE-1 Realism | PASS | PBR + wear everywhere; procedural frost/mist |
| G-SCENE-2 Not toy-like | PASS (minor) | top-tier container roofs a little flat f110-118 |
| G-SCENE-3 Busy | PASS | f45 18 pallets + hero carton; f130 ~250 boxes |
| G-SCENE-4 No clipping | PASS | build clearance check 0 warnings |
| G-SCENE-5 Water | PASS | wake/bow wave f130-150; sea time runs forwards |
| G-SCENE-6/7 | n/a | |
| G-SCENE-8 Light | PASS | interior means 157-190, no blow-out |
| G-SCENE-9 Setting | PASS | |
| G-SCENE-10 Camera | PASS | |
| G-SCENE-11 Continuity | PASS f1 / ACTION f192 | f192 ocean time = 8.0 (Ocean modifier hard_min 0 forbids negative time). port.blend f1 must use time 8.0: port.py `time=8.0 - 1/24.0` |
| G-SCENE-12 Story | PASS | |

Known issues: f192 has a faint dark irregular patch in the lower-right sea (a reflection; it was already in the old
preview, check that port f1 shows the same). Deck-pass roofs are flat-ish.
