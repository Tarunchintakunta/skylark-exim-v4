# pond art pass: round 3

Sheet: docs/renders/pond-before-after.jpg (rows f1, f22, f108, f160, f194, f216; before on the left, after on the right, 960 px each).

## Changes
- Exposure +0.35 (AgX Punchy), so frames are no darker than before.
- Rim sun #ffe0a0 raised 1.1 → 1.6.
- BRIDGE_HORIZON (lead request): the sky tint is keyed. f1–150 keep row 11 (horizon #ffd98f, camera zenith #3f6f9a, lighting zenith #7fb6c8). At f216 both camera and lighting rays use sea.py's gradient (horizon #ffbf7a → zenith #24496b, max-normalised, mix 0.85, top 0.24).
- End ramp: exposure is keyed 0.35 at f180 → 1.05 at f216 to meet sea f1.

## Judgement
- **Not empty.** All frames were already populated.
- **Not more toy-like.** The fields are a touch saturated at f1/f22 but read as paddy.
- **Not fake.** Colour comes from the light and the sky: warm horizon and glints, cool teal shadows. There is no overlay.
- **No clipping.**
- **Rich colour, not grey.** The water is lagoon green-teal, the floats and aerator paddles are marigold, and the f194/f216 sunrise is peach against a blue zenith.

## Luma (full res, before ramp)
| Frame | Before | After |
|---|---|---|
| f1 | 143/45 | 122/29 |
| f22 | 139/26 | 125/32 |
| f108 | 186/47 | 185/48 |
| f160 | 142/55 | 132/58 |
| f194 | 180/53 | 160/56 |
| f216 | 203/27 | 172/39 → 191/34 with the ramp (probe) |

All pass.

The aerial frames are somewhat darker than before, because the old version was washed out by grey haze. They are within gates.

## BRIDGE_HORIZON check
SSIM of f216 vs render/sea/0001.png:
- 0.881 without the ramp;
- 0.918 with the ramp (exposure 1.05).

Remaining difference: sea f1 has a whiter, bloomier horizon glow and its sun disc is blown out. The lead's equalising step will close that gap.

Still time (full res, 32 spp): 1.7–7.5 s/frame with a warm shader cache (f1 12.6 s cold).
