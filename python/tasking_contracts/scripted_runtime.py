"""Dependency-terminal runtime for independent scripted decision models.

The runtime owns only the common scheduling envelope: model lifecycle, clock
monotonicity, decision cadence, action hold/expiry, provenance context, and
active-roster routing. Observation, action, intent, and report payloads stay
opaque and remain owned by domain adapters. This module deliberately does not
import RL, gym, NumPy, native bindings, or a simulation runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping, Sequence

from .scripted_registry import ScriptedDecisionModel, ScriptedModelRegistry


SCRIPTED_RUNTIME_STATUS_READY = "ready"
SCRIPTED_RUNTIME_STATUS_RUNNING = "running"
SCRIPTED_RUNTIME_STATUS_TERMINATED = "terminated"
SCRIPTED_RUNTIME_STATUS_CLOSED = "closed"
SCRIPTED_RUNTIME_ACTION_DECIDED = "decided"
SCRIPTED_RUNTIME_ACTION_HELD = "held"
SCRIPTED_RUNTIME_ACTION_EXPIRED = "expired"


def _finite_nonnegative(value: float, *, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite non-negative number") from exc
    if not isfinite(number) or number < 0.0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return number


@dataclass(frozen=True)
class ScriptedRuntimeAgentSpec:
    """Common scheduling envelope for one active or inactive roster member."""

    agent_id: str
    model_id: str
    domain: str
    role_id: str
    decision_period_s: float = 0.0
    action_hold_s: float = 0.0
    action_expiry_s: float | None = None
    communication_state: str = "available"
    authority_scope: str = "unspecified"
    active: bool = True

    def __post_init__(self) -> None:
        values = {
            "agent_id": self.agent_id,
            "model_id": self.model_id,
            "domain": self.domain,
            "role_id": self.role_id,
            "communication_state": self.communication_state,
            "authority_scope": self.authority_scope,
        }
        for name, value in values.items():
            if not str(value).strip():
                raise ValueError(f"scripted runtime {name} must be non-empty")
        object.__setattr__(self, "agent_id", str(self.agent_id).strip())
        object.__setattr__(self, "model_id", str(self.model_id).strip())
        object.__setattr__(self, "domain", str(self.domain).strip().lower())
        object.__setattr__(self, "role_id", str(self.role_id).strip())
        object.__setattr__(self, "communication_state", str(self.communication_state).strip())
        object.__setattr__(self, "authority_scope", str(self.authority_scope).strip())
        object.__setattr__(
            self,
            "decision_period_s",
            _finite_nonnegative(self.decision_period_s, name="decision_period_s"),
        )
        object.__setattr__(self, "action_hold_s", _finite_nonnegative(self.action_hold_s, name="action_hold_s"))
        if self.action_expiry_s is not None:
            object.__setattr__(
                self,
                "action_expiry_s",
                _finite_nonnegative(self.action_expiry_s, name="action_expiry_s"),
            )


@dataclass(frozen=True)
class ScriptedRuntimeReport:
    """Small common report envelope; payload reports remain domain-owned."""

    agent_id: str
    model_id: str
    domain: str
    role_id: str
    clock_s: float
    dt_s: float
    decision_index: int
    observation_version: str
    action_source: str
    action_expiry_s: float | None
    communication_state: str
    runtime_status: str


@dataclass(frozen=True)
class ScriptedRuntimeStep:
    """Opaque action plus the common runtime report for one roster member."""

    action: Any
    report: ScriptedRuntimeReport


class ScriptedRuntimeAgent:
    """Schedule one registered scripted model without owning domain payloads."""

    def __init__(self, spec: ScriptedRuntimeAgentSpec, model: ScriptedDecisionModel) -> None:
        if not isinstance(spec, ScriptedRuntimeAgentSpec):
            raise TypeError("scripted runtime agent requires ScriptedRuntimeAgentSpec")
        if not isinstance(model, ScriptedDecisionModel):
            raise TypeError("scripted runtime agent model must implement reset/decide/close")
        self.spec = spec
        self.model = model
        self.status = SCRIPTED_RUNTIME_STATUS_READY
        self.episode_seed: int | None = None
        self.reset_index = 0
        self._last_clock_s: float | None = None
        self._next_decision_s: float = 0.0
        self._action_expiry_s: float | None = None
        self._last_action: Any = None
        self._has_action = False
        self._decision_index = 0

    @property
    def replay_identity(self) -> str:
        seed = "none" if self.episode_seed is None else str(self.episode_seed)
        return f"{self.spec.agent_id}:{self.spec.model_id}:seed={seed}:reset={self.reset_index}"

    def reset(self, *, context: Any = None, episode_seed: int | None = None) -> None:
        self.reset_index += 1
        self.episode_seed = None if episode_seed is None else int(episode_seed)
        self._last_clock_s = None
        self._next_decision_s = 0.0
        self._action_expiry_s = None
        self._last_action = None
        self._has_action = False
        self._decision_index = 0
        base_context = dict(context) if isinstance(context, Mapping) else {}
        base_context.update(
            {
                "agent_id": self.spec.agent_id,
                "model_id": self.spec.model_id,
                "domain": self.spec.domain,
                "role_id": self.spec.role_id,
                "communication_state": self.spec.communication_state,
                "authority_scope": self.spec.authority_scope,
                "episode_seed": self.episode_seed,
                "reset_index": self.reset_index,
                "replay_identity": self.replay_identity,
            }
        )
        self.model.reset(context=base_context)
        self.status = SCRIPTED_RUNTIME_STATUS_RUNNING

    def step(
        self,
        *,
        observation: Any,
        clock_s: float,
        observation_version: str = "",
        context: Any = None,
        force_decide: bool = False,
    ) -> ScriptedRuntimeStep:
        if self.status == SCRIPTED_RUNTIME_STATUS_READY:
            raise RuntimeError("scripted runtime agent must be reset before stepping")
        if self.status != SCRIPTED_RUNTIME_STATUS_RUNNING:
            raise RuntimeError(f"scripted runtime agent is not running: {self.status}")
        now = _finite_nonnegative(clock_s, name="clock_s")
        if self._last_clock_s is not None and now < self._last_clock_s:
            raise ValueError(
                f"scripted runtime clock moved backwards for {self.spec.agent_id!r}: "
                f"{now} < {self._last_clock_s}"
            )
        dt = 0.0 if self._last_clock_s is None else now - self._last_clock_s
        self._last_clock_s = now
        observation_key = str(observation_version)

        expired = self._has_action and self._action_expiry_s is not None and now >= self._action_expiry_s
        due = (
            bool(force_decide)
            or not self._has_action
            or expired
            or now >= self._next_decision_s
        )
        if due:
            model_context = dict(context) if isinstance(context, Mapping) else {}
            model_context.update(
                {
                    "agent_id": self.spec.agent_id,
                    "model_id": self.spec.model_id,
                    "domain": self.spec.domain,
                    "role_id": self.spec.role_id,
                    "clock_s": now,
                    "dt_s": dt,
                    "observation_version": observation_key,
                    "communication_state": self.spec.communication_state,
                    "authority_scope": self.spec.authority_scope,
                    "episode_seed": self.episode_seed,
                    "reset_index": self.reset_index,
                    "replay_identity": self.replay_identity,
                }
            )
            self._last_action = self.model.decide(observation=observation, context=model_context, dt=dt)
            self._has_action = True
            self._decision_index += 1
            self._next_decision_s = now + self.spec.decision_period_s
            expiry = self.spec.action_expiry_s
            if expiry is None:
                expiry = self.spec.action_hold_s
            self._action_expiry_s = None if expiry <= 0.0 else now + expiry
            source = SCRIPTED_RUNTIME_ACTION_DECIDED
        else:
            source = SCRIPTED_RUNTIME_ACTION_EXPIRED if expired else SCRIPTED_RUNTIME_ACTION_HELD

        report = ScriptedRuntimeReport(
            agent_id=self.spec.agent_id,
            model_id=self.spec.model_id,
            domain=self.spec.domain,
            role_id=self.spec.role_id,
            clock_s=now,
            dt_s=dt,
            decision_index=self._decision_index,
            observation_version=observation_key,
            action_source=source,
            action_expiry_s=self._action_expiry_s,
            communication_state=self.spec.communication_state,
            runtime_status=self.status,
        )
        return ScriptedRuntimeStep(action=self._last_action, report=report)

    def terminate(self, *, reason: str = "") -> None:
        if self.status == SCRIPTED_RUNTIME_STATUS_CLOSED:
            return
        self.status = SCRIPTED_RUNTIME_STATUS_TERMINATED
        self.termination_reason = str(reason)

    def close(self) -> None:
        if self.status != SCRIPTED_RUNTIME_STATUS_CLOSED:
            self.model.close()
            self.status = SCRIPTED_RUNTIME_STATUS_CLOSED


class ScriptedRuntimeRoster:
    """Deterministic active-roster router for independent scripted models."""

    def __init__(self, agents: Sequence[ScriptedRuntimeAgent] = ()) -> None:
        self._agents: dict[str, ScriptedRuntimeAgent] = {}
        for agent in agents:
            self.add(agent)

    @classmethod
    def from_registry(
        cls,
        registry: ScriptedModelRegistry,
        specs: Sequence[ScriptedRuntimeAgentSpec],
        *,
        factory_kwargs_by_agent: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> "ScriptedRuntimeRoster":
        kwargs_by_agent = factory_kwargs_by_agent or {}
        agents = []
        for spec in specs:
            kwargs = dict(kwargs_by_agent.get(spec.agent_id, {}))
            model = registry.create_for(
                domain=spec.domain,
                role_id=spec.role_id,
                model_id=spec.model_id,
                **kwargs,
            )
            agents.append(ScriptedRuntimeAgent(spec, model))
        return cls(agents)

    def add(self, agent: ScriptedRuntimeAgent) -> None:
        if not isinstance(agent, ScriptedRuntimeAgent):
            raise TypeError("scripted runtime roster entries must be ScriptedRuntimeAgent")
        if agent.spec.agent_id in self._agents:
            raise ValueError(f"duplicate scripted runtime agent: {agent.spec.agent_id}")
        self._agents[agent.spec.agent_id] = agent

    def agent(self, agent_id: str) -> ScriptedRuntimeAgent:
        try:
            return self._agents[str(agent_id)]
        except KeyError as exc:
            raise KeyError(f"unknown scripted runtime agent: {agent_id}") from exc

    def reset(
        self,
        *,
        context_by_agent: Mapping[str, Any] | None = None,
        episode_seed: int | None = None,
    ) -> None:
        contexts = context_by_agent or {}
        for agent_id in sorted(self._agents):
            self._agents[agent_id].reset(
                context=contexts.get(agent_id),
                episode_seed=episode_seed,
            )

    def step(
        self,
        *,
        observations: Mapping[str, Any],
        clock_s: float,
        observation_versions: Mapping[str, str] | None = None,
        context_by_agent: Mapping[str, Any] | None = None,
        force_decide: bool = False,
    ) -> dict[str, ScriptedRuntimeStep]:
        versions = observation_versions or {}
        contexts = context_by_agent or {}
        results: dict[str, ScriptedRuntimeStep] = {}
        for agent_id in sorted(self._agents):
            agent = self._agents[agent_id]
            if not agent.spec.active:
                continue
            if agent_id not in observations:
                raise KeyError(f"missing observation for active scripted runtime agent: {agent_id}")
            results[agent_id] = agent.step(
                observation=observations[agent_id],
                clock_s=clock_s,
                observation_version=versions.get(agent_id, ""),
                context=contexts.get(agent_id),
                force_decide=force_decide,
            )
        return results

    def terminate(self, *, reason: str = "") -> None:
        for agent_id in sorted(self._agents):
            self._agents[agent_id].terminate(reason=reason)

    def close(self) -> None:
        for agent_id in sorted(self._agents):
            self._agents[agent_id].close()

    def snapshot(self) -> tuple[ScriptedRuntimeAgentSpec, ...]:
        return tuple(self._agents[agent_id].spec for agent_id in sorted(self._agents))


__all__ = [
    "SCRIPTED_RUNTIME_ACTION_DECIDED",
    "SCRIPTED_RUNTIME_ACTION_EXPIRED",
    "SCRIPTED_RUNTIME_ACTION_HELD",
    "SCRIPTED_RUNTIME_STATUS_CLOSED",
    "SCRIPTED_RUNTIME_STATUS_READY",
    "SCRIPTED_RUNTIME_STATUS_RUNNING",
    "SCRIPTED_RUNTIME_STATUS_TERMINATED",
    "ScriptedRuntimeAgent",
    "ScriptedRuntimeAgentSpec",
    "ScriptedRuntimeReport",
    "ScriptedRuntimeRoster",
    "ScriptedRuntimeStep",
]
