---
name: 3d-website
description: Operating system for designing and building premium 3D animated websites — cinematic scroll-driven scenes, Three.js interaction frameworks, luxury UI/motion systems, and conversion-focused 3D landing pages, with a performance-first launch gate. This skill should be used when the user asks for a 3D website, immersive or cinematic landing page, Three.js/WebGL experience, scroll-driven storytelling site, "agency-quality" redesign, or wants an existing page elevated with 3D/motion.
argument-hint: [what to build or redesign, e.g. "new homepage for biznomad"]
---

# 3D Website Operating System

Eight composable operating modes for premium 3D web work. The verbatim persona prompts
live in [references/prompt_library.md](references/prompt_library.md) — read it, adopt the
relevant persona(s), and execute their scope against the actual project. A ready-to-adapt
single-file starter lives in [assets/threejs-starter.html](assets/threejs-starter.html).

## Mode routing

Match the request to modes; chain them for full builds:

| Request shape | Modes (in order) |
|---|---|
| Full site / "build me a 3D website" / redesign from scratch | 8 → 1 → 3 → 4 → 6 → 5 → 7 |
| Landing page / homepage / campaign page | 6 → 3 → 4 → 7 |
| "Make my existing site cinematic/immersive" | 2 → 4 → 7 |
| Design system / brand feel only | 1 → 3 |
| Implementation planning only | 5 |
| Pre-launch review / "it's slow" | 7 |

Modes: 1 Operating System · 2 Cinematic Experience · 3 UI & Motion System ·
4 Three.js Blueprint · 5 AI Dev Sprint · 6 Converting Landing Page ·
7 Performance & Optimization · 8 Elite Agency (orchestrator).

## Workflow

1. **Brand intake first.** Before any design output, extract the project's real design
   tokens: colors, gradients, fonts, logo treatment, voice. Pull from the live site,
   existing CSS variables, a login/app page, or brand docs — never invent a palette when
   one exists. Confirm the conversion goal (book, buy, sign up) and the working endpoints
   behind each CTA before designing around them.
2. **Read the prompt library** and adopt the persona(s) for the routed modes. Produce the
   design rationale the prompts demand: every scene, animation, and interaction gets a
   one-line purpose. If it has no purpose, cut it.
3. **Build.** Start from `assets/threejs-starter.html` for single-file pages, or apply its
   patterns (import map, lazy init, reduced-motion guard, DPR cap, visibility pause) in a
   framework project. Wire CTAs to verified-working destinations only.
4. **Run the Mode 7 gate before showing anything.** No deliverable ships without passing
   the launch checklist below.
5. **Never overwrite a live page.** New designs land as a sibling artifact (new file,
   `/v2/` path, draft deploy, or branch) until explicitly promoted.

## Non-negotiable engineering rules

- **Reduced motion:** `prefers-reduced-motion: reduce` gets a static, fully-usable page —
  no autoplaying camera or particle churn. Gate the render loop, not just CSS.
- **3D never blocks content:** headline, CTAs, and copy are real DOM rendered before the
  canvas initializes; WebGL failure or blocked CDN must degrade to a styled page, not a
  blank one. Wrap module init in try/catch with a `.no-webgl` fallback class.
- **Performance budget:** cap `devicePixelRatio` at 2 (1.5 on mobile), pause the loop on
  `visibilitychange` and when the canvas scrolls out of view (IntersectionObserver),
  scale particle/geometry counts by viewport width, dispose geometries/materials on
  teardown. Target 60fps desktop / 30fps floor on mid-range mobile.
- **Scroll choreography:** drive camera/scene from a normalized scroll progress value
  (lerped, not raw) so it stays smooth and framework-agnostic. Section reveals via
  IntersectionObserver, not scroll math.
- **Accessibility:** semantic landmarks, focus-visible states, aria-labels on icon
  buttons, contrast ≥ 4.5:1 for text over scenes (use scrims), keyboard-reachable CTAs.
- **Icons are inline SVG** (Lucide-style) — never emoji in UI.
- **SEO/meta:** title, description, OG tags, and JSON-LD survive the 3D treatment; text
  content must exist in DOM for crawlers, not baked into canvas.

## Mode 7 launch checklist

Run before presenting any build:

- [ ] Console clean on load and after full scroll-through
- [ ] LCP element is DOM text/image, not the canvas; no layout shift from canvas mount
- [ ] Reduced-motion pass: page readable and navigable with animations off
- [ ] WebGL-blocked pass: disable the module import — page still renders and converts
- [ ] Mobile viewport (375w): readable type, tappable CTAs, frame rate acceptable, no
      horizontal scroll
- [ ] All CTAs hit verified-working URLs (curl them); tracking events fire
- [ ] Meta/OG/JSON-LD present; images compressed; fonts subset or system-stack fallback

## Deliverable format

Ship: (1) the artifact (file or draft URL), (2) a scene-by-scene rationale table
(element → purpose → trigger), (3) the checklist results, (4) what was deliberately left
out and why. For staged deploys, include the preview URL and the promote command without
executing it.
