# SCENES.md — every Blender scene, one by one (PM briefs)

Build order = render priority (the opening and the biggest "wow" first): **1 table → 2 port → 3 reefer → 4 sea → 5 pond → 6 truck → 7 plant-cold → 8 plant-line → 9 map still → 10 product turntable fallbacks (only if needed)**. Frame ranges: `scripts/scenes.sh`. Camera/caption/boundary details: STORYBOARD.md. Assets: ASSET_LIBRARY.md (IDs in brackets). Gates: QUALITY_GATES.md G-SCENE-1…12.

Common to every scene
- Render: EEVEE, 1920×1080, 24 fps, AgX (look per kind), 64 samples, motion blur 0.5, ray tracing half-res; applied by `blender/render_settings.py`. Preview: 960×540, 16 samples, no motion blur.
- Build with linked collections from `assets-src/blender/lib/*.blend` (ASSET_LIBRARY) so the same object is identical in every file; bridges (`BRIDGE_*`) are linked collections too.
- Lighting: Nishita/physical sky + sun for exteriors (Poly Haven CC0 HDRI allowed for reflections), area/practical lights for interiors. Exposure never pushed down to "moody"; no compositor overlays.
- Never run a render inside an MCP call. Save, then `scripts/render-scene.sh <blend> preview` in the background (`&` + log to `logs/`).
- Each .blend ≤ ~1.5 M visible tris per frame (instancing for crowds/containers), textures ≤ 4K hero / 2K others / 1K background, so a frame renders in ≤ ~12 s on an M-series Mac. Measure the first preview frame time and log it; if > 15 s/frame at full res, simplify (instancing, lower texture res, fewer lights) before the full render.

---

## S1 · table.blend → v-table (1–216, 9 s)  · kind int
**Purpose:** first impression; the buyer's world; introduce the hero carton. Must look like a premium food-photography film, not a CG kitchen.
**Reference description:** evening dinner for two in a modern apartment: oak table, linen, ceramic plates, warm pendant light + cool window fill; a kitchen counter behind with the opened master carton, frosted inner bag, glazed shrimp blocks.
**Contents & density:** table, 2 chairs, 2 diners (hands/forearms + partial torsos only, sleeves, a watch; [P-DINER-1/2]), plates with grilled shrimp skewers (A-PROD-PRAWN cooked shader ×10) and seared tuna steak (sculpted from A-PROD-TUNA flesh texture), greens, lemon, glasses with water/wine (real refraction), bread, napkins, cutlery, phone; counter with A-HERO-CARTON (open), kettle, bowl, cutting board, a plant; window with soft out-of-focus city lights (generic bokeh, no landmarks).
**Animation:** hands cut and lift a skewer (IK, fingers gripping), slight steam from the plate (smoke sim, subtle), candle flicker; frost on the carton bag glints as the camera passes.
**Realism checklist:** food has subsurface + specular; cutlery reflections; no CG-perfect symmetry; crumbs and a small sauce smear; linen wrinkles; glazed blocks show ice glaze over shrimp.
**Acceptance:** G-SCENE all; the plate reads as appetising in the first 2 seconds; boundary BRIDGE-FROST at f216.

