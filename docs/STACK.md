# STACK.md — PR stack and merge order (bottom first, "Create a merge commit")

Every PR is based on the one before it, so each preview deploy (made from the top branch) contains everything.
Merge strictly in this order; after each merge GitHub retargets the next PR to main automatically.

| # | PR | Branch | Issue |
|---|---|---|---|
| 1 | #33 | docs/1-handoff-pack | #1 |
| 2 | #34 | chore/2-scaffold | #2 |
| 3 | #35 | feat/3-tokens-fonts | #3 |
| 4 | #36 | feat/4-clock | #4 |
| 5 | #37 | feat/5-video-pool | #5 |
| 6 | #38 | feat/6-copy-captions | #6 |
| 7 | #39 | feat/7-header-menu | #7 |
| 8 | #40 | feat/8-reduced-motion | #8 |
| 9 | #41 | chore/9-tests-ci | #9 |
| 10 | #42 | feat/23-quality | #23 |
| 11 | #43 | feat/25-people | #25 |
| 12 | #44 | feat/26-quote | #26 |
| 13 | #45 | feat/27-footer-licenses | #27 |
| 14 | #46 | feat/28-seo | #28 |
| 15 | #47 | feat/24-markets | #24 |
| 16 | #48 | asset/10-blender-library | #10 |
| 17 | (pending) | asset/11-product-models | #11 |
| 18 | #49 | feat/21-now-forward | #21 |
| 19 | #50 | feat/22-products | #22 |

Scene, deploy and report PRs are added above as they open.
