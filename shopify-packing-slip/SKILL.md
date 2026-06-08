---
name: shopify-packing-slip
description: Update Shopify packing slip templates via Playwright browser automation. Use when the user wants to edit, update, preview, or push packing slip changes to any Shopify store.
---

# Shopify Packing Slip Manager

Automates viewing, editing, and deploying packing slip templates to Shopify stores via Playwright browser automation.

## When to Use

Trigger on: "packing slip", "packing slips", "update packing slip", "edit packing slip", "push packing slip", "packing slip template"

## Prerequisites

- Playwright MCP server must be running
- User must be logged into Shopify admin in the Playwright browser (or log in manually when prompted)
- Template file must be prepared locally before pushing

## Store Registry

Always confirm which store before making changes. Known stores:

| Store | Shopify Domain | Local Template Dir |
|-------|---------------|-------------------|
| Holistic Vitalis | holisticvitalis.myshopify.com | `Projects/Clients/Holistic-Vitalis/` |
| Vicelle Naturals | zrwwbj-jq.myshopify.com | `Projects/Clients/Vicelle-Naturals/` |
| Biznomad | biznomad.myshopify.com | `Projects/Clients/Biznomad/` |

## File Naming Convention

Each store directory should contain:
- `packing-slip-current.txt` — The current live template (backup)
- `packing-slip-updated.html` — The pending update to push
- `packing-slip-preview.html` — Browser-viewable preview with sample data and font-size annotations
- `packing-slip-mix-match-snippet.html` — Reusable mix & match bundle snippet (if applicable)

## Workflow

### 1. View Current Template

Read `packing-slip-current.txt` from the store's local directory. If it doesn't exist, pull it from Shopify admin via Playwright:

```
Navigate to: https://admin.shopify.com/store/{store-handle}/settings/shipping/packing_slip_template
```

Extract the editor content via:
```javascript
const cmContent = document.querySelector('.cm-content');
const view = cmContent.cmView.view;
const content = view.state.doc.toString();
```

### 2. Generate Preview

Create `packing-slip-preview.html` with:
- Sample order data using the store's actual products
- Font-size annotation labels (red badges) on every text element
- Toggle button for showing/hiding annotations
- View selector for sections (if template has multiple sections)
- Open in browser for the user to review

### 3. Make Modifications

Edit the template as requested. Common operations:
- Font size adjustments (calculate percentage changes, round to nearest px)
- Layout changes
- Adding/removing sections
- Mix & match bundle callout styling

Save the modified template to `packing-slip-updated.html`.

### 4. Push to Shopify via Playwright

**CRITICAL: This is the exact sequence that works. Do NOT deviate.**

Shopify's packing slip editor uses CodeMirror 6 inside a React app. The React form state only detects changes made through native browser events (keyboard input, clipboard paste). Programmatic CM6 `dispatch()` or JavaScript `click()` events will NOT trigger Shopify's save mechanism.

#### Step-by-step:

1. **Copy template to system clipboard:**
   ```bash
   cat packing-slip-updated.html | pbcopy
   ```

2. **Navigate to the packing slip editor:**
   ```
   https://admin.shopify.com/store/{store-handle}/settings/shipping/packing_slip_template
   ```
   If login page appears, ask user to log in manually in the Playwright browser.

3. **Wait for editor to load** (2 seconds after page load)

4. **Focus the editor:**
   ```javascript
   const editor = page.locator('.cm-content');
   await editor.click();
   ```

5. **Select all and delete existing content:**
   ```javascript
   await page.keyboard.press('Meta+a');
   await page.waitForTimeout(200);
   await page.keyboard.press('Backspace');
   ```

6. **Paste from system clipboard:**
   ```javascript
   await page.keyboard.press('Meta+v');
   await page.waitForTimeout(2000);
   ```

7. **Click Save (use the FIRST Save button — contextual save bar):**
   ```javascript
   const saveBtn = page.locator('button:has-text("Save")').first();
   await saveBtn.click();
   await page.waitForTimeout(3000);
   ```

8. **Verify save succeeded — look for toast notification:**
   ```javascript
   const toasts = Array.from(document.querySelectorAll('[class*="Toast"]'))
     .map(t => t.textContent.trim());
   // Should contain "Packing slip template saved"
   ```

9. **Update local backup:**
   ```bash
   cp packing-slip-updated.html packing-slip-current.txt
   ```

### What Does NOT Work (Lessons Learned)

- **CM6 `view.dispatch()`** — Updates the editor visually but Shopify's React wrapper doesn't detect the change. Save button appears enabled but clicking it does nothing.
- **JavaScript `button.click()`** — Shopify's React event handlers don't fire from synthetic JS click events.
- **`MouseEvent` dispatch** — Same problem as above.
- **`form.submit()`** — Navigates to a 404 page. Shopify doesn't use traditional form submission.
- **Hidden `Submit` button** — Blocked by overlapping elements, not clickable via Playwright.
- **`ClipboardEvent('paste')`** — CM6 accepts it but Shopify's React form state doesn't update.

**Only native keyboard events (Meta+a, Backspace, Meta+v) properly trigger Shopify's change detection.**

## Liquid Variable Gotcha

**CRITICAL:** Shopify packing slips use `line_items_in_shipment`, NOT `line_items`. The `line_items` variable is empty in the packing slip context. Always use:
```liquid
{% for line_item in line_items_in_shipment %}
```
Never use `{% for line_item in line_items %}` — it will render an empty table with no products.

Other order-level variables (`order.name`, `order.total_price`, `shipping_address`, etc.) work normally.

**ALSO:** Line item properties in the shipment context use `prop.first` (name) and `prop.last` (value), NOT `prop.name` / `prop.value`. The `.name`/`.value` syntax only works in notification email templates. Using wrong accessors renders blank colons.

## Safety Rules

- ALWAYS confirm which store before pushing
- ALWAYS save a backup of the current template before overwriting
- ALWAYS verify the save succeeded via toast notification
- NEVER push without user confirmation on live stores
- Test with "Preview template" button in Shopify admin when possible
