# Shopify 2.0 Patterns

## Section Anatomy

Every custom section is a `.liquid` file with HTML/Liquid + a `{% schema %}` block:

```liquid
<div class="my-section" style="background: {{ section.settings.bg_color }};">
  <div class="page-width">
    {%- for block in section.blocks -%}
      <div {{ block.shopify_attributes }}>
        {{ block.settings.title }}
      </div>
    {%- endfor -%}
  </div>
</div>

{% schema %}
{
  "name": "My Section",
  "tag": "section",
  "settings": [
    { "type": "color", "id": "bg_color", "label": "Background", "default": "#ffffff" }
  ],
  "blocks": [
    {
      "type": "item",
      "name": "Item",
      "limit": 10,
      "settings": [
        { "type": "text", "id": "title", "label": "Title", "default": "Item" }
      ]
    }
  ],
  "presets": [
    {
      "name": "My Section",
      "blocks": [
        { "type": "item", "settings": { "title": "First item" } }
      ]
    }
  ]
}
{% endschema %}
```

### Schema Setting Types

| Type | Use | Notes |
|------|-----|-------|
| `text` | Short text | Single line |
| `textarea` | Long text | Multi-line |
| `richtext` | HTML content | NO `style` attributes allowed |
| `color` | Color picker | Returns hex string |
| `range` | Numeric slider | Requires `min`, `max`, `step`, `default` |
| `select` | Dropdown | Requires `options` array |
| `checkbox` | Boolean | Returns true/false |
| `image_picker` | Image upload | Returns image object |
| `url` | URL input | For links |

### Richtext Restrictions

Shopify richtext fields accept only semantic HTML. **Forbidden:**
- `style` attributes on any tag
- `class` attributes
- `<div>` tags

**Allowed:** `<p>`, `<strong>`, `<em>`, `<ul>`, `<ol>`, `<li>`, `<a>`, `<br>`

### Block shopify_attributes

Always include `{{ block.shopify_attributes }}` on block wrapper elements. This enables Theme Customizer's click-to-select functionality.

## JSON Template Structure

Templates live at `templates/product.{suffix}.json` (or `collection.{suffix}.json`, etc.).

```json
{
  "sections": {
    "main": {
      "type": "main-product",
      "blocks": {
        "title": { "type": "title", "settings": {} },
        "price": { "type": "price", "settings": {} }
      },
      "block_order": ["title", "price"],
      "settings": {
        "enable_sticky_info": true,
        "gallery_layout": "thumbnail_slider"
      }
    },
    "trust_banner": {
      "type": "trust-banner",
      "settings": { "bg_color": "#f5f1eb" },
      "blocks": {
        "item_1": { "type": "trust_item", "settings": { "title": "Quality" } }
      },
      "block_order": ["item_1"]
    }
  },
  "order": ["main", "trust_banner"]
}
```

### Key Rules

- Section keys in `sections` object are arbitrary IDs (e.g. `"main"`, `"trust_banner"`)
- `type` must match the section filename without `.liquid` (e.g. `"trust-banner"`)
- `block_order` array controls rendering order
- `order` array controls section order on the page

## Common Block Types (Sense Theme)

### main-product blocks
`title`, `rating`, `price`, `variant_picker`, `quantity_selector`, `buy_buttons`, `description`, `collapsible_tab`, `share`, `sku`, `inventory`, `custom_liquid`, `popup`, `icon-with-text`, `complementary`, `text`

### collapsible_tab settings
- `heading` (text) — Tab title
- `icon` (select) — Icon name: `clipboard`, `leaf`, `truck`, `return`, `heart`, `star`, `check_mark`
- `content` (richtext) — Tab body content

### collapsible-content section (FAQ)
Uses `collapsible_row` blocks with: `heading` (text), `icon` (select), `row_content` (richtext)

Settings: `layout` (`none`, `row`, `section`), `heading_alignment`, `color_scheme`, `container_color_scheme`

### image-with-text section
**Uses blocks, NOT section settings for content:**
- Block type `heading` → `settings.heading`
- Block type `text` → `settings.text`, `settings.text_style`
- Block type `button` → `settings.button_label`, `settings.button_link`

Section settings: `height`, `desktop_image_width`, `layout` (`collage`), `content_layout`, `section_color_scheme`, `color_scheme`

### Color Schemes
Sense theme uses `scheme-1` through `scheme-5`. **NOT** `background-1` or `background-2`.

### Gallery Layouts
`stacked`, `columns`, `thumbnail`, `thumbnail_slider`

## Deployment via API

### Push a section file
```
PUT /admin/api/2024-01/themes/{theme_id}/assets.json
{
  "asset": {
    "key": "sections/my-section.liquid",
    "value": "<liquid content>"
  }
}
```

### Push a template
```
PUT /admin/api/2024-01/themes/{theme_id}/assets.json
{
  "asset": {
    "key": "templates/product.custom.json",
    "value": "{\"sections\": {...}, \"order\": [...]}"
  }
}
```

### Assign product to template
```
PUT /admin/api/2024-01/products/{product_id}.json
{
  "product": { "id": product_id, "template_suffix": "custom" }
}
```

## Template Assignment Safety

**Problem:** `template_suffix` on a product applies to ALL themes. If the redesign theme has `product.custom.json` but the live theme doesn't, products will 404 on the live theme.

**Solution:** Always push a fallback template to the live theme before assigning products:

1. Fetch the live theme's current `product.json`
2. Push that content as `product.custom.json` on the live theme
3. Push the redesigned `product.custom.json` on the staging theme
4. Assign products to `template_suffix: "custom"`

Result: Live theme renders products with fallback (unchanged), staging theme renders with redesign.

## Rate Limiting

Add `time.sleep(0.5)` between API calls to avoid Shopify's rate limit (40 requests/minute for private apps).
