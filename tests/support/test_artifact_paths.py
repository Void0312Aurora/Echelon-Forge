from __future__ import annotations

from tempfile import TemporaryDirectory
import unittest
from pathlib import Path
from unittest.mock import patch

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

from python import artifact_paths # noqa: E402


class ArtifactPathResolutionTests(unittest.TestCase):
  def _assert_archived_path_resolves(self, requested: str, archived: str) -> None:
    with TemporaryDirectory() as tmp_dir:
      repo_root = Path(tmp_dir)
      expected = repo_root / archived
      expected.parent.mkdir(parents=True)
      expected.touch()
      with patch.object(artifact_paths, "_REPO_ROOT", repo_root):
        resolved = artifact_paths.resolve_artifact_path(requested)

      self.assertIsNotNone(resolved)
      self.assertEqual(Path(str(resolved)), expected.resolve())

  def test_archived_execution_model_path_resolves(self) -> None:
    self._assert_archived_path_resolves(
      "experiments_tmp/20260318_p5_takeoff_to_landing_continuous_v3_retrain_v1/final_model.zip",
      (
        "experiments/_archive_20260322_test_results/root_level/experiments_tmp/"
        "20260318_p5_takeoff_to_landing_continuous_v3_retrain_v1/final_model.zip"
      ),
    )

  def test_archived_leader_model_path_resolves(self) -> None:
    self._assert_archived_path_resolves(
      "experiments/20260319_p7_leader_c2_reporting_smoke_v2/final_model.zip",
      (
        "experiments/_archive_20260322_test_results/"
        "20260319_p7_leader_c2_reporting_smoke_v2/final_model.zip"
      ),
    )


if __name__ == "__main__":
  unittest.main()
