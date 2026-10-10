# ASSET_LIBRARY.md — every Blender model, one by one

Rules for every asset
- Lives in `assets-src/blender/lib/<group>.blend` as a collection named by its ID; scenes LINK (not append) it, so a fix propagates everywhere.
- Real-world scale in metres, applied transforms, origin at base centre, bevelled edges, UV-unwrapped, PBR textures (albedo/roughness/normal, + metallic where needed) from Poly Haven or ambientCG (CC0, photo-scanned; record each in docs/LICENSES.md) plus a procedural wear mask layer (dirt, rust, scuffs, grime).
- **LOD:** L0 hero (close-up), L1 mid (≤ 30 % of L0 tris, Decimate), L2 far (≤ 10 %, or a baked impostor card for distant crowds/boats). Scenes pick LOD by distance with a geometry-nodes switch or by hand.
- Budgets below are L0 maximums; texture sizes are maxima.
- Every asset gets a PR still: 3 angles at 1920×1080 under neutral HDRI + one in-scene still. Checked against G-SCENE-1/2.
- Nothing from AI generators; no paid/login asset stores. Allowed sources: built by you in Blender, MPFB2 (MakeHuman, CC0 outputs), Poly Haven, ambientCG, the scans in ASSETS.md, public-domain elevation data.

Format: **ID — name** · purpose (where in the story) · reference description · budget (tris / textures) · LOD · animation/rig · acceptance criteria.

## Hero and products
1. **A-HERO-CARTON — Skylark master carton** · in every chapter 00–07 + live GLB in B1 · white/kraft double-wall corrugated export carton ~ 50×35×25 cm, printed "SKYLARK EXIM · VISAKHAPATNAM · INDIA" + species "VANNAMEI", flaps, tape, strapping; inside a frosted poly bag with 6 glazed 2 kg shrimp blocks · 12k tris / 2K (render), web GLB ≤ 500 KB with 1K WebP · L0/L1 · lid-open shape keys/armature (exported as glTF animation for B1) · fold lines visible, corrugation on cut edges, frost reads as frost, label only allowed text.
2. **A-PROD-TUNA — yellowfin tuna (scan)** · products B2, table (steak), sea catch · cleaned with `blender/clean_scan.py` then by hand: rebuild pectoral, dorsal and tail fins as clean solid fins (model + project scan texture), delete specks, paint out red blotches, keep eyes · 60k tris render / ≤ 500 KB web · L0/L1/L2 · none (turntable driven by site) · G-PROD all.
3. **A-PROD-PRAWN — green tiger prawn (scan)** · B2, table skewers (cooked shader variant), crates · cleaned, legs/antennae kept intact (thin geometry: check no holes), raw + glazed + cooked + peeled material/shape variants for the plant · 40k / ≤ 500 KB web · L0–L2 · none · G-PROD.
4. **A-PROD-PRAWN-ALT — tiger prawn by aniljaco (CC-BY)** · alternative if A-PROD-PRAWN fails G-PROD · already web-light (1.4 MB source) · credit in LICENSES.
5. **A-PROD-SKIPJACK — skipjack (scan)** · sea catch filler (never labelled) · cleaned · 30k · L1/L2 for heaps.
6. **A-PROD-SHRIMP-FILLER — greasyback shrimp (scan)** · crate/heap filler only · 20k · L1/L2 instanced.
7. **A-PROD-SWORDFISH — swordfish (modelled)** · B2 only if it passes G-PROD at close range · model from multiple side/top reference photos: long flat bill (~⅓ body), no scales look, high crescent dorsal, crescent tail, no pelvic fins, dark bronze-grey back to silver belly, subtle iridescence; sculpt muscle segments; hand-painted 2K texture · 50k / ≤ 500 KB web · L0 · none · if it looks CG at 100 % zoom: omit from 3D and keep swordfish as a text entry.
8. **A-PROD-PLINTH — ice-slab plinth** · B2 stage · rectangular block of clear ice with bubbles and chipped edges, glossy wet top · 4k (+ normal map) · L0 · none · reads as ice, not glass.

