from __future__ import annotations

import json
import os
from typing import Iterable

from examples.viz.runtime.action_utils import normalize_fixed_action


DEFAULT_PROFILE_ROOTS = ("examples/viz/profiles",)
SESSION_OVERRIDE_FIELDS = {
    "model",
    "scripted",
    "train_config",
    "pause_on_done",
    "seed",
    "algo",
    "include_proprio",
    "mission_obs_mode",
    "visual_downsample",
    "visual_update_interval",
    "action_mode",
    "fixed_action",
    "zero_randomization",
}
TACTICAL_WORKSPACE_ALIASES = {
    "cop": "cop",
    "common": "cop",
    "commonpicture": "cop",
    "commonoperationalpicture": "cop",
    "env": "environment",
    "environment": "environment",
    "areas": "environment",
    "track": "tracks",
    "tracks": "tracks",
    "sensor": "tracks",
    "sensors": "tracks",
    "sensorlinks": "tracks",
    "3d": "inspect3d",
    "inspect3d": "inspect3d",
    "3dinspect": "inspect3d",
    "modelinspect": "inspect3d",
}
TACTICAL_LAYER_ALIASES = {
    "env": "environment",
    "environment": "environment",
    "route": "route",
    "routes": "route",
    "waypoints": "route",
    "trail": "trails",
    "trails": "trails",
    "track": "tracks",
    "tracks": "tracks",
    "sensortrack": "tracks",
    "sensortracks": "tracks",
    "ring": "sensorRings",
    "rings": "sensorRings",
    "sensorring": "sensorRings",
    "sensorrings": "sensorRings",
    "datalink": "datalinks",
    "datalinks": "datalinks",
    "link": "datalinks",
    "links": "datalinks",
    "weapon": "weapons",
    "weapons": "weapons",
    "effect": "weapons",
    "effects": "weapons",
}


def _iter_profile_roots(roots: Iterable[str] | None = None) -> list[str]:
    out: list[str] = []
    for root in list(roots or DEFAULT_PROFILE_ROOTS):
        abs_root = os.path.abspath(root)
        if os.path.isdir(abs_root):
            out.append(abs_root)
    return out


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


def _resolve_path(value: str | None, *, profile_dir: str) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if os.path.isabs(text):
        return _to_rel_if_possible(text) if os.path.exists(text) else text

    direct = os.path.abspath(text)
    if os.path.exists(direct):
        return _to_rel_if_possible(direct)

    via_profile = os.path.abspath(os.path.join(profile_dir, text))
    if os.path.exists(via_profile):
        return _to_rel_if_possible(via_profile)

    return text


def _compact_ui_key(value: object) -> str:
    text = str(value or "").strip()
    return "".join(ch for ch in text.lower() if ch.isalnum())


def _normalize_ui_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    if isinstance(value, float) and value in {0.0, 1.0}:
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on", "enabled"}:
            return True
        if text in {"0", "false", "no", "off", "disabled"}:
            return False
    return None


def _normalize_tactical_workspace(value: object) -> str | None:
    return TACTICAL_WORKSPACE_ALIASES.get(_compact_ui_key(value))


def _normalize_tactical_layers(raw_layers: object) -> dict:
    if not isinstance(raw_layers, dict):
        return {}
    out: dict = {}
    for raw_key, raw_value in raw_layers.items():
        layer_key = TACTICAL_LAYER_ALIASES.get(_compact_ui_key(raw_key))
        if not layer_key:
            continue
        enabled = _normalize_ui_bool(raw_value)
        if enabled is None:
            continue
        out[layer_key] = enabled
    return out


def _normalize_ui_defaults(raw_ui: dict | None) -> dict:
    ui = raw_ui if isinstance(raw_ui, dict) else {}
    out: dict = {}

    presentation_mode = str(ui.get("presentation_mode", "")).strip().upper()
    if presentation_mode in {"MAP", "3D"}:
        out["presentation_mode"] = presentation_mode

    camera_mode = str(ui.get("camera_mode", "")).strip().upper()
    if camera_mode in {"CHASE", "FREE"}:
        out["camera_mode"] = camera_mode

    focus_unit = str(ui.get("focus_unit", "")).strip()
    if focus_unit:
        out["focus_unit"] = focus_unit

    tactical_workspace = _normalize_tactical_workspace(ui.get("tactical_workspace"))
    if tactical_workspace:
        out["tactical_workspace"] = tactical_workspace

    tactical_layers = _normalize_tactical_layers(ui.get("tactical_layers"))
    if tactical_layers:
        out["tactical_layers"] = tactical_layers

    try:
        tactical_zoom = float(ui.get("tactical_zoom"))
    except Exception:
        tactical_zoom = None
    if tactical_zoom is not None and tactical_zoom > 0.0:
        out["tactical_zoom"] = tactical_zoom

    return out


