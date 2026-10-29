from __future__ import annotations

import dataclasses
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

from python.experiment.contracts import CONTRACT_SCHEMA_VERSION
from python.experiment.contracts import EVIDENCE_LABELS
from python.experiment.contracts import POLICY_INPUT_PROVENANCE_LABELS
from python.experiment.contracts import BranchRef
from python.experiment.contracts import ContractError
from python.experiment.contracts import DecisionWindow
from python.experiment.contracts import SessionSpec
from python.experiment.contracts import SnapshotRef
from python.experiment.contracts import Transition
from python.experiment.contracts import canonical_bytes
from python.experiment.contracts import content_digest
from python.experiment.contracts import from_payload

REPO_ROOT = Path(__file__).resolve().parents[2]
DIGEST = "a" * 64
OTHER_DIGEST = "b" * 64


def _session(**overrides: object) -> SessionSpec:
    fields = {
        "session_id": "toy_session",
        "backend": "reference_toy",
        "scenario_ref": "toy:delayed_commitment",
        "config_digest": DIGEST,
        "seed": 7,
        "agent_ids": ("agent_0", "agent_1"),
        "evidence_label": "toy",
    }
    fields.update(overrides)
    return SessionSpec(**fields)


def _snapshot(**overrides: object) -> SnapshotRef:
    fields = {
        "session_digest": DIGEST,
        "step": 3,
        "state_digest": OTHER_DIGEST,
        "event_cursor": 0,
        "rng_digest": DIGEST,
    }
    fields.update(overrides)
    return SnapshotRef(**fields)


