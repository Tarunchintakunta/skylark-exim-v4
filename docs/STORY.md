# STORY.md — Skylark Exim v4: "Trace it back"

## 1. Logline
A carton of Skylark shrimp on a dinner table abroad. Scroll, and the camera travels *upstream* through everything that carton passed through — the reefer at sea, the port at Visakhapatnam, the −18 °C cold room, packing, freezing, the quality lab, grading, peeling, washing, the chilled truck — until it reaches the source: a partner farm pond at sunrise and a fishing boat landing its catch at dawn, and the people who work them. Then the page turns round — "Now, forward." — into the business: products, quality, markets, the partners, and a request for a quote.

## 2. Why this story (for the buyer)
Seafood buyers judge an exporter by control of the chain. Telling the chain backwards from *their* table puts the buyer first and makes every step a proof point, ending at the source with full trust, exactly when the RFQ form appears. Every caption is one of Skylark's own 9 work-flow steps (CONTENT.md §5), so the story needs no invented facts.

## 3. Structure (13 film chapters + 6 business sections, one continuous scroll)
| # | Chapter | Countdown | Where | Scene id(s) |
|---|---|---|---|---|
| 0 | The table | — (title: "Trace it back.") | A buyer's dining table abroad, evening | v-table |
| 1 | Under a cold seal | 09 | Reefer container on a ship at sea | v-reefer |
| 2 | Papers before ports | 09 | Port of Visakhapatnam: cranes, ship, documents | v-port |
| 3 | Held at −18 °C to −20 °C | 08 | Cold store at Anandapuram | v-cold |
| 4 | Packed and labelled | 07 | Packing hall | v-pack |
| 5 | Frozen, then glazed | 06 | IQF tunnel + glazing | v-freeze |
| 6 | Tested before it moves | 05 | Lab unit | v-qc |
| 7 | Sorted by size, weight and type | 04 | Grading line | v-grade |
| 8 | Made to order | 03 | Peeling & deveining hall | v-peel |
| 9 | Washed clean | 02 | Receiving & washing | v-wash |
| 10 | Kept chilled on the road | 02 | Reefer truck at the plant dock, Anandapuram–Pendurthi road | v-truck |
| 11 | Raised with partner farmers | 01 | Aquaculture pond at sunrise | v-pond |
| 12 | Landed at dawn | 01 | Fishing boat at sea, Vizag coast at dawn; crew portrait | v-sea |
| B1 | Now, forward | 01 → 09 | Live 3D carton + the 9 steps read forwards | live R3F |
| B2 | Products | — | Live 3D tuna / prawn / swordfish over giant species names | live R3F |
| B3 | Quality & facility | — | Stills from v-qc / v-cold renders, 700 pallets, compliance | DOM + posters |
| B4 | Markets | — | Blender-rendered relief map, routes drawn by scroll, 16 markets | still + SVG |
| B5 | The people behind it | — | Managing partners, vision, mission | DOM |
| B6 | Request a quote | — | RFQ form (mailto), phones, office, plant, profile PDF | DOM |
Footer.

## 4. Storytelling devices (all mandatory)
1. **One continuous flight.** All 13 film chapters are chained with shared boundary frames (SSIM ≥ 0.99). No crossfades, no cuts, no fades to black inside the film. The camera always moves upstream (generally backwards/away from where the carton is going).
2. **Match-surface bridges.** Each cross-set join hides inside a surface that fills the frame and exists in both sets: frost on the carton (table → reefer), sea surface top-down (reefer → port), corrugated reefer door (port → cold store), IQF belt (freeze → lab line), dock-door daylight (wash → truck), coastal aerial (truck → pond), sea horizon at sunrise (pond → sea). Details per join in STORYBOARD.md.
3. **The hero carton.** One Skylark master carton (asset A-HERO-CARTON) appears in every chapter until it is "unmade": on the table (opened), in the reefer stack, on the crane's container, on a pallet in the cold room, being sealed in packing; from freezing upstream, the hero becomes *the shrimp themselves* (the glazed block, the graded tray, the peeled shrimp, the crate on ice, the harvest net). The live-3D B1 section uses the same carton as a GLB.
4. **The countdown numeral.** A huge Fraunces numeral (09 … 01), outlined, sits in each shot's planned "type zone" and changes with a soft vertical roll on chapter change. It is typography, not a HUD: no box, no pill, no progress rail.
5. **Actions play forwards.** Water falls down, nets rise, cartons get sealed. Only the order of chapters is reversed. Never reverse a simulation.
6. **Light tells time backwards.** Evening (table) → bright day (sea, port) → clean white interiors (plant) → morning (truck) → sunrise (pond) → dawn (sea). Never dark, never a colour overlay; dawn scenes still pass the brightness floor (check-clip.sh).
7. **People everywhere it's real.** Diners' hands at the table, port crew, forklift driver in thermal suit, packing/peeling/grading staff in full PPE, lab technician, truck driver and dock hand, farmers, fishing crew. Varied faces, ages, body types, real clothing with folds, natural weight-bearing poses. The final chapter ends on the people at mid-distance, backlit by dawn.

