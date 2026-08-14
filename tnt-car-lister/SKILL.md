---
name: tnt-car-lister
description: Turn a bought/won TNT cash-for-cars lead into a ready-to-post Facebook Marketplace listing packet — pull photos, auto-blur license plates + drop VIN closeups, mine the seller's texts and call transcripts for the real issues (faults, engine/OBD codes, title status), and write an honest, price-tiered description. Use when the user says "list this car", "make a FB Marketplace listing for [car/lead]", "build a listing packet", "help me sell this car", "post the porsche/prius/[car]", or references a won/bought car lead that needs selling. Covers the TNT voice stack (Retell/Beside/GHL), GHL lead/photo fetching, and the safety rules around FB Marketplace (personal account = never auto-post, gate everything).
---

# TNT Car Lister

Turn a won cash-for-cars lead into a sellable FB Marketplace listing — honestly, safely, with photos prepped.

## Hard rules (do not violate)

1. **Never auto-publish to Facebook.** A personal FB account is the asset; botting it gets checkpointed/banned. This skill produces a *packet*; posting is a manual, owner-gated step.
2. **Never publish the customer's street address.** City/ZIP only. The generator enforces this — don't override.
3. **Blur every license plate.** If a photo can't be classified (Gemini down/rate-limited), EXCLUDE it rather than risk an unblurred plate. VIN stickers / paperwork closeups are auto-dropped.
4. **Be honest about the bad stuff.** Non-runner, no-title, stalling, codes — disclose up front. It protects against chargebacks and angry buyers.

## The pipeline (canonical scripts live on TNT + GitHub)

`fb_listing_gen.py` (lead → packet) and `call_transcripts.py` (call audio/text → transcript) are committed at `github.com/Biznomad/two-and-through-ops` under `scripts/`, deployed on TNT at `/root/two-and-through-ops/scripts/`. Bundled copies in this skill's `scripts/` are for reference/patching.

### 1. Identify the lead
Find the lead in `/root/two-and-through-ops/data/leads.json` → `leads[]`. Match by `id`, phone, or `ghl_contact_id`. Look for `status: won` + `service_interest: cash-for-cars`.

### 2. Generate the packet
```bash
ssh biznomad 'ssh tnt "cd /root/two-and-through-ops && python3 scripts/fb_listing_gen.py --lead <LEAD_ID>"'
```
Outputs `data/fb-listings/<lead_id>/`: `listing.json` (all FB fields), `listing.txt` (copy-paste), `listing.html` (owner preview), `photos/` (ordered, plates blurred, exterior first).
- Other modes: `--contact <GHL_CONTACT_ID>` · `--scan-won` (every won lead) · `--selftest` (offline logic checks).

### 3. Review the packet with the owner
Show price (always flagged CONFIRM), description, photo order, title status, extracted issues. Owner confirms price + wording before posting.

### 4. Post (manual, gated)
Open FB Marketplace → Create listing → Vehicle. Fill fields from `listing.json`, paste description, drag photos from `data/fb-listings/<lead_id>/photos/` (or pull them to the Mac first). Cross-post to Atlanta car-selling groups (join first, throttle 2–3/day, vary text — see references/posting.md).

## Gotchas that already bit us (don't relearn)

- **SSH is jump-hosted:** every TNT command is `ssh biznomad 'ssh tnt "..."'`. If `exec request failed on channel 0`, the biznomad VPS is fork-starved (too many services) — reboot via Hostinger panel, then race in.
- **GHL fetch caps at 50 messages** and drops the oldest (which are usually the exterior photos). The script paginates ALL messages — don't use the naive `fetch_msgs` for cars with long threads.
- **Gemini shared key gets 429'd by the whole fleet.** Free tier rolls daily. Throttle + 429-retry are in the script. If plate-blur fails (all photos "unclassified"), it's quota — wait for reset, don't force-post.
- **GHL CDN is Cloudflare-fronted** → needs a real `User-Agent` (python-urllib default is blocked).
- **Title status usually lives in the seller's texts**, not the structured note. And T&T's *own outbound* "bill of sale" template must NOT count as "no title" — detect from inbound messages only.
- **The model field slurps appended pipeline log lines** like `[T1156 ...] Segmented to auto_partner_referral`. Cut notes at newline/bracket, cap model at 3 words.

## Call transcripts (for the spoken details — codes, mileage)

Engine codes, mileage, and fault details are often spoken, not texted. See **references/voice-stack.md** for which provider has which call. Quick version:
- `call_transcripts.py sync` — pull all Retell transcripts (Avery agent, +16786733121)
- `call_transcripts.py phone +1XXXXXXXXXX` — calls for a number
- `call_transcripts.py transcribe <url>` — Gemini-transcribe ANY recording (handles GHL/Beside audio once you have the URL)

FB Marketplace groups + cross-posting throttle rules: **references/posting.md**.

## Pricing tiers (suggested START price — always owner-confirmed)

| runs | title | formula | floor |
|---|---|---|---|
| yes | clean | est_high × 3 | $1800 |
| yes | none | est_high × 2 | $1200 |
| no | clean | est_high × 3 (or no est) | $2000 |
| no | none | est_high × 1.5 | $1200 (parts) |

Round to nearest $100; use floor when no estimate exists.
