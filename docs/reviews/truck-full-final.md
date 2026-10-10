# truck.blend — full render, final review

Full render: assets-src/render/truck/0001–0216.png, 216/216 frames at 1920x1080. EEVEE, AgX Medium High Contrast, 24 fps, motion blur, 32 samples. The render took 23 min wall time: 6.3 s per frame on average, 14.5 s at most (dock/cargo frames), on a GPU shared with other renders. Contact sheet: docs/renders/truck-full-sheet.jpg.

**First impression.** One continuous move. It pulls back out of the reefer box (crates of prawns on ice) and rises over a rounded Indian cab-over. The yard is busy and worn: 3 reefers, 9 people, crate stacks, blue fish iceboxes, a hose to the drain, wet patches, dust, weeds and saw-cut joints. The camera then climbs over plotted farmland, coconut groves and aquaculture pond blocks to the coast. At f216 the sea fills the upper right with surf lines, a beach, a casuarina belt and boats. It no longer reads as a city-builder game.

Four questions (full frames 1, 22, 40, 58, 108, 130, 194, 205, 216 and the sheet)
- Empty? No.
- Toy-like? No primitive vehicle sits in frame centre: the forklift was removed and the parked two-wheelers are mid-distance. The broadleaf crowns are still somewhat stylised from ~150 m (f130, top left), but nothing close to the camera.
- Fake? Water stays in the sea and the ponds. The sea sheen is broken glitter on swell, not a pillar.
- Clipping? None seen. Pond blocks are kept off the yard and the road, and no trees stand under the low climb.

| Gate | Final | Frames |
|---|---|---|
| G-SCENE-1 Realism | PASS | PBR + grime: cab, box (panel joints, tape, streaks), yard (worn concrete, joints, dust, grime, oil, wet), land/sea/beach shaders |
| G-SCENE-2 Not toy-like | PASS | lofted cab-over with bevels, tread tyres (f90–f108); forklift removed |
| G-SCENE-3 Busy | PASS | f90–f130 yard; f150–f216 farmland, groves, ponds, road traffic, villages, boats |
| G-SCENE-4 No clipping | PASS | f1–f216 sheet + stills |
| G-SCENE-5 Water | PASS | f194–f216 |
| G-SCENE-6 People | PASS | 9 MPFB people, no identical pair, mid-distance |
| G-SCENE-7 Fish | PASS | prawn scans on ice, f1–f40 |
| G-SCENE-8 Light | PASS | luma below |
| G-SCENE-9 Setting | PASS | Indian cab-over, blank yellow plate, LHT, coastal Andhra land use |
| G-SCENE-10 Camera | PASS | steady turn to the east from f120; shutter 0.3, 0.15 on the climb (f172+) |
| G-SCENE-11 Continuity | to equalise | f1 BRIDGE_DOCK unchanged; f216 BRIDGE_COAST to spec (300 m, 24 mm, pitch −35°, heading east, sun 15°/90°), but the coast moved 250 m closer, so pond.blend f1 must be re-equalised to the new f216 |
| G-SCENE-12 Story | PASS | |

Luma (single chapter 1–216): f22 (10 %) mean 113 sd 44 ok · f108 (50 %) mean 137 sd 38 ok · f194 (90 %) mean 118 sd 29 ok · f1 110/53 ok · f216 143/45 ok.
