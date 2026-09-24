"""Gymnasium adapter for the bounded native Ground infantry probe.

This adapter makes the compiled single-soldier probe consumable by ordinary
RL tooling without promoting it to a production WorldBatch environment. The
probe remains the authority for reset, transition, reward, and replay data.
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

from .native_probe import GroundInfantryNativeProbe, NativeGroundInfantryTransition


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
            self.observation_space = spaces.Dict(
                {
                    "position_local_enu_m": spaces.Box(
                        low=-np.inf, high=np.inf, shape=(3,), dtype=np.float32
                    ),
                    "velocity_local_enu_mps": spaces.Box(
                        low=-np.inf, high=np.inf, shape=(3,), dtype=np.float32
                    ),
                    "terrain": spaces.Box(
                        low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32
                    ),
                    "terrain_effects": spaces.Box(
                        low=-np.inf, high=np.inf, shape=(1,), dtype=np.float32
                    ),
                    "movement_effects": spaces.Box(
                        low=-np.inf, high=np.inf, shape=(8,), dtype=np.float32
                    ),
                    "field_semantics": spaces.Box(
                        low=-np.inf, high=np.inf, shape=(7,), dtype=np.float32
                    ),
                    "weapon_state": spaces.Box(
                        low=-np.inf, high=np.inf, shape=(8,), dtype=np.float32
                    ),
                    "health_state": spaces.Box(
                        low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32
                    ),
                    "command_state": spaces.Box(
                        low=-np.inf, high=np.inf, shape=(7,), dtype=np.float32
                    ),
                    "mission_state": spaces.Box(
                        low=-np.inf, high=np.inf, shape=(3,), dtype=np.float32
                    ),
                    "waypoint_state": spaces.Box(
                        low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32
                    ),
                    "state": spaces.Box(
                        low=-np.inf, high=np.inf, shape=(3,), dtype=np.float32
                    ),
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
