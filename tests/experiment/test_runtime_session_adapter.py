"""Thin RuntimeFacade request/result session adapter contract tests."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from observation_replay_fixtures import make_observation_packet
from python.experiment.contracts import content_digest
from python.experiment.runtime_candidate import RuntimeCandidateError
from python.experiment.runtime_candidate import RuntimeCandidateSession
from python.experiment.runtime_candidate import RuntimeSnapshotFacts
from python.experiment.runtime_candidate import runtime_config_digest
from python.experiment.runtime_facade_backend import RuntimeFacadeCandidateBackend
from python.experiment.runtime_session_adapter import RUNTIME_SESSION_ADAPTER_SCHEMA
from python.experiment.runtime_session_adapter import RuntimeSessionAdapter
from python.experiment.runtime_session_adapter import RuntimeSessionStepResult
from python.experiment.runtime_session_adapter import TAKEOFF_SURFACE
from python.tasking_contracts.common.agent_contracts import OBS_FACADE_OBSERVATION_PACKET


class _Identity:
    def __init__(self) -> None:
        self.step = 0

    def snapshot_facts(self) -> RuntimeSnapshotFacts:
        return RuntimeSnapshotFacts(
            step=self.step,
            state_digest=f"{self.step + 1:064x}",
            event_cursor=self.step,
            rng_digest=f"{self.step + 101:064x}",
            episode_seed=42,
        )


class _Runtime:
    def __init__(self, identity: _Identity) -> None:
        self.identity = identity
        self.steps = 0
        self.actions: list[tuple[tuple[str, str], ...]] = []
        self.capabilities = type(
            "Capabilities",
            (),
            {"has_observation_batch_request": True, "has_export_observation_packet": True},
        )()

    def apply_world_setup(self, _request: object) -> dict[str, object]:
        return {"agent_0": SimpleNamespace(entity_id=1, world_index=0)}

    def set_actions(self, actions: tuple[tuple[str, str], ...]) -> None:
        self.actions.append(actions)

    def step_batch(self) -> None:
        self.steps += 1
        self.identity.step += 1

    def read_observation_packet(self, refs: list[object], **_kwargs: object) -> object:
        return make_observation_packet(refs[0], self.steps)

    def native_snapshot_facts(self, _world_index: int = 0) -> object:
        facts = self.identity.snapshot_facts()
        return type(
            "NativeFacts",
            (),
            {
                "step": facts.step,
                "state_digest": facts.state_digest,
                "event_cursor": facts.event_cursor,
                "rng_digest": facts.rng_digest,
                "terminated": False,
                "episode_seed": facts.episode_seed,
            },
        )()


def _backend() -> tuple[RuntimeFacadeCandidateBackend, _Runtime, _Identity]:
    identity = _Identity()
    runtime = _Runtime(identity)
    backend = RuntimeFacadeCandidateBackend(
        runtime,
        agent_ids=("agent_0",),
        setup_applier=lambda value: value.apply_world_setup(object()),
        action_applier=lambda value, actions: value.set_actions(actions),
        identity_owner=identity,
        reward_reader=lambda _runtime, actions, _before, _after: {
            agent_id: 0 for agent_id, _action in actions
        },
    )
    return backend, runtime, identity


def _session(backend: RuntimeFacadeCandidateBackend) -> RuntimeCandidateSession:
    return RuntimeCandidateSession(
        session_id="session_adapter",
        backend_id="runtime_candidate",
        scenario_ref="scenario:session_adapter",
        config_digest=runtime_config_digest({"world_count": 1, "time_step_units": 1}),
        seed=42,
        agent_ids=("agent_0",),
        policy_ref="policy:test",
        backend=backend,
    )


def test_single_step_setup_request_result_contract() -> None:
    backend, runtime, _identity = _backend()
    session = _session(backend)
    adapter = RuntimeSessionAdapter(session)

    assert adapter.setup.session_id == session.spec.session_id
    assert adapter.setup.surface_id == TAKEOFF_SURFACE
    assert adapter.setup.sequence == 0
    assert adapter.setup.snapshot_digest == session.head().digest
    request = adapter.make_request({"agent_0": "takeoff"})
    assert request.payload["schema"] == RUNTIME_SESSION_ADAPTER_SCHEMA
    result = adapter.step(request)

    assert runtime.steps == 1
    assert adapter.sequence == 1
    assert result.sequence == 1
    assert result.request_digest == request.request_digest
    assert result.source_snapshot_digest == request.source_snapshot_digest
    assert result.target_snapshot_digest == session.head().digest
    assert result.transition.observation_provenance == OBS_FACADE_OBSERVATION_PACKET


def test_request_and_result_identity_provenance_is_bound() -> None:
    backend, _runtime, _identity = _backend()
    session = _session(backend)
    adapter = RuntimeSessionAdapter(session)
    request = adapter.make_request({"agent_0": "hold"})
    result = adapter.step(request)

    assert result.session_id == request.session_id
    assert result.surface_id == request.surface_id
    assert result.config_digest == request.config_digest
    assert result.transition.actions == request.actions
    assert result.transition.branch_digest == session.baseline.digest
    assert result.result_digest == content_digest(
        "experiment.runtime-session-result", adapter._result_payload(result)
    )


def test_malformed_stale_duplicate_and_unsupported_inputs_fail_closed() -> None:
    backend, runtime, identity = _backend()
    session = _session(backend)
    with pytest.raises(RuntimeCandidateError, match="unsupported.*surface"):
        RuntimeSessionAdapter(session, surface_id="air.execution.unknown.v1")
    with pytest.raises(RuntimeCandidateError, match="unsupported.*provenance"):
        RuntimeSessionAdapter(session, observation_provenance="synthetic")

    adapter = RuntimeSessionAdapter(session)
    request = adapter.make_request({"agent_0": "hold"})
    malformed = replace(request, sequence=99)
    with pytest.raises(RuntimeCandidateError, match="digest is malformed"):
        adapter.step(malformed)
    result = adapter.step(request)
    with pytest.raises(RuntimeCandidateError, match="duplicate.*request"):
        adapter.step(request)
    with pytest.raises(RuntimeCandidateError, match="unknown or stale"):
        adapter.accept_result(request, result)

    stale = adapter.make_request({"agent_0": "hold"})
    identity.step += 1
    with pytest.raises(RuntimeCandidateError, match="changed outside"):
        adapter.step(stale)
    assert runtime.steps == 1
    with pytest.raises(RuntimeCandidateError, match="failed closed"):
        adapter.make_request({"agent_0": "hold"})


def test_result_contract_rejects_tampered_digest_before_publication() -> None:
    backend, _runtime, _identity = _backend()
    session = _session(backend)
    adapter = RuntimeSessionAdapter(session)
    request = adapter.make_request({"agent_0": "hold"})
    adapter._pending[request.request_digest] = request
    transition = session.step(
        {"agent_0": "hold"}, observation_provenance=OBS_FACADE_OBSERVATION_PACKET
    )
    valid = adapter._result(request, transition)
    tampered = replace(valid, target_snapshot_digest=request.source_snapshot_digest)
    with pytest.raises(RuntimeCandidateError, match="digest is malformed"):
        adapter.accept_result(request, tampered)
    assert adapter.sequence == 0
    assert adapter.setup.snapshot_digest != session.head().digest


__all__ = ["RuntimeSessionStepResult"]
