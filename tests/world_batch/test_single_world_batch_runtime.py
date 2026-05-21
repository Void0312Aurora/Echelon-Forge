from __future__ import annotations

import json
import tempfile
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402

from python.rl.runtime.single_world_batch_runtime import (  # noqa: E402
    build_single_world_batch_execution_runtime,
)


def _inline_single_world_scenario() -> dict:
    return {
        "scenario_name": "wp16_single_world_runtime_window_inline",
        "meta": {
            "max_steps": 2,
        },
        "environment": {
            "time_step": 0.05,
            "terrain_type": "legacy",
            "wind": {
                "speed_mps": 2.0,
                "dir_from_deg": 180.0,
                "shear_mps_per_km": 0.0,
            },
            "zones": [
                {
                    "name": "Runway_A",
                    "x": 0.0,
                    "y": 0.0,
                    "width": 60.0,
                    "length": 2500.0,
                    "heading": 90.0,
                    "surface": "Concrete",
                }
            ],
        },
        "mission_command": {
            "command_code": 2,
            "target_heading": 90.0,
            "target_altitude": 1200.0,
            "target_speed": 180.0,
        },
        "entities": [
            {
                "name": "Lead",
                "type": "Aircraft",
                "side": "Blue",
                "is_agent": True,
                "pos": [-1400.0, 0.0, 1200.0],
                "vel": [0.0, 180.0, 0.0],
                "heading": 90.0,
            }
        ],
    }


class SingleWorldBatchRuntimeTests(unittest.TestCase):
    def test_single_world_runtime_step_uses_runtime_window_evidence_when_facade_api_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/single_world_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

            runtime = build_single_world_batch_execution_runtime(
                scenario_path=scenario_path,
                env_settings={
                    "include_visual": False,
                    "include_proprio": False,
                },
            )
            try:
                _obs, _reset_info = runtime.reset(seed=7)
                action = np.zeros((17,), dtype=np.float32)
                _next_obs, _reward, _terminated, _truncated, info = runtime.step(action)

                evidence = runtime.last_runtime_window_evidence
                self.assertIsNotNone(evidence)
                assert evidence is not None
                self.assertFalse(bool(evidence.uses_compat_fallback))
                self.assertEqual(
                    [str(getattr(record, "barrier_id", "") or "") for record in evidence.barrier_trace],
                    ["input_injection", "window_commit", "export"],
                )
                self.assertEqual(
                    [str(getattr(record, "node_id", "") or "") for record in evidence.executed_nodes],
                    [
                        "p7.fire_control_launch.v1",
                        "p9.effects_damage.v1",
                        "p10.observation_export.v1",
                    ],
                )
                self.assertAlmostEqual(
                    float(getattr(evidence.window_result.cadence_config, "window_duration_s", 0.0)),
                    0.1,
                    places=6,
                )
                cadence_domains = [
                    str(getattr(record, "domain", "") or "")
                    for record in list(getattr(evidence.window_result, "cadence_trace", []))
                ]
                self.assertEqual(cadence_domains.count("policy"), 1)
                self.assertEqual(cadence_domains.count("control"), 2)
                self.assertEqual(cadence_domains.count("physics"), 6)
                self.assertEqual(cadence_domains.count("export"), 1)
                self.assertTrue(
                    any(
                        bool(getattr(record, "held", False))
                        or str(getattr(record, "decision", "") or "") in {"held", "expired"}
                        for record in list(getattr(evidence.window_result, "cadence_trace", []))
                        if str(getattr(record, "domain", "") or "") == "control"
                    )
                )
                self.assertEqual(str(evidence.observation_packet.barrier_id), "export")
                self.assertEqual(
                    str(evidence.observation_packet.provenance.source_label),
                    "facade_observation_packet",
                )
                self.assertEqual(str(evidence.engagement_packet.barrier_id), "export")
                self.assertEqual(
                    str(evidence.engagement_packet.packet_provenance.source_label),
                    "track_state_packet",
                )
                self.assertEqual(
                    str(evidence.engagement_packet.diagnostics_provenance.source_label),
                    "world_truth_diagnostics",
                )
                self.assertIn("runtime_window_evidence", info)
                self.assertEqual(
                    info["runtime_window_evidence"]["barrier_ids"],
                    ["input_injection", "window_commit", "export"],
                )
                self.assertEqual(
                    info["runtime_window_evidence"]["observation_provenance"],
                    "facade_observation_packet",
                )
                self.assertEqual(
                    info["runtime_window_evidence"]["engagement_provenance"],
                    "track_state_packet",
                )
                self.assertEqual(
                    info["runtime_window_evidence"]["diagnostics_provenance"],
                    "world_truth_diagnostics",
                )
                self.assertEqual(
                    info["runtime_window_evidence"]["cadence_reason"],
                    "selected_slice_cadence_trace_runtime_window_wp17c",
                )
            finally:
                runtime.close()

    def test_single_world_runtime_reports_explicit_compatibility_fallback_when_window_api_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/single_world_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

            runtime = build_single_world_batch_execution_runtime(
                scenario_path=scenario_path,
                env_settings={
                    "include_visual": False,
                    "include_proprio": False,
                },
            )
            try:
                original_supports = runtime.access.supports_runtime_window_api
                runtime.access.supports_runtime_window_api = lambda: False  # type: ignore[method-assign]
                _obs, _reset_info = runtime.reset(seed=9)
                action = np.zeros((17,), dtype=np.float32)
                _next_obs, _reward, _terminated, _truncated, info = runtime.step(action)

                self.assertIsNone(runtime.last_runtime_window_evidence)
                self.assertEqual(
                    info["runtime_window_evidence"]["cadence_reason"],
                    "compatibility_fallback_world_batch_step_worlds_wp16c",
                )
                self.assertTrue(bool(info["runtime_window_evidence"]["uses_compat_fallback"]))
                self.assertEqual(info["runtime_window_evidence"]["barrier_ids"], [])
                runtime.access.supports_runtime_window_api = original_supports  # type: ignore[method-assign]
            finally:
                runtime.close()

    def test_world_batch_vec_env_and_leader_group_expose_window_evidence_accessors_without_forcing_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/single_world_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

            from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv  # noqa: E402
            from python.rl.runtime.leader_world_batch_runtime import (  # noqa: E402
                LeaderWorldBatchExecutionRuntimeGroup,
            )

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=False,
            )
            try:
                self.assertTrue(hasattr(vec_env, "last_runtime_window_evidence"))
                self.assertIsNone(vec_env.last_runtime_window_evidence)

                group = LeaderWorldBatchExecutionRuntimeGroup(vec_env)
                self.assertTrue(hasattr(group, "last_runtime_window_evidence"))
                self.assertIsNone(group.last_runtime_window_evidence)
            finally:
                vec_env.close()


if __name__ == "__main__":
    unittest.main()
