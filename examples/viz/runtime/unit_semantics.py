"""Echelon semantics for viz unit payloads.

Operational/strategic-scale views aggregate by echelon instead of drawing
every platform. The runtime does not model echelon as a first-class field
yet, so the only honest source today is the echelon token embedded in the
platform type name (e.g. ``Ground_Platoon_MVP``). This module pins that
inference so the unit contract can carry ``echelon`` from day one; when the
engine grows a native echelon field this inference becomes a fallback.
"""

from __future__ import annotations

# Ordered most-specific-first so e.g. "FIRE_TEAM" wins over "TEAM"-like noise.
_ECHELON_TOKENS: tuple[tuple[str, str], ...] = (
    ("FIRE_TEAM", "fire_team"),
    ("FIRETEAM", "fire_team"),
    ("SQUAD", "squad"),
    ("SECTION", "section"),
    ("PLATOON", "platoon"),
    ("COMPANY", "company"),
    ("BATTERY", "battery"),
    ("BATTALION", "battalion"),
    ("REGIMENT", "regiment"),
    ("BRIGADE", "brigade"),
    ("DIVISION", "division"),
    ("CORPS", "corps"),
)


def infer_echelon(type_name: str | None, unit_name: str | None = None) -> str:
    """Best-effort echelon from type/unit naming; empty string when unknown."""
    for source in (type_name, unit_name):
        text = str(source or "").upper()
        if not text:
            continue
        for token, echelon in _ECHELON_TOKENS:
            if token in text:
                return echelon
    return ""


__all__ = ["infer_echelon"]
