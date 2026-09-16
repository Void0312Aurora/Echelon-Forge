from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.diagnostics import kill_chain_maneuver_apn_admission as admission


def test_summarize_run_preserves_tracker_and_apn_evidence() -> None:
  gain = 0.5
  result = {
    "case_id": "synthetic",
    "nearest_miss_distance_m": 7.5,
    "max_achieved_lateral_g": 12.0,
    "resolved_guidance_runtime": {
      **{
        key: value
        for key, value in admission.PRODUCTION_MECHANISM_TUNING.items()
        if key != "max_lateral_g"
      },
      "guidance_max_lateral_g": 35.0,
      "apn_target_accel_gain": gain,
    },
    "guidance_runtime_trace": [
      {
        "time_s": 3.5,
        "truth_distance_m": 4000.0,
        "target_acceleration_valid": True,
        "target_accel_error_mps2": 1.0,
        "target_track_accel_mps2": 7.0,
        "guidance_apn_lateral_accel_mps2": 2.0,
        "guidance_component_sum_error_mps2": 1.0e-12,
      },
      {
        "time_s": 4.0,
        "truth_distance_m": 3000.0,
        "target_acceleration_valid": True,
        "target_accel_error_mps2": 0.5,
        "target_track_accel_mps2": 7.5,
        "guidance_apn_lateral_accel_mps2": 3.0,
        "guidance_component_sum_error_mps2": 2.0e-12,
      },
    ],
  }

  row = admission._summarize_run(
    result,
    tier="clean_stage4",
    range_km=8.0,
    bearing_deg=30.0,
    target_accel_x_mps2=8.0,
    apn_gain=gain,
    seed=20260621,
  )

  assert row["entered_R_fuze"] is True
  assert row["rho_fuze"] == 0.5
  assert row["acceleration_valid_observed"] is True
  assert row["terminal_acceleration_error_mps2"] == 0.5
  assert row["max_estimated_acceleration_mps2"] == 7.5
  assert row["max_apn_acceleration_mps2"] == 3.0
  assert row["resolved_runtime_mismatch"] == {}


def test_clear_net_benefit_requires_no_envelope_regression() -> None:
  baseline = {
    "apn_gain": 0.0,
    "hit_count": 28,
    "worst_nearest_distance_m": 90.0,
    "total_excess_over_R_fuze_m": 150.0,
  }
  beneficial = {
    "apn_gain": 0.125,
    "hit_count": 28,
    "worst_nearest_distance_m": 85.0,
    "total_excess_over_R_fuze_m": 140.0,
  }
  regression = {
    **beneficial,
    "worst_nearest_distance_m": 95.0,
  }

  assert admission._clear_net_benefit(beneficial, baseline) is True
  assert admission._clear_net_benefit(regression, baseline) is False


def test_mirror_error_pairs_bearing_and_acceleration_signs() -> None:
  common = {
    "tier": "clean_stage4",
    "range_km": 8.0,
    "apn_gain": 0.5,
    "seed": 20260621,
  }
  rows = [
    {
      **common,
      "bearing_deg": -30.0,
      "target_accel_x_mps2": -8.0,
      "nearest_distance_m": 2.0000,
    },
    {
      **common,
      "bearing_deg": 30.0,
      "target_accel_x_mps2": 8.0,
      "nearest_distance_m": 2.0004,
    },
  ]

  assert admission._mirror_error(rows) == pytest.approx(0.0004)


def test_config_backed_parity_keeps_clean_and_noisy_rows_distinct() -> None:
  common = {
    "range_km": 8.0,
    "bearing_deg": 30.0,
    "target_accel_x_mps2": 8.0,
    "seed": 20260621,
  }
  selected = [
    {
      **common,
      "tier": "clean_stage4",
      "nearest_distance_m": 1.0,
      "acceleration_rmse_mps2": 0.0,
    },
    {
      **common,
      "tier": "noisy_stage5_holdout",
      "nearest_distance_m": 2.0,
      "acceleration_rmse_mps2": 3.0,
    },
  ]
  config_backed = [
    {**selected[0], "tier": "config_backed_clean"},
    {**selected[1], "tier": "config_backed_noisy"},
  ]

  parity = admission._config_backed_parity(config_backed, selected)

  assert parity["max_nearest_distance_delta_m"] == 0.0
  assert parity["max_acceleration_rmse_delta_mps2"] == 0.0


