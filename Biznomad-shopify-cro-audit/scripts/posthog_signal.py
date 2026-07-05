#!/usr/bin/env python3
"""
Wave 0 — PostHog behavioral-signal puller for the Biznomad Shopify CRO audit.

Fully reusable across clients. Stdlib-only (urllib) — no pip deps.
Pulls the real conversion leaks BEFORE the static/browser waves so the audit
aims at what is actually losing money: funnel drop-off, rageclicks, JS
exceptions, CVR trend, and a deploy-regression signature.

Config is 100% env-driven (no client-specific paths hardcoded):

  POSTHOG_PERSONAL_API_KEY   required   personal/all-access key, starts `phx_`
  POSTHOG_PROJECT_ID         required   numeric project id (e.g. 453359)
  POSTHOG_HOST               optional   default https://us.posthog.com
                                        NOTE: HogQL host is the APP host
                                        (us.posthog.com), NOT the ingest host
                                        (us.i.posthog.com). EU = https://eu.posthog.com
  OUTPUT_DIR                 optional   default cwd; writes wave0-posthog.md here
  POSTHOG_DATE_FROM          optional   YYYY-MM-DD; default = today-14d
  POSTHOG_DATE_TO            optional   YYYY-MM-DD; default = today
  POSTHOG_FUNNEL_EVENTS      optional   comma-list overriding the default funnel
                                        events (order matters). Default:
                                        $pageview,product_viewed,product_added_to_cart,
                                        checkout_started,payment_info_submitted,purchase
  POSTHOG_DEPLOY_DATE        optional   YYYY-MM-DD to annotate on the CVR trend
                                        (e.g. a theme deploy you suspect)
  POSTHOG_BENIGN_EXC         optional   comma-list of substrings to treat as
                                        benign JS-exception noise. Default:
                                        _AutofillCallbackHandler,Load failed,Script error.,NetworkError

Usage:
  set -a; source <client>/posthog.env; set +a
  OUTPUT_DIR=<client>/audit-YYYY-MM-DD python3 posthog_signal.py
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# ── config ────────────────────────────────────────────────────────────────
API_KEY = os.environ.get("POSTHOG_PERSONAL_API_KEY") or os.environ.get("POSTHOG_API_KEY")
PROJECT_ID = os.environ.get("POSTHOG_PROJECT_ID")
HOST = (os.environ.get("POSTHOG_HOST") or "https://us.posthog.com").rstrip("/")
# Defend against accidentally using the ingest host for HogQL (a known gotcha).
if HOST.startswith("https://us.i."):
    HOST = "https://us.posthog.com"
elif HOST.startswith("https://eu.i."):
    HOST = "https://eu.posthog.com"

OUTPUT_DIR = os.environ.get("OUTPUT_DIR") or os.getcwd()
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "wave0-posthog.md")

today = datetime.utcnow().date()
DATE_TO = os.environ.get("POSTHOG_DATE_TO") or today.isoformat()
DATE_FROM = os.environ.get("POSTHOG_DATE_FROM") or (today - timedelta(days=14)).isoformat()
DEPLOY_DATE = os.environ.get("POSTHOG_DEPLOY_DATE", "").strip()

DEFAULT_FUNNEL = "$pageview,product_viewed,product_added_to_cart,checkout_started,payment_info_submitted,purchase"
FUNNEL_EVENTS = [e.strip() for e in (os.environ.get("POSTHOG_FUNNEL_EVENTS") or DEFAULT_FUNNEL).split(",") if e.strip()]

DEFAULT_BENIGN = "_AutofillCallbackHandler,Load failed,Script error.,NetworkError"
BENIGN = [b.strip() for b in (os.environ.get("POSTHOG_BENIGN_EXC") or DEFAULT_BENIGN).split(",") if b.strip()]

if not API_KEY or not PROJECT_ID:
    sys.stderr.write(
        "ERROR: POSTHOG_PERSONAL_API_KEY and POSTHOG_PROJECT_ID are required.\n"
        "Source the client's posthog.env first (set -a; source posthog.env; set +a).\n"
    )
    sys.exit(2)

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


# ── http ──────────────────────────────────────────────────────────────────
def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return None, f"HTTPError {e.code}: {body[:500]}"
    except Exception as ex:  # noqa: BLE001
        return None, str(ex)


def hogql(query_str):
    url = f"{HOST}/api/projects/{PROJECT_ID}/query/"
    return post_json(url, {"query": {"kind": "HogQLQuery", "query": query_str}})


def _q(s):
    """Single-quote-escape a value for inline HogQL."""
    return s.replace("'", "''")


# ── pulls ─────────────────────────────────────────────────────────────────
def pull_funnel_counts():
    """Raw per-event counts for the configured funnel (directional CVR)."""
    cases = ",\n".join(
        f"  countIf(event = '{_q(ev)}') as step{i}" for i, ev in enumerate(FUNNEL_EVENTS)
    )
    q = f"""
    SELECT
{cases}
    FROM events
    WHERE toDate(timestamp) >= '{DATE_FROM}' AND toDate(timestamp) <= '{DATE_TO}'
    """
    return hogql(q)


def pull_rageclicks():
    q = f"""
    SELECT properties['$el_text'] as element_text,
           properties['$current_url'] as page_url,
           count() as rage_count
    FROM events
    WHERE event = '$rageclick'
      AND toDate(timestamp) >= '{DATE_FROM}' AND toDate(timestamp) <= '{DATE_TO}'
    GROUP BY element_text, page_url
    ORDER BY rage_count DESC
    LIMIT 15
    """
    return hogql(q)


def _exc_has_labels(res):
    """True if the result has non-empty type/message in col 0 or 1 (not all blank)."""
    for r in rows(res):
        if (r[0] and str(r[0]).strip()) or (len(r) > 1 and r[1] and str(r[1]).strip()):
            return True
    return False


def pull_exceptions():
    # Primary: modern posthog-js stores arrays in $exception_types / $exception_values
    # (the typed $exception_type/$exception_message scalars are often EMPTY on newer SDKs —
    #  grouping by them silently yields "(unknown)" rows, so we extract the array head instead).
    q = f"""
    SELECT JSONExtractString(properties['$exception_types'], 1) as exc_type,
           JSONExtractString(properties['$exception_values'], 1) as exc_msg,
           properties['$current_url'] as page_url,
           count() as exc_count
    FROM events
    WHERE event = '$exception'
      AND toDate(timestamp) >= '{DATE_FROM}' AND toDate(timestamp) <= '{DATE_TO}'
    GROUP BY exc_type, exc_msg, page_url
    ORDER BY exc_count DESC
    LIMIT 25
    """
    res, err = hogql(q)
    if not err and _exc_has_labels(res):
        return res, None
    # Fallback: older SDK scalar props
    q2 = f"""
    SELECT properties['$exception_type'] as exc_type,
           properties['$exception_message'] as exc_msg,
           properties['$current_url'] as page_url,
           count() as exc_count
    FROM events
    WHERE event = '$exception'
      AND toDate(timestamp) >= '{DATE_FROM}' AND toDate(timestamp) <= '{DATE_TO}'
    GROUP BY exc_type, exc_msg, page_url
    ORDER BY exc_count DESC
    LIMIT 25
    """
    res2, err2 = hogql(q2)
    if not err2 and _exc_has_labels(res2):
        return res2, None
    # Last resort: page + count only (at least shows where errors cluster)
    q3 = f"""
    SELECT properties['$current_url'] as page_url, count() as exc_count
    FROM events
    WHERE event = '$exception'
      AND toDate(timestamp) >= '{DATE_FROM}' AND toDate(timestamp) <= '{DATE_TO}'
    GROUP BY page_url ORDER BY exc_count DESC LIMIT 25
    """
    res3, err3 = hogql(q3)
    return res3, (err3 or err2 or err)


def pull_cvr_trend():
    q = f"""
    SELECT toDate(timestamp) as day,
           countIf(event = 'purchase') as purchases,
           countIf(event = '$pageview') as pageviews,
           round(100.0 * countIf(event = 'purchase') / nullIf(countIf(event = '$pageview'), 0), 3) as cvr_pct
    FROM events
    WHERE toDate(timestamp) >= '{DATE_FROM}' AND toDate(timestamp) <= '{DATE_TO}'
    GROUP BY day ORDER BY day ASC
    """
    return hogql(q)


def pull_event_inventory():
    """Surface event-name mismatches (e.g. add_to_cart vs product_added_to_cart)."""
    q = f"""
    SELECT event, count() as c
    FROM events
    WHERE toDate(timestamp) >= '{DATE_FROM}' AND toDate(timestamp) <= '{DATE_TO}'
    GROUP BY event ORDER BY c DESC LIMIT 40
    """
    return hogql(q)


# ── helpers ───────────────────────────────────────────────────────────────
def is_benign(label):
    return bool(label) and any(b in str(label) for b in BENIGN)


def rows(res):
    return (res or {}).get("results", []) or []


# ── main ──────────────────────────────────────────────────────────────────
def main():
    print(f"Pulling PostHog signal — project {PROJECT_ID} @ {HOST} ({DATE_FROM}→{DATE_TO})")

    funnel, funnel_err = pull_funnel_counts()
    rage, rage_err = pull_rageclicks()
    exc, exc_err = pull_exceptions()
    cvr, cvr_err = pull_cvr_trend()
    inv, inv_err = pull_event_inventory()

    for label, res, err in [
        ("Funnel", funnel, funnel_err), ("Rageclicks", rage, rage_err),
        ("Exceptions", exc, exc_err), ("CVR trend", cvr, cvr_err),
        ("Event inventory", inv, inv_err),
    ]:
        print(f"  {label}: {'OK' if res and rows(res) else ('FAILED — ' + str(err) if err else 'no rows')}")

    L = []
    L.append("# Wave 0 — PostHog Signal")
    L.append("")
    L.append(f"_Pulled: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_  ")
    L.append(f"_Window: {DATE_FROM} → {DATE_TO}_  ")
    L.append(f"_Project: {PROJECT_ID} | Host: {HOST}_")
    L.append("")

    # ── Funnel ──
    L.append("## Funnel (raw event counts — directional, not unique-person)")
    L.append("")
    inv_events = {str(r[0]): int(r[1]) for r in rows(inv)} if rows(inv) else {}
    if funnel and rows(funnel):
        row = rows(funnel)[0]
        L.append("| Step | Event | Count | Step CVR | Drop % |")
        L.append("|------|-------|------:|---------:|-------:|")
        prev = None
        for i, ev in enumerate(FUNNEL_EVENTS):
            cnt = int(row[i]) if i < len(row) and row[i] else 0
            if prev and prev > 0:
                cvr_step, drop = round(100.0 * cnt / prev, 1), round(100.0 * (prev - cnt) / prev, 1)
            else:
                cvr_step, drop = 100.0, 0.0
            L.append(f"| {i+1} | `{ev}` | {cnt:,} | {cvr_step}% | {drop}% |")
            prev = cnt
        # worst step
        counts = [int(row[i]) if i < len(row) and row[i] else 0 for i in range(len(FUNNEL_EVENTS))]
        worst_i, worst_drop = None, 0.0
        for i in range(1, len(counts)):
            if counts[i - 1] > 0:
                d = 100.0 * (counts[i - 1] - counts[i]) / counts[i - 1]
                if d > worst_drop:
                    worst_drop, worst_i = d, i
        if worst_i is not None:
            L.append("")
            L.append(f"**Worst leak:** `{FUNNEL_EVENTS[worst_i-1]}` → `{FUNNEL_EVENTS[worst_i]}` "
                     f"= **{worst_drop:.1f}% drop**. Aim Waves 2–3 here.")
    else:
        L.append(f"**Error:** `{funnel_err}`")
    L.append("")

    # ── Event-name sanity ──
    if inv_events:
        L.append("## Event inventory (top events) — name-mismatch check")
        L.append("")
        L.append("| Event | Count |")
        L.append("|-------|------:|")
        for ev, c in list(inv_events.items())[:15]:
            L.append(f"| `{ev}` | {c:,} |")
        # flag configured funnel events that have zero volume
        missing = [ev for ev in FUNNEL_EVENTS if ev not in inv_events]
        if missing:
            L.append("")
            L.append("> ⚠️ **Funnel events with ZERO volume:** "
                     + ", ".join(f"`{m}`" for m in missing)
                     + ". Either not instrumented or named differently "
                     "(e.g. `add_to_cart` vs `product_added_to_cart`). Any Meta CAPI / "
                     "Klaviyo flow keyed on the missing name is receiving no signal — verify.")
        L.append("")

    # ── CVR trend ──
    L.append("## CVR trend (daily, purchase / pageview)")
    L.append("")
    if cvr and rows(cvr):
        L.append("| Date | Purchases | Pageviews | CVR% |")
        L.append("|------|----------:|----------:|-----:|")
        for r in rows(cvr):
            day = str(r[0])[:10]
            pur = int(r[1]) if r[1] else 0
            pv = int(r[2]) if r[2] else 0
            cvr_pct = float(r[3]) if r[3] else 0.0
            mark = "  ← suspected deploy" if DEPLOY_DATE and day == DEPLOY_DATE else ""
            L.append(f"| {day} | {pur:,} | {pv:,} | {cvr_pct:.3f}%{mark} |")
        if DEPLOY_DATE:
            pre = [float(r[3]) for r in rows(cvr) if r[3] and str(r[0])[:10] < DEPLOY_DATE]
            post = [float(r[3]) for r in rows(cvr) if r[3] and str(r[0])[:10] >= DEPLOY_DATE]
            if pre and post:
                ap, apo = sum(pre) / len(pre), sum(post) / len(post)
                L.append("")
                L.append(f"**Deploy-regression check ({DEPLOY_DATE}):** pre {ap:.3f}% → post {apo:.3f}% "
                         f"= **{apo-ap:+.3f}%**. If CVR fell here while ad CTR/CPM stayed flat, "
                         "the cause is a site deploy, not ads — cross-check theme asset `updated_at` clustering.")
    else:
        L.append(f"**Error:** `{cvr_err}`")
    L.append("")

    # ── Rageclicks ──
    L.append("## Top rageclicks (dead/broken controls surface here)")
    L.append("")
    if rage and rows(rage):
        L.append("| Element text | Page URL | Count |")
        L.append("|--------------|----------|------:|")
        for r in rows(rage)[:12]:
            el = str(r[0])[:80] if r[0] else "(no text)"
            url = str(r[1])[:100] if r[1] else "(unknown)"
            cnt = int(r[2]) if r[2] else 0
            L.append(f"| {el} | {url} | {cnt} |")
    else:
        L.append(f"**Error:** `{rage_err}`")
    L.append("")

    # ── Exceptions ──
    L.append("## JS exceptions on the buy path (silent conversion breakers)")
    L.append("")
    L.append(f"_Benign noise excluded: {', '.join('`'+b+'`' for b in BENIGN)}_")
    L.append("")
    if exc and rows(exc):
        cols = exc.get("columns", [])
        four = len(cols) >= 4
        L.append("| Type | Message | Page URL | Count |" if four else "| Exception | Page URL | Count |")
        L.append("|------|---------|----------|------:|" if four else "|-----------|----------|------:|")
        shown = 0
        for r in rows(exc):
            if four:
                etype = str(r[0])[:50] if r[0] and str(r[0]) not in ("None", "") else "(unknown)"
                emsg = str(r[1])[:70] if r[1] and str(r[1]) not in ("None", "") else "—"
                url = str(r[2])[:90] if r[2] else "(unknown)"
                cnt = int(r[3]) if r[3] else 0
                label = etype if emsg == "—" else emsg
                if is_benign(label) or is_benign(etype):
                    continue
                L.append(f"| {etype} | {emsg} | {url} | {cnt} |")
            else:
                label = str(r[0])[:110] if r[0] and str(r[0]) not in ("None", "") else "(unknown)"
                url = str(r[1])[:90] if len(r) > 1 and r[1] else "(unknown)"
                cnt = int(r[-1]) if r[-1] else 0
                if is_benign(label):
                    continue
                L.append(f"| {label} | {url} | {cnt} |")
            shown += 1
            if shown >= 12:
                break
        if shown == 0:
            L.append("| (all exceptions benign / none in window) | - | - |")
    else:
        L.append(f"**Error:** `{exc_err}`")
    L.append("")

    # ── Key signals ──
    L.append("## Key signals (aim the audit here)")
    L.append("")
    signals = []
    if funnel and rows(funnel):
        counts = [int(rows(funnel)[0][i]) if rows(funnel)[0][i] else 0 for i in range(len(FUNNEL_EVENTS))]
        worst_i, worst_drop = None, 0.0
        for i in range(1, len(counts)):
            if counts[i - 1] > 0:
                d = 100.0 * (counts[i - 1] - counts[i]) / counts[i - 1]
                if d > worst_drop:
                    worst_drop, worst_i = d, i
        if worst_i is not None:
            signals.append(f"Biggest funnel leak: **{FUNNEL_EVENTS[worst_i-1]} → {FUNNEL_EVENTS[worst_i]} "
                           f"({worst_drop:.0f}% drop)** — chase this offer/UX in Waves 2–3.")
    if rage and rows(rage):
        top = rows(rage)[0]
        signals.append(f"Top rageclick: **'{str(top[0])[:50]}'** on `{str(top[1])[:70]}` ({top[2]}×) — "
                       "verify the control actually works in Wave 2.")
    if exc and rows(exc):
        def _row_benign(r):
            return is_benign(r[0]) or (len(r) > 2 and is_benign(r[1]))
        nb = [r for r in rows(exc) if not _row_benign(r)]
        if nb:
            top = nb[0]
            label = " ".join(str(x) for x in top[:2] if x and str(x).strip()) or "(unknown)"
            page = str(top[-2])[:70] if len(top) > 2 else ""
            signals.append(f"Top non-benign JS exception: **'{label[:80]}'** "
                           f"({top[-1]}×) on `{page}` — treat as P1 if it fires on a product/cart/checkout page.")
        else:
            signals.append("No non-benign JS exceptions in window — error guards holding.")
    if not signals:
        signals.append("Insufficient data — check event instrumentation / API key scope; "
                       "fall back to browser sampling in Wave 2.")
    for s in signals:
        L.append(f"- {s}")
    L.append("")
    L.append("---")
    L.append(f"_Generated by `posthog_signal.py` (Wave 0) — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    content = "\n".join(L)
    with open(OUTPUT_FILE, "w") as f:
        f.write(content)
    print(f"\nWritten: {OUTPUT_FILE}\n")
    print(content)


if __name__ == "__main__":
    main()
