---
name: shopify-plus-expert
description: Complete Shopify Plus development and design expert. Builds distinctive themes (Liquid, OS 2.0, Theme DNA), develops custom apps (OAuth, webhooks, App Bridge), implements Storefront/Admin API integrations, creates checkout extensions and Shopify Functions, configures subscriptions and selling plans, and optimizes performance. Use when building Shopify themes, creating storefronts, developing apps, customizing checkout, working with Liquid templates, GraphQL APIs, Hydrogen, Polaris, subscription billing, or any Shopify Plus features. Merged from shopify-theme-design + shopify-expert + shopify-developer.
---

# Shopify Plus Expert

Senior Shopify Plus developer and designer. Combines distinctive theme design, full-stack app development, headless commerce, and Plus-exclusive features (checkout extensibility, B2B, Flow, Scripts→Functions).

## Store Context

- **Store:** biznomad.myshopify.com (Shopify Plus)
- **Access Token:** stored in VPS credentials (`SHOPIFY_ACCESS_TOKEN`)
- **Client ID:** ce7b70e29f174b55f15dc8723a7b9794
- **API Version:** 2026-01
- **Products:** Dental AI plans ($497, $997, $1,997/mo) with subscription selling plans

## Core Workflow

1. **Requirements** — Theme, app, headless, or checkout customization?
2. **Architecture** — Scaffold with `shopify theme init` or `shopify app create`; configure schemas
3. **Design** — Run Vibe Discovery for themes (see Theme Design section); build from Theme DNA
4. **Implement** — Liquid templates, GraphQL queries, app features, checkout extensions
5. **Validate** — `shopify theme check` for Liquid; `shopify app dev` for apps; test in sandbox
6. **Deploy** — `shopify theme push` or `shopify app deploy`; monitor error logs

## Quick Reference

| Item | Value |
|------|-------|
| API version | `2026-01` (stable) |
| GraphQL Admin | `POST https://biznomad.myshopify.com/admin/api/2026-01/graphql.json` |
| Storefront API | `POST https://biznomad.myshopify.com/api/2026-01/graphql.json` |
| Ajax API | `/cart.js`, `/cart/add.js`, `/cart/change.js` |
| CLI | `npm install -g @shopify/cli` |
| Theme dev | `shopify theme dev --store biznomad.myshopify.com` |
| Docs | [shopify.dev](https://shopify.dev) |

## Reference Files

Load the reference that matches your task:

### Liquid & Themes
| Reference | When to Load |
|-----------|-------------|
| `references/liquid-syntax.md` | Writing/debugging `.liquid` files, tags, control flow |
| `references/liquid-filters.md` | All filter categories with examples |
| `references/liquid-objects.md` | Product, collection, cart, customer, global objects |
| `references/liquid-templating.md` | Complete Liquid templating patterns |
| `references/theme-development.md` | OS 2.0 architecture, sections, blocks, JSON templates, settings |

### APIs
| Reference | When to Load |
|-----------|-------------|
| `references/api-admin.md` | GraphQL Admin API, REST (legacy), OAuth, webhooks, rate limits |
| `references/api-storefront.md` | Storefront API, Ajax API, cart operations |
| `references/storefront-api.md` | Headless commerce, Hydrogen, custom frontends |

### Apps & Extensions
| Reference | When to Load |
|-----------|-------------|
| `references/app-development.md` | Shopify CLI, extensions, Polaris, App Bridge |
| `references/checkout-customization.md` | Checkout UI extensions, Shopify Functions, Plus checkout |
| `references/functions.md` | Shopify Functions (replacing Scripts), Rust/JS targets |
| `references/hydrogen.md` | Hydrogen framework, React Router 7, headless storefronts |

### Operations
| Reference | When to Load |
|-----------|-------------|
| `references/performance.md` | Core Web Vitals, asset optimization, caching |
| `references/performance-optimization.md` | Theme speed, image optimization |
| `references/debugging.md` | Liquid errors, API debugging, common issues |

## Theme Design: Vibe Discovery (Do First for Themes)

Before writing theme code, run Vibe Discovery to generate a UNIQUE aesthetic:

1. **Brand Assets Check** — Ask for logo/colors, extract palette
2. **Vibe Questions:**
   - What adjective would your customer use for your store? (3 words)
   - Show me a non-e-commerce website/image that has the vibe you want
   - If your store were a physical space, what would it look and smell like?
3. **Generate Theme DNA:**
   - Color system (primary, secondary, accent, neutral, semantic)
   - Typography pairing (display + body)
   - Spacing rhythm and border radius scale
   - Signature interactions (hover, scroll, transitions)
   - Photography style guide
4. **Apply to every template** — Theme DNA drives all design decisions

### Anti-Slop Mandate
Every theme must be unmistakable. Avoid:
- Dawn-clone minimal aesthetic
- Stock photo energy
- Feature bloat and overwhelming settings
- "That's clearly Shopify" tells

## Shopify Plus Exclusive Features

- **Checkout Extensibility** — Custom checkout UI with React extensions
- **B2B** — Company accounts, custom pricing, payment terms
- **Flow** — Visual workflow automation (triggers → conditions → actions)
- **Scripts → Functions** — Custom pricing, shipping, payment logic
- **Launchpad** — Scheduled sales, theme changes, scripts
- **Multipass** — SSO customer login
- **Wholesale Channel** — Separate storefront for wholesale
- **Unlimited Staff Accounts** — For team/agent access

## Subscription Billing (Current Setup)

Selling Plan Group: "Dental AI Monthly" (ID: gid://shopify/SellingPlanGroup/1172930648)
- Plan: "Monthly - 7 Day Free Trial" (ID: gid://shopify/SellingPlan/1916338264)
- Pricing: $0 first cycle (trial), full price after cycle 1
- Products attached: all 3 dental plans

Checkout URLs:
- Starter $497: `https://biznomad.myshopify.com/cart/43920738123864:1`
- Growth $997: `https://biznomad.myshopify.com/cart/43920738680920:1`
- Enterprise $1,997: `https://biznomad.myshopify.com/cart/43920739336280:1`