def test_contract_import_has_no_runtime_bootstrap_side_effects() -> None:
    probe = (
        "import sys\n"
        "import python.experiment.contracts\n"
        "roots = {name.split('.')[0] for name in sys.modules}\n"
        "assert not roots & {'ef_py', 'gymnasium', 'stable_baselines3', 'torch', 'numpy'}\n"
        "assert 'python.rl' not in sys.modules\n"
        "assert 'tools' not in roots\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_canonical_bytes_match_the_authority_canonical_json_profile() -> None:
    from tools.maintenance.runtime_authority_contracts import canonical_json_bytes

    for value in (
        _session().to_payload(),
        _snapshot().to_payload(),
        {"z": [3, {"é": None, "a": True}], "中": "x", "A": -9007199254740991},
        # Code-point and UTF-16 order disagree for this pair.
        {"\uffff": 1, "\U00010000": 2, "\ue000": [{"\U0001f600": 0, "\uffef": None}]},
    ):
        assert canonical_bytes(value) == canonical_json_bytes(value)


@pytest.mark.parametrize(
    "value",
    [
        {"x": 1.5},
        {"x": float("nan")},
        {"x": 2**53},
        {"x": -(2**53)},
        {1: "non-string key"},
        {"x": object()},
        {"x": "\ud800"},
    ],
)
def test_canonical_bytes_reject_values_outside_the_float_free_profile(value: object) -> None:
    with pytest.raises(ContractError):
        canonical_bytes(value)


def test_content_digest_is_domain_separated() -> None:
    payload = {"a": 1}
    assert content_digest("experiment.snapshot-ref", payload) != content_digest(
        "experiment.branch-ref", payload
    )
    assert content_digest("experiment.snapshot-ref", payload) == content_digest(
        "experiment.snapshot-ref", {"a": 1}
    )


def test_every_contract_round_trips_through_its_payload() -> None:
    snapshot = _snapshot()
    branch = BranchRef.root(snapshot)
    child = BranchRef.child(branch, snapshot, intervention=(("agent_0", "commit"),), label="commit")
    window = DecisionWindow(
        session_digest=DIGEST,
        start_step=3,
        horizon=4,
        agent_ids=("agent_0",),
        reason="uniform_probe",
    )
    transition = Transition(
        branch_digest=child.digest,
        step=3,
        source_snapshot_digest=snapshot.digest,
        target_snapshot_digest=_snapshot(step=4).digest,
        actions=(("agent_0", "commit"), ("agent_1", "hold")),
        rewards=(("agent_0", -1), ("agent_1", 0)),
        terminated=False,
        observation_provenance="facade_observation_packet",
    )
    for contract in (_session(), snapshot, branch, child, window, transition):
        payload = contract.to_payload()
        assert payload["schema_version"] == CONTRACT_SCHEMA_VERSION
        rebuilt = from_payload(payload)
        assert rebuilt == contract
        assert rebuilt.digest == contract.digest


def test_from_payload_rejects_unknown_missing_and_mistyped_fields() -> None:
    payload = _snapshot().to_payload()
    with pytest.raises(ContractError, match="unknown"):
        from_payload({**payload, "extra": 1})
    without_step = dict(payload)
    del without_step["step"]
    with pytest.raises(ContractError, match="missing"):
        from_payload(without_step)
    with pytest.raises(ContractError):
        from_payload({**payload, "step": "3"})
    with pytest.raises(ContractError, match="schema_version"):
        from_payload({**payload, "schema_version": "echelon_forge.experiment.v0"})
    with pytest.raises(ContractError, match="kind"):
        from_payload({**payload, "kind": "not_a_contract"})
    # Hostile, non-hashable or non-dict input must fail as a contract error.
    with pytest.raises(ContractError, match="kind"):
        from_payload({**payload, "kind": ["snapshot-ref"]})
    with pytest.raises(ContractError, match="plain dicts"):
        canonical_bytes({"x": MappingProxyType({"y": 1})})


def test_unencodable_text_fails_at_construction() -> None:
    with pytest.raises(ContractError, match="surrogate"):
        dataclasses.replace(_session(), scenario_ref="x" + chr(0xD800))


@pytest.mark.parametrize(
    "overrides",
    [
        {"session_id": "Bad Id"},
        {"backend": ""},
        {"config_digest": "ABC"},
        {"seed": -1},
        {"seed": True},
        {"agent_ids": ()},
        {"agent_ids": ("agent_1", "agent_0")},
        {"agent_ids": ("agent_0", "agent_0")},
        {"evidence_label": "maintained"},
    ],
)
def test_session_spec_fails_closed(overrides: dict[str, object]) -> None:
    with pytest.raises(ContractError):
        _session(**overrides)


def test_session_spec_evidence_labels_never_claim_runtime_authority() -> None:
    assert EVIDENCE_LABELS == ("synthetic", "toy", "runtime_candidate")


@pytest.mark.parametrize(
    "overrides",
    [
        {"step": -1},
        {"state_digest": "g" * 64},
        {"event_cursor": -1},
        {"session_digest": ""},
    ],
)
def test_snapshot_ref_fails_closed(overrides: dict[str, object]) -> None:
    with pytest.raises(ContractError):
        _snapshot(**overrides)


def test_snapshot_identity_covers_every_state_component() -> None:
    base = _snapshot()
    for field in ("step", "state_digest", "event_cursor", "rng_digest", "session_digest"):
        value = getattr(base, field)
        changed = value + 1 if isinstance(value, int) else ("c" * 64)
        assert dataclasses.replace(base, **{field: changed}).digest != base.digest


def test_branch_ancestry_is_part_of_identity() -> None:
    snapshot = _snapshot()
    root = BranchRef.root(snapshot)
    assert root.parent_digest is None and root.depth == 0 and root.intervention == ()
    commit = BranchRef.child(root, snapshot, intervention=(("agent_0", "commit"),), label="commit")
    hold = BranchRef.child(root, snapshot, intervention=(("agent_0", "hold"),), label="hold")
    assert commit.parent_digest == root.digest and commit.depth == 1
    assert commit.digest != hold.digest
    nested = BranchRef.child(commit, snapshot, intervention=(("agent_1", "commit"),), label="joint")
    assert nested.depth == 2 and nested.parent_digest == commit.digest


@pytest.mark.parametrize(
    "intervention",
    [
        (("agent_1", "commit"), ("agent_0", "hold")),
        (("agent_0", "commit"), ("agent_0", "hold")),
        (("agent_0", ""),),
    ],
)
def test_branch_intervention_must_be_sorted_unique_and_named(
    intervention: tuple[tuple[str, str], ...],
) -> None:
    root = BranchRef.root(_snapshot())
    with pytest.raises(ContractError):
        BranchRef.child(root, _snapshot(), intervention=intervention, label="bad")


def test_root_branch_cannot_carry_parent_or_intervention() -> None:
    root = BranchRef.root(_snapshot())
    with pytest.raises(ContractError):
        dataclasses.replace(root, parent_digest=DIGEST)
    with pytest.raises(ContractError):
        dataclasses.replace(root, intervention=(("agent_0", "commit"),))
    with pytest.raises(ContractError):
        dataclasses.replace(root, depth=1)


def test_child_branch_requires_parent_and_intervention() -> None:
    root = BranchRef.root(_snapshot())
    child = BranchRef.child(root, _snapshot(), intervention=(("agent_0", "commit"),), label="c")
    with pytest.raises(ContractError):
        dataclasses.replace(child, parent_digest=None)
    with pytest.raises(ContractError):
        dataclasses.replace(child, intervention=())


def test_child_branch_must_start_from_a_snapshot_at_or_after_its_parent() -> None:
    root = BranchRef.root(_snapshot(step=5))
    with pytest.raises(ContractError, match="before"):
        BranchRef.child(root, _snapshot(step=4), intervention=(("agent_0", "commit"),), label="c")
    with pytest.raises(ContractError, match="session"):
        BranchRef.child(
            root,
            _snapshot(step=6, session_digest=OTHER_DIGEST),
            intervention=(("agent_0", "commit"),),
            label="c",
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"horizon": 0},
        {"start_step": -1},
        {"agent_ids": ()},
        {"reason": "Not An Identifier"},
    ],
)
def test_decision_window_fails_closed(overrides: dict[str, object]) -> None:
    fields = {
        "session_digest": DIGEST,
        "start_step": 0,
        "horizon": 1,
        "agent_ids": ("agent_0",),
        "reason": "uniform_probe",
    }
    fields.update(overrides)
    with pytest.raises(ContractError):
        DecisionWindow(**fields)


