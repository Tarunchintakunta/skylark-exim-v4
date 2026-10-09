# BANNED_CLAIMS.md

`tests/content.spec.ts` must load the built site in Playwright, collect all **user-visible text** (`document.body.innerText` after scrolling the whole page, plus every `alt`, `aria-label`, `title`, `<meta>` content and the JSON-LD), and fail if any phrase in the **Banned strings** list matches as a whole word/phrase (case-insensitive, regex `\b<phrase>\b`; don't grep JS bundles: library code contains words like "buttons" and "ASC"). Claude reviews every caption against CONTENT.md before each PR.

## Banned strings (exact, case-insensitive)
Bay of Bengal · purse seine · purse-seine · longline · long-line · trawl net · gillnet · pomfret · snapper · salmon · lobster · crab · oyster · sashimi grade · sushi grade · Rotterdam · Dubai · Tokyo · New York · North America · USA · United States · EIC · MPEDA · BAP · BRC · ASC · MSC · ISO 22000 · ISO 9001 · award-winning · award winning · #1 · number one · largest · biggest · since 19 · since 20 · founded · established in · years of experience · tonnes · tons · metric ton · MT/day · per day · capacity of (except the exact "700 pallets" sentence) · hectares · acres · farms across · vessels in our fleet · our fleet · our boats · our trawlers · −1 °C · -1°C · 40 ft · 40ft · 20 ft · blast freez · residue · antibiotic-free · chemical-free · nitrofuran · chloramphenicol · tetracycline · every batch tested · 100% · zero defects · organic · wild-caught (unless Tarun confirms) · Incoterm · FOB · CIF · count/lb · 16/20 · 21/25 · 26/30 · 31/40 · 41/50 · lorem · placeholder · TODO · coming soon · awaiting

## Banned kinds of claim (review by reading, not grep)
1. Any number not in CONTENT.md. The only numbers allowed: 700 (pallets), −18 °C to −20 °C, the 9 step numbers, 16 (markets count), phone numbers, PIN 530052, S.No. 297/Part.
2. Any certificate other than "HACCP, EU, FDA, etc." quoted as the site quotes it ("compliance with export certificates"). No badges or seals as images.
3. Any named customer, partner farm, vessel, port terminal, shipping line, country of a specific buyer, or person other than the two managing partners.
4. Any fishing method, fishing ground or sea name. Visakhapatnam / Vizag / Andhra Pradesh / Anandapuram / Sheela Nagar / Lodagalavanipalem / Pendurthi are the only place names besides the 16 markets.
5. Any species not in CONTENT.md §6 shown as a product (labelled, carded or captioned). The greasyback-shrimp scan is crate filler only and never labelled.
6. Any statement that the plant processes fish (the work-flow page is about shrimp).
7. Sustainability/ethics claims beyond the exact words of C1, C2 and the mission/vision.
8. Fake readable text in renders: no made-up labels, batch codes, certificates, number plates with real-looking numbers, signage words. Allowed readable text in renders: "SKYLARK EXIM", "VISAKHAPATNAM · INDIA", a species name from §6, "−18 °C". Number plates: blank or blurred to unreadable.
9. AI-generated media of any kind, and any stock photo/video. Fonts and code-generated graphics are fine. CC0 scans from ASSETS.md are fine.
