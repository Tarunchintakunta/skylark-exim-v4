# STORYBOARD.md — shot by shot, opening to footer

Conventions
- Frames at 24 fps. Frame ranges and blend names are the single source of truth in `scripts/scenes.sh` (they match this file; if you change one, change both in the same commit).
- **Scroll** = desktop pinned length in `vh` (≈ 40 vh per second of clip). Mobile = 0.8 × desktop. Scroll maps linearly to clip time, with GSAP `scrub: 0.6` smoothing.
- **Type zone** = the area of frame the camera keeps calm (sky, wall, sea, shadow) for the countdown numeral and the headline. Subject and faces never sit in it. Mobile type zone is always the lower 38 % of the portrait crop (bottom-safe area), with a 0→35 % ink gradient *only behind the text block* (not a full-frame overlay).
- **Mobile crop:** 960×540 tier played in a portrait viewport with `object-fit: cover` and a per-chapter `object-position` (given below) so the subject stays in frame.
- **Captions** come only from CONTENT.md (reference in brackets). Headlines without facts are creative copy.
- Every caption animates in with SplitText (lines, then words, 0.9 s, `power3.out`, y 110 % → 0, rotate 0) when the chapter is 8 % in, and out at 88 %. Exactly one headline visible at any time. Countdown numeral rolls (yPercent −100 / 0 / 100) at chapter boundaries.
- **Boundary** = the exact frame shared with the neighbouring clip (SSIM ≥ 0.99, `scripts/boundary-check.sh`).

---

## Loader (0 – first paint)
No progress bar, no percentage. Ink screen; the Skylark wordmark (SVG traced from the logo) fades in at 60 % opacity; as soon as the v-table 1920/1280/960 *poster* has decoded (≤ 180 KB) and fonts are ready, the wordmark scales down into the header position (0.8 s) and the poster fades up. Max 1.2 s on Fast 4G; if fonts are late, swap anyway. The first clip is requested on the first wheel/touch/keyboard scroll (TRD §6).

---

## 00 · v-table — "Trace it back."  (table.blend 1–216, 9.0 s, 360 vh)
- **Set:** a buyer's dining table in a warm modern apartment abroad, early evening; window light + practical pendant lamp. No flags, no landmarks, no identifiable city.
- **Camera:** starts as a macro top-down on a white plate: grilled shrimp skewers (vannamei, from A-PROD-PRAWN, cooked shader variant) and a seared tuna steak on a bed of greens, two hands with cutlery entering (f1–60). Slow crane up and back to a 3/4 view of the table for two (f60–130): glasses, bread, linen napkins, a phone face-down. Then a lateral dolly to the kitchen counter behind, where the **opened Skylark master carton** (A-HERO-CARTON) sits with frosted glazed shrimp blocks inside (f130–190). Final push-in into the frost on the carton's inner bag until frost crystals fill the frame (f190–216).
- **Type zone:** upper-left third (dim wall / window) for f1–130; left half (dark cabinet) f130–216.
- **Copy:** eyebrow "Skylark Exim · Visakhapatnam" [C1] · headline **"Trace it back."** · line "Before it reached this table, it came a long way. Scroll to follow it home." (creative, no claim). At 70 %: hint "Scroll" with a 1 px marigold line (fades out after first scroll, never a pill).
- **Boundary out (f216) = BRIDGE-FROST:** frost-crystal macro, lens 100 mm, f/2.8, camera axis −Z, frost material M-FROST-BRIDGE, white balance 6500 K. Linked collection `BRIDGE_FROST` used identically in reefer.blend f1.
- **Mobile:** object-position 60 % 50 % (plate then carton centre). 
- **Alt:** "A dinner table with grilled shrimp and tuna; an opened Skylark Exim carton of frozen shrimp on the counter."

