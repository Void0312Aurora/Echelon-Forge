"""Maintained RuntimeFacade adapter boundary tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from python.experiment.runtime_candidate import RuntimeCandidateError
from python.experiment.runtime_candidate import RuntimeCandidateSession
from python.experiment.runtime_candidate import RuntimeSnapshotFacts
from python.experiment.runtime_candidate import runtime_config_digest
from python.experiment.runtime_facade_backend import RuntimeFacadeCandidateBackend
from python.experiment.runtime_facade_backend import RuntimeFacadeNativeIdentityOwner
from python.tasking_contracts.common.agent_contracts import OBS_FACADE_OBSERVATION_PACKET


AGENTS = ("agent_0", "agent_1")
UNSORTED_AGENTS = ("agent_1", "agent_0")


class _IdentityOwner:
    def __init__(self) -> None:
        self.step = 0

    def snapshot_facts(self) -> RuntimeSnapshotFacts:
        return RuntimeSnapshotFacts(
            step=self.step,
            state_digest=f"{self.step + 1:064x}",
            event_cursor=self.step,
            rng_digest=f"{self.step + 101:064x}",
        )


class _Runtime:
    def __init__(self, identity: _IdentityOwner) -> None:
        self.identity = identity
        self.setups = 0
        self.steps = 0
        self.actions: list[tuple[tuple[str, str], ...]] = []
        self.capabilities = SimpleNamespace(
            has_observation_batch_request=True,
            has_export_observation_packet=True,
        )

    def apply_world_setup(self, _request: object) -> dict[str, object]:
        self.setups += 1
        return {agent_id: ("baseline", agent_id) for agent_id in AGENTS}

    def set_actions(self, actions: tuple[tuple[str, str], ...]) -> None:
        self.actions.append(actions)

    def step_batch(self) -> None:
        self.steps += 1
        self.identity.step += 1

    def read_observation_packet(self, refs: list[object], **_kwargs: object) -> object:
        return {"refs": tuple(refs), "step": self.steps}

    def native_snapshot_facts(self, _world_index: int = 0) -> object:
        return SimpleNamespace(
            step=self.identity.step,
            state_digest=f"{self.identity.step + 1:064x}",
            event_cursor=self.identity.step,
            rng_digest=f"{self.identity.step + 101:064x}",
            terminated=False,
        )


def _setup(runtime: object) -> dict[str, object]:
    return runtime.apply_world_setup(object())


def _backend() -> tuple[RuntimeFacadeCandidateBackend, _Runtime, _IdentityOwner]:
    identity = _IdentityOwner()
    runtime = _Runtime(identity)

    def reward_reader(
        _runtime: object,
        actions: tuple[tuple[str, str], ...],
        _before: RuntimeSnapshotFacts,
        _after: RuntimeSnapshotFacts,
    ) -> dict[str, int]:
        return {agent_id: index for index, (agent_id, _action) in enumerate(actions)}

    backend = RuntimeFacadeCandidateBackend(
        runtime,
        agent_ids=AGENTS,
        setup_applier=_setup,
        action_applier=lambda value, actions: value.set_actions(actions),
        identity_owner=identity,
        reward_reader=reward_reader,
    )
    return backend, runtime, identity


def _session(backend: RuntimeFacadeCandidateBackend) -> RuntimeCandidateSession:
    return RuntimeCandidateSession(
        session_id="facade_session",
        backend_id="runtime_candidate",
        scenario_ref="scenario:maintained",
        config_digest=runtime_config_digest({"world_count": 1, "time_step_units": 1}),
        seed=19,
        agent_ids=AGENTS,
        policy_ref="policy:fixture",
        backend=backend,
    )


def test_maintained_facade_step_uses_native_identity_and_packets() -> None:
    backend, runtime, _identity = _backend()
    session = _session(backend)

    transition = session.step(
        {"agent_0": "hold", "agent_1": "turn"},
        observation_provenance=OBS_FACADE_OBSERVATION_PACKET,
    )

    assert runtime.steps == 1
    assert runtime.setups == 1
    assert runtime.actions == [(('agent_0', 'hold'), ('agent_1', 'turn'))]
    assert transition.rewards == (("agent_0", 0), ("agent_1", 1))
    assert session.capabilities.can_agent_observation_refs
    assert not session.capabilities.can_fork
    assert not session.capabilities.can_snapshot_restore
    assert len(session.agent_observation_packet_series("agent_0")) == 2


def test_maintained_facade_keeps_fork_disabled_without_branch_action_owner() -> None:
    backend, _runtime, _identity = _backend()
    session = _session(backend)

    assert not backend.supports_fork
    assert not backend.supports_checkpoints
    assert not session.capabilities.can_fork
    assert not session.capabilities.can_snapshot_restore


def test_native_identity_owner_reads_bound_facade_facts() -> None:
    runtime = _Runtime(_IdentityOwner())
    owner = RuntimeFacadeNativeIdentityOwner(runtime)

    facts = owner.snapshot_facts()

    assert facts == RuntimeSnapshotFacts(
        step=0,
        state_digest="1".zfill(64),
        event_cursor=0,
        rng_digest="65".zfill(64),
        terminated=False,
    )


def test_maintained_facade_rejects_external_identity_mutation() -> None:
    backend, runtime, identity = _backend()
    session = _session(backend)
    identity.step = 1

    with pytest.raises(RuntimeCandidateError, match="outside the session step boundary"):
        session.step(
            {"agent_0": "hold", "agent_1": "hold"},
            observation_provenance=OBS_FACADE_OBSERVATION_PACKET,
        )
    assert runtime.steps == 0


def test_maintained_facade_canonicalizes_action_pairs_for_session_agents() -> None:
    identity = _IdentityOwner()
    runtime = _Runtime(identity)
    backend = RuntimeFacadeCandidateBackend(
        runtime,
        agent_ids=UNSORTED_AGENTS,
        setup_applier=_setup,
        action_applier=lambda value, actions: value.set_actions(actions),
        identity_owner=identity,
        reward_reader=lambda _runtime, actions, _before, _after: {
            agent_id: index for index, (agent_id, _action) in enumerate(actions)
        },
    )
    backend.initial_snapshot()
    backend.step((('agent_1', 'turn'), ('agent_0', 'hold')))

    assert runtime.actions == [(('agent_0', 'hold'), ('agent_1', 'turn'))]


def test_maintained_facade_requires_identity_and_observation_capabilities() -> None:
    identity = _IdentityOwner()
    runtime = _Runtime(identity)
    runtime.capabilities.has_export_observation_packet = False
    with pytest.raises(RuntimeCandidateError, match="packet bindings"):
        RuntimeFacadeCandidateBackend(
            runtime,
            agent_ids=AGENTS,
            setup_applier=_setup,
            action_applier=lambda _runtime, _actions: None,
            identity_owner=identity,
            reward_reader=lambda *_args: {agent_id: 0 for agent_id in AGENTS},
        )


def test_maintained_facade_rejects_malformed_native_digests() -> None:
    identity = _IdentityOwner()
    identity.snapshot_facts = lambda: RuntimeSnapshotFacts(  # type: ignore[method-assign]
        step=0,
        state_digest="A" * 64,
        event_cursor=0,
        rng_digest="b" * 64,
    )
    runtime = _Runtime(identity)
    backend = RuntimeFacadeCandidateBackend(
        runtime,
        agent_ids=AGENTS,
        setup_applier=_setup,
        action_applier=lambda _runtime, _actions: None,
        identity_owner=identity,
        reward_reader=lambda *_args: {agent_id: 0 for agent_id in AGENTS},
    )

    with pytest.raises(RuntimeCandidateError, match="malformed digests"):
        backend.initial_snapshot()


def test_maintained_facade_rejects_setup_without_exact_agent_refs() -> None:
    identity = _IdentityOwner()
    runtime = _Runtime(identity)
    with pytest.raises(RuntimeCandidateError, match="exactly one maintained ref"):
        RuntimeFacadeCandidateBackend(
            runtime,
            agent_ids=AGENTS,
            setup_applier=lambda _runtime: {"agent_0": object()},
            action_applier=lambda _runtime, _actions: None,
            identity_owner=identity,
            reward_reader=lambda *_args: {agent_id: 0 for agent_id in AGENTS},
        )


def test_maintained_facade_requires_native_identity_owner() -> None:
    runtime = _Runtime(_IdentityOwner())
    with pytest.raises(RuntimeCandidateError, match="native identity owner"):
        RuntimeFacadeCandidateBackend(
            runtime,
            agent_ids=AGENTS,
            setup_applier=_setup,
            action_applier=lambda _runtime, _actions: None,
            identity_owner=object(),
            reward_reader=lambda *_args: {agent_id: 0 for agent_id in AGENTS},
        )


def test_bound_facade_branch_owner_runs_session_checkpoint_and_nested_fork() -> None:
    ef_py = pytest.importorskip("ef_py")
    runtime = ef_py.RuntimeFacade(1)
    agent_ids = ("agent_0",)

    def setup(value: object) -> dict[str, object]:
        request = ef_py.BatchWorldSetupRequest()
        request.seeds = [42]
        request.time_steps = [1.0]
        spawn = ef_py.WorldSpawnRequest()
        spawn.type_name = "Aircraft"
        spawn.entity_name = "controlled_aircraft"
        spawn.is_agent = True
        spawn.z = 3000.0
        spawn.vx = 150.0
        request.spawn_requests = [spawn]
        result = value.apply_world_setup(request)
        ref = ef_py.WorldEntityRef()
        ref.entity_id = result.entity_ids[0]
        return {"agent_0": ref}

    def assignment(_owner: object, actions: tuple[tuple[str, str], ...]) -> list[object]:
        action = ef_py.PilotAction()
        action.active = True
        action.throttle = 0.0 if actions[0][1] == "idle" else 1.0
        ref = ef_py.WorldEntityRef()
        ref.entity_id = entity_id[0]
        item = ef_py.WorldPilotActionAssignment()
        item.entity_id = ref.entity_id
        item.action = action
        return [item]

    entity_id = [0]

    def setup_and_remember(value: object) -> dict[str, object]:
        refs = setup(value)
        entity_id[0] = refs["agent_0"].entity_id
        return refs

    def apply(value: object, actions: tuple[tuple[str, str], ...]) -> None:
        value.set_pilot_actions_batch(assignment(value, actions))

    def rewards(
        _value: object,
        _actions: tuple[tuple[str, str], ...],
        _before: RuntimeSnapshotFacts,
        _after: RuntimeSnapshotFacts,
    ) -> dict[str, int]:
        return {"agent_0": 0}

    branch_refs: list[object] = []

    def branch_ref_factory(handle: object, _agent_id: str, baseline: object) -> object:
        branch_refs.append(handle)
        return baseline

    backend = RuntimeFacadeCandidateBackend(
        runtime,
        agent_ids=agent_ids,
        setup_applier=setup_and_remember,
        action_applier=apply,
        branch_action_applier=assignment,
        branch_ref_factory=branch_ref_factory,
        reward_reader=rewards,
    )
    session = RuntimeCandidateSession(
        session_id="bound_facade_branch",
        backend_id="runtime_candidate",
        scenario_ref="scenario:aircraft",
        config_digest=runtime_config_digest({"world_count": 1, "time_step_units": 1}),
        seed=42,
        agent_ids=agent_ids,
        policy_ref="policy:test",
        backend=backend,
    )
    assert session.capabilities.can_fork
    assert session.capabilities.can_snapshot_restore
    session.step({"agent_0": "idle"}, observation_provenance=OBS_FACADE_OBSERVATION_PACKET)
    saved = session.checkpoint()
    branch = session.fork(
        session.baseline,
        saved,
        intervention={"agent_0": "idle"},
        label="idle_child",
        horizon=1,
    )
    transition = session.step_branch(
        branch, {"agent_0": "idle"}, observation_provenance=OBS_FACADE_OBSERVATION_PACKET
    )
    assert transition.target_snapshot_digest
    nested = session.fork(
        branch,
        session.head(branch),
        intervention={"agent_0": "idle"},
        label="nested",
        horizon=1,
    )
    assert session.step_branch(
        nested, {"agent_0": "idle"}, observation_provenance=OBS_FACADE_OBSERVATION_PACKET
    ).target_snapshot_digest
    assert len(session.agent_observation_packet_series("agent_0", branch)) == 2
    assert branch_refs
