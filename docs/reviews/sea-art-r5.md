# sea art pass r5-r6 (lead notes: no world fog, complementary grade, not darker than before)

- No world fog: sea.py never calls look.fog or look.apply. The mist #f0c9a0 0.0006 is a bounded volume box, SK_MIST, 1.2 km x 1.2 km x 60 m.
- Grade per COLOR_SCRIPT §3: complementary. Lift is deep teal #0f3d4a (amount 0.025), gain is dawn gold #ffb070 (0.03), sat 1.12, vignette 0.10,
  AgX - Medium High Contrast (the lead's tested look).
- Brightness: r4 was darker than before, so r5 set exposure 0 with fill 2.2 / rim 3600, and r6 set exposure +0.25 with fill 3.0.

| Frame | Before | r4 | r5 | r6 (final) |
|---|---|---|---|---|
| f1 | 203/27 | 212/27 | 220/24 | 224/22 |
| f27 | 223/21 | 209/33 | 217/30 | 222/27 |
| f132 | 131/50 | 93/53 | 105/53 | 113/53 |
| f196 | 116/43 | 73/41 | 86/45 | 95/46 |
| f238 | 137/56 | 104/68 | 117/67 | 126/66 |
| f264 | 165/77 | 165/77 | 166/76 | 171/74 |

The remaining drop at f132-f238 (12-21 levels of mean) is the sea: it is now deep teal #0f3d4a, the row's dominant colour,
where before it was a pale grey sky reflection. The boat, crew and catch are as bright as before or brighter. More exposure
would wash out f1 and f27, which are already at 222-224. Before/after sheet: docs/renders/sea-before-after.jpg (r6).