## 09 · v-reefer — "Under a cold seal."  (reefer.blend 1–192, 8.0 s, 320 vh)
- **Set:** inside a 40-ft reefer container, then the container stack on a feeder container ship at sea, bright late morning.
- **Camera:** from BRIDGE-FROST (f1) the frost pulls out of focus to reveal the same carton on a pallet inside the reefer: stacked cartons, T-floor, airflow chute, cold mist (f1–60). Camera tracks backward down the aisle toward the doors; the doors are open as a cut-away (no wall passing through objects) and the camera exits into daylight (f60–110), rises up past the reefer unit (fan grille, plug cable, status lamp) and the container stack (lashing bars, twistlocks, varied weathered boxes) to a high aerial of the ship cutting through the sea, bow wave and wake correct (f110–170). Final tilt down to a top-down of open sea beside the hull (f170–192).
- **Type zone:** right half dark container wall (f1–110); sky band top 35 % (f110–170).
- **Copy:** countdown **09** · eyebrow "Step 9 · Export documentation & logistics" [§5.9] · headline **"Under a cold seal."** · line "Shipped in reefer containers that keep the cold chain unbroken to the destination." [§5.9]
- **Boundary in:** BRIDGE-FROST. **Boundary out (f192) = BRIDGE-SEA:** top-down open sea, camera 60 m above, lens 35 mm, Ocean modifier seed 41, time = 0, sun azimuth 135°, elevation 52°; linked collection `BRIDGE_SEA` (same ocean object + sun + world) used identically in port.blend f1.
- **Mobile:** object-position 50 %; aerial reframed to keep the hull centred.
- **Alt:** "Cartons of frozen shrimp inside a refrigerated container, then the container ship at sea."

## 09 · v-port — "Papers before ports."  (port.blend 1–264, 11.0 s, 440 vh)
- **Set:** Port of Visakhapatnam container terminal, clear day, busy. Feeder ship alongside the quay; 3 weathered ship-to-shore (STS) cranes; container yard with straddle stacks; terminal tractors; reach stacker; crew; the plant's reefer truck arriving.
- **Camera:** from BRIDGE-SEA (f1) the camera rises and flies backward toward the coast (f1–70): breakwater, the headland, the harbour channel. It glides along the ship's side at deck height (f70–150) to a **3/4 side angle** on the middle STS crane lowering the **white reefer container (with the hero cartons inside) onto its slot**: spreader locked at four corners, wire ropes taut, container hovering 1.5 m above the slot with a contact shadow (f150–200), then landing exactly on the corner castings of the box below (f200–215), lashing crew stepping in. Camera then drops to quay level and pulls back past the documentation desk under a canopy at the quay office (clipboard, stamped sheaf of export papers — no readable text — and a laptop; two staff checking), and pushes onto the closed corrugated rear doors of a **second reefer on a truck chassis waiting to be lifted** until the doors fill the frame (f215–264).
- **Type zone:** sky above the cranes (f70–215), shade of the canopy (f215–250).
- **Copy:** countdown **09** · eyebrow "Step 9 · Export documentation & logistics" · headline **"Papers before ports."** · line "Our documentation staff prepare all necessary documents and track every shipment, in compliance with export certificates — HACCP, EU, FDA, etc." [W2, §5.9]
- **Boundary out (f264) = BRIDGE-DOOR:** corrugated reefer rear doors, locking bars and cam keepers, frame-filling, camera 1.2 m from the doors, lens 50 mm, soft daylight; linked collection `BRIDGE_DOOR` (door object + light rig) identical in plant-cold.blend f1 where the same doors are the cold-store dispatch dock.
- **Mobile:** object-position 55 % (crane + reefer); the landing beat holds 20 % longer (mobile scroll factor 0.9 for this chapter).
- **Alt:** "A crane lowers a white refrigerated container onto a ship at the Visakhapatnam port while staff check export documents."

