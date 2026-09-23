from __future__ import annotations

from pathlib import Path

from tools.maintenance.p5d_measure_supported_row import measure_supported_row


def test_supported_row_measurement_collects_repeated_process_slo_and_adoption(tmp_path: Path) -> None:
  root = Path(__file__).resolve().parents[3]
  report = measure_supported_row(
    current_build=root / "build-long-horizon-p5d-wheel",
    rollback_build=root / "build-long-horizon-p5c-wheel-final3",
    cycles=3,
    state_dir=tmp_path / "processes",
    plan_sha256="1" * 64,
  )
  assert report["cycles"] == 3
  assert report["release_id"] == "local-supported-row"
  assert report["plan_sha256"] == "1" * 64
  assert report["slo"]["passed"]
  assert report["slo"]["reasons"] == []
  assert report["snapshot"]["ratios"]["caller_adoption"] == 1.0
  assert len(report["samples"]) == 3
  assert all(sample["caller_adopted"] for sample in report["samples"])