## S2 · port.blend → v-port (1–264, 11 s)  · kind ext
**Purpose:** scale and professionalism; documentation; the "wow" crane shot Tarun asked for in v3 (clear container placement).
**Reference description:** an Indian container terminal at Visakhapatnam on a clear day: blue-grey STS cranes with rust streaks, a feeder ship at the quay with mixed weathered containers, a long yard of stacks, terminal tractors, a reach stacker, lashing crew in hi-vis + helmets, a canopy desk with documentation staff, the headland and breakwater behind, a few clouds.
**Contents & density:** sea + breakwater [A-ENV-SEA, A-ENV-BREAKWATER], coastal terrain + headland [A-ENV-COAST], quay [A-PORT-QUAY], 3× STS crane [A-PORT-STS ×3 with A-PORT-SPREADER], feeder ship [A-VESSEL-FEEDER] with ≥ 120 containers on deck in proper bays, 2 tugs [A-VESSEL-TUG] near the bow, 1 pilot boat [A-VESSEL-PILOT], yard ≥ 300 containers instanced [A-CONT-40RF, A-CONT-40DRY, A-CONT-20DRY, varied colours/weathering], 4 terminal tractors + chassis [A-PORT-TT], 1 reach stacker [A-PORT-RS], 1 reefer truck with second reefer at the quay [A-TRUCK-REEFER + A-CONT-40RF], light towers, bollards, mooring lines, ≥ 10 people [P-PORT-*], documentation canopy desk [A-PORT-DOCDESK: clipboard, papers with unreadable lines, stamp, laptop].
**Animation:** STS trolley + spreader descend with the white reefer: hover 1.5 m above slot (contact shadow visible), slow 2 s landing onto corner castings, twistlocks rotate; wire ropes stay taut (curve object driven by trolley); tractors drive; tugs push with wash; crew walk; flags and mooring lines sway; sea animated (Ocean modifier) with ship moored (no wake), tugs with prop wash.
**Realism checklist:** containers corrugated with doors/locking bars/corner castings, reefer units on reefers; stacks with gaps; lashing bars; cell guides on the ship; crane ladders, cabins, festoon cables; puddles/oil stains on the quay; no hard ship shadow on water; no dark overlay.
**Acceptance:** G-SCENE all; the landing frame still (f205) exported to the PR; boundary in BRIDGE-SEA (f1), out BRIDGE-DOOR (f264).

## S3 · reefer.blend → v-reefer (1–192, 8 s)  · kind ext
**Purpose:** the cold chain at sea; transition from the table's frost to the open sea.
**Reference description:** the inside of a 40-ft reefer (aluminium T-floor, white walls, airflow chute, frost haze) with stacked cartons; then a feeder ship underway in open sea, containers on deck, white reefer with its unit and plug cable.
**Contents & density:** reefer interior [A-CONT-40RF-INT], 18+ pallets of cartons [A-CARTON-PALLET] with the hero carton on top front, cold mist volume; exterior: A-VESSEL-FEEDER underway (same ship asset as port), ≥ 120 containers, A-ENV-SEA open ocean, bow wave + wake foam (Ocean foam + particle spray + displacement), gulls ×4 [A-FX-GULL].
**Animation:** camera move per STORYBOARD; ship moving at ~12 kn with pitch/roll 1–2°; wake foam trails; reefer fan spinning.
**Realism checklist:** no camera passing through solid geometry (doors open, cut-away reveal); ship hull rust streaks, waterline grime; sea colour deep blue-green with sky reflection; no shadow-floor on water (shadow catcher off for the ocean; ocean uses glossy/transmission, not diffuse).
**Acceptance:** G-SCENE all; boundaries BRIDGE-FROST (f1), BRIDGE-SEA (f192).

## S4 · sea.blend → v-sea (1–264, 11 s)  · kind dawn
**Purpose:** the source and the people; emotional end of the film.
**Reference description:** Indian mechanised fishing boat (Vizag style: wooden or steel hull painted blue/red/white, wheelhouse aft or forward, mast with nets and small flags, tyres as fenders, rust and weathering) at dawn; crew of 6 in T-shirts, lungis/shorts, some in oilskins, gloves and caps; catch on deck in crates with crushed ice; coastline with a headland silhouette; 2–3 other boats on the horizon.
**Contents & density:** A-VESSEL-FISHING-A (hero), A-VESSEL-FISHING-B ×2 (distance), A-VESSEL-COUNTRY ×1 (small catamaran-type boat, distance), A-ENV-SEA dawn, A-ENV-COAST dawn, net [A-NET-HAUL with cloth sim, mesh opacity map], crates [A-CRATE-FISH ×8] with crushed ice [A-ICE-CRUSHED], scans: tuna ×3, skipjack ×4, mackerel (model from skipjack scan reshaded only as unlabelled filler — or omit), sea shrimp (greasyback + green tiger prawn scans) heaps; people P-CREW-1…6; gulls ×8.
**Animation:** boat rocking on Ocean swell (follows surface via geometry nodes or keyed to wave sampling), net hauled by winch with cloth sim and water draining as particles (droplets with motion blur), crew pull/sort cycles (hand-keyed on Rigify/MPFB rig, hands gripping), gulls flying, sun rising 2° over the shot.
**Realism checklist:** catch stays inside crates and the net; deck wet with puddles and reflections; no stiff mannequins; faces only mid-distance, backlit rim at dawn; varied skin tones and builds; no yacht/teak deck (v3 fail); horizon straight.
**Acceptance:** G-SCENE all; boundary in BRIDGE-HORIZON (f1); last frame is a strong poster (used in B5).