## 08 · v-cold — "Held at −18 °C to −20 °C."  (plant-cold.blend 1–192, 8.0 s, 320 vh)
- **Set:** Anandapuram plant, cold store and dispatch dock: insulated doors with strip curtains, high-bay pallet racking (≥ 5 levels, ≥ 10 bays visible, frosted), pallets of cartons in stretch wrap, forklift (A-FORKLIFT) with operator in a thermal suit, cold-mist volumes at the door, frost on racking and floor edges.
- **Camera:** from BRIDGE-DOOR (f1) the reefer doors swing open (f1–30) and the camera dollies backward into the cold store past the strip curtain (f30–70), down the rack aisle as the forklift lowers the pallet with the hero carton (f70–150), and rises to a high view of the full store (f150–192).
- **Type zone:** left: the insulated wall panels.
- **Copy:** countdown **08** · eyebrow "Step 8 · Cold storage" · headline **"Held at −18 °C to −20 °C."** (nowrap span) · line "Cold rooms until dispatch. Our warehouse holds 700 pallets." [§5.8, F2]
- **Boundary out (f192):** same file (shared frame with v-pack).
- **Mobile:** object-position 40 % (aisle vanishing point).
- **Alt:** "Frosted pallet racks in a cold store; a forklift operator in a thermal suit moves a pallet of cartons."

## 07 · v-pack — "Packed and labelled."  (plant-cold.blend 192–383, 8.0 s, 320 vh)
- **Set:** packing hall next to the cold store: stainless tables, carton erector, inner poly bags, labelling station, strapping machine, pallets being built; 6–8 staff in full PPE (white coats, hairnets, masks, gloves, white boots).
- **Camera:** through a glazed door from the cold store (f192–230) into the packing hall, travelling backward along the line against the flow: a pallet being built → strapping → label applied (label shows only "SKYLARK EXIM · VISAKHAPATNAM · INDIA" and "VANNAMEI") → a worker folding the hero carton lid closed over glazed shrimp blocks (f300–383).
- **Type zone:** upper 30 % (white ceiling with ducting).
- **Copy:** **07** · "Step 7 · Packaging" · **"Packed and labelled."** · "Export-grade cartons, vacuum packs or custom packaging, labelled with product, size, batch and export compliance." [§5.7]
- **Boundary out (f383):** shared frame with v-freeze (same file).
- **Mobile:** object-position 50 %.
- **Alt:** "Workers in hairnets, masks and gloves pack frozen shrimp into Skylark Exim cartons."

## 06 · v-freeze — "Frozen, then glazed."  (plant-cold.blend 383–574, 8.0 s, 320 vh)
- **Set:** spiral/IQF freezer outfeed with stainless mesh belt, glazing spray curtain, frost on the housing, cold vapour; a worker checking a tray.
- **Camera:** follows the belt *upstream*: glazed IQF shrimp on the belt (f383–440), the glazing spray (fine particle droplets with motion blur, falling down) (f440–500), into the IQF tunnel mouth (f500–540), ending on a frame-filling top-down of the belt entering the freezer with raw graded shrimp in rows (f540–574).
- **Type zone:** left 40 % (freezer housing).
- **Copy:** **06** · "Step 6 · Freezing & glazing" · **"Frozen, then glazed."** · "Frozen by IQF or block freezing, then glazed with a thin layer of ice to keep it fresh in transit." [§5.6]
- **Boundary out (f574) = BRIDGE-BELT:** top-down on the stainless belt with rows of raw shrimp, lens 35 mm, 1.0 m above belt, belt UV offset 0; linked collection `BRIDGE_BELT` identical at plant-line.blend f1.
- **Mobile:** object-position 50 %.
- **Alt:** "Individually quick-frozen shrimp leave a freezer tunnel under a fine glazing spray."

## 05 · v-qc — "Tested before it moves."  (plant-line.blend 1–192, 8.0 s, 320 vh)
- **Set:** the lab unit beside the line: bench, analytical balance, sample trays, thermometer probe, glassware, sample bags, a window to the line; one technician in lab coat, hairnet, mask, gloves.
- **Camera:** from BRIDGE-BELT (f1) rises to a QC station on the line where a technician takes a sample tray (f1–70), follows the tray backwards through the lab door (f70–110), lab bench beat: probe in a shrimp, tray on the balance, sample looked at under the lamp; no microscopes, no readable numbers on screens (f110–192).
- **Type zone:** upper right (white lab wall).
- **Copy:** **05** · "Step 5 · Quality control & inspection" · **"Tested before it moves."** · "Checked for hygiene, freshness, texture and defects. Samples tested for international food-safety compliance." [§5.5]
- **Mobile:** object-position 45 %.
- **Alt:** "A lab technician checks shrimp samples at the quality-control bench."

