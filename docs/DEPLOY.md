# DEPLOY.md — Vercel (Tarun's account, Hobby plan)

v3 hit "Deployment rate limited — retry in 24 hours" because every push to every branch deployed. v4 deploys only on purpose.

## 1. vercel.json (commit in the first infra PR)
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "cleanUrls": true,
  "git": { "deploymentEnabled": false },
  "headers": [
    { "source": "/(media|models|fonts|og)/(.*)", "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }] },
    { "source": "/(.*)", "headers": [
      { "key": "X-Content-Type-Options", "value": "nosniff" },
      { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
      { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" } ] }
  ]
}
```
`git.deploymentEnabled: false` stops Git-triggered deployments for all branches. Media file names are content-stable; when a clip changes, bump a `?v=` query from `media.json` or rename (`v-port.2_1920.mp4`) so the immutable cache never serves an old clip.

## 2. Link and create the project (once)
```bash
vercel whoami                         # must be Tarun's account; if not logged in, log it in NIGHT_LOG and stop deploy work (don't try other accounts)
vercel link --yes --project skylark-exim-v4     # creates the project if it doesn't exist
vercel git connect                    # optional: shows PR links in GitHub; auto-deploys stay off because of vercel.json
```

## 3. Preview deploys — by CLI, only at milestones (max ~6 per night)
From the TOP of the stack (the branch containing everything so far):
```bash
npm run build && vercel deploy --yes > .vercel/last-preview.txt   # preview, never --prod
```
Milestones: (1) skeleton + engine + first previews, (2) all film chapters with preview-grade media, (3) business sections complete, (4) first full renders wired, (5) final morning build (+1 spare). If Vercel answers with a rate limit: stop deploying, log the retry time, continue with local `vite preview` + Playwright, and say so in the morning report.
Post every preview URL as a PR comment on the top PR and in NIGHT_LOG.md.

## 4. Open previews for Tarun's phone
Tarun must open previews on his phone without logging in. Show the current setting: `vercel project protection skylark-exim-v4`. Tarun has asked for previews to be open (this pack is his instruction), so run `vercel project protection disable skylark-exim-v4 --sso` once, then verify with `curl -sI <preview-url>` → 200 (not 401). If the CLI lacks the command, use `vercel curl` for your own tests and put "turn off Vercel Authentication for previews: Project → Settings → Deployment Protection" in MORNING_CHECKLIST. The previews carry `X-Robots-Tag: noindex` (Vercel default for previews).

## 5. Test perf on the deployed preview
`PERF_URL=$(cat .vercel/last-preview.txt) npx playwright test tests/scroll-perf.spec.ts` and `npx lhci autorun --collect.url=$PERF_URL` — numbers go into the PR. Localhost numbers alone are not accepted (v3 lesson).

## 6. Production
Never `vercel --prod` and never point a domain. Production happens only after Tarun approves and merges.
