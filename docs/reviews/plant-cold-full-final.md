# plant-cold full final (574/574 frames, 1920x1080 EEVEE 32 spp, AgX Medium High Contrast, motion blur)
Frames: assets-src/render/plant-cold/0001-0574.png. Sheet: docs/renders/plant-cold-full-sheet.jpg. Reviews: plant-cold-full-r1.md, -r2.md.
First impression: a real working cold store / packing hall / IQF outfeed, no washed-out or blank frames.

Post-render fixes (round 3, affected ranges re-rendered): packing hall/IQF were hidden until f175 and popped in behind the door glass -> visible from f2 (2-176 re-rendered); motion-blur shutter hard switch at f506 popped -> linear ramp 0.5 -> 0 over f488-528 (489-574 re-rendered). Checked 174/176 and 505/506: no pop.

Luma (mean/sd), chapter 10/50/90 %:
- v-cold  f20 189/15, f96 135/48, f173 135/34 (f1 202/21)
- v-pack  f211 163/23, f288 163/33, f364 168/56 (f192 143/33, f383 174/53)
- v-freeze f402 152/53, f479 150/43, f555 130/43 (f574 169/20)
All ok.

| Gate | Result | Frames / notes |
|---|---|---|
| G-SCENE-1 Realism | PASS | IQF housing frost slightly blotchy (f500-545 top) |
| G-SCENE-2 Not toy-like | PASS (watch) | reach truck boxy, bevelled |
| G-SCENE-3 Busy | PASS | 442 pallets, 10 staff + operator |
| G-SCENE-4 Clipping | PASS | camera clears spray bar >= 0.5 m (f496-574 checked) |
| G-SCENE-5 Water | PASS | spray droplets blurred through f488, sharper after (small) |
| G-SCENE-6 People | PASS | no close frontal faces; f235 carrier from behind |
| G-SCENE-7 Shrimp | PASS | CC0 scans |
| G-SCENE-8 Light | PASS | no overlay; exposure eases 0 -> -1.9 over f520-574 |
| G-SCENE-9 Setting | PASS | |
| G-SCENE-10 Camera | PASS | f150-230 re-planned to frame the door + hall |
| G-SCENE-11 Continuity | PASS f1 / ACTION f574 | BRIDGE_BELT moved to x=-47.4, exposure -1.9 -> lead re-equalises plant-line f1 |
| G-SCENE-12 Story | PASS | |
Known issues: IQF housing frost blotchy at close range; top-down shrimp scans are pale and partly read through the belt mesh; droplets f510-528 nearly unblurred.
