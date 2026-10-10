# REPORT.md — Skylark v4 status, Sat 10 Oct 2026, 18:15 IST

This covers the night run (00:23 → 09:00) and the day run (11:15 → 18:15). Nothing was merged, and nothing was pushed to `main` after the README commit, which is still its only commit. No AI media of any kind was used: Blender (always with `--factory-startup`, so the installed AI extension never loads), code, typography, and CC0 / CC BY 4.0 scans.

**Headline:**

- **All 13 film chapters are full 1080p renders** (EEVEE, AgX, 24 fps, every frame rendered). Each scene was reviewed against QUALITY_GATES on full-resolution frames and contact sheets.
- **The local suite passes:** 31 passed, 0 failed.
- **Lighthouse (localhost):** 97/100/100/100 on mobile and 100/100/100/100 on desktop.
- **There is still no preview URL.** The Git deploy, limited to `scene/31-media-refresh`, also landed as **Production**. Following your instruction I stopped, reverted it and removed the deployment. Every number below is from `vite preview` on localhost, not from a deployed preview.

## 1. Preview URL

| URL  | Opens without login? |
| ---- | -------------------- |
| none | —                    |

**What happened:**

- **Night:** Vercel CLI deploys (plain, `--target=preview`, git-less) all landed as production and were removed.
- **Day:** `vercel.json` set `git.deploymentEnabled = {"main": false, "**": false, "scene/31-media-refresh": true}`.
  - Pushing `infra/30-git-preview` created nothing, which is correct.
  - Pushing `scene/31-media-refresh` created `dpl_BqDJKPSsGzLF7k12UHJmmtM5bYRZ` with **target: production**.
  - That push came from `gitSource.ref scene/31-media-refresh`, while the project's `productionBranch` is `main`.
- **Cleanup:**
  - Git deploys were set back to `false`.
  - The deployment was removed after ~3 min.
  - `vercel ls` is empty.

**What to check in the Vercel dashboard** (project skylark-exim-v4, Settings → Environments / Git):

- Why non-production branches deploy to Production. My guess is that the project has never kept a production deployment, so Vercel promotes the first one.
- Deployment Protection is on (`ssoProtection: all_except_custom_domains`). A preview will **not** open without a Vercel login unless you add a share link or a protection bypass.

Once a real preview exists, run the deployed checks with:

```
PERF_URL=<url> npx playwright test
```

## 2. Chapters — all full quality

- Sizes are in KB for the 1920 / 1280 / 960 tiers. The caps are 2,250 / 1,600 / 700; 960 was lowered from 1,000, see §4.
- **Native join** is the SSIM of the two scenes' own bridge frames before equalising.
- After `scripts/equalise-boundaries.sh`, every join is pixel-identical (`boundary-check` 12/12 at SSIM 1.000).
- Joins with a low native match also get a 4-frame dissolve inside the next clip (`scripts/soften-join.sh`), so they don't jump.
- **s/frame** is the average full-render time on the shared GPU. The v3 session was rendering 2–8 jobs throughout.

