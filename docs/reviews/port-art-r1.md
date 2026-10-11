# port.blend art pass (issue #75, COLOR_SCRIPT row 02 v-port: dusk harbour), rounds

Code: assets-src/blender/build/port_art.py (exec'd at the end of port.py after sklib.finish; rebuild verified 61 s).
Stills: assets-src/blender/stills/port/{a1..a9,b1,b2,after}_f###.png. Before/after: docs/renders/port-before-after.jpg
(rows f1, f27, f132, f204, f238, f264; left = before render/before/port, right = after, full res 32 spp).

| Round | Change | Result |
|---|---|---|
| a1-a2 | dusk sun 8/260 #ff8c4a, sky tint, fill/rim, sodium, world fog 0.0006 / 0.00015 | black frames (luma 9-19): world volume absorbs sky + sun -> fog removed (lead note too) |
| a3-a7 | no fog, exposure, sky-tint variants | quay neon magenta: NOT lighting. Test copy lived in /tmp, relative texture paths broke -> missing-texture magenta. Moved the test base into assets-src/blender/ |
| a8-a9 | world, sea and grade copied from reefer.py (lead): sky_world(8,260) x 0.6 EASE ramp #e8825a -> #1b2a4a, sea deep/shallow, #ff8c4a glints, haze #c98a7a, exposure +0.9, lift #3a5b8c .012, gain #ff9a5c .015 | believable dusk; f1 SSIM vs reefer 0192 0.95 |
| b1-b2 | key 6.0, violet fill #4b4a8c 4.0 (no shadow), rim #ffb06b 2.5 | violet shadows vs warm rims; all luma ok |

Four questions (after): empty? no. Toy-like? no more than before; dusk light hides the flat quay better than midday. Fake? sun glare on the sea at f204 and sodium pools read real. Clipping? none new.
Rich colour, not grey: cranes and boxes carry warm rims on the sun side and violet-blue shadows, the sea is deep dusk blue with warm glints, and the hills are brown-violet in haze.
