---
name: system-showcase
description: Build a premium scroll-animated showcase/pitch site for any Biznomad system, automation stack, or client offering — animated feature breakdowns, behind-the-scenes automation visuals (IP-safe), pricing, guarantee, CTA — deployed to a fresh Netlify site. Use when the user says "build a showcase", "pitch site", "present my system", "scroll presentation", "demo site for [offer/client]", or wants a visual sales page for something Biznomad built.
---

# System Showcase

Turn a working system/offer into a scroll-driven pitch site a prospect can *feel*: pinned scroll-scrubbed flow diagrams, SVG line-draws, live counters, typing scenarios — all real data, zero IP leakage. Reference implementation (built for Boss Cash Cars, July 2026): `assets/template/index.html`, live at bosscashcars-hq.netlify.app.

## Workflow

### 1. Gather REAL data first — never mock
Every number on the page must trace to a real system output (scans, deals, GSC, dashboards). Pull live data via ssh/API before writing HTML. A prospect who checks one number and finds it fake is lost. Curate out garbage rows (e.g. $13 "asking prices" from scraped finance posts).

### 2. Define the section arc
Standard narrative (reorder/trim per audience, keep the spine):
1. **Hero** — "[Client], on autopilot." + LIVE badge + scroll cue
2. **Where you stand** — audit stats, honest, counters
3. **Meet the platform** — browser-mock of the command center (see IP rules)
4. **The core loop** — PINNED scroll-scrubbed flow (the centerpiece; one per page max)
5. **Automation breakdowns ×N** — one section per automation: converging-channels SVG hub, timeline ladder, scenario card with typing
6. **AI edge** — the tools competitors lack (radar sweep, scan bars, real values)
7. **Proof** — real-data table
8. **Pricing** — tiers + performance option
9. **Guarantee** — the risk-reversal
10. **Close** — checklist + CTA

Each automation section gets an **UNDER THE HOOD** strip: `Signal in → Brain decides → Action fires → Everything logged` — shows sophistication without naming tools.

### 3. IP-protection pass (hard rules)
- The platform is **"BizNomad"** — NEVER name the underlying vendor (GoHighLevel/GHL), nor Retell, Twilio, n8n, PostHog, Google Ads internals, or any tooling.
- Show WHAT happens (outcomes, timings), never HOW it's wired (no architecture, no tool logos, no API names).
- Withhold: budgets, bids, CPLs, negative keyword lists, account IDs, other clients' numbers, scripts.
- Verify before ship: `grep -inE "gohighlevel|ghl|retell|twilio|n8n|posthog|zapier|make\.com|openai|anthropic|claude" index.html` → must be empty.
- Other-client social proof: name the brand only if the prospect already knows it (e.g. a buyer of that brand's output); never their internal metrics.

### 4. Build from the template
Copy `assets/template/` → new project dir; rewrite copy/data; keep the engine. Rules baked into the template (keep them):
- Brand tokens: ink `#0a0d13` · panel `#11151f` · border `#232a3d` · red `#e8415a` · gold `#ffb000` · green `#2dd47f` · fg `#dde3f0` · dim `#7d8699`; Unbounded (display) / Archivo (body) / JetBrains Mono (data). Numbers are ALWAYS mono.
- **No emoji anywhere** — inline SVG `<symbol>` icons only (defs block in template).
- GSAP + ScrollTrigger **self-hosted** in `js/` (already in template) — no CDN scripts.
- `.rv` class = reveal-on-scroll default; `html.static .rv` forces final state.
- **`?static` mode is mandatory**: `?static` query param (and `prefers-reduced-motion`) skips all animation JS and CSS-forces final states. This is the QA/screenshot/print path.
- Fixed chrome: top progress bar + right dot-nav with section spy.
- Animation pattern catalog + exact code: `references/animation_patterns.md`.

### 5. QA before showing anyone
1. Serve locally: `python3 -m http.server 8899 --directory <dir>`.
2. **vh trap**: headless Chrome `--window-size=1440,6000` makes `100vh` sections giant — do NOT full-page screenshot that way. Use the gstack browse binary (`$HOME/.claude/skills/gstack/browse/dist/browse`): `goto` the `?static` URL → screenshot (it captures full page at real viewport).
3. Animated-mode sanity: `browse js "JSON.stringify({gsap:typeof gsap,triggers:ScrollTrigger.getAll().length})"` — expect gsap `object` + a healthy trigger count; then scroll mid-way into the pinned section and screenshot to confirm partial state (line half-drawn, early nodes lit).
4. Read the screenshots. Fix anything off BEFORE deploy (premium-from-first-deploy rule).

### 6. Deploy — fresh Netlify site, never over an existing one
```bash
netlify api createSite --data '{"name":"<client>-hq"}'          # returns id (name often ignored)
netlify api updateSite --data '{"site_id":"<id>","body":{"name":"<client>-hq"}}'   # rename MUST nest under "body"
netlify deploy --prod --dir=. --site=<id>
curl -s -o /dev/null -w "%{http_code}" https://<name>.netlify.app/   # expect 200
```
Then repeat QA step 3 against the live URL.

### 7. Handoff
- `open` the live URL for the owner.
- Owner reviews before the client ever sees it (publish gate).
- Report: URL, section list, data sources used, and the IP-scan result.

## Companion deliverables (optional, same content)
- Slide deck: standalone HTML slides w/ arrow-key nav + `@media print` (1280×720 pages) → headless Chrome `--print-to-pdf`.
- Proposal PDF: light "paper" HTML → `--print-to-pdf`. Keep copy in sync with the site.
