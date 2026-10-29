from __future__ import annotations

import dataclasses

import pytest

from python.experiment.contracts import BranchRef
from python.experiment.contracts import ContractError
from python.experiment.contracts import SessionSpec
from python.experiment.contracts import SnapshotRef
from python.experiment.contracts import Transition
from python.experiment.trace import TRACE_SCHEMA_VERSION
from python.experiment.trace import BranchTrace
from python.experiment.trace import TraceManifest
from python.experiment.trace import manifest_from_payload

DIGEST = "a" * 64


def _session() -> SessionSpec:
    return SessionSpec(
        session_id="toy_session",
        backend="reference_toy",
        scenario_ref="toy:delayed_commitment",
        config_digest=DIGEST,
        seed=7,
        agent_ids=("agent_0",),
        evidence_label="toy",
    )


def _snapshot(session: SessionSpec, step: int, state: str) -> SnapshotRef:
    return SnapshotRef(
        session_digest=session.digest,
        step=step,
        state_digest=state * 64,
        event_cursor=step,
        rng_digest=DIGEST,
    )


def _branch_trace(session: SessionSpec, branch: BranchRef, states: str) -> BranchTrace:
    snapshots = [_snapshot(session, branch.origin_step + offset, state) for offset, state in enumerate(states)]
    # A child's first step applies its intervention, as every session enforces.
    first_actions = branch.intervention or (("agent_0", "hold"),)
    transitions = tuple(
        Transition(
            branch_digest=branch.digest,
            step=source.step,
            source_snapshot_digest=source.digest,
            target_snapshot_digest=target.digest,
            actions=first_actions if index == 0 else (("agent_0", "hold"),),
            rewards=(("agent_0", 1),),
            terminated=False,
            observation_provenance="facade_observation_packet",
        )
        for index, (source, target) in enumerate(zip(snapshots, snapshots[1:]))
    )
    return BranchTrace(branch=branch, transitions=transitions)


def _manifest() -> tuple[TraceManifest, SessionSpec]:
    session = _session()
    origin = _snapshot(session, 0, "0")
    root = BranchRef.root(origin)
    child = BranchRef.child(root, origin, intervention=(("agent_0", "commit"),), label="commit")
    manifest = TraceManifest(
        session=session,
        policy_ref="toy_policy:hold",
        branches=(_branch_trace(session, root, "0123"), _branch_trace(session, child, "0456")),
    )
    return manifest, session


def test_manifest_digest_is_stable_and_round_trips() -> None:
    manifest, _ = _manifest()
    again, _ = _manifest()
    assert manifest.digest == again.digest
    payload = manifest.to_payload()
    assert payload["schema_version"] == TRACE_SCHEMA_VERSION
    rebuilt = manifest_from_payload(payload)
    assert rebuilt == manifest
    assert rebuilt.digest == manifest.digest


def test_manifest_digest_is_independent_of_branch_order() -> None:
    manifest, _ = _manifest()
    reordered = dataclasses.replace(manifest, branches=tuple(reversed(manifest.branches)))
    assert reordered.digest == manifest.digest
    assert [trace.branch.digest for trace in reordered.branches] == [
        trace.branch.digest for trace in manifest.branches
    ]


def test_manifest_digest_changes_when_any_transition_changes() -> None:
    manifest, _ = _manifest()
    first = manifest.branches[0]
    changed_transition = dataclasses.replace(first.transitions[0], rewards=(("agent_0", 2),))
    changed = dataclasses.replace(
        manifest,
        branches=(
            dataclasses.replace(first, transitions=(changed_transition, *first.transitions[1:])),
            manifest.branches[1],
        ),
    )
    assert changed.digest != manifest.digest


def test_manifest_binds_policy_identity() -> None:
    manifest, _ = _manifest()
    assert manifest.to_payload()["policy_ref"] == "toy_policy:hold"
    assert dataclasses.replace(manifest, policy_ref="toy_policy:commit").digest != manifest.digest
    with pytest.raises(ContractError, match="policy_ref"):
        dataclasses.replace(manifest, policy_ref=" ")


def test_manifest_rejects_a_branch_from_another_session() -> None:
    manifest, _ = _manifest()
    other = dataclasses.replace(_session(), seed=8)
    stray_root = BranchRef.root(_snapshot(other, 0, "0"))
    with pytest.raises(ContractError, match="session"):
        dataclasses.replace(
            manifest, branches=(*manifest.branches, _branch_trace(other, stray_root, "09"))
        )


def test_manifest_rejects_orphan_children_and_duplicate_branches() -> None:
    manifest, _ = _manifest()
    root_trace, child_trace = manifest.branches
    with pytest.raises(ContractError, match="parent"):
        dataclasses.replace(manifest, branches=(child_trace,))
    with pytest.raises(ContractError, match="duplicate"):
        dataclasses.replace(manifest, branches=(root_trace, root_trace, child_trace))
    with pytest.raises(ContractError, match="root"):
        dataclasses.replace(manifest, branches=())


