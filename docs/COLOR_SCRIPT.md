# COLOR_SCRIPT.md — Skylark v4 art direction (issue #75)

The journey runs backwards in time ("Trace it back"): the table at evening, the reefer ship at dusk, the plant during its working day, the truck in the morning, and the pond and the sea at sunrise. Each chapter has one **dominant mood** (about 60 % of the frame), a **secondary** colour (about 30 %) and a small **accent** (about 10 %, almost always marigold, the brand thread). The colour comes from the **light and the world**, never from a full-frame tint. QUALITY_GATES G-SCENE-8 still holds: no colour overlay, vignette ≤ 15 % (we use ≤ 12 %), and luma above the floor in check-clip.

Reference: drinkzoi.co is a deep navy field with soft out-of-focus light glows, cool ice highlights, and saturated colour only where light hits.

## 1. Chapters (scroll order)

All values are hex. K = colour temperature in kelvin.

| #   | Clip                  | Mood                                                        | Dominant                                            | Secondary                           | Accent                                          | Key light                                                    | Fill light                                      | Rim light                                                    | World / sky                                           | Fog / volume                                        |
| --- | --------------------- | ----------------------------------------------------------- | --------------------------------------------------- | ----------------------------------- | ----------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------- | --------------------------------------------------- |
| 00  | v-table               | Evening dinner, candle-warm                                 | `#3a1f14` walnut dusk                               | `#c8743a` amber                     | `#e2a03a` marigold                              | 2900 K `#ffb46b` window/pendant, from camera-left high       | `#5b7da6` cool blue from the window side, 0.25× | `#ff8a3d` warm candle rim behind the plates                  | `#1d2433` evening window bokeh                        | faint warm haze, density 0.002                      |
| 01  | v-reefer              | Frost → night ocean                                         | `#cfe6f2` frost cyan (macro) → `#123a5a` ocean blue | `#6fb7d9` ice blue                  | `#e2a03a` marigold (carton tape)                | interior: `#d9ecff` 6500 K LED; exterior: dusk sun `#ff9a5c` | `#3a5b8c`                                       | `#9fd8ff` ice rim on cartons / `#ff7b54` sun rim on the hull | dusk gradient `#1b2a4a` → `#e8825a` horizon           | interior cold mist `#cfe6f2` 0.004; sea haze 0.0008 |
| 02  | v-port                | Dusk harbour, purple-orange                                 | `#2b2147` dusk violet                               | `#e57a44` sunset orange             | `#ffd28a` sodium lamps                          | sun elev 8°, az 260°, `#ff8c4a`                              | sky `#4b4a8c`                                   | `#ffb06b` low sun rims on cranes and boxes                   | Nishita/sky dusk, horizon `#f29a5e`, zenith `#262457` | harbour haze `#c98a7a` 0.0006                       |
| 03  | v-cold                | Icy blue-violet cold store                                  | `#1e2a4f` deep ice violet                           | `#7aa6e0` frost blue                | `#e2a03a` marigold (bollards, carton tape)      | 7500 K `#cfe0ff` high-bay                                    | `#6b5fb5` violet bounce                         | `#9fe3ff` cyan rim on rack edges                             | `#0f1630`                                             | cold mist `#b9c8ff` 0.006 (door vapour)             |
| 04  | v-pack                | Clean cool plant + marigold                                 | `#dfe9f5` cool white-blue                           | `#5f86b8` steel blue                | `#e2a03a` marigold (tape, labels, aprons' ties) | 5500 K `#f2f6ff` panels                                      | `#8fb4e8`                                       | `#ffcf8a` warm rim from the doorway                          | `#1a2433`                                             | very light `#dfe9f5` 0.0015                         |
| 05  | v-freeze              | Icy cyan, glaze spray                                       | `#13324a` IQF steel-teal                            | `#8fe0f0` glaze cyan                | `#e2a03a` marigold                              | 8000 K `#d6ecff`                                             | `#4f6fa8`                                       | `#a8f0ff` spray backlight                                    | `#0d1a26`                                             | vapour `#cfefff` 0.008                              |
| 06  | v-qc                  | Lab: cool blue with warm lamp                               | `#d8e4f2` lab white-blue                            | `#3f6fa0` blue                      | `#f0b04a` warm task lamp                        | 5000 K `#eef4ff`                                             | `#7f9fd0`                                       | `#ffc27a` lamp rim                                           | `#18222e`                                             | none                                                |
| 07  | v-grade               | Cool blue line, crates on ice                               | `#2a4a6e` line blue                                 | `#bfe0f0` ice                       | `#e2a03a` marigold crates                       | 5500 K                                                       | `#7090c8`                                       | `#ffd59a` warm rim                                           | `#141e2a`                                             | light `#d0e4f2` 0.002                               |
| 08  | v-peel                | Busy hall, blue + warm skin                                 | `#3a5f86` hall blue                                 | `#e9eef5` PPE white                 | `#e2a03a` marigold                              | 5000 K                                                       | `#6c8cc0`                                       | `#ffc890`                                                    | `#141e2a`                                             | light 0.0015                                        |
| 09  | v-wash                | Water + morning through the dock                            | `#2f6e8a` water teal-blue                           | `#f2c27a` morning light at the door | `#e2a03a`                                       | interior 5500 K → doorway sun `#ffc078`                      | `#5d86b0`                                       | `#ffd08a` door backlight                                     | outside: morning `#9cc6e8`                            | wet haze `#cfe3ee` 0.003                            |
| 10  | v-truck               | Morning coast: gold + green                                 | `#d9a256` morning gold                              | `#4f7f4a` field green               | `#2f8fa0` sea teal                              | sun elev 20°, az 100°, `#ffc98a`                             | sky `#8fb8e0`                                   | `#ffd59a`                                                    | morning sky, horizon `#ffd7a0`, zenith `#5f93c8`      | morning haze `#e8d2b0` 0.0005                       |
| 11  | v-pond                | Sunrise ponds: green-teal + soft yellow                     | `#2f6e68` lagoon green-teal                         | `#f2d27a` soft sunrise yellow       | `#e2a03a`                                       | sun elev 6°, az 95°, `#ffcf7a`                               | `#7fb6c8`                                       | `#ffe0a0` palm and net rims                                  | sunrise sky, horizon `#ffd98f`, zenith `#3f6f9a`      | low pond mist `#f4e2c0` 0.002                       |
| 12  | v-sea                 | Dawn sea: deep teal → dawn gold, sunrise orange on the boat | `#0f3d4a` deep teal                                 | `#f0b35a` dawn gold                 | `#ff7a3d` sunrise orange (boat, life ring)      | sun elev 4°, az 95°, `#ffb070`                               | `#4f8fa8`                                       | `#ffcf8a`                                                    | dawn sky, horizon `#ffbf7a`, zenith `#24496b`         | sea mist `#f0c9a0` 0.0006                           |
| P   | prod-tuna, prod-prawn | Zoi studio: navy + ice                                      | `#0f1d33` navy                                      | `#9fd8ff` ice                       | `#e2a03a`                                       | 5600 K softbox                                               | `#3a5b8c`                                       | `#9fe3ff`                                                    | `#0b1424`                                             | none                                                |

## 2. Bridges (shared frames must match on both sides)

Both scenes of a join use the same light at the shared frame. The exact frame is still equalised, with a 4-frame dissolve where it was already used.

| Join                          | Shared look at the bridge frame                                                                                   |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| table → reefer (BRIDGE_FROST) | frost macro lit by 6500 K `#e6f2ff` softbox, with a faint `#ffb46b` warm kick from the table side                 |
| reefer → port (BRIDGE_SEA)    | top-down sea at **dusk**: sun elev 8°, az 260°, `#ff8c4a`; sky dusk preset (updated from the old elev 52° midday) |
| port → cold (BRIDGE_DOOR)     | reefer doors at dusk: warm `#ff9a5c` side light from camera-left, violet sky fill `#4b4a8c`                       |
| freeze → qc (BRIDGE_BELT)     | belt top-down: cool 8000 K key, cyan rim, exposure as rendered by plant-cold                                      |
| wash → truck (BRIDGE_DOCK)    | dock looking out: interior 5500 K, outside morning sun 20°/100° `#ffc98a`                                         |
| truck → pond (BRIDGE_COAST)   | aerial: sun 15°, az 90°, `#ffc98a` (truck) / `#ffcf7a` (pond): same hue family                                    |
| pond → sea (BRIDGE_HORIZON)   | sunrise horizon: sun 4°, az 95°, `#ffb070`, horizon `#ffbf7a`                                                     |

## 3. Grade (Blender compositor, per scene, `assets-src/blender/lib/look.py`)

- **View transform:** AgX, look **"AgX - Punchy"** for exteriors and **"AgX - Medium High Contrast"** for interiors.
- **Lift / gamma / gain — complementary, not monochrome:** shadows lift toward the chapter's _cool_ colour (fill / secondary: teal, blue or violet), highlights warm toward the key (gain). Warm light against cool shadow gives the layered Zoi look. Lifting shadows into a warm dominant hue (gold, amber) turns the frame sepia: the truck test proved it, so don't. Interiors that are cool overall (cold store, IQF) do the reverse: cool lift, with the marigold accents and the warm doorway rim as the only warmth. Tint strength: lift ≤ 0.025, gain ≤ 0.035.
- **Saturation:** 1.08–1.15. **Contrast:** via the AgX look plus a gentle S-curve.
- **Bloom:** Glare node (Bloom / Fog Glow), threshold 1.0, mix ≈ −0.85, size 7–8, on highlights only.
- **Vignette:** ≤ 12 % at the corners (blurred ellipse mask multiply).
- **Film grain is applied on the web layer, not baked.** Grain baked into H.264 costs 30–60 % more bitrate and would break the 2,300 KB cap. The site adds a static SVG noise layer at 3–4 % opacity instead (an animated one doubled the scroll frame time, so it stays still).
- **Chained clips** (plant-cold v-cold/v-pack/v-freeze and plant-line v-qc…v-wash) use **one grade per .blend**, so the internal joins stay identical. Cross-file joins are equalised and boundary-checked afterwards.

## 4. Web layer palette (CSS custom properties)

The existing tokens (`--ink`, `--frost`, `--glaze`, `--steel`, `--marigold`, `--lagoon`) stay. Per-chapter variables are driven by scroll and blended between chapters with GSAP:

- `--ch-bg-a`: the gradient field behind and around the film (glow 1)
- `--ch-bg-b`: glow 2
- `--ch-accent`: eyebrow, countdown outline, hint line
- `--ch-glow`: the soft glow layer behind the active caption

| Clip     | --ch-bg-a | --ch-bg-b | --ch-accent | --ch-glow |
| -------- | --------- | --------- | ----------- | --------- |
| v-table  | `#2a1810` | `#5a3420` | `#e2a03a`   | `#c8743a` |
| v-reefer | `#0e2238` | `#1f4f73` | `#9fd8ff`   | `#6fb7d9` |
| v-port   | `#1d1838` | `#5a2f4a` | `#ffb06b`   | `#e57a44` |
| v-cold   | `#141c3a` | `#2c3a73` | `#9fe3ff`   | `#6b5fb5` |
| v-pack   | `#14202e` | `#28466a` | `#e2a03a`   | `#5f86b8` |
| v-freeze | `#0d1f2c` | `#164a5c` | `#8fe0f0`   | `#4f9fb8` |
| v-qc     | `#121c28` | `#2a4a6e` | `#f0b04a`   | `#3f6fa0` |
| v-grade  | `#101a26` | `#24456a` | `#e2a03a`   | `#7090c8` |
| v-peel   | `#101a26` | `#2c4f78` | `#e2a03a`   | `#6c8cc0` |
| v-wash   | `#0f1e28` | `#245a6e` | `#f2c27a`   | `#2f6e8a` |
| v-truck  | `#1f1a10` | `#4f5a2c` | `#ffc98a`   | `#d9a256` |
| v-pond   | `#0f2624` | `#2f6e68` | `#f2d27a`   | `#7fb6c8` |
| v-sea    | `#0b2228` | `#0f3d4a` | `#ffb070`   | `#f0b35a` |

Business sections (B1–B6) inherit the last chapter (v-sea dawn), then settle into a Zoi navy field `#0b1424` → `#13243b` with ice `#9fd8ff` and marigold accents.

## 5. Smoothness budget

- The colour layers are compositor-only: CSS gradients on `opacity` and `transform`, no animated `background-position` repaint across the full viewport. Custom-property updates are throttled to the one gsap ticker.
- The grain is a single static SVG noise tile moved with `transform` (GPU), at 3–4 % opacity, and disabled under `prefers-reduced-motion`.
- Long tasks budget stays at 0 after load.
