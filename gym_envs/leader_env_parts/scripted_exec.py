from __future__ import annotations

from typing import Any

import numpy as np

from python.tasking_contracts.air.execution.model import AIR_SCRIPTED_EXECUTION_MODEL_ID
from python.tasking_contracts.air.registry import AIR_SCRIPTED_MODEL_REGISTRY
from python.tasking_contracts.common.decision_runtime import (
    DecisionRuntimeAgent,
    DecisionRuntimeAgentSpec,
    DecisionRuntimeStep,
)


class ScriptedExecutiveController:
    def __init__(
        self,
        env: Any,
        *,
        transition_alt_agl_m: float = 140.0,
        model_id: str = AIR_SCRIPTED_EXECUTION_MODEL_ID,
    ):
        self.env = env
        self.transition_alt_agl_m = float(transition_alt_agl_m)
        self.model_id = str(model_id).strip() or AIR_SCRIPTED_EXECUTION_MODEL_ID
        self._model = None
        self._runtime_agent: DecisionRuntimeAgent | None = None
        self._last_runtime_step: DecisionRuntimeStep | None = None

    @property
    def active_mode(self) -> str:
        return "takeoff" if self._model is None else self._model.active_mode

    @property
    def takeoff_ctrl(self):
        return None if self._model is None else self._model.takeoff_ctrl

    @property
    def stable_ctrl(self):
        return None if self._model is None else self._model.stable_ctrl

    @property
    def landing_ctrl(self):
        return None if self._model is None else self._model.landing_ctrl

    @property
    def runtime_report(self):
        return None if self._last_runtime_step is None else self._last_runtime_step.report

    @property
    def replay_identity(self) -> str | None:
        return None if self._runtime_agent is None else self._runtime_agent.replay_identity

    @property
    def action_dim(self) -> int:
        return int(self.env.action_space.shape[0])

    def reset(self, obs: dict, *, episode_seed: int | None = None) -> None:
        dt = 0.05
        try:
            dt = float(getattr(self.env.unwrapped.sim, "get_time_step", lambda: 0.05)())
        except Exception:
            dt = 0.05
        loader = getattr(self.env.unwrapped, "loader", None)
        runway_length_m = max(
            (
                float(beacon.get("length", 0.0))
                for beacon in list(getattr(loader, "ils_beacons", []) or [])
            ),
            default=0.0,
        )
        self._model = AIR_SCRIPTED_MODEL_REGISTRY.create_for(
            domain="air",
            role_id="autopilot_controller",
            model_id=self.model_id,
            action_dim=self.action_dim,
            dt=dt,
            transition_alt_agl_m=self.transition_alt_agl_m,
            runway_length_m=runway_length_m,
        )
        agent_id = str(getattr(self.env.unwrapped, "agent_id", "air-scripted-executive"))
        self._runtime_agent = DecisionRuntimeAgent(
            DecisionRuntimeAgentSpec(
                agent_id=agent_id,
                model_id=self.model_id,
                domain="air",
                role_id="autopilot_controller",
                authority_scope="air_execution",
            ),
            self._model,
        )
        self._runtime_agent.reset(
            context={"observation": obs, "phase_name": self._phase_name()},
            episode_seed=episode_seed,
        )
        self._last_runtime_step = None

    def _phase_name(self) -> str:
        loader = getattr(self.env.unwrapped, "loader", None)
        return "" if loader is None else str(getattr(loader, "mission_phase_name", ""))

    def predict(self, obs: dict) -> np.ndarray:
        if self._runtime_agent is None:
            self.reset(obs)
        assert self._runtime_agent is not None
        dt = 0.05
        try:
            dt = float(getattr(self.env.unwrapped.sim, "get_time_step", lambda: 0.05)())
        except Exception:
            dt = 0.05
        clock_s = float(getattr(self.env.unwrapped, "steps", 0)) * max(dt, 1.0e-6)
        phase_name = self._phase_name()
        observation_version = (
            f"reset:{self._runtime_agent.reset_index}:"
            f"step:{int(getattr(self.env.unwrapped, 'steps', 0))}"
        )
        self._last_runtime_step = self._runtime_agent.step(
            observation=obs,
            clock_s=clock_s,
            observation_version=observation_version,
            context={"observation": obs, "phase_name": phase_name},
        )
        return np.asarray(self._last_runtime_step.action, dtype=np.float32).reshape(-1)

    def close(self) -> None:
        if self._runtime_agent is not None:
            self._runtime_agent.close()
        self._runtime_agent = None
        self._last_runtime_step = None
        self._model = None
