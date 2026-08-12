from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.diagnostics import cuda_resident_retained_evidence_paths as retained_paths


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "tests/fixtures/runtime_profiles/cuda_resident_program_2"
RECORD = FIXTURE / "cuda_resident_cp9_promotion_decision_20260813.json"
DOC = FIXTURE / "cuda_resident_cp9_promotion_decision_20260813.md"
DOC_ZH = FIXTURE / "cuda_resident_cp9_promotion_decision_20260813.zh.md"
FACADE_CONFIG = ROOT / "src/runtime/facade/runtime_facade_config.cpp"
README = FIXTURE / "README.md"
README_ZH = FIXTURE / "README.zh.md"


def _record() -> dict:
    value = json.loads(RECORD.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_cp9_record_identity_and_owner_decision_are_frozen() -> None:
    record = _record()
    assert record["schema_version"] == "cuda_resident.cp9_promotion_decision.v1"
    assert record["decision_id"] == "cp9.scoped_promotion.cuda_resident.20260813"
    assert record["status"] == "scoped_promotion_recorded"
    assert record["authority"] == "cuda_resident_promotion_program_20260808"
    assert record["owner_decision"]["decided_by"] == "repository_owner"
    assert record["owner_decision"]["option_chosen"] == "scoped_promote"
    assert set(record["owner_decision"]["alternatives_declined"]) == {
        "unrestricted_promote",
        "hold",
    }


def test_cp9_all_six_gates_are_green_with_an_uncompromised_review() -> None:
    record = _record()
    gates = record["gate_evaluation"]
    assert set(gates) == {
        "G_A_full_window_spi_measured",
        "G_B_cpu_cuda_invocation_equivalent",
        "G_C_learner_equivalent_consumption_measured",
        "G_D_achieved_counters_complete",
        "G_E_selected_slice_parity",
        "G_F_small_batch_disposition",
    }
    for gate in gates.values():
        assert gate["verdict"] == "green"
    review = record["independent_review"]
    assert review["performed"] is True
    assert review["edited_implementation_under_review"] is False
    assert review["blocking_findings"] == 0
    assert review["recommendation"] == "scoped_promote"
    assert review["verification"]["authorization_flags_verified_false_everywhere"] is True


def test_cp9_scope_keeps_cpu_default_and_performance_experimental() -> None:
    record = _record()
    scope = record["promotion_scope"]
    assert scope["promoted_to"] == "selectable_maintained_backend_explicit_opt_in"
    assert scope["surface"] == "resident_fixture_contract_fixed_air_fifteen_field_observation"
    assert scope["advisory_minimum_world_count"] == 4
    assert scope["maintained_default_backend"] == "flecs_cpu_reference"
    assert scope["maintained_default_unchanged_at_all_world_counts"] is True
    assert scope["performance_claims_grade"] == "host_specific_experimental_advisory_only"
    excluded = set(scope["excluded_from_this_promotion"])
    assert "production_dictionary_observation_stack" in excluded
    assert "maintained_performance_contract" in excluded
    assert "kernel_or_launch_tuning_authority" in excluded
    limitations = record["limitations"]
    assert limitations["fixture_surface_only"] is True
    assert limitations["performance_tuning_claimed"] is False
    assert limitations["unrestricted_promotion_claimed"] is False


def test_cp9_evidence_pointers_hash_exactly_against_tracked_artifacts() -> None:
    record = _record()
    for name, descriptor in record["evidence"].items():
        if name == "decision_base_commit":
            assert isinstance(descriptor, str) and len(descriptor) >= 8
            continue
        # The record froze logical (pre-migration) paths; resolve to the
        # fixture tree for the on-disk hash check.
        path = ROOT / retained_paths.physical_relative(str(descriptor["path"]))
        assert path.is_file(), name
        assert path.stat().st_size == descriptor["bytes"], name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == descriptor["sha256"], name


def test_cp9_decision_changes_no_runtime_behavior_until_exposure_scope_lands() -> None:
    record = _record()
    boundary = record["implementation_boundary"]
    assert boundary["behavior_changed_by_this_commit"] is False
    facade = FACADE_CONFIG.read_text(encoding="utf-8")
    for flag in boundary["facade_flags_still_false"]:
        assert f".{flag} = false" in facade, flag
    forbidden = set(record["forbidden_without_new_explicit_authority"])
    assert "changing_the_maintained_default_backend" in forbidden
    assert "registry_or_driver_policy_modification" in forbidden


def test_cp9_recorded_gaps_carry_the_gd_elevation_obligation() -> None:
    record = _record()
    gaps = {gap["id"]: gap for gap in record["recorded_gaps"]}
    assert "gd_artifact_elevation_record_missing" in gaps
    assert "elevation" in gaps["gd_artifact_elevation_record_missing"]["obligation"]
    assert "achieved_counters_predate_cp5_fusion" in gaps


def test_cp9_documents_are_bilingual_and_registered() -> None:
    doc = DOC.read_text(encoding="utf-8")
    doc_zh = DOC_ZH.read_text(encoding="utf-8")
    for text in (doc, doc_zh):
        assert "cp9.scoped_promotion.cuda_resident.20260813" in text
        assert "cuda_resident_cp9_promotion_decision_20260813.json" in text
    assert "Scoped Promotion" in doc
    assert "范围化晋升" in doc_zh
    readme = README.read_text(encoding="utf-8")
    readme_zh = README_ZH.read_text(encoding="utf-8")
    assert "cuda_resident_cp9_promotion_decision_20260813.md" in readme
    assert "cuda_resident_cp9_promotion_decision_20260813.json" in readme
    assert "cuda_resident_cp9_promotion_decision_20260813.zh.md" in readme_zh
