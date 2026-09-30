"""Dependency-terminal runtime for independent decision models.

The runtime owns only the common scheduling envelope: model lifecycle, clock
monotonicity, decision cadence, decision-output caching, provenance context,
and active-roster routing. Observation, action, intent, and report payloads stay
opaque and remain owned by domain adapters. This module deliberately does not
import RL, gym, NumPy, native bindings, or a simulation runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping, Sequence

from .decision_registry import DECISION_MODEL_KINDS, DecisionModel, DecisionModelRegistry


DECISION_RUNTIME_STATUS_READY = "ready"
DECISION_RUNTIME_STATUS_RUNNING = "running"
DECISION_RUNTIME_STATUS_TERMINATED = "terminated"
DECISION_RUNTIME_STATUS_CLOSED = "closed"
DECISION_RUNTIME_ACTION_DECIDED = "decided"
DECISION_RUNTIME_ACTION_HELD = "held"


def _finite_nonnegative(value: float, *, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite non-negative number") from exc
    if not isfinite(number) or number < 0.0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return number


@dataclass(frozen=True)
class DecisionRuntimeAgentSpec:
    """Common scheduling envelope for one active or inactive roster member."""

    agent_id: str
    model_id: str
    domain: str
    role_id: str
    model_kind: str = "scripted"
    decision_period_s: float = 0.0
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
                raise ValueError(f"decision runtime {name} must be non-empty")
        object.__setattr__(self, "agent_id", str(self.agent_id).strip())
        object.__setattr__(self, "model_id", str(self.model_id).strip())
        object.__setattr__(self, "domain", str(self.domain).strip().lower())
        object.__setattr__(self, "role_id", str(self.role_id).strip())
        model_kind = str(self.model_kind).strip().lower()
        if model_kind not in DECISION_MODEL_KINDS:
            raise ValueError(f"unknown decision model kind: {self.model_kind!r}")
        object.__setattr__(self, "model_kind", model_kind)
        object.__setattr__(self, "communication_state", str(self.communication_state).strip())
        object.__setattr__(self, "authority_scope", str(self.authority_scope).strip())
        object.__setattr__(
            self,
            "decision_period_s",
            _finite_nonnegative(self.decision_period_s, name="decision_period_s"),
        )


@dataclass(frozen=True)
class DecisionRuntimeReport:
    """Small common report envelope; payload reports remain domain-owned."""

    agent_id: str
    model_id: str
    domain: str
    role_id: str
    model_kind: str
    clock_s: float
    dt_s: float
    decision_index: int
    observation_version: str
    action_source: str
    communication_state: str
    runtime_status: str


@dataclass(frozen=True)
class DecisionRuntimeStep:
    """Opaque action plus the common runtime report for one roster member."""

    action: Any
    report: DecisionRuntimeReport


class DecisionRuntimeAgent:
    """Schedule one registered decision model without owning domain payloads."""

    def __init__(self, spec: DecisionRuntimeAgentSpec, model: DecisionModel) -> None:
        if not isinstance(spec, DecisionRuntimeAgentSpec):
            raise TypeError("decision runtime agent requires DecisionRuntimeAgentSpec")
        if not isinstance(model, DecisionModel):
            raise TypeError("decision runtime agent model must implement reset/decide/close")
        declared_kind = getattr(model, "model_kind", None)
        if declared_kind is None:
            declared_kind = getattr(model, "_decision_model_kind", None)
        if declared_kind is None:
            raise ValueError(
                f"decision model {spec.model_id!r} must declare model_kind before direct runtime construction"
            )
        normalized_kind = str(declared_kind).strip().lower()
        if normalized_kind not in DECISION_MODEL_KINDS:
            raise ValueError(f"decision model {spec.model_id!r} declares unknown model kind: {declared_kind!r}")
        if normalized_kind != spec.model_kind:
            raise ValueError(
                f"decision model kind mismatch for {spec.model_id!r}: "
                f"spec={spec.model_kind!r}, model={normalized_kind!r}"
            )
        self.spec = spec
        self.model = model
        self.status = DECISION_RUNTIME_STATUS_READY
        self.episode_seed: int | None = None
        self.reset_index = 0
        self._last_clock_s: float | None = None
        self._last_decision_clock_s: float | None = None
        self._next_decision_s: float = 0.0
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
        self._last_decision_clock_s = None
        self._next_decision_s = 0.0
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
                "model_kind": self.spec.model_kind,
                "communication_state": self.spec.communication_state,
                "authority_scope": self.spec.authority_scope,
                "episode_seed": self.episode_seed,
                "reset_index": self.reset_index,
                "replay_identity": self.replay_identity,
            }
        )
        self.model.reset(context=base_context)
        self.status = DECISION_RUNTIME_STATUS_RUNNING

    def step(
        self,
        *,
        observation: Any,
        clock_s: float,
        observation_version: str = "",
        context: Any = None,
        force_decide: bool = False,
    ) -> DecisionRuntimeStep:
        if self.status == DECISION_RUNTIME_STATUS_READY:
            raise RuntimeError("decision runtime agent must be reset before stepping")
        if self.status != DECISION_RUNTIME_STATUS_RUNNING:
            raise RuntimeError(f"decision runtime agent is not running: {self.status}")
        now = _finite_nonnegative(clock_s, name="clock_s")
        if self._last_clock_s is not None and now < self._last_clock_s:
            raise ValueError(
                f"decision runtime clock moved backwards for {self.spec.agent_id!r}: "
                f"{now} < {self._last_clock_s}"
            )
        dt = 0.0 if self._last_clock_s is None else now - self._last_clock_s
        self._last_clock_s = now
        observation_key = str(observation_version)

        due = (
            bool(force_decide)
            or not self._has_action
            or now >= self._next_decision_s
        )
        if due:
            decision_dt = (
                0.0
                if self._last_decision_clock_s is None
                else now - self._last_decision_clock_s
            )
            model_context = dict(context) if isinstance(context, Mapping) else {}
            model_context.update(
                {
                    "agent_id": self.spec.agent_id,
                    "model_id": self.spec.model_id,
                    "domain": self.spec.domain,
                    "role_id": self.spec.role_id,
                    "model_kind": self.spec.model_kind,
                    "clock_s": now,
                    "dt_s": decision_dt,
                    "observation_version": observation_key,
                    "communication_state": self.spec.communication_state,
                    "authority_scope": self.spec.authority_scope,
                    "episode_seed": self.episode_seed,
                    "reset_index": self.reset_index,
                    "replay_identity": self.replay_identity,
                }
            )
            self._last_action = self.model.decide(
                observation=observation,
                context=model_context,
                dt=decision_dt,
            )
            self._last_decision_clock_s = now
            self._has_action = True
            self._decision_index += 1
            self._next_decision_s = now + self.spec.decision_period_s
            source = DECISION_RUNTIME_ACTION_DECIDED
        else:
            # This is a decision-output cache hit. Action validity, expiry,
            # interpolation, and drop behavior belong to the maintained
            # facade ActionHoldPolicy.
            source = DECISION_RUNTIME_ACTION_HELD

        report = DecisionRuntimeReport(
            agent_id=self.spec.agent_id,
            model_id=self.spec.model_id,
            domain=self.spec.domain,
            role_id=self.spec.role_id,
            model_kind=self.spec.model_kind,
            clock_s=now,
            dt_s=dt,
            decision_index=self._decision_index,
            observation_version=observation_key,
            action_source=source,
            communication_state=self.spec.communication_state,
            runtime_status=self.status,
        )
        return DecisionRuntimeStep(action=self._last_action, report=report)

    def terminate(self, *, reason: str = "") -> None:
        if self.status == DECISION_RUNTIME_STATUS_CLOSED:
            return
        self.status = DECISION_RUNTIME_STATUS_TERMINATED
        self.termination_reason = str(reason)

    def close(self) -> None:
        if self.status != DECISION_RUNTIME_STATUS_CLOSED:
            self.model.close()
            self.status = DECISION_RUNTIME_STATUS_CLOSED


class DecisionRuntimeRoster:
    """Deterministic active-roster router for independent decision models."""

    def __init__(self, agents: Sequence[DecisionRuntimeAgent] = ()) -> None:
        self._agents: dict[str, DecisionRuntimeAgent] = {}
        for agent in agents:
            self.add(agent)

    @classmethod
    def from_registry(
        cls,
        registry: DecisionModelRegistry,
        specs: Sequence[DecisionRuntimeAgentSpec],
        *,
        factory_kwargs_by_agent: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> "DecisionRuntimeRoster":
        kwargs_by_agent = factory_kwargs_by_agent or {}
        agents = []
        for spec in specs:
            kwargs = dict(kwargs_by_agent.get(spec.agent_id, {}))
            model = registry.create_for(
                domain=spec.domain,
                role_id=spec.role_id,
                model_id=spec.model_id,
                model_kind=spec.model_kind,
                **kwargs,
            )
            agents.append(DecisionRuntimeAgent(spec, model))
        return cls(agents)

    def add(self, agent: DecisionRuntimeAgent) -> None:
        if not isinstance(agent, DecisionRuntimeAgent):
            raise TypeError("decision runtime roster entries must be DecisionRuntimeAgent")
        if agent.spec.agent_id in self._agents:
            raise ValueError(f"duplicate decision runtime agent: {agent.spec.agent_id}")
        self._agents[agent.spec.agent_id] = agent

    def agent(self, agent_id: str) -> DecisionRuntimeAgent:
        try:
            return self._agents[str(agent_id)]
        except KeyError as exc:
            raise KeyError(f"unknown decision runtime agent: {agent_id}") from exc

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
    ) -> dict[str, DecisionRuntimeStep]:
        versions = observation_versions or {}
        contexts = context_by_agent or {}
        active_ids = tuple(
            agent_id
            for agent_id in sorted(self._agents)
            if self._agents[agent_id].spec.active
        )
        for agent_id in active_ids:
            if agent_id not in observations:
                raise KeyError(f"missing observation for active decision runtime agent: {agent_id}")

        results: dict[str, DecisionRuntimeStep] = {}
        for agent_id in active_ids:
            agent = self._agents[agent_id]
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

    def snapshot(self) -> tuple[DecisionRuntimeAgentSpec, ...]:
        return tuple(self._agents[agent_id].spec for agent_id in sorted(self._agents))


__all__ = [
    "DECISION_RUNTIME_ACTION_DECIDED",
    "DECISION_RUNTIME_ACTION_HELD",
    "DECISION_RUNTIME_STATUS_CLOSED",
    "DECISION_RUNTIME_STATUS_READY",
    "DECISION_RUNTIME_STATUS_RUNNING",
    "DECISION_RUNTIME_STATUS_TERMINATED",
    "DecisionRuntimeAgent",
    "DecisionRuntimeAgentSpec",
    "DecisionRuntimeReport",
    "DecisionRuntimeRoster",
    "DecisionRuntimeStep",
]