def _normalize_startup(raw_startup: dict | None) -> dict:
    startup = raw_startup if isinstance(raw_startup, dict) else {}
    out = {
        "speed": 1.0,
        "auto_start": False,
    }
    try:
        out["speed"] = max(0.05, min(16.0, float(startup.get("speed", 1.0))))
    except Exception:
        out["speed"] = 1.0
    out["auto_start"] = bool(startup.get("auto_start", False))
    return out


def _normalize_session_overrides(raw_session: dict | None, *, profile_dir: str) -> dict:
    session = raw_session if isinstance(raw_session, dict) else {}
    out: dict = {}
    for key in SESSION_OVERRIDE_FIELDS:
        if key not in session:
            continue
        value = session.get(key)
        if key in {"model", "train_config"}:
            value = _resolve_path(value, profile_dir=profile_dir)
        elif key == "fixed_action":
            value = normalize_fixed_action(value, name="profile session.fixed_action")
        out[key] = value
    return out


def _load_profile_json(profile_path: str) -> dict:
    with open(profile_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Viz profile must be a JSON object: {profile_path}")
    return data


def resolve_profile_path(profile_ref: str, roots: Iterable[str] | None = None) -> str:
    ref = str(profile_ref or "").strip()
    if not ref:
        raise ValueError("Viz profile reference is empty.")

    candidates: list[str] = []
    if os.path.isabs(ref):
        candidates.append(ref)
    else:
        candidates.append(os.path.abspath(ref))
        for root in _iter_profile_roots(roots):
            candidates.append(os.path.join(root, ref))
            if not ref.endswith(".json"):
                candidates.append(os.path.join(root, f"{ref}.json"))

    for candidate in candidates:
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)
    raise FileNotFoundError(f"Viz profile not found: {ref}")


def list_viz_profiles(roots: Iterable[str] | None = None) -> list[dict]:
    found: list[dict] = []
    for root in _iter_profile_roots(roots):
        for current_root, _dirs, files in os.walk(root):
            for filename in sorted(files):
                if not filename.endswith(".json"):
                    continue
                abs_path = os.path.join(current_root, filename)
                try:
                    data = _load_profile_json(abs_path)
                except Exception as exc:
                    found.append(
                        {
                            "path": _to_rel_if_possible(abs_path),
                            "name": filename,
                            "description": f"INVALID PROFILE: {exc}",
                            "scenario": "",
                            "valid": False,
                        }
                    )
                    continue
                found.append(
                    {
                        "path": _to_rel_if_possible(abs_path),
                        "name": str(data.get("name") or os.path.splitext(filename)[0]),
                        "description": str(data.get("description") or "").strip(),
                        "scenario": str(data.get("scenario") or "").strip(),
                        "valid": True,
                    }
                )
    found.sort(key=lambda item: (not bool(item.get("valid", True)), str(item.get("name", "")).lower(), str(item.get("path", ""))))
    return found


def load_viz_profile(profile_ref: str, roots: Iterable[str] | None = None) -> dict:
    abs_path = resolve_profile_path(profile_ref, roots=roots)
    data = _load_profile_json(abs_path)
    profile_dir = os.path.dirname(abs_path)

    scenario = _resolve_path(data.get("scenario"), profile_dir=profile_dir)
    if not scenario:
        raise ValueError(f"Viz profile missing required 'scenario': {abs_path}")

    name = str(data.get("name") or os.path.splitext(os.path.basename(abs_path))[0]).strip()
    description = str(data.get("description") or "").strip()
    session_overrides = _normalize_session_overrides(data.get("session"), profile_dir=profile_dir)
    startup = _normalize_startup(data.get("startup"))
    ui_defaults = _normalize_ui_defaults(data.get("ui"))
    asset_registry = str(data.get("asset_registry") or "").strip()
    if asset_registry:
        asset_registry = _resolve_path(asset_registry, profile_dir=profile_dir) or ""

    return {
        "path": _to_rel_if_possible(abs_path),
        "abs_path": abs_path,
        "name": name,
        "description": description,
        "scenario": scenario,
        "asset_registry": asset_registry,
        "session_overrides": session_overrides,
        "startup": startup,
        "ui_defaults": ui_defaults,
        "summary": {
            "path": _to_rel_if_possible(abs_path),
            "name": name,
            "description": description,
            "scenario": scenario,
            "asset_registry": asset_registry,
            "startup": startup,
            "ui_defaults": ui_defaults,
        },
    }
