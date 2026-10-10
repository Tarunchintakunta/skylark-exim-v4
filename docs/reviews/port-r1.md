# port.blend — review r1 (stills r1_f001…f264, 960×540, 64 spp)

First impression: layout reads as a port (ship, 3 cranes, yard, breakwater, headland), but it is not a "wow" shot yet.
Lighting is flat because the camera looks along the sun for most of the move; cranes read as pale toy blue; far hills black.

| Gate | Result | Notes |
|---|---|---|
| G-SCENE-1 realism | FAIL | material indices were dropped by `materials.clear()` (trees all bark, hull/deck one material); crane paint too light/clean |
| G-SCENE-2 not toy | FAIL | blunt elliptic bow (f70), boxy tug superstructure filling f70 foreground, tractors primitive |
| G-SCENE-3 density | PASS | 3 STS, 165 ship + 1317 yard containers, 6 vehicles; people not built in r1 |
| G-SCENE-4 clipping | PASS (visual) | landed reefer sits on castings; no hull/quay overlap seen |
| G-SCENE-5 water | FAIL f1 | f1 swirl = Track-To camera spinning at the straight-down key under motion blur |
| G-SCENE-6 people | n/a | r1 built with `nopeople` |
| G-SCENE-8 light | FAIL | flat front light; far hills render black; no aerial perspective |
| G-SCENE-10 camera | FAIL | landing (f205) hidden behind the 3-tier stacks of bay −26.4; crane 3/4 angle missing |
| G-SCENE-12 story | FAIL | landing not readable |
| perf | FAIL | 25–47 s per 960×540 still; env + yard instances cost ~23 s |

Fixes for r2: Euler camera keys (exact rotation 0,0,0 at f1); crane beat from the NE corridor between cranes 2 and 3 (sun 80° to the side,
camera flies through crane 2's portal); desk + truck moved into that corridor; tugs to the sea side; parabolic bow; darker rustier
crane paint; restore material indices; distance haze on terrain; merge tetrapods/trees/far-yard LOD into single meshes.
