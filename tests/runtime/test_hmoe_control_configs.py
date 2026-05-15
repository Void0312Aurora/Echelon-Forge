from __future__ import annotations

import copy
import json
import subprocess
import unittest
from pathlib import Path


class HMoEControlConfigTests(unittest.TestCase):
    def _load_json(self, path: Path) -> dict:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)
        return data

    def _strip_policy_specific_fields(self, config: dict) -> dict:
        payload = copy.deepcopy(config)
        payload.pop("policy", None)
        hmoe_cfg = payload.get("hmoe", {})
        if isinstance(hmoe_cfg, dict):
            hmoe_cfg.pop("bootstrap_from_shared_action_head", None)
            if not hmoe_cfg:
                payload.pop("hmoe", None)
        hyper = payload.get("hyperparameters", {})
        if isinstance(hyper, dict):
            policy_kwargs = hyper.get("policy_kwargs", {})
            if isinstance(policy_kwargs, dict):
                for key in (
                    "family_subexpert_counts",
                    "hmoe_residual_scale",
                    "hmoe_head_lr_scale",
                    "hmoe_residual_warmup_fraction",
                    "hmoe_residual_start_factor",
                ):
                    policy_kwargs.pop(key, None)
        return payload

    def test_fair_configs_only_differ_in_policy_specific_fields(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        shared_path = (
            repo_root
            / "examples"
            / "config"
            / "training"
            / "active"
            / "cooperative_takeoff_to_cruise_nav_shared_fair_v1.json"
        )
        hmoe_path = (
            repo_root
            / "examples"
            / "config"
            / "training"
            / "active"
            / "cooperative_takeoff_to_cruise_nav_hmoe_fair_v1.json"
        )
        shared_cfg = self._load_json(shared_path)
        hmoe_cfg = self._load_json(hmoe_path)

        self.assertEqual(shared_cfg.get("policy"), "SquashedMultiInputPolicy")
        self.assertEqual(hmoe_cfg.get("policy"), "HierarchicalMoEExecutionPolicy")
        self.assertEqual(
            self._strip_policy_specific_fields(shared_cfg),
            self._strip_policy_specific_fields(hmoe_cfg),
        )

    def test_control_script_has_valid_shell_syntax(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        script_path = repo_root / "scripts" / "run_hmoe_cooperative_takeoff_to_cruise_control.sh"
        proc = subprocess.run(
            ["bash", "-n", str(script_path)],
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout)


if __name__ == "__main__":
    unittest.main()