## Vessels
9. **A-VESSEL-FEEDER — feeder container ship (~150 m)** · v-reefer, v-port · weathered red-brown hull with rust streaks and waterline grime, white accommodation block aft with bridge wings, cranes-less deck with cell guides and lashing bridges, mooring winches, lifeboat, funnel without logo, anchor and hawse pipes · 250k / 4K hull + trim sheets · L0/L1/L2 · subtle pitch/roll; mooring lines (v-port) · containers sit in bays aligned, no crosswise boxes (v3 fail), hull never intersects quay.
10. **A-VESSEL-TUG ×2 — harbour tugs** · v-port · Indian port tug, red/black hull, tyre fenders, push knees · 60k / 2K · L0/L1 · prop wash particles · water wash at stern.
11. **A-VESSEL-PILOT — pilot boat** · v-port distance · 20k / 1K · L1/L2 · moving with wake.
12. **A-VESSEL-FISHING-A — hero mechanised fishing boat** · v-sea · Vizag-style ~15 m boat: painted hull (blue/white/red bands, eye motif optional), wheelhouse, mast with flags (no text), net drum/winch, tyre fenders, rust, chipped paint, deck crates, ice hold hatch · 150k / 4K · L0/L1 · rocks on swell; winch turns · hull reads as an Indian working boat, not a yacht.
13. **A-VESSEL-FISHING-B — background fishing boats** · v-sea, v-port distance · 2 colour variants of A-hull simplified · 25k / 1K · L1/L2 · swell motion.
14. **A-VESSEL-COUNTRY — small country boat** · v-sea distance, v-pond horizon optional · 8k / 1K · L2.

## Port
15. **A-PORT-STS ×3 — ship-to-shore cranes** · v-port · Indian terminal STS crane (blue-grey, rust streaks): A-frame, boom raised/lowered, trolley, operator cabin, ladders, stairs, festoon cables, rail wheels, warning stripes · 200k / 4K trim sheets · L0/L1 · trolley + hoist rig driving A-PORT-SPREADER and wire-rope curves · ropes always taut and attached.
16. **A-PORT-SPREADER — telescopic spreader** · v-port · yellow spreader spanning the container length, 4 corner twistlocks (rotating), guide flippers, hydraulic hoses, hoist sheaves · 30k / 2K · L0 · twistlock rotation, flippers down · locks visibly on the four corner castings.
17. **A-CONT-40RF — 40-ft reefer container** · v-reefer, v-port, v-cold door bridge · white corrugated walls, reefer unit at front (fan grille, panel, plug cable), rear doors with 4 locking bars + cam keepers, corner castings, ISO dimensions 12.19×2.44×2.90 m (HC), unreadable stencils · 20k / 2K + wear · L0/L1/L2 instanced · doors open rig.
18. **A-CONT-40RF-INT — reefer interior** · v-reefer · aluminium T-floor, white stainless walls, air chute, LED · 15k / 2K · L0.
19. **A-CONT-40DRY / A-CONT-20DRY — dry containers** · v-reefer, v-port · corrugated, 8 colour variants (maroon, blue, green, grey, orange, white…) × 3 weathering levels, no real line logos · 12k / 2K · L0/L1/L2 instanced.
20. **A-PORT-QUAY — quay apron** · v-port · concrete with joints, crane rails, bollards, fenders, puddles, oil stains, painted lanes (worn), light towers · 50k / 4K tiled + decals · L0.
21. **A-PORT-TT ×4 — terminal tractors + chassis** · v-port · 25k / 2K · L1 · driving paths.
22. **A-PORT-RS — reach stacker** · v-port · 40k / 2K · L1 · lifts a box.
23. **A-PORT-DOCDESK — documentation canopy desk** · v-port · canopy, table, chairs, clipboard, sheaf of papers (unreadable lines), stamp pad, laptop · 15k / 2K · L0 · page turns.

