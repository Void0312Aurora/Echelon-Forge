"""Deterministic single-infantry action and terrain proxy.

This module is an engineering scaffold for the eastern-plain training package.
It consumes the frozen Arnis bundle and the metadata-only field overlay, but it
does not install a runtime system, mutate ``SimulationKernel`` state, or claim
passability/cover/fire authority.  The water and speed rules below are an
explicit proxy policy so reset/step/replay work can progress while the native
Ground movement and terrain owners are still held.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np


GROUND_INFANTRY_ACTION_MODE = "ground_infantry_step_v1"
GROUND_INFANTRY_PROXY_CONTRACT_VERSION = "ground_infantry_proxy.v1"
STANCE_NAMES = ("stand", "crouch", "prone")
ROUTE_INTENT_NAMES = ("direct", "follow_track", "seek_cover", "cross_bridge")

_LANDCOVER_LABELS = {
    0: "unknown_nodata",
    10: "tree_cover",
    20: "shrubland",
    30: "grassland",
    40: "cropland",
    50: "built_up",
    60: "bare_sparse_vegetation",
    70: "snow_ice",
    80: "permanent_water",
    90: "herbaceous_wetland",
    95: "mangroves",
}

# These values are deliberately labelled as an engineering proxy.  They are
# not a calibrated movement model and must not be copied into native runtime
# semantics without a separate owner/acceptance package.
_LANDCOVER_SPEED_MULTIPLIER = {
    10: 0.55,
    20: 0.65,
    30: 0.90,
    40: 0.82,
    50: 0.45,
    60: 0.75,
    70: 0.20,
    80: 0.0,
    90: 0.45,
    95: 0.40,
}
_EARTH_RADIUS_M = 6_378_137.0


class GroundInfantryProxyError(ValueError):
    """Raised when the proxy cannot establish a deterministic safe input."""


@dataclass(frozen=True)
class GroundInfantryAction:
    """Normalized four-field action used by the future RL adapter."""

    desired_heading_deg: float
    desired_speed_fraction: float
    stance: str
    route_intent: str

    def vector(self) -> tuple[float, float, float, float]:
        return (
            float(self.desired_heading_deg),
            float(self.desired_speed_fraction),
            float(STANCE_NAMES.index(self.stance)),
            float(ROUTE_INTENT_NAMES.index(self.route_intent)),
        )


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise GroundInfantryProxyError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise GroundInfantryProxyError(f"{label} must be numeric") from exc
    if not math.isfinite(result):
        raise GroundInfantryProxyError(f"{label} must be finite")
    return result


def _wrap_heading(value: float) -> float:
    wrapped = (float(value) + 180.0) % 360.0 - 180.0
    # Avoid -0.0 in serialized traces.
    return 0.0 if abs(wrapped) < 1.0e-12 else wrapped


def _categorical_name(value: Any, names: tuple[str, ...], label: str) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in names:
            return normalized
        raise GroundInfantryProxyError(f"{label} must be one of {names}")
    numeric = _finite(value, label)
    index = int(round(numeric))
    index = max(0, min(len(names) - 1, index))
    return names[index]


def normalize_ground_infantry_action(
    action: GroundInfantryAction | Mapping[str, Any] | Sequence[Any],
) -> GroundInfantryAction:
    """Normalize a dict or four-value RL vector without hidden dimensions."""

    if isinstance(action, GroundInfantryAction):
        return GroundInfantryAction(
            desired_heading_deg=_wrap_heading(
                _finite(action.desired_heading_deg, "desired_heading_deg")
            ),
            desired_speed_fraction=max(
                0.0,
                min(1.0, _finite(action.desired_speed_fraction, "desired_speed_fraction")),
            ),
            stance=_categorical_name(action.stance, STANCE_NAMES, "stance"),
            route_intent=_categorical_name(action.route_intent, ROUTE_INTENT_NAMES, "route_intent"),
        )

    if isinstance(action, Mapping):
        return normalize_ground_infantry_action(
            GroundInfantryAction(
                desired_heading_deg=action.get("desired_heading_deg", 0.0),
                desired_speed_fraction=action.get("desired_speed_fraction", 0.0),
                stance=action.get("stance", STANCE_NAMES[0]),
                route_intent=action.get("route_intent", ROUTE_INTENT_NAMES[0]),
            )
        )

    try:
        values = np.asarray(action, dtype=np.float64).reshape(-1)
    except (TypeError, ValueError) as exc:
        raise GroundInfantryProxyError("action must be a mapping or a four-value vector") from exc
    if values.size != 4:
        raise GroundInfantryProxyError(
            f"{GROUND_INFANTRY_ACTION_MODE} expects four values, got {values.size}"
        )
    if not np.isfinite(values).all():
        raise GroundInfantryProxyError("action vector must contain only finite values")
    return normalize_ground_infantry_action(
        GroundInfantryAction(
            desired_heading_deg=float(values[0]),
            desired_speed_fraction=float(values[1]),
            stance=float(values[2]),
            route_intent=float(values[3]),
        )
    )


def build_ground_infantry_command(
    action: GroundInfantryAction | Mapping[str, Any] | Sequence[Any],
    *,
    entity_id: int = 0,
) -> dict[str, Any]:
    """Project the action into a transport-neutral command shell.

    The shell is intentionally not an ``ef_py.MissionCommand``.  A later
    native adapter must map it through the maintained command-chain owner and
    obtain an explicit acceptance test before this projection can be promoted.
    """

    normalized = normalize_ground_infantry_action(action)
    return {
        "contract_version": GROUND_INFANTRY_PROXY_CONTRACT_VERSION,
        "command_kind": GROUND_INFANTRY_ACTION_MODE,
        "entity_id": int(entity_id),
        "active": True,
        "desired_heading_deg": normalized.desired_heading_deg,
        "desired_speed_fraction": normalized.desired_speed_fraction,
        "stance": normalized.stance,
        "route_intent": normalized.route_intent,
        "authority": "engineering_proxy_only",
    }


@dataclass(frozen=True)
class GroundInfantryState:
    x_m: float
    y_m: float
    heading_deg: float = 0.0
    stance: str = "stand"
    sim_time_s: float = 0.0
    step_index: int = 0
    route_progress_m: float = 0.0

    def __post_init__(self) -> None:
        for label, value in (
            ("x_m", self.x_m),
            ("y_m", self.y_m),
            ("heading_deg", self.heading_deg),
            ("sim_time_s", self.sim_time_s),
            ("route_progress_m", self.route_progress_m),
        ):
            _finite(value, label)
        if int(self.step_index) < 0:
            raise GroundInfantryProxyError("step_index must be non-negative")
        if self.stance not in STANCE_NAMES:
            raise GroundInfantryProxyError(f"stance must be one of {STANCE_NAMES}")


@dataclass(frozen=True)
class GroundTerrainSample:
    x_m: float
    y_m: float
    elevation_m: float | None
    slope_deg: float | None
    landcover_code: int | None
    landcover_label: str
    semantic_kinds: tuple[str, ...]
    speed_multiplier: float | None
    known: bool
    provenance: str = "arnis_bundle_plus_field_overlay"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GroundInfantryTransition:
    state: GroundInfantryState
    observation: dict[str, Any]
    terrain: GroundTerrainSample
    moved_distance_m: float
    reward: float
    blocked: bool
    blocked_reason: str | None
    trace: dict[str, Any]


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def _distance_point_to_segment(
    point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]
) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length_sq = dx * dx + dy * dy
    if length_sq <= 1.0e-12:
        return _distance(point, start)
    t = max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length_sq))
    return _distance(point, (start[0] + t * dx, start[1] + t * dy))


def _point_in_polygon(point: tuple[float, float], points: Sequence[Sequence[float]]) -> bool:
    inside = False
    if len(points) < 3:
        return False
    x, y = point
    for index, current in enumerate(points):
        previous = points[index - 1]
        x1, y1 = float(previous[0]), float(previous[1])
        x2, y2 = float(current[0]), float(current[1])
        crosses = (y1 > y) != (y2 > y)
        if crosses:
            x_at_y = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < x_at_y:
                inside = not inside
    return inside


def _geometry_points(geometry: Mapping[str, Any]) -> list[tuple[float, float]]:
    if geometry.get("geometry_type") == "point":
        point = geometry.get("point")
        return [(float(point[0]), float(point[1]))] if isinstance(point, list) and len(point) == 2 else []
    points = geometry.get("points")
    if not isinstance(points, list):
        return []
    return [
        (float(point[0]), float(point[1]))
        for point in points
        if isinstance(point, list) and len(point) == 2
    ]


def _point_near_geometry(
    point: tuple[float, float], geometry: Mapping[str, Any], radius_m: float
) -> bool:
    points = _geometry_points(geometry)
    if not points:
        return False
    geometry_type = geometry.get("geometry_type")
    if geometry_type == "polygon":
        if _point_in_polygon(point, points):
            return True
    if geometry_type == "point":
        return _distance(point, points[0]) <= radius_m
    return any(
        _distance_point_to_segment(point, points[index - 1], current) <= radius_m
        for index, current in enumerate(points)
    )


def _segment_near_geometry(
    start: tuple[float, float], end: tuple[float, float], geometry: Mapping[str, Any], radius_m: float
) -> bool:
    length = _distance(start, end)
    samples = max(1, int(math.ceil(length / max(1.0, radius_m))))
    for index in range(samples + 1):
        fraction = index / samples
        point = (
            start[0] + (end[0] - start[0]) * fraction,
            start[1] + (end[1] - start[1]) * fraction,
        )
        if _point_near_geometry(point, geometry, radius_m):
            return True
    return False


class GroundFieldProxy:
    """Read-only Arnis-backed proxy for reset/step/replay development."""

    def __init__(
        self,
        *,
        bundle_root: Path,
        overlay: Mapping[str, Any],
        acceptance: Mapping[str, Any],
        elevation: np.ndarray,
        landcover: np.ndarray,
        elevation_metadata: Mapping[str, Any],
        max_speed_mps: float = 1.5,
    ) -> None:
        self.bundle_root = Path(bundle_root).resolve()
        self.overlay = dict(overlay)
        self.acceptance = dict(acceptance)
        self.elevation = elevation
        self.landcover = landcover
        self.elevation_metadata = dict(elevation_metadata)
        self.max_speed_mps = _finite(max_speed_mps, "max_speed_mps")
        if self.max_speed_mps <= 0.0:
            raise GroundInfantryProxyError("max_speed_mps must be positive")
        self._entries = tuple(self.overlay.get("entries", ()))
        self._origin_x, self._origin_y = self._origin()
        self._step_x, self._step_y = self._steps()
        self._extent_x = abs(self._step_x) * float(self.elevation.shape[1] - 1)
        self._extent_y = abs(self._step_y) * float(self.elevation.shape[0] - 1)

    @classmethod
    def from_fixture(
        cls,
        fixture_root: Path,
        *,
        max_speed_mps: float = 1.5,
    ) -> "GroundFieldProxy":
        root = Path(fixture_root).expanduser().resolve()
        bundle_root = root / "expected"
        overlay_path = root / "field_overlay.json"
        acceptance_path = root / "field_acceptance.json"
        try:
            overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
            acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
            bundle = json.loads((bundle_root / "bundle.json").read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise GroundInfantryProxyError(f"failed to load Arnis proxy fixture: {exc}") from exc
        if not isinstance(overlay, dict) or overlay.get("contract_version") != "field_overlay.v1":
            raise GroundInfantryProxyError("unsupported or missing field overlay contract")
        if not bool(overlay.get("evidence", {}).get("metadata_only", False)):
            raise GroundInfantryProxyError("field overlay must remain metadata-only")
        if not isinstance(acceptance, dict) or not bool(acceptance.get("valid")):
            raise GroundInfantryProxyError("field acceptance is not valid; proxy fails closed")
        if not isinstance(bundle, dict):
            raise GroundInfantryProxyError("Arnis bundle must be an object")
        elevation_artifact = cls._artifact(bundle, "elevation_raster")
        landcover_artifact = cls._artifact(bundle, "landcover_raster")
        elevation = cls._load_raster(bundle_root, elevation_artifact, "<f4")
        landcover = cls._load_raster(bundle_root, landcover_artifact, "u1")
        if elevation.shape != landcover.shape:
            raise GroundInfantryProxyError("elevation and landcover grids must have the same shape")
        metadata = elevation_artifact.get("metadata")
        if not isinstance(metadata, dict):
            raise GroundInfantryProxyError("elevation metadata is required for proxy mapping")
        cls._verify_overlay_source(root, overlay)
        return cls(
            bundle_root=bundle_root,
            overlay=overlay,
            acceptance=acceptance,
            elevation=elevation,
            landcover=landcover,
            elevation_metadata=metadata,
            max_speed_mps=max_speed_mps,
        )

    @staticmethod
    def _artifact(bundle: Mapping[str, Any], kind: str) -> Mapping[str, Any]:
        for artifact in bundle.get("artifacts", []):
            if isinstance(artifact, Mapping) and artifact.get("kind") == kind:
                return artifact
        raise GroundInfantryProxyError(f"bundle is missing {kind}")

    @staticmethod
    def _load_raster(bundle_root: Path, artifact: Mapping[str, Any], dtype: str) -> np.ndarray:
        path = artifact.get("path")
        shape = artifact.get("shape")
        if not isinstance(path, str) or not isinstance(shape, list) or len(shape) != 2:
            raise GroundInfantryProxyError("raster artifact has invalid path or shape")
        raster_path = (bundle_root / path).resolve()
        if bundle_root.resolve() not in raster_path.parents or not raster_path.is_file():
            raise GroundInfantryProxyError(f"raster path is missing or escapes bundle: {path}")
        if not all(type(value) is int and value > 0 for value in shape):
            raise GroundInfantryProxyError("raster shape must contain positive integers")
        return np.memmap(raster_path, dtype=dtype, mode="r", shape=tuple(shape))

    @staticmethod
    def _verify_overlay_source(root: Path, overlay: Mapping[str, Any]) -> None:
        source = overlay.get("source")
        if not isinstance(source, Mapping):
            raise GroundInfantryProxyError("overlay source provenance is required")
        label = str(source.get("path", "")).replace("\\", "/")
        candidates = (root / "input" / label, root / label)
        source_path = next((candidate for candidate in candidates if candidate.is_file()), None)
        if source_path is None:
            raise GroundInfantryProxyError(f"overlay source is missing: {label}")
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if digest != str(source.get("sha256", "")):
            raise GroundInfantryProxyError("overlay source digest does not match provenance")

    def _origin(self) -> tuple[float, float]:
        raw = self.elevation_metadata.get("origin_xy_m")
        if not isinstance(raw, list) or len(raw) != 2:
            raise GroundInfantryProxyError("elevation origin_xy_m is required")
        return _finite(raw[0], "origin_xy_m[0]"), _finite(raw[1], "origin_xy_m[1]")

    def _steps(self) -> tuple[float, float]:
        raw = self.elevation_metadata.get("step_xy_m")
        if not isinstance(raw, list) or len(raw) != 2:
            raise GroundInfantryProxyError("elevation step_xy_m is required")
        step_x = _finite(raw[0], "step_xy_m[0]")
        step_y = _finite(raw[1], "step_xy_m[1]")
        if abs(step_x) <= 0.0 or abs(step_y) <= 0.0:
            raise GroundInfantryProxyError("elevation steps must be non-zero")
        return step_x, step_y

    def _grid_index(self, x_m: float, y_m: float) -> tuple[int, int] | None:
        # The field overlay is expressed from the synthetic OSM south-west
        # corner (0, 0), while the Arnis raster is centered on that same tile
        # (its origin is typically negative-x/positive-y).  The proxy keeps
        # the overlay frame as its public frame and applies this explicit
        # north-up raster index transform.  A native terrain owner must carry
        # this mapping as a real coordinate contract rather than inheriting a
        # fixture assumption.
        column = int(round(float(x_m) / abs(self._step_x)))
        row = int(round(float(y_m) / abs(self._step_y)))
        if not (0 <= row < self.elevation.shape[0] and 0 <= column < self.elevation.shape[1]):
            return None
        return row, column

    def _semantic_kinds(self, point: tuple[float, float]) -> tuple[str, ...]:
        kinds: set[str] = set()
        for entry in self._entries:
            if not isinstance(entry, Mapping):
                continue
            geometry = entry.get("geometry")
            if not isinstance(geometry, Mapping):
                continue
            kind = str(entry.get("overlay_kind", ""))
            tags = entry.get("attributes", {}).get("source_tags", {})
            radius = 0.0
            if isinstance(tags, Mapping):
                try:
                    radius = max(0.0, float(tags.get("width", 0.0)) * 0.5)
                except (TypeError, ValueError):
                    radius = 0.0
            if _point_near_geometry(point, geometry, radius):
                kinds.add(kind)
        return tuple(sorted(kinds))

    def sample(self, x_m: float, y_m: float) -> GroundTerrainSample:
        x = _finite(x_m, "x_m")
        y = _finite(y_m, "y_m")
        index = self._grid_index(x, y)
        semantic_kinds = self._semantic_kinds((x, y))
        if index is None:
            return GroundTerrainSample(
                x_m=x,
                y_m=y,
                elevation_m=None,
                slope_deg=None,
                landcover_code=None,
                landcover_label="unknown_nodata",
                semantic_kinds=semantic_kinds,
                speed_multiplier=None,
                known=False,
            )
        row, column = index
        elevation = float(self.elevation[row, column])
        code = int(self.landcover[row, column])
        left = max(0, column - 1)
        right = min(self.elevation.shape[1] - 1, column + 1)
        top = max(0, row - 1)
        bottom = min(self.elevation.shape[0] - 1, row + 1)
        dx = (float(self.elevation[row, right]) - float(self.elevation[row, left])) / (
            max(1, right - left) * abs(self._step_x)
        )
        dy = (float(self.elevation[bottom, column]) - float(self.elevation[top, column])) / (
            max(1, bottom - top) * abs(self._step_y)
        )
        slope_deg = math.degrees(math.atan(math.hypot(dx, dy)))
        multiplier = _LANDCOVER_SPEED_MULTIPLIER.get(code)
        if multiplier is not None:
            multiplier *= max(0.2, 1.0 - slope_deg / 60.0)
        return GroundTerrainSample(
            x_m=x,
            y_m=y,
            elevation_m=elevation,
            slope_deg=slope_deg,
            landcover_code=code,
            landcover_label=_LANDCOVER_LABELS.get(code, "unknown_class"),
            semantic_kinds=semantic_kinds,
            speed_multiplier=multiplier,
            known=multiplier is not None and math.isfinite(elevation),
        )

    def reset(
        self,
        *,
        x_m: float = 100.0,
        y_m: float = 100.0,
        heading_deg: float = 0.0,
        stance: str = "stand",
    ) -> GroundInfantryState:
        action = normalize_ground_infantry_action(
            {
                "desired_heading_deg": heading_deg,
                "desired_speed_fraction": 0.0,
                "stance": stance,
                "route_intent": "direct",
            }
        )
        sample = self.sample(x_m, y_m)
        if not sample.known:
            raise GroundInfantryProxyError("reset point has unknown proxy terrain")
        return GroundInfantryState(
            x_m=float(x_m),
            y_m=float(y_m),
            heading_deg=action.desired_heading_deg,
            stance=action.stance,
        )

    def _water_hit(
        self, start: tuple[float, float], end: tuple[float, float]
    ) -> bool:
        length = _distance(start, end)
        samples = max(1, int(math.ceil(length / 2.0)))
        for index in range(samples + 1):
            fraction = index / samples
            point = (
                start[0] + (end[0] - start[0]) * fraction,
                start[1] + (end[1] - start[1]) * fraction,
            )
            sample = self.sample(*point)
            if sample.landcover_code == 80 or "river_corridor" in sample.semantic_kinds:
                return True
        return False

    def _bridge_hit(self, start: tuple[float, float], end: tuple[float, float]) -> bool:
        for entry in self._entries:
            if not isinstance(entry, Mapping) or entry.get("overlay_kind") != "bridge_crossing":
                continue
            geometry = entry.get("geometry")
            if not isinstance(geometry, Mapping):
                continue
            tags = entry.get("attributes", {}).get("source_tags", {})
            width = 4.0
            if isinstance(tags, Mapping):
                try:
                    width = max(2.0, float(tags.get("width", width)))
                except (TypeError, ValueError):
                    pass
            if _segment_near_geometry(start, end, geometry, width * 0.5):
                return True
        return False

    def _observation(
        self,
        state: GroundInfantryState,
        terrain: GroundTerrainSample,
        *,
        velocity_x_mps: float,
        velocity_y_mps: float,
        blocked_reason: str | None,
    ) -> dict[str, Any]:
        return {
            "contract_version": GROUND_INFANTRY_PROXY_CONTRACT_VERSION,
            "authority": "engineering_proxy_only",
            "position_local_enu_m": [state.x_m, state.y_m, terrain.elevation_m],
            "velocity_local_enu_mps": [velocity_x_mps, velocity_y_mps, 0.0],
            "heading_deg": state.heading_deg,
            "stance": state.stance,
            "sim_time_s": state.sim_time_s,
            "step_index": state.step_index,
            "route_progress_m": state.route_progress_m,
            "terrain": terrain.as_dict(),
            "blocked_reason": blocked_reason,
            "unknown_value_policy": "explicit_unknown_with_provenance",
        }

    def step(
        self,
        state: GroundInfantryState,
        action: GroundInfantryAction | Mapping[str, Any] | Sequence[Any],
        *,
        dt_s: float = 1.0,
    ) -> GroundInfantryTransition:
        dt = _finite(dt_s, "dt_s")
        if dt <= 0.0:
            raise GroundInfantryProxyError("dt_s must be positive")
        normalized = normalize_ground_infantry_action(action)
        start = (float(state.x_m), float(state.y_m))
        current = self.sample(*start)
        distance = 0.0
        blocked_reason: str | None = None
        end = start
        if not current.known:
            blocked_reason = "unknown_terrain"
        else:
            multiplier = float(current.speed_multiplier or 0.0)
            distance = self.max_speed_mps * normalized.desired_speed_fraction * multiplier * dt
            heading_rad = math.radians(normalized.desired_heading_deg)
            end = (
                start[0] + math.sin(heading_rad) * distance,
                start[1] + math.cos(heading_rad) * distance,
            )
            if self._grid_index(*end) is None:
                blocked_reason = "outside_map_extent"
            elif not self.sample(*end).known:
                blocked_reason = "unknown_terrain"
            elif self._water_hit(start, end):
                bridge_admitted = normalized.route_intent == "cross_bridge" and self._bridge_hit(start, end)
                if not bridge_admitted:
                    blocked_reason = "river_crossing_requires_bridge_intent"
        blocked = blocked_reason is not None
        if blocked:
            end = start
            distance = 0.0
        next_state = GroundInfantryState(
            x_m=end[0],
            y_m=end[1],
            heading_deg=normalized.desired_heading_deg,
            stance=normalized.stance,
            sim_time_s=state.sim_time_s + dt,
            step_index=state.step_index + 1,
            route_progress_m=state.route_progress_m + distance,
        )
        terrain = self.sample(*end)
        velocity_x = (end[0] - start[0]) / dt
        velocity_y = (end[1] - start[1]) / dt
        observation = self._observation(
            next_state,
            terrain,
            velocity_x_mps=velocity_x,
            velocity_y_mps=velocity_y,
            blocked_reason=blocked_reason,
        )
        reward = float(distance / max(self.max_speed_mps * dt, 1.0))
        if blocked:
            reward -= 0.25
        trace = {
            "contract_version": GROUND_INFANTRY_PROXY_CONTRACT_VERSION,
            "authority": "engineering_proxy_only",
            "action": list(normalized.vector()),
            "state_before": asdict(state),
            "state_after": asdict(next_state),
            "blocked": blocked,
            "blocked_reason": blocked_reason,
            "moved_distance_m": distance,
            "reward": reward,
        }
        return GroundInfantryTransition(
            state=next_state,
            observation=observation,
            terrain=terrain,
            moved_distance_m=distance,
            reward=reward,
            blocked=blocked,
            blocked_reason=blocked_reason,
            trace=trace,
        )


__all__ = [
    "GROUND_INFANTRY_ACTION_MODE",
    "GROUND_INFANTRY_PROXY_CONTRACT_VERSION",
    "GroundFieldProxy",
    "GroundInfantryAction",
    "GroundInfantryProxyError",
    "GroundInfantryState",
    "GroundInfantryTransition",
    "GroundTerrainSample",
    "build_ground_infantry_command",
    "normalize_ground_infantry_action",
]
