"""Optional user-maintained institution preset loader.

The distributed schools.yaml is intentionally empty.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

SCHOOLS_FILE = Path(__file__).resolve().parent.parent / "data" / "schools.yaml"


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in ("", "null", "None"):
        return None
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip('"') for part in inner.split(",")]
    return value


def _load_schools_without_yaml(text: str) -> list[dict[str, Any]]:
    """Read the repository schools.yaml format without requiring PyYAML."""
    schools: list[dict[str, Any]] = []
    current: Optional[dict[str, Any]] = None
    section: Optional[str] = None

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped == "schools:":
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if stripped.startswith("- name:"):
            if current:
                schools.append(current)
            current = {"name": _parse_scalar(stripped.split(":", 1)[1]), "auth": {}}
            section = None
            continue
        if current is None:
            continue
        if indent == 4 and stripped.endswith(":"):
            section = stripped[:-1]
            current.setdefault(section, {})
            continue
        if ":" not in stripped:
            continue

        key, value = stripped.split(":", 1)
        if section and indent >= 6:
            current.setdefault(section, {})[key.strip()] = _parse_scalar(value)
        else:
            section = None
            current[key.strip()] = _parse_scalar(value)

    if current:
        schools.append(current)
    return schools


def load_schools() -> list[dict[str, Any]]:
    """Load institution presets using PyYAML or the built-in minimal parser."""
    if not SCHOOLS_FILE.exists():
        return []
    text = SCHOOLS_FILE.read_text(encoding="utf-8")
    if yaml is None:
        return _load_schools_without_yaml(text)
    data = yaml.safe_load(text)
    return data.get("schools", []) if data else []


def match_school(query: str) -> Optional[dict[str, Any]]:
    """Find an institution using fuzzy matching.

    Match order: exact name, exact alias, then substring.
    Return the matching institution dictionary, or None.
    """
    query = query.strip().lower()
    if not query:
        return None

    schools = load_schools()
    if not schools:
        return None

    # 1. Exact name match
    for s in schools:
        if s["name"].lower() == query:
            return s

    # 2. Exact alias match
    for s in schools:
        for alias in s.get("aliases", []):
            if alias.lower() == query:
                return s

    # 3. Name substring match
    for s in schools:
        if query in s["name"].lower():
            return s

    # 4. Alias substring match
    for s in schools:
        for alias in s.get("aliases", []):
            if query in alias.lower():
                return s

    return None


def list_school_names() -> list[str]:
    """Return all preset institution names."""
    return [s["name"] for s in load_schools()]


if __name__ == "__main__":
    schools = load_schools()
    print(f"Number of user-maintained institution presets: {len(schools)}")
