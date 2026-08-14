#!/usr/bin/env python3
"""TNT Facebook Marketplace listing generator (Layer 1 — safe, headless).

Turns a bought/won car lead into a ready-to-post listing packet:
  lead -> parse details -> pull photos -> auto-blur plates (Gemini vision)
       -> mine texts + call transcript for the REAL issues -> write packet.

Output (per car) in data/fb-listings/<lead_id>/ :
  listing.json   all Facebook vehicle fields + suggested price
  listing.txt    copy-paste-ready title + description + photo order
  listing.html   owner preview (photos + fields + description)
  photos/        clean, ordered photos (plates blacked out, VIN closeups dropped)

Runs on the TNT ops server (needs GHL PIT + GEMINI_API_KEY). Reuses
buyer_ready (GHL) and call_transcripts (Retell/Gemini) already deployed there.

Usage:
  fb_listing_gen.py --lead <LEAD_ID>          one car
  fb_listing_gen.py --contact <GHL_CONTACT>   one car by GHL contact
  fb_listing_gen.py --scan-won                every 'won' cash-for-cars lead
  fb_listing_gen.py --selftest                offline unit checks (no creds)
"""
import os, sys, re, json, time, base64, urllib.request, urllib.error, html

OPS = "/root/two-and-through-ops"
OUT_ROOT = os.path.join(OPS, "data", "fb-listings")

# ---------------------------------------------------------------- creds / deps
def _cfg(path, key):
    try:
        for ln in open(path):
            ln = ln.strip()
            if ln.startswith(key + "=") and not ln.startswith("#"):
                return ln.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""

def gemini_key():
    for f in (os.path.join(OPS, ".env"), "/root/.hermes/.env", "/root/nareem/.env"):
        k = _cfg(f, "GEMINI_API_KEY")
        if k:
            return k
    return os.environ.get("GEMINI_API_KEY", "")

# VIN check-digit validation (ISO 3779) — mirrors media_examiner
_TRANS = {**{str(d): d for d in range(10)},
          **{c: v for c, v in zip("ABCDEFGHJKLMNPRSTUVWXYZ",
                                   [1,2,3,4,5,6,7,8,1,2,3,4,5,7,9,2,3,4,5,6,7,8,9])}}
_WEIGHTS = [8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2]
VIN_RE = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")

def vin_valid(v):
    v = (v or "").upper()
    if len(v) != 17 or any(c in "IOQ" for c in v):
        return False
    try:
        total = sum(_TRANS[c] * w for c, w in zip(v, _WEIGHTS))
    except KeyError:
        return False
    check = total % 11
    return v[8] == ("X" if check == 10 else str(check))

# ---------------------------------------------------------------- parsing
FIELD_RE = lambda k: re.compile(k + r"\s*:\s*([^|]+)", re.I)

def parse_notes(notes):
    """Extract structured facts from a cash-for-cars lead note."""
    notes = notes or ""
    out = {"year": "", "make": "", "model": "", "runs": "", "title": "",
           "condition": "", "est_low": None, "est_high": None, "zip": ""}
    def grab(k):
        m = FIELD_RE(k).search(notes)
        return m.group(1).strip() if m else ""
    veh = grab("Vehicle") or grab("Notes")
    veh = re.split(r"[\n\[]", veh)[0].strip()          # cut appended log lines / brackets
    m = re.search(r"(19|20)\d\d", veh)
    if m:
        out["year"] = m.group(0)
        rest = re.findall(r"[A-Za-z][A-Za-z0-9-]*", veh[m.end():])   # words only
        if rest:
            out["make"] = rest[0].title()
            out["model"] = " ".join(rest[1:4]).title()  # cap at 3 words
    runs = (grab("Runs") + " " + notes).lower()
    if any(w in runs for w in ("non-runner", "non runner", "no-start", "no start", "doesn't run", "does not run", "won't start")):
        out["runs"] = "non-runner"
    elif "drive" in runs or "runs" in grab("Runs").lower():
        out["runs"] = "runs"
    title = grab("Title").lower()
    if "notitle" in title or "no title" in title or "bill of sale" in title:
        out["title"] = "none"
    elif title:
        out["title"] = "clean"
    out["condition"] = grab("Condition")
    er = grab("Est. range") or grab("Est range")
    nums = re.findall(r"\$?([\d,]{3,6})", er)
    if len(nums) >= 2:
        out["est_low"], out["est_high"] = int(nums[0].replace(",", "")), int(nums[1].replace(",", ""))
    zp = grab("ZIP") or grab("Zip")
    zm = re.search(r"\b(\d{5})\b", zp or notes)
    if zm:
        out["zip"] = zm.group(1)
    return out

