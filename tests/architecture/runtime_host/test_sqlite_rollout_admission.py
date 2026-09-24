from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Mapping

import pytest

from tools.maintenance.runtime_authority_contracts import authority_digest_sha256
from tools.maintenance.runtime_authority_contracts import canonical_json_bytes as authority_json_bytes
from tools.maintenance.runtime_durable_artifact_ledger import LedgerContractError
from tools.maintenance.runtime_durable_artifact_ledger import SQLiteArtifactLedger
from tools.maintenance.runtime_durable_artifact_ledger import RECEIPT_MEDIA_TYPE
from python.rl.runtime.rollout_gate import build_rollout_decision_envelope

from tests.architecture.runtime_host import test_rollout_evidence_binding as evidence_fixtures


def _decision(*, state: str, sequence: int, decision_id: str, predecessor: str = "") -> dict[str, object]:
    return build_rollout_decision_envelope(
        evidence_fixtures._rollout_payload(
            state=state,
            sequence=sequence,
            decision_id=decision_id,
            predecessor=predecessor,
            manifest=evidence_fixtures._release_envelope()["payload_sha256"],
        ),
        key_id=evidence_fixtures.KEY_ID,
        signing_key=evidence_fixtures.KEY,
    )


def _release() -> dict[str, object]:
    return evidence_fixtures._release_envelope()


def _receipt_for(decision: Mapping[str, object], release: Mapping[str, object]) -> dict[str, object]:
    payload = decision["payload"]
    receipt = evidence_fixtures._receipt_envelope(
        decision_id=str(payload["decision_id"]),
        manifest_sha256=str(release["payload_sha256"]),
    )
    receipt_payload = receipt["payload"]
    receipt_payload["release_binding"]["rollout_decision_sha256"] = decision["payload_sha256"]
    receipt["payload_sha256"] = authority_digest_sha256(
        "runtime.run-receipt",
        RECEIPT_MEDIA_TYPE,
        authority_json_bytes(receipt_payload),
    )
    return receipt


def _open_ledger(tmp_path: Path) -> tuple[SQLiteArtifactLedger, object, dict[str, object]]:
    ledger = SQLiteArtifactLedger(tmp_path / "ledger")
    token = ledger.acquire_fence(
        "rollout:release-evidence-test",
        "release-controller",
        role="release_controller",
    )
    return ledger, token, _release()


def _advance_to_production(
    ledger: SQLiteArtifactLedger,
    token: object,
    release: Mapping[str, object],
) -> None:
    predecessor = ""
    for sequence, state in enumerate(("prepared", "shadow", "canary-ready", "production-canary")):
        decision_id = f"decision-evidence-{sequence}"
        decision = _decision(
            state=state,
            sequence=sequence,
            decision_id=decision_id,
            predecessor=predecessor,
        )
        ledger.commit_rollout_admission(
            token,
            decision,
            release_manifest=release,
            run_receipt=_receipt_for(decision, release),
            verification_key=evidence_fixtures.KEY,
            audit_identity="release-controller-test",
            expected_slot_version=sequence,
        )
        predecessor = decision_id


def _advance_to_stable(
    ledger: SQLiteArtifactLedger,
    token: object,
    release: Mapping[str, object],
) -> None:
    predecessor = ""
    states = (
        "prepared",
        "shadow",
        "canary-ready",
        "production-canary",
        "adoption-expanding",
        "rollback-window",
        "stable",
    )
    for sequence, state in enumerate(states):
        decision_id = f"decision-evidence-{sequence}"
        decision = _decision(
            state=state,
            sequence=sequence,
            decision_id=decision_id,
            predecessor=predecessor,
        )
        ledger.commit_rollout_admission(
            token,
            decision,
            release_manifest=release,
            run_receipt=_receipt_for(decision, release),
            verification_key=evidence_fixtures.KEY,
            audit_identity="release-controller-test",
            expected_slot_version=sequence,
        )
        predecessor = decision_id


def test_sqlite_rollout_admission_commits_and_reloads_atomically(tmp_path: Path) -> None:
    ledger, token, release = _open_ledger(tmp_path)
    try:
        prepared = _decision(state="prepared", sequence=0, decision_id="decision-evidence-0")
        version, evidence = ledger.commit_rollout_admission(
            token,
            prepared,
            release_manifest=release,
            run_receipt=_receipt_for(prepared, release),
            verification_key=evidence_fixtures.KEY,
            audit_identity="release-controller-test",
        )
        assert version == 1
        assert evidence["release_id"] == "release-evidence-test"
        assert evidence["package_digest"] == evidence_fixtures.PACKAGE
        admission = ledger.read_rollout_admission(
            "release-evidence-test",
            verification_key=evidence_fixtures.KEY,
        )
        assert admission["decision"]["payload"]["decision_id"] == "decision-evidence-0"
        assert admission["evidence"]["schema_version"] == "echelon_forge.rollout_evidence_binding.v1"
        assert admission["admissions_open"]
        assert ledger.stat_blob(
            admission["evidence"]["run_receipt_blob_sha256"],
            role="runtime_evidence",
        )[0] == RECEIPT_MEDIA_TYPE
    finally:
        ledger.close()

    restarted = SQLiteArtifactLedger(tmp_path / "ledger")
    try:
        admission = restarted.read_rollout_admission(
            "release-evidence-test",
            verification_key=evidence_fixtures.KEY,
        )
        assert admission["version"] == 1
        assert admission["decision"]["payload"]["state"] == "prepared"
    finally:
        restarted.close()


