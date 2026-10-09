# ASSETS.md — external sources (URLs only; nothing binary is in this pack)

## Photoreal scans (Objaverse on Hugging Face, no login; download with scripts/fetch-scans.sh)

> Correction (10 Oct 2026, from the Objaverse/Sketchfab metadata): the ffish.asia scans are **CC BY 4.0, not CC0** — credit "ffish.asia / floraZia.com" (done on /licenses and in the footer).
| ID | Species | URL | Licence | Notes |
|---|---|---|---|---|
| A-PROD-TUNA | Yellowfin tuna (ffish.asia scan) | https://huggingface.co/datasets/allenai/objaverse/resolve/main/glbs/000-129/d4eeea976932414d91fc786ce6cec547.glb | CC0 | ~57 MB, split into ~20 chunks of 65k verts; colour-checker cube included → clean_scan.py; fins ragged in v3 → rebuild |
| A-PROD-PRAWN | Green tiger prawn (ffish.asia) | https://huggingface.co/datasets/allenai/objaverse/resolve/main/glbs/000-044/af273265e0324bc4a645ebad96c254df.glb | CC0 | checker cube; heavy |
| A-PROD-PRAWN-ALT | Tiger prawn by aniljaco | https://huggingface.co/datasets/allenai/objaverse/resolve/main/glbs/000-146/9ea34d3bfbf24b13aa8a37115b1e6551.glb | CC-BY 4.0 | 1.4 MB; credit "aniljaco" in docs/LICENSES.md + /licenses if used |
| A-PROD-SKIPJACK | Skipjack (ffish.asia) | https://huggingface.co/datasets/allenai/objaverse/resolve/main/glbs/000-157/9431157b2fce4ea9a72d9cfe3ce37a6d.glb | CC0 | filler in catch heaps, never labelled |
| A-PROD-SHRIMP-FILLER | Greasyback shrimp (ffish.asia) | https://huggingface.co/datasets/allenai/objaverse/resolve/main/glbs/000-050/8680087cf63643f48b6de895ca288df6.glb | CC0 | filler only (species not in CONTENT.md) |
| — | Swordfish | none exists without login | — | model in Blender (A-PROD-SWORDFISH) or omit |
Verify each licence from the Objaverse/Sketchfab metadata (`objaverse` annotations) before use and record in docs/LICENSES.md.

## CC0 textures, HDRIs, plants, props (photo-scanned, not AI; no login)
- Poly Haven — https://polyhaven.com (textures, HDRIs, some models; CC0; API https://api.polyhaven.com)
- ambientCG — https://ambientcg.com (PBR materials; CC0)
- MPFB2 / MakeHuman — https://static.makehumancommunity.org/mpfb.html (human bodies, clothes; outputs CC0; add-on GPL)
- Elevation for coast/map: NASA SRTM / GEBCO / Natural Earth (public domain) — credit in LICENSES.
Not allowed: AI generators, paid stores, login-gated packs, stock video/photos.

## Skylark files (download once)
- Logo PNG: https://skylarkexim.com/wp-content/uploads/2025/10/Logo-11-scaled.png → trace to SVG (`[CONFIRM]` vector from Tarun)
- Company profile PDF: https://skylarkexim.com/wp-content/uploads/2025/10/SKYLARK-EXIM-PPT-for-pdf.pdf → compress ≤ 2,300 KB (`gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -dColorImageResolution=150`)

## Fonts (OFL 1.1)
- Fraunces — https://github.com/google/fonts/tree/main/ofl/fraunces (or `@fontsource-variable/fraunces`)
- Hanken Grotesk — https://github.com/google/fonts/tree/main/ofl/hankengrotesk (or `@fontsource-variable/hanken-grotesk`)
Subset with `pyftsubset` (fonttools) to Latin + − ° NBSP thin space; commit WOFF2 + OFL.txt.
