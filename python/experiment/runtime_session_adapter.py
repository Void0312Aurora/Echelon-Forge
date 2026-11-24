"""Thin one-step adapter over the maintained RuntimeFacade session contract.

This module owns request/result identity only. Runtime state, setup, stepping,
and observation production remain owned by ``RuntimeCandidateSession`` and its
``RuntimeFacadeCandidateBackend``. No WorldBatch orchestration or durable
execution authority is introduced here.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping

from python.experiment.contracts import Transition, content_digest
from python.experiment.runtime_candidate import RuntimeCandidateError, RuntimeCandidateSession
from python.tasking_contracts.common.agent_contracts import OBS_FACADE_OBSERVATION_PACKET


RUNTIME_SESSION_ADAPTER_SCHEMA = "echelon_forge.runtime_facade_session_adapter.v1"
TAKEOFF_SURFACE = "air.execution.takeoff.v1"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value.strip():
        raise RuntimeCandidateError(f"{name} must be a non-empty string")
    return value


def _digest(value: object, name: str) -> str:
    value = _text(value, name)
    if _SHA256.fullmatch(value) is None:
        raise RuntimeCandidateError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _pairs(value: object, name: str) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple or not value:
        raise RuntimeCandidateError(f"{name} must be a non-empty tuple")
    if any(
        type(pair) is not tuple
        or len(pair) != 2
        or type(pair[0]) is not str
        or not pair[0]
        or type(pair[1]) is not str
        or not pair[1]
        for pair in value
    ):
        raise RuntimeCandidateError(f"{name} must contain non-empty Agent/action pairs")
    if tuple(sorted(value)) != value or len(set(value)) != len(value):
        raise RuntimeCandidateError(f"{name} must be sorted and unique")
    return value


def _transition_payload(transition: Transition) -> dict[str, object]:
    return {
        "branch_digest": transition.branch_digest,
        "step": transition.step,
        "source_snapshot_digest": transition.source_snapshot_digest,
        "target_snapshot_digest": transition.target_snapshot_digest,
        "actions": [[agent, action] for agent, action in transition.actions],
        "rewards": [[agent, reward] for agent, reward in transition.rewards],
        "terminated": transition.terminated,
        "observation_provenance": transition.observation_provenance,
    }


@dataclass(frozen=True)
class RuntimeSessionSetup:
    """Immutable setup acknowledgement produced from the maintained session."""

    session_id: str
    surface_id: str
    config_digest: str
    agent_ids: tuple[str, ...]
    sequence: int
    snapshot_digest: str
    observation_provenance: str

    def __post_init__(self) -> None:
        _text(self.session_id, "session_id")
        _text(self.surface_id, "surface_id")
        _digest(self.config_digest, "config_digest")
        if type(self.agent_ids) is not tuple or not self.agent_ids:
            raise RuntimeCandidateError("agent_ids must be a non-empty tuple")
        if any(type(agent) is not str or not agent for agent in self.agent_ids):
            raise RuntimeCandidateError("agent_ids must contain non-empty strings")
        if len(set(self.agent_ids)) != len(self.agent_ids):
            raise RuntimeCandidateError("agent_ids must be unique")
        if type(self.sequence) is not int or self.sequence < 0:
            raise RuntimeCandidateError("setup sequence must be a non-negative integer")
        _digest(self.snapshot_digest, "snapshot_digest")
        _text(self.observation_provenance, "observation_provenance")


@dataclass(frozen=True)
class RuntimeSessionStepRequest:
    """One immutable request accepted by the maintained facade session owner."""

    session_id: str
    surface_id: str
    config_digest: str
    sequence: int
    source_snapshot_digest: str
    actions: tuple[tuple[str, str], ...]
    observation_provenance: str
    request_digest: str

    def __post_init__(self) -> None:
        _text(self.session_id, "session_id")
        _text(self.surface_id, "surface_id")
        _digest(self.config_digest, "config_digest")
        if type(self.sequence) is not int or self.sequence < 0:
            raise RuntimeCandidateError("request sequence must be a non-negative integer")
        _digest(self.source_snapshot_digest, "source_snapshot_digest")
        _pairs(self.actions, "actions")
        _text(self.observation_provenance, "observation_provenance")
        _digest(self.request_digest, "request_digest")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": RUNTIME_SESSION_ADAPTER_SCHEMA,
            "session_id": self.session_id,
            "surface_id": self.surface_id,
            "config_digest": self.config_digest,
            "sequence": self.sequence,
            "source_snapshot_digest": self.source_snapshot_digest,
            "actions": [[agent, action] for agent, action in self.actions],
            "observation_provenance": self.observation_provenance,
        }


@dataclass(frozen=True)
class RuntimeSessionStepResult:
    """One immutable result projected from a maintained facade transition."""

    session_id: str
    surface_id: str
    config_digest: str
    sequence: int
    request_digest: str
    source_snapshot_digest: str
    target_snapshot_digest: str
    transition: Transition
    result_digest: str

    def __post_init__(self) -> None:
        _text(self.session_id, "session_id")
        _text(self.surface_id, "surface_id")
        _digest(self.config_digest, "config_digest")
        if type(self.sequence) is not int or self.sequence < 1:
            raise RuntimeCandidateError("result sequence must be a positive integer")
        _digest(self.request_digest, "request_digest")
        _digest(self.source_snapshot_digest, "source_snapshot_digest")
        _digest(self.target_snapshot_digest, "target_snapshot_digest")
        if not isinstance(self.transition, Transition):
            raise RuntimeCandidateError("result transition is malformed")
        _digest(self.result_digest, "result_digest")


class RuntimeSessionAdapter:
    """Fail-closed request/result boundary over one baseline session.

    The adapter never creates worlds or synthesizes state. A request is bound to
    the live baseline head and a result is accepted only when the maintained
    session has advanced exactly one sequence and returned the matching
    transition provenance.
    """

    def __init__(
        self,
        session: RuntimeCandidateSession,
        *,
        surface_id: str = TAKEOFF_SURFACE,
        observation_provenance: str = OBS_FACADE_OBSERVATION_PACKET,
    ) -> None:
        if not isinstance(session, RuntimeCandidateSession):
            raise RuntimeCandidateError("session adapter requires RuntimeCandidateSession")
        if surface_id != TAKEOFF_SURFACE:
            raise RuntimeCandidateError("unsupported RuntimeFacade session surface")
        if observation_provenance != OBS_FACADE_OBSERVATION_PACKET:
            raise RuntimeCandidateError("unsupported RuntimeFacade observation provenance")
        self._session = session
        self._surface_id = surface_id
        self._provenance = observation_provenance
        self._setup = RuntimeSessionSetup(
            session_id=session.spec.session_id,
            surface_id=surface_id,
            config_digest=session.spec.config_digest,
            agent_ids=session.spec.agent_ids,
            sequence=session.head().step,
            snapshot_digest=session.head().digest,
            observation_provenance=observation_provenance,
        )
        self._sequence = self._setup.sequence
        self._source_digest = self._setup.snapshot_digest
        self._pending: dict[str, RuntimeSessionStepRequest] = {}
        self._accepted_requests: set[str] = set()
        self._accepted_results: set[str] = set()
        self._failed = False

    @property
    def setup(self) -> RuntimeSessionSetup:
        return self._setup

    @property
    def sequence(self) -> int:
        return self._sequence

    def make_request(self, actions: Mapping[str, str]) -> RuntimeSessionStepRequest:
        self._ensure_live()
        if not isinstance(actions, Mapping):
            raise RuntimeCandidateError("step actions must be a mapping")
        pairs = tuple(sorted((agent, action) for agent, action in actions.items()))
        if tuple(agent for agent, _ in pairs) != tuple(sorted(self._setup.agent_ids)):
            raise RuntimeCandidateError("step actions must cover exactly the session Agents")
        live = self._session.head()
        if live.step != self._sequence or live.digest != self._source_digest:
            raise RuntimeCandidateError("session head changed outside the adapter boundary")
        payload = {
            "schema": RUNTIME_SESSION_ADAPTER_SCHEMA,
            "session_id": self._setup.session_id,
            "surface_id": self._surface_id,
            "config_digest": self._setup.config_digest,
            "sequence": self._sequence,
            "source_snapshot_digest": self._source_digest,
            "actions": [[agent, action] for agent, action in pairs],
            "observation_provenance": self._provenance,
        }
        return RuntimeSessionStepRequest(
            session_id=self._setup.session_id,
            surface_id=self._surface_id,
            config_digest=self._setup.config_digest,
            sequence=self._sequence,
            source_snapshot_digest=self._source_digest,
            actions=pairs,
            observation_provenance=self._provenance,
            request_digest=content_digest("experiment.runtime-session-request", payload),
        )

    def step(self, request: RuntimeSessionStepRequest) -> RuntimeSessionStepResult:
        self._ensure_live()
        self._validate_request(request)
        self._pending[request.request_digest] = request
        try:
            transition = self._session.step(
                dict(request.actions), observation_provenance=request.observation_provenance
            )
            result = self._result(request, transition)
            return self.accept_result(request, result)
        except RuntimeCandidateError:
            self._failed = True
            self._pending.pop(request.request_digest, None)
            raise

    def accept_result(
        self, request: RuntimeSessionStepRequest, result: RuntimeSessionStepResult
    ) -> RuntimeSessionStepResult:
        self._ensure_live()
        if self._pending.get(getattr(request, "request_digest", None)) != request:
            raise RuntimeCandidateError("result belongs to an unknown or stale request")
        self._validate_request(request, check_reuse=False)
        if result.result_digest in self._accepted_results:
            raise RuntimeCandidateError("duplicate RuntimeFacade session result")
        expected = self._result_payload(result)
        if result.result_digest != content_digest("experiment.runtime-session-result", expected):
            raise RuntimeCandidateError("RuntimeFacade session result digest is malformed")
        if (
            result.session_id != request.session_id
            or result.surface_id != request.surface_id
            or result.config_digest != request.config_digest
            or result.request_digest != request.request_digest
            or result.sequence != request.sequence + 1
            or result.source_snapshot_digest != request.source_snapshot_digest
            or result.target_snapshot_digest != result.transition.target_snapshot_digest
            or result.transition.step != request.sequence
            or result.transition.source_snapshot_digest != request.source_snapshot_digest
            or result.transition.actions != request.actions
            or result.transition.observation_provenance != request.observation_provenance
        ):
            raise RuntimeCandidateError("RuntimeFacade session result provenance or sequence mismatch")
        live = self._session.head()
        if live.step != result.sequence or live.digest != result.target_snapshot_digest:
            raise RuntimeCandidateError("RuntimeFacade session result does not match live facade head")
        self._pending.pop(request.request_digest, None)
        self._accepted_requests.add(request.request_digest)
        self._accepted_results.add(result.result_digest)
        self._sequence = result.sequence
        self._source_digest = result.target_snapshot_digest
        return result

    def _result(
        self, request: RuntimeSessionStepRequest, transition: Transition
    ) -> RuntimeSessionStepResult:
        payload = {
            "schema": RUNTIME_SESSION_ADAPTER_SCHEMA,
            "session_id": request.session_id,
            "surface_id": request.surface_id,
            "config_digest": request.config_digest,
            "sequence": request.sequence + 1,
            "request_digest": request.request_digest,
            "source_snapshot_digest": request.source_snapshot_digest,
            "target_snapshot_digest": transition.target_snapshot_digest,
            "transition": _transition_payload(transition),
        }
        return RuntimeSessionStepResult(
            session_id=request.session_id,
            surface_id=request.surface_id,
            config_digest=request.config_digest,
            sequence=request.sequence + 1,
            request_digest=request.request_digest,
            source_snapshot_digest=request.source_snapshot_digest,
            target_snapshot_digest=transition.target_snapshot_digest,
            transition=transition,
            result_digest=content_digest("experiment.runtime-session-result", payload),
        )

    @staticmethod
    def _result_payload(result: RuntimeSessionStepResult) -> dict[str, object]:
        return {
            "schema": RUNTIME_SESSION_ADAPTER_SCHEMA,
            "session_id": result.session_id,
            "surface_id": result.surface_id,
            "config_digest": result.config_digest,
            "sequence": result.sequence,
            "request_digest": result.request_digest,
            "source_snapshot_digest": result.source_snapshot_digest,
            "target_snapshot_digest": result.target_snapshot_digest,
            "transition": _transition_payload(result.transition),
        }

    def _validate_request(
        self, request: RuntimeSessionStepRequest, *, check_reuse: bool = True
    ) -> None:
        if not isinstance(request, RuntimeSessionStepRequest):
            raise RuntimeCandidateError("RuntimeFacade session request is malformed")
        if request.request_digest != content_digest(
            "experiment.runtime-session-request", request.payload
        ):
            raise RuntimeCandidateError("RuntimeFacade session request digest is malformed")
        if check_reuse and (
            request.request_digest in self._accepted_requests
            or request.request_digest in self._pending
        ):
            raise RuntimeCandidateError("duplicate RuntimeFacade session request")
        if (
            request.session_id != self._setup.session_id
            or request.surface_id != self._surface_id
            or request.config_digest != self._setup.config_digest
            or request.sequence != self._sequence
            or request.source_snapshot_digest != self._source_digest
            or request.observation_provenance != self._provenance
            or tuple(agent for agent, _ in request.actions) != tuple(sorted(self._setup.agent_ids))
        ):
            raise RuntimeCandidateError("RuntimeFacade session request identity or sequence mismatch")

    def _ensure_live(self) -> None:
        if self._failed:
            raise RuntimeCandidateError("RuntimeFacade session adapter is failed closed")


__all__ = [
    "RUNTIME_SESSION_ADAPTER_SCHEMA",
    "RuntimeSessionAdapter",
    "RuntimeSessionSetup",
    "RuntimeSessionStepRequest",
    "RuntimeSessionStepResult",
    "TAKEOFF_SURFACE",
]
