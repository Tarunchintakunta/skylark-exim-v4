# TRD.md — technical requirements

## 1. Stack (install latest within these majors; verify on npm when you start)
Vite 7/8 · React 19 · TypeScript (create-vite default, strict) · three r18x · @react-three/fiber 9 · @react-three/drei 10 · gsap 3.13+ (ScrollTrigger, SplitText — all plugins free) + @gsap/react · lenis 1.3 · zod (form validation) · @playwright/test · @lhci/cli · axe-core/@axe-core/playwright · @gltf-transform/cli 4 (npx in scripts) · simple-git-hooks + lint-staged · eslint + prettier.
No jQuery, no CDN scripts, no analytics, no UI kits.

## 2. Architecture
- One page (`/`) + `/licenses` + 404. Static build, Vercel.
- **One clock:** `gsap.ticker` drives Lenis (`lenis.raf(t*1000)`), ScrollTrigger (`lenis.on('scroll', ScrollTrigger.update)`), the video scrubber and R3F (`frameloop="demand"`, `invalidate()` from the ticker only while a 3D section is active). `gsap.ticker.lagSmoothing(0)`. No other rAF loops.
- Lenis desktop: `{ autoRaf:false, lerp:0.09, smoothWheel:true }`; touch devices: native scroll (`syncTouch:false`), `ScrollTrigger.config({ ignoreMobileResize:true })`.
- **Stage:** one fixed full-screen layer holding the video pool (3 `<video>` elements) + poster `<img>` + one transparent R3F `<Canvas>` (mounted lazily for B1/B2 only). Chapters are spacer divs with ScrollTriggers. No per-frame React state; progress lives in a mutable store read by refs.
- Copy, chapters, media ids, mobile object-positions in data files: `src/config/{chapters,copy,media,products,markets,map}.ts`; `src/config/media.json` lists every concrete media path (generated at build by a small `scripts/gen-media-manifest.mjs` you write from chapters.ts × tiers) for `check-media-refs.mjs`.

## 3. Folder structure
```
docs/ (this pack + renders/ reviews/ LICENSES.md)  assets-src/ (git-ignored: blender/ lib/ render/ video/ scans/ models/)
public/ media/ models/ fonts/ og/ docs/ robots.txt sitemap.xml favicon.svg
scripts/ (from the pack)  blender/ (from the pack)
src/ main.tsx App.tsx  config/  engine/{ticker,scrollStore,lenis}.ts  film/{Stage,VideoPool,Chapter,Countdown,Caption}.tsx
     three/{CanvasRoot,HeroCarton,ProductStage}.tsx  sections/{NowForward,Products,Quality,Markets,People,Quote,Footer}.tsx
     ui/{Header,Menu,Loader,StickyRfq}.tsx  styles/{tokens,global,type}.css  a11y/
tests/ smoke content one-headline chapters-media weight scroll-perf a11y .spec.ts  lighthouserc.json  vercel.json  .github/
```

## 4. Chapter config
```ts
interface ChapterDef { id: string; clip?: string; vh: number; mobileVh?: number; countdown?: string;
  eyebrow?: string; headline: string; line?: string; source: string /* CONTENT ref */;
  typeZone: 'tl'|'tr'|'l'|'r'|'top'|'bottom'; objectPosition: string; alt: string; }
```

## 5. Media rules
- Clips: H.264 High, 24 fps, GOP 6 (`-g 6 -keyint_min 6 -sc_threshold 0`), `-bf 0`, `+faststart`, no audio, tiers 1920 / 1280 / 960 wide, **each file ≤ 2,250 KB** (`scripts/encode-clips.sh`). Posters WebP first + last frame (`scripts/make-posters.sh`).
- Tier choice: viewport CSS width × DPR → ≥ 1600 → 1920; ≥ 1000 → 1280; else 960. `navigator.connection.saveData` or effectiveType ≤ 3g → 960. Decided once at load (and on large resize), never per frame.
- **No frame-image sequences** (v3 shipped ~2,900 images / 80–99 MB and stuttered). No GIF. No video over 2,250 KB.
- GLB ≤ 500 KB each, meshopt + WebP (`scripts/optimize-glb.sh`), loaded with drei `useGLTF` + MeshoptDecoder; preloaded when the previous section is active.
- Fonts: self-hosted WOFF2 subsets, 2 preloads max.
- Images: WebP, explicit width/height, `decoding="async"`, lazy below the fold, `fetchpriority="high"` only on the first poster.

