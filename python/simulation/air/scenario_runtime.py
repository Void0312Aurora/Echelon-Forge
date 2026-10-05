"""Simulation-owned Air scenario orchestration.

This module keeps the direct Air command/report/action loop next to the
simulation provider boundary.  A provider supplies native snapshots and
maintained DTO storage; the runtime owns the ordering of director decisions,
command-chain submission, observation projection, action projection, stepping
and optional event-owned terminal evaluation.  It deliberately has no RL or
Gym dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from types import SimpleNamespace
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from python.tasking_contracts.air.execution import AirScriptedExecutionModel
from python.tasking_contracts.common.decision_runtime import (
    DecisionRuntimeAgent,
    DecisionRuntimeAgentSpec,
)

from ..backend import SimulationScenarioBackend
from .action import build_pilot_action
from .director import AirDirectorDecision, AirDirectorInput, AirScriptedDirector
from .terminal import AirCombatTerminalState

EntityKey = tuple[int, int]
MissionCommandFactory = Callable[[EntityKey, Any, int], Any]


@dataclass(frozen=True)
class AirFacadeStepResult:
    """Evidence for one fully ordered direct Air simulation step."""

    step_index: int
    snapshot: Any
    decisions: Mapping[EntityKey, AirDirectorDecision]
    actions: Mapping[EntityKey, Any]
    command_chain: Mapping[str, tuple[Any, ...]]
    terminal: AirCombatTerminalState | None
    replay_identities: tuple[str, ...]


@dataclass(frozen=True)
class AirFacadeScenarioRun:
    """Replay-friendly evidence emitted by the scenario runtime."""

    seed: int
    entity_keys: tuple[EntityKey, ...]
    phases: tuple[tuple[str, ...], ...]
    steps: int
    initial_sim_time_s: tuple[float, ...]
    final_sim_time_s: tuple[float, ...]
    final_positions_m: tuple[tuple[float, float, float], ...]
    action_norms: tuple[tuple[float, ...], ...]
    terminal: AirCombatTerminalState | None
    replay_identities: tuple[str, ...]

    def replay_receipt(self) -> "AirFacadeReplayReceipt":
        return AirFacadeReplayReceipt.from_run(self)


@dataclass(frozen=True)
class AirFacadeReplayReceipt:
    """Canonical process-independent replay evidence for one Air run."""

    schema_version: str
    seed: int
    steps: int
    replay_identities: tuple[str, ...]
    phases: tuple[tuple[str, ...], ...]
    initial_sim_time_s: tuple[float, ...]
    final_sim_time_s: tuple[float, ...]
    final_positions_m: tuple[tuple[float, float, float], ...]
    action_norms: tuple[tuple[float, ...], ...]
    terminal_status: str | None
    terminal_reason: str | None
    digest: str

    @classmethod
    def from_run(cls, run: AirFacadeScenarioRun) -> "AirFacadeReplayReceipt":
        payload = {
            "schema_version": "air.facade.replay.v1",
            "seed": int(run.seed),
            "steps": int(run.steps),
            "replay_identities": list(run.replay_identities),
            "phases": [list(phases) for phases in run.phases],
            "initial_sim_time_s": list(run.initial_sim_time_s),
            "final_sim_time_s": list(run.final_sim_time_s),
            "final_positions_m": [list(position) for position in run.final_positions_m],
            "action_norms": [list(norms) for norms in run.action_norms],
            "terminal_status": None if run.terminal is None else run.terminal.status,
            "terminal_reason": None if run.terminal is None else run.terminal.reason,
        }
        digest = _canonical_digest(payload)
        return cls(
            schema_version=payload["schema_version"],
            seed=int(payload["seed"]),
            steps=int(payload["steps"]),
            replay_identities=tuple(payload["replay_identities"]),
            phases=tuple(tuple(values) for values in payload["phases"]),
            initial_sim_time_s=tuple(payload["initial_sim_time_s"]),
            final_sim_time_s=tuple(payload["final_sim_time_s"]),
            final_positions_m=tuple(tuple(values) for values in payload["final_positions_m"]),
            action_norms=tuple(tuple(values) for values in payload["action_norms"]),
            terminal_status=payload["terminal_status"],
            terminal_reason=payload["terminal_reason"],
            digest=digest,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "seed": self.seed,
            "steps": self.steps,
            "replay_identities": list(self.replay_identities),
            "phases": [list(values) for values in self.phases],
            "initial_sim_time_s": list(self.initial_sim_time_s),
            "final_sim_time_s": list(self.final_sim_time_s),
            "final_positions_m": [list(values) for values in self.final_positions_m],
            "action_norms": [list(values) for values in self.action_norms],
            "terminal_status": self.terminal_status,
            "terminal_reason": self.terminal_reason,
            "digest": self.digest,
        }


class AirFacadeScenarioRuntime:
    """Run the compiled Air command/report/action lifecycle through a provider."""

    def __init__(
        self,
        backend: SimulationScenarioBackend,
        *,
        director: AirScriptedDirector | None = None,
        action_dim: int = 17,
        dt: float = 0.05,
        mission_command_factory: MissionCommandFactory | None = None,
        waypoint_count: int = 3,
        remaining_waypoints: int = 3,
        ils: Sequence[float] = (1.0, 0.0, 0.0, 9000.0),
        task_name: str = "TASK_CAP",
        own_entity_keys: Sequence[EntityKey] | None = None,
        target_entity_keys: Sequence[EntityKey] | None = None,
        own_slot_indices: Sequence[int] | None = None,
        target_slot_indices: Sequence[int] | None = None,
    ) -> None:
        self.backend = backend
        self.director = director or AirScriptedDirector()
        self.action_dim = int(action_dim)
        self.dt = float(dt) if float(dt) > 1.0e-6 else 0.05
        self.mission_command_factory = mission_command_factory or _default_mission_command
        self.waypoint_count = max(0, int(waypoint_count))
        self.remaining_waypoints = max(0, int(remaining_waypoints))
        self.ils = tuple(float(value) for value in ils)
        self.task_name = str(task_name or "TASK_CAP")
        self.own_entity_keys = _normalize_keys(own_entity_keys)
        self.target_entity_keys = _normalize_keys(target_entity_keys)
        self._own_slot_indices = _normalize_indices(own_slot_indices)
        self._target_slot_indices = _normalize_indices(target_slot_indices)
        if (self.own_entity_keys is None) != (self.target_entity_keys is None):
            raise ValueError("Air terminal evaluation requires both own and target entity keys")
        if (self._own_slot_indices is None) != (self._target_slot_indices is None):
            raise ValueError("Air terminal evaluation requires both own and target slot indices")
        if self.own_entity_keys is not None and self._own_slot_indices is not None:
            raise ValueError("Air terminal evaluation accepts entity keys or slot indices, not both")
        self._current: Any | None = None
        self._agents: dict[EntityKey, DecisionRuntimeAgent] = {}
        self._phase_history: dict[EntityKey, list[str]] = {}
        self._action_history: dict[EntityKey, list[float]] = {}
        self._initial_times: tuple[float, ...] = ()
        self._step_index = 0
        self._terminal: AirCombatTerminalState | None = None
        self._closed = False

    @property
    def current_snapshot(self) -> Any:
        if self._current is None:
            raise RuntimeError("Air scenario runtime must be reset before reading its snapshot")
        return self._current

    @property
    def terminal(self) -> AirCombatTerminalState | None:
        return self._terminal

    @property
    def replay_identities(self) -> tuple[str, ...]:
        if self._current is None:
            return ()
        return tuple(self._agents[key].replay_identity for key in self._current.entity_keys)

    def reset(self, seed: int) -> Any:
        """Seed and materialize a fresh provider episode."""

        self._require_open()
        self._close_models()
        self.backend.seed(int(seed))
        current = self.backend.reset()
        keys = tuple(getattr(current, "entity_keys", ()))
        if not keys:
            raise RuntimeError("Air scenario runtime provider returned an empty controlled roster")
        observations = self._scripted_observations()
        if len(observations) != len(keys):
            raise RuntimeError("Air scenario runtime observation count does not match controlled roster")
        self._agents = {}
        self._phase_history = {key: [] for key in keys}
        self._action_history = {key: [] for key in keys}
        for slot_index, (key, observation) in enumerate(zip(keys, observations)):
            model = AirScriptedExecutionModel(action_dim=self.action_dim, dt=self.dt)
            agent = DecisionRuntimeAgent(
                DecisionRuntimeAgentSpec(
                    agent_id=f"air:slot:{slot_index}",
                    model_id="air.execution.phase_scripted",
                    domain="air",
                    role_id="platform_execution",
                    model_kind="scripted",
                ),
                model,
            )
            agent.reset(
                context={"observation": observation, "phase_name": ""},
                episode_seed=int(seed),
            )
            self._agents[key] = agent
        self._initial_times = tuple(float(obs.sim_time) for obs in current.observations)
        self._current = current
        self._step_index = 0
        self._terminal = None
        self._align_terminal_roster(keys)
        return current

    def step(self) -> AirFacadeStepResult:
        """Execute one director -> command chain -> action -> provider step."""

        self._require_open()
        current = self.current_snapshot
        if self._terminal is not None and self._terminal.status != "running":
            raise RuntimeError("Air scenario runtime cannot step after terminal evaluation")
        keys = tuple(current.entity_keys)
        if set(keys) != set(self._agents):
            raise RuntimeError("Air scenario runtime roster changed without reset")
        decisions: dict[EntityKey, AirDirectorDecision] = {}
        for index, key in enumerate(keys):
            decision = self.director.decide(
                AirDirectorInput(
                    entity_id=key[1],
                    sim_time_s=float(current.observations[index].sim_time),
                    observation=current.observations[index],
                    instruments=current.instruments[index],
                    mission_command=self.mission_command_factory(key, current, index),
                    waypoint_count=self.waypoint_count,
                    remaining_waypoints=self.remaining_waypoints,
                    ils=self.ils,
                    task_name=self.task_name,
                )
            )
            decisions[key] = decision
            self._phase_history[key].append(str(decision.phase_name))

        submit = getattr(self.backend, "submit_air_director_decisions", None)
        if not callable(submit):
            raise TypeError("Air scenario provider must expose submit_air_director_decisions")
        submit(decisions)
        command_chain = self._read_command_chain()
        observations = self._scripted_observations()
        actions: dict[EntityKey, Any] = {}
        for index, key in enumerate(keys):
            runtime_step = self._agents[key].step(
                observation=observations[index],
                clock_s=float(current.observations[index].sim_time),
                observation_version=f"{self._step_index}:slot:{index}",
                context={"phase_name": decisions[key].phase_name},
                force_decide=True,
            )
            raw_action = runtime_step.action
            values = np.asarray(raw_action, dtype=np.float32).reshape(-1)
            self._action_history[key].extend(
                (float(np.linalg.norm(values)), float(np.max(np.abs(values))))
            )
            actions[key] = build_pilot_action(
                values,
                action_mode="full",
                instrument_state=current.instruments[index],
            )

        next_snapshot = self.backend.step(actions)
        self._current = next_snapshot
        self._step_index += 1
        self._terminal = self._evaluate_terminal()
        return AirFacadeStepResult(
            step_index=self._step_index,
            snapshot=next_snapshot,
            decisions=dict(decisions),
            actions=dict(actions),
            command_chain=command_chain,
            terminal=self._terminal,
            replay_identities=self.replay_identities,
        )

    def run(self, *, seed: int, steps: int) -> AirFacadeScenarioRun:
        """Run a bounded episode and return stable semantic evidence."""

        if int(steps) <= 0:
            raise ValueError("Air scenario runtime steps must be positive")
        self.reset(int(seed))
        for _ in range(int(steps)):
            self.step()
        current = self.current_snapshot
        return AirFacadeScenarioRun(
            seed=int(seed),
            entity_keys=tuple(current.entity_keys),
            phases=tuple(tuple(self._phase_history[key]) for key in current.entity_keys),
            steps=int(steps),
            initial_sim_time_s=self._initial_times,
            final_sim_time_s=tuple(float(obs.sim_time) for obs in current.observations),
            final_positions_m=tuple(
                tuple(round(float(getattr(obs, name)), 6) for name in ("x", "y", "z"))
                for obs in current.observations
            ),
            action_norms=tuple(
                tuple(round(value, 6) for value in self._action_history[key])
                for key in current.entity_keys
            ),
            terminal=self._terminal,
            replay_identities=self.replay_identities,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._close_models()
        self.backend.close()
        self._current = None
        self._closed = True

    def _scripted_observations(self) -> tuple[dict[str, Any], ...]:
        builder = getattr(self.backend, "air_scripted_observations", None)
        if not callable(builder):
            raise TypeError("Air scenario provider must expose air_scripted_observations")
        return tuple(builder())

    def _read_command_chain(self) -> Mapping[str, tuple[Any, ...]]:
        reader = getattr(self.backend, "read_command_chain", None)
        if not callable(reader):
            raise TypeError("Air scenario provider must expose read_command_chain")
        return reader()

    def _evaluate_terminal(self) -> AirCombatTerminalState | None:
        if self.own_entity_keys is None or self.target_entity_keys is None:
            return None
        evaluator = getattr(self.backend, "evaluate_air_combat_terminal", None)
        if not callable(evaluator):
            raise TypeError("Air terminal groups require provider terminal evaluation")
        return evaluator(
            own_entity_ids=self.own_entity_keys,
            target_entity_ids=self.target_entity_keys,
            entity_keys=self.current_snapshot.entity_keys,
        )

    def _align_terminal_roster(self, keys: Sequence[EntityKey]) -> None:
        if self._own_slot_indices is not None and self._target_slot_indices is not None:
            all_indices = self._own_slot_indices + self._target_slot_indices
            if any(index < 0 or index >= len(keys) for index in all_indices):
                raise ValueError("Air terminal slot indices must belong to the provider controlled roster")
            self.own_entity_keys = tuple(keys[index] for index in self._own_slot_indices)
            self.target_entity_keys = tuple(keys[index] for index in self._target_slot_indices)
        if self.own_entity_keys is None or self.target_entity_keys is None:
            return
        allowed = set(keys)
        if not set(self.own_entity_keys).issubset(allowed) or not set(self.target_entity_keys).issubset(allowed):
            raise ValueError("Air terminal entity keys must belong to the provider controlled roster")

    def _close_models(self) -> None:
        for agent in self._agents.values():
            agent.close()
        self._agents = {}

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("Air scenario runtime is closed")


def _default_mission_command(key: EntityKey, snapshot: Any, index: int) -> Any:
    del key, snapshot, index
    return SimpleNamespace(
        command_code=1,
        cmd_heading_deg=90.0,
        cmd_altitude_m=1200.0,
        cmd_speed_mps=180.0,
    )


def _normalize_keys(values: Sequence[EntityKey] | None) -> tuple[EntityKey, ...] | None:
    if values is None:
        return None
    normalized = tuple((int(key[0]), int(key[1])) for key in values)
    if not normalized or any(world < 0 or entity <= 0 for world, entity in normalized):
        raise ValueError("Air terminal entity keys must contain positive entity IDs")
    if len(set(normalized)) != len(normalized):
        raise ValueError("Air terminal entity keys must be unique")
    return normalized


def _normalize_indices(values: Sequence[int] | None) -> tuple[int, ...] | None:
    if values is None:
        return None
    normalized = tuple(int(value) for value in values)
    if not normalized or len(set(normalized)) != len(normalized) or any(value < 0 for value in normalized):
        raise ValueError("Air terminal slot indices must be unique and non-negative")
    return normalized


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "AirFacadeReplayReceipt",
    "AirFacadeScenarioRuntime",
    "AirFacadeScenarioRun",
    "AirFacadeStepResult",
]
