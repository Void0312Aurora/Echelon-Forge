from __future__ import annotations

import dataclasses

import pytest

from python.experiment.contracts import BranchRef
from python.experiment.contracts import ContractError
from python.experiment.contracts import SessionSpec
from python.experiment.contracts import SnapshotRef
from python.experiment.contracts import Transition
from python.experiment.trace import BranchTrace
from python.experiment.trace import TraceManifest
from python.experiment.trace_projection import SeedSplit
from python.experiment.trace_projection import project_manifests
from python.experiment.trace_projection import projection_from_payload


DIGEST = "a" * 64


def _manifest(seed: int, *, policy_ref: str = "policy:fixed", evidence: str = "runtime_candidate"):
    session = SessionSpec(
        session_id=f"runtime_session_{seed}",
        backend="runtime_candidate",
        scenario_ref="scenario:fixed",
        config_digest=DIGEST,
        seed=seed,
        agent_ids=("pilot",),
        evidence_label=evidence,
    )

    def snapshot(step: int, marker: str) -> SnapshotRef:
        return SnapshotRef(
            session_digest=session.digest,
            step=step,
            state_digest=marker * 64,
            event_cursor=step,
            rng_digest=DIGEST,
        )

    root_origin = snapshot(0, "b")
    root_mid = snapshot(1, "c")
    root_end = snapshot(2, "d")
    root = BranchRef.root(root_origin)
    root_trace = BranchTrace(
        root,
        (
            Transition(
                branch_digest=root.digest,
                step=0,
                source_snapshot_digest=root_origin.digest,
                target_snapshot_digest=root_mid.digest,
                actions=(("pilot", "idle"),),
                rewards=(("pilot", -10),),
                terminated=False,
                observation_provenance="fixed_protocol_no_policy_observation",
            ),
            Transition(
                branch_digest=root.digest,
                step=1,
                source_snapshot_digest=root_mid.digest,
                target_snapshot_digest=root_end.digest,
                actions=(("pilot", "idle"),),
                rewards=(("pilot", -11),),
                terminated=False,
                observation_provenance="fixed_protocol_no_policy_observation",
            ),
        ),
    )
    child = BranchRef.child(
        root,
        root_mid,
        intervention=(("pilot", "full"),),
        label="full",
    )
    child_end = snapshot(2, "e")
    child_trace = BranchTrace(
        child,
        (
            Transition(
                branch_digest=child.digest,
                step=1,
                source_snapshot_digest=root_mid.digest,
                target_snapshot_digest=child_end.digest,
                actions=(("pilot", "full"),),
                rewards=(("pilot", -3),),
                terminated=False,
                observation_provenance="fixed_protocol_no_policy_observation",
            ),
        ),
    )
    return TraceManifest(session, policy_ref, (child_trace, root_trace))


def test_projection_preserves_branch_lineage_and_assigns_one_split_per_session() -> None:
    projection = project_manifests(
        (_manifest(11), _manifest(17)),
        SeedSplit(training=(11,), evaluation=(17,)),
        consumer="evaluation",
    )
    assert len(projection.rows) == 6
    assert {row.split for row in projection.rows if row.seed == 11} == {"training"}
    assert {row.split for row in projection.rows if row.seed == 17} == {"evaluation"}
    assert all(row.evidence_label == "runtime_candidate" for row in projection.rows)
    assert all(
        row.observation_provenance == "fixed_protocol_no_policy_observation"
        for row in projection.rows
    )
    child_rows = [row for row in projection.rows if row.branch_label == "full"]
    assert child_rows and all(row.parent_branch_digest is not None for row in child_rows)
    assert all("observation" not in row.to_payload() for row in projection.rows)


def test_projection_is_canonical_and_round_trips_with_digest_verification() -> None:
    split = SeedSplit(training=(11,), evaluation=(17,))
    first = project_manifests((_manifest(17), _manifest(11)), split, consumer="ppo")
    second = project_manifests((_manifest(11), _manifest(17)), split, consumer="ppo")
    assert first.digest == second.digest
    payload = first.to_payload()
    assert projection_from_payload(payload) == first
    assert projection_from_payload(payload).to_payload() == payload
    payload["rows"][0]["rewards"][0][1] -= 1
    with pytest.raises(ContractError, match="digest"):
        projection_from_payload(payload)


@pytest.mark.parametrize("consumer", ["bc", "evaluation", "ppo", "world_model"])
def test_all_declared_consumers_share_the_same_projection_contract(consumer: str) -> None:
    projection = project_manifests(
        (_manifest(11),), SeedSplit(training=(11,), evaluation=(17,)), consumer=consumer
    )
    assert projection.consumer == consumer
    assert len(projection.compatibility_records()) == 3


def test_projection_rejects_leakage_and_mixed_authority() -> None:
    with pytest.raises(ContractError, match="disjoint"):
        SeedSplit(training=(11,), evaluation=(11,))
    with pytest.raises(ContractError, match="absent"):
        project_manifests(
            (_manifest(12),), SeedSplit(training=(11,), evaluation=(17,)), consumer="bc"
        )
    with pytest.raises(ContractError, match="multiple manifests"):
        project_manifests(
            (_manifest(11), dataclasses.replace(_manifest(11), policy_ref="policy:other")),
            SeedSplit(training=(11,), evaluation=(17,)),
            consumer="bc",
        )
    with pytest.raises(ContractError, match="policy"):
        project_manifests(
            (_manifest(11), _manifest(17, policy_ref="policy:other")),
            SeedSplit(training=(11,), evaluation=(17,)),
            consumer="bc",
        )
    with pytest.raises(ContractError, match="evidence"):
        project_manifests(
            (_manifest(11), _manifest(17, evidence="toy")),
            SeedSplit(training=(11,), evaluation=(17,)),
            consumer="bc",
        )


def test_projection_decoder_fails_closed_on_unknown_schema_fields() -> None:
    projection = project_manifests(
        (_manifest(11),), SeedSplit(training=(11,), evaluation=(17,)), consumer="world_model"
    )
    payload = projection.to_payload()
    payload["unknown"] = True
    with pytest.raises(ContractError, match="keys differ"):
        projection_from_payload(payload)
    payload = projection.to_payload()
    payload["schema_version"] = "echelon_forge.experiment_trace_projection.v0"
    with pytest.raises(ContractError, match="schema"):
        projection_from_payload(payload)