def detect_title(parsed, messages):
    """Title status usually lives in the texts. Scan INBOUND (seller) msgs only —
    T&T's own outbound bill-of-sale template must not count as 'no title'."""
    if parsed.get("title"):
        return parsed["title"]
    inb = " ".join((m.get("body") or "") for m in messages
                   if m.get("direction") == "inbound").lower()
    if re.search(r"\bno[\s-]*title\b|don'?t have (the )?title|without (a )?title", inb):
        return "none"
    if re.search(r"title (in (my|your) name|on hand|in hand)|have the title|it is in my name", inb):
        return "clean"
    return ""

def _all_msgs(br, conv_id):
    """Paginate ALL messages (fetch_msgs caps at 50 and drops the oldest photos)."""
    msgs, last = [], None
    for _ in range(20):
        q = f"/conversations/{conv_id}/messages?limit=100" + (f"&lastMessageId={last}" if last else "")
        d = br._ghl(q, version="2021-04-15")
        block = d.get("messages") or {}
        arr = block.get("messages", []) if isinstance(block, dict) else block
        if not arr:
            break
        msgs.extend(arr)
        nxt = block.get("lastMessageId") if isinstance(block, dict) else None
        if not nxt or nxt == last:
            break
        last = nxt
    return msgs

def safe_location(rec, parsed):
    """City/ZIP only — NEVER publish the customer's street address."""
    z = parsed.get("zip") or ""
    if not z:
        m = re.search(r"\b(\d{5})\b", rec.get("address", "") or "")
        z = m.group(1) if m else ""
    return f"Metro Atlanta ({z})" if z else "Metro Atlanta"

def extract_vin(messages):
    for m in messages or []:
        for cand in VIN_RE.findall((m.get("body") or "").upper().replace(" ", "")):
            if vin_valid(cand):
                return cand
    return ""

# ---------------------------------------------------------------- pricing
def compute_price(p):
    """Transparent suggested START price. Always owner-confirmed."""
    hi = p.get("est_high") or 0
    runs, title = p.get("runs"), p.get("title")
    if runs == "runs" and title == "clean":
        mult, floor = 3.0, 1800
    elif runs == "runs" and title == "none":
        mult, floor = 2.0, 1200
    elif runs == "non-runner" and title == "clean":
        mult, floor = 3.0, 2000
    else:  # non-runner + no title  => parts
        mult, floor = 1.5, 1200
    if hi:
        val = max(int(round(hi * mult / 100.0)) * 100, floor)
    else:
        val = floor
    return {"suggested": val, "confirm": True,
            "basis": f"est_high={hi or 'n/a'} x{mult} (runs={runs}, title={title})"}

# ---------------------------------------------------------------- gemini vision / nlp
_GEM_LAST = [0.0]      # throttle state — free tier is ~10-15 req/min
_GEM_MIN_GAP = 5.0

