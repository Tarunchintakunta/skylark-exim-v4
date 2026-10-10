# pond.blend — full-quality review r1 (1920x1080, saved .blend settings, stills in assets-src/blender/stills/pond/r5..r12_*_full.png)

First impression: the aerial now reads as a real coastal Andhra farm belt: a patchwork of paddy / pasture / straw / ploughed fields with field bunds and farm tracks, coconut rows along the tracks, five hamlets of pastel plaster houses with tin or RCC roofs, gentle relief, then the 16-pond farm with long aerator wakes in every pond. The low pass shows murky plankton-green water with wind ripples and cat's-paw patches instead of a sky mirror; the harvest close-up has a drag net with an orange float line around the waders, and the crew wear coloured checked lungis instead of all-white robes.

Fixes vs pond-r2 known issues
- Aerators: 29 units, each running one leaves a 28 m foam trail (13 m in the harvest pond, ending mid-pond), boiling white water at the wheels, spray curtains behind the paddles, and a darker churned-silt plume. The foam is now BLENDED: the ray-traced-refraction water layer was painting over the dithered foam, so trails disappeared at grazing angles (f108). Trails stay inside each pond (the foam plane sits 8 mm above the water and goes under the bund wherever the bank rises).
- Water: volume removed (also faster). Turbid green-brown body colour with per-pond variation, transmission 0.26, specular 0.22, two moving ripple layers + gust patches, roughness 0.09-0.28. Far ponds vary from plankton green to silty olive.
- Net IN the water: an arc-shaped seine (4 cm diamond mesh) from bank to bank around the crew, following the bed, head rope + orange floats on the surface, stakes at both ends; below the surface it fades to the murk colour with depth and is only seen refracted.
- Land: relief up to about 2 m away from the farms; rectangular field patchwork with bunds and tracks (shader, 'field' mask, kept off the farm and the low-pass corridor); about 240 coconut palms in rows along the tracks (489 far palms in all); 50 houses in 5 hamlets; tree clumps doubled (412 trees). Mist sheets fade out beyond 60-150 m, so the ponds no longer show white "cloud" blobs from the aerial.
- People: P1 and P5 now wear green and maroon checked lungis (P2 already blue). From 6 m and further they no longer read as white robes.

Four questions: empty? no (fields, rows, hamlets, aerators). Toy-like? Houses are simple boxes but stay at 150 m or more, hazed and only in the aerial. Fake? The lungi pullers in f130-150 still stand stiffly; their faces are at least 6 m from camera. Clipping? None seen: the net follows the bed and the stakes are 1.5 m tall, so the camera passes about 1 m over them.

| Gate | r1 | Frames / notes |
|---|---|---|
| G-SCENE-1 Realism | PASS | PBR terrain, plaster, tin, bark; procedural only on water, foam, leaves |
| G-SCENE-2 Not toy-like | PASS (minor) | houses simple but far (f1-45) |
| G-SCENE-3 Busy | PASS | f1/f22 fields + palms + hamlets + 16 ponds with wakes; f150-172 crew of 5, net, crates |
| G-SCENE-4 Clipping | PASS | f150/f172 net on the bed, waders in the water |
| G-SCENE-5 Water | PASS | f60/f108 trails on the water only, f130 churn, f172 murky water with refraction, net in the water |
| G-SCENE-6 People | PASS (minor) | f172 coloured lungis; pull poses a little stiff |
| G-SCENE-7 Shrimp | PASS | unchanged (CC0 scan in bag + crates) |
| G-SCENE-8 Light | PASS | luma ok on every still (mean 133-203, sd 22-55) |
| G-SCENE-9 Setting | PASS | Andhra fields, palms, hamlets, lungis |
| G-SCENE-10 Camera | PASS | unchanged path |
| G-SCENE-11 Continuity | PASS (spec) | f1 BRIDGE_COAST and f216 BRIDGE_HORIZON unchanged (camera, lens, sun, ocean res 10 from f186) |
| G-SCENE-12 Story | PASS | |

Luma (r10-r12): f1 136/22, f22 139/25, f60 164/50, f108 186/47, f130 188/47, f150 170/54, f172 133/55, f194 180/53, f216 203/27: all ok.

Perf: 32 spp (no visible noise on the f172 close-up), 4 shadow steps, sun shadow max res 8 mm, shadow scale 0.5, trace_max_roughness 0.3, no water volume. Ocean at res 8 until f185, then res 10 (second modifier; show_render keyed). Things the camera cannot see are hidden: far land after f112, crew before f50, and every land object after its last frame inside the frustum (bounding-box test, f170+). Measured on the shared GPU while 4-6 other renders ran: f1 7-8 s, f22 7-11 s, f60 15-23 s, f108 13-18 s, f130 17-25 s, f150 11-18 s, f172 11-18 s, f194 12-13 s, f216 7-9 s. The r4 times were 18-24 s per frame plus a 69 s first frame.

Known: the sea is static. The ocean time driver is frame/24-9, which clamps to 0 for the whole shot; this is unchanged because the f216 bridge needs time=0. The lungi pullers' poses are a little stiff.
