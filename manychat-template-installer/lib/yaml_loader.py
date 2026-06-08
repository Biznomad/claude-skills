"""YAML loader + validator for the ManyChat installer.

Fails fast and loud if required keys are missing. The schema is intentionally
strict so we can't accidentally pollute a client account with placeholder text
left over from the master template.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

REQUIRED_TOP_KEYS = (
    "client_slug",
    "template_url",
    "target_page_name",
    "placeholders",
    "flows",
)

REQUIRED_PLACEHOLDERS = (
    "brand_name",
    "owner_first_name",
    "shop_url",
    "support_email",
)


class ConfigError(ValueError):
    """Raised when a YAML config is malformed or missing required keys."""


def load_config(path: str | Path) -> dict[str, Any]:
    """Load + validate a client YAML config.

    Raises ConfigError on any structural problem. Returns the dict otherwise.
    """
    if yaml is None:
        raise RuntimeError("Install pyyaml first: pip install pyyaml")

    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise ConfigError(f"Config not found: {p}")

    with p.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        raise ConfigError(f"Top-level YAML must be a mapping, got {type(cfg).__name__}")

    # Required top-level keys
    missing = [k for k in REQUIRED_TOP_KEYS if k not in cfg]
    if missing:
        raise ConfigError(f"Missing required top-level keys: {missing}")

    # client_slug sanity: must match filename to prevent foot-guns
    stem = p.stem
    if cfg["client_slug"] != stem:
        raise ConfigError(
            f"client_slug '{cfg['client_slug']}' does not match filename '{stem}'. "
            "Rename the file or update the YAML to enforce per-client isolation."
        )

    # template_url sanity
    if not str(cfg["template_url"]).startswith("https://"):
        raise ConfigError(f"template_url must be https://, got: {cfg['template_url']!r}")

    # Required placeholders
    placeholders = cfg.get("placeholders") or {}
    if not isinstance(placeholders, dict):
        raise ConfigError("`placeholders` must be a mapping")
    missing_ph = [k for k in REQUIRED_PLACEHOLDERS if k not in placeholders]
    if missing_ph:
        raise ConfigError(f"Missing required placeholders: {missing_ph}")

    # Optional shapes
    if "flows" in cfg and not isinstance(cfg["flows"], list):
        raise ConfigError("`flows` must be a list of flow display names")
    if "tag_renames" in cfg and not isinstance(cfg["tag_renames"], dict):
        raise ConfigError("`tag_renames` must be a mapping of old -> new")
    if "field_renames" in cfg and not isinstance(cfg["field_renames"], dict):
        raise ConfigError("`field_renames` must be a mapping of old -> new")
    if "post_install_actions" in cfg and not isinstance(cfg["post_install_actions"], list):
        raise ConfigError("`post_install_actions` must be a list of action dicts")

    return cfg