def _child_of(root_trace: BranchTrace, origin: SnapshotRef, **overrides) -> BranchRef:
    fields = dict(
        origin_snapshot_digest=origin.digest,
        origin_step=origin.step,
        session_digest=origin.session_digest,
        parent_digest=root_trace.branch.digest,
        depth=1,
        intervention=(("agent_0", "commit"),),
        label="commit",
    )
    fields.update(overrides)
    return BranchRef(**fields)


def test_manifest_accepts_a_child_forked_mid_trace() -> None:
    manifest, session = _manifest()
    root_trace = manifest.branches[0]
    mid = _snapshot(session, 2, "2")
    child = _child_of(root_trace, mid)
    rebuilt = dataclasses.replace(
        manifest, branches=(root_trace, _branch_trace(session, child, "29"))
    )
    assert len(rebuilt.branches) == 2


def test_manifest_rejects_a_child_whose_depth_skips_a_level() -> None:
    manifest, session = _manifest()
    root_trace = manifest.branches[0]
    child = _child_of(root_trace, _snapshot(session, 0, "0"), depth=7)
    with pytest.raises(ContractError, match="depth"):
        dataclasses.replace(manifest, branches=(root_trace, _branch_trace(session, child, "05")))


@pytest.mark.parametrize(
    ("step", "state"),
    [(0, "9"), (2, "9"), (9, "3")],
    ids=["unreached-state-at-origin-step", "unreached-state-mid-trace", "reached-state-wrong-step"],
)
def test_manifest_rejects_a_child_forked_from_an_unreached_state(step: int, state: str) -> None:
    manifest, session = _manifest()
    root_trace = manifest.branches[0]
    child = _child_of(root_trace, _snapshot(session, step, state))
    with pytest.raises(ContractError, match="parent recorded reaching"):
        dataclasses.replace(
            manifest, branches=(root_trace, _branch_trace(session, child, state + "8"))
        )


def test_manifest_rejects_a_child_whose_first_step_skips_its_intervention() -> None:
    manifest, session = _manifest()
    root_trace, child_trace = manifest.branches
    first = child_trace.transitions[0]
    skipped = dataclasses.replace(first, actions=(("agent_0", "hold"),))
    with pytest.raises(ContractError, match="intervention"):
        dataclasses.replace(
            manifest,
            branches=(
                root_trace,
                dataclasses.replace(child_trace, transitions=(skipped, *child_trace.transitions[1:])),
            ),
        )


def test_manifest_rejects_agents_outside_the_session() -> None:
    manifest, session = _manifest()
    root_trace, child_trace = manifest.branches
    outsider = _child_of(root_trace, _snapshot(session, 0, "0"), intervention=(("agent_9", "x"),))
    with pytest.raises(ContractError, match="agent_9"):
        dataclasses.replace(manifest, branches=(root_trace, BranchTrace(branch=outsider)))
    first = root_trace.transitions[0]
    foreign = dataclasses.replace(
        first, actions=(("agent_42", "hold"),), rewards=(("agent_42", 1),)
    )
    with pytest.raises(ContractError, match="agent_42"):
        dataclasses.replace(
            manifest,
            branches=(
                dataclasses.replace(root_trace, transitions=(foreign, *root_trace.transitions[1:])),
                child_trace,
            ),
        )


def test_manifest_decoder_applies_the_tree_rules() -> None:
    manifest, session = _manifest()
    payload = manifest.to_payload()
    child_payload = next(item for item in payload["branches"] if item["branch"]["depth"] == 1)
    child_payload["branch"]["depth"] = 4
    with pytest.raises(ContractError):
        manifest_from_payload(payload)


def test_branch_trace_rejects_broken_state_chains() -> None:
    manifest, session = _manifest()
    trace = manifest.branches[0]
    first, second, third = trace.transitions
    with pytest.raises(ContractError, match="chain"):
        dataclasses.replace(trace, transitions=(first, third))
    with pytest.raises(ContractError, match="origin"):
        dataclasses.replace(trace, transitions=(second, third))
    foreign = dataclasses.replace(first, branch_digest="c" * 64)
    with pytest.raises(ContractError, match="branch"):
        dataclasses.replace(trace, transitions=(foreign, second, third))
    terminal = dataclasses.replace(second, terminated=True)
    with pytest.raises(ContractError, match="terminated"):
        dataclasses.replace(trace, transitions=(first, terminal, third))


def test_manifest_decoder_fails_closed() -> None:
    manifest, _ = _manifest()
    payload = manifest.to_payload()
    with pytest.raises(ContractError, match="unknown"):
        manifest_from_payload({**payload, "extra": True})
    with pytest.raises(ContractError, match="schema_version"):
        manifest_from_payload({**payload, "schema_version": "echelon_forge.experiment_trace.v0"})
    tampered = dict(payload)
    tampered["branches"] = [dict(entry) for entry in payload["branches"]]
    tampered["branches"][0]["branch"] = {**tampered["branches"][0]["branch"], "label": "renamed"}
    with pytest.raises(ContractError, match="branch"):
        manifest_from_payload(tampered)
