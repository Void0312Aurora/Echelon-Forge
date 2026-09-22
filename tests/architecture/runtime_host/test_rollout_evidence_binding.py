from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.maintenance.runtime_authority_contracts import authority_digest_sha256
from tools.maintenance.runtime_authority_contracts import build_release_manifest_shell
from tools.maintenance.runtime_authority_contracts import canonical_json_bytes as authority_json_bytes

from python.rl.runtime.rollout_gate import FileRolloutDecisionStore
from python.rl.runtime.rollout_gate import build_rollout_decision_envelope
from python.rl.runtime.rollout_gate import canonical_json_bytes
from python.rl.runtime.rollout_evidence import RolloutEvidenceError
from python.rl.runtime.rollout_evidence import load_rollout_evidence
from python.rl.runtime.world_batch import adapter as adapter_module


KEY = b"p5d-evidence-test-key-0123456789abcdef"
KEY_ID = "p5d-evidence-key"
PLAN = "e" * 64
PACKAGE = "a" * 64
WHEEL = "b" * 64


def _rollout_payload(*, state: str, sequence: int, decision_id: str, predecessor: str, manifest: str) -> dict[str, str]:
    return {
        "authority_kind": "rollout_decision",
        "schema_version": "echelon_forge.rollout_decision.v1",
        "contract_version": "echelon_forge.rollout_decision_contract.v1",
        "writer_role": "release_controller",
        "decision_id": decision_id,
        "release_id": "release-evidence-test",
        "manifest_sha256": manifest,
        "plan_sha256": PLAN,
        "plan_reader_generation_min": "1",
        "plan_reader_generation_max": "2",
        "predecessor_decision_id": predecessor,
        "state": state,
        "writer_generation": "1",
        "decision_sequence": str(sequence),
        "cohort": "local-in-process",
        "rollback_deadline": "2026-12-31T00:00:00Z",
        "checkpoint_id": "",
        "irreversible_write_boundary": "none",
    }


def _release_envelope() -> dict[str, object]:
    return build_release_manifest_shell(
        {
            "authority_kind": "release_manifest",
            "schema_version": "echelon_forge.release_manifest.v1",
            "contract_version": "echelon_forge.release_manifest_contract.v1",
            "writer_role": "release_artifact_pipeline",
            "release_id": "release-evidence-test",
            "writer_generation": "1",
            "reader_generation_min": "1",
            "reader_generation_max": "2",
            "package_set": [{"name": "cmo", "sha256": PACKAGE}],
            "supported_rows": ["windows-cp312"],
            "provenance_sha256": "c" * 64,
            "sbom_sha256": "d" * 64,
            "toolchain_identity": "msvc-v143",
            "source_revision": "revision-test",
            "compatibility_generation": "1",
            "minimum_reader_generation": "1",
            "state_schema_generation": "1",
            "rollback_policy": "package-restart",
            "stored_artifact_inventory_sha256": "f" * 64,
            "rollback_deadline": "2026-12-31T00:00:00Z",
            "last_reader_deadline": "2026-12-31T00:00:00Z",
            "irreversible_write_boundary": "none",
        }
    )


def _receipt_envelope(*, decision_id: str, manifest_sha256: str) -> dict[str, object]:
    vector = json.loads(
        (
            Path("tests/architecture/composition/fixtures/run_receipt.v1.json")
            .read_text(encoding="utf-8")
        )
    )
    receipt = json.loads(vector["canonical_envelope_json"])
    payload = receipt["payload"]
    payload["release_binding"]["release_id"] = "release-evidence-test"
    payload["release_binding"]["release_manifest_sha256"] = manifest_sha256
    payload["release_binding"]["rollout_decision_id"] = decision_id
    payload["release_binding"]["rollout_decision_sha256"] = "0" * 64
    payload["plan_binding"]["plan_sha256"] = PLAN
    payload["package"]["digest"] = PACKAGE
    payload["package"]["wheel_digest"] = WHEEL
    receipt["payload_sha256"] = authority_digest_sha256(
        "runtime.run-receipt",
        "application/vnd.echelon-forge.run-receipt.v1+json",
        authority_json_bytes(payload),
    )
    return receipt


