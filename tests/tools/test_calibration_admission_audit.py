from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.diagnostics import calibration_admission_audit as audit


REPO_ROOT = Path(__file__).resolve().parents[2]
CURRENT_MANIFEST = (
    REPO_ROOT
    / "docs/task/air_combat/a2_high_fidelity_damage_model"
    / "archive"
    / "missile_lethality_calibration_gates"
    / "mlf10_calibration_evidence_manifest_20260619.json"
)


def _non_claims() -> list[str]:
    return list(audit.REQUIRED_NON_CLAIMS)


def _scope() -> dict[str, str]:
    return {
        "target_type": "F-16C_Block50",
        "weapon_family": "AIM-120C-class",
        "mechanism_family": "blast_fragmentation",
        "aspect_bucket": "beam",
        "closure_bucket": "high",
        "miss_distance_bucket": "near_miss_0_35m",
    }


def _base_record(evidence_id: str) -> dict[str, object]:
    return {
        "schema_version": audit.RECORD_SCHEMA_VERSION,
        "evidence_id": evidence_id,
        "evidence_class": "calibration_candidate",
        "source_kind": "validated_physics_surrogate",
        "source_ref": "repo://retained/example/manifest.json",
        "provenance": "independently reviewed component fragility benchmark package",
        "rights_status": "release_grade_admitted",
        "source_gate_status": "passed",
        "validation_status": "passed",
        "scope": _scope(),
        "population": {
            "identity": "independent benchmark population v1",
            "denominator_name": "validated_case_count",
            "sample_count": 64,
            "filters": "scope axes exactly match",
            "independence_assumption": "benchmark inputs are independent of fitted rows",
        },
        "uncertainty": {
            "method": "bootstrap_interval",
            "coverage": "95 percent interval over admitted cases",
            "residuals": [],
        },
        "independent_review": {
            "status": "passed",
            "reviewer_ref": "repo://retained/example/reviewer_signoff.json",
        },
        "authority_requests": {},
        "non_claims": _non_claims(),
        "residuals": [],
    }


def _manifest(*records: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": audit.MANIFEST_SCHEMA_VERSION,
        "manifest_id": "test_manifest",
        "non_claims": _non_claims(),
        "evidence_records": list(records),
    }


def test_admits_only_eligible_field_after_every_gate_passes() -> None:
    record = _base_record("ADMIT-001")
    record["authority_requests"] = {"effect_scale_authority": True}

    report = audit.audit_manifest(_manifest(record))
    decision = report["decisions"][0]

    assert report["schema_version"] == audit.REPORT_SCHEMA_VERSION
    assert report["decision_counts"]["admitted"] == 1
    assert decision["classification"] == "admitted"
    assert decision["authority_decisions"]["effect_scale_authority"]["decision"] == "admitted"
    assert report["admitted_authorities"] == [
        {
            "evidence_id": "ADMIT-001",
            "authority_field": "effect_scale_authority",
            "scope": _scope(),
        }
    ]
    assert report["authority_boundary"]["real_world_pk"] is False


def test_keeps_engineering_proxy_and_synthetic_report_non_authoritative() -> None:
    proxy = _base_record("PROXY-001")
    proxy.update(
        {
            "evidence_class": "engineering_proxy",
            "source_kind": "engineering_runtime_proxy",
            "rights_status": "repository_local",
            "source_gate_status": "not_applicable",
            "validation_status": "regression_passed",
        }
    )
    retained = _base_record("MLF9-001")
    retained.update(
        {
            "evidence_class": "retained_non_authoritative",
            "source_kind": "synthetic_simulation_report",
            "rights_status": "repository_local",
            "source_gate_status": "not_applicable",
            "validation_status": "simulation_trend_passed",
        }
    )

    report = audit.audit_manifest(_manifest(retained, proxy))

    assert [item["evidence_id"] for item in report["decisions"]] == [
        "MLF9-001",
        "PROXY-001",
    ]
    assert report["decision_counts"]["engineering_proxy"] == 1
    assert report["decision_counts"]["retained_non_authoritative"] == 1
    assert report["decision_counts"]["admitted"] == 0


def test_fails_closed_for_missing_rights_and_forbidden_authority() -> None:
    record = _base_record("BLOCK-001")
    record["rights_status"] = "candidate_only"
    record["authority_requests"] = {
        "effect_scale_authority": True,
        "pk_authority": True,
    }

    report = audit.audit_manifest(_manifest(record))
    decision = report["decisions"][0]

    assert decision["classification"] == "blocked"
    assert decision["gate_status"] == "fail_closed"
    assert "rights_not_release_grade_admitted" in decision["blocking_reasons"]
    assert "authority_forbidden_in_v1:pk_authority" in decision["blocking_reasons"]
    assert decision["authority_decisions"]["effect_scale_authority"]["decision"] == "blocked"
    assert decision["authority_decisions"]["pk_authority"]["decision"] == "blocked"
    assert report["admitted_authorities"] == []


