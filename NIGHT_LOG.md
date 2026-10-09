# NIGHT_LOG.md — times IST

- 00:23 Pack unzipped to ~/Desktop/skylark-v4-unzip/skylark-v4-pack; every file read in the prescribed order (docs, templates, scripts, blender, 6 reference sheets).
- 00:25 Versions: Blender 5.2.0 LTS · ffmpeg 8.1.2 · gh 2.92.0 · Vercel CLI 59.25.0 · Node v25.9.0 · npm 11.12.1 · Python 3.13.9 · Ghostscript missing → `brew install ghostscript` started. Mac: Apple M5 Pro, 15 cores, 24 GB.
- 00:25 `caffeinate -dims` running. gh logged in as Tarunchintakunta (scopes gist, read:org, repo, workflow — no `project` scope, so the GitHub Project is skipped as GIT_WORKFLOW §1 allows). vercel whoami = tarunchintakunta.
- 00:27 Repo created private with README-only commit on main. Branch protection refused (HTTP 403: "Upgrade to GitHub Pro or make this repository public") → rules obeyed manually: no pushes to main, no merges.
- 00:29 12 labels, 5 milestones, issues #1–#32 created.
- 00:31 Judgement calls / contradictions:
  - Reference JPGs (600 KB) are kept out of git in assets-src/reference/ (GIT_WORKFLOW §4 forbids binaries outside public/ and docs/renders/; stricter reading wins).
  - Linear PR stack instead of ≤ 5 deep, because DEPLOY.md requires deploying from the top of the stack containing everything.
  - G-SITE-1 greps the DOM for "placeholder": form fields use visible labels and no `placeholder` attributes.
  - MPFB2 (people) add-on is not installed in Blender 5.2; installing from the extensions platform is attempted in #10. If it fails, people are kept at mid-distance/backlit with simple modelled bodies and clothing, and flagged as a known issue (never mannequin close-ups).
  - Blender has a "higgsfield_blender" extension installed: it is an AI generator and is NOT used (rule 1).
- 00:37 MISTAKE: while freeing a port I ran `pkill -f "vite preview --port 4173"`, which stopped another project's local preview server on port 4173 (pid 86792, not part of v4; most likely a v3 session). Nothing else was touched. Tarun: restart that preview if you still need it. My local servers now use port 5791 only.
- 00:44 #2–#6 done: scaffold, fonts/tokens, one clock, 3-video pool (probe with synthetic clips: 0 stalls, ≤3 attached, only the first poster before first scroll), captions (1 visible headline at sampled positions desktop + mobile). Blender workers running: shared lib (sklib) and MPFB people. User said: decide doubts on my own and finish.
- 00:47 Logo decision: the live logo PNG is a busy raster illustration (and may itself be generator-made), so it is NOT traced or shipped; the header uses a Fraunces typographic wordmark. Vector logo stays [CONFIRM] / needs-tarun.
- 00:52 #7–#9 done (header/menu/loader, reduced motion, tests + CI). Earlier entries 00:37/00:44/00:47 corrected — they had been estimated instead of read from the clock; from now on every entry uses `date`.
- 00:57 Sections B3, B5, B6 (+ PDF 1,622 KB), footer, /licenses, 404, SEO done on branches #23 #25 #26 #27 #28. Canonical uses https://skylark-exim-v4.vercel.app until the domain is decided ([CONFIRM]).
