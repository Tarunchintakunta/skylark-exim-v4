# port.blend — review r2–r4 (stills r2/r3/r4, full4_f205 1920×1080, preview docs/renders/port-preview.mp4 + port-sheet.jpg)

First impression (r4 preview): reads as a busy Visakhapatnam terminal; the crane landing (f185–215) is clear and is the strongest beat.
Weak: far hills/headland still read as pale grey layered cards; the f20–70 aerial is clean/grey; the tugs' white superstructures are boxy.

| Gate | Result | Notes (frames) |
|---|---|---|
| G-SCENE-1 realism | PASS (near) / FAIL (far) | PBR + wear on every hard surface; far hills = hazed scrub texture but still flat-looking (f40–150) |
| G-SCENE-2 not toy | PARTIAL | tug superstructures and truck cab boxy (f20, f67, f250); containers, crane, ship OK |
| G-SCENE-3 density | PASS | 3 STS; 165 ship + 2558 yard containers (183 full-mesh near, rest merged LOD); 8 moving vehicles (4 TT, reach stacker, 2 straddle carriers, pilot boat) + parked chassis; 12 people |
| G-SCENE-4 clipping | PASS (visual) | reefer lands on the tier-2 castings at f204 (base z exact), spreader/ropes driven; no hull/quay overlap |
| G-SCENE-5 water | PASS | one Ocean (seed 41, origin under f1 camera), far plane with a hole (no flat plane through troughs), no ship shadow on water |
| G-SCENE-6 people | PASS | MPFB, hi-vis/helmets on quay + lashing bridge, 2 staff in formal shirts + lanyards at the canopy desk; faces ≥ 4 m |
| G-SCENE-8 light | PASS (except f1) | sun az 135, 52°→40°; f1 BRIDGE_SEA luma ~50 (dark sea by spec), rest 148–201 |
| G-SCENE-9 setting | PASS | no text/logos; papers have unreadable line texture |
| G-SCENE-10 camera | PASS | Euler-keyed Bezier; f1 rotation (0,0,0) 60 m 35 mm; f264 = BRIDGE_DOOR (doors at 1.2 m, 50 mm, looking −X, sun behind-left) |
| G-SCENE-12 story | PASS | white reefer lowered and landed on a ship by an STS crane, documentation desk, reefer truck |
| perf | PASS (borderline) | full 1920×1080 64 spp f205: 13.7 s / 16.2 s with 2 other renders in parallel; preview 14 min |
