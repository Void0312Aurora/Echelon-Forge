from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()


class EvalSB3Tests(unittest.TestCase):
    def test_tool_reports_slot_summary_for_cooperative_policy(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        model_path = repo_root / "experiments" / "coop_cruise_navv2_formation_role_v1_formal_20260512_gpu" / "final_model.zip"
        if not model_path.exists():
            self.skipTest("cooperative formal checkpoint is not present in workspace")

        with tempfile.TemporaryDirectory() as tmpdir:
            json_out = Path(tmpdir) / "coop_eval.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "tools" / "eval" / "eval_sb3.py"),
                    "--mode",
                    "cooperative",
                    "--scenario",
                    str(repo_root / "scenarios" / "cruise" / "cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json"),
                    "--train_config",
                    str(repo_root / "examples" / "config" / "training" / "active" / "cooperative_cruise_nav_v2_formation_v1.json"),
                    "--model",
                    str(model_path),
                    "--episodes",
                    "1",
                    "--seed",
                    "100",
                    "--json_out",
                    str(json_out),
                ],
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
                env=dict(os.environ, PYTHONPATH=str(repo_root / "build-workshop")),
            )

            self.assertEqual(proc.returncode, 0, msg=proc.stdout)
            payload = json.loads(json_out.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("mode"), "cooperative")
            self.assertIn("slot_summary", payload)
            self.assertGreaterEqual(len(payload["slot_summary"]), 2)
            self.assertIn("policy_routes", payload)
            self.assertIn("shared_execution", payload["policy_routes"])
            slot_names = set(payload["slot_summary"].keys())
            self.assertTrue(any("ElementLead" in name for name in slot_names))
            self.assertTrue(any("Wingman" in name for name in slot_names))
            for summary in payload["slot_summary"].values():
                self.assertIn("termination_counts", summary)
                self.assertIn("shared_world_reset_rate", summary)


if __name__ == "__main__":
    unittest.main()