## Road and plant exterior
24. **A-TRUCK-REEFER — Indian reefer truck** · v-truck, v-port · Tata Signa / Ashok Leyland style cab: proper grille, bumpers, mirrors on arms, sun visor, wipers, blank plate, insulated white body with reefer unit on the front, rear doors + seals, side underrun guards, mud flaps, mud/road grime on lower body, rust on chassis · 120k / 4K · L0/L1 · doors open, wheels turn, suspension bob · cab not boxy, never clips the dock.
25. **A-PLANT-EXT — Anandapuram plant exterior and dock** · v-truck · PUF-panel building, dock levellers with seals and scuffed bumpers, yard with tyre marks, oil stains, drain covers, a security cabin, signboard without text · 150k / 4K · L0/L1.
26. **A-VEH-2W, A-VEH-AUTO, A-VEH-BUS — Indian traffic** · v-truck, v-pond road · motorbikes/scooters ×3 variants, auto-rickshaw, bus · 15–40k / 1K · L1/L2 · driving.
27. **A-ENV-ROAD — Anandapuram–Pendurthi road tile** · v-truck · two-lane asphalt with worn edges, gravel shoulders, trees, roadside stalls, power poles, hills · terrain 300k / 4K · L0/L1.

## Plant interior
28. **A-PLANT-COLDSTORE** · v-cold · PUF walls, insulated doors, strip curtains (A-CURTAIN), high-bay racks (frost), pallets with stretch-wrapped cartons (instanced A-CARTON-PALLET), evaporator units, LED, floor frost edges · 400k instanced / 2K · L0/L1.
29. **A-FORKLIFT — electric reach truck** · v-cold · 60k / 2K · L0 · mast lift, reach.
30. **A-CARTON-PALLET — pallet of master cartons** · v-reefer, v-cold, v-pack · 4k / 1K · instanced.
31. **A-PLANT-PACK — packing hall** · v-pack · stainless tables, A-CARTON-ERECTOR, A-STRAPPER, label printer, pallet jack, roll conveyors · 200k / 2K · L0/L1.
32. **A-IQF — IQF freezer outfeed + glazing** · v-freeze · stainless spiral/tunnel housing, mesh belt, glazing spray bar, frost, vapour · 120k / 2K · L0 · belt scroll, spray particles.
33. **A-PLANT-LAB — lab unit** · v-qc · bench, balance, probe thermometer, sample trays/bags, glassware, sink, cabinets, window · 60k / 2K · L0 · (no microscopes).
34. **A-GRADER — roller grading machine** · v-grade · rollers, chutes, hopper, crates beneath · 80k / 2K · L0 · rollers turn, rigid-body shrimp.
35. **A-PEEL-TABLE — peeling/deveining table** · v-peel · long stainless table with ice bed, trays, bowls, tools · 20k / 2K · instanced ×2.
36. **A-WASH-TANK — receiving wash tank** · v-wash · stainless tank, inflow pipe, overflow to floor gutter, basket · 25k / 2K · water sim or animated displacement + particles, water stays inside.
37. **A-SCALE, A-CRATE-SHRIMP, A-CRATE-FISH, A-ICE-CRUSHED, A-ICE-FLAKE** · plant, pond, sea · perforated plastic crates (blue/red/green, scuffed), ice as instanced chunks with refraction · 2–6k each / 1K · instanced, rigid-body settled.
38. **A-CURTAIN — PVC strip curtain** · v-cold, v-pack · cloth sim strips · 2k.

