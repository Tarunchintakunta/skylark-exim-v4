# MORNING_CHECKLIST.md — for Tarun (about 20 minutes)

1. **Read the morning REPORT** — a comment on the top PR of the stack in github.com/Tarunchintakunta/skylark-exim-v4 (also `NIGHT_LOG.md` on that branch). It lists: preview URL, what's done, which chapters are full-render vs preview-grade, gate results, known issues, merge order.
2. **Open the latest preview URL on your phone and on your laptop.** Scroll the whole story slowly, then fast, then back up. Note any: stutter, grey/black frame, overlapping headline, empty-looking scene, toy-like object, fake-looking person/fish/water, clipping.
3. **Check the film chapters** against this list (one line each in your reply to Claude): 00 table · 09 reefer · 09 port (container landing clear?) · 08 cold store · 07 packing · 06 freezing · 05 lab · 04 grading · 03 peeling · 02 washing · 02 truck · 01 pond · 01 sea + crew.
4. **Check products:** do the tuna / prawn / swordfish look real up close? Swordfish omitted is OK.
5. **Check the words** against what you know is true. Answer the `[CONFIRM]` items (CONTENT.md): "diversified commodities", "coastal communities" vs "commodities", "culture material and solvents", Bangkok separate from Thailand, HOSO/HLSO/PUD expansions, a vector logo, the production domain.
6. **Vercel:** if the preview asked you to log in, turn off Vercel Authentication for previews (Project → Settings → Deployment Protection) or tell Claude to run `vercel project protection disable skylark-exim-v4 --sso`.
7. **Merging:** only you merge. Follow the merge order in the report (bottom of the stack first, "Create a merge commit"). Don't merge PRs labelled `known-issue` until fixed.
8. **Tell Claude the next round:** paste your notes as "v4 review round 1: …". Claude fixes, re-renders previews, and asks again.
