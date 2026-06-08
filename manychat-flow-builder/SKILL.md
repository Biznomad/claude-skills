---
name: manychat-flow-builder
description: |-
  Automate ManyChat DM funnel creation via API and browser. Build support and sales ecosystems, quiz flows, cart recovery, and retention sequences programmatically.
---

# ManyChat Flow Builder

Automate ManyChat DM funnel creation via API and browser. Build support & sales ecosystems, quiz flows, cart recovery, and retention sequences programmatically.

## When to Use

- Building DM funnels and automations for e-commerce brands
- Setting up welcome flows, abandoned cart recovery, replenishment
- Creating support/FAQ handlers with human handoff
- Bulk-creating custom fields, tags, and subscriber segments
- Integrating Shopify order data with ManyChat subscriber data

## Prerequisites

- ManyChat Pro account (API access requires Pro)
- ManyChat API token from Settings → API
- Instagram/Facebook page connected to ManyChat
- Node.js 18+ for MCP server
- Python 3 + Playwright for browser automation

## API-First Setup (Always Do This First)

### 1. Get Page Info
```bash
manychat_page_info()
```

### 2. Create Custom Fields
```bash
manychat_create_custom_field(name: "wellness_goal", type: "text", description: "Primary health goal")
manychat_create_custom_field(name: "preferred_gel", type: "text", description: "Product match")
manychat_create_custom_field(name: "last_order_date", type: "date", description: "Recent order")
manychat_create_custom_field(name: "cart_total", type: "number", description: "Abandoned cart")
```

**Field Types:** text, number, date, datetime, boolean

### 3. Create Tags
```bash
manychat_create_tag(name: "lead_new")
manychat_create_tag(name: "customer_first")
manychat_create_tag(name: "cart_abandoner")
manychat_create_tag(name: "quiz_completed")
```

### 4. List Existing Flows
```bash
manychat_list_flows()
```

## Browser Automation (For Flow Building)

ManyChat's API does NOT support creating/editing flows. Use Playwright browser automation.

### Authentication

The account uses Google OAuth. You cannot automate OAuth login without the user's Google password. Instead:

1. Open a visible browser (headed mode)
2. Hand off to user to sign in with Google
3. Resume automation after login

```python
from playwright.sync_api import sync_playwright

browser = p.chromium.launch_persistent_context(
    user_data_dir="/tmp/mc-profile",
    headless=False,  # MUST be headed for OAuth
    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
)
page = browser.new_page()
page.goto("https://app.manychat.com/signin")
# User signs in with Google
```

### Navigating to Flow Builder

```python
# After login, go to automation page
page.goto(f"https://app.manychat.com/{PAGE_ID}/cms")

# Create new automation
page.locator('button:has-text("New Automation")').first.click()
page.locator('button:has-text("Start From Scratch")').first.click()
page.locator('text=Start from a blank canvas').click()

# Result: URL becomes .../cms/files/{flow_id}/edit
```

### Key Data-Test IDs

| Element | Data-Test-ID |
|---------|-------------|
| New Automation button | `cms` |
| Flow title | `cms-flow-title` |
| Builder switch | `builder-switch-button` |
| AI generator open | `ai-flow-generator-open-button` |
| AI input | `ai-flow-generator-message-input` |
| AI send | `ai-flow-generator-send-message-button` |
| AI use automation | `ai-flow-generator-use-automation-button` |
| Flow chart | `flow-chart-builder` |
| Publish | `flow-editor-publish` |
| Preview | `flow-editor-preview` |

### Handling React UI Overlays

ManyChat uses React with overlay panels that intercept pointer events. Solutions:

```python
# Close overlays before clicking
page.keyboard.press("Escape")
page.mouse.click(100, 100)  # Click outside panel

# Use force click to bypass overlays
page.locator('button:has-text("New Automation")').first.click(force=True)

# Use JavaScript click when DOM clicks fail
page.evaluate("""
    () => {
        const btn = Array.from(document.querySelectorAll('button'))
            .find(b => b.textContent.trim() === 'New Automation');
        ['mousedown', 'mouseup', 'click'].forEach(evt => {
            btn.dispatchEvent(new MouseEvent(evt, { bubbles: true }));
        });
    }
""")
```

### Using ManyChat AI Builder

The AI builder can scaffold flows quickly. It asks a series of questions:

1. **Goal**: "Generate more leads and drive sales"
2. **Channel**: "Instagram" or "Messenger"
3. **Template type**: "Engage with a quiz", "Collect contact's data", "Grow email list"
4. **Topic**: Describe your quiz/product focus
5. **Questions**: Provide questions in format:
   ```
   Question: [Your question]
   Answer Options:
   A) [Option A]
   B) [Option B]
   C) [Option C]
   D) [Option D]
   Correct Answer: [Letter]
   ```

⚠️ **Limitation**: AI builder is designed for trivia/knowledge quizzes, not product recommendation flows. For sales funnels, build manually.

## Flow Architecture Patterns

### 1. Welcome & Lead Capture Flow

```
Trigger: New Subscriber
  → Welcome message + goal buttons
    → [Energy] [Skin] [Digestion] [Wellness]
      → Acknowledge goal + quiz offer
        → [Take Quiz] [See Products]
          → Quiz Path: 3 questions
            → Product recommendation
              → [Add to Cart] [Learn More]
                → Email capture (if empty)
                  → 23hr delay → Discount reminder
```

