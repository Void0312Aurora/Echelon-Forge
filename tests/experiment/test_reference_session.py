from __future__ import annotations

import pytest

from python.experiment.contracts import BranchRef
from python.experiment.contracts import ContractError
from python.experiment.contracts import SnapshotRef
from python.experiment.reference_session import REFERENCE_BACKEND
from python.experiment.reference_session import DelayedCommitmentWorld
from python.experiment.reference_session import ReferenceSession
from python.experiment.reference_session import SessionError
from python.experiment.trace import manifest_from_payload

AGENTS = ("agent_0", "agent_1")
BELIEF = "decision_belief_packet"


def _session(seed: int = 7) -> ReferenceSession:
    return ReferenceSession.open(
        session_id="toy_session", seed=seed, agent_ids=AGENTS, policy_ref="toy_policy:hold"
    )


def _hold() -> dict[str, str]:
    return {agent: "hold" for agent in AGENTS}


def _step(session: ReferenceSession, branch: BranchRef, actions: dict[str, str]) -> None:
    session.step(branch, actions, observation_provenance=BELIEF)


def _run(session: ReferenceSession, branch: BranchRef, steps: int, actions: dict[str, str]) -> None:
    for _ in range(steps):
        _step(session, branch, actions)


def test_session_identity_names_the_reference_backend_and_toy_evidence() -> None:
    spec = _session().spec
    assert spec.backend == REFERENCE_BACKEND
    assert spec.evidence_label == "toy"
    assert spec.agent_ids == AGENTS


def test_identical_inputs_reproduce_identical_traces() -> None:
    first, second = _session(), _session()
    for session in (first, second):
        _run(session, session.baseline, 5, _hold())
    assert first.manifest().digest == second.manifest().digest
    assert first.manifest().to_payload() == second.manifest().to_payload()


def test_seed_is_bound_into_every_snapshot_component() -> None:
    first, second = _session(seed=7), _session(seed=8)
    first_head, second_head = first.head(first.baseline), second.head(second.baseline)
    assert first_head.session_digest != second_head.session_digest
    assert first_head.rng_digest != second_head.rng_digest
    assert first_head.state_digest == second_head.state_digest


def test_snapshot_step_tracks_the_world_step_exactly() -> None:
    sessions = [_session() for _ in range(4)]
    for session in sessions:
        _run(session, session.baseline, 3, _hold())
        heads = [item.step for item in session.trace(session.baseline).transitions]
        assert heads == [0, 1, 2]
        assert session.head(session.baseline).step == 3
    assert len({session.manifest().digest for session in sessions}) == 1


def test_restore_reproduces_the_continuation_exactly() -> None:
    session = _session()
    _run(session, session.baseline, 2, _hold())
    snapshot = session.head(session.baseline)
    _run(session, session.baseline, 4, _hold())
    original = session.trace(session.baseline).transitions[2:]

    replay = session.fork(session.baseline, snapshot, intervention={"agent_0": "hold"}, label="replay")
    _run(session, replay, 4, _hold())
    replayed = session.trace(replay).transitions
    assert [item.target_snapshot_digest for item in replayed] == [
        item.target_snapshot_digest for item in original
    ]
    assert [item.rewards for item in replayed] == [item.rewards for item in original]


def test_forked_branch_does_not_mutate_parent_or_sibling() -> None:
    session = _session()
    _run(session, session.baseline, 2, _hold())
    origin = session.head(session.baseline)
    parent_before = session.trace(session.baseline)

    commit = session.fork(session.baseline, origin, intervention={"agent_0": "commit"}, label="commit")
    hold = session.fork(session.baseline, origin, intervention={"agent_0": "hold"}, label="hold")
    _run(session, commit, 3, {"agent_0": "commit", "agent_1": "hold"})
    sibling_head = session.head(hold)

    assert session.trace(session.baseline) == parent_before
    assert session.head(hold) == sibling_head == origin
    _run(session, hold, 3, _hold())
    assert session.head(commit) != session.head(hold)
    assert commit.parent_digest == hold.parent_digest == session.baseline.digest


