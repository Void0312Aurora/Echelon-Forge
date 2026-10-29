"""P3-A bounded runtime-candidate adapter tests."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from python.experiment.contracts import ContractError
from python.experiment.runtime_candidate import RuntimeCandidateError
from python.experiment.runtime_candidate import RuntimeKernelCandidateBackend
from python.experiment.runtime_candidate import RuntimeCandidateSession
from python.experiment.runtime_candidate import RuntimeNativeBranchAdmission
from python.experiment.runtime_candidate import RuntimeSnapshotFacts
from python.experiment.runtime_candidate import RuntimeStepResult
from python.experiment.runtime_candidate import runtime_config_digest
from python.experiment.trace import manifest_from_payload


AGENTS = ("agent_0", "agent_1")
OBSERVATION = "decision_belief_packet"


@dataclass
class FakeBackend:
    invalid_step: int | None = None
    terminal_at: int | None = None
    cursor: int = 0

    def initial_snapshot(self) -> RuntimeSnapshotFacts:
        return RuntimeSnapshotFacts(
            step=0,
            state_digest="a" * 64,
            event_cursor=0,
            rng_digest="b" * 64,
        )

    def step(self, actions: tuple[tuple[str, str], ...]) -> RuntimeStepResult:
        self.cursor += 1
        step = self.invalid_step if self.invalid_step is not None else self.cursor
        return RuntimeStepResult(
            snapshot=RuntimeSnapshotFacts(
                step=step,
                state_digest=f"{self.cursor:064x}",
                event_cursor=self.cursor,
                rng_digest=f"{self.cursor + 100:064x}",
                terminated=self.terminal_at == self.cursor,
            ),
            rewards={agent_id: index for index, (agent_id, _) in enumerate(actions)},
        )


@dataclass
class NativeBranchBackend(FakeBackend):
    branch_cursor: dict[str, int] | None = None

    def __post_init__(self) -> None:
        self.branch_cursor = {}

    def fork_branch(
        self,
        snapshot: RuntimeSnapshotFacts,
        intervention: tuple[tuple[str, str], ...],
        label: str,
        horizon: int,
    ) -> RuntimeNativeBranchAdmission:
        del intervention, label, horizon
        handle = f"branch-{len(self.branch_cursor) + 1}"
        self.branch_cursor[handle] = snapshot.step
        return RuntimeNativeBranchAdmission(snapshot=snapshot, handle=handle)

    def step_branch(
        self, handle: object, actions: tuple[tuple[str, str], ...]
    ) -> RuntimeStepResult:
        assert isinstance(handle, str)
        assert self.branch_cursor is not None
        self.branch_cursor[handle] += 1
        step = self.branch_cursor[handle]
        return RuntimeStepResult(
            snapshot=RuntimeSnapshotFacts(
                step=step,
                state_digest=f"{1000 + step:064x}",
                event_cursor=1000 + step,
                rng_digest=f"{2000 + step:064x}",
            ),
            rewards={agent_id: index for index, (agent_id, _) in enumerate(actions)},
        )


@dataclass
class AgentRefBranchBackend(NativeBranchBackend):
    supports_agent_observation_refs: bool = True

    def observation_refs(self, handle: object | None = None) -> dict[str, object]:
        branch = "baseline" if handle is None else str(handle)
        return {agent_id: (branch, agent_id, self.cursor) for agent_id in AGENTS}


class CheckpointBackend(NativeBranchBackend):
    """Deterministic owner seam for rejection and failure injection tests."""

    reward_drift = False

    def checkpoint_branch(
        self, handle: object | None, snapshot: RuntimeSnapshotFacts
    ) -> RuntimeNativeBranchAdmission:
        if handle is not None:
            assert self.branch_cursor[handle] == snapshot.step
        return self.fork_branch(snapshot, (), "checkpoint", 1)

    def fork_from_branch(
        self,
        handle: object,
        snapshot: RuntimeSnapshotFacts,
        intervention: tuple[tuple[str, str], ...],
        label: str,
        horizon: int,
    ) -> RuntimeNativeBranchAdmission:
        assert self.branch_cursor[handle] == snapshot.step
        return self.fork_branch(snapshot, intervention, label, horizon)

    def step_branch(
        self, handle: object, actions: tuple[tuple[str, str], ...]
    ) -> RuntimeStepResult:
        self.branch_cursor[handle] += 1
        step = self.branch_cursor[handle]
        return RuntimeStepResult(
            snapshot=RuntimeSnapshotFacts(
                step=step,
                state_digest=f"{step:064x}",
                event_cursor=step,
                rng_digest=f"{step + 100:064x}",
                terminated=self.terminal_at == step,
            ),
            rewards={
                agent: index + int(self.reward_drift) for index, (agent, _) in enumerate(actions)
            },
        )


def _session(backend: FakeBackend | None = None) -> RuntimeCandidateSession:
    return RuntimeCandidateSession(
        session_id="runtime_session",
        backend_id="runtime_candidate",
        scenario_ref="scenario:bounded",
        config_digest=runtime_config_digest({"world_count": 1, "time_step_units": 1}),
        seed=19,
        agent_ids=AGENTS,
        policy_ref="policy:fixture",
        backend=backend or FakeBackend(),
    )


def _actions() -> dict[str, str]:
    return {"agent_0": "hold", "agent_1": "hold"}


def test_candidate_session_records_authoritative_identity_and_manifest() -> None:
    session = _session()
    transition = session.step(_actions(), observation_provenance=OBSERVATION)

    assert session.spec.evidence_label == "runtime_candidate"
    assert session.capabilities.can_step
    assert not session.capabilities.can_snapshot_restore
    assert not session.capabilities.can_fork
    assert transition.step == 0
    assert transition.source_snapshot_digest == session.baseline.origin_snapshot_digest
    assert transition.target_snapshot_digest == session.head().digest
    assert session.manifest().branches[0].transitions == (transition,)


def test_identical_backend_inputs_produce_identical_manifest_identity() -> None:
    first, second = _session(), _session()
    for session in (first, second):
        session.step(_actions(), observation_provenance=OBSERVATION)
        session.step(_actions(), observation_provenance=OBSERVATION)
    assert first.manifest().digest == second.manifest().digest
    assert first.manifest().to_payload() == second.manifest().to_payload()


def test_candidate_rejects_invalid_provenance_before_backend_step() -> None:
    backend = FakeBackend()
    session = _session(backend)
    with pytest.raises(RuntimeCandidateError, match="provenance"):
        session.step(_actions(), observation_provenance="raw_world_truth")
    assert backend.cursor == 0
    assert session.manifest().branches[0].transitions == ()


def test_candidate_rejects_incomplete_actions_and_rewards() -> None:
    session = _session()
    with pytest.raises(RuntimeCandidateError, match="cover exactly"):
        session.step({"agent_0": "hold"}, observation_provenance=OBSERVATION)

    class BadRewards(FakeBackend):
        def step(self, actions: tuple[tuple[str, str], ...]) -> RuntimeStepResult:
            result = super().step(actions)
            return RuntimeStepResult(result.snapshot, {"agent_0": 1})

    with pytest.raises(RuntimeCandidateError, match="rewards"):
        _session(BadRewards()).step(_actions(), observation_provenance=OBSERVATION)


def test_candidate_rejects_backend_step_identity_drift() -> None:
    with pytest.raises(RuntimeCandidateError, match="does not match expected"):
        _session(FakeBackend(invalid_step=3)).step(_actions(), observation_provenance=OBSERVATION)


def test_candidate_fails_closed_for_fork_and_restore() -> None:
    session = _session()
    with pytest.raises(RuntimeCandidateError, match="fork"):
        session.fork(session.baseline, session.head(), intervention=_actions(), label="branch")
    with pytest.raises(RuntimeCandidateError, match="restore"):
        session.restore(session.head())


def test_candidate_uses_native_sibling_branch_and_preserves_parent_head() -> None:
    backend = NativeBranchBackend()
    session = _session(backend)
    session.step(_actions(), observation_provenance=OBSERVATION)
    origin = session.head()
    child = session.fork(
        session.baseline,
        origin,
        intervention={"agent_0": "commit"},
        label="commit",
        horizon=2,
    )
    assert session.capabilities.can_fork
    assert session.head(child) == origin
    session.step_branch(
        child,
        {"agent_0": "commit", "agent_1": "hold"},
        observation_provenance=OBSERVATION,
    )
    assert session.head(session.baseline) == origin
    assert session.head(child).step == origin.step + 1
    assert len(session.manifest().branches) == 2


def test_candidate_records_agent_observation_refs_per_branch_without_inference() -> None:
    backend = AgentRefBranchBackend()
    session = _session(backend)
    assert session.has_agent_observation_refs
    assert session.capabilities.can_agent_observation_refs
    session.step(_actions(), observation_provenance=OBSERVATION)
    parent_refs = session.agent_observation_ref_series("agent_0")
    assert len(parent_refs) == 2
    child = session.fork(
        session.baseline,
        session.head(),
        intervention={"agent_0": "commit"},
        label="commit",
        horizon=1,
    )
    assert session.agent_observation_ref_series("agent_0", child) == (
        ("branch-1", "agent_0", 1),
    )
    session.step_branch(
        child,
        {"agent_0": "commit", "agent_1": "hold"},
        observation_provenance=OBSERVATION,
    )
    assert len(session.agent_observation_ref_series("agent_0", child)) == 2
    joined = session.agent_observation_ref_sources("agent_0", branches=(child,))
    assert tuple(joined) == ((session.manifest().digest, child.digest),)
    with pytest.raises(RuntimeCandidateError, match="no maintained Agent observation ref"):
        missing = _session()
        assert not missing.capabilities.can_agent_observation_refs
        missing.agent_observation_ref_series("agent_0")


def test_candidate_rejects_partial_or_identity_drifting_native_branch_backends() -> None:
    class PartialBackend(FakeBackend):
        def fork_branch(self, *args: object) -> RuntimeNativeBranchAdmission:
            raise AssertionError("partial capability must remain closed")

    partial = _session(PartialBackend())
    assert not partial.capabilities.can_fork
    with pytest.raises(RuntimeCandidateError, match="does not support branch fork"):
        partial.fork(partial.baseline, partial.head(), intervention={"agent_0": "hold"}, label="x")

    class DriftBackend(NativeBranchBackend):
        def fork_branch(
            self,
            snapshot: RuntimeSnapshotFacts,
            intervention: tuple[tuple[str, str], ...],
            label: str,
            horizon: int,
        ) -> RuntimeNativeBranchAdmission:
            admission = super().fork_branch(snapshot, intervention, label, horizon)
            return RuntimeNativeBranchAdmission(
                snapshot=RuntimeSnapshotFacts(
                    step=snapshot.step,
                    state_digest="f" * 64,
                    event_cursor=snapshot.event_cursor,
                    rng_digest=snapshot.rng_digest,
                ),
                handle=admission.handle,
            )

    drift = _session(DriftBackend())
    with pytest.raises(RuntimeCandidateError, match="changed the parent state identity"):
        drift.fork(drift.baseline, drift.head(), intervention={"agent_0": "hold"}, label="x")


def test_terminal_result_rejects_following_step() -> None:
    session = _session(FakeBackend(terminal_at=1))
    transition = session.step(_actions(), observation_provenance=OBSERVATION)
    assert transition.terminated
    with pytest.raises(RuntimeCandidateError, match="terminated"):
        session.step(_actions(), observation_provenance=OBSERVATION)


def test_config_digest_rejects_float_profile_values() -> None:
    with pytest.raises(ContractError, match="floats"):
        runtime_config_digest({"time_step": 0.1})


def test_runtime_session_consumes_real_native_kernel_sibling() -> None:
    ef_py = pytest.importorskip("ef_py")
    candidate_py = pytest.importorskip("ef_runtime_candidate_py")
    assert not hasattr(ef_py, "RuntimeKernelCandidate")
    native = candidate_py.RuntimeKernelCandidate(0x52544B2D50595448, 901, True, 19)
    backend = RuntimeKernelCandidateBackend(native, AGENTS)
    session = _session(backend)
    session.step(_actions(), observation_provenance=OBSERVATION)
    parent = session.head()
    child = session.fork(
        session.baseline,
        parent,
        intervention={"agent_0": "commit"},
        label="native_commit",
        horizon=2,
    )
    assert session.head(child) == parent
    session.step_branch(
        child,
        {"agent_0": "commit", "agent_1": "hold"},
        observation_provenance=OBSERVATION,
    )
    assert session.head(child).step == parent.step + 1
    assert session.head(session.baseline) == parent
    assert native.shutdown()


def test_saved_checkpoint_restores_after_parent_termination_and_replays_without_rewriting() -> None:
    session = _session(CheckpointBackend(terminal_at=3))
    session.step(_actions(), observation_provenance=OBSERVATION)
    saved = session.checkpoint()
    assert session.checkpoint() == saved
    for _ in range(2):
        session.step(_actions(), observation_provenance=OBSERVATION)
    parent_head = session.head()
    parent_trace = session.trace(session.baseline)
    assert parent_trace.transitions[-1].terminated
    with pytest.raises(RuntimeCandidateError, match="terminal"):
        session.checkpoint()

    restored = session.restore(saved, intervention=_actions(), label="restored", horizon=2)
    for _ in range(2):
        session.step_branch(restored, _actions(), observation_provenance=OBSERVATION)
    replayed = session.replay(session.baseline, saved, label="verified_replay")
    assert session.capabilities.can_snapshot_restore
    assert session.head(restored) == session.head(replayed) == parent_head
    assert session.trace(session.baseline) == parent_trace
    assert [item.target_snapshot_digest for item in session.trace(replayed).transitions] == [
        item.target_snapshot_digest for item in parent_trace.transitions[1:]
    ]
    assert manifest_from_payload(session.manifest().to_payload()) == session.manifest()


def test_historical_and_descendant_forks_use_their_own_native_handles() -> None:
    session = _session(CheckpointBackend())
    session.step(_actions(), observation_provenance=OBSERVATION)
    saved = session.checkpoint()
    session.step(_actions(), observation_provenance=OBSERVATION)
    child = session.fork(session.baseline, saved, intervention=_actions(), label="history")
    session.step_branch(child, _actions(), observation_provenance=OBSERVATION)
    child_saved = session.checkpoint(child)
    session.step_branch(child, _actions(), observation_provenance=OBSERVATION)
    descendant = session.fork(child, child_saved, intervention=_actions(), label="descendant")
    sibling = session.fork(child, session.head(child), intervention=_actions(), label="current")
    child_head = session.head(child)
    session.step_branch(descendant, _actions(), observation_provenance=OBSERVATION)
    assert session.head(descendant) == child_head == session.head(sibling)
    assert descendant.parent_digest == child.digest
    assert descendant.depth == child.depth + 1
    assert session.head().step == 2


def test_restore_rejects_unsaved_foreign_and_wrong_branch_snapshots_without_allocating() -> None:
    backend = CheckpointBackend()
    session = _session(backend)
    origin = session.head()
    session.step(_actions(), observation_provenance=OBSERVATION)
    saved = session.checkpoint()
    child = session.restore(saved, intervention=_actions(), label="child")
    before = session.manifest()
    handles = len(backend.branch_cursor)
    for snapshot, parent in (
        (origin, session.baseline),
        (saved, child),
        (replace(saved, state_digest="f" * 64), session.baseline),
        (replace(saved, session_digest="e" * 64), session.baseline),
    ):
        with pytest.raises(RuntimeCandidateError, match="checkpointed"):
            session.restore(snapshot, parent=parent, intervention=_actions(), label="invalid")
    with pytest.raises(RuntimeCandidateError, match="intervention"):
        session.restore(saved)
    with pytest.raises(RuntimeCandidateError, match="duplicate"):
        session.restore(saved, intervention=_actions(), label="child")
    with pytest.raises(ContractError, match="label"):
        session.restore(saved, intervention=_actions(), label="invalid label")
    with pytest.raises(RuntimeCandidateError, match="horizon"):
        session.restore(saved, intervention=_actions(), label="bad_horizon", horizon=0)
    assert len(backend.branch_cursor) == handles
    assert session.manifest() == before


def test_checkpoint_identity_drift_does_not_publish_a_restore_source() -> None:
    class Drift(CheckpointBackend):
        def checkpoint_branch(
            self, handle: object | None, snapshot: RuntimeSnapshotFacts
        ) -> RuntimeNativeBranchAdmission:
            result = super().checkpoint_branch(handle, snapshot)
            return replace(result, snapshot=replace(snapshot, rng_digest="f" * 64))

    session = _session(Drift())
    session.step(_actions(), observation_provenance=OBSERVATION)
    before = session.manifest()
    with pytest.raises(RuntimeCandidateError, match="identity"):
        session.checkpoint()
    with pytest.raises(RuntimeCandidateError, match="checkpointed"):
        session.restore(session.head(), intervention=_actions())
    assert session.manifest() == before


def test_divergent_replay_is_discarded_and_saved_checkpoint_remains_usable() -> None:
    backend = CheckpointBackend()
    session = _session(backend)
    session.step(_actions(), observation_provenance=OBSERVATION)
    saved = session.checkpoint()
    with pytest.raises(RuntimeCandidateError, match="no recorded continuation"):
        session.replay(session.baseline, saved, label="empty")
    session.step(_actions(), observation_provenance=OBSERVATION)
    before = session.manifest()
    backend.reward_drift = True
    with pytest.raises(RuntimeCandidateError, match="diverged at step 1"):
        session.replay(session.baseline, saved, label="replay")
    assert session.manifest() == before
    backend.reward_drift = False
    replayed = session.replay(session.baseline, saved, label="replay")
    assert session.head(replayed) == session.head()


def test_partial_checkpoint_seam_remains_disabled() -> None:
    class Partial(NativeBranchBackend):
        def checkpoint_branch(self, *args: object) -> RuntimeNativeBranchAdmission:
            raise AssertionError("partial seam must remain disabled")

    session = _session(Partial())
    assert not session.capabilities.can_snapshot_restore
    with pytest.raises(RuntimeCandidateError, match="does not support"):
        session.checkpoint()


def test_native_wrapper_reports_only_capabilities_exposed_by_the_native_producer() -> None:
    class StepOnlyNative:
        def start(self) -> bool:
            return True

        def snapshot_facts(self) -> RuntimeSnapshotFacts:
            return FakeBackend().initial_snapshot()

    session = _session(RuntimeKernelCandidateBackend(StepOnlyNative(), AGENTS))
    assert not session.capabilities.can_fork
    assert not session.capabilities.can_snapshot_restore


@pytest.mark.parametrize("field", ["state_digest", "rng_digest", "event_cursor", "terminated"])
def test_replay_rejects_drift_in_every_native_snapshot_component(field: str) -> None:
    class Drift(CheckpointBackend):
        def step_branch(
            self, handle: object, actions: tuple[tuple[str, str], ...]
        ) -> RuntimeStepResult:
            result = super().step_branch(handle, actions)
            bad = True if field == "terminated" else 500 if field == "event_cursor" else "f" * 64
            return replace(result, snapshot=replace(result.snapshot, **{field: bad}))

    session = _session(Drift())
    session.step(_actions(), observation_provenance=OBSERVATION)
    saved = session.checkpoint()
    session.step(_actions(), observation_provenance=OBSERVATION)
    before = session.manifest()
    with pytest.raises(RuntimeCandidateError, match="diverged"):
        session.replay(session.baseline, saved, label="drift")
    assert session.manifest() == before


@pytest.mark.parametrize("seed", [19, 83, 191])
def test_real_aircraft_session_checkpoint_restore_nested_fork_and_verified_replay(
    seed: int,
) -> None:
    ef_py = pytest.importorskip("ef_py")
    candidate_py = pytest.importorskip("ef_runtime_candidate_py")
    native = candidate_py.RuntimeKernelCandidate(0x52544B2D5245504C, seed, True, seed)
    backend = RuntimeKernelCandidateBackend(native, AGENTS)
    try:
        spawn = ef_py.WorldSpawnRequest()
        spawn.type_name = "Aircraft"
        spawn.z = 3000.0
        spawn.vx = 150.0
        assert native.spawn_unit(spawn)
        session = RuntimeCandidateSession(
            session_id="aircraft_replay",
            backend_id="runtime_candidate",
            scenario_ref="scenario:single_aircraft",
            seed=seed,
            agent_ids=AGENTS,
            config_digest=runtime_config_digest({"altitude_m": 3000, "speed_mps": 150}),
            policy_ref="policy:default_native_step",
            backend=backend,
        )
        assert session.capabilities.can_snapshot_restore
        initial = session.head()
        with pytest.raises(RuntimeCandidateError, match="rejected"):
            session.checkpoint()
        assert session.head() == initial
        session.step(_actions(), observation_provenance=OBSERVATION)
        saved = session.checkpoint()
        for _ in range(3):
            session.step(_actions(), observation_provenance=OBSERVATION)
        parent_trace = session.trace(session.baseline)
        parent_head = session.head()
        assert saved.state_digest != parent_head.state_digest
        restored = session.restore(saved, intervention=_actions(), label="restored", horizon=3)
        for expected in parent_trace.transitions[1:]:
            actual = session.step_branch(restored, _actions(), observation_provenance=OBSERVATION)
            assert replace(actual, branch_digest=expected.branch_digest) == expected
        assert session.head(restored) == parent_head
        nested_saved = session.checkpoint(restored)
        session.step_branch(restored, _actions(), observation_provenance=OBSERVATION)
        nested = session.fork(restored, nested_saved, intervention=_actions(), label="nested")
        sibling = session.restore(saved, intervention=_actions(), label="sibling")
        session.step_branch(nested, _actions(), observation_provenance=OBSERVATION)
        assert session.head(nested) == session.head(restored)
        assert session.head(sibling) == saved
        replayed = session.replay(session.baseline, saved, label="verified_replay")
        assert session.head(replayed) == parent_head
        assert session.head() == parent_head
        assert session.trace(session.baseline) == parent_trace
        assert manifest_from_payload(session.manifest().to_payload()) == session.manifest()
    finally:
        assert native.shutdown()
