# Design Tokens

## Color System

### Building a Palette from Brand Colors

Given a brand's primary color, generate a full palette:

```
Primary:    brand color (e.g. #2e7d32)
Secondary:  complementary or analogous
Accent:     high-contrast highlight
Neutral:    gray scale (50, 100, 200, ..., 900)
Success:    green (#22c55e)
Warning:    amber (#f59e0b)
Error:      red (#ef4444)
Info:       blue (#3b82f6)
```

### Common Palettes

**Warm Natural** (wellness, organic brands):
```css
--primary: #2e7d32;     /* forest green */
--secondary: #8b6914;   /* warm gold */
--accent: #c75b39;      /* terracotta */
--bg-warm: #faf8f5;     /* warm white */
--bg-cream: #f5f1eb;    /* cream */
--text-primary: #1a1a1a;
--text-secondary: #555555;
```

**Modern Minimal** (tech, SaaS):
```css
--primary: #0f172a;     /* slate 900 */
--secondary: #3b82f6;   /* blue 500 */
--accent: #8b5cf6;      /* violet 500 */
--bg: #ffffff;
--bg-subtle: #f8fafc;   /* slate 50 */
--text-primary: #0f172a;
--text-muted: #64748b;  /* slate 500 */
```

**Bold & Vibrant** (creative, fashion):
```css
--primary: #7c3aed;     /* violet 600 */
--secondary: #ec4899;   /* pink 500 */
--accent: #f59e0b;      /* amber 500 */
--bg: #fafafa;
--text-primary: #18181b;
--text-secondary: #71717a;
```

## Typography

### Font Pairing Patterns

| Style | Heading | Body |
|-------|---------|------|
| Classic | Playfair Display | Inter |
| Modern | Inter | Inter |
| Elegant | Cormorant Garamond | Lato |
| Technical | JetBrains Mono | Inter |
| Warm | Merriweather | Source Sans 3 |

### Type Scale (1.25 ratio)

```css
--text-xs:  0.75rem;   /* 12px */
--text-sm:  0.875rem;  /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg:  1.125rem;  /* 18px */
--text-xl:  1.25rem;   /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
```

## Spacing

### 4px Base Unit

```css
--space-1:  4px;
--space-2:  8px;
--space-3:  12px;
--space-4:  16px;
--space-6:  24px;
--space-8:  32px;
--space-12: 48px;
--space-16: 64px;
--space-24: 96px;
```

### Section Spacing

| Breakpoint | Section padding |
|------------|----------------|
| Mobile (<640px) | 32px top/bottom, 16px sides |
| Tablet (640-1024px) | 48px top/bottom, 24px sides |
| Desktop (>1024px) | 64px top/bottom, auto (max-width container) |

## Border Radius

```css
--radius-sm: 4px;    /* buttons, inputs */
--radius-md: 8px;    /* cards */
--radius-lg: 12px;   /* modals, large cards */
--radius-xl: 16px;   /* hero sections */
--radius-full: 9999px; /* pills, avatars */
```

## Shadows

```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 2px 8px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 4px 16px rgba(0, 0, 0, 0.08);
--shadow-xl: 0 8px 32px rgba(0, 0, 0, 0.1);
```

## Responsive Breakpoints

```css
/* Mobile-first */
@media (min-width: 640px)  { /* sm - tablet */ }
@media (min-width: 768px)  { /* md - tablet landscape */ }
@media (min-width: 1024px) { /* lg - desktop */ }
@media (min-width: 1280px) { /* xl - large desktop */ }
```

## Component Patterns

### Trust Banner
3-column flex, wraps on mobile, emoji icon + bold title + subtext. `gap: 40px` desktop, `gap: 20px` mobile.

### Testimonial Card
Card with shadow, star rating (gold ★), italic quote, author line. Grid layout: `repeat(auto-fit, minmax(280px, 1fr))`.

### Comparison Table
Two columns: green "us" with ✓, gray "them" with ✗. Responsive font scaling on mobile.

### FAQ Accordion
Collapsible content blocks. Use native `<details>/<summary>` for HTML, or Shopify's `collapsible-content` section.

### CTA Section
Centered text + button. High-contrast background. Button with hover transition.
