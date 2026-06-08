# Deployment Patterns

## Netlify (Static Sites)

### CLI Deploy
```bash
# Install
npm install -g netlify-cli

# Deploy (creates new site if needed)
netlify deploy --prod --dir=./dist

# With build command
netlify deploy --prod --build
```

### netlify.toml
```toml
[build]
  publish = "dist"
  command = "npm run build"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### Environment Variables
Set via Netlify UI (Site settings → Environment variables) or CLI:
```bash
netlify env:set API_KEY "value"
```

## Shopify API Deployment

### Authentication
```python
SHOP_DOMAIN = "store.myshopify.com"
ACCESS_TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]
API_VERSION = "2024-01"
BASE_URL = f"https://{SHOP_DOMAIN}/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json",
}
```

### Deploy Workflow (Safe)

1. **Work on unpublished theme** — never modify the live theme directly
2. **Push custom sections** via `PUT /themes/{id}/assets.json`
3. **Push JSON templates** to staging theme
4. **Push fallback templates** to live theme (safety net)
5. **Assign products** to new template suffix
6. **Validate** all assets exist, preview URLs work
7. **Publish** staging theme only after manual review

### Bundled Scripts

**`scripts/deploy_shopify_section.py`**
Reads `.liquid` files from a directory and pushes them to a Shopify theme via the Admin API.

Usage: Set environment variables `SHOPIFY_DOMAIN`, `SHOPIFY_TOKEN`, `SHOPIFY_THEME_ID`, then run with path to sections directory.

**`scripts/deploy_shopify_template.py`**
Pushes a JSON template file to a theme and optionally assigns products.

Usage: Set environment variables, provide template path and optional product IDs.

### Theme Discovery
```python
def find_theme_by_name(name):
    resp = requests.get(f"{BASE_URL}/themes.json", headers=HEADERS)
    for t in resp.json()["themes"]:
        if t["name"] == name:
            return t["id"]
    return None
```

## Vercel (Next.js)

### CLI Deploy
```bash
# Install
npm install -g vercel

# Deploy
vercel --prod

# With environment variables
vercel env add NEXT_PUBLIC_API_URL
```

### vercel.json (optional)
```json
{
  "framework": "nextjs",
  "buildCommand": "next build",
  "outputDirectory": ".next"
}
```

## Pre-Deploy Checklist

- [ ] All pages render without errors
- [ ] Mobile responsive (test at 360px, 768px, 1024px)
- [ ] Images optimized (WebP where possible)
- [ ] Meta tags and OG images set
- [ ] Favicon configured
- [ ] SSL/HTTPS working
- [ ] Environment variables set (not hardcoded)
- [ ] Error pages (404, 500) configured
- [ ] Analytics/tracking pixels added
- [ ] Performance: Lighthouse score > 80