def _gemini(parts, key, timeout=120):
    body = {"contents": [{"parts": parts}]}
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "gemini-2.5-flash:generateContent?key=" + key)
    for attempt in (1, 2, 3):
        gap = _GEM_MIN_GAP - (time.time() - _GEM_LAST[0])
        if gap > 0:
            time.sleep(gap)
        _GEM_LAST[0] = time.time()
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
            return d["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 3:
                time.sleep(8 * attempt); continue
            raise

def _img_part(path):
    mime = "image/png" if path.endswith(".png") else "image/jpeg"
    return {"inline_data": {"mime_type": mime, "data": base64.b64encode(open(path, "rb").read()).decode()}}

def classify_photo(path, key):
    """Return dict: {kind: exterior|interior|engine|document, plate_bbox:[x0,y0,x1,y1]|null}
    bbox normalized 0..1. document = VIN sticker / paperwork -> drop from public post."""
    if not key:
        return {"kind": "unknown", "plate_bbox": None}
    prompt = ("You are prepping a used-car photo for a public marketplace post. "
              "Reply with ONLY compact JSON: {\"kind\":\"exterior|interior|engine|part|document\","
              "\"plate_bbox\":[x0,y0,x1,y1] or null}. kind=document ONLY if the image is mainly a "
              "printed VIN sticker, a title/registration/paperwork document, or a phone/computer "
              "screen — NOT a photo of a car part, fuse box, or engine bay (those are 'part' or "
              "'engine' and MUST be kept). plate_bbox = normalized 0..1 bounding box of any "
              "visible LICENSE PLATE (registration tag), else null.")
    try:
        txt = _gemini([{"text": prompt}, _img_part(path)], key).replace("```json", "").replace("```", "")
        m = re.search(r"\{.*\}", txt, re.S)
        return json.loads(m.group(0)) if m else {"kind": "unknown", "plate_bbox": None}
    except Exception as e:
        return {"kind": "unknown", "plate_bbox": None, "err": str(e)}

def blur_region(path, bbox, out_path):
    """Black out a normalized bbox. Pure/local — no creds. Returns out_path."""
    from PIL import Image, ImageDraw
    im = Image.open(path).convert("RGB")
    w, h = im.size
    x0, y0, x1, y1 = bbox
    pad = 0.012
    box = (int(max(0, x0 - pad) * w), int(max(0, y0 - pad) * h),
           int(min(1, x1 + pad) * w), int(min(1, y1 + pad) * h))
    ImageDraw.Draw(im).rectangle(box, fill=(15, 15, 15))
    im.save(out_path, quality=92)
    return out_path

def extract_issues(convo_text, key):
    """Mine the thread + transcript for specific defects the SELLER explicitly stated."""
    if not key:
        return []
    prompt = ("From this cash-for-cars conversation, list ONLY specific mechanical PROBLEMS, "
              "defects, or diagnostic facts the SELLER explicitly stated about this car — e.g. "
              "\"won't start\", \"burnt fuse box (part 7L0 937 559)\", an engine/OBD fault code, "
              "a missing catalytic converter, whether a replacement part is or isn't included, "
              "or a specific cosmetic defect. STRICT RULES: do NOT restate the year/make/model, "
              "VIN, mileage, title status, keys, price, or whether it generally runs — those are "
              "handled elsewhere. Do NOT infer, guess, or invent anything not explicitly said. "
              "Return a JSON array of short strings; [] if none stated. Conversation:\n" + convo_text[:12000])
    bad = re.compile(r"\b(vin|title|keys?|mileage|bill of sale|no ?title|for sale)\b", re.I)
    try:
        txt = _gemini([{"text": prompt}], key).replace("```json", "").replace("```", "")
        m = re.search(r"\[.*\]", txt, re.S)
        arr = json.loads(m.group(0)) if m else []
        out = []
        for x in arr:
            s = str(x).strip().rstrip(".")
            if s and not bad.search(s):
                out.append(s)
        return out[:8]
    except Exception:
        return []

# ---------------------------------------------------------------- description
def build_listing(parsed, vin, issues, price, city):
    y, mk, md = parsed["year"], parsed["make"], parsed["model"]
    title_line = f"{y} {mk} {md}".strip()
    runs = parsed["runs"]
    has_title = parsed["title"] == "clean"
    no_title = parsed["title"] == "none"

    fb_condition = "Poor" if runs == "non-runner" else "Fair"
    headline = title_line
    if runs == "non-runner":
        headline += " — Runs Project / Non-Runner"
    if no_title:
        headline += " — Bill of Sale Only"

    lines = [f"{title_line}."]
    # lead disclosure
    if runs == "non-runner":
        lead = "⚠️ PLEASE READ — DOES NOT RUN."
    else:
        lead = "Starts, runs, and drives."
    if issues:
        lead += " " + " ".join(i if i.endswith(".") else i + "." for i in issues[:3])
    lines.append("\n" + lead)
    # title disclosure
    if no_title:
        lines.append("\n⚠️ NO TITLE — bill of sale only. Priced accordingly.")
    elif has_title:
        lines.append("\n✅ Clean title in hand (not salvage, not rebuilt).")
    # bullets
    good = ["✅ Complete, straight body — all glass and panels"]
    if has_title:
        good.insert(0, "✅ Clean, in-hand title")
    expect = []
    if runs == "non-runner":
        expect.append("• Does not start or drive — bring a trailer")
    for i in issues[3:7]:
        expect.append("• " + i)
    lines.append("\nWhat's good:\n" + "\n".join(good))
    if expect:
        lines.append("\nWhat to expect (priced accordingly):\n" + "\n".join(expect))
    lines.append(f"\nSelling AS-IS, whole vehicle — not parting out. Cash only, buyer arranges "
                 f"tow/pickup ({city} area). Serious buyers welcome to come look. "
                 f"Reasonable offers — no lowballs.")
    description = "\n".join(lines)

    return {
        "headline": headline,
        "fields": {
            "vehicle_type": "Car/Truck", "year": y, "make": mk, "model": md,
            "vin": vin, "price": price["suggested"], "price_confirm": True,
            "body_style": _body_style(md), "condition": fb_condition,
            "fuel_type": _fuel(mk, md), "transmission": "Automatic",
            "clean_title": has_title, "location_city": city, "mileage": "",
        },
        "description": description,
    }

def _body_style(model):
    m = (model or "").lower()
    if "prius" in m: return "Hatchback"
    if any(s in m for s in ("cayenne","suburban","tahoe","explorer","suv","rav","cr-v","escape")): return "SUV"
    if any(t in m for t in ("truck","f-150","silverado","ram","tacoma","tundra")): return "Truck"
    return "Sedan"

def _fuel(make, model):
    m = (model or "").lower()
    if "prius" in m: return "Hybrid"
    return "Gasoline"

# ---------------------------------------------------------------- selftest (offline)
def selftest():
    ok = True
    def chk(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name); ok = ok and cond

    pr = parse_notes("CASH-FOR-CARS LEAD | Vehicle: 2005 Toyota Prius | Type: sedan | Runs: drives | Title: notitle | Condition: whole | Est. range: $500-$700 | ZIP: 30228")
    chk("prius year/make/model", (pr["year"], pr["make"], pr["model"]) == ("2005", "Toyota", "Prius"))
    chk("prius runs/title", pr["runs"] == "runs" and pr["title"] == "none")
    chk("prius est range", (pr["est_low"], pr["est_high"]) == (500, 700))
    chk("prius zip", pr["zip"] == "30228")

    po = parse_notes("Vehicle situation: Complete non-runner — sell for cash | Notes: 2006 Porsche cayenne")
    chk("porsche year/make/model", (po["year"], po["make"], po["model"]) == ("2006", "Porsche", "Cayenne"))
    chk("porsche non-runner", po["runs"] == "non-runner")

    chk("vin valid", vin_valid("WP1AA29P36LA24294") and vin_valid("JTDKB20U357018671"))
    chk("vin invalid", not vin_valid("WP1AA29P36LA24295"))

    chk("price prius runs+notitle", compute_price(pr)["suggested"] == max(700 * 2, 1200))
    chk("price porsche nonrun+clean(no est)", compute_price({**po, "title": "clean"})["suggested"] == 2000)

    l = build_listing({**pr, "title": "none"}, "JTDKB20U357018671",
                      ["Starts and drives but cuts off after ~10 min (likely hybrid battery)"],
                      compute_price(pr), "South Metro Atlanta")
    chk("desc no-title disclosed", "NO TITLE" in l["description"])
    chk("desc issue folded in", "cuts off" in l["description"])
    chk("fields hatchback/hybrid", l["fields"]["body_style"] == "Hatchback" and l["fields"]["fuel_type"] == "Hybrid")
    print("\n--- sample Prius description ---\n" + l["description"])
    print("\nSELFTEST:", "ALL PASS" if ok else "FAILURES")
    return ok

# ---------------------------------------------------------------- packet (needs TNT)
def generate(lead=None, contact=None):
    sys.path.insert(0, os.path.join(OPS, "scripts", "mecca"))
    import buyer_ready as br
    key = gemini_key()
    leads = json.load(open(os.path.join(OPS, "data", "leads.json")))["leads"]
    rec = next((l for l in leads
                if (lead and l.get("id") == lead)
                or (contact and l.get("ghl_contact_id") == contact)), None)
    if not rec:
        print("lead not found"); return None
    cid = rec.get("ghl_contact_id")
    parsed = parse_notes(rec.get("notes"))
    msgs = []
    if cid:
        d = br._ghl(f"/conversations/search?locationId={br.LOC}&contactId={cid}", version="2021-04-15")
        convs = d.get("conversations", []) if isinstance(d, dict) else []
        if convs:
            msgs = sorted(_all_msgs(br, convs[0]["id"]), key=lambda x: x.get("dateAdded", ""))
    vin = extract_vin(msgs)
    # transcript (Retell) if available
    convo = "\n".join(f"[{m.get('direction')}] {m.get('body','')}" for m in msgs if m.get("body"))
    try:
        import call_transcripts as ct
        for f in os.listdir(ct.OUT):
            if f.endswith(".txt"):
                t = open(os.path.join(ct.OUT, f)).read()
                if (rec.get("phone", "")[-7:] or "~") in t:
                    convo += "\n[CALL]\n" + t
    except Exception:
        pass
    parsed["title"] = detect_title(parsed, msgs)   # title often only in the texts (inbound)
    issues = extract_issues(convo, key)
    price = compute_price(parsed)
    city = safe_location(rec, parsed)                # city/ZIP only, never street address
    listing = build_listing(parsed, vin, issues, price, city)

    dest = os.path.join(OUT_ROOT, rec.get("id"))
    photos = os.path.join(dest, "photos")
    os.makedirs(photos, exist_ok=True)
    RANK = {"exterior": 0, "interior": 1, "engine": 2, "part": 3, "unknown": 4}
    n = 0; staged = []; dbg = []
    for m in msgs:
        if m.get("direction") != "inbound":
            continue
        for a in (m.get("attachments") or []):
            if not (isinstance(a, str) and a.startswith("http")):
                continue
            n += 1
            raw = os.path.join(dest, f"_raw_{n:02d}.jpg")
            try:  # CDN is Cloudflare-fronted -> needs a real User-Agent
                rq = urllib.request.Request(a, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(rq, timeout=60) as r, open(raw, "wb") as fh:
                    fh.write(r.read())
            except Exception as e:
                dbg.append(f"#{n} DL_FAIL:{str(e)[:30]}"); continue
            info = classify_photo(raw, key)
            kind = info.get("kind") or "unknown"
            if kind == "document":
                dbg.append(f"#{n} drop:document"); os.remove(raw); continue
            if kind == "unknown":   # couldn't verify -> may hide a plate; exclude for owner review
                dbg.append(f"#{n} EXCLUDE:unclassified"); os.remove(raw); continue
            if info.get("plate_bbox"):
                blur_region(raw, info["plate_bbox"], raw)  # blur in place
                dbg.append(f"#{n} keep:{kind}+plateblur")
            else:
                dbg.append(f"#{n} keep:{kind}")
            staged.append((RANK.get(kind, 4), n, raw))
    staged.sort(key=lambda t: (t[0], t[1]))   # exterior first, then chronological
    kept = []
    for i, (_r, _n, raw) in enumerate(staged, 1):
        final = os.path.join(photos, f"{i:02d}.jpg")
        os.rename(raw, final)
        kept.append(os.path.basename(final))
    print("photo debug:", " | ".join(dbg))
    listing["photos"] = kept
    json.dump(listing, open(os.path.join(dest, "listing.json"), "w"), indent=2)
    open(os.path.join(dest, "listing.txt"), "w").write(
        listing["headline"] + "\n\nPRICE (confirm): $" + str(price["suggested"]) +
        "\n\n" + listing["description"] + "\n\nPhoto order: " + ", ".join(kept))
    _write_html(dest, listing, price)
    print("packet ->", dest, "| photos:", len(kept), "| vin:", vin or "n/a")
    return dest

def _write_html(dest, listing, price):
    imgs = "".join(f'<img src="photos/{p}" style="width:220px;margin:4px;border-radius:8px">' for p in listing.get("photos", []))
    f = listing["fields"]
    rows = "".join(f"<tr><td style='color:#888'>{k}</td><td>{html.escape(str(v))}</td></tr>" for k, v in f.items())
    doc = f"""<!doctype html><meta charset=utf-8><body style="font-family:system-ui;max-width:900px;margin:24px auto">
<h2>{html.escape(listing['headline'])}</h2>
<h3 style="color:#c00">Suggested price: ${price['suggested']} — CONFIRM</h3>
<div>{imgs}</div><table style="border-collapse:collapse;margin-top:12px">{rows}</table>
<pre style="white-space:pre-wrap;background:#f6f6f6;padding:16px;border-radius:8px;margin-top:12px">{html.escape(listing['description'])}</pre>
</body>"""
    open(os.path.join(dest, "listing.html"), "w").write(doc)

# ---------------------------------------------------------------- cli
if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        sys.exit(0 if selftest() else 1)
    if "--lead" in a:
        generate(lead=a[a.index("--lead") + 1])
    elif "--contact" in a:
        generate(contact=a[a.index("--contact") + 1])
    elif "--scan-won" in a:
        leads = json.load(open(os.path.join(OPS, "data", "leads.json")))["leads"]
        for l in leads:
            if l.get("status") == "won" and l.get("service_interest") == "cash-for-cars":
                generate(lead=l.get("id"))
    else:
        print(__doc__)
