from __future__ import annotations

import copy

import pytest

from tools.maintenance import p5d_rebuild_retirement_gate as retirement_gate
from tools.maintenance import runtime_rebuild_unreachability as rebuild_inventory

from tests.architecture.runtime_host.test_sqlite_rollout_admission import (
    _advance_to_stable,
    _open_ledger,
)
from tests.architecture.runtime_host import test_rollout_evidence_binding as evidence_fixtures


def _stable_admission() -> dict[str, object]:
    return {
        "version": 7,
        "admissions_open": True,
        "writer_advancement_frozen": False,
        "decision": {
            "payload": {
                "release_id": "release-evidence-test",
                "decision_id": "decision-evidence-6",
                "state": "stable",
            },
            "payload_sha256": "a" * 64,
        },
        "evidence": {
            "admissions_open": True,
            "writer_advancement_frozen": False,
        },
    }


def _stable_retention() -> dict[str, object]:
    return {
        "release_id": "release-evidence-test",
        "state": "stable",
        "slot_version": 7,
        "evidence_version": 7,
        "blobs": {
            "release_manifest": {"digest": "b" * 64, "retention_class": "active-release"},
            "rollout_decision": {"digest": "c" * 64, "retention_class": "rollback-window"},
            "run_receipt": {"digest": "d" * 64, "retention_class": "run-retained"},
            "rollout_evidence": {"digest": "e" * 64, "retention_class": "rollback-window"},
        },
    }


def _attestation(inventory: dict[str, object]) -> dict[str, object]:
    return {
        "attestation_id": "cutover-attestation-1",
        "release_id": "release-evidence-test",
        "decision_id": "decision-evidence-6",
        "decision_payload_sha256": "a" * 64,
        "inventory_sha256": inventory["inventory_sha256"],
        "production_caller_cutover": True,
        "rollback_window_verified": True,
        "adoption_evidence_sha256": "f" * 64,
        "rollback_window_evidence_sha256": "1" * 64,
    }


def test_retirement_gate_requires_stable_admission_and_explicit_attestation() -> None:
    inventory = rebuild_inventory.load_fixture()
    admission = _stable_admission()
    retention = _stable_retention()

    with pytest.raises(retirement_gate.RetirementGateError, match="attestation"):
        retirement_gate.build_retirement_proof(
            admission=admission,
            retention=retention,
            inventory=inventory,
            cutover_attestation=None,
        )

def test_retirement_gate_rejects_pre_stable_rollout() -> None:
    inventory = rebuild_inventory.load_fixture()
    admission = _stable_admission()
    admission["decision"] = {
        **admission["decision"],
        "payload": {**admission["decision"]["payload"], "state": "production-canary"},
    }
    attestation = _attestation(inventory)

    with pytest.raises(retirement_gate.RetirementGateError, match="stable"):
        retirement_gate.build_retirement_proof(
            admission=admission,
            retention=_stable_retention(),
            inventory=inventory,
            cutover_attestation=attestation,
        )


def test_retirement_gate_returns_production_authority_only_proof() -> None:
    inventory = rebuild_inventory.load_fixture()
    proof = retirement_gate.build_retirement_proof(
        admission=_stable_admission(),
        retention=_stable_retention(),
        inventory=inventory,
        cutover_attestation=_attestation(inventory),
    )

    assert proof["retired"] is True
    assert proof["retirement_scope"] == "production_rebuild_authority_only"
    assert proof["native_test_capability_retained"] is True
    assert proof["reachability_state"] == "retired_after_rollback_window"
    assert proof["inventory_sha256"] == inventory["inventory_sha256"]


def test_retirement_gate_rejects_inventory_drift() -> None:
    inventory = copy.deepcopy(rebuild_inventory.load_fixture())
    inventory["production_callable_references"] = {"src/main.cpp": [1]}

    with pytest.raises(retirement_gate.RetirementGateError, match="inventory"):
        retirement_gate.build_retirement_proof(
            admission=_stable_admission(),
            retention=_stable_retention(),
            inventory=inventory,
            cutover_attestation=_attestation(inventory),
        )


def test_retirement_gate_accepts_durable_stable_ledger_projection(tmp_path) -> None:
    ledger, token, release = _open_ledger(tmp_path)
    try:
        _advance_to_stable(ledger, token, release)
        admission = ledger.read_rollout_admission(
            "release-evidence-test",
            verification_key=evidence_fixtures.KEY,
        )
        retention = ledger.read_rollout_retention(
            "release-evidence-test",
            verification_key=evidence_fixtures.KEY,
        )
        inventory = rebuild_inventory.load_fixture()
        decision = admission["decision"]
        payload = decision["payload"]
        attestation = {
            "attestation_id": "cutover-attestation-durable-ledger-1",
            "release_id": payload["release_id"],
            "decision_id": payload["decision_id"],
            "decision_payload_sha256": decision["payload_sha256"],
            "inventory_sha256": inventory["inventory_sha256"],
            "production_caller_cutover": True,
            "rollback_window_verified": True,
            "adoption_evidence_sha256": "f" * 64,
            "rollback_window_evidence_sha256": "1" * 64,
        }

        proof = retirement_gate.build_retirement_proof(
            admission=admission,
            retention=retention,
            inventory=inventory,
            cutover_attestation=attestation,
        )

        assert proof["retired"] is True
        assert proof["slot_version"] == admission["version"] == 7
        assert proof["decision_id"] == payload["decision_id"]
        assert proof["retirement_scope"] == "production_rebuild_authority_only"
    finally:
        ledger.close()
