"""Exercise the P2-B baseline against the local supported row."""

from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.governance_audit

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_p2b_baseline_records_repeatable_control_and_runtime_observations() -> None:
  from tools.maintenance.p2b_sustainability_baseline import build_baseline

  report = build_baseline(
    current_build=REPO_ROOT / "build-long-horizon-p5d-wheel",
    rollback_build=REPO_ROOT / "build-long-horizon-p5c-wheel-final3",
    runs=1,
    process_cycles=1,
  )

  assert report["status"] == "passed"
  assert report["controls"]["declared"] == 8
  assert report["control_yield"]["check_runs"] == 4
  assert report["control_yield"]["observed_pass_rate"] == 1.0
  assert report["supported_row"]["total_cycles"] == 1
  assert report["supported_row"]["caller_adoption_rate"] == 1.0
  assert report["supported_row"]["resource_observations"]["sample_count"] == 2
  assert report["supported_row"]["resource_observations"]["budget_status"] == "observed_only"
  assert report["supported_row"]["safety_events"] == {
    "stale_reference_rejections": 0,
    "wrong_epoch_results": 0,
    "duplicate_publications": 0,
    "security_denials": 0,
  }
  assert report["evidence_retrieval"]["availability_ratio"] == 1.0