def _publication_fixture(tmp_path: Path) -> tuple[dict[str, dict[str, object]], str, str]:
  expected: dict[str, dict[str, object]] = {}
  indexed: dict[str, dict[str, object]] = {}
  for key in admission.PUBLISHED_ARTIFACT_KEYS:
    path = tmp_path / f"{key}.dat"
    payload = f"payload:{key}\n".encode()
    path.write_bytes(payload)
    expected[key] = {
      "sha256": hashlib.sha256(payload).hexdigest(),
      "bytes": len(payload),
    }
    indexed[key] = {**expected[key], "uri": path.as_uri()}
  index_path = tmp_path / "artifact-index.json"
  index_path.write_text(
    json.dumps(
      {
        "schema_version": admission.ARTIFACT_INDEX_SCHEMA_VERSION,
        "artifacts": indexed,
      }
    ),
    encoding="utf-8",
  )
  attestation_path = tmp_path / "runtime-attestation.json"
  attestation_path.write_text(
    json.dumps(
      {
        "schema_version": admission.RUNTIME_ATTESTATION_SCHEMA_VERSION,
        "git_head": "reviewed-head",
        "ef_py_sha256": "ef-py-digest",
      }
    ),
    encoding="utf-8",
  )
  return expected, index_path.as_uri(), attestation_path.as_uri()


def test_bundle_admission_holds_dirty_or_unpublished_evidence(tmp_path: Path) -> None:
  report = {"admission": {"p10_complete": True}}
  expected, index_uri, attestation_uri = _publication_fixture(tmp_path)

  unpublished = admission._bundle_admission(
    report,
    worktree_porcelain="",
    artifact_uri=None,
    artifact_index_uri=None,
    runtime_attestation_uri=None,
    retention_owner="Echelon-Forge maintainers",
    expected_artifacts=expected,
    git_head="reviewed-head",
    ef_py_sha256="ef-py-digest",
  )
  dirty = admission._bundle_admission(
    report,
    worktree_porcelain=" M tools/diagnostics/example.py",
    artifact_uri=tmp_path.as_uri(),
    artifact_index_uri=index_uri,
    runtime_attestation_uri=attestation_uri,
    retention_owner="Echelon-Forge maintainers",
    expected_artifacts=expected,
    git_head="reviewed-head",
    ef_py_sha256="ef-py-digest",
  )
  verified = admission._bundle_admission(
    report,
    worktree_porcelain="",
    artifact_uri=tmp_path.as_uri(),
    artifact_index_uri=index_uri,
    runtime_attestation_uri=attestation_uri,
    retention_owner="Echelon-Forge maintainers",
    expected_artifacts=expected,
    git_head="reviewed-head",
    ef_py_sha256="ef-py-digest",
  )

  assert unpublished == {
    "promotion_status": "held",
    "blockers": [
      "raw_packets_not_published",
      "artifact_index_missing",
      "runtime_build_attestation_missing",
    ],
  }
  assert dirty == {
    "promotion_status": "held",
    "blockers": ["generator_worktree_not_clean"],
  }
  assert verified == {"promotion_status": "passed", "blockers": []}


def test_bundle_admission_rejects_invalid_uri_and_mismatched_attestation(
  tmp_path: Path,
) -> None:
  expected, index_uri, attestation_uri = _publication_fixture(tmp_path)
  report = {"admission": {"p10_complete": True}}

  invalid_uri = admission._bundle_admission(
    report,
    worktree_porcelain="",
    artifact_uri="not-a-uri",
    artifact_index_uri=index_uri,
    runtime_attestation_uri=attestation_uri,
    retention_owner="Echelon-Forge maintainers",
    expected_artifacts=expected,
    git_head="reviewed-head",
    ef_py_sha256="ef-py-digest",
  )
  mismatched_runtime = admission._bundle_admission(
    report,
    worktree_porcelain="",
    artifact_uri=tmp_path.as_uri(),
    artifact_index_uri=index_uri,
    runtime_attestation_uri=attestation_uri,
    retention_owner="Echelon-Forge maintainers",
    expected_artifacts=expected,
    git_head="different-head",
    ef_py_sha256="ef-py-digest",
  )
  mismatched_expected = {key: dict(value) for key, value in expected.items()}
  mismatched_expected[admission.PUBLISHED_ARTIFACT_KEYS[0]]["sha256"] = "0" * 64
  mismatched_artifact = admission._bundle_admission(
    report,
    worktree_porcelain="",
    artifact_uri=tmp_path.as_uri(),
    artifact_index_uri=index_uri,
    runtime_attestation_uri=attestation_uri,
    retention_owner="Echelon-Forge maintainers",
    expected_artifacts=mismatched_expected,
    git_head="reviewed-head",
    ef_py_sha256="ef-py-digest",
  )

  assert invalid_uri == {
    "promotion_status": "held",
    "blockers": ["artifact_uri_invalid"],
  }
  assert mismatched_runtime == {
    "promotion_status": "held",
    "blockers": ["runtime_build_attestation_mismatch"],
  }
  assert mismatched_artifact == {
    "promotion_status": "held",
    "blockers": ["artifact_index_digest_mismatch"],
  }
