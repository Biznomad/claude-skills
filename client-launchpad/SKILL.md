---
name: client-launchpad
description: Automated client onboarding for Biznomad agency. Generates a luxury e-commerce website and client dashboard from brand assets (logo, product photos). Use when onboarding a new client, building a client website, creating a client dashboard, launching a new brand, or when the user says "new client", "launch client", "client launchpad", "build website for client", or "onboard client". Handles design system generation, website build, dashboard with packages/pricing, password gate, Netlify deployment, and mobile optimization.
---

# Client Launchpad

Automates the Biznomad agency client onboarding workflow: brand assets in, luxury e-commerce website + client dashboard out, deployed to Netlify.

## Workflow

### Step 1: Asset Discovery

Scan the provided folder for brand assets. Catalog everything found:

- **Logos** — PNG, JPG, SVG, WebP
- **Product photos** — hero shots, lifestyle, flatlays, detail crops
- **Videos** — MP4, WebM for hero backgrounds
- **Brand documents** — style guides, mood boards, PDFs

List each asset with a short description. Identify which images work best for: hero background, product grid, about section, testimonials.

### Step 2: Client Config

Gather from the user (ask for anything missing):

| Field | Example | Required |
|-------|---------|----------|
| Brand name | "DLluxe Scrubs" | Yes |
| Tagline | "Premium Medical Apparel" | Yes |
| Product categories | scrubs, socks, accessories | Yes |
| Color direction | luxury, playful, medical, earth tones | Yes |
| Package pricing overrides | default or custom | No |
| Dashboard password | client-chosen password | Yes |
| Phone number (SMS) | +1-555-123-4567 | Yes |
| Calendar booking link | calendly.com/biznomad | Yes |
| Biznomad logo path | Use `assets/biznomad-logo.jpg` from this skill | Auto |

### Step 3: Design System Generation

Run the UI/UX Pro Max design system generator to create a cohesive design language:

```bash
python3 ~/.claude/skills/ui-ux-pro-max/scripts/search.py "<brand keywords>" --design-system -p "<Brand Name>"
```

Extract and apply:
- **Primary, secondary, accent colors** with dark/light variants
- **Typography** — heading + body font pairing
- **Style direction** — glassmorphism, minimalist, editorial, etc.
- **CSS custom properties** for theming both site and dashboard

### Step 4: Website Build

Generate a single-page static HTML/CSS/JS luxury e-commerce site. Use the `document-skills:frontend-design` skill for production-grade quality.

See `references/website-template.md` for the complete section-by-section structure. Required sections:

1. **Preloader** — branded loading animation
2. **Announcement bar** — sliding ticker with 5+ rotating messages
3. **Navigation** — sticky glass nav with logo, links, cart icon
4. **Hero** — cinematic full-viewport section with product image grid background
5. **Product collection** — grid with color swatches, hover zoom, quick-add buttons
6. **Product detail** — mock PDP with image gallery, swatches, sizes, quantity, add-to-cart, reviews
7. **Brand story** — editorial split-layout with parallax
8. **Accessories** — secondary products showcase
9. **Trust features** — SVG icon grid (free shipping, quality, returns, support)
10. **Testimonials** — auto-rotating carousel with star ratings
11. **Newsletter** — email capture with incentive
12. **Footer** — social links, nav links, payment icons, Biznomad powered-by

All sections must include:
- Scroll reveal animations (IntersectionObserver)
- Mobile responsive design (breakpoints: 1024px, 768px, 480px)
- CSS custom properties for theming
- Semantic HTML

### Step 5: Dashboard Build

Generate a dark-mode client portal. See `references/dashboard-template.md` for full structure. Required features:

1. **Password gate** — SHA-256 hashed, sessionStorage persistence
2. **Sidebar** — Biznomad logo, nav links, collapse on mobile
3. **Website preview banner** — screenshot/link to live site
4. **Stats row** — project status, website status, speed to launch, packages selected, investment tracker
5. **Project overview** — timeline tracker with milestones
6. **Website packages** — 4 tiers (see `references/packages.md`)
7. **Maintenance plans** — 3 tiers with unlimited revisions
8. **Marketing packages** — 3 tiers
9. **Biznomad Platform** — CRM, Automations, Funnels, Booking, Reputation, Unified Inbox (FREE with marketing)
10. **Add-on services** — grid of extras
11. **Trust banners** — payment method icons, guarantees
12. **Interactive selection** — click-to-select packages, toast notifications, running total
13. **Mobile menu** — hamburger with slide-out drawer
14. **Action buttons** — "Schedule a Call" (calendar link), "Message Us" (sms: link)
15. **Footer** — Powered by Biznomad

Hash the dashboard password:
```bash
bash ~/.claude/skills/client-launchpad/scripts/hash-password.sh "<password>"
```

### Step 6: Deployment

Deploy both sites to Netlify:

```bash
# Website
bash ~/.claude/skills/client-launchpad/scripts/deploy.sh "<brand-slug>" "/path/to/website"

# Dashboard
bash ~/.claude/skills/client-launchpad/scripts/deploy.sh "<brand-slug>-dashboard" "/path/to/dashboard"
```

After deployment, verify both URLs are live and update the dashboard's website preview link to point to the production website URL.

### Step 7: Memory

Save the new client to the user's memory index. Add an entry with:
- Client name and directory path
- Shopify store (if applicable)
- Website URL (Netlify)
- Dashboard URL (Netlify)
- Status: Active

## Important Notes

- **Always** invoke `document-skills:frontend-design` for website quality — avoid generic AI aesthetics
- **Always** invoke `ui-ux-pro-max` for design system generation
- Website packages emphasize **SPEED TO MARKET** (3-7 day delivery)
- All pricing in `references/packages.md` is the default — configurable per client
- Dashboard password uses SHA-256 hash: `echo -n "password" | shasum -a 256 | cut -d ' ' -f1`
- Biznomad Platform features are **always FREE** with any marketing package
- Mobile optimization is **mandatory** for both sites — test at 375px width
- The Biznomad logo is at `~/.claude/skills/client-launchpad/assets/biznomad-logo.jpg`
- Deploy to **Netlify** (never Surge) — all projects going forward
- Keep client data isolated — never mix assets, keys, or credentials between clients

## Resources

### scripts/
- `deploy.sh` — Deploys a directory to Netlify as a new site
- `hash-password.sh` — Generates SHA-256 hash for dashboard passwords

### references/
- `website-template.md` — Complete website HTML structure patterns and CSS/JS reference
- `dashboard-template.md` — Complete dashboard HTML structure patterns and interactive JS
- `packages.md` — Default Biznomad package pricing, features, and platform details

### assets/
- `biznomad-logo.jpg` — Biznomad agency logo for dashboards and footers