def test_blocks_mixed_eligible_and_forbidden_authority_without_publishing_grant() -> None:
    record = _base_record("MIXED-001")
    record["authority_requests"] = {
        "effect_scale_authority": True,
        "pk_authority": True,
    }

    report = audit.audit_manifest(_manifest(record))
    decision = report["decisions"][0]

    assert decision["classification"] == "blocked"
    assert decision["gate_status"] == "fail_closed"
    assert decision["admitted_authority_fields"] == []
    assert report["admitted_authorities"] == []
    assert decision["authority_decisions"]["effect_scale_authority"]["decision"] == "blocked"
    assert (
        "authority_forbidden_in_v1:pk_authority"
        in decision["authority_decisions"]["effect_scale_authority"]["reasons"]
    )


def test_non_boolean_authority_request_fails_closed_without_truthy_admission() -> None:
    record = _base_record("BADBOOL-001")
    record["authority_requests"] = {"effect_scale_authority": "false"}

    report = audit.audit_manifest(_manifest(record))
    decision = report["decisions"][0]

    assert decision["classification"] == "blocked"
    assert decision["gate_status"] == "fail_closed"
    assert "authority_request_not_boolean:effect_scale_authority" in decision["blocking_reasons"]
    assert decision["authority_decisions"]["effect_scale_authority"]["requested"] is False
    assert decision["authority_decisions"]["effect_scale_authority"]["decision"] == "blocked"
    assert report["admitted_authorities"] == []


def test_missing_evidence_id_fails_closed_before_authority_grant() -> None:
    record = _base_record("")
    record["authority_requests"] = {"effect_scale_authority": True}

    report = audit.audit_manifest(_manifest(record))
    decision = report["decisions"][0]

    assert decision["evidence_id"] == "missing_evidence_id"
    assert decision["classification"] == "blocked"
    assert decision["gate_status"] == "fail_closed"
    assert "evidence_id_missing" in decision["blocking_reasons"]
    assert decision["authority_decisions"]["effect_scale_authority"]["decision"] == "blocked"
    assert report["admitted_authorities"] == []


def test_rejects_ineligible_source_without_trusting_input_admitted_label() -> None:
    record = _base_record("REJECT-001")
    record.update(
        {
            "evidence_class": "admitted",
            "source_kind": "leaked",
            "authority_requests": {"effect_scale_authority": True},
        }
    )

    decision = audit.audit_manifest(_manifest(record))["decisions"][0]

    assert decision["classification"] == "rejected"
    assert decision["authority_decisions"]["effect_scale_authority"]["decision"] == "rejected"


def test_manifest_missing_non_claim_fails_closed() -> None:
    record = _base_record("BLOCK-002")
    record["authority_requests"] = {"component_failure_probability_authority": True}
    manifest = _manifest(record)
    manifest["non_claims"] = [claim for claim in _non_claims() if claim != "real_world_pk"]

    report = audit.audit_manifest(manifest)

    assert "manifest_non_claim_missing:real_world_pk" in report["manifest_blocking_reasons"]
    assert report["decisions"][0]["classification"] == "blocked"
    assert report["decision_counts"]["admitted"] == 0


def test_cli_writes_retained_report(tmp_path: Path) -> None:
    record = _base_record("CLI-001")
    record.update(
        {
            "evidence_class": "blocked",
            "source_gate_status": "fail_closed",
            "authority_requests": {"effect_scale_authority": True},
            "residuals": ["independent source signoff missing"],
        }
    )
    manifest_path = tmp_path / "manifest.json"
    report_path = tmp_path / "report.json"
    manifest_path.write_text(json.dumps(_manifest(record)), encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            "tools/diagnostics/calibration_admission_audit.py",
            "--manifest_json",
            str(manifest_path),
            "--json_out",
            str(report_path),
            "--report_surface",
            "unit_test_retained_artifact",
        ],
        check=True,
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["report_surface"] == "unit_test_retained_artifact"
    assert report["decision_counts"]["blocked"] == 1
    assert report["decision_counts"]["admitted"] == 0


def test_current_repository_manifest_remains_fail_closed() -> None:
    manifest = json.loads(CURRENT_MANIFEST.read_text(encoding="utf-8"))

    report = audit.audit_manifest(
        manifest,
        manifest_ref=CURRENT_MANIFEST.relative_to(REPO_ROOT).as_posix(),
        report_surface="current_repository_regression",
    )

    assert report["record_count"] == 7
    assert report["decision_counts"] == {
        "engineering_proxy": 1,
        "retained_non_authoritative": 1,
        "calibration_candidate": 0,
        "admitted": 0,
        "rejected": 1,
        "blocked": 4,
    }
    assert report["admitted_authorities"] == []
    assert report["manifest_blocking_reasons"] == []
