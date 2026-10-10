# table — art round 6 (lead: f1/f31/f95 read red-magenta; f1 is the OG image)
Root cause: warm light hexes went through look.hex_rgb (linearised), so #ffb46b became (1, 0.46, 0.15), a deep orange-red
light. On red-brown walnut, with the cool #5b7da6 lift raising blue above green, the table went magenta (wood crop R/G 2.6, B > G).
Fix (build script only, f160+ lights untouched apart from the shared key/pendant):
- amber(h): warm light colour = geometric mean of the linear and the seen hex (#ffb46b -> (1, 0.57, 0.25)); key 190 W,
  pendant 145 W, rims #ffc27a 20 W (was #ff8a3d), candle #ffb46b 2.7 W (was #ff8a3d).
- Walnut albedo tint (0.16, 0.075, 0.04) -> (0.14, 0.10, 0.042): warm brown, lower red saturation.
- Napkins cream #efe6d6.
- Haze 0.008 and window fill #5b7da6 200 W kept.
Iterations (wood-crop R/G, f1 / f31 / f95): r5 2.60 / 2.59 / 2.07 -> seen-hex lights 1.47 / 1.46 / 1.28 (too neutral, lost the
candle warmth) -> midway amber 1.64 / 1.62 / 1.43 -> albedo nudges 1.52 / 1.51 / 1.35 -> final 1.43 / 1.42 / 1.29.
Crops: f1/f31 x1600 y850 300x200; f95 x900 y850 300x150 (tool: /tmp/claude-501/sk/table/art/rg.py).
Stills: f1 130/40, f31 128/40, f95 126/50 (ok), 3.0–4.6 s/frame. Look: brown walnut, candle pool, cream napkins, charcoal
plate with a cool rim, ruby tuna; no pink cast.
