#!/usr/bin/env python3
"""
ads-compliance-check — pre-flight gate for ad publish.

Checks performed (in order):
  1. Manifest schema / required-fields validation
  2. Meta 72-hour blackout (per-campaign last-change timestamp + 20% budget cap)
  3. Copy banned-phrase scan (regex, niche-aware)
  4. Required disclaimers per niche
  5. Per-platform policy red-flags
  6. Image / aspect-ratio checks per platform spec
  7. Vision-LLM brand-fidelity scan  [TODO: wire up to Gemini/Claude vision]

Exit codes:
  0  PASS — safe to publish
  1  FAIL — fix list printed
  2  Manifest invalid or missing

Usage:
  python compliance-check.py [path/to/ads-manifest.json] [--record] [--json]

State file:
  ~/.claude/skills/ads-compliance-check/.state/last-changes.json
  Schema: { "<platform>:<account_id>:<campaign_id>": "<iso8601 utc>" }

Only stdlib + (optional) Pillow / requests if available. The script must run
without any external pip installs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Optional imports — degrade gracefully
try:
    from PIL import Image  # type: ignore
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

SKILL_DIR = Path(__file__).resolve().parent
STATE_DIR = SKILL_DIR / ".state"
STATE_FILE = STATE_DIR / "last-changes.json"
BANNED_FILE = SKILL_DIR / "BANNED_PHRASES.json"

# ---------------------------------------------------------------------------
# Platform specs
# ---------------------------------------------------------------------------

PLATFORM_IMAGE_SPECS: dict[str, list[dict[str, Any]]] = {
    "meta": [
        {"name": "feed-square", "w": 1080, "h": 1080, "ratio": 1.0, "tol": 0.02},
        {"name": "feed-portrait", "w": 1080, "h": 1350, "ratio": 4 / 5, "tol": 0.02},
        {"name": "story-reel", "w": 1080, "h": 1920, "ratio": 9 / 16, "tol": 0.02},
    ],
    "google": [
        {"name": "square", "w": 1200, "h": 1200, "ratio": 1.0, "tol": 0.02},
        {"name": "landscape", "w": 1200, "h": 628, "ratio": 1.91, "tol": 0.03},
        {"name": "portrait", "w": 960, "h": 1200, "ratio": 0.8, "tol": 0.03},
    ],
    "tiktok": [
        {"name": "vertical", "w": 1080, "h": 1920, "ratio": 9 / 16, "tol": 0.02},
    ],
    "linkedin": [
        {"name": "landscape", "w": 1200, "h": 627, "ratio": 1.91, "tol": 0.03},
        {"name": "square", "w": 1200, "h": 1200, "ratio": 1.0, "tol": 0.02},
    ],
    "microsoft": [
        {"name": "landscape", "w": 1200, "h": 628, "ratio": 1.91, "tol": 0.03},
    ],
}

PLATFORM_BLACKOUT_HOURS: dict[str, int] = {
    "meta": 72,
    "google": 24,
    "tiktok": 48,
    "linkedin": 48,
    "microsoft": 24,
}

PLATFORM_MAX_BUDGET_DELTA_PCT: dict[str, float] = {
    "meta": 0.20,
    "google": 0.30,
    "tiktok": 0.25,
    "linkedin": 0.25,
    "microsoft": 0.30,
}

# Platform-specific extra niche layers automatically applied
PLATFORM_AUTO_NICHE: dict[str, list[str]] = {
    "tiktok": ["tiktok_extra"],
}

# Required disclaimers per niche
NICHE_REQUIRED_DISCLAIMERS: dict[str, list[str]] = {
    "health": [
        "these statements have not been evaluated by the fda",
    ],
    "finance": [
        "terms apply",
    ],
    "real_estate": [
        "equal housing opportunity",
    ],
}

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


class CheckResult:
    __slots__ = ("name", "passed", "details", "fixes")

    def __init__(self, name: str, passed: bool, details: str = "", fixes: list[str] | None = None):
        self.name = name
        self.passed = passed
        self.details = details
        self.fixes = fixes or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "details": self.details,
            "fixes": self.fixes,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_iso(ts: str) -> dt.datetime:
    # Accept both "...Z" and "+00:00"
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(ts)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def load_state() -> dict[str, str]:
    if not STATE_FILE.exists():
        return {}
    try:
        return load_json(STATE_FILE)
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state: dict[str, str]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)


def state_key(change: dict[str, Any]) -> str:
    return f"{change['platform']}:{change.get('account_id', '?')}:{change.get('campaign_id', '?')}"


def aspect_ratio_match(spec: dict[str, Any], w: int, h: int) -> bool:
    if h == 0:
        return False
    actual = w / h
    return abs(actual - spec["ratio"]) <= spec["tol"]


def all_copy_text(change: dict[str, Any]) -> str:
    """Flatten every string in the change.copy block into one searchable blob."""
    copy = change.get("copy", {}) or {}
    chunks: list[str] = []
    for value in copy.values():
        if isinstance(value, str):
            chunks.append(value)
        elif isinstance(value, list):
            chunks.extend(str(v) for v in value if isinstance(v, (str, int, float)))
        elif isinstance(value, dict):
            chunks.extend(str(v) for v in value.values() if isinstance(v, (str, int, float)))
    return "\n".join(chunks)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_manifest(manifest: dict[str, Any]) -> CheckResult:
    fixes: list[str] = []
    if "changes" not in manifest or not isinstance(manifest["changes"], list):
        fixes.append("Manifest must contain a top-level 'changes' array.")
    else:
        for i, change in enumerate(manifest["changes"]):
            missing = [k for k in ("platform", "change_type") if k not in change]
            if missing:
                fixes.append(f"changes[{i}] missing required keys: {missing}")
            if change.get("platform") not in PLATFORM_IMAGE_SPECS:
                fixes.append(
                    f"changes[{i}].platform '{change.get('platform')}' is not supported. "
                    f"Allowed: {sorted(PLATFORM_IMAGE_SPECS)}"
                )
            if change.get("change_type") not in {"new", "edit", "pause", "resume"}:
                fixes.append(
                    f"changes[{i}].change_type must be one of new|edit|pause|resume"
                )
    return CheckResult(
        name="manifest.schema",
        passed=not fixes,
        details="Manifest structurally valid." if not fixes else "Manifest invalid.",
        fixes=fixes,
    )


def check_blackout(change: dict[str, Any], state: dict[str, str], now: dt.datetime) -> CheckResult:
    platform = change["platform"]
    hours = PLATFORM_BLACKOUT_HOURS.get(platform, 24)
    key = state_key(change)
    last = state.get(key)
    if change["change_type"] == "new":
        return CheckResult(
            name=f"blackout[{change.get('id', key)}]",
            passed=True,
            details=f"New campaign — no prior change on record for {key}.",
        )
    if not last:
        return CheckResult(
            name=f"blackout[{change.get('id', key)}]",
            passed=True,
            details=f"No prior change recorded for {key} — treating as cold start.",
        )
    last_dt = parse_iso(last)
    elapsed = now - last_dt
    elapsed_hours = elapsed.total_seconds() / 3600
    if elapsed_hours < hours:
        remaining = hours - elapsed_hours
        return CheckResult(
            name=f"blackout[{change.get('id', key)}]",
            passed=False,
            details=(
                f"{platform} blackout: last change on {key} was {elapsed_hours:.1f}h ago "
                f"(window = {hours}h). Wait another {remaining:.1f}h."
            ),
            fixes=[
                f"Defer this change until {(last_dt + dt.timedelta(hours=hours)).isoformat()}.",
                "If ROAS<0.5x AND spend>2x daily target, an emergency pause is allowed — "
                "document the reason in the manifest 'notes' field.",
            ],
        )
    return CheckResult(
        name=f"blackout[{change.get('id', key)}]",
        passed=True,
        details=f"{platform} blackout cleared — {elapsed_hours:.1f}h since last change ({hours}h required).",
    )


def check_budget_delta(change: dict[str, Any]) -> CheckResult:
    budget = change.get("budget")
    platform = change["platform"]
    max_pct = PLATFORM_MAX_BUDGET_DELTA_PCT.get(platform, 0.20)
    if not budget:
        return CheckResult(
            name=f"budget[{change.get('id', '?')}]",
            passed=True,
            details="No budget change in this manifest entry.",
        )
    prev = float(budget.get("previous_daily_usd") or 0)
    new = float(budget.get("new_daily_usd") or 0)
    if change["change_type"] == "new" or prev == 0:
        return CheckResult(
            name=f"budget[{change.get('id', '?')}]",
            passed=True,
            details=f"New campaign at ${new}/day — no prior budget to compare.",
        )
    delta = (new - prev) / prev
    if abs(delta) > max_pct:
        direction = "increase" if delta > 0 else "decrease"
        allowed = prev * (1 + max_pct) if delta > 0 else prev * (1 - max_pct)
        return CheckResult(
            name=f"budget[{change.get('id', '?')}]",
            passed=False,
            details=(
                f"{platform} budget {direction} {delta*100:+.1f}% exceeds cap of "
                f"{max_pct*100:.0f}% (${prev} -> ${new})."
            ),
            fixes=[
                f"Reduce target to ${allowed:.2f}/day or less for this adjustment.",
                "Stage the change in two steps separated by the blackout window.",
            ],
        )
    return CheckResult(
        name=f"budget[{change.get('id', '?')}]",
        passed=True,
        details=f"Budget delta {delta*100:+.1f}% within ±{max_pct*100:.0f}% cap.",
    )


def _compile_phrases(phrases: list[str]) -> list[re.Pattern[str]]:
    compiled: list[re.Pattern[str]] = []
    for p in phrases:
        # Wrap in word boundaries when the phrase looks like plain words
        pattern = p
        if not (pattern.startswith("\\b") or pattern.startswith("(") or pattern.startswith("[")):
            pattern = r"\b" + pattern + r"\b"
        try:
            compiled.append(re.compile(pattern, re.IGNORECASE))
        except re.error:
            # Fall back to a literal match if the entry isn't a valid regex
            compiled.append(re.compile(re.escape(p), re.IGNORECASE))
    return compiled


def _collect_phrases(banned: dict[str, Any], niches: list[str]) -> tuple[list[re.Pattern[str]], dict[str, str]]:
    phrases: list[str] = list(banned.get("common", []))
    fix_hints: dict[str, str] = {}
    for niche in niches:
        bucket = banned.get(niche)
        if not bucket:
            continue
        if isinstance(bucket, dict):
            phrases.extend(bucket.get("phrases", []))
            if "fix_hint" in bucket:
                for p in bucket.get("phrases", []):
                    fix_hints[p] = bucket["fix_hint"]
        elif isinstance(bucket, list):
            phrases.extend(bucket)
    return _compile_phrases(phrases), fix_hints


def check_copy(change: dict[str, Any], manifest: dict[str, Any], banned: dict[str, Any]) -> CheckResult:
    text = all_copy_text(change)
    if not text.strip():
        return CheckResult(
            name=f"copy[{change.get('id', '?')}]",
            passed=True,
            details="No copy in this change.",
        )

    niches = list(manifest.get("niche", []))
    niches.extend(PLATFORM_AUTO_NICHE.get(change["platform"], []))
    patterns, fix_hints = _collect_phrases(banned, niches)

    hits: list[tuple[str, str]] = []
    for pat in patterns:
        m = pat.search(text)
        if m:
            hits.append((pat.pattern, m.group(0)))

    if hits:
        fixes = [
            f"Remove or rephrase: '{matched}' (pattern: {pat})."
            + (f" Hint: {fix_hints[pat]}" if pat in fix_hints else "")
            for pat, matched in hits
        ]
        return CheckResult(
            name=f"copy[{change.get('id', '?')}]",
            passed=False,
            details=f"Banned phrases detected ({len(hits)}).",
            fixes=fixes,
        )
    return CheckResult(
        name=f"copy[{change.get('id', '?')}]",
        passed=True,
        details=f"Copy clean against {len(patterns)} patterns.",
    )


def check_disclaimers(change: dict[str, Any], manifest: dict[str, Any]) -> CheckResult:
    niches = manifest.get("niche", [])
    required: list[str] = []
    for niche in niches:
        required.extend(NICHE_REQUIRED_DISCLAIMERS.get(niche, []))
    if not required:
        return CheckResult(
            name=f"disclaimers[{change.get('id', '?')}]",
            passed=True,
            details="No niche disclaimers required.",
        )
    present_raw = change.get("disclaimers_present", []) or []
    present_blob = "\n".join(present_raw).lower()
    # Also check copy block as a fallback — disclaimer may live inline
    present_blob += "\n" + all_copy_text(change).lower()
    missing = [d for d in required if d not in present_blob]
    if missing:
        return CheckResult(
            name=f"disclaimers[{change.get('id', '?')}]",
            passed=False,
            details=f"Missing required disclaimers: {missing}",
            fixes=[f"Add disclaimer to ad copy or 'disclaimers_present' array: \"{d}\"" for d in missing],
        )
    return CheckResult(
        name=f"disclaimers[{change.get('id', '?')}]",
        passed=True,
        details=f"All {len(required)} required disclaimers present.",
    )


def check_images(change: dict[str, Any]) -> CheckResult:
    platform = change["platform"]
    specs = PLATFORM_IMAGE_SPECS.get(platform, [])
    paths = change.get("creative_paths") or []
    declared = change.get("image_spec") or {}

    if not paths:
        return CheckResult(
            name=f"images[{change.get('id', '?')}]",
            passed=True,
            details="No creative_paths in this change (copy-only).",
        )

    fixes: list[str] = []
    details: list[str] = []

    for p in paths:
        path = Path(p).expanduser()
        if not path.exists():
            fixes.append(f"Creative file not found: {path}")
            continue

        ext = path.suffix.lower()
        if ext in {".mp4", ".mov", ".webm", ".m4v", ".avi"}:
            # Video: trust the declared image_spec or skip
            if declared.get("width") and declared.get("height"):
                w, h = int(declared["width"]), int(declared["height"])
                if not any(aspect_ratio_match(s, w, h) for s in specs):
                    fixes.append(
                        f"{path.name}: declared {w}x{h} does not match any {platform} spec "
                        f"({[s['name'] for s in specs]})"
                    )
                else:
                    details.append(f"{path.name}: video declared {w}x{h} matches platform spec.")
            else:
                details.append(f"{path.name}: video — declared dimensions missing, manual review needed.")
            continue

        if not HAVE_PIL:
            details.append(
                f"{path.name}: Pillow not installed — skipping pixel-level check (declared dims used)."
            )
            if declared.get("width") and declared.get("height"):
                w, h = int(declared["width"]), int(declared["height"])
                if not any(aspect_ratio_match(s, w, h) for s in specs):
                    fixes.append(
                        f"{path.name}: declared {w}x{h} does not match any {platform} spec."
                    )
            continue

        try:
            with Image.open(path) as img:
                w, h = img.size
            if not any(aspect_ratio_match(s, w, h) for s in specs):
                fixes.append(
                    f"{path.name}: {w}x{h} (ratio {w/h:.3f}) does not match any {platform} spec "
                    f"({[(s['name'], s['ratio']) for s in specs]})"
                )
            else:
                matched = next(s for s in specs if aspect_ratio_match(s, w, h))
                details.append(f"{path.name}: {w}x{h} ✓ ({platform}/{matched['name']})")
        except Exception as exc:
            fixes.append(f"{path.name}: failed to open image — {exc}")

    return CheckResult(
        name=f"images[{change.get('id', '?')}]",
        passed=not fixes,
        details=" | ".join(details) if details else "No image checks performed.",
        fixes=fixes,
    )


def check_brand_fidelity_vision(change: dict[str, Any]) -> CheckResult:
    """
    TODO: Wire up to a vision LLM (Gemini 2.5 Pro or Claude Sonnet vision) to verify:
      - HV logo presence on demo composites
      - Mason jar shape (NOT pill bottle / tall jam jar)
      - Gel liquid colors per SKU (Pineapple Skies = teal, not yellow, etc.)
      - Black cap on Black Gold Gummies (not gold)
      - Two SEPARATE badges on gummy bottom
      - Greek-key border presence
      - Required disclaimer overlay legibility

    Env var detection order:
      ANTHROPIC_API_KEY  -> use Claude vision
      GOOGLE_API_KEY     -> use Gemini vision
      (none)             -> SKIP and return PASS with TODO note

    Implementation sketch (left out intentionally — needs prompt engineering + cost gate):
      1. For each image / first-frame of video, encode base64.
      2. POST to model with a structured rubric (see HV brand-compliance memory).
      3. Parse JSON response { violations: [...] } — any violation -> FAIL.
    """
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_google = bool(os.environ.get("GOOGLE_API_KEY"))
    paths = change.get("creative_paths") or []

    if not paths:
        return CheckResult(
            name=f"brand_fidelity[{change.get('id', '?')}]",
            passed=True,
            details="No creatives to scan.",
        )

    if not (has_anthropic or has_google):
        return CheckResult(
            name=f"brand_fidelity[{change.get('id', '?')}]",
            passed=True,
            details=(
                "Vision LLM not configured (no ANTHROPIC_API_KEY or GOOGLE_API_KEY). "
                "SKIPPING — TODO: implement vision call. Manually verify Mason jar, gel colors, "
                "logo composite, badge layout per feedback_hv_brand_compliance.md."
            ),
        )

    # TODO: real implementation — return PASS for now with a clear note.
    provider = "anthropic" if has_anthropic else "google"
    return CheckResult(
        name=f"brand_fidelity[{change.get('id', '?')}]",
        passed=True,
        details=f"Vision check stubbed ({provider} key found). TODO: wire vision call.",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run(manifest_path: Path, record: bool, json_out: bool) -> int:
    if not manifest_path.exists():
        msg = f"Manifest not found: {manifest_path}"
        print(msg, file=sys.stderr)
        return 2

    try:
        manifest = load_json(manifest_path)
    except json.JSONDecodeError as exc:
        print(f"Manifest is not valid JSON: {exc}", file=sys.stderr)
        return 2

    try:
        banned = load_json(BANNED_FILE)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Failed to load BANNED_PHRASES.json: {exc}", file=sys.stderr)
        return 2

    state = load_state()
    now = utc_now()

    results: list[CheckResult] = []

    schema = check_manifest(manifest)
    results.append(schema)
    if not schema.passed:
        _emit(results, json_out)
        return 1

    for change in manifest["changes"]:
        results.append(check_blackout(change, state, now))
        results.append(check_budget_delta(change))
        results.append(check_copy(change, manifest, banned))
        results.append(check_disclaimers(change, manifest))
        results.append(check_images(change))
        results.append(check_brand_fidelity_vision(change))

    overall_pass = all(r.passed for r in results)
    _emit(results, json_out)

    if record and overall_pass:
        for change in manifest["changes"]:
            state[state_key(change)] = now.isoformat()
        save_state(state)
        if not json_out:
            print(f"\n[state] recorded {len(manifest['changes'])} changes to {STATE_FILE}")

    return 0 if overall_pass else 1


def _emit(results: list[CheckResult], json_out: bool) -> None:
    if json_out:
        payload = {
            "overall_pass": all(r.passed for r in results),
            "checks": [r.to_dict() for r in results],
        }
        print(json.dumps(payload, indent=2))
        return

    print("=" * 72)
    print("  ads-compliance-check report")
    print("=" * 72)
    for r in results:
        badge = "PASS" if r.passed else "FAIL"
        print(f"  [{badge}] {r.name}: {r.details}")
        for fix in r.fixes:
            print(f"         - fix: {fix}")
    overall = all(r.passed for r in results)
    print("-" * 72)
    print(f"  OVERALL: {'PASS — safe to publish' if overall else 'FAIL — do NOT publish'}")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="ads-compliance-check pre-flight gate")
    parser.add_argument(
        "manifest",
        nargs="?",
        default="./ads-manifest.json",
        help="Path to ads-manifest.json (default ./ads-manifest.json)",
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="On PASS, write current UTC timestamp to state file for every campaign in the manifest.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the human report.",
    )
    args = parser.parse_args()

    return run(Path(args.manifest).expanduser().resolve(), args.record, args.json)


if __name__ == "__main__":
    sys.exit(main())
