"""Exercise the P2-B baseline against the local supported row."""

from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.governance_audit

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_p2b_cadence_counts_observed_package_pairs_without_cross_products() -> None:
  from tools.maintenance.p2b_sustainability_baseline import _summarize_release_cadence

  report = _summarize_release_cadence([
    {
      "release_id": "release-one",
      "plan_sha256": "a" * 64,
      "cycles": 2,
      "slo": {"passed": True},
      "samples": [
        {"current_pyd_sha256": "1" * 64, "rollback_pyd_sha256": "2" * 64},
        {"current_pyd_sha256": "1" * 64, "rollback_pyd_sha256": "2" * 64},
      ],
    },
    {
      "release_id": "release-two",
      "plan_sha256": "a" * 64,
      "cycles": 1,
      "slo": {"passed": True},
      "samples": [
        {"current_pyd_sha256": "3" * 64, "rollback_pyd_sha256": "4" * 64},
      ],
    },
  ])

  assert report["status"] == "distinct_package_batches_observed"
  assert report["representative_release_cadence"] == "open"
  assert report["distinct_release_id_count"] == 2
  assert report["distinct_plan_sha256_count"] == 1
  assert report["distinct_package_pair_count"] == 2
  assert report["batches"][0]["package_pair_consistent"] is True
  assert report["batches"][1]["package_pair_consistent"] is True


def test_p2b_cadence_rejects_incomplete_and_changed_pairs_within_one_batch() -> None:
  from tools.maintenance.p2b_sustainability_baseline import _summarize_release_cadence

  incomplete = _summarize_release_cadence([{
    "release_id": "release-one",
    "plan_sha256": "a" * 64,
    "cycles": 1,
    "slo": {"passed": True},
    "samples": [{"current_pyd_sha256": "", "rollback_pyd_sha256": "2" * 64}],
  }])
  assert incomplete["status"] == "incomplete_package_observation"

  inconsistent = _summarize_release_cadence([{
    "release_id": "release-one",
    "plan_sha256": "a" * 64,
    "cycles": 2,
    "slo": {"passed": True},
    "samples": [
      {"current_pyd_sha256": "1" * 64, "rollback_pyd_sha256": "2" * 64},
      {"current_pyd_sha256": "3" * 64, "rollback_pyd_sha256": "4" * 64},
    ],
  }])
  assert inconsistent["status"] == "inconsistent_package_batch"
  assert inconsistent["distinct_package_pair_count"] == 2
  assert inconsistent["batches"][0]["package_pair_consistent"] is False


def test_p2b_baseline_records_repeatable_control_and_runtime_observations() -> None:
  from tools.maintenance.p2b_sustainability_baseline import build_baseline

  report = build_baseline(
    current_build=REPO_ROOT / "build-long-horizon-p5d-wheel",
    rollback_build=REPO_ROOT / "build-long-horizon-p5c-wheel-final3",
    runs=1,
    process_cycles=1,
  )

  assert report["status"] == "passed"
  assert report["controls"]["declared"] == 6
  assert report["control_yield"]["check_runs"] == 4
  assert report["control_yield"]["observed_pass_rate"] == 1.0
  assert report["supported_row"]["total_cycles"] == 1
  assert report["supported_row"]["caller_adoption_rate"] == 1.0
  assert report["supported_row"]["resource_observations"]["sample_count"] == 2
  assert report["supported_row"]["resource_observations"]["budget_status"] == "observed_only"
  assert report["supported_row"]["cadence"]["status"] == "local_repeat_only"
  assert report["supported_row"]["cadence"]["representative_release_cadence"] == "open"
  assert report["supported_row"]["cadence"]["release_batch_count"] == 1
  assert report["supported_row"]["cadence"]["distinct_release_id_count"] == 1
  assert report["supported_row"]["cadence"]["distinct_package_pair_count"] == 1
  assert report["supported_row"]["cadence"]["batches"][0]["package_pair_consistent"] is True
  assert report["supported_row"]["safety_events"] == {
    "stale_reference_rejections": 0,
    "wrong_epoch_results": 0,
    "duplicate_publications": 0,
    "security_denials": 0,
  }
  assert report["evidence_retrieval"]["availability_ratio"] == 1.0
