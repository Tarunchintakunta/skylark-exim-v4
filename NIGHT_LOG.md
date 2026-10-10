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