## 6. Video engine (the smoothness core)
- **Pool of 3** `<video muted playsinline preload="auto" disablepictureinpicture>`: prev / current / next. Nothing is requested before the user's first scroll/touch/key (the first poster carries the LCP). On first scroll: attach current (v-table) then next. Thereafter on every chapter change re-assign: keep prev, current, next attached; `removeAttribute('src'); load()` anything else.
- Prefetch next as soon as current fires `canplaythrough` (not at 50 %, v3's bug). Also warm the next *poster* (img decode) at chapter start.
- Seeking: per tick `target = progress × (duration − 1/24)`; if `!video.seeking` and |target − currentTime| > 1/48 → `fastSeek` where supported else `currentTime = target`; else store pending and apply on `seeked`. Only seek inside a buffered range; if the target is not buffered, hold the last good frame (never blank) and count a stall.
- Joins are shared frames: at the boundary swap the visible element only after the incoming video has rendered its first frame (`requestVideoFrameCallback` or `seeked` + `readyState ≥ 2`); the outgoing element stays visible until then. Scrolling back up: incoming prev shows its `_end` poster until its last frame is decoded. → no grey frames either direction.
- iOS Low Power / decode failure: if `readyState < 2` 1.5 s after attach, fall back to poster crossfades for that clip only.
- Publish metrics for tests: `window.__v4 = { stalls, seeks, maxSeekMs, attached: string[], tier }`.

## 7. 3D engine
- One `<Canvas dpr={[1, 1.75]} gl={{ antialias:false, powerPreference:'high-performance', stencil:false, alpha:true }} frameloop="demand">`, mounted when B1 is ≤ 1 viewport away, unmounted ≥ 2 viewports after B2. Mobile dpr 1–1.5, no shadows.
- Lighting: small 1K CC0 studio HDRI (Poly Haven) as environment, ACES or AgX tone mapping matched to renders. Products turn with scroll (no drag on mobile). The DOM giant species name sits UNDER the transparent canvas (Zoi layering).

## 8. Typography & motion
Fraunces + Hanken Grotesk (STORY.md §6). SplitText for headlines (lines/words; revert on resize); `−18 °C` inside a nowrap span excluded from splitting. Animate only transform/opacity; `will-change` only on the active caption and the stage. No `filter` animations.

## 9. Budgets (fail CI if exceeded)
| Metric | Limit |
|---|---|
| Initial transfer (before first scroll) | ≤ 3 MB desktop, ≤ 1.5 MB mobile |
| JS initial (gzip) | ≤ 200 KB; three/R3F in a lazy chunk |
| Full scroll media | ≤ 32 MB desktop (1920), ≤ 22 MB (1280), ≤ 14 MB mobile (960) |
| Long tasks during scripted scroll (desktop) | 0 > 50 ms |
| rAF p95 | ≤ 20 ms desktop |
| Video stalls | 0 desktop; ≤ 2 mobile emulation (4× CPU, Fast 4G) |
| Lighthouse mobile (deployed preview) | perf ≥ 90, a11y ≥ 95, BP ≥ 95, SEO ≥ 95 |
| LCP / CLS / TBT mobile | < 2.5 s / < 0.05 / < 200 ms |

## 10. Accessibility
Reduced motion (QUALITY_GATES G-SITE-8), skip links (to main, to #quote), focus rings, semantic headings (one h1 = "Trace it back."), alt text per STORYBOARD, captions also in DOM text for screen readers, form labels/errors, colour contrast per STORY.md.

## 11. SEO
Title "Skylark Exim — Seafood exporter, Visakhapatnam | Shrimps & marine fish"; description from C1; canonical (Vercel URL until the domain is decided — `[CONFIRM]`); OG/Twitter 1200×630 Blender still; JSON-LD Organization (name, email, telephone ×2, address Sheela Nagar, Visakhapatnam, Andhra Pradesh, IN); robots.txt allows all on production, `noindex` header on previews; sitemap.

## 12. RFQ
Client-only. zod schema; on submit build `mailto:info@skylarkexim.com?subject=…&body=…` (encodeURIComponent, body ≤ 1,800 chars, truncate message with "…"), `window.location.href = mailto`. Show the honest fallback message. Honeypot filled → do nothing. No fake API, no "Thank you, we received it".

## 13. Tests (all run in CI on PRs; perf/Lighthouse also run against the deployed preview URL at milestones)
- smoke: loads, header links land, RFQ validation + mailto composition, product prefill.
- content: BANNED_CLAIMS (visible text), every caption equals copy.ts.
- one-headline: G-SITE-2 sampling at 6 widths.
- chapters-media: G-SITE-4 screenshots down + up, luma/stddev check; `node scripts/check-media-refs.mjs`.
- weight: CDP transferred bytes initial + full scroll, per tier.
- scroll-perf: `PERF_URL=<preview>` — long tasks, rAF, `window.__v4.stalls`, desktop + mobile emulation with CDP `Network.emulateNetworkConditions` (Fast 4G: 9 Mbps down, 1.5 Mbps up, 170 ms RTT) and `Emulation.setCPUThrottlingRate {rate:4}`.
- a11y: axe on load, B2, B6, reduced-motion run.
- Lighthouse CI: `lhci autorun --collect.url=$PREVIEW_URL` (3 runs, mobile), assertions per §9.

## 14. CI
`.github/workflows/ci.yml` on pull_request: npm ci → typecheck → lint → build → check-media-refs → Playwright (smoke, content, one-headline, chapters-media, weight, a11y) against `vite preview` → Lighthouse CI on `dist` (gate) → upload reports. Perf on the deployed preview is run by Claude locally with `PERF_URL` and pasted into the PR.
