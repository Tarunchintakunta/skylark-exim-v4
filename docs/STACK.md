# STACK.md — PR stack and merge order (bottom first, "Create a merge commit")

Every PR is based on the one before it, so each preview deploy (made from the top branch) contains everything.
Merge strictly in this order; after each merge GitHub retargets the next PR to main automatically.

| #   | PR  | Branch                   | Issue                             |
| --- | --- | ------------------------ | --------------------------------- |
| 1   | #33 | docs/1-handoff-pack      | #1                                |
| 2   | #34 | chore/2-scaffold         | #2                                |
| 3   | #35 | feat/3-tokens-fonts      | #3                                |
| 4   | #36 | feat/4-clock             | #4                                |
| 5   | #37 | feat/5-video-pool        | #5                                |
| 6   | #38 | feat/6-copy-captions     | #6                                |
| 7   | #39 | feat/7-header-menu       | #7                                |
| 8   | #40 | feat/8-reduced-motion    | #8                                |
| 9   | #41 | chore/9-tests-ci         | #9                                |
| 10  | #42 | feat/23-quality          | #23                               |
| 11  | #43 | feat/25-people           | #25                               |
| 12  | #44 | feat/26-quote            | #26                               |
| 13  | #45 | feat/27-footer-licenses  | #27                               |
| 14  | #46 | feat/28-seo              | #28                               |
| 15  | #47 | feat/24-markets          | #24                               |
| 16  | #48 | asset/10-blender-library | #10                               |
| 17  | #51 | asset/11-product-models  | #11                               |
| 18  | #49 | feat/21-now-forward      | #21                               |
| 19  | #50 | feat/22-products         | #22                               |
| 20  | #52 | perf/29-mobile-pass      | #29                               |
| 21  | #53 | scene/12-table           | #12                               |
| 22  | #54 | scene/17-truck           | #17                               |
| 23  | #55 | scene/15-sea             | #15                               |
| 24  | #56 | scene/13-port            | #13                               |
| 25  | #57 | scene/16-pond            | #16                               |
| 26  | #58 | scene/14-reefer          | #14                               |
| 27  | #59 | scene/18-plant-cold      | #18                               |
| 28  | #60 | scene/19-plant-line      | #19                               |
| 29  | #61 | scene/31-media-refresh   | #31 (also covers #20, #32 report) |

Note the table order, not the PR numbers: #51 (asset/11) sits below #49, and #52 (perf/29) sits above #50.
#63 holds the reverted Git-deploy attempt (deploys stay off; #30 stays needs-tarun, see docs/REPORT.md). The morning report is committed on the top branch (#61).
