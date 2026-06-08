# Stack Selection Guide

## Decision Matrix

| Factor | Vanilla HTML | Astro | Next.js | Shopify Liquid |
|--------|-------------|-------|---------|----------------|
| **Best for** | Landing pages, portfolios | Content sites, blogs, docs | Apps with auth/state/API | E-commerce stores |
| **Interactivity** | Minimal JS | Islands of React/Vue | Full React SPA/SSR | Theme Customizer |
| **Build step** | None | `astro build` | `next build` | Shopify handles |
| **Deploy** | Netlify/any static host | Netlify/Vercel | Vercel | Shopify |
| **Learning curve** | None | Low | Medium | Medium (Liquid) |
| **SEO** | Manual | Built-in | Built-in (SSR) | Built-in |
| **CMS** | Manual | MDX/headless CMS | Headless CMS | Shopify Admin |

## When to Use Each

### Vanilla HTML/CSS/JS
- Single-page marketing or landing page
- Portfolio site
- Client wants to edit HTML directly
- No build tooling needed
- Maximum simplicity

### Astro + Tailwind
- Multi-page content site (blog, docs, marketing)
- Need partial interactivity (React islands)
- SEO-critical pages
- Static-first with optional server rendering
- MDX content authoring

### Next.js + Tailwind
- Dashboard or admin panel
- App with user auth and sessions
- Server-side API routes needed
- Real-time features (WebSocket)
- Complex state management

### Shopify Liquid
- Product pages, collection pages, homepage on Shopify store
- Client manages content via Theme Customizer
- E-commerce with cart, checkout, subscriptions
- Must integrate with Shopify apps (ReCharge, etc.)

## CSS Strategy

| Stack | Recommended CSS |
|-------|----------------|
| Vanilla HTML | Inline `<style>` or single CSS file |
| Astro | Tailwind CSS or scoped `<style>` |
| Next.js | Tailwind CSS or CSS Modules |
| Shopify | Inline styles in Liquid (Theme Customizer friendly) |

## File Structure Patterns

### Vanilla HTML
```
project/
├── index.html
├── styles.css
├── script.js
└── assets/
```

### Astro
```
project/
├── src/
│   ├── pages/
│   ├── components/
│   ├── layouts/
│   └── styles/
├── public/
├── astro.config.mjs
└── tailwind.config.mjs
```

### Next.js
```
project/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── api/
├── components/
├── lib/
├── public/
├── next.config.js
└── tailwind.config.ts
```

### Shopify Theme
```
theme/
├── sections/       ← Custom Liquid sections
├── templates/      ← JSON templates
├── snippets/       ← Reusable Liquid partials
├── assets/         ← CSS/JS/images
└── config/
    └── settings_schema.json
```