**Custom fields used:** wellness_goal, preferred_gel, energy_level, skin_type
**Tags applied:** quiz_completed, goal_energy/goal_skin/etc

### 2. Abandoned Cart Recovery

```
Trigger: Shopify webhook (cart abandoned)
  → Tag: cart_abandoner
  → Set field: cart_total
  → 30min delay
    → Cart reminder message
      → [Complete Order] [Need Help?]
  → 24hr delay (if no purchase)
    → Social proof + urgency
      → [Checkout] [Get 10% Off]
  → 48hr delay (if no purchase)
    → Final nudge or nurture sequence
```

### 3. Support & FAQ Flow

```
Trigger: Keywords (help, support, issue, refund)
  → Menu: [Order Status] [Products] [Shipping] [Returns] [Human]
    → Order Status: ask for order # → webhook to Shopify
    → Products: route to recommendation
    → Shipping: show rates + tracking link
    → Returns: collect details → tag support_open → notify Slack
    → Human: tag support_human_needed → Slack notification
```

### 4. Replenishment Flow

```
Trigger: 21 days after last_order_date
  → Check-in: "Running low on {preferred_gel}?"
    → [Need More] [Still Have Some] [Try Something New]
      → Reorder: 1-click checkout
      → Still have: delay 7 days, re-ask
      → New product: cross-sell recommendation
```

## Shopify Integration

### Webhook Middleware (Node.js/Express)

```javascript
// Receive Shopify order created
app.post('/webhook/shopify/order-created', async (req, res) => {
  const { email, customer, line_items } = req.body;
  const subscriber = await manychat.findSubscriberByEmail(email);
  
  // Set lifecycle tags
  if (customer.orders_count === 1) {
    await manychat.addTag(subscriber.id, 'customer_first');
  }
  
  // Set product tags
  line_items.forEach(item => {
    const tag = PRODUCT_TAG_MAP[item.handle];
    if (tag) await manychat.addTag(subscriber.id, tag);
  });
  
  // Set custom fields
  await manychat.setCustomField(subscriber.id, 'last_order_date', new Date());
});
```

### Shopify → ManyChat Events

| Shopify Event | ManyChat Action |
|---------------|-----------------|
| Order created | Tag customer, set last_order_date |
| Cart abandoned | Tag cart_abandoner, set cart_total, trigger flow |
| Order fulfilled | Remove cart_abandoner, schedule review flow |
| Refund created | Tag refund_requested |

## Meta Ads → DM Bridge

```
Meta Ads Manager:
  Campaign Objective: Messages
  Ad Format: Click to Message
  CTA: Send Message
  
ManyChat:
  Keyword trigger: "ATL same day" (or custom keyword)
  → Trigger: ATL Same-Day Flow
```

## Growth Tools Setup

### Instagram Comment Automation

| Post Type | Trigger Comments | Auto-DM |
|-----------|-----------------|---------|
| Product posts | "LINK", "PRICE", "INFO" | Product card + welcome flow |
| Educational | "GUIDE", "MORE", "TIPS" | Lead magnet PDF |
| Atlanta-specific | "ATL", "SAME DAY" | ATL campaign flow |

### Story Reply Triggers
- Reply to story → Welcome Flow
- Story poll response → Segmentation tag + follow-up
- Story mention → UGC Flow + discount code

## Message Voice & Tone

### Do
- "Hey beautiful soul! 🌿"
- "Welcome to the Holistic Vitalis family"
- "What brings you here today?"
- Use warm, natural language
- Include emojis sparingly (🌿💚✨🌊)

### Don't
- Sound robotic or corporate
- Use all caps
- Send 3+ messages without user response
- Pushy sales language ("BUY NOW!!!")

## Analytics to Track

| Metric | Target |
|--------|--------|
| DM opt-in rate | 8-15% |
| Quiz completion | 45-60% |
| Cart recovery | 10-18% |
| Bot resolution | 70-80% |
| Replenishment conversion | 15-25% |

## Troubleshooting

### "Channel permissions lost" modal
Close by pressing Escape or clicking the X button before proceeding.

### Clicks not registering
React event delegation requires specific event sequences:
```python
page.evaluate("""
    ['mousedown', 'mouseup', 'click'].forEach(evt => {
        btn.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
    });
""")
```

### Flow builder URL pattern
```
https://app.manychat.com/{PAGE_ID}/cms/files/{FLOW_ID}/edit
```

### Cookie import fails
ManyChat cookies are under `manychat.com` and `app.manychat.com`. Use both domains when importing.

## Complete Build Checklist

- [ ] Connect ManyChat Pro + API token
- [ ] Connect Instagram/Facebook channels
- [ ] Create all custom fields (12)
- [ ] Create all tags (30+)
- [ ] Build Welcome Flow
- [ ] Build Support/FAQ Flow
- [ ] Build Abandoned Cart Flow
- [ ] Build ATL Same-Day Flow
- [ ] Build Replenishment Flow
- [ ] Build Review & Referral Flow
- [ ] Build Story Mention Flow
- [ ] Build Bundle/Upsell Flow
- [ ] Set up Shopify webhooks
- [ ] Set up comment automation
- [ ] Set up ad-to-DM bridge
- [ ] Test all flows end-to-end
- [ ] Publish all flows

## Resources

- ManyChat API Docs: https://api.manychat.com/swagger
- Playwright Docs: https://playwright.dev/python/
- Holistic Vitalis Ecosystem: `~/Projects/Clients/Holistic-Vitalis/manychat-ecosystem/`