## Farm and sea environment
39. **A-ENV-SEA — ocean** · v-reefer, v-port, v-sea, bridges · Ocean modifier (seed 41), foam via dynamic paint/attributes, glossy + transmission shader (no diffuse shadow-catcher), depth colour · procedural · bow wave/wake from geometry nodes + particles.
40. **A-ENV-COAST — Vizag coastline + headland** · v-port, v-truck aerial, v-sea · terrain from public-domain elevation (SRTM) around Visakhapatnam, beaches, vegetation scatter, town blocks in the distance (generic, no landmarks named) · 500k / 4K · L1/L2.
41. **A-ENV-BREAKWATER** · v-port · tetrapods/rock armour instanced · 100k instanced.
42. **A-ENV-PONDS — aquaculture pond grid** · v-pond, v-truck aerial · ponds with water (volume absorption), textured bunds (grass tufts, wet mud edge, footpaths, ruts), drains, sluice gates · terrain 400k / 4K · L0/L1.
43. **A-AERATOR — paddle-wheel aerator** · v-pond · floats, motor, paddle wheels, cable to bund · 8k / 1K · wheels spin, foam trail particles confined to pond.
44. **A-VEG-PALM ×6 variants, A-VEG-TREE ×4 (neem, casuarina, mango, banana), A-VEG-SHRUB, grass** · v-pond, v-truck, v-port · varied height/lean/fronds, wind sway · 10–40k / 2K · L0–L2 + scatter.
45. **A-SHED, A-BIKE, A-SACK-FEED** · v-pond · tin-roof shed with rust, motorbike, feed sacks (no readable brand) · 5–30k / 1K.
46. **A-NET-HAUL — fishing net** · v-sea · cloth sim with mesh opacity, floats, ropes, catch inside (rigid bodies) · 60k · water draining particles.
47. **A-NET-BAG — pond harvest bag net** · v-pond · cloth sim, shrimp packed inside, sits in water until lifted · 30k.
48. **A-FX-GULL, A-FX-EGRET — birds** · v-sea, v-port, v-pond · rigged flapping loops, boids particles · 5k each.
49. **A-MAP — relief map plane** · B4 still · see SCENES.md S9.

## People (MPFB2/MakeHuman base meshes, CC0 outputs; Rigify or MPFB rig; clothing as separate meshes with cloth sim or sculpted folds)
Every person: unique face (shape keys), skin texture with pores/subsurface, eyebrows/hair (particle or cards), real clothing with folds, footwear, natural pose with weight shift; hand-keyed animation with variation; L0 (≤ 60k incl. clothes) / L1 (≤ 15k) / L2 impostor for distant crowds.
50. **P-DINER-1/2** · v-table · hands/forearms + partial torsos, a shirt cuff and a sweater sleeve, a ring/watch · gripping cutlery.
51. **P-PORT-1…10** · v-port · lashing crew (hi-vis vests, helmets, gloves, work boots), 2 documentation staff (formal shirts, lanyards), crane operator in cabin, tractor drivers.
52. **P-YARD-1…4** · v-truck · truck driver, signalling worker (hi-vis, waving back the truck from the side), dock hand, security guard.
53. **P-COLD-1** · v-cold · thermal suit, hood, gloves, on the reach truck.
54. **P-PLANT-1…24** · v-pack, v-freeze, v-grade, v-peel, v-wash · white coats/aprons, hairnets, face masks, gloves, white gumboots; women and men, varied ages; ≥ 8 unique bodies re-dressed for 24.
55. **P-LAB-1** · v-qc · lab coat, hairnet, mask, nitrile gloves.
56. **P-FARM-1…6** · v-pond · cotton shirts, lungis/shorts, towels, caps; harvest crew wet to the knee.
57. **P-CREW-1…6** · v-sea · T-shirts, lungis/shorts, oilskins on two, gloves, caps; final portrait at the rail.

## Bridges (linked collections shared by two .blend files — STORYBOARD.md)
58. **BRIDGE_FROST** (table ↔ reefer) · 59. **BRIDGE_SEA** (reefer ↔ port) · 60. **BRIDGE_DOOR** (port ↔ plant-cold) · 61. **BRIDGE_BELT** (plant-cold ↔ plant-line) · 62. **BRIDGE_DOCK** (plant-line ↔ truck) · 63. **BRIDGE_COAST** (truck ↔ pond) · 64. **BRIDGE_HORIZON** (pond ↔ sea). Each = camera state (via `blender/boundary_camera.py`) + the surface object + light/world. Acceptance: `scripts/boundary-check.sh` OK.
