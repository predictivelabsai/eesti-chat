"""Single source of truth for the app version.

The repo-root ``VERSION`` file holds two lines: a semver on line 1 and the ISO
release date on line 2. Bump it (and prepend a ``docs/change_log.md`` entry) on
every change — see AGENTS.md. The version also cache-busts static assets.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"


@lru_cache(maxsize=1)
def _lines() -> list[str]:
    try:
        return [ln.strip() for ln in _VERSION_FILE.read_text().strip().splitlines()]
    except Exception:
        return []


def app_version() -> str:
    ls = _lines()
    return ls[0] if ls and ls[0] else "0.0.0"


def app_version_date() -> str:
    ls = _lines()
    return ls[1] if len(ls) > 1 and ls[1] else ""
