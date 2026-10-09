# reefer.blend review — rounds 1-4 (stills in assets-src/blender/stills/reefer/r1..r5_*)

First impression: reads as the story — frosted carton macro -> clean bright reefer load -> out the doors -> unit -> deck -> feeder underway -> open sea.

r1: interior blown out (f1/f20 white), ocean edge seam at 300 m, f115 too close to roof. r2: lights cut, frost
shader rebuilt (faceted crystals), focus on the reefer unit, aerial re-framed. r3/r4 (lead notes): seam fixed
(patched sklib.ocean far plane + distance normal blend), f115 deck pass raised/slowed, mist added, gulls placed in
the aerial. r4 found the wake mask image was not persisting (generated image not packed) -> saved+packed, mist reduced.

| Gate | Result | Notes |
|---|---|---|
| G-SCENE-1 Realism | PASS (minor) | all hard surfaces sklib PBR + wear; frost, mist, LED, gull feathers procedural |
| G-SCENE-2 Not toy-like | PASS (minor) | real metres, bevels; top-tier container roofs read flat at f118 under 52 deg sun |
| G-SCENE-3 Busy | PASS | 18 pallets (2x9), ~250 containers on deck, 4 gulls |
| G-SCENE-4 No clipping | PASS | camera clearance check per frame in build (0 warnings); doors are a cut-away |
| G-SCENE-5 Water | PASS? | emission+glossy sea (no shadow floor), wake/bow foam mask + bow spray particles; verify wake visibility in preview |
| G-SCENE-6 People | n/a | |
| G-SCENE-7 Fish | n/a | |
| G-SCENE-8 Light | PASS | cool LED interior + door daylight; sky_world(52,135) outside |
| G-SCENE-9 Setting | PASS | no text except carton print |
| G-SCENE-10 Camera | PASS | baked monotone-cubic path, eased ends; ocean time runs 7.96 -> 0 (hard min 0) |
| G-SCENE-11 Continuity | PASS (to verify) | f1 BRIDGE_FROST, f192 BRIDGE_SEA exact (cam 0,0,60 rot 0, lens 35, seed 41, t=0) |
| G-SCENE-12 Story | PASS | |

r5 + preview (docs/renders/reefer-preview.mp4, reefer-sheet.jpg): wake + bow wave now read (white trail along the
hull, stern wake), mist faint, horizon seamless, gulls in the aerial. Remaining: interior frame ~21 s at 1080p/64 spp
(exterior 6.5 s); top-tier container roofs read flat in the f110-118 deck pass; ocean time runs backwards toward 0.
