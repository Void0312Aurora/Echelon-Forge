from __future__ import annotations

import unittest
from pathlib import Path

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

from python.artifact_paths import resolve_artifact_path # noqa: E402


class ArtifactPathResolutionTests(unittest.TestCase):
  def test_archived_execution_model_path_resolves(self) -> None:
    resolved = resolve_artifact_path(
      "experiments_tmp/20260318_p5_takeoff_to_landing_continuous_v3_retrain_v1/final_model.zip"
    )
    self.assertIsNotNone(resolved)
    self.assertTrue(Path(str(resolved)).exists())
    self.assertIn("_archive_20260322_test_results", str(resolved))

  def test_archived_leader_model_path_resolves(self) -> None:
    resolved = resolve_artifact_path(
      "experiments/20260319_p7_leader_c2_reporting_smoke_v2/final_model.zip"
    )
    self.assertIsNotNone(resolved)
    self.assertTrue(Path(str(resolved)).exists())
    self.assertIn("_archive_20260322_test_results", str(resolved))


if __name__ == "__main__":
  unittest.main()
