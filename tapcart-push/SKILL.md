---
name: tapcart-push
description: Send or schedule a Tapcart push notification for Holistic Vitalis. Use when the user says "send a push", "push notification", "tapcart push", or wants to notify app subscribers about a sale, product launch, event, or promotion.
---

# Tapcart Push Notification Skill

Script location: `/Users/biznomad/Projects/Clients/Holistic-Vitalis/tapcart-push/send_push.py`

## Step 1: Gather notification details

If the user hasn't provided them, ask (use AskUserQuestion):
- **Title** (headline — shown in bold, max ~60 chars)
- **Message** (body copy, max ~100 chars)
- **Send time**: now vs. scheduled date/time (Eastern)
- **Audience**: all subscribers (default) or a specific segment

For promotional pushes, suggest copy using HV brand voice: direct, benefit-led, emoji-friendly.

**Free Shipping Weekend defaults (use if user says "free shipping weekend"):**
- Title: `🚛 Free Shipping All Weekend!`
- Message: `Shop now & get FREE shipping on every order. No minimum. Offer ends Sunday! 🌿`
- Send: Now
- Audience: All subscribers

## Step 2: Check Playwright is installed

```bash
cd /Users/biznomad/Projects/Clients/Holistic-Vitalis/tapcart-push
python3 -c "from playwright.async_api import async_playwright; print('✅ Playwright ready')" 2>/dev/null || echo "NEEDS_INSTALL"
```

If `NEEDS_INSTALL`:
```bash
pip install playwright && playwright install chromium
```

## Step 3: Check if session exists (first time = headed mode required)

```bash
ls /Users/biznomad/Projects/Clients/Holistic-Vitalis/tapcart-push/.session/profile/ 2>/dev/null | wc -l
```

- If **0 files** → first-time setup. Run with `--headed` and tell the user to log into Shopify admin in the browser that opens, then navigate to the Tapcart app. The session is saved automatically.
- If **files exist** → session is saved, run headlessly.

## Step 4: Run the script

**Send now (all subscribers):**
```bash
python3 /Users/biznomad/Projects/Clients/Holistic-Vitalis/tapcart-push/send_push.py \
  --title "TITLE_HERE" \
  --message "MESSAGE_HERE"
```

**Schedule for specific time:**
```bash
python3 /Users/biznomad/Projects/Clients/Holistic-Vitalis/tapcart-push/send_push.py \
  --title "TITLE_HERE" \
  --message "MESSAGE_HERE" \
  --schedule "2026-06-22 10:00"
```

**Target a segment:**
```bash
python3 /Users/biznomad/Projects/Clients/Holistic-Vitalis/tapcart-push/send_push.py \
  --title "TITLE_HERE" \
  --message "MESSAGE_HERE" \
  --segment "Segment Name Here"
```

**Dry run (see filled form, no send):**
```bash
python3 /Users/biznomad/Projects/Clients/Holistic-Vitalis/tapcart-push/send_push.py \
  --title "TITLE_HERE" \
  --message "MESSAGE_HERE" \
  --dry-run
```

**First-time / re-auth:**
```bash
python3 /Users/biznomad/Projects/Clients/Holistic-Vitalis/tapcart-push/send_push.py \
  --title "TITLE_HERE" \
  --message "MESSAGE_HERE" \
  --headed
```

## Step 5: Report result

After the script runs:
- ✅ **Success**: Report title, message, audience, and send/schedule time
- ❌ **Error**: Read `tapcart-push/error.png` and report what went wrong; check if session needs refresh (run `--headed` again)
- If `--dry-run`: Read `tapcart-push/dry-run-preview.png` and show the user

## Session refresh

If the script fails with "session expired", run with `--headed` to re-authenticate. Sessions typically last 30 days.

## Push notification best practices (HV)

- Keep titles under 50 chars — truncated on lock screen past that
- Lead with the offer/urgency in the first 5 words
- Emojis in title/message are supported
- Best send times: 10am–12pm ET and 6pm–8pm ET
- Don't send more than 2 pushes/week to avoid unsubscribes