def test_sqlite_rollout_retention_survives_backup_and_restore(tmp_path: Path) -> None:
    ledger, token, release = _open_ledger(tmp_path)
    try:
        _advance_to_production(ledger, token, release)
        retention = ledger.read_rollout_retention(
            "release-evidence-test",
            verification_key=evidence_fixtures.KEY,
        )
        assert retention["state"] == "production-canary"
        assert {
            name: row["retention_class"]
            for name, row in retention["blobs"].items()
        } == {
            "release_manifest": "active-release",
            "rollout_decision": "rollback-window",
            "run_receipt": "run-retained",
            "rollout_evidence": "rollback-window",
        }
        backup = tmp_path / "ledger-backup.sqlite3"
        ledger.backup_to(backup)
    finally:
        ledger.close()

    restored = SQLiteArtifactLedger.restore_from(backup, tmp_path / "restored")
    try:
        restored_retention = restored.read_rollout_retention(
            "release-evidence-test",
            verification_key=evidence_fixtures.KEY,
        )
        assert restored_retention["blobs"] == retention["blobs"]
    finally:
        restored.close()


def test_sqlite_rollout_lifecycle_reaches_stable_with_rollback_retention(tmp_path: Path) -> None:
    ledger, token, release = _open_ledger(tmp_path)
    try:
        _advance_to_stable(ledger, token, release)
        admission = ledger.read_rollout_admission(
            "release-evidence-test",
            verification_key=evidence_fixtures.KEY,
        )
        assert admission["decision"]["payload"]["state"] == "stable"
        assert admission["admissions_open"]
        assert not admission["writer_advancement_frozen"]

        retention = ledger.read_rollout_retention(
            "release-evidence-test",
            verification_key=evidence_fixtures.KEY,
        )
        assert retention["state"] == "stable"
        assert retention["slot_version"] == 7
        assert {
            name: row["retention_class"]
            for name, row in retention["blobs"].items()
        } == {
            "release_manifest": "active-release",
            "rollout_decision": "rollback-window",
            "run_receipt": "run-retained",
            "rollout_evidence": "rollback-window",
        }
    finally:
        ledger.close()


def test_sqlite_rollout_admission_enforces_transition_cas_and_evidence_identity(tmp_path: Path) -> None:
    ledger, token, release = _open_ledger(tmp_path)
    try:
        prepared = _decision(state="prepared", sequence=0, decision_id="decision-evidence-0")
        ledger.commit_rollout_admission(
            token,
            prepared,
            release_manifest=release,
            run_receipt=_receipt_for(prepared, release),
            verification_key=evidence_fixtures.KEY,
            audit_identity="release-controller-test",
        )
        shadow = _decision(
            state="shadow",
            sequence=1,
            decision_id="decision-evidence-1",
            predecessor="decision-evidence-0",
        )
        with pytest.raises(LedgerContractError, match="compare-and-swap"):
            ledger.commit_rollout_admission(
                token,
                shadow,
                release_manifest=release,
                run_receipt=_receipt_for(shadow, release),
                verification_key=evidence_fixtures.KEY,
                audit_identity="release-controller-test",
                expected_slot_version=0,
            )
        ledger.commit_rollout_admission(
            token,
            shadow,
            release_manifest=release,
            run_receipt=_receipt_for(shadow, release),
            verification_key=evidence_fixtures.KEY,
            audit_identity="release-controller-test",
            expected_slot_version=1,
        )
        drifted = _receipt_for(shadow, release)
        drifted_payload = deepcopy(drifted["payload"])
        drifted_payload["release_binding"]["rollout_decision_id"] = "decision-other"
        drifted["payload"] = drifted_payload
        drifted["payload_sha256"] = authority_digest_sha256(
            "runtime.run-receipt",
            RECEIPT_MEDIA_TYPE,
            authority_json_bytes(drifted_payload),
        )
        canary = _decision(
            state="canary-ready",
            sequence=2,
            decision_id="decision-evidence-2",
            predecessor="decision-evidence-1",
        )
        with pytest.raises(LedgerContractError, match="evidence binding"):
            ledger.commit_rollout_admission(
                token,
                canary,
                release_manifest=release,
                run_receipt=drifted,
                verification_key=evidence_fixtures.KEY,
                audit_identity="release-controller-test",
                expected_slot_version=2,
            )
    finally:
        ledger.close()