## 04 · v-grade — "Sorted by size, weight and type."  (plant-line.blend 192–383, 8.0 s, 320 vh)
- **Set:** grading machine (roller grader with chutes), sorting table, crates of graded shrimp in ice, 5–6 staff in PPE.
- **Camera:** backward along the grader against the flow: chutes dropping sizes into crates, hands sorting on the table, an overhead reveal of the whole grading line.
- **Type zone:** upper 30 %.
- **Copy:** **04** · "Step 4 · Grading & sorting" · **"Sorted by size, weight and type."** · "Graded for uniformity to export standards." [§5.4]
- **Mobile:** object-position 50 %.
- **Alt:** "Shrimp roll through a grading machine into crates by size."

## 03 · v-peel — "Made to order."  (plant-line.blend 383–574, 8.0 s, 320 vh)
- **Set:** peeling & deveining hall: long stainless tables with ice, 10–14 workers each side in PPE, hands peeling, deveining tools, trays separating head-on / headless / peeled.
- **Camera:** slow backward tracking along the table at shoulder height, then rising to a high wide of the hall.
- **Type zone:** upper 28 % (ceiling, lights).
- **Copy:** **03** · "Step 3 · De-heading, peeling & deveining" · **"Made to order."** · "Head, shell and vein removed by hand or machine, to the product requirement: head-on, headless, peeled or value-added." [§5.3]
- **Mobile:** object-position 50 %.
- **Alt:** "Rows of workers in masks and gloves peel and devein shrimp on ice."

## 02 · v-wash — "Washed clean."  (plant-line.blend 574–765, 8.0 s, 320 vh)
- **Set:** receiving bay: crates of iced shrimp tipped into a stainless wash tank, flowing chlorinated-looking clear water (correct flow, splash stays in the tank, drains to floor gutters), receiving scale, ice flakes; dock door open to daylight with the reefer truck backed in.
- **Camera:** backward from the wash tank toward the receiving dock (f574–700); the dock door's daylight blooms to fill the frame (exposure-matched, not white-out) (f700–765).
- **Type zone:** left (tiled wall).
- **Copy:** **02** · "Step 2 · Receiving & washing" · **"Washed clean."** · "Washed thoroughly with clean, treated water to remove impurities." [§5.2]
- **Boundary out (f765) = BRIDGE-DOCK:** camera inside the dock looking out through the open truck doors to the yard, lens 28 mm, exposure −0.3; linked collection `BRIDGE_DOCK` identical at truck.blend f1.
- **Mobile:** object-position 50 %.
- **Alt:** "Shrimp are washed in a stainless tank at the receiving bay."

## 02 · v-truck — "Kept chilled on the road."  (truck.blend 1–216, 9.0 s, 360 vh)
- **Set:** Anandapuram plant yard and dock, morning; Indian reefer truck (A-TRUCK-REEFER, Tata/Ashok Leyland style cab) backed against the dock seal, wheel chock, signalling worker beside (not in the truck path), dock hand at the door; then the Anandapuram–Pendurthi road with hills, roadside trees, two-wheelers and an auto-rickshaw.
- **Camera:** from BRIDGE-DOCK (f1) the camera pulls back through the truck body (cut-away rear doors, cartons of crates on ice) (f1–60), out over the cab as it is shown arriving in reverse to the dock (forward action, already parked at f1 then the shot reveals yard life) (f60–120), rises and flies backward along the road over the truck route toward the coast (f120–200), climbing to a high coastal aerial: green land, ponds on one side, the sea on the other (f200–216).
- **Type zone:** sky (f120–216); yard wall (f1–120).
- **Copy:** **02** · "Step 2 · Receiving" · **"Kept chilled on the road."** · "Transported under chilled conditions to our processing plant at Anandapuram, Visakhapatnam." [§5.2, F3]
- **Boundary out (f216) = BRIDGE-COAST:** aerial 300 m, lens 24 mm, pitch −35°, sun at 15° elevation, east; linked collection `BRIDGE_COAST` (terrain tile + sun + sky) identical at pond.blend f1.
- **Mobile:** object-position 50 %.
- **Alt:** "A refrigerated truck at the plant dock in Anandapuram, then the road toward the coast."

