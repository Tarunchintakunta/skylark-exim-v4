# plant-cold art pass final (574/574 frames, 1920x1080 EEVEE 32 spp, AgX Medium High Contrast, motion blur)
Frames: assets-src/render/plant-cold/0001-0574.png. Sheet: docs/renders/plant-cold-art-sheet.jpg.
Before|after: docs/renders/plant-cold-before-after.jpg. Rows top to bottom: f1, f96, f192, f288, f383, f479, f574 (left is before, right is after).
Reviews: plant-cold-art-r1..r4.md. Render: 38 min wall, avg 3.5 s/frame, max 11 s (budget 15); f1-110 re-render 10 min, avg 5.3 s, max 9 s.

## What changed (build/plant-cold.py, rebuild reproduces it)
- Lights: cold key #cfe0ff (7500 K) high-bay areas; violet bounce fill #6b5fb5 from the dock side; cyan #9fe3ff rims from the far wall (3 high + 1 floor).
  Pack: key #f2f6ff, fill #8fb4e8, warm #ffcf8a doorway rim from the far right corner. IQF: key #d6ecff (8000 K), fill #4f6fa8, #a8f0ff spray backlight.
  Belt: key #d6ecff + #a8f0ff grazing rim. LED fixtures 7000 K.
- World: f1 dusk (BRIDGE_DOOR, matched to port/0264 after the lead review): #4b4a8c mixed 45 % into a neutral #b4adb8 sky, strength 1.3;
  sun #ff9a5c energy 5, elev 8 deg, az 168 (camera-left, grazing), disc 12 deg (soft shadows like port's area light); sun off by f110. f1-110 re-rendered.
  Interior world keyed #0f1630 (cold), #1a2433 (pack, f215), #0d1a26 (freeze, f430), strength 3.
- Fog (closed interiors only, per lead note; look.apply no longer adds it): world volume keyed. Density 0 at f1-39 (exterior), 0.0025 #b9c8ff cold,
  0.0015 #dfe9f5 pack, 0.004 #cfefff IQF, 0.0015 at f560. Volumetric tile 8, 16 samples, end 40 m. Door/IQF mist volumes tinted #b9c8ff / #cfefff.
- Materials: PUF walls cool blue-white (0.56,0.62,0.72) + existing grime/streaks; cold floor (0.26,0.30,0.40), pack epoxy steel-blue (0.17,0.27,0.40);
  marigold safety tape lines in the packing hall (y -0.9 / 3.0).
- Grade: look.apply(S,'plant-cold'), then look.grade(lift #1e2a4f amt 0.008, gain #cfe0ff amt 0.012, sat 1.15, bloom 0.15, vignette 0.10).
  The preset amounts (0.025/0.03) gave a full-frame blue cast (A/B in r2). Exposure 0 through f520, then easing to -2.3 at f574 (unchanged mechanism).
  One grade for the blend, so f192/f383 are identical by construction.

## Luma (mean/sd), chapter 10/50/90 % + bounds
- v-cold  f20 99/49, f96 118/49, f173 129/44 (f1 135/19; port 0264 is 137/19)
- v-pack  f211 143/30, f288 172/41, f364 169/65 (f192 156/34, f383 176/61)
- v-freeze f402 186/53, f479 153/46, f555 172/68 (f574 176/18)
All ok.

| Gate | Result | Notes |
|---|---|---|
| G-SCENE-1 Realism | PASS | IQF housing frost still blotchy close up (f500-545) |
| G-SCENE-2 Not toy-like | PASS (watch) | reach truck boxy |
| G-SCENE-3 Busy | PASS | unchanged |
| G-SCENE-4 Clipping | PASS | camera unchanged |
| G-SCENE-5 Water | PASS | spray backlit cyan |
| G-SCENE-6 People | PASS | |
| G-SCENE-7 Shrimp | PASS | CC0 scans |
| G-SCENE-8 Light/no overlay | PASS | cast comes from lights/world; grade tint 0.008/0.012; vignette 0.10 |
| G-SCENE-9 Setting | PASS | |
| G-SCENE-10 Camera | PASS | unchanged |
| G-SCENE-11 Continuity | PASS | f1 vs port/0264 SSIM 0.942, luma 135 vs 137; f110->111 join: luma 112/112, frame SSIM steady ~0.67 (motion), no pop; f574 BRIDGE_BELT (plant-line must match the new f574) |
| G-SCENE-12 Story | PASS | |
| Art: rich colour, not grey | PASS | blue-violet store with kraft/marigold, cool-white hall with warm rim, steel-teal IQF |

Known issues: f1 bars are a touch darker on their shaded side than port's (SSIM 0.942); the lead equalises the exact shared frame.
Packing-hall highlights near the doorway rim bloom hot (f300-340 table edges). f574 sd 18 (ok, under the aim of 20): belt top-down stays pale steel-white.
