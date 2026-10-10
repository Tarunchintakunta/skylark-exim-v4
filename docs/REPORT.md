# REPORT.md — morning report, Sat 10 Oct 2026 (IST)

Night run: 00:23 → 09:00. Nothing was merged. Nothing was pushed to main after the README commit. No AI media of any kind was used: Blender (factory startup, the installed AI extension never loaded), code, typography and CC0 / CC BY scans only.

**Headline:** the site is complete and passes almost every gate locally. All 13 film chapters are real Blender renders, but only at **preview grade** (960×540 renders, upscaled). **There is no preview URL**, because every Vercel CLI deploy landed as production. I removed those deployments and stopped. That item is `needs-tarun` on #30.

## 1. Preview URLs

| URL  | Opens without login? |
| ---- | -------------------- |
| none | —                    |

- Vercel CLI 59.25 created every deployment as **production**. That happened with a plain `vercel deploy`, with `--target=preview`, and from a git-less copy.
- The likely cause: `vercel link` auto-connected the GitHub repo, with production branch `main`.
- The three deployments (i8i28zbit, nz8z50105, 9y40eygo8) each lived under 5 minutes and were removed. One more upload failed.
- To fix: check Vercel → Project → Settings → Git / Environments. Then run `vercel deploy` from `scene/31-media-refresh` and it should make a real preview.
- Every number below is from `vite preview` on localhost.

## 2. Chapters

All 13 clips pass `check-clip` (H.264, GOP 6, no B-frames, faststart, caps). `boundary-check` gives SSIM 1.000 on all 12 joins. That is **after equalising**: frame B1 is a copy of frame A-last. The native SSIM is listed per join because a low value means a visible change one frame after the cut.

Sizes are KB for the 1920 / 1280 / 960 tiers. Caps are 2,250 / 1,600 / 1,000.

| Ch  | Scene         | Clip     | Status                     | Gates                                                           | KB 1920 / 1280 / 960 | PR  |
| --- | ------------- | -------- | -------------------------- | --------------------------------------------------------------- | -------------------- | --- |
| 1   | S1 table      | v-table  | preview-grade              | look PARTIAL (food/hands CG); join out BRIDGE_FROST native 0.26 | 2048 / 1572 / 928    | #53 |
| 2   | S2 port       | v-port   | preview-grade              | density PASS; far hills FAIL; joins 0.990 / 0.987               | 2217 / 1483 / 988    | #56 |
| 3   | S3 reefer     | v-reefer | preview-grade              | wake PASS; frost luma/sd FAIL at 10 % (mean 226, sd 7)          | 2085 / 1533 / 904    | #58 |
| 4   | S4 sea        | v-sea    | preview-grade (best scene) | self-review r4 PASS (minor)                                     | 2221 / 1598 / 938    | #55 |
| 5   | S5 pond       | v-pond   | preview-grade              | aerators PARTIAL; join BRIDGE_HORIZON 0.911                     | 2124 / 1441 / 907    | #57 |
| 6   | S6 truck      | v-truck  | preview-grade              | look FAIL (toy-like); join BRIDGE_COAST native 0.58             | 2106 / 1566 / 912    | #54 |
| 7   | S7 cold store | v-cold   | preview-grade              | density PASS                                                    | 2054 / 1561 / 996    | #59 |
| 8   | S7 packing    | v-pack   | preview-grade              | PPE PASS; luma FAIL at 10 % (sd 10–11)                          | 2118 / 1600 / 948    | #59 |
| 9   | S7 IQF freeze | v-freeze | preview-grade              | join BRIDGE_BELT native 0.07                                    | 2240 / 1534 / 939    | #59 |
| 10  | S8 QC lab     | v-qc     | preview-grade              | PPE FAIL (lab tech in jeans); sd 12 at 10 %                     | 2044 / 1600 / 900    | #60 |
| 11  | S8 grading    | v-grade  | preview-grade              | sd 11 at 10 % FAIL                                              | 2224 / 1520 / 883    | #60 |
| 12  | S8 peeling    | v-peel   | preview-grade              | density PASS                                                    | 2056 / 1581 / 934    | #60 |
| 13  | S8 wash/dock  | v-wash   | preview-grade              | join BRIDGE_DOCK native 0.48                                    | 2208 / 1448 / 933    | #60 |