## 5. Tone and copy voice
Calm, confident, factual. Short headlines (≤ 6 words), one supporting line (≤ 22 words) taken from CONTENT.md. British spelling as on the site ("specialising", "recognised"). No exclamation marks, no superlatives beyond the site's own words ("trusted", "premium", "top-notch").

## 6. Visual language (distinct from v3 and from skylarkexim.com)
**Palette "Ice & Marigold"** (v3 was sand / deep sea / rust):
| Token | Hex | Use |
|---|---|---|
| `--ink` | `#0E1417` | page background in the film, body text on light |
| `--frost` | `#EEF3F2` | headline/text on film, light section background |
| `--glaze` | `#BFD3D6` | secondary text, hairlines, map land |
| `--steel` | `#5E6E73` | captions on light, borders |
| `--marigold` | `#E2A03A` | the ONE accent: CTA, countdown outline on hover, route lines (Indian marigold, warm dawn) |
| `--lagoon` | `#2F6E68` | pond/farm accents, focus ring on light |
Contrast (computed): frost on ink 16.6:1; glaze on ink 11.9:1; ink on marigold 8.2:1; lagoon on frost 5.3:1; steel on frost 4.7:1 (all ≥ WCAG AA 4.5:1; verify with axe).
Render grading matches the palette: cool whites and steel in the plant, warm marigold sun at dawn/sunrise, neutral daylight at the port. No teal-orange cliché grade, no blue wash.

**Typography** (v3 was Instrument Serif + Inter Tight):
- Display: **Fraunces** (variable; axes opsz, wght, SOFT, WONK) — SIL Open Font License 1.1 (Undercase Type). Headlines at opsz 144, wght 300–420, SOFT 50; the countdown numerals in outline (CSS `-webkit-text-stroke`, fill transparent) at wght 300.
- Text: **Hanken Grotesk** (variable wght 100–900) — SIL Open Font License 1.1 (Hanken Design Co.). Body 400, eyebrows 600 uppercase tracking 0.14em, tabular numerals for phone numbers.
- No monospace anywhere (it read as "dashboard" in v3).
- Self-hosted WOFF2, Latin subset (+ U+2212 minus, U+00B0 degree, U+2009 thin space, U+00A0), `font-display: swap`, preload only Fraunces (display axis subset) and Hanken Grotesk 400. Commit both OFL.txt files to `public/fonts/` and list them in docs/LICENSES.md. Verify the licence file from github.com/google/fonts (`ofl/fraunces`, `ofl/hankengrotesk`) before committing.
- Type scale (desktop / mobile): display 9.5vw max 168 px / 15vw; countdown 34vw / 48vw outline; h2 64 / 40; body 19 / 17; eyebrow 13 / 12. One headline on screen at a time, max 2 lines, never overlaps the subject's face or the hero object (type zones in STORYBOARD.md).

**Layout:** pinned full-bleed stage; type sits in the shot's type zone; minimal header (wordmark left, "Request a quote" right, menu button) that fades to 0 opacity while scrolling the film and returns on scroll-up or pointer near the top. No side rails, no chips, no pills, no HUD, no "chapter x/y", no placeholder tags, ever.

## 7. What is NOT in v4
No start screen, no path choice, no globe, no data chips, no monospace, no stock photos, no AI images or video, no frame-image sequences, no sound by default (an optional ambient sound toggle is out of scope tonight).
