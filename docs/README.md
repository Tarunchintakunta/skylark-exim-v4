# Skylark Exim v4 — overnight handoff pack ("Trace it back")

**What this is:** everything Claude Code needs to build a brand-new, second Skylark Exim website overnight, alone: a cinematic Zoi-style scroll story in which the camera travels *backwards* along a carton's journey — from a buyer's dinner table abroad, through the reefer at sea, Vizag port, the Anandapuram cold store and plant, the chilled truck, to the partner farm pond and the fishing boat at dawn — then turns round into products, quality, markets, the partners and a quote form. Every visual is built in Blender or live 3D. No AI media, no stock. Facts only from skylarkexim.com. The current v3 site keeps going separately.

## Paste order
1. Unzip `skylark-v4-pack.zip` somewhere on the Mac (e.g. `~/skylark-v4-pack`).
2. Open Claude Code in an empty folder (e.g. `~/code`), with the Blender MCP connector running and Blender open, `gh` and `vercel` logged in to your accounts.
3. Paste the whole of `CLAUDE_MASTER_PROMPT.md` (everything under the line), and add one line on top: `The pack is at ~/skylark-v4-pack.`
4. Leave the Mac plugged in, lid open (Claude also runs `caffeinate`). Go to sleep.

## What Claude does overnight
Creates the private repo `Tarunchintakunta/skylark-exim-v4` (README-only first commit), issues/milestones/project, PLAN.md and NIGHT_LOG.md; builds the site engine; builds every Blender asset and scene one by one, self-reviewing each against QUALITY_GATES.md with contact sheets (up to 4 rounds); renders 960×540 previews for all scenes first, then full 1080p renders in priority order in the background; wires the best available render into every chapter so the site is always complete; builds products/quality/markets/people/RFQ; deploys previews to Vercel by CLI at milestones only; tests speed on the deployed preview; opens small stacked PRs with micro commits; never pushes to main and never merges.

## What you check in the morning
`MORNING_CHECKLIST.md` (≈ 20 min): the report comment on the top PR, the preview on phone and laptop, each chapter, the products, the `[CONFIRM]` questions, then merge in the order given (only you merge).

## Files
| File | Purpose |
|---|---|
| CLAUDE_MASTER_PROMPT.md | the single paste-in prompt |
| STORY_OPTIONS.md / STORY.md | 3 concepts, the chosen one, palette + fonts |
| STORYBOARD.md | every chapter shot by shot: copy, scroll, camera, frames, bridges, mobile |
| SCENES.md / ASSET_LIBRARY.md | every Blender scene and every model (64 items) with PM briefs and budgets |
| QUALITY_GATES.md | hard pass/fail gates + the self-critique procedure |
| PRD.md / TRD.md | product + technical requirements and budgets |
| RENDER_PIPELINE.md, scripts/, blender/ | render/encode/check tooling (tested on synthetic clips) |
| GIT_WORKFLOW.md / DEPLOY.md | repo, issues, micro commits, PRs, Vercel rate-limit-safe deploys |
| CONTENT.md / BANNED_CLAIMS.md | verified facts (re-fetched 10 Oct 2026) and what may never be said |
| ASSETS.md / LICENSES.template.md | scan URLs, CC0 sources, fonts, licence log |
| REFERENCES.md, reference/ | the 6 reference sites analysed and mapped to chapters |
| MORNING_CHECKLIST.md | your morning review |
