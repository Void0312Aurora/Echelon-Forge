from __future__ import annotations

import copy
import json
import math
import os
import tempfile
from typing import Any

from python.angles import wrap_signed_deg
from python.runtime_bootstrap import resolve_repo_path

class ContractSkipped(RuntimeError):
    pass


_MAX_SPEC_EXTENDS_DEPTH = 4


def _load_spec(path: str) -> dict[str, Any]:
    return _load_spec_recursive(path, chain=(), depth=0)


def _load_spec_recursive(
    path: str,
    *,
    chain: tuple[str, ...],
    depth: int,
) -> dict[str, Any]:
    resolved_path = os.path.abspath(path)
    canonical_path = os.path.normcase(os.path.realpath(resolved_path))
    if canonical_path in chain:
        cycle = " -> ".join((*chain, canonical_path))
        raise ValueError(f"Contract spec extends cycle detected: {cycle}")

    with open(resolved_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Contract spec must be a JSON object: {resolved_path}")
    if "extends" not in data:
        return data

    extends = data.pop("extends")
    if not isinstance(extends, str) or not extends.strip():
        raise ValueError(
            f"Contract spec 'extends' must be a non-empty string: {resolved_path}"
        )
    if depth >= _MAX_SPEC_EXTENDS_DEPTH:
        raise ValueError(
            "Contract spec maximum extends depth "
            f"({_MAX_SPEC_EXTENDS_DEPTH}) exceeded: {resolved_path}"
        )

    base_path = _resolve_spec_extends_path(extends, resolved_path)
    base = _load_spec_recursive(
        base_path,
        chain=(*chain, canonical_path),
        depth=depth + 1,
    )
    return _deep_merge(base, data)


def _resolve_spec_extends_path(extends: str, spec_path: str) -> str:
    if os.path.isabs(extends):
        candidate_paths = [os.path.abspath(extends)]
    else:
        candidate_paths = [
            os.path.abspath(os.path.join(os.path.dirname(spec_path), extends)),
            os.path.abspath(resolve_repo_path(extends)),
        ]
    for candidate_path in candidate_paths:
        if os.path.isfile(candidate_path):
            return candidate_path
    resolved_candidates = ", ".join(candidate_paths)
    raise FileNotFoundError(
        f"Contract spec extends target {extends!r} was not found; "
        f"checked {resolved_candidates}"
    )


def _write_inline_scenario(scenario: dict[str, Any]) -> str:
    fd, path = tempfile.mkstemp(suffix=".json", prefix="scenario_contract_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(scenario, f)
    return path


def _deep_merge(base: Any, patch: Any) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = {k: copy.deepcopy(v) for k, v in base.items()}
        for key, value in patch.items():
            if key in merged:
                merged[key] = _deep_merge(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged
    if isinstance(base, list) and isinstance(patch, list):
        return copy.deepcopy(patch)
    return copy.deepcopy(patch)


def _load_json_file(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Scenario JSON must be an object: {path}")
    return data


def _materialize_scenario_path(spec: dict[str, Any]) -> tuple[str, bool]:
    scenario_base = spec.get("scenario_base", None)
    scenario_patch = spec.get("scenario_patch", None)
    if scenario_base is not None:
        base_path = resolve_repo_path(str(scenario_base))
        base_scenario = _load_json_file(base_path)
        if scenario_patch is not None:
            if not isinstance(scenario_patch, dict):
                raise ValueError("'scenario_patch' must be a JSON object")
            base_scenario = _deep_merge(base_scenario, scenario_patch)
        return _write_inline_scenario(base_scenario), True
    if "scenario" in spec:
        return resolve_repo_path(str(spec["scenario"])), False
    inline_scenario = spec.get("scenario_inline", None)
    if isinstance(inline_scenario, dict):
        return _write_inline_scenario(inline_scenario), True
    raise ValueError("Contract must provide either 'scenario' or 'scenario_inline'")


def _leg_lengths(route: list[dict[str, Any]]) -> list[float]:
    prev_x = 0.0
    prev_y = 0.0
    out: list[float] = []
    for wp in route:
        x = float(wp["x"])
        y = float(wp["y"])
        out.append(float(math.hypot(x - prev_x, y - prev_y)))
        prev_x = x
        prev_y = y
    return out


def _turn_geometry(route: list[dict[str, Any]]) -> tuple[list[float], list[float]]:
    points = [(0.0, 0.0)] + [(float(wp["x"]), float(wp["y"])) for wp in route]
    tracks: list[float] = []
    legs: list[float] = []
    for idx in range(1, len(points)):
        dx = points[idx][0] - points[idx - 1][0]
        dy = points[idx][1] - points[idx - 1][1]
        legs.append(float(math.hypot(dx, dy)))
        tracks.append(float(math.degrees(math.atan2(dx, dy)) % 360.0))
    turns: list[float] = []
    for idx in range(1, len(tracks)):
        delta = (tracks[idx] - tracks[idx - 1] + 180.0) % 360.0 - 180.0
        turns.append(abs(float(delta)))
    return legs, turns


def _turn_radius_m(speed_mps: float, bank_limit_deg: float) -> float:
    bank_rad = math.radians(max(1.0, min(80.0, float(bank_limit_deg))))
    tanb = math.tan(bank_rad)
    if abs(tanb) <= 1.0e-6:
        return float("inf")
    speed = max(30.0, float(speed_mps))
    return (speed * speed) / (9.80665 * abs(tanb))


def _turn_budget_cost_m(turn_abs_deg: float, *, speed_mps: float, bank_limit_deg: float, cost_scale: float) -> float:
    turn_abs_deg = abs(float(turn_abs_deg))
    if turn_abs_deg <= 1.0e-6 or float(cost_scale) <= 1.0e-6:
        return 0.0
    radius_m = _turn_radius_m(float(speed_mps), float(bank_limit_deg))
    if not math.isfinite(radius_m) or radius_m <= 0.0:
        return 0.0
    return float(radius_m) * math.radians(turn_abs_deg) * float(cost_scale)


# Local name preserved as a thin alias; semantics owned by python.angles.
_wrap_deg = wrap_signed_deg


def _check_optional_range(value: float, bounds: dict[str, Any], *, label: str) -> str | None:
    if "min" in bounds and value < float(bounds["min"]):
        return f"{label} below minimum: {value:.1f} < {float(bounds['min']):.1f}"
    if "max" in bounds and value > float(bounds["max"]):
        return f"{label} above maximum: {value:.1f} > {float(bounds['max']):.1f}"
    if "abs_min" in bounds and abs(value) < float(bounds["abs_min"]):
        return f"{label} abs below minimum: {abs(value):.1f} < {float(bounds['abs_min']):.1f}"
    if "abs_max" in bounds and abs(value) > float(bounds["abs_max"]):
        return f"{label} abs exceeds maximum: {abs(value):.1f} > {float(bounds['abs_max']):.1f}"
    return None