## 01 · v-pond — "Raised with partner farmers."  (pond.blend 1–216, 9.0 s, 360 vh)
- **Set:** coastal aquaculture farm at sunrise: rectangular ponds with textured bunds (grass tufts, wet mud edges, footpaths, tyre ruts), working paddle-wheel aerators with foam trails that stay inside each pond, varied palms + neem/casuarina + shrubs, a farm shed, feed sacks, 3–5 farmers, a harvest crew lifting a net bag of shrimp into crates of ice, birds (egrets), soft mist low over water.
- **Camera:** from BRIDGE-COAST (f1) descends over the ponds (f1–90), low flight across the water toward the harvest (f90–160), ends at the bund on the farmers lifting the net bag (shrimp visible through the mesh, water draining down) and turning to look across the land toward the sea; the camera tilts up to the sea horizon at sunrise (f160–216).
- **Type zone:** sky (f1–90, f160–216); far bund line (f90–160).
- **Copy:** **01** · "Step 1 · Raw material procurement" · **"Raised with partner farmers."** · "Strategic partnerships with aquaculture farmers and a focus on responsible sourcing." [C2]
- **Boundary out (f216) = BRIDGE-HORIZON:** sea horizon at sunrise, horizon at 46 % frame height, lens 35 mm, sun 4° above horizon at azimuth 95°, sky + sea material linked collection `BRIDGE_HORIZON` identical at sea.blend f1.
- **Mobile:** object-position 55 %.
- **Alt:** "Farmers lift a net of shrimp from a pond at sunrise; aerators turn the water."