| Ch  | Scene         | Clip     | Frames        | s/frame | Gates                                                                 | Native join in        | KB 1920 / 1280 / 960 | PR  |
| --- | ------------- | -------- | ------------- | ------- | --------------------------------------------------------------------- | --------------------- | -------------------- | --- |
| 1   | S1 table      | v-table  | 216           | 6.4     | PASS (10: opening is a high-angle 58 mm f/2 macro, not pure top-down) | —                     | 2126 / 1470 / 641    | #53 |
| 2   | S3 reefer     | v-reefer | 192           | 8.7     | PASS                                                                  | frost 0.32 → dissolve | 2120 / 1556 / 651    | #58 |
| 3   | S2 port       | v-port   | 264           | 8.3     | PASS                                                                  | sea 0.989             | 2222 / 1463 / 651    | #56 |
| 4   | S7 cold store | v-cold   | 574 (3 clips) | 10.7    | PASS                                                                  | door 0.978            | 2124 / 1427 / 676    | #59 |
| 5   | S7 packing    | v-pack   | ↑             | ↑       | PASS                                                                  | inside blend          | 1987 / 1521 / 670    | #59 |
| 6   | S7 IQF        | v-freeze | ↑             | ↑       | PASS                                                                  | inside blend          | 2010 / 1459 / 625    | #59 |
| 7   | S8 QC lab     | v-qc     | 765 (4 clips) | 11.8    | PASS (lab tech now in full PPE)                                       | belt 0.959            | 2066 / 1570 / 666    | #60 |
| 8   | S8 grading    | v-grade  | ↑             | ↑       | PASS                                                                  | inside blend          | 2105 / 1465 / 685    | #60 |
| 9   | S8 peeling    | v-peel   | ↑             | ↑       | PASS                                                                  | inside blend          | 2129 / 1502 / 634    | #60 |
| 10  | S8 wash/dock  | v-wash   | ↑             | ↑       | PASS                                                                  | inside blend          | 2008 / 1485 / 687    | #60 |
| 11  | S6 truck      | v-truck  | 216           | 6.3     | PASS                                                                  | dock 0.55 → dissolve  | 2215 / 1466 / 634    | #54 |
| 12  | S5 pond       | v-pond   | 216           | 11.1    | PASS                                                                  | coast 0.53 → dissolve | 2156 / 1464 / 638    | #57 |
| 13  | S4 sea        | v-sea    | 264           | 8.4     | PASS                                                                  | horizon 0.944         | 2093 / 1491 / 654    | #55 |

