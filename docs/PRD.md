# PRD.md — Skylark Exim v4 "Trace it back"

## Goal
A finished, award-level, cinematic scroll-story website for Skylark Exim (seafood exporter, Visakhapatnam) that makes overseas buyers trust the company and send a request for quote. A second site alongside v3, with a completely different story (STORY.md) and look. Repo `Tarunchintakunta/skylark-exim-v4` (private), Vercel project `skylark-exim-v4`.

## Audience
Seafood importers, distributors and buyers abroad (the 16 markets in CONTENT.md §7), on desktop at work and on mid-range Android phones on 4G.

## Success criteria (morning acceptance)
1. The full story plays as ONE continuous 3D camera journey from the dinner table to the dawn boat, then the business sections, with nothing missing, no placeholder, no grey/black frames — on the deployed preview, desktop and phone.
2. Every visual is Blender-built (rendered video/stills) or live Three.js GLB or code/typography. Zero AI media, zero stock.
3. Every fact traces to CONTENT.md; BANNED_CLAIMS test passes.
4. QUALITY_GATES G-SCENE/G-PROD/G-MEDIA/G-SITE pass (or listed as known issues in the morning report with evidence).
5. Feels buttery: 60 fps desktop, no stutter on a mid-range Android at Fast 4G, Lighthouse mobile perf ≥ 90 / a11y ≥ 95.

## Scope
**In:** film chapters 00–01 (13 clips), B1 Now forward (live carton), B2 Products (live 3D), B3 Quality & facility, B4 Markets map, B5 People, B6 RFQ (mailto) + contact + profile PDF, footer, /licenses page, SEO/OG, reduced motion, mobile.
**Out:** CMS, multi-language, backend, analytics/trackers, cookie banner (no cookies set), sound, chat widgets, globe, start screen.

## Functional requirements
- F1 Scroll story with pinned stage; scroll scrubs the clip; captions per STORYBOARD.md; countdown numerals.
- F2 Header: wordmark (home), menu (Story, Products, Quality, Markets, People, Contact), "Request a quote" → B6. Hides during film scroll-down, shows on scroll-up.
- F3 Products: live 3D models (tuna, prawn, swordfish if it passes), full species lists and shrimp forms from CONTENT.md, "Enquire" prefill.
- F4 Markets: relief map + routes drawn by scroll + 16-market list.
- F5 RFQ form → `mailto:info@skylarkexim.com` (subject + body), validation, honeypot, keyboard accessible. Tel links. Profile PDF ≤ 2,300 KB.
- F6 Reduced motion: posters + captions, no scrubbing, no smooth scroll.
- F7 /licenses page rendering docs/LICENSES.md.
- F8 404 page in the same style.

## Non-functional
Performance, weight, accessibility, SEO budgets in TRD §9 and QUALITY_GATES G-SITE. Browsers: Chrome/Edge/Firefox/Safari last 2, iOS Safari 16+, Android Chrome.

## Content
CONTENT.md only. Creative headlines allowed if they contain no claim. Copy lives in `src/config/copy.ts` with `// CONTENT §x` references.

## Deliverables by morning
Repo with stacked PRs (no merges), deployed preview URL(s), NIGHT_LOG.md, PLAN.md, morning REPORT comment on the top PR, docs/renders/ previews + sheets + reviews, MORNING_CHECKLIST answers pending for Tarun.
