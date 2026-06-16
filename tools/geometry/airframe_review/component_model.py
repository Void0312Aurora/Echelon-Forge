"""Damage component model helpers used by airframe review reports."""

from __future__ import annotations

from typing import Any


def damage_component_names(aircraft: dict[str, Any]) -> list[str]:
  names: list[str] = []
  for hitbox in aircraft.get("damage_model", {}).get("hitboxes", []):
    for component in hitbox.get("components", []):
      component_name = component.get("name")
      if component_name:
        names.append(component_name)
  return names


def duplicate_names(names: list[str]) -> list[str]:
  counts: dict[str, int] = {}
  for name in names:
    counts[name] = counts.get(name, 0) + 1
  return sorted(name for name, count in counts.items() if count > 1)
