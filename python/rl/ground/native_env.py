"""Gymnasium adapter for the bounded native Ground infantry probe.

This adapter makes the compiled single-soldier probe consumable by ordinary
RL tooling without promoting it to a production WorldBatch environment. The
probe remains the authority for reset, transition, reward, and replay data.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

try:  # RL dependencies are optional for non-training repository consumers.
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:  # pragma: no cover - exercised only in minimal installs.
    gym = None
    spaces = None

from .native_probe import GroundInfantryNativeProbe, NativeGroundInfantryTransition


_FLOAT32_MAX = float(np.finfo(np.float32).max)


def _fixture_bounds(probe: GroundInfantryNativeProbe) -> tuple[float, float, float, float, float, float] | None:
    """Read spatial/elevation bounds from the verified continuous bundle when present."""

    manifest_path = Path(probe.bundle_dir) / "bundle.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        artifact = next(
            item for item in manifest["artifacts"] if item["kind"] == "elevation_raster"
        )
        shape = tuple(int(value) for value in artifact["shape"])
        metadata = artifact["metadata"]
        origin_x, origin_y = (float(value) for value in metadata["origin_xy_m"])
        step_x, step_y = (float(value) for value in metadata["step_xy_m"])
        x_end = origin_x + (shape[1] - 1) * step_x
        y_end = origin_y + (shape[0] - 1) * step_y
        raster = np.memmap(
            Path(probe.bundle_dir) / artifact["path"],
            dtype=np.dtype(artifact["dtype"]),
            mode="r",
            shape=shape,
        )
        elevation_low = float(np.min(raster))
        elevation_high = float(np.max(raster))
        return (
            min(origin_x, x_end),
            max(origin_x, x_end),
            min(origin_y, y_end),
            max(origin_y, y_end),
            elevation_low,
            elevation_high,
        )
    except (OSError, KeyError, StopIteration, TypeError, ValueError):
        return None


def _finite_observation_bounds(probe: GroundInfantryNativeProbe) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Build finite bounds from the probe horizon and source fixture metadata."""

    points = (probe.start_xy_m,) + tuple(probe.waypoints_xy_m)
    travel_budget_m = probe.max_speed_mps * probe.time_step_s * probe.max_steps
    position_low_x = min(point[0] for point in points) - travel_budget_m
    position_high_x = max(point[0] for point in points) + travel_budget_m
    position_low_y = min(point[1] for point in points) - travel_budget_m
    position_high_y = max(point[1] for point in points) + travel_budget_m

    fixture = _fixture_bounds(probe)
    if fixture is None:
        map_low_x, map_high_x, map_low_y, map_high_y = (
            position_low_x,
            position_high_x,
            position_low_y,
            position_high_y,
        )
        elevation_low, elevation_high = -1.0e6, 1.0e6
        field_distance_high = 1.0e6
    else:
        map_low_x, map_high_x, map_low_y, map_high_y, elevation_low, elevation_high = fixture
        field_distance_high = math.hypot(
            map_high_x - map_low_x + 2.0 * travel_budget_m,
            map_high_y - map_low_y + 2.0 * travel_budget_m,
        )
    elevation_low = min(elevation_low, 0.0) - 1.0
    elevation_high = max(elevation_high, 0.0) + 1.0

    goal_x = [point[0] for point in probe.waypoints_xy_m]
    goal_y = [point[1] for point in probe.waypoints_xy_m]
    mission_dx = [goal - position for goal in goal_x for position in (position_low_x, position_high_x)]
    mission_dy = [goal - position for goal in goal_y for position in (position_low_y, position_high_y)]
    mission_distance_high = max(
        math.hypot(abs(dx), abs(dy)) for dx in mission_dx for dy in mission_dy
    )
    uint64_as_float = _FLOAT32_MAX

    return {
        "position_local_enu_m": (
            np.asarray([position_low_x, position_low_y, -1.0], dtype=np.float32),
            np.asarray([position_high_x, position_high_y, 1.0], dtype=np.float32),
        ),
        "velocity_local_enu_mps": (
            np.full(3, -probe.max_speed_mps, dtype=np.float32),
            np.full(3, probe.max_speed_mps, dtype=np.float32),
        ),
        "terrain": (
            np.asarray([elevation_low, 0.0, 0.0, 0.0, 0.0], dtype=np.float32),
            np.asarray([elevation_high, 5.0, 1.0, 1.0, 1.0], dtype=np.float32),
        ),
        "terrain_effects": (
            np.asarray([0.0], dtype=np.float32),
            np.asarray([90.0], dtype=np.float32),
        ),
        "movement_effects": (
            np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32),
            np.asarray([5.0, 90.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32),
        ),
        "field_semantics": (
            np.asarray([0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0], dtype=np.float32),
            np.asarray([1.0, field_distance_high, 360.0, field_distance_high, 360.0, 1.0, 1.0], dtype=np.float32),
        ),
        "weapon_state": (
            np.zeros(8, dtype=np.float32),
            np.asarray([1.0, 1.0, _FLOAT32_MAX, _FLOAT32_MAX, _FLOAT32_MAX, _FLOAT32_MAX, 1.0, _FLOAT32_MAX], dtype=np.float32),
        ),
        "health_state": (
            np.zeros(2, dtype=np.float32),
            np.full(2, 100.0, dtype=np.float32),
        ),
        "command_state": (
            np.asarray([0.0, -180.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32),
            np.asarray([1.0, 180.0, probe.max_speed_mps, 3.0, 2.0, uint64_as_float, uint64_as_float], dtype=np.float32),
        ),
        "mission_state": (
            np.asarray([min(mission_dx), min(mission_dy), 0.0], dtype=np.float32),
            np.asarray([max(mission_dx), max(mission_dy), mission_distance_high], dtype=np.float32),
        ),
        "waypoint_state": (
            np.asarray([0.0, 0.0], dtype=np.float32),
            np.asarray([float(len(probe.waypoints_xy_m)), float(len(probe.waypoints_xy_m))], dtype=np.float32),
        ),
        "state": (
            np.asarray([0.0, 0.0, 0.0], dtype=np.float32),
            np.asarray([360.0, 2.0, float(probe.max_steps)], dtype=np.float32),
        ),
    }


if gym is None:  # pragma: no cover - the fallback is a clear dependency boundary.

    class GroundInfantryNativeEnv:  # type: ignore[no-redef]
        """Placeholder that reports the optional RL dependency explicitly."""

        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise ModuleNotFoundError(
                "gymnasium is required for GroundInfantryNativeEnv; "
                "install the project's RL optional dependencies"
            )

else:

    class GroundInfantryNativeEnv(gym.Env):
        """Single-soldier Gymnasium surface backed by ``GroundInfantryNativeProbe``."""

        metadata = {"render_modes": []}

        def __init__(self, probe: GroundInfantryNativeProbe) -> None:
            super().__init__()
            self.probe = probe
            self.action_space = spaces.Box(
                low=np.asarray([-180.0, 0.0, 0.0, 0.0], dtype=np.float32),
                # The native command projection currently admits only the
                # direct route intent; held route intents stay on the proxy.
                high=np.asarray([180.0, 1.0, 2.0, 0.0], dtype=np.float32),
                dtype=np.float32,
            )
            bounds = _finite_observation_bounds(probe)
            self.observation_space = spaces.Dict(
                {
                    key: spaces.Box(low=low, high=high, dtype=np.float32)
                    for key, (low, high) in bounds.items()
                }
            )
            self._trace: list[dict[str, Any]] = []

        @staticmethod
        def _observation(payload: Mapping[str, Sequence[float]]) -> dict[str, np.ndarray]:
            return {
                key: np.asarray(values, dtype=np.float32)
                for key, values in payload.items()
            }

        def reset(
            self,
            *,
            seed: int | None = None,
            options: Mapping[str, Any] | None = None,
        ) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
            del options  # Probe construction owns the fixed map/start/goal boundary.
            super().reset(seed=seed)
            observation, info = self.probe.reset(seed=0 if seed is None else int(seed))
            self._trace = [info["trace"]]
            return self._observation(observation), info

        def step(
            self, action: Sequence[float] | Mapping[str, Any]
        ) -> tuple[dict[str, np.ndarray], float, bool, bool, dict[str, Any]]:
            transition: NativeGroundInfantryTransition = self.probe.step(action)
            self._trace.append(transition.trace)
            info = {
                "contract_version": transition.trace["contract_version"],
                "authority": transition.trace["authority"],
                "production_boundary": "not_world_batch",
                "blocked": transition.blocked,
                "blocked_reason": transition.blocked_reason,
                "termination_reason": transition.trace.get("termination_reason"),
                "truncation_reason": transition.truncation_reason,
                "trace": transition.trace,
            }
            return (
                self._observation(transition.observation),
                float(transition.reward),
                bool(transition.terminated),
                bool(transition.truncated),
                info,
            )

        @property
        def trace(self) -> tuple[dict[str, Any], ...]:
            return tuple(self._trace)


__all__ = ["GroundInfantryNativeEnv"]