**Product turntables (S10 fallbacks, PR #66).** prod-tuna and prod-prawn are rendered at full 1080p: 120 frames each, a 360° loop on a crushed-ice slab under a studio HDRI, about 5.5 s/frame. G-PROD-2/3/4 and G-SCENE-8 pass, and check-clip passes. The sizes are 2014 / 1168 / 686 KB (tuna) and 2031 / 1178 / 696 KB (prawn). They are **not wired into B2**, because the live GLBs still pass G-PROD.

**Swordfish** (A-PROD-SWORDFISH) was modelled procedurally and reviewed over 4 rounds. Proportions pass, but at 100 % zoom it reads as clean CG: airbrushed skin, hard seams where the fins meet the body, and a bead-like eye. That fails G-PROD-2 and G-PROD-4, so per ASSET_LIBRARY §7 swordfish stays a text entry and no swordfish turntable was rendered (`docs/reviews/swordfish-final.md`).

**Every render in `scripts/scenes.sh` is now done**, except prod-swordfish, which is intentionally not rendered because its model failed.

**Main fixes per scene.** The details are in each scene PR's "full 1080p" comment and in `docs/reviews/*-full-final.md`.

- **table:**
  - Rebuilt food on the CC0 prawn scan, real cutlery and glass (the glasses are no longer black).
  - Hands are kept out of frame.
  - The frost bridge is about 26k 3D crystals.
  - The OG image is regenerated from frame 1.
- **reefer:**
  - The frost now has texture, and the camera leaves it by f22.
  - The interior is no longer white-out.
  - The ocean runs forwards. The port ocean is offset to t = 8.0 so the waves continue across the cut.
- **port:**
  - Real vegetated hills, reshaped tugs and cab.
  - The diagonal crane shadow stripes are gone.
  - Motion blur is keyed to camera speed.
- **plant-cold:**
  - AgX Medium High Contrast and darker surfaces.
  - The packing door beat is re-planned (v-pack at 10 % was 195/10 FAIL, now 163/23).
  - Lights merged (39 → few), which brought the frame time down.
- **plant-line:**
  - The washed-out look came from sky light lighting the closed interior; fixed.
  - The lab and grading beats are re-planned (v-qc at 10 % now 189/20, v-grade at 10 % now 174/26).
  - The lab tech now wears full PPE.
  - Frame time went from 65 s to 12 s (clothing baked once, frustum culling, 8 lights).
- **truck:**
  - An Indian cab-over truck.
  - A busy, lived-in yard and real terrain (~23k instanced trees).
  - The sea is clearly visible on the coast at f216.
- **pond:**
  - 29 aerators with foam trails, murky water, and a net in the water.
  - Fields and hamlets.
  - The coast is rebuilt to match the truck's coast.
- **sea:** the white-ring reflections are fixed.

## 3. Tests, Lighthouse, weight (localhost, final run 17:55 on the top branch)

**Playwright: 31 passed, 0 failed.** The 7 skipped are by design: one-headline runs every width under the desktop project only, and the menu test is desktop-only. Logs are in `logs/tests-day2.log`.

| Suite                                                                 | Desktop 1440×900                                      | Mobile Pixel 7 (4× CPU, Fast 4G)                |
| --------------------------------------------------------------------- | ----------------------------------------------------- | ----------------------------------------------- |
| smoke, content / banned claims, G-SITE-1, axe ×3, reduced motion, rfq | PASS                                                  | PASS                                            |
| one-headline @360 / 390 / 768 / 1280 / 1440 / 1920                    | PASS                                                  | —                                               |
| chapters-media (13 chapters × 10/50/90 %, down + up)                  | **PASS** (was FAIL)                                   | PASS                                            |
| scroll-perf                                                           | **PASS** long 0, rAF p95 16.7 ms, stalls 0 (was FAIL) | PASS long 7, p95 16.8 ms, stalls 0 (budget ≤ 2) |
| weight                                                                | PASS initial 0.26 MB, full 20.6 MB                    | PASS initial 0.25 MB, full 10.5 MB              |

**Lighthouse** (lhci, 3 runs each, `/index.html`, localhost):

| Preset           | Perf | A11y | BP  | SEO | LCP   | TBT     | CLS |
| ---------------- | ---- | ---- | --- | --- | ----- | ------- | --- |
| mobile (default) | 97   | 100  | 100 | 100 | 2.4 s | 0–10 ms | 0   |
| desktop          | 100  | 100  | 100 | 100 | 0.5 s | 0 ms    | 0   |

**MB per tier, full scroll** (`scripts/path-weight.sh`):

| Tier         | Weight  | Budget |
| ------------ | ------- | ------ |
| desktop 1920 | 28.9 MB | 32 MB  |
| laptop 1280  | 20.4 MB | 22 MB  |
| mobile 960   | 9.7 MB  | 14 MB  |

**Media checks:** `check-clip` passes 13/13, `boundary-check` 12/12, and `check-media-refs` reports 117 references with 0 missing.

## 4. What fixed the two failing tests (PR #64)

- **Desktop long task:**
  - LoAF and CPU profiling showed one 60–90 ms render-only frame at page load. It had no script attribution and happened at t ≈ 250 ms, before any scroll.
  - The observer was created mid-frame and caught it.
  - G-SITE-5 counts "long tasks during a scripted full scroll after load", so the test now waits for idle and counts only tasks that start after that point. The budget is still 0.
  - SplitText also now splits each headline on first show rather than all 13 at load.
- **Washed-out frames:** fixed at the source in the full renders (exposure, AgX look, darker albedos, re-planned camera beats). Every chapter's 10/50/90 % frame is now sd ≥ 15.
- **Mobile stalls (found today):**
  - With ~950 KB clips the same test gave 14–16 stalls. That reproduced on last night's build too, so last night's "1 stall" was not representative.
  - At 9 Mbps a 950 KB clip takes ~0.85 s to arrive, while the scripted scroll crosses a mobile chapter in ~0.5 s.
  - The 960 tier is now re-encoded at ≤ 700 KB. Stalls are 0–2 and the mobile full scroll is 10.5 MB.
  - Desktop and laptop tiers are unchanged.

## 5. Known issues

1. **No deployed numbers.** Everything is localhost: no preview could be created without landing in production (§1).
2. **Joins with dissolves.** Table → reefer (frost, 0.32), plant-line → truck (dock, 0.55) and truck → pond (coast, 0.53) didn't match natively. The shared frame is identical and a 4-frame dissolve hides the rest, but a soft "melt" is visible if you scroll slowly.
3. **Plant-line opening:** a smooth but visible brightness bump during the f1–40 cross-fade from the plant-cold belt.
4. **Remaining CG tells, all minor and recorded in the reviews:**
   - table: matte frost crystals, a slightly waxy lemon.
   - port: crane booms deliberately cast no sun shadow, so the stripes are gone.
   - plant-cold: blotchy IQF frost close up.
   - plant-line: fluffy coat hems, strong blur at the lab door around f240–260.
   - truck: broadleaf crowns slightly stylised at ~150 m.
   - pond: static sea (the sunrise bridge relies on it).
   - sea: simple wheelhouse.
5. **Table opening:** it is a high-angle macro, not the storyboard's pure top-down.
6. **Product turntables:** at side-on angles the mobile centre crop shows only the middle of these long products. If the turntables are ever swapped in, they need `object-position` or letterboxing.
7. **Mobile video quality:** the 960 tier is softer at ≤ 700 KB (crf 30–37), which is visible on fine textures.
8. **Branch protection is not enabled.** GitHub returned a 403 on a private repo without Pro, so the rules were followed manually.
9. **Night-run mistake:** `pkill` stopped another project's preview server on port 4173 (pid 86792). It is logged in NIGHT_LOG.

## 6. [CONFIRM] questions and needs-tarun

These are unchanged from the morning; the site stays neutral on each.

- **[CONFIRM] questions:**
  - Is "diversified commodities" the right wording, and is it "coastal communities" or "commodities"?
  - Should "culture material and solvents" appear?
  - Should Bangkok be listed separately from Thailand?
  - What do HOSO, HLSO and PUD expand to?
  - Is the canonical domain `https://skylark-exim-v4.vercel.app`, or a production domain?
  - The ffish.asia scans are CC BY 4.0 (credited). Can you confirm that licence?
- **needs-tarun:**
  - **#30:** fix the Vercel project so non-main branches deploy as Preview, and decide whether previews should open without login.
  - A vector logo. The site uses a typographic wordmark for now.
  - A GitHub Project, which was skipped because the token has no `project` scope.

## 7. Merge order (bottom first, "Create a merge commit")

**#33 → #34 → #35 → #36 → #37 → #38 → #39 → #40 → #41 → #42 → #43 → #44 → #45 → #46 → #47 → #48 → #51 → #49 → #50 → #52 → #53 → #54 → #55 → #56 → #57 → #58 → #59 → #60 → #63 → #64 → #66 → #61**

Out-of-number spots: #51 goes before #49, #52 after #50, and #63, #64 and #66 sit between #60 and #61. The full table is in `docs/STACK.md`. Today's renders were merged forward through the stack branches (merge commits named "stack update"). Each PR's diff against its base is still only its own work.

## 8. Time per area

| Area                                                                      | Time                                                            |
| ------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Night: setup, site engine, sections, 3D, previews, incidents              | 00:23–09:00 (see the night report in git history and NIGHT_LOG) |
| Day: Git preview attempt and incident                                     | 11:15–11:35 · 20 min                                            |
| Day: long-task diagnosis and fix                                          | 11:35–12:00 · 25 min                                            |
| Day: 8 parallel scene workers (review rounds, optimisation, full renders) | 11:45–17:20 · ~5.5 h wall clock, GPU-bound and shared with v3   |
| Day: encode, equalise, dissolves, OG, stack merges                        | as each scene landed, plus 17:20–17:40                          |
| Day: mobile stall/weight investigation, 700 KB tier                       | 17:40–17:55 · 15 min                                            |
| Day: final suite, Lighthouse ×2, report                                   | 17:55–18:15 · 20 min                                            |
| Day: product turntables (tuna, prawn) + swordfish attempt                 | 18:30–19:30 · ~1 h, two workers in parallel                     |
