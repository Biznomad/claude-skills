---
name: biznomad-website-builder
description: Build, redesign, and deploy websites across any stack — static HTML, Next.js, Astro, or Shopify Liquid themes. Handles design systems, brand-aware layouts, component architecture, and deployment pipelines (Netlify, Vercel, Shopify API). Use when asked to build a website, redesign a site, create a landing page, build a web app, create Shopify sections/templates, or deploy web projects. Triggers on requests like "build me a website", "redesign this page", "create a landing page", "build a Shopify theme", "deploy to Netlify".
---

# Website Builder

## Workflow

### 1. Assess the Project

Determine project type and select stack:

| Signal | Stack | Deploy |
|--------|-------|--------|
| Marketing site, portfolio, simple pages | Vanilla HTML/CSS/JS or Astro | Netlify |
| Dynamic app with auth, API, database | Next.js + Tailwind | Vercel |
| Shopify store pages (product, collection, homepage) | Liquid + JSON templates | Shopify API |
| Content-heavy blog/docs | Astro + MDX | Netlify |

For detailed stack selection criteria, see `references/stack_guide.md`.

### 2. Establish Design System

Before writing any component, define design tokens:

```
Colors:    primary, secondary, accent, neutral (50-900), success, error
Typography: heading font, body font, scale (xs through 4xl)
Spacing:   4px base unit (4, 8, 12, 16, 24, 32, 48, 64)
Radius:    sm (4px), md (8px), lg (12px), full
Shadows:   sm, md, lg
```

Apply brand assets (logo, colors, fonts) consistently across all components. For palette construction patterns, see `references/design_tokens.md`. For wellness/e-commerce design inspiration (Serene Herbs, Magic Mind style), see `references/design_inspiration.md`.

### 3. Build Components

**Static sites**: Build section-by-section, mobile-first. Each section is self-contained with its own styles.

**React/Next.js apps**: Component-first architecture. Build atoms → molecules → organisms → pages.

**Shopify themes**: Build as Liquid sections with `{% schema %}` blocks for Theme Customizer editability. For Shopify-specific patterns, gotchas, and deployment, see `references/shopify_2_0.md`.

### 4. Deploy

**Netlify** (static sites):
```bash
npx netlify-cli deploy --prod --dir=./dist
```

**Shopify** (Liquid sections + JSON templates):
Use bundled scripts to push via Admin API:
- `scripts/deploy_shopify_section.py` — push `.liquid` section files
- `scripts/deploy_shopify_template.py` — push JSON template + assign products

**Vercel** (Next.js):
```bash
npx vercel --prod
```

For deployment details and safety patterns, see `references/deployment.md`.

## Shopify Quick Reference

Shopify is the most error-prone stack. Key gotchas:

1. **Block types** — Use theme's actual block type names (e.g. `title` not `@app/title`)
2. **Richtext fields** — No `style` attributes on HTML tags; only semantic HTML
3. **Color schemes** — Named `scheme-1` through `scheme-5` (not `background-1`)
4. **image-with-text** — Content uses blocks (heading, text, button), NOT section-level settings
5. **template_suffix safety** — Changing suffix affects ALL themes; always push a fallback template to the live theme first
6. **Rate limiting** — Add `time.sleep(0.5)` between API calls

Full Shopify reference with examples: `references/shopify_2_0.md`