def _write_admitted_records(tmp_path: Path) -> tuple[Path, Path, FileRolloutDecisionStore]:
    release = _release_envelope()
    release_path = tmp_path / "release.json"
    release_path.write_bytes(canonical_json_bytes(release))
    prepared_payload = _rollout_payload(
        state="prepared",
        sequence=0,
        decision_id="decision-evidence-0",
        predecessor="",
        manifest=release["payload_sha256"],
    )
    store = FileRolloutDecisionStore(
        tmp_path / "rollout.json",
        writer_id="release-controller",
        signing_key=KEY,
        key_id=KEY_ID,
    )
    prepared = store.commit(
        build_rollout_decision_envelope(prepared_payload, key_id=KEY_ID, signing_key=KEY)
    )
    shadow_payload = _rollout_payload(
        state="shadow",
        sequence=1,
        decision_id="decision-evidence-1",
        predecessor=prepared_payload["decision_id"],
        manifest=release["payload_sha256"],
    )
    shadow = store.commit(
        build_rollout_decision_envelope(shadow_payload, key_id=KEY_ID, signing_key=KEY),
        expected_decision_sha256=prepared.decision_sha256,
    )
    ready_payload = _rollout_payload(
        state="canary-ready",
        sequence=2,
        decision_id="decision-evidence-2",
        predecessor=shadow_payload["decision_id"],
        manifest=release["payload_sha256"],
    )
    ready = store.commit(
        build_rollout_decision_envelope(ready_payload, key_id=KEY_ID, signing_key=KEY),
        expected_decision_sha256=shadow.decision_sha256,
    )
    canary_payload = _rollout_payload(
        state="production-canary",
        sequence=3,
        decision_id="decision-evidence-3",
        predecessor=ready_payload["decision_id"],
        manifest=release["payload_sha256"],
    )
    canary = store.commit(
        build_rollout_decision_envelope(canary_payload, key_id=KEY_ID, signing_key=KEY),
        expected_decision_sha256=ready.decision_sha256,
    )
    receipt = _receipt_envelope(
        decision_id=canary_payload["decision_id"],
        manifest_sha256=release["payload_sha256"],
    )
    receipt["payload"]["release_binding"]["rollout_decision_sha256"] = canary.envelope["payload_sha256"]
    receipt["payload_sha256"] = authority_digest_sha256(
        "runtime.run-receipt",
        "application/vnd.echelon-forge.run-receipt.v1+json",
        authority_json_bytes(receipt["payload"]),
    )
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_bytes(canonical_json_bytes(receipt))
    return release_path, receipt_path, store


def test_rollout_evidence_projection_binds_release_receipt_and_package(tmp_path: Path) -> None:
    release_path, receipt_path, store = _write_admitted_records(tmp_path)
    binding = load_rollout_evidence(release_path, receipt_path)
    admission = store.read()
    assert admission is not None
    assert binding.release_id == admission.envelope["payload"]["release_id"]
    assert binding.manifest_sha256 == admission.envelope["payload"]["manifest_sha256"]
    assert binding.plan_sha256 == PLAN
    assert binding.package_digest == PACKAGE
    assert binding.wheel_digest == WHEEL


def test_rollout_evidence_projection_rejects_receipt_decision_drift(tmp_path: Path) -> None:
    release_path, receipt_path, store = _write_admitted_records(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["payload"]["release_binding"]["rollout_decision_id"] = "decision-other"
    receipt["payload_sha256"] = authority_digest_sha256(
        "runtime.run-receipt",
        "application/vnd.echelon-forge.run-receipt.v1+json",
        authority_json_bytes(receipt["payload"]),
    )
    receipt_path.write_bytes(canonical_json_bytes(receipt))
    with pytest.raises(RolloutEvidenceError, match="release/plan/decision"):
        admission = store.read()
        assert admission is not None
        binding = load_rollout_evidence(release_path, receipt_path)
        from python.rl.runtime.rollout_evidence import assert_rollout_evidence_binding

        assert_rollout_evidence_binding(admission, binding)


def test_adapter_can_require_release_and_receipt_binding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    release_path, receipt_path, store = _write_admitted_records(tmp_path)
    admission = store.read()
    assert admission is not None

    class _Facade:
        pass

    monkeypatch.setattr(adapter_module.ef_py, "RuntimeFacade", lambda _world_count: _Facade())
    adapter = adapter_module.RuntimeFacadeAdapter(
        1,
        production_rollout_path=str(store.path),
        production_rollout_key=KEY,
        require_production_admission=True,
        production_release_id="release-evidence-test",
        production_manifest_sha256=admission.envelope["payload"]["manifest_sha256"],
        production_plan_sha256=PLAN,
        production_release_manifest_path=str(release_path),
        production_run_receipt_path=str(receipt_path),
        production_package_digest=PACKAGE,
        production_wheel_digest=WHEEL,
        require_production_evidence_binding=True,
    )
    assert adapter.rollout_evidence_binding is not None