## 01 · v-sea — "Landed at dawn."  (sea.blend 1–264, 11.0 s, 440 vh)
- **Set:** dawn sea off the Vizag coast; a mechanised Indian fishing boat (A-VESSEL-FISHING-A, painted wooden hull, wheelhouse, mast with flags and nets) with 5–6 crew in work clothes (lungis/shorts, T-shirts, some oilskins, gloves) hauling and sorting catch onto deck into crates on ice — sea shrimp, mackerel, a few tuna (scans); 2–3 other boats in the distance; gulls; the coast and headland silhouette.
- **Camera:** from BRIDGE-HORIZON (f1) flies low over the sea toward the boat (f1–80), circles the stern as the net comes in, water draining correctly through the mesh (f80–160), deck beat: catch on crushed ice, gloved hands sorting (f160–210), then pulls back to a mid-distance portrait of the crew standing at the rail, backlit by the dawn sun, one waving to another boat (f210–264). The last frame is the final film image (it stays on screen as the poster for B1's intro).
- **Type zone:** sky (f1–160); sky above the crew (f210–264).
- **Copy:** **01** · "Step 1 · Raw material procurement" · **"Landed at dawn."** · "Sourced directly from farms or fishing vessels, and checked for size, freshness and health before acceptance." [§5.1] — at 85 %: closing line **"This is where it starts."**
- **Boundary out:** none (end of film; transitions to B1 by the page scrolling the pinned stage up).
- **Mobile:** object-position 50 % (boat), 60 % at the portrait.
- **Alt:** "A fishing crew hauls and sorts its catch on ice at dawn off the Visakhapatnam coast."

---

## B1 · Now, forward  (live R3F, 240 vh pinned)
- The film stage scrolls away upward; a frost-coloured section with the **live 3D hero carton** (A-HERO-CARTON GLB ≤ 500 KB, same model as in the renders) centred on a transparent canvas. As you scroll, the carton turns 1.5 revolutions and its lid opens to show glazed shrimp blocks (morph/rig animation exported in the GLB, driven by scroll).
- Behind it (DOM, under the transparent canvas, Zoi-style), the 9 steps scroll forwards as giant Fraunces lines: "01 Sourced" … "09 Shipped" (one at a time, each crossing the screen behind the carton).
- Copy: headline **"Now, forward."** · line C1 (shortened: first sentence) · small link "Read our full work flow" scrolls to B3.
- Mobile: carton at 70 % size, steps as stacked lines (no horizontal crossing), 180 vh.

## B2 · Products  (live R3F, 3 × 120 vh pinned + list)
- Zoi "big word behind product" layout: giant species name in Fraunces outline behind the transparent canvas, a live 3D model in front turning with scroll on an ice-slab plinth (A-PROD-PLINTH), soft studio HDRI.
  1. **Tuna** (A-PROD-TUNA, yellowfin scan, cleaned) · "Marine fish" · list of all 8 marine fish (§6) below.
  2. **Shrimps** (A-PROD-PRAWN, the tiger prawn scan in its own natural look; the giant word is "Shrimps", never a species name the scan doesn't match) · the 5 shrimps (§6) + the 6 forms table.
  3. **Swordfish** (A-PROD-SWORDFISH, Blender-modelled) · ONLY if it passes G-PROD at close range; otherwise omit the 3D stage for it and keep swordfish as a text entry.
- Each block: "Enquire about this" text button → B6 with category + species prefilled (query params, no state lost).
- States line: "Raw fresh · chilled · frozen" [C1].
- Mobile: model 80 vw, name above (not behind) the model, no orbit drag, scroll-driven rotation only.

## B3 · Quality & facility  (DOM, 140 vh)
- Two large framed stills from the film (v-qc end poster, v-cold poster) with slow parallax (transform only).
- Lines: W4 quality control staff · F1 processing facility · F2 700 pallets · F4 lab unit and processing unit at Anandapuram · §5.9 compliance ("HACCP, EU, FDA, etc.") · W1 prompt delivery · W3 best seafood, quickest time.
- "Our work flow" — the 9 steps as a compact two-column list (title + one line each), no icons.

## B4 · Markets  (still + SVG, 200 vh pinned)
- Blender-rendered relief map (markets-map still, A-MAP; equirectangular crop 20°W–150°E, 10°S–65°N; ink sea, glaze land, soft relief shading; no labels baked in).
- SVG overlay in the same projection: Visakhapatnam origin dot; 16 marigold routes (great-circle arcs) draw on with scroll (stroke-dashoffset), in the site's order.
- The 16 market names are a typographic list beside the map (desktop: right column; mobile: below the map, 2 columns), highlighting each as its route draws. No labels on the map (v3 globe labels overlapped).
- Headline **"We deliver worldwide."** [C7] · line "Our market places, as listed by Skylark Exim." + "16 markets" count.

## B5 · The people behind it  (DOM, 120 vh)
- "Managing partners" — **V. Yashod Kumar** · **N.V. Prudhvi** in Fraunces, no photos.
- Vision and mission (CONTENT.md §2, "Use" text), C3 line.
- Background: the v-sea crew portrait poster (last frame), dimmed only by a gradient behind the text block.

## B6 · Request a quote  (DOM)
- Form: name*, company*, country*, email*, phone, category (Marine fish / Shrimps), species (from §6 per category), form (§6 forms, shrimps only), state (raw fresh / chilled / frozen), quantity (free text), destination (free text), message (≤ 2,000 chars), honeypot. Submit composes a `mailto:info@skylarkexim.com` with subject "RFQ — <company> — <species>" and a plain-text body; shows "Your email app has opened with the request. If it didn't, write to info@skylarkexim.com." No fake success, no backend.
- Contact block: phones (tel:), email, office, processing unit address (F3), "Download company profile (PDF)".
- Mobile: sticky bottom "Request a quote" button appears after v-port and hides inside B6.

## Footer
Wordmark, C4 short line, nav (Story, Products, Quality, Markets, People, Contact), phones, email, office, © Skylark Exim, "Made in Blender. No AI imagery." (Tarun can delete this line), licences link (docs/LICENSES.md rendered at /licenses).

---

## Totals
Film: 13 clips, 2,712 rendered frames (113 s), 4,520 vh desktop / 3,616 vh mobile. Business: ~1,000 vh desktop. Media requested per full scroll (budget): desktop ≤ 32 MB, laptop ≤ 22 MB, mobile ≤ 14 MB (`scripts/path-weight.sh`).
