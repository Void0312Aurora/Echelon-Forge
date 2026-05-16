from __future__ import annotations

import json
import os
from typing import Iterable


DEFAULT_ASSET_REGISTRY_PATH = "examples/viz/assets/registry/default.json"
DEFAULT_ASSET_REGISTRY_ROOTS = ("examples/viz/assets/registry",)


def _to_rel_if_possible(path: str) -> str:
    abs_path = os.path.abspath(path)
    cwd = os.path.abspath(os.getcwd())
    try:
        rel = os.path.relpath(abs_path, cwd)
    except ValueError:
        return abs_path
    if rel.startswith(".."):
        return abs_path
    return rel


def _resolve_registry_path(path: str | None = None) -> str:
    ref = str(path or DEFAULT_ASSET_REGISTRY_PATH).strip()
    if not ref:
        ref = DEFAULT_ASSET_REGISTRY_PATH
    if os.path.isabs(ref):
        return ref
    direct = os.path.abspath(ref)
    if os.path.isfile(direct):
        return direct
    for root in DEFAULT_ASSET_REGISTRY_ROOTS:
        abs_root = os.path.abspath(root)
        candidate = os.path.join(abs_root, ref)
        if os.path.isfile(candidate):
            return candidate
        if not ref.endswith(".json"):
            candidate_json = os.path.join(abs_root, f"{ref}.json")
            if os.path.isfile(candidate_json):
                return candidate_json
    return direct


def list_asset_registries(roots: Iterable[str] | None = None) -> list[dict]:
    found: list[dict] = []
    for root in list(roots or DEFAULT_ASSET_REGISTRY_ROOTS):
        abs_root = os.path.abspath(root)
        if not os.path.isdir(abs_root):
            continue
        for current_root, _dirs, files in os.walk(abs_root):
            for filename in sorted(files):
                if not filename.endswith(".json"):
                    continue
                abs_path = os.path.join(current_root, filename)
                try:
                    with open(abs_path, "r", encoding="utf-8") as handle:
                        data = json.load(handle)
                    if not isinstance(data, dict):
                        raise ValueError("registry root is not a JSON object")
                    found.append(
                        {
                            "path": _to_rel_if_possible(abs_path),
                            "name": str(data.get("name") or os.path.splitext(filename)[0]).strip(),
                            "description": str(data.get("description") or "").strip(),
                            "valid": True,
                        }
                    )
                except Exception as exc:
                    found.append(
                        {
                            "path": _to_rel_if_possible(abs_path),
                            "name": os.path.splitext(filename)[0],
                            "description": f"INVALID REGISTRY: {exc}",
                            "valid": False,
                        }
                    )
    found.sort(key=lambda item: (not bool(item.get("valid", True)), str(item.get("name", "")).lower(), str(item.get("path", ""))))
    return found


def _resolve_asset_path(value: str | None, *, registry_dir: str) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.startswith("/static/"):
        return text
    if os.path.isabs(text):
        return _to_rel_if_possible(text) if os.path.exists(text) else text

    direct = os.path.abspath(text)
    if os.path.exists(direct):
        return _to_rel_if_possible(direct)

    via_registry = os.path.abspath(os.path.join(registry_dir, text))
    if os.path.exists(via_registry):
        return _to_rel_if_possible(via_registry)

    return text


def _normalize_entry(raw: dict, *, registry_dir: str) -> dict:
    match = raw.get("match", {}) if isinstance(raw.get("match"), dict) else {}
    visual = raw.get("visual", {}) if isinstance(raw.get("visual"), dict) else {}

    chase_offset = visual.get("chase_offset", [0.0, 30.0, 80.0])
    if not isinstance(chase_offset, list) or len(chase_offset) != 3:
        chase_offset = [0.0, 30.0, 80.0]

    return {
        "id": str(raw.get("id") or "").strip(),
        "label": str(raw.get("label") or "").strip(),
        "match": {
            "unit_type": str(match.get("unit_type") or "").strip(),
            "platform_type_patterns": [str(x).strip() for x in list(match.get("platform_type_patterns", []) or []) if str(x).strip()],
            "name_patterns": [str(x).strip() for x in list(match.get("name_patterns", []) or []) if str(x).strip()],
            "service_profiles": [str(x).strip() for x in list(match.get("service_profiles", []) or []) if str(x).strip()],
        },
        "visual": {
            "asset_path": _resolve_asset_path(visual.get("asset_path"), registry_dir=registry_dir),
            "scale": float(visual.get("scale", 1.0) or 1.0),
            "yaw_correction_deg": float(visual.get("yaw_correction_deg", 0.0) or 0.0),
            "waterline_offset_m": float(visual.get("waterline_offset_m", 0.0) or 0.0),
            "chase_offset": [float(chase_offset[0]), float(chase_offset[1]), float(chase_offset[2])],
            "fallback_hull_length_m": float(visual.get("fallback_hull_length_m", 160.0) or 160.0),
            "fallback_hull_beam_m": float(visual.get("fallback_hull_beam_m", 24.0) or 24.0),
            "fallback_hull_height_m": float(visual.get("fallback_hull_height_m", 12.0) or 12.0),
            "fallback_super_length_m": float(visual.get("fallback_super_length_m", 56.0) or 56.0),
            "fallback_super_beam_m": float(visual.get("fallback_super_beam_m", 16.0) or 16.0),
            "fallback_super_height_m": float(visual.get("fallback_super_height_m", 18.0) or 18.0),
            "fallback_super_offset_x_m": float(visual.get("fallback_super_offset_x_m", -8.0) or -8.0),
            "fallback_super_offset_y_m": float(visual.get("fallback_super_offset_y_m", 18.0) or 18.0),
        },
        "realism": {
            "substitute_for": str(raw.get("substitute_for") or "").strip(),
            "realism_note": str(raw.get("realism_note") or "").strip(),
        },
        "show_in_2d_as": str(raw.get("show_in_2d_as") or "").strip(),
        "show_sensor_ring": bool(raw.get("show_sensor_ring", False)),
        "render_priority": int(raw.get("render_priority", 100)),
    }


def load_asset_registry(path: str | None = None) -> dict:
    abs_path = _resolve_registry_path(path)
    with open(abs_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Asset registry must be a JSON object: {abs_path}")

    registry_dir = os.path.dirname(abs_path)
    entries = [_normalize_entry(raw, registry_dir=registry_dir) for raw in list(data.get("entries", []) or []) if isinstance(raw, dict)]

    return {
        "path": _to_rel_if_possible(abs_path),
        "name": str(data.get("name") or "default").strip(),
        "description": str(data.get("description") or "").strip(),
        "entries": entries,
    }