def test_fork_requires_a_snapshot_recorded_on_the_parent_branch() -> None:
    session = _session()
    _run(session, session.baseline, 2, _hold())
    other = _session(seed=9)
    foreign = other.head(other.baseline)
    with pytest.raises(SessionError, match="not recorded"):
        session.fork(session.baseline, foreign, intervention={"agent_0": "commit"}, label="x")
    commit = session.fork(
        session.baseline, session.head(session.baseline), intervention={"agent_0": "commit"}, label="c"
    )
    _run(session, commit, 1, {"agent_0": "commit", "agent_1": "hold"})
    with pytest.raises(SessionError, match="not recorded"):
        session.fork(session.baseline, session.head(commit), intervention={"agent_0": "hold"}, label="h")


def test_intervention_is_applied_to_the_first_branch_step() -> None:
    session = _session()
    commit = session.fork(
        session.baseline, session.head(session.baseline), intervention={"agent_0": "commit"}, label="c"
    )
    with pytest.raises(SessionError, match="intervention"):
        _step(session, commit, _hold())
    _step(session, commit, {"agent_0": "commit", "agent_1": "hold"})
    _step(session, commit, _hold())


def test_step_rejects_unknown_agents_actions_and_branches() -> None:
    session = _session()
    with pytest.raises(SessionError, match="agents"):
        _step(session, session.baseline, {"agent_0": "hold"})
    with pytest.raises(SessionError, match="action"):
        _step(session, session.baseline, {"agent_0": "fly", "agent_1": "hold"})
    other = _session(seed=11)
    stranger = BranchRef.root(other.head(other.baseline))
    with pytest.raises(SessionError, match="unknown branch"):
        _step(session, stranger, _hold())


def test_step_rejects_policy_inputs_outside_maintained_provenance() -> None:
    session = _session()
    for label in ("raw_world_truth", "diagnostics_oracle"):
        with pytest.raises(ContractError, match="provenance"):
            session.step(session.baseline, _hold(), observation_provenance=label)
    assert session.trace(session.baseline).transitions == ()


def test_terminated_branch_cannot_step_further() -> None:
    session = ReferenceSession.open(
        session_id="toy_session",
        seed=7,
        agent_ids=AGENTS,
        policy_ref="toy_policy:hold",
        world=DelayedCommitmentWorld(max_steps=2),
    )
    _run(session, session.baseline, 2, _hold())
    assert session.trace(session.baseline).transitions[-1].terminated
    with pytest.raises(SessionError, match="terminated"):
        _step(session, session.baseline, _hold())
    with pytest.raises(SessionError, match="terminal"):
        session.fork(
            session.baseline, session.head(session.baseline), intervention={"agent_0": "commit"}, label="c"
        )


def test_branch_returns_match_the_toy_rollout_model() -> None:
    from python.experiment.counterfactual_toy import rollout_branch

    session = _session()
    origin = session.head(session.baseline)
    joint = session.fork(
        session.baseline, origin, intervention={"agent_0": "commit", "agent_1": "commit"}, label="joint"
    )
    _run(session, joint, 8, {"agent_0": "commit", "agent_1": "commit"})
    _run(session, session.baseline, 8, _hold())
    expected_joint = rollout_branch((1, 1), horizon=8).discounted_return
    expected_hold = rollout_branch((0, 0), horizon=8).discounted_return
    assert session.branch_return(joint) == expected_joint
    assert session.branch_return(session.baseline) == expected_hold


def test_manifest_round_trips_and_marks_toy_evidence() -> None:
    session = _session()
    _run(session, session.baseline, 2, _hold())
    commit = session.fork(
        session.baseline, session.head(session.baseline), intervention={"agent_0": "commit"}, label="c"
    )
    _run(session, commit, 2, {"agent_0": "commit", "agent_1": "hold"})
    manifest = session.manifest()
    assert manifest.session.evidence_label == "toy"
    assert manifest.policy_ref == "toy_policy:hold"
    rebuilt = manifest_from_payload(manifest.to_payload())
    assert rebuilt.digest == manifest.digest
    assert len(rebuilt.branches) == 2


def test_snapshot_refs_carry_no_state_payload() -> None:
    session = _session()
    payload = session.head(session.baseline).to_payload()
    assert set(payload) == {
        "kind",
        "schema_version",
        "session_digest",
        "step",
        "state_digest",
        "event_cursor",
        "rng_digest",
    }
    with pytest.raises(ContractError):
        SnapshotRef(**{**{k: payload[k] for k in payload if k not in ("kind", "schema_version")}, "step": -1})