- **Full 1080p renders: none.** The GPU was shared all night with another Claude session's v3 renders, which ran 6 Blender jobs at a time. Then a network outage (about 05:25–08:30) stopped every worker. The v-sea full render was queued but deferred, then lost.
- **Product models (#51):**
  - tuna 478 KB and prawn 440 KB both pass G-PROD.
  - hero carton is 110 KB.
  - Swordfish is omitted: there was no good model, and no placeholder is shown.
- **Markets map:** Blender stills at 1920 and 960. The projection check passes.

## 3. Business sections, performance, weight

| Section                                                | Status       |
| ------------------------------------------------------ | ------------ |
| B1 Now forward (live carton GLB)                       | done #49     |
| B2 Products (tuna, prawn live; lists; Enquire prefill) | done #50     |
| B3 Quality & facility                                  | done #42     |
| B4 Markets (map + routes by scroll)                    | done #47     |
| B5 People                                              | done #43     |
| B6 Quote (zod, mailto, company profile PDF 1,622 KB)   | done #44     |
| Footer, /licenses, 404, SEO / OG / JSON-LD             | done #45 #46 |

**Final local test run (08:50):** 23 passed, 1 skipped, 2 failed. The full log is `logs/tests-final.log`.

- The smoke, content / banned claims, G-SITE-1, axe (desktop and mobile, 3 positions), reduced motion, rfq unit and weight suites all pass.
- One-headline passes at 360, 390, 1440 and 1920.
- **FAIL** chapters-media (desktop). Five samples at 10 % into a chapter are too uniform (sd < 12): v-pack, v-grade, v-qc and v-reefer. The cause is the over-white plant and reefer interiors, which is a media problem, not a code problem. The same test passes on mobile.
- **FAIL** scroll-perf (desktop): 1 long task against a budget of 0. rAF p95 is 16.8 ms and there were 0 stalls. Mobile passes with 7 long tasks, p95 16.8 ms and 1 stall (budget ≤ 2).

**Lighthouse** (lhci, 3 runs, localhost `/index.html`):

| Metric         | Result    |
| -------------- | --------- |
| Performance    | 97        |
| Accessibility  | 100       |
| Best Practices | 100       |
| SEO            | 100       |
| LCP            | 2.3–2.4 s |
| TBT            | 10–60 ms  |
| CLS            | 0         |

**MB per tier, full scroll** (`scripts/path-weight.sh`):

| Tier         | Full scroll | Budget |
| ------------ | ----------- | ------ |
| desktop 1920 | 28.9 MB     | 32 MB  |
| laptop 1280  | 21.1 MB     | 22 MB  |
| mobile 960   | 13.2 MB     | 14 MB  |

Measured in the browser: desktop test viewport 21 MB, mobile 13.97 MB. The initial load is 0.27 MB.

## 4. Known issues

1. **Every film chapter is preview-grade.** The overall look reads CG or game-like. The worst offenders are truck (city-builder feel) and the port's far hills.
2. **Hard cuts.** Four joins had poor native continuity: frost 0.26, belt 0.07, dock 0.48 and coast 0.58. Equalising makes the boundary frame identical, but the next frame jumps.
3. **Plant interiors** (pack, qc, grade) and the reefer frost are washed out and nearly white. This is why chapters-media fails.
4. **Scene details:**
   - The QC lab tech wears jeans and orange shoes, which is not full PPE.
   - The pond has no or weak aerators.
   - The reefer ocean time runs backwards.
   - There is interpolation ghosting around table f196.
   - The truck aerial barely shows the sea.
5. **Interpolation.** Previews were rendered every 2nd frame. ffmpeg minterpolate filled the gaps, so fast motion can smear.
6. **Desktop perf.** There is 1 long task during the scripted scroll.
7. **No deployed numbers.** All performance figures are localhost only.
8. **Branch protection is not enabled.** GitHub refused it with a 403 on a private repo without Pro. The rules were followed manually.
9. **My mistake at 00:37.** I ran `pkill -f "vite preview --port 4173"` and stopped another project's preview server (pid 86792), probably the v3 session's. Please restart it if you need it. Nothing else outside v4 was touched.

## 5. [CONFIRM] questions and needs-tarun

These are open in CONTENT.md and were left neutral or omitted on the site:

- [CONFIRM] Is "diversified commodities" the right wording?
- [CONFIRM] Should it read "coastal communities" or "commodities"?
- [CONFIRM] Is "culture material and solvents" a product line to mention?
- [CONFIRM] Should Bangkok be listed separately from Thailand?
- [CONFIRM] Are the HOSO / HLSO / PUD expansions correct?
- [CONFIRM] What are the production domain and canonical URL? The canonical is currently `https://skylark-exim-v4.vercel.app`.
- [CONFIRM] Is the ffish.asia licence right? The scans are credited as CC BY 4.0 on /licenses and in the footer. ASSETS.md had said CC0.

`needs-tarun` items:

- **#30:** Vercel CLI deploys land in production, so there is no preview yet (see §1).
- **Vector logo.** The site uses a typographic wordmark. The live PNG logo is a busy raster image and was not traced.
- **GitHub Project.** It was skipped because the gh token has no `project` scope.

## 6. Merge order

Merge bottom first with "Create a merge commit". The full table is in `docs/STACK.md`.

#33 → #34 → #35 → #36 → #37 → #38 → #39 → #40 → #41 → #42 → #43 → #44 → #45 → #46 → #47 → #48 → **#51** → #49 → #50 → **#52** → #53 → #54 → #55 → #56 → #57 → #58 → #59 → #60 → #61

Watch the two out-of-number spots: #51 goes before #49, and #52 goes after #50.

## 7. Time per area (approximate, from NIGHT_LOG)

Many areas ran in parallel through subagents.

| Area                                                                           | Time                                                          |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| Pack reading, setup, repo, issues                                              | 00:23–00:31 · 10 min                                          |
| Site engine (clock, video pool, captions, header, a11y, tests/CI)              | 00:31–00:52 · 25 min                                          |
| Business sections, SEO, licenses                                               | 00:52–01:15 · 25 min                                          |
| Live 3D (B1/B2) and product GLBs                                               | 00:57–01:15, plus a products worker until ~03:00              |
| Blender library and 8 scene builders / previews                                | 01:00–05:25 · ~4.5 h wall clock, GPU-bound and shared with v3 |
| Render pipeline fixes (lock watchdog, ocean 70 s → 2 s/frame, light profiling) | ~45 min, spread across the run                                |
| Vercel deploy attempts and incident                                            | 04:30–04:50 · 20 min                                          |
| Network outage (all workers stopped)                                           | ~05:25–08:30 · ~3 h lost                                      |
| Media swap, equalise, tier re-encodes, budgets, final tests, PRs, report       | 08:30–09:00 · 30 min                                          |
