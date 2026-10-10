---
name: Blender scene
about: One scene built, self-reviewed, rendered, encoded and wired
labels: 'scene'
---
## Goal
Build `assets-src/blender/<blend>.blend` → clip(s) `<ids>` per docs/SCENES.md §S<n> and docs/STORYBOARD.md.
## Acceptance criteria
- [ ] Contents & density list met (SCENES.md §S<n>)
- [ ] `blender/scene_audit.py` → AUDIT PASS
- [ ] Preview + 12-frame sheet in docs/renders; review rounds docs/reviews/<blend>-rN.md (≤ 4); all G-SCENE gates PASS
- [ ] Boundaries: `scripts/boundary-check.sh` OK for both joins
- [ ] Full render (or preview-grade, flagged) → encode → posters → `scripts/check-clip.sh` clean
- [ ] Wired into its chapter; chapter screenshot desktop + mobile, down + up scroll, in the PR
## Sources
docs/SCENES.md §S<n> · docs/STORYBOARD.md · docs/ASSET_LIBRARY.md · scripts/scenes.sh
