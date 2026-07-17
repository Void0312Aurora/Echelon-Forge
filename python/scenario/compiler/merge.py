from __future__ import annotations

import json
import os
from typing import Any

from .clone import _clone_scenario_value
from .validation import validate_scenario_compiler_shape


def _merge_prefab_data(target: dict[str, Any], prefab: dict[str, Any]) -> None:
    if "zones" in prefab:
        if "environment" not in target or not isinstance(target.get("environment"), dict):
            target["environment"] = {}
        current_zones = target["environment"].get("zones", [])
        if not isinstance(current_zones, list):
            current_zones = []
        current_zones.extend(_clone_scenario_value(prefab["zones"]))
        target["environment"]["zones"] = current_zones

    if "entities" in prefab:
        current_entities = target.get("entities", [])
        if not isinstance(current_entities, list):
            current_entities = []
        current_entities.extend(_clone_scenario_value(prefab["entities"]))
        target["entities"] = current_entities


def _compile_merged_scenario_data(
    raw_scenario_data: dict[str, Any],
    *,
    project_root: str,
) -> tuple[dict[str, Any], tuple[str, ...], tuple[str, ...]]:
    merged = _clone_scenario_value(raw_scenario_data)
    imports = merged.get("imports", None)
    imported_files: list[str] = []
    warnings: list[str] = []

    if isinstance(imports, list):
        for imp in imports:
            if not isinstance(imp, dict):
                continue
            rel_path = imp.get("file")
            if not rel_path:
                continue

            full_path = os.path.abspath(os.path.join(project_root, str(rel_path)))
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Scenario import file not found: {full_path}")

            with open(full_path, "r", encoding="utf-8") as handle:
                prefab = json.load(handle)
            if not isinstance(prefab, dict):
                raise ValueError(
                    f"Imported scenario prefab must contain a JSON object: {full_path}"
                )
            validate_scenario_compiler_shape(
                prefab,
                source_path=full_path,
                context="imported scenario prefab",
            )

            _merge_prefab_data(merged, prefab)
            imported_files.append(full_path)

    return merged, tuple(imported_files), tuple(warnings)


__all__ = [
    "_merge_prefab_data",
    "_compile_merged_scenario_data",
]