## S5 · pond.blend → v-pond (1–216, 9 s)  · kind dawn
**Purpose:** partner farms; step 1 for farmed shrimp.
**Reference description:** coastal Andhra aquaculture: grid of rectangular ponds with earthen bunds, paddle-wheel aerators churning foam lines, sheds with tin roofs, coconut palms of varied height/lean, neem and casuarina trees, shrubs, footpaths, a two-wheeler parked, feed sacks, farmers in cotton shirts/lungis with towels on shoulders, a harvest crew in shorts in knee-deep water at the drain with a bag net, crates of ice on the bund, sunrise mist, egrets.
**Contents & density:** A-ENV-PONDS terrain (≥ 12 ponds visible from the aerial), A-AERATOR ×10 (working: wheels turn, foam trails stay in-pond), A-VEG-PALM ×40 (6 variants), A-VEG-TREE ×30, A-VEG-SHRUB/grass scatter, A-SHED ×3, A-BIKE ×1, A-SACK-FEED ×12, A-CRATE-SHRIMP ×6 with ice and shrimp, harvest net bag [A-NET-BAG cloth], people P-FARM-1…6, egrets ×6 [A-FX-EGRET].
**Animation:** aerators, net bag lifted out of the water (water draining as particles + dripping), farmers' natural work cycles, birds, mist drift, sun rising.
**Realism checklist:** pond water with depth colour, murk (volume absorption), refraction; sun glint as a surface highlight only; bunds textured (grass tufts, wet mud edge, ruts); nothing floating above water; no foam on bunds; no cloned palms in a row.
**Acceptance:** G-SCENE all; boundaries BRIDGE-COAST (f1), BRIDGE-HORIZON (f216).

## S6 · truck.blend → v-truck (1–216, 9 s)  · kind ext
**Purpose:** chilled transport; link plant ↔ source; the Indian setting.
**Reference description:** Anandapuram plant exterior in morning light: dock with seal and bumpers, yard with tyre marks and oil stains, an Indian reefer truck (Tata Signa / Ashok Leyland style cab, insulated white box with a reefer unit on the front, mud on lower body), wheel chock, a signalling worker in hi-vis waving from the side, a dock hand at the door; then the Anandapuram–Pendurthi road: two-lane asphalt with worn edges, trees, roadside stalls, two-wheelers, an auto-rickshaw, hills; rising to the coastal aerial.
**Contents & density:** A-PLANT-EXT (facade, dock, yard), A-TRUCK-REEFER (hero), A-TRUCK-REEFER variant parked, A-VEH-2W ×4, A-VEH-AUTO ×1, A-VEH-BUS ×1 (distance), A-ENV-ROAD terrain tile + A-ENV-COAST, A-VEG-* scatter, people P-YARD-1…4, crates on ice inside the truck body.
**Animation:** dock hand pulls the truck door, signaller waves, traffic moves on the road (correct side: left-hand traffic), camera flight per STORYBOARD.
**Realism checklist:** blank/unreadable number plates; grime and rust streaks; scuffed dock bumpers; correct cab proportions (not boxy); truck never inside walls (v3 fail); left-hand traffic.
**Acceptance:** G-SCENE all; boundaries BRIDGE-DOCK (f1), BRIDGE-COAST (f216).

