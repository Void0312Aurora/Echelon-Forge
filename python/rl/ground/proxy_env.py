"""Gymnasium harness for the explicitly non-authoritative infantry proxy.

The class remains a deterministic diagnostic substitute alongside the admitted
native probe. It exercises reset/step/observation/reward/termination and trace
contracts, but must not be registered as the maintained ``WorldBatchVecEnv``
production environment.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

try:  # RL dependencies are optional for non-training repository consumers.
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:  # pragma: no cover - exercised only in minimal installs.
    gym = None
    spaces = None

from .infantry_proxy import (
    GROUND_INFANTRY_PROXY_CONTRACT_VERSION,
    GroundFieldProxy,
    GroundInfantryState,
    GroundInfantryTransition,
    ROUTE_INTENT_NAMES,
    STANCE_NAMES,
)


if gym is None:  # pragma: no cover - the fallback is a clear dependency boundary.

    class GroundInfantryProxyEnv:  # type: ignore[no-redef]
        """Placeholder that reports the optional RL dependency explicitly."""

        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise ModuleNotFoundError(
                "gymnasium is required for GroundInfantryProxyEnv; "
                "install the project's RL optional dependencies"
            )

else:

    class GroundInfantryProxyEnv(gym.Env):
        """Single-soldier Gymnasium environment backed by ``GroundFieldProxy``."""

        metadata = {"render_modes": []}

        def __init__(
            self,
            proxy: GroundFieldProxy,
            *,
            start_xy_m: tuple[float, float] = (400.0, 100.0),
            goal_xy_m: tuple[float, float] = (600.0, 100.0),
            goal_radius_m: float = 5.0,
            max_steps: int = 256,
            blocked_step_limit: int = 8,
        ) -> None:
            super().__init__()
            self.proxy = proxy
            self.start_xy_m = (float(start_xy_m[0]), float(start_xy_m[1]))
            self.goal_xy_m = (float(goal_xy_m[0]), float(goal_xy_m[1]))
            self.goal_radius_m = float(goal_radius_m)
            self.max_steps = int(max_steps)
            self.blocked_step_limit = int(blocked_step_limit)
            if self.goal_radius_m <= 0.0:
                raise ValueError("goal_radius_m must be positive")
            if self.max_steps <= 0 or self.blocked_step_limit <= 0:
                raise ValueError("max_steps and blocked_step_limit must be positive")

            self._validate_known_point(self.start_xy_m, "start_xy_m")
            self._validate_known_point(self.goal_xy_m, "goal_xy_m")
            map_low_x, map_high_x, map_low_y, map_high_y = self.proxy.map_bounds_xy_m
            elevation_low, elevation_high = self.proxy.elevation_bounds_m
            map_diagonal = self.proxy.map_diagonal_m

            self.action_space = spaces.Box(
                low=np.asarray([-180.0, 0.0, 0.0, 0.0], dtype=np.float32),
                high=np.asarray([180.0, 1.0, 2.0, 3.0], dtype=np.float32),
                dtype=np.float32,
            )
            self.observation_space = spaces.Dict(
                {
                    "position_local_enu_m": spaces.Box(
                        low=np.asarray([map_low_x, map_low_y], dtype=np.float32),
                        high=np.asarray([map_high_x, map_high_y], dtype=np.float32),
                        dtype=np.float32,
                    ),
                    "velocity_local_enu_mps": spaces.Box(
                        low=np.full(2, -self.proxy.max_speed_mps, dtype=np.float32),
                        high=np.full(2, self.proxy.max_speed_mps, dtype=np.float32),
                        dtype=np.float32,
                    ),
                    "terrain": spaces.Box(
                        low=np.asarray([elevation_low, 0.0, 0.0], dtype=np.float32),
                        high=np.asarray([elevation_high, 90.0, 255.0], dtype=np.float32),
                        dtype=np.float32,
                    ),
                    "semantic_context": spaces.Box(
                        low=np.asarray([-1.0, -180.0, -1.0, -180.0, 0.0, 0.0], dtype=np.float32),
                        high=np.asarray(
                            [map_diagonal, 180.0, map_diagonal, 180.0, 1.0, 1.0],
                            dtype=np.float32,
                        ),
                    ),
                    "semantic_flags": spaces.MultiBinary(5),
                    "mission_goal_relative_state": spaces.Box(
                        low=np.asarray([-map_high_x, -map_high_y, 0.0], dtype=np.float32),
                        high=np.asarray([map_high_x, map_high_y, map_diagonal], dtype=np.float32),
                        dtype=np.float32,
                    ),
                    "state": spaces.Box(
                        low=np.asarray([-180.0, 0.0, 0.0, 0.0], dtype=np.float32),
                        high=np.asarray(
                            [180.0, 2.0, 3.0, self.max_steps * self.proxy.max_speed_mps],
                            dtype=np.float32,
                        ),
                        dtype=np.float32,
                    ),
                }
            )
            self._state: GroundInfantryState | None = None
            self._blocked_steps = 0
            self._trace: list[dict[str, Any]] = []

        def _validate_known_point(self, point: Sequence[float], label: str) -> tuple[float, float]:
            if isinstance(point, (str, bytes)) or len(point) != 2:
                raise ValueError(f"{label} must contain two coordinates")
            try:
                normalized = (float(point[0]), float(point[1]))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{label} must contain numeric coordinates") from exc
            terrain = self.proxy.sample(*normalized)
            if not terrain.known:
                raise ValueError(f"{label} must lie on known proxy terrain")
            return normalized

        def _state_or_raise(self) -> GroundInfantryState:
            if self._state is None:
                raise RuntimeError("GroundInfantryProxyEnv.reset must be called first")
            return self._state

        def _observation(self, transition: GroundInfantryTransition) -> dict[str, np.ndarray]:
            payload = transition.observation
            terrain = transition.terrain
            semantic_kinds = set(terrain.semantic_kinds)
            velocity = payload["velocity_local_enu_mps"]
            return {
                "position_local_enu_m": np.asarray(
                    [payload["position_local_enu_m"][0], payload["position_local_enu_m"][1]],
                    dtype=np.float32,
                ),
                "velocity_local_enu_mps": np.asarray(velocity[:2], dtype=np.float32),
                "terrain": np.asarray(
                    [
                        float(terrain.elevation_m),
                        float(terrain.slope_deg),
                        float(terrain.landcover_code),
                    ],
                    dtype=np.float32,
                ),
                "semantic_context": np.asarray(
                    [
                        *payload["semantic_context"][
                            "nearest_tree_line_distance_and_bearing"
                        ],
                        *payload["semantic_context"][
                            "nearest_settlement_distance_and_bearing"
                        ],
                        float(payload["semantic_context"]["river_active"]),
                        float(payload["semantic_context"]["bridge_active"]),
                    ],
                    dtype=np.float32,
                ),
                "mission_goal_relative_state": np.asarray(
                    [
                        self.goal_xy_m[0] - float(payload["position_local_enu_m"][0]),
                        self.goal_xy_m[1] - float(payload["position_local_enu_m"][1]),
                        float(
                            np.linalg.norm(
                                np.asarray(self.goal_xy_m, dtype=np.float64)
                                - np.asarray(payload["position_local_enu_m"][:2], dtype=np.float64)
                            )
                        ),
                    ],
                    dtype=np.float32,
                ),
                "semantic_flags": np.asarray(
                    [
                        "farmland_area" in semantic_kinds,
                        "tree_line" in semantic_kinds,
                        "settlement_anchor" in semantic_kinds
                        or "settlement_structure" in semantic_kinds,
                        "river_corridor" in semantic_kinds,
                        "bridge_crossing" in semantic_kinds,
                    ],
                    dtype=np.int8,
                ),
                "state": np.asarray(
                    [
                        float(payload["heading_deg"]),
                        float(STANCE_NAMES.index(payload["stance"])),
                        float(ROUTE_INTENT_NAMES.index(payload["route_intent"])),
                        float(payload["route_progress_m"]),
                    ],
                    dtype=np.float32,
                ),
            }

        def _info(
            self,
            transition: GroundInfantryTransition,
            *,
            terminated: bool,
            truncated: bool,
            termination_reason: str | None = None,
        ) -> dict[str, Any]:
            return {
                "contract_version": GROUND_INFANTRY_PROXY_CONTRACT_VERSION,
                "authority": "engineering_proxy_only",
                "blocked": transition.blocked,
                "blocked_reason": transition.blocked_reason,
                "moved_distance_m": transition.moved_distance_m,
                "trace": transition.trace,
                "terminated": terminated,
                "truncated": truncated,
                "termination_reason": termination_reason,
            }

        def reset(
            self,
            *,
            seed: int | None = None,
            options: Mapping[str, Any] | None = None,
        ) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
            super().reset(seed=seed)
            options = options or {}
            start = options.get("start_xy_m", self.start_xy_m)
            goal = options.get("goal_xy_m", self.goal_xy_m)
            if not isinstance(start, Sequence) or len(start) != 2:
                raise ValueError("options.start_xy_m must contain two coordinates")
            if not isinstance(goal, Sequence) or len(goal) != 2:
                raise ValueError("options.goal_xy_m must contain two coordinates")
            self.start_xy_m = self._validate_known_point(start, "options.start_xy_m")
            self.goal_xy_m = self._validate_known_point(goal, "options.goal_xy_m")
            self._state = self.proxy.reset(x_m=self.start_xy_m[0], y_m=self.start_xy_m[1])
            self._blocked_steps = 0
            self._trace = []
            transition = self.proxy.step(self._state, [0.0, 0.0, 0.0, 0.0])
            self._state = transition.state
            # Reset observation is produced by a zero-speed proxy step, but
            # the step index/time are rewound so reset remains a pure boundary.
            self._state = GroundInfantryState(
                x_m=self._state.x_m,
                y_m=self._state.y_m,
                heading_deg=self._state.heading_deg,
                stance=self._state.stance,
                route_intent=self._state.route_intent,
            )
            reset_transition = GroundInfantryTransition(
                state=self._state,
                observation=self.proxy.observation_for_state(
                    self._state,
                    velocity_x_mps=0.0,
                    velocity_y_mps=0.0,
                    blocked_reason=None,
                ),
                terrain=self.proxy.sample(self._state.x_m, self._state.y_m),
                moved_distance_m=0.0,
                reward=0.0,
                blocked=False,
                blocked_reason=None,
                trace={
                    "contract_version": GROUND_INFANTRY_PROXY_CONTRACT_VERSION,
                    "authority": "engineering_proxy_only",
                    "event": "reset",
                    "seed": seed,
                },
            )
            return self._observation(reset_transition), {
                "contract_version": GROUND_INFANTRY_PROXY_CONTRACT_VERSION,
                "authority": "engineering_proxy_only",
                "seed": seed,
                "goal_xy_m": list(self.goal_xy_m),
                "trace": reset_transition.trace,
            }

        def step(
            self, action: Sequence[float] | Mapping[str, Any]
        ) -> tuple[dict[str, np.ndarray], float, bool, bool, dict[str, Any]]:
            state = self._state_or_raise()
            previous_distance = float(np.linalg.norm(np.asarray(self.goal_xy_m) - [state.x_m, state.y_m]))
            transition = self.proxy.step(state, action)
            self._state = transition.state
            self._trace.append(transition.trace)
            self._blocked_steps = self._blocked_steps + 1 if transition.blocked else 0
            current_distance = float(
                np.linalg.norm(np.asarray(self.goal_xy_m) - [self._state.x_m, self._state.y_m])
            )
            progress = previous_distance - current_distance
            reward = float(transition.reward + 0.1 * progress)
            terminated = current_distance <= self.goal_radius_m
            truncated = (
                not terminated
                and self._state.step_index >= self.max_steps
            ) or self._blocked_steps >= self.blocked_step_limit
            reason = None
            if terminated:
                reason = "goal_reached"
            elif self._blocked_steps >= self.blocked_step_limit:
                reason = "blocked_step_limit"
            elif self._state.step_index >= self.max_steps:
                reason = "max_steps"
            info = self._info(
                transition,
                terminated=terminated,
                truncated=truncated,
                termination_reason=reason,
            )
            info["distance_to_goal_m"] = current_distance
            info["progress_m"] = progress
            info["trace_length"] = len(self._trace)
            return self._observation(transition), reward, terminated, truncated, info

        @property
        def trace(self) -> tuple[dict[str, Any], ...]:
            return tuple(self._trace)


__all__ = ["GroundInfantryProxyEnv"]
