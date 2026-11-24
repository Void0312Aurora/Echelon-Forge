"""Typed native flight actions and an explicitly chosen speed-change evaluator.

No binding imports live here. The caller supplies the existing PilotAction and
WorldPilotActionAssignment constructors. Action symbols, entity bindings, and
the evaluator are immutable and committed by the session config digest.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Callable, Mapping

from python.experiment.contracts import FIXED_PROTOCOL_PROVENANCE, content_digest
from python.experiment.runtime_candidate import (
    RuntimeCandidateError,
    RuntimeKernelCandidateBackend,
    RuntimeStepResult,
)


@dataclass(frozen=True)
class FlightAction:
    """Selected flight-control catalog entry, in exact integer thousandths."""

    throttle: int
    pitch: int = 0
    roll: int = 0
    rudder: int = 0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            low = 0 if name == "throttle" else -1000
            if type(value) is not int or not low <= value <= 1000:
                raise RuntimeCandidateError(f"invalid flight action {name}")


@dataclass(frozen=True)
class SpeedChangeEvaluator:
    """Reward = rounded final speed mm/s minus rounded initial speed mm/s.

    This is an explicit acceleration diagnostic, not a combat/task reward or a
    claim that increasing speed improves a trained policy.
    """

    identity: str = "speed_change_mmps_v1"

    def __post_init__(self) -> None:
        if self.identity != "speed_change_mmps_v1":
            raise RuntimeCandidateError("unsupported speed evaluator")

    def measure(self, observation: object) -> int:
        speed = float(getattr(observation, "speed"))
        if not math.isfinite(speed) or speed < 0:
            raise RuntimeCandidateError("native observation has invalid speed")
        return round(speed * 1000)


class RuntimePilotActionBackend(RuntimeKernelCandidateBackend):
    """Native action dispatch with fixed entity mapping, catalog, and scoring."""

    def __init__(
        self,
        native_candidate: object,
        *,
        entity_bindings: tuple[tuple[str, str], ...],
        catalog: tuple[tuple[str, FlightAction], ...],
        evaluator: SpeedChangeEvaluator,
        action_factory: Callable[[], object],
        assignment_factory: Callable[[], object],
        observation_ref_factory: Callable[[object | None, str], object] | None = None,
        observation_provider: object | None = None,
        protocol_context: tuple[tuple[str, int], ...] = (),
    ) -> None:
        bindings = tuple(sorted(entity_bindings))
        entries = tuple(sorted(catalog))
        if (
            not bindings
            or len({key for key, _ in bindings}) != len(bindings)
            or len({value for _, value in bindings}) != len(bindings)
            or any(
                type(key) is not str or not key or type(value) is not str or not value
                for key, value in bindings
            )
            or not entries
            or len({key for key, _ in entries}) != len(entries)
            or any(not key or not isinstance(value, FlightAction) for key, value in entries)
            or not isinstance(evaluator, SpeedChangeEvaluator)
        ):
            raise RuntimeCandidateError("invalid native pilot protocol")
        self._bindings = bindings
        self._catalog = entries
        self._evaluator = evaluator
        self._action_factory = action_factory
        self._assignment_factory = assignment_factory
        if observation_ref_factory is not None and not callable(observation_ref_factory):
            raise RuntimeCandidateError("invalid native pilot observation ref factory")
        if observation_ref_factory is not None and observation_provider is not None:
            raise RuntimeCandidateError(
                "native pilot observation ref factory and provider are mutually exclusive"
            )
        if observation_provider is not None:
            if not callable(getattr(observation_provider, "observation_refs", None)):
                raise RuntimeCandidateError("invalid native pilot observation provider refs")
            if not callable(
                getattr(observation_provider, "observation_packet_reader", None)
            ):
                raise RuntimeCandidateError(
                    "invalid native pilot observation provider packet reader"
                )
            provider_agent_ids = getattr(observation_provider, "agent_ids", None)
            if provider_agent_ids is not None and tuple(provider_agent_ids) != tuple(
                key for key, _ in bindings
            ):
                raise RuntimeCandidateError(
                    "native pilot observation provider agents differ from entity bindings"
                )
        self._observation_provider = observation_provider
        self._observation_ref_factory = observation_ref_factory
        if (
            type(protocol_context) is not tuple
            or any(type(row) is not tuple or len(row) != 2 for row in protocol_context)
            or any(
                type(key) is not str or type(value) is not int for key, value in protocol_context
            )
            or len(dict(protocol_context)) != len(protocol_context)
        ):
            raise RuntimeCandidateError("invalid native pilot protocol context")
        self._context = tuple(sorted(protocol_context))
        super().__init__(native_candidate, tuple(key for key, _ in bindings))

    required_observation_provenance = FIXED_PROTOCOL_PROVENANCE

    @property
    def supports_agent_observation_refs(self) -> bool:
        return self._observation_provider is not None or self._observation_ref_factory is not None

    def observation_refs(self, handle: object | None = None) -> Mapping[str, object]:
        if self._observation_provider is not None:
            return self._observation_provider.observation_refs(handle)
        if self._observation_ref_factory is None:
            raise RuntimeCandidateError(
                "native pilot has no RuntimeFacade Agent observation ref provider"
            )
        return {
            agent_id: self._observation_ref_factory(handle, agent_id)
            for agent_id, _ in self._bindings
        }

    def observation_packet_reader(self, handle: object | None = None) -> object:
        """Return the maintained packet reader for the selected native branch."""

        if self._observation_provider is not None:
            return self._observation_provider.observation_packet_reader(handle)
        source = self._native if handle is None else handle
        if not callable(getattr(source, "read_observation_packet", None)):
            raise RuntimeCandidateError(
                "native pilot branch has no maintained observation packet reader"
            )
        return source

    @property
    def config_digest(self) -> str:
        return content_digest("experiment.native-pilot-protocol", self.protocol_payload())

    def protocol_payload(self) -> dict:
        return {
            "schema": "echelon_forge.native_pilot_protocol.v1",
            "entity_bindings": [list(pair) for pair in self._bindings],
            "catalog": {name: asdict(action) for name, action in self._catalog},
            "evaluator": asdict(self._evaluator),
            "other_pilot_fields": "maintained_dto_defaults_active_true",
            "context": dict(self._context),
        }

    def step(self, actions: tuple[tuple[str, str], ...]) -> RuntimeStepResult:
        return self._controlled_step(self._native, actions)

    def step_branch(
        self, handle: object, actions: tuple[tuple[str, str], ...]
    ) -> RuntimeStepResult:
        return self._controlled_step(handle, actions)

    def _controlled_step(
        self, handle: object, actions: tuple[tuple[str, str], ...]
    ) -> RuntimeStepResult:
        if tuple(key for key, _ in actions) != self._agent_ids:
            raise RuntimeCandidateError("pilot action agents do not match entity bindings")
        entries = dict(self._catalog)
        assignments = []
        for (agent, logical_name), (action_agent, symbol) in zip(
            self._bindings, actions, strict=True
        ):
            if agent != action_agent or symbol not in entries:
                raise RuntimeCandidateError("unknown native pilot action symbol")
            command = self._action_factory()
            action = entries[symbol]
            command.active = True
            command.throttle = action.throttle / 1000
            command.stick_pitch = action.pitch / 1000
            command.stick_roll = action.roll / 1000
            command.rudder = action.rudder / 1000
            assignment = self._assignment_factory()
            assignment.world_index = 0
            assignment.entity_id = self._resolve(handle, logical_name)
            assignment.action = command
            assignments.append(assignment)
        before = self._measures(handle)
        if not bool(getattr(handle, "step_pilot_actions")(assignments)):
            raise RuntimeCandidateError("native pilot action submission rejected")
        after = self._measures(handle)
        return RuntimeStepResult(
            snapshot=self._facts(getattr(handle, "snapshot_facts")()),
            rewards={agent: after[agent] - before[agent] for agent in before},
        )

    def _measures(self, handle: object) -> dict[str, int]:
        result = {}
        for agent, logical_name in self._bindings:
            entity = self._resolve(handle, logical_name)
            observation = getattr(handle, "observation")(entity)
            if observation is None:
                raise RuntimeCandidateError("native pilot entity observation unavailable")
            result[agent] = self._evaluator.measure(observation)
        return result

    @staticmethod
    def _resolve(handle: object, logical_name: str) -> int:
        entity = getattr(handle, "resolve_entity")(logical_name)
        if type(entity) is not int or entity <= 0:
            raise RuntimeCandidateError("native pilot logical entity unavailable")
        return entity