## S7 · plant-cold.blend → v-cold (1–192), v-pack (192–383), v-freeze (383–574)  · kinds cold/int/cold
**Purpose:** steps 8, 7, 6 in one continuous interior flight.
**Reference description:** a modern Indian shrimp processing plant: insulated PUF panel walls, epoxy floors with drains, stainless equipment, LED panels, strip curtains; cold store with high-bay racks and frosted pallets; packing hall; IQF spiral/tunnel freezer outfeed with glazing curtain.
**Contents & density:** A-PLANT-COLDSTORE (racks ≥ 10 bays × 5 levels, ≥ 150 pallets instanced), A-FORKLIFT (electric reach truck) + operator P-COLD-1 in thermal suit, strip curtains [A-CURTAIN cloth], cold mist volumes; packing hall A-PLANT-PACK (tables, A-CARTON-ERECTOR, A-STRAPPER, label printer, pallets being built) with 8 staff P-PLANT-* in full PPE; A-IQF (belt, housing, glazing spray, frost) + 2 staff; the hero carton through all of it.
**Animation:** reach truck lowers pallet; curtain strips part as the camera passes (cloth); packers fold, tape, label, strap (hand-keyed loops with variation, offset so no two move in sync); IQF belt scrolling (UV/geometry), glazing spray particles; mist drifting.
**Realism checklist:** PPE complete on every staff member; frost on cold surfaces only; floor wet near the IQF, dry in packing; no salmon, no fish fillets (shrimp only); no microscopes; labels only the allowed text.
**Acceptance:** G-SCENE all; boundaries BRIDGE-DOOR (f1), BRIDGE-BELT (f574); internal shared frames 192 and 383 are automatic (same file).

## S8 · plant-line.blend → v-qc (1–192), v-grade (192–383), v-peel (383–574), v-wash (574–765)  · kind int
**Purpose:** steps 5, 4, 3, 2 in one continuous interior flight.
**Reference description:** same plant language as S7. Lab unit with bench, balance, probes, sample trays, sink, fume-free clean bench, window to the line; roller grader; long peeling tables with ice; receiving bay with wash tank, scale, crates, dock door.
**Contents & density:** A-PLANT-LAB + P-LAB-1; A-GRADER + 6 staff; A-PEEL-TABLE ×2 with 24 staff (instanced variations, ≥ 8 unique people models re-dressed), trays of shrimp at each stage (head-on, headless, peeled — scans with deformation/texture variants); A-WASH-TANK with water sim/flow + 3 staff; A-SCALE, A-CRATE-SHRIMP ×20, ice flakes; dock door to BRIDGE-DOCK.
**Animation:** technician probes and weighs; grader rollers turn, shrimp drop down chutes (rigid-body bake); peeling hand loops (varied); crates tipped into tank, water flowing down and staying in the tank; drains.
**Realism checklist:** see S7; hands contact shrimp; water physics G-SCENE-5; no identical neighbouring workers.
**Acceptance:** G-SCENE all; boundaries BRIDGE-BELT (f1), BRIDGE-DOCK (f765).

## S9 · map.blend → markets-map still
**Purpose:** B4 markets backdrop (distinct from v3's globe).
**Build:** plane with Natural Earth / NASA public-domain elevation (e.g. GEBCO/ETOPO public data, credit in LICENSES) as displacement + relief shading, equirectangular crop 20°W–150°E, 10°S–65°N, ink sea `#0E1417`, glaze land `#BFD3D6`, soft top-left light, no labels, no borders. Orthographic camera so the SVG overlay projection matches exactly (store the lon/lat → pixel transform in `src/config/map.ts`).
**Acceptance:** projection test: Visakhapatnam dot lands on the coast within 4 px at 1920 width.

## S10 · prod-*.blend → turntable fallbacks (only if a live GLB fails G-PROD)
360° turntable on the ice-slab plinth (A-PROD-PLINTH), studio HDRI, 120 frames, encoded like any clip; used in B2 in place of the live model.

## OG still
table.blend f1 re-framed for 1200×630 with the wordmark space on the left (`scripts/render-still.sh og-image`).
