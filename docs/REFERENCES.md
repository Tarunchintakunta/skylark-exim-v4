# REFERENCES.md — Tarun's 6 reference sites, what v4 borrows and where

Source: audit of all six sites on 9 Oct 2026 (headless Chromium + CDP network capture + bundle inspection; numbers are transferred bytes; FPS on that GPU-less box is not meaningful, long tasks and bytes are). Sheets in `reference/*-desktop-sheet.jpg` (Blackbird's screenshots were covered by its newsletter modal, so no sheet). `reference/v3-tarun-feedback-screens.jpg` = the v3 screens Tarun annotated.

**Primary style reference: drinkzoi.co.** v4 = one continuous scroll-driven 3D journey, camera flying between scenes, pinned typography, no dashboard UI — Zoi's look, delivered at a fraction of Zoi's weight.

## 1. drinkzoi.co (Zoi) — PRIMARY
- **What it is:** WordPress + Three r175 + GSAP ScrollTrigger + SplitText + Lenis (duration 1.2). A tea can in an ice block floats over giant one-line type ("Make drink. …", "South Africa"); scroll turns the can and flies the camera; a frosted wall of product cards; deep-blue blurred backdrop.
- **Borrow:** (a) one continuous camera journey with no hard cuts → v4 film chapters chained by shared frames + match-surface bridges (all chapters 00–01); (b) giant single-line display type with the 3D object in FRONT of the text (DOM text under a transparent canvas) → B1 Now forward (carton over the 9 steps) and B2 Products (fish over species names); (c) icy/glassy material language → frost bridge (00→09), IQF/glaze (06), ice plinth (B2); (d) slow, weighty easing (Lenis lerp 0.09, scrub 0.6) → whole site; (e) SplitText line reveals → every caption; (f) minimal header with almost no chrome → header.
- **Don't copy:** 48 MB preloaded, 5 × 4.9 MB uncompressed GLBs (we measured 303 KB after meshopt+WebP), a 192-frame 1080p WebP sequence (17.9 MB), 30 long tasks, LCP 5.7 s. v4: GLB ≤ 500 KB, no image sequences, nothing loaded before first scroll except the poster.

## 2. mont-fort.com (Mont-Fort)
- **What it is:** Astro + Three + Lenis + GSAP ScrollTrigger/SplitText; chaptered story, mountains in cloud, an aerial ship over grey sea, a light airy palette, staged loading (hero first, heavy assets later), KTX2 textures, view transitions.
- **Borrow:** (a) the aerial top-down ship over the sea → v-reefer end + BRIDGE-SEA (09) and the port approach (09); (b) calm, airy type with lots of space → B3/B5; (c) **staged loading** (hero first, later chapters streamed) → TRD §6 prev/current/next pool; (d) baked lighting on simple geometry for heavy things → the markets relief map is a baked Blender still (B4) instead of live 3D.
- **Don't copy:** the 6.9 MB earth texture and 913 ms transcode long tasks.

## 3. blackbirdrd.com (Blackbird) — the engineering model
- **What it is:** Next.js + vanilla Three + Lenis + ScrollTrigger; 3 product GLBs with meshopt + quantization, no textures, 47–261 KB; one 960×540 background video at 311 kbps with a 17 KB poster; 2.4 MB after a full scroll; 0 long tasks.
- **Borrow:** (a) tiny meshopt GLBs, dpr cap, antialias off → B1/B2 canvas (TRD §7); (b) poster-first video with small mobile tier → every clip has first/last WebP posters and a 960 tier (all chapters); (c) nothing heavy before first paint → loader/first scroll rule; (d) IntersectionObserver to render only what's on screen → canvas mount/unmount around B1–B2.

## 4. mokn.io (Mokn)
- **What it is:** Webflow + GSAP (ScrollTrigger, SplitText, MotionPath) with NATIVE scroll; bold centred lines; short silent MP4s instead of heavy animation; its scrubbed WebP sequence is switched off under 768 px.
- **Borrow:** (a) native scroll on touch devices → mobile (Lenis smoothing off); (b) mobile gets lighter media, never a broken frame → 960 tier + per-chapter object-position (all chapters, mobile); (c) one bold line at a time → one-headline gate G-SITE-2; (d) `preload` discipline for off-screen video → pool unloads clips 2+ away.
- **Don't copy:** the 4.9 MB intro video; image sequences.

## 5. pfenergy.eu (PF Energy)
- **What it is:** WordPress/Bricks + one Spline scene on one full-screen WebGL canvas: the product tin opens, pouches fly out, scenes morph — all one scene whose timeline is scrubbed by scroll; DrawSVG line drawing.
- **Borrow:** (a) **one persistent scene whose state is scrubbed** → the film is conceptually one world (shared bridges) and B1's carton lid opening is a single scrubbed GLB animation; (b) the "open the pack, reveal the product" payoff → B1 carton opens to glazed shrimp blocks; (c) line drawing on scroll → B4 market routes (stroke-dashoffset).
- **Don't copy:** 10.8 s LCP, CLS 0.19, ~91 JS files, plugins.

## 6. facilpay.io (FacilPay)
- **What it is:** Webflow + Three particle globe + Rive + Lottie; glowing product on deep navy; clean centred hero.
- **Borrow:** (a) clean, centred, confident hero composition → v-table opening type layout; (b) small vector micro-animations → the countdown numeral roll and the "Scroll" hint line (CSS/GSAP only, no Rive/Lottie runtime needed).
- **Don't copy:** 15.9 MB of PNGs, duplicate GSAP versions, CLS 1.96, 1.7 s long task, a globe (v3 had one; v4 uses the map).

## Borrowing map by chapter
| v4 chapter | Borrowed from |
|---|---|
| Loader / first paint | Blackbird (poster-first, nothing heavy), Mont-Fort (staged) |
| 00 v-table | Zoi (giant type, slow easing), FacilPay (centred hero) |
| 09 v-reefer, v-port | Mont-Fort (aerial ship), Zoi (continuous flight) |
| 08–02 plant chapters | Zoi (continuous camera, frost/ice material), Mokn (one bold line) |
| 02 v-truck, 01 v-pond, v-sea | Zoi (camera flight), Mont-Fort (aerial calm) |
| B1 Now forward | Zoi (object over giant type), PF Energy (scrubbed pack opening) |
| B2 Products | Zoi (product over giant word), Blackbird (tiny meshopt GLBs) |
| B3 Quality, B5 People | Mont-Fort (airy type, space) |
| B4 Markets | PF Energy (line drawing), Mont-Fort (baked art on simple geometry) |
| Mobile everywhere | Mokn (native scroll, lighter media), Blackbird (960 video, posters) |
| Engine | Blackbird + Mokn (0 long tasks), Mont-Fort (staged loading); avoid Zoi/FacilPay weight |
