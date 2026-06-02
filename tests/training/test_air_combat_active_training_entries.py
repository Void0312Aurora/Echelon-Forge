from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
AIR_COMBAT_ACTIVE_DIR = REPO_ROOT / "examples" / "config" / "training" / "active" / "air_combat"
STAGE1_CONFIG = AIR_COMBAT_ACTIVE_DIR / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1.json"
STAGE1_TEMPORAL_CONFIG = (
    AIR_COMBAT_ACTIVE_DIR / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_temporal_world_batch_probe_v1.json"
)
STAGE1_HYBRID_CONFIG = (
    AIR_COMBAT_ACTIVE_DIR / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1.json"
)
STAGE1_HYBRID_TEMPORAL_CONFIG = (
    AIR_COMBAT_ACTIVE_DIR / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_world_batch_probe_v1.json"
)
STAGE1_HYBRID_SHAPED_CONFIG = (
    AIR_COMBAT_ACTIVE_DIR / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json"
)
STAGE1_HYBRID_TEMPORAL_SHAPED_CONFIG = (
    AIR_COMBAT_ACTIVE_DIR
    / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1.json"
)
STAGE1_SCENARIO = REPO_ROOT / "scenarios" / "air_combat" / "1v1" / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json"
STAGE1_SHAPED_SCENARIO = (
    REPO_ROOT
    / "scenarios"
    / "air_combat"
    / "1v1"
    / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class AirCombatActiveTrainingEntryTests(unittest.TestCase):
    def test_stage1_bvr_probe_config_matches_maintained_world_batch_surface(self) -> None:
        cfg = _load_json(STAGE1_CONFIG)
        scenario = _load_json(STAGE1_SCENARIO)

        self.assertEqual(cfg.get("agent_layer"), "execution")
        self.assertEqual(cfg.get("algo"), "AdaptiveKLPPO")
        self.assertEqual(cfg.get("policy"), "HierarchicalMoEExecutionPolicy")
        self.assertEqual(int(cfg.get("n_envs")), 4)
        self.assertEqual(int(cfg.get("total_timesteps")), 8192)

        runtime = cfg.get("runtime")
        self.assertIsInstance(runtime, dict)
        self.assertTrue(bool(runtime.get("world_batch_vec_env")))
        self.assertEqual(int(runtime.get("world_batch_threads")), 4)
        self.assertEqual(runtime.get("batch_observation_backend"), "compiled")
        self.assertEqual(runtime.get("batch_visual_backend"), "compiled")
        self.assertTrue(bool(runtime.get("policy_observation_torch_bridge")))

        env = cfg.get("env")
        self.assertIsInstance(env, dict)
        self.assertEqual(env.get("action_mode"), "full")
        self.assertEqual(env.get("mission_obs_mode"), "basic")
        self.assertEqual(env.get("step_info_mode"), "terminal")
        self.assertEqual(env.get("execution_step_runtime_mode"), "compiled")
        self.assertEqual(env.get("flight_shaping_backend"), "compiled")

        hyperparams = cfg.get("hyperparameters")
        self.assertIsInstance(hyperparams, dict)
        self.assertEqual(int(hyperparams.get("n_steps")), 256)
        self.assertEqual(int(hyperparams.get("batch_size")), 512)
        self.assertEqual(hyperparams.get("policy_kwargs", {}).get("features_extractor_class"), "TransformerExtractor")

        realism = scenario.get("realism_gradient")
        self.assertIsInstance(realism, dict)
        self.assertEqual(realism.get("domain"), "air_combat")
        self.assertEqual(realism.get("workline"), "1v1")
        self.assertEqual(realism.get("stage"), "A1-S1")
        self.assertEqual(scenario.get("mission_command", {}).get("assigned_target_name"), "Red_Target")
        self.assertTrue(bool(scenario.get("mission_command", {}).get("authorization_to_fire")))
        self.assertEqual(scenario.get("entities", [])[1].get("ammo", {}).get("missiles_remaining"), 0)

    def test_stage1_bvr_temporal_probe_pairs_with_reactive_baseline(self) -> None:
        reactive = _load_json(STAGE1_CONFIG)
        temporal = _load_json(STAGE1_TEMPORAL_CONFIG)

        for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
            self.assertEqual(temporal.get(key), reactive.get(key), key)
        self.assertEqual(temporal.get("runtime"), reactive.get("runtime"))
        self.assertEqual(temporal.get("early_stop"), reactive.get("early_stop"))
        self.assertEqual(temporal.get("diagnostics"), reactive.get("diagnostics"))
        self.assertEqual(temporal.get("hmoe"), reactive.get("hmoe"))

        reactive_env = dict(reactive.get("env", {}))
        temporal_env = dict(temporal.get("env", {}))
        self.assertEqual(int(temporal_env.pop("temporal_history_len")), 16)
        self.assertEqual(temporal_env, reactive_env)

        reactive_hyper = dict(reactive.get("hyperparameters", {}))
        temporal_hyper = dict(temporal.get("hyperparameters", {}))
        reactive_policy_kwargs = dict(reactive_hyper.pop("policy_kwargs"))
        temporal_policy_kwargs = dict(temporal_hyper.pop("policy_kwargs"))
        self.assertEqual(temporal_hyper, reactive_hyper)
        self.assertEqual(
            temporal_policy_kwargs.get("features_extractor_class"),
            "TemporalTransformerExtractor",
        )
        self.assertEqual(
            reactive_policy_kwargs.get("features_extractor_class"),
            "TransformerExtractor",
        )
        self.assertEqual(temporal_policy_kwargs.get("family_subexpert_counts"), reactive_policy_kwargs.get("family_subexpert_counts"))
        self.assertEqual(temporal_policy_kwargs.get("net_arch"), reactive_policy_kwargs.get("net_arch"))
        temporal_extractor = temporal_policy_kwargs.get("features_extractor_kwargs", {})
        self.assertEqual(int(temporal_extractor.get("features_dim")), 192)
        self.assertEqual(int(temporal_extractor.get("temporal_n_heads")), 4)
        self.assertEqual(int(temporal_extractor.get("temporal_n_layers")), 2)

    def test_stage1_bvr_hybrid_probe_pairs_with_full_action_baseline(self) -> None:
        full = _load_json(STAGE1_CONFIG)
        hybrid = _load_json(STAGE1_HYBRID_CONFIG)

        for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
            self.assertEqual(hybrid.get(key), full.get(key), key)
        self.assertEqual(hybrid.get("runtime"), full.get("runtime"))
        self.assertEqual(hybrid.get("early_stop"), full.get("early_stop"))
        self.assertEqual(hybrid.get("diagnostics"), full.get("diagnostics"))
        self.assertEqual(hybrid.get("hmoe"), full.get("hmoe"))

        full_env = dict(full.get("env", {}))
        hybrid_env = dict(hybrid.get("env", {}))
        self.assertEqual(full_env.pop("action_mode"), "full")
        self.assertEqual(hybrid_env.pop("action_mode"), "air_combat_hybrid_v1")
        self.assertEqual(hybrid_env, full_env)

        hybrid_policy_kwargs = hybrid.get("hyperparameters", {}).get("policy_kwargs", {})
        self.assertEqual(hybrid_policy_kwargs.get("features_extractor_class"), "TransformerExtractor")
        self.assertEqual(hybrid_policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")

    def test_stage1_bvr_hybrid_temporal_probe_pairs_with_hybrid_reactive_baseline(self) -> None:
        hybrid = _load_json(STAGE1_HYBRID_CONFIG)
        hybrid_temporal = _load_json(STAGE1_HYBRID_TEMPORAL_CONFIG)

        for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
            self.assertEqual(hybrid_temporal.get(key), hybrid.get(key), key)
        self.assertEqual(hybrid_temporal.get("runtime"), hybrid.get("runtime"))
        self.assertEqual(hybrid_temporal.get("early_stop"), hybrid.get("early_stop"))
        self.assertEqual(hybrid_temporal.get("diagnostics"), hybrid.get("diagnostics"))
        self.assertEqual(hybrid_temporal.get("hmoe"), hybrid.get("hmoe"))

        hybrid_env = dict(hybrid.get("env", {}))
        hybrid_temporal_env = dict(hybrid_temporal.get("env", {}))
        self.assertEqual(int(hybrid_temporal_env.pop("temporal_history_len")), 16)
        self.assertEqual(hybrid_temporal_env, hybrid_env)

        hybrid_hyper = dict(hybrid.get("hyperparameters", {}))
        hybrid_temporal_hyper = dict(hybrid_temporal.get("hyperparameters", {}))
        hybrid_policy_kwargs = dict(hybrid_hyper.pop("policy_kwargs"))
        hybrid_temporal_policy_kwargs = dict(hybrid_temporal_hyper.pop("policy_kwargs"))
        self.assertEqual(hybrid_temporal_hyper, hybrid_hyper)
        self.assertEqual(hybrid_policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")
        self.assertEqual(hybrid_temporal_policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")
        self.assertEqual(hybrid_policy_kwargs.get("features_extractor_class"), "TransformerExtractor")
        self.assertEqual(hybrid_temporal_policy_kwargs.get("features_extractor_class"), "TemporalTransformerExtractor")
        self.assertEqual(
            hybrid_temporal_policy_kwargs.get("family_subexpert_counts"),
            hybrid_policy_kwargs.get("family_subexpert_counts"),
        )
        self.assertEqual(hybrid_temporal_policy_kwargs.get("net_arch"), hybrid_policy_kwargs.get("net_arch"))

    def test_stage1_bvr_hybrid_shaped_probe_uses_training_shaped_scenario_contract(self) -> None:
        hybrid = _load_json(STAGE1_HYBRID_CONFIG)
        shaped = _load_json(STAGE1_HYBRID_SHAPED_CONFIG)
        scenario = _load_json(STAGE1_SHAPED_SCENARIO)

        for key in ("agent_layer", "algo", "policy", "n_envs"):
            self.assertEqual(shaped.get(key), hybrid.get(key), key)
        self.assertEqual(int(shaped.get("total_timesteps")), 32768)
        self.assertEqual(int(shaped.get("save_freq")), 8192)
        self.assertEqual(shaped.get("runtime"), hybrid.get("runtime"))
        self.assertEqual(shaped.get("env"), hybrid.get("env"))
        self.assertEqual(shaped.get("early_stop"), hybrid.get("early_stop"))
        self.assertEqual(shaped.get("diagnostics"), hybrid.get("diagnostics"))
        self.assertEqual(shaped.get("hmoe"), hybrid.get("hmoe"))
        wrapper_cfg = shaped.get("wrappers", {}).get("multi_timescale_action", {})
        self.assertTrue(bool(wrapper_cfg.get("enabled")))
        self.assertEqual(wrapper_cfg.get("scripted_baseline_mode"), "stable_flight")
        self.assertEqual(wrapper_cfg.get("scripted_blend_indices"), [0, 1, 2, 3])
        self.assertEqual(wrapper_cfg.get("scripted_lock_indices"), [])
        self.assertEqual(wrapper_cfg.get("low_freq_indices"), [])
        self.assertEqual(wrapper_cfg.get("snap_binary_indices"), [])
        self.assertEqual(wrapper_cfg.get("binary_hysteresis_indices"), [])

        shaped_policy_kwargs = dict(shaped.get("hyperparameters", {}).get("policy_kwargs", {}))
        hybrid_policy_kwargs = dict(hybrid.get("hyperparameters", {}).get("policy_kwargs", {}))
        self.assertLess(
            float(shaped_policy_kwargs.pop("log_std_init")),
            float(hybrid_policy_kwargs.pop("log_std_init")),
        )
        self.assertEqual(shaped_policy_kwargs, hybrid_policy_kwargs)

        self.assertIn("training_shaped", scenario.get("realism_gradient", {}).get("stage_name", ""))
        rewards = scenario.get("rewards", {})
        self.assertTrue(bool(rewards.get("air_combat_release_shaping_enabled")))
        self.assertGreater(float(rewards.get("air_combat_first_release_bonus", 0.0)), 0.0)
        self.assertLess(float(rewards.get("air_combat_invalid_fire_penalty", 0.0)), 0.0)
        self.assertLess(float(rewards.get("air_combat_repeat_release_penalty", 0.0)), 0.0)
        self.assertEqual(scenario.get("entities", [])[0].get("ammo", {}).get("missiles_remaining"), 4)
        self.assertEqual(scenario.get("entities", [])[1].get("ammo", {}).get("missiles_remaining"), 0)

    def test_stage1_bvr_hybrid_temporal_shaped_probe_pairs_with_hybrid_shaped_baseline(self) -> None:
        shaped = _load_json(STAGE1_HYBRID_SHAPED_CONFIG)
        temporal_shaped = _load_json(STAGE1_HYBRID_TEMPORAL_SHAPED_CONFIG)

        for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
            self.assertEqual(temporal_shaped.get(key), shaped.get(key), key)
        self.assertEqual(temporal_shaped.get("runtime"), shaped.get("runtime"))
        self.assertEqual(temporal_shaped.get("early_stop"), shaped.get("early_stop"))
        self.assertEqual(temporal_shaped.get("diagnostics"), shaped.get("diagnostics"))
        self.assertEqual(temporal_shaped.get("hmoe"), shaped.get("hmoe"))
        self.assertEqual(temporal_shaped.get("wrappers"), shaped.get("wrappers"))

        shaped_env = dict(shaped.get("env", {}))
        temporal_shaped_env = dict(temporal_shaped.get("env", {}))
        self.assertEqual(int(temporal_shaped_env.pop("temporal_history_len")), 16)
        self.assertEqual(temporal_shaped_env, shaped_env)

        shaped_hyper = dict(shaped.get("hyperparameters", {}))
        temporal_shaped_hyper = dict(temporal_shaped.get("hyperparameters", {}))
        shaped_policy_kwargs = dict(shaped_hyper.pop("policy_kwargs"))
        temporal_shaped_policy_kwargs = dict(temporal_shaped_hyper.pop("policy_kwargs"))
        self.assertEqual(temporal_shaped_hyper, shaped_hyper)
        self.assertEqual(shaped_policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")
        self.assertEqual(temporal_shaped_policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")
        self.assertEqual(shaped_policy_kwargs.get("features_extractor_class"), "TransformerExtractor")
        self.assertEqual(temporal_shaped_policy_kwargs.get("features_extractor_class"), "TemporalTransformerExtractor")
        self.assertEqual(
            temporal_shaped_policy_kwargs.get("family_subexpert_counts"),
            shaped_policy_kwargs.get("family_subexpert_counts"),
        )
        self.assertEqual(temporal_shaped_policy_kwargs.get("net_arch"), shaped_policy_kwargs.get("net_arch"))
        self.assertEqual(temporal_shaped_policy_kwargs.get("log_std_init"), shaped_policy_kwargs.get("log_std_init"))
        temporal_extractor = temporal_shaped_policy_kwargs.get("features_extractor_kwargs", {})
        shaped_extractor = shaped_policy_kwargs.get("features_extractor_kwargs", {})
        self.assertEqual(int(temporal_extractor.get("features_dim")), int(shaped_extractor.get("features_dim")))
        self.assertEqual(int(temporal_extractor.get("n_heads")), int(shaped_extractor.get("n_heads")))
        self.assertEqual(int(temporal_extractor.get("n_layers")), int(shaped_extractor.get("n_layers")))
        self.assertEqual(int(temporal_extractor.get("temporal_n_heads")), 4)
        self.assertEqual(int(temporal_extractor.get("temporal_n_layers")), 2)

    def test_stage1_bvr_probe_bootstraps_on_current_execution_path(self) -> None:
        entries = [
            ("reactive", STAGE1_CONFIG, STAGE1_SCENARIO),
            ("temporal", STAGE1_TEMPORAL_CONFIG, STAGE1_SCENARIO),
            ("hybrid", STAGE1_HYBRID_CONFIG, STAGE1_SCENARIO),
            ("hybrid_temporal", STAGE1_HYBRID_TEMPORAL_CONFIG, STAGE1_SCENARIO),
            ("hybrid_shaped", STAGE1_HYBRID_SHAPED_CONFIG, STAGE1_SHAPED_SCENARIO),
            ("hybrid_temporal_shaped", STAGE1_HYBRID_TEMPORAL_SHAPED_CONFIG, STAGE1_SHAPED_SCENARIO),
        ]
        for label, config_path, scenario_path in entries:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmpdir:
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(REPO_ROOT / "train.py"),
                        "--scenario",
                        str(scenario_path),
                        "--train_config",
                        str(config_path),
                        "--output_base",
                        tmpdir,
                        "--run_name",
                        f"air_combat_stage1_bvr_{label}_probe_bootstrap",
                        "--test_only",
                    ],
                    cwd=str(REPO_ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=False,
                )

            self.assertNotIn("unknown agent_layer", proc.stdout)
            self.assertIn("Agent layer: execution", proc.stdout)
            self.assertIn("world_batch_vec_env=True", proc.stdout)
            self.assertIn("World batch runtime:", proc.stdout)
            self.assertIn("Execution reward runtime: requested_backend=compiled effective_backend=compiled", proc.stdout)
            if label in {"hybrid", "hybrid_temporal", "hybrid_shaped", "hybrid_temporal_shaped"}:
                self.assertIn("action_mode=air_combat_hybrid_v1", proc.stdout)
            if label in {"temporal", "hybrid_temporal", "hybrid_temporal_shaped"}:
                self.assertIn("temporal_history_len=16", proc.stdout)
            self.assertIn("Error: --test_only requires --resume_path", proc.stdout)


if __name__ == "__main__":
    unittest.main()
