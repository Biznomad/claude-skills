# Design Inspiration — Wellness E-commerce

Patterns extracted from high-converting wellness/supplement Shopify stores.

## Visual Style: Clean Wellness

**Characteristics:**
- High whitespace, minimal decoration
- Earthy color palette with one bold accent
- Sans-serif typography (Inter, Roboto)
- Product photography as hero content
- Trust elements integrated naturally (not cluttered)

## Color Palettes

### Earthy Wellness (Serene Herbs style)
```css
--primary: #1b4a26;        /* deep forest green */
--accent: #d7fd41;         /* electric lime (CTA) */
--bg-primary: #ffffff;
--bg-warm: #f9f4ea;        /* warm cream */
--bg-dark: #121212;        /* dark sections */
--text-primary: #121212;
--text-muted: #666666;
```

### Teal Performance (Magic Mind style)
```css
--primary: #04a188;        /* teal (CTA buttons) */
--bg-primary: #ffffff;
--bg-subtle: #efefef;      /* light gray sections */
--nav-bg: #1c1b1b;         /* dark navigation */
--text-primary: #1c1b1b;
--text-muted: #6a6a6a;
--error: #f94c43;
```

## Page Structure (Top to Bottom)

### Typical Wellness PDP
1. **Sticky announcement bar** — shipping offer, sale countdown
2. **Product hero** — sticky info panel + image gallery (thumbnail slider)
3. **Trust banner** — 3 items: quality, shipping, key benefit
4. **Benefits grid** — 3-6 items, emoji icons, clean cards
5. **"What to Expect" timeline** — week-by-week results
6. **Educational section** — "What is [product]?" with image
7. **Testimonials** — 3 cards, star ratings, real names
8. **Comparison table** — "Us vs Them" with checkmarks
9. **FAQ accordion** — 5-7 collapsible questions
10. **Disclaimer** — FDA/supplement disclaimer
11. **Related products** — 4-product carousel

### Typical Wellness Homepage
1. **Hero banner** — full-width image, headline, CTA
2. **Featured collection** — 3-4 product cards
3. **Brand story** — image + text split
4. **Social proof** — review count, press logos, testimonials
5. **Benefits overview** — icon grid, 6 items
6. **Newsletter** — email capture with incentive
7. **Footer** — links, social, legal

## Component Patterns

### Product Cards
```css
/* Zero-padding, left-aligned, subtle shadow on hover */
.product-card {
  border-radius: 0;
  text-align: left;
  transition: box-shadow 0.3s ease;
}
.product-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}
```

### CTA Buttons
```css
/* Rounded, bold, single accent color */
.btn-primary {
  background: var(--primary);
  color: white;
  border-radius: 6px;
  padding: 14px 28px;
  font-weight: 700;
  border: none;
  transition: opacity 0.2s;
}
.btn-primary:hover { opacity: 0.9; }
```

### Trust Banner
3-column flex, centered, cream/warm background. Each item: emoji/icon → bold title → subtext.

### Testimonial Cards
White cards on warm background, star ratings in gold, italic quotes, author dash-prefixed.

### Comparison Table
Green column (us) with checkmarks, gray column (them) with X marks. Clean borders, responsive font scaling.

## Typography Patterns

| Element | Size | Weight | Style |
|---------|------|--------|-------|
| Hero headline | 2.5-3rem | 700 | Tight line-height (1.1) |
| Section heading | 1.6rem | 700 | Centered |
| Body text | 0.95rem | 400 | 1.5-1.6 line-height |
| Button text | 0.9rem | 700 | Uppercase optional |
| Caption/meta | 0.82rem | 400 | Muted color |

## Spacing

| Context | Mobile | Desktop |
|---------|--------|---------|
| Section padding | 32px 16px | 64px 0 |
| Card gap | 16px | 24px |
| Trust banner gap | 20px | 40px |
| Content max-width | 100% | 1000px |

## Mobile Patterns

- Grid collapses to single column at 600px
- Trust banner wraps with tighter gaps
- Navigation becomes hamburger/drawer
- Images full-width, product info stacks below
- Font sizes reduce by ~0.1rem
- Touch targets minimum 44px
