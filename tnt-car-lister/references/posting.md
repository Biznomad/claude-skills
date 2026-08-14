# Posting to Facebook Marketplace + Groups

## Why nothing is automated past the packet
Facebook has **no official API** for personal-account Marketplace listings, group posting, or personal DMs. Botting a personal account at volume → checkpoint or ban. The account holds the listings + buyer chats, so it's the asset. Strategy: automate the packet (safe, headless), gate the posting (manual or throttled browser).

## Manual post flow (per car)
1. facebook.com/marketplace/create/vehicle
2. Fill from `listing.json`: vehicle type, year, make, model, price, body style, exterior/interior, condition, fuel, transmission, clean-title checkbox (only if clean), mileage if known.
3. Paste `listing.txt` description.
4. Drag photos from `photos/` (01.jpg is cover = exterior lead).
5. **Save draft first** — FB create forms do NOT auto-save; if the tab navigates away, the unsaved form is lost. Then Publish.

## Cross-posting to car-selling groups (Atlanta)
Join first, then share the listing into the group. Best Atlanta-area groups (by fit + traffic):
- Atlanta Cheap Cars & Trucks $5000 or Less (~55K)
- Cash Cars Atlanta — No Rules (~31K) — best home for no-title cars
- Cars For Sale Cobb County & Metro Atlanta (~67K) — biggest reach
- Georgia Auto Marketplace (~49K)
- Georgia Vehicles For Sale (~39K)
- GA/TN/AL Used Vehicles for Sale (~32K)
- Georgia Used Auto Parts Sales & Trade (~2.9K) — parts/project cars only
- North Georgia Cars/Trucks + Parts (~48K)

## Throttle / anti-spam (critical)
- **Max ~2–3 group joins per day.** Rapid joins trip FB's spam detector.
- **1 post every few minutes**, not a burst.
- **Vary the text per group** — FB hashes duplicate posts and flags them. Tweak the headline / reorder bullets for each share.
- Some groups gate first-post behind a one-question form ("city + ZIP where you live" + agree-to-rules). Answer truthfully, don't skip.
- Space cross-posts across 2–3 days for a single car rather than all at once.

## Buyer DMs
Real buyers will message fast. Draft replies under TNT rules (no price commitment without owner tap; do-not-text list; STOP handling). Best long-term path: sell via a **FB Page + Commerce Manager vehicle catalog** connected to **GHL's Messenger integration** → official, ban-safe, AI-draftable. Personal-profile DMs can be read/drafted/sent via the Chrome extension but are browser-risky.
