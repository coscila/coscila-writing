"""Connectivity self-check module.

Run lightweight connectivity checks before downloads; cache results for 10 minutes.
Provide specific troubleshooting advice on failure.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from config import CONFIG_DIR, load_config
from validators import validate_carsi_entry, validate_sso_domain

# Cache file
CACHE_FILE = CONFIG_DIR / "health_cache.json"
CACHE_TTL = 600  # 10 minutes


def _load_cache() -> Optional[dict[str, Any]]:
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_cache(data: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _clear_cache() -> None:
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()


def _diagnose_failure(cfg: dict[str, Any]) -> list[str]:
    """Provide troubleshooting advice based on configuration."""
    suggestions: list[str] = []
    auth = cfg.get("auth", {})
    sso_domain = auth.get("sso_domain", "")
    carsi_entry = auth.get("carsi_entry", "")

    suggestions.append("Possible causes and suggestions: ")

    if sso_domain:
        suggestions.append(
            f"1. Check network access: are you on campus or connected to the VPN?"
            f"Off-campus access to  {sso_domain} may require a VPN."
        )
    if carsi_entry:
        suggestions.append(
            f"2. The CARSI entry may have changed: visit https://www.carsi.edu.cn/ "
            f"to verify the current institution entry, or request reconfiguration."
        )
    suggestions.append("3. Institutional authentication may be temporarily unavailable; retry later.")
    suggestions.append("4. If failures persist, request reconfiguration to correct the parameters.")

    return suggestions


def health_check(force: bool = False) -> dict[str, Any]:
    """Run connectivity checks.

    Parameters:
        force: Whether to bypass cached results

    Returns:
        {
            "ok": bool,
            "checked_at": str,
            "cached": bool,
            "details": [...],
            "suggestions": [...]  # Only on failure
        }
    """
    # Check cached results
    if not force:
        cache = _load_cache()
        if cache and (time.time() - cache.get("checked_at_ts", 0)) < CACHE_TTL:
            cache["cached"] = True
            return cache

    cfg = load_config()
    if cfg is None:
        return {
            "ok": False,
            "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cached": False,
            "details": ["No configuration found; run the configuration wizard first"],
            "suggestions": ["Request institution configuration or use /reconfig to open the wizard"],
        }

    details: list[str] = []
    all_ok = True

    auth = cfg.get("auth", {})
    sso_domain = auth.get("sso_domain", "")
    carsi_entry = auth.get("carsi_entry", "")

    # 1. Probe the SSO domain
    if sso_domain:
        ok, msg = validate_sso_domain(sso_domain)
        details.append(f"[SSO] {msg}")
        if not ok:
            all_ok = False
    else:
        details.append("[SSO] sso_domain is not configured")
        all_ok = False

    # 2. Probe the CARSI entry if configured
    if carsi_entry:
        ok, msg = validate_carsi_entry(carsi_entry)
        details.append(f"[CARSI] {msg}")
        if not ok:
            all_ok = False
    else:
        details.append("[CARSI] CARSI entry is not configured (ignore if the institution does not use CARSI)")

    result: dict[str, Any] = {
        "ok": all_ok,
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checked_at_ts": time.time(),
        "cached": False,
        "details": details,
    }

    if not all_ok:
        result["suggestions"] = _diagnose_failure(cfg)

    # Write cached results
    _save_cache(result)

    return result


def clear_cache() -> None:
    """Clear the self-check cache after configuration changes."""
    _clear_cache()


if __name__ == "__main__":
    result = health_check(force=True)
    print(f"Self-check result: {'passed' if result['ok'] else 'failed'}")
    print(f"Checked at: {result['checked_at']}")
    for d in result.get("details", []):
        print(f"  {d}")
    for s in result.get("suggestions", []):
        print(f"  {s}")