def test_transition_admits_maintained_inputs_or_explicitly_no_policy_observation() -> None:
    assert POLICY_INPUT_PROVENANCE_LABELS == (
        "facade_observation_packet",
        "decision_belief_packet",
        "fixed_protocol_no_policy_observation",
    )
    fields = {
        "branch_digest": DIGEST,
        "step": 0,
        "source_snapshot_digest": DIGEST,
        "target_snapshot_digest": OTHER_DIGEST,
        "actions": (("agent_0", "hold"),),
        "rewards": (("agent_0", 1),),
        "terminated": False,
        "observation_provenance": "decision_belief_packet",
    }
    Transition(**fields)
    Transition(**{**fields, "observation_provenance": "fixed_protocol_no_policy_observation"})
    for label in ("raw_world_truth", "diagnostics_oracle", "agent_observation_adapter_projection"):
        with pytest.raises(ContractError, match="provenance"):
            Transition(**{**fields, "observation_provenance": label})


@pytest.mark.parametrize(
    "overrides",
    [
        {"source_snapshot_digest": OTHER_DIGEST},
        {"actions": ()},
        {"actions": (("agent_1", "hold"), ("agent_0", "hold"))},
        {"rewards": (("agent_1", 1),)},
        {"rewards": (("agent_0", 1.5),)},
        {"terminated": 0},
        {"step": -1},
    ],
)
def test_transition_fails_closed(overrides: dict[str, object]) -> None:
    fields = {
        "branch_digest": DIGEST,
        "step": 0,
        "source_snapshot_digest": DIGEST,
        "target_snapshot_digest": OTHER_DIGEST,
        "actions": (("agent_0", "hold"),),
        "rewards": (("agent_0", 1),),
        "terminated": False,
        "observation_provenance": "facade_observation_packet",
    }
    fields.update(overrides)
    if overrides.get("source_snapshot_digest") == OTHER_DIGEST:
        fields["target_snapshot_digest"] = OTHER_DIGEST
    with pytest.raises(ContractError):
        Transition(**fields)