def test_sqlite_rollout_admission_keeps_release_manifest_immutable(tmp_path: Path) -> None:
    ledger, token, release = _open_ledger(tmp_path)
    try:
        prepared = _decision(state="prepared", sequence=0, decision_id="decision-evidence-0")
        ledger.commit_rollout_admission(
            token,
            prepared,
            release_manifest=release,
            run_receipt=_receipt_for(prepared, release),
            verification_key=evidence_fixtures.KEY,
            audit_identity="release-controller-test",
        )
        altered_release = deepcopy(release)
        altered_release["signatures"] = [{
            "algorithm": "test-only",
            "key_id": "test-key",
            "signature": "test-signature",
            "signer_context": "test-context",
        }]
        shadow = _decision(
            state="shadow",
            sequence=1,
            decision_id="decision-evidence-1",
            predecessor="decision-evidence-0",
        )
        with pytest.raises(LedgerContractError, match="release manifest changed"):
            ledger.commit_rollout_admission(
                token,
                shadow,
                release_manifest=altered_release,
                run_receipt=_receipt_for(shadow, altered_release),
                verification_key=evidence_fixtures.KEY,
                audit_identity="release-controller-test",
                expected_slot_version=1,
            )
    finally:
        ledger.close()


def test_sqlite_rollout_kill_switch_closes_admission_and_allows_typed_backout(tmp_path: Path) -> None:
    ledger, token, release = _open_ledger(tmp_path)
    try:
        prepared = _decision(state="prepared", sequence=0, decision_id="decision-evidence-0")
        ledger.commit_rollout_admission(
            token,
            prepared,
            release_manifest=release,
            run_receipt=_receipt_for(prepared, release),
            verification_key=evidence_fixtures.KEY,
            audit_identity="release-controller-test",
        )
        killed = ledger.trip_rollout_kill_switch(
            token,
            ["wrong_epoch_result"],
            verification_key=evidence_fixtures.KEY,
            audit_identity="release-controller-test",
        )
        assert not killed["admissions_open"]
        assert killed["kill_switch_reasons"] == ("wrong_epoch_result",)
        shadow = _decision(state="shadow", sequence=1, decision_id="decision-evidence-1", predecessor="decision-evidence-0")
        with pytest.raises(LedgerContractError, match="closed rollout admission"):
            ledger.commit_rollout_admission(
                token,
                shadow,
                release_manifest=release,
                run_receipt=_receipt_for(shadow, release),
                verification_key=evidence_fixtures.KEY,
                audit_identity="release-controller-test",
                expected_slot_version=1,
            )
        backed_out = _decision(state="backed-out", sequence=1, decision_id="decision-evidence-backout", predecessor="decision-evidence-0")
        result = ledger.commit_rollout_admission(
            token,
            backed_out,
            release_manifest=release,
            run_receipt=_receipt_for(backed_out, release),
            verification_key=evidence_fixtures.KEY,
            audit_identity="release-controller-test",
            expected_slot_version=1,
            admissions_open=False,
            writer_advancement_frozen=True,
            kill_switch_reasons=("operator-backout",),
        )
        assert result[0] == 2
        assert ledger.read_rollout_admission(
            "release-evidence-test",
            verification_key=evidence_fixtures.KEY,
        )["decision"]["payload"]["state"] == "backed-out"
    finally:
        ledger.close()


def test_runtime_facade_adapter_can_read_sqlite_rollout_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from python.rl.runtime.world_batch import adapter as adapter_module

    ledger, token, release = _open_ledger(tmp_path)
    try:
        _advance_to_production(ledger, token, release)
        reader = lambda: ledger.read_rollout_snapshot(
            "release-evidence-test",
            verification_key=evidence_fixtures.KEY,
        )

        class _Facade:
            pass

        monkeypatch.setattr(adapter_module.ef_py, "RuntimeFacade", lambda _world_count: _Facade())
        adapter = adapter_module.RuntimeFacadeAdapter(
            1,
            production_rollout_key=evidence_fixtures.KEY,
            production_rollout_snapshot_reader=reader,
            require_production_admission=True,
            production_release_id="release-evidence-test",
            production_manifest_sha256=str(release["payload_sha256"]),
            production_plan_sha256=evidence_fixtures.PLAN,
            production_package_digest=evidence_fixtures.PACKAGE,
            production_wheel_digest=evidence_fixtures.WHEEL,
        )
        assert adapter.rollout_admission is not None
        assert adapter.rollout_admission.state == "production-canary"
        assert adapter.rollout_evidence_binding is not None

        ledger.trip_rollout_kill_switch(
            token,
            ["operator_backout"],
            verification_key=evidence_fixtures.KEY,
            audit_identity="release-controller-test",
        )
        with pytest.raises(RuntimeError, match="production rollout admission rejected"):
            adapter.refresh_rollout_admission()
    finally:
        ledger.close()
