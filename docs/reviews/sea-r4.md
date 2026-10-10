# sea.blend (v-sea, f1-264, dawn): self-review r4

Rounds: r1 (first build), r2 (lead critique: foam blotches, deck shot, net, stiff crew), r3 (patched sklib.ocean, larger sea, pull-back path), r4 (deck-beat framing).
Stills are in assets-src/blender/stills/sea/ (r1_*, r2_*, r3_*, r4_*, full_*). The preview is docs/renders/sea-preview.mp4 and the contact sheet is docs/renders/sea-sheet.jpg.

**First impression:** this is a working Vizag trawler at dawn: blue, white and red painted planked hull, tyre fenders, rusty net drum, red stern A-frame, and the cod-end coming up dripping. The deck beat (gloved hands sorting skipjack and prawns on crushed ice, wet deck reflections) reads strongly. The last frame shows the crew at the starboard rail: one hauling, one leaning, one coiling rope, one carrying a basket and one waving, with the headland and two boats on the left.

| Gate | Result | Notes (frames) |
|---|---|---|
| G-SCENE-1 Realism | PASS (minor) | Hull, deck, metal and tyres use CC0 PBR + grime masks. Gull, flag, glove and rope materials are procedural (small, soft materials) |
| G-SCENE-2 Not toy-like | PASS (minor) | Bevelled hardware, real metres. The wheelhouse is a plain box with windows (fine at mid distance, f264) |
| G-SCENE-3 Busy | PASS | Hero boat, 6 crew, 8 crates + tuna tub, 2 boats + a small boat, headland, 8 gulls |
| G-SCENE-4 No clipping | PASS (visual) | Catch sits inside the crates and net. At f178-196 the camera passes 0.3-0.5 m from an A-frame leg and the bag. scene_audit was not run |
| G-SCENE-5 Water | PASS (minor) | No foam blotches (foam off). Particle drips fall from the bag with motion blur (f120+). The net is opaque above the water only, and the sea is opaque, so the net shows no underwater murk |
| G-SCENE-6 People | PASS (minor) | MPFB crew with varied ages, skin tones, builds and actions. Faces are mid-distance at f264. Around f215-225 faces pass about 3.5 m from the camera with motion blur |
| G-SCENE-7 Fish | PASS | Only ffish.asia CC0 scans (skipjack, yellowfin, green tiger prawn, greasyback), unlabelled |
| G-SCENE-8 Light | PASS (to verify) | Dawn sky with Physical Sky, sun 4->6 deg at az 95, no overlay. The sky is pale peach rather than deep marigold. Luma floor is checked by check-clip |
| G-SCENE-9 Setting | PASS | Indian working boat, plain flags, no text |
| G-SCENE-10 Camera | PASS (minor) | One eased flight. The approach (f1-80) is fast, so close objects get motion blur |
| G-SCENE-11 Continuity | n/a | f1 = BRIDGE_HORIZON: horizon at 46 %, lens 35, 3 m, sun az 95 / 4 deg, ocean seed 41. The lead equalises the join |
| G-SCENE-12 Story | PASS | "Landed at dawn": catch on ice, crew at the rail |

Four questions: not empty; mostly not toy-like (wheelhouse simple); nothing glaringly fake (crew is the weakest at close range in the pull-back); no clipping seen.
