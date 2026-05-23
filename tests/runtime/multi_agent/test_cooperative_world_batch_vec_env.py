from __future__ import annotations

import json
import math
import tempfile
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

try:
    from stable_baselines3 import PPO  # noqa: E402
except ModuleNotFoundError:  # pragma: no cover
    PPO = None

try:
    from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv  # noqa: E402
except ModuleNotFoundError:  # pragma: no cover
    CooperativeWorldBatchVecEnv = None

import python.rl.runtime.cooperative_world_batch_vec_env as cooperative_vec_env_module  # noqa: E402
from python.rl.runtime.multi_agent_runtime import MultiAgentWorldRuntimeView  # noqa: E402
from python.rl.runtime.world_batch import RuntimeCompatibilityView  # noqa: E402
from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index  # noqa: E402


def _cooperative_cruise_scenario() -> dict:
    return {
        "scenario_name": "cooperative_cruise_vec_env_smoke",
        "meta": {"max_steps": 16},
        "environment": {
            "time_step": 0.05,
            "terrain_type": "flat",
            "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
            "zones": [
                {
                    "name": "Runway 09",
                    "x": 0.0,
                    "y": 0.0,
                    "width": 45.0,
                    "length": 3000.0,
                    "heading": 90.0,
                    "surface": "Concrete",
                }
            ],
        },
        "mission_command": {
            "command_code": 3,
            "target_heading": 90.0,
            "target_altitude": 1400.0,
            "target_speed": 210.0,
            "formation_id": 17,
            "form_offset_x": 180.0,
            "form_offset_y": -90.0,
            "form_offset_z": 30.0,
            "waypoint_mode": "flyby",
            "waypoints": [
                {"x": 15000.0, "y": 0.0, "z": 1400.0, "radius_m": 1000.0},
                {"x": 30000.0, "y": 3000.0, "z": 1400.0, "radius_m": 1000.0},
            ],
        },
        "entities": [
            {
                "name": "Lead",
                "type": "F-16C_Block50",
                "side": "Blue",
                "is_agent": True,
                "pos": [0.0, 0.0, 1400.0],
                "vel": [210.0, 0.0, 0.0],
                "heading": 90.0,
            },
            {
                "name": "Wing",
                "type": "F-16C_Block50",
                "side": "Blue",
                "is_agent": True,
                "pos": [-120.0, -180.0, 1400.0],
                "vel": [210.0, 0.0, 0.0],
                "heading": 90.0,
            },
        ],
        "cooperative_roster": {
            "team_id": 7001,
            "element_id": 7001,
            "policy_route": "shared_execution",
            "members": [
                {
                    "entity": "Lead",
                    "role_code": 21,
                    "formation_role_id": "ElementLead",
                    "relative_slot_code": 11,
                    "policy_route": "shared_execution",
                },
                {
                    "entity": "Wing",
                    "role_code": 22,
                    "formation_role_id": "Wingman",
                    "relative_slot_code": 12,
                    "reference_entity": "Lead",
                    "policy_route": "shared_execution",
                },
            ],
        },
    }


def _cooperative_interval_takeoff_scenario() -> dict:
    return {
        "scenario_name": "cooperative_interval_takeoff_vec_env_smoke",
        "meta": {"max_steps": 16},
        "imports": [{"file": "examples/config/prefabs/airbase_large_runway45.json"}],
        "environment": {
            "time_step": 0.05,
            "terrain_type": "flat",
            "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
        },
        "mission_command": {
            "command_code": 2,
            "target_heading": 90.0,
            "target_altitude": 220.0,
            "target_speed": 155.0,
            "takeoff_procedure_code": 2,
            "takeoff_clearance_code": 3,
            "takeoff_interval_s": 6.0,
            "runway_slot_code": 1,
            "formation_id": 31,
            "form_offset_x": 180.0,
            "form_offset_y": -90.0,
            "form_offset_z": 25.0,
        },
        "entities": [
            {
                "name": "Lead",
                "type": "F-16C_Block50",
                "side": "Blue",
                "is_agent": True,
                "pos": [-1400.0, 0.0, 2.1],
                "vel": [0.0, 0.0, 0.0],
                "heading": 90.0,
            },
            {
                "name": "Wing",
                "type": "F-16C_Block50",
                "side": "Blue",
                "is_agent": True,
                "pos": [-1460.0, 0.0, 2.1],
                "vel": [0.0, 0.0, 0.0],
                "heading": 90.0,
            },
        ],
        "cooperative_roster": {
            "team_id": 7101,
            "element_id": 7101,
            "policy_route": "shared_execution",
            "members": [
                {
                    "entity": "Lead",
                    "role_code": 21,
                    "formation_role_id": "ElementLead",
                    "relative_slot_code": 11,
                    "policy_route": "shared_execution",
                    "mission_command_overrides": {
                        "takeoff_procedure_code": 2,
                        "takeoff_clearance_code": 3,
                        "takeoff_interval_s": 6.0,
                        "runway_slot_code": 1,
                        "form_offset_x": 0.0,
                        "form_offset_y": 0.0,
                        "form_offset_z": 0.0,
                    },
                },
                {
                    "entity": "Wing",
                    "role_code": 22,
                    "formation_role_id": "Wingman",
                    "relative_slot_code": 12,
                    "reference_entity": "Lead",
                    "policy_route": "shared_execution",
                    "mission_command_overrides": {
                        "takeoff_procedure_code": 2,
                        "takeoff_clearance_code": 1,
                        "takeoff_interval_s": 6.0,
                        "runway_slot_code": 1,
                        "form_offset_x": 180.0,
                        "form_offset_y": -90.0,
                        "form_offset_z": 25.0,
                    },
                },
            ],
        },
    }


def _cooperative_takeoff_to_cruise_scenario() -> dict:
    return {
        "scenario_name": "cooperative_takeoff_to_cruise_vec_env_smoke",
        "meta": {"max_steps": 16},
        "imports": [{"file": "examples/config/prefabs/airbase_large_runway45.json"}],
        "environment": {
            "time_step": 0.05,
            "terrain_type": "flat",
            "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
            "randomization": {
                "world_yaw_range": [0.0, 0.0],
                "world_yaw_origin": [0.0, 0.0],
                "rotate_mission_heading_with_world": True,
            },
        },
        "mission_command": {
            "command_code": 3,
            "target_heading": 90.0,
            "target_altitude": 1400.0,
            "target_speed": 205.0,
            "takeoff_procedure_code": 2,
            "takeoff_clearance_code": 3,
            "takeoff_interval_s": 6.0,
            "runway_slot_code": 1,
            "formation_id": 31,
            "form_offset_x": 180.0,
            "form_offset_y": -90.0,
            "form_offset_z": 30.0,
            "waypoint_mode": "flyby",
            "waypoints": [
                {"x": 14000.0, "y": 0.0, "z": 1400.0, "radius_m": 1000.0},
                {"x": 26000.0, "y": 3500.0, "z": 1400.0, "radius_m": 1000.0},
            ],
        },
        "entities": [
            {
                "name": "Lead",
                "type": "F-16C_Block50",
                "side": "Blue",
                "is_agent": True,
                "pos": [-1400.0, 0.0, 2.1],
                "vel": [0.0, 0.0, 0.0],
                "heading": 90.0,
            },
            {
                "name": "Wing",
                "type": "F-16C_Block50",
                "side": "Blue",
                "is_agent": True,
                "pos": [-1460.0, 0.0, 2.1],
                "vel": [0.0, 0.0, 0.0],
                "heading": 90.0,
            },
        ],
        "cooperative_roster": {
            "team_id": 7201,
            "element_id": 7201,
            "policy_route": "shared_execution",
            "members": [
                {
                    "entity": "Lead",
                    "role_code": 21,
                    "formation_role_id": "ElementLead",
                    "relative_slot_code": 11,
                    "policy_route": "shared_execution",
                    "mission_command_overrides": {
                        "takeoff_procedure_code": 2,
                        "takeoff_clearance_code": 3,
                        "takeoff_interval_s": 6.0,
                        "runway_slot_code": 1,
                        "form_offset_x": 0.0,
                        "form_offset_y": 0.0,
                        "form_offset_z": 0.0,
                    },
                },
                {
                    "entity": "Wing",
                    "role_code": 22,
                    "formation_role_id": "Wingman",
                    "relative_slot_code": 12,
                    "reference_entity": "Lead",
                    "policy_route": "shared_execution",
                    "mission_command_overrides": {
                        "takeoff_procedure_code": 2,
                        "takeoff_clearance_code": 1,
                        "takeoff_interval_s": 6.0,
                        "runway_slot_code": 1,
                        "form_offset_x": 180.0,
                        "form_offset_y": -90.0,
                        "form_offset_z": 30.0,
                    },
                },
            ],
        },
    }


class CooperativeWorldBatchVecEnvTests(unittest.TestCase):
    def test_multi_agent_runtime_view_task_order_export_uses_maintained_contracts_only(self) -> None:
        class _Loader:
            active_roster = []

        class _TaskingPacket:
            def __init__(self, refs, task_order_contracts):
                self.refs = list(refs)
                self.task_order_contracts = list(task_order_contracts)

        class _Runtime:
            def __init__(self) -> None:
                self.requests: list[object] = []

            def export_tasking_packet(self, request):
                self.requests.append(request)
                contract = cooperative_vec_env_module.ef_py.TaskOrderMaintainedBatchContract()
                contract.shared_core.task_id = 451
                return _TaskingPacket(request.refs, [contract])

        runtime = _Runtime()
        view = MultiAgentWorldRuntimeView(
            runtime=runtime,
            loader=_Loader(),
            world_index=0,
            action_space=None,
            action_mode="full",
            mission_obs_mode="basic",
            include_proprio=False,
        )
        ref = cooperative_vec_env_module.ef_py.WorldEntityRef()
        ref.world_index = 0
        ref.entity_id = 91
        view.refs = lambda: [ref]  # type: ignore[method-assign]

        packet = view.export_tasking_packet(
            include_mission_commands=False,
            include_task_order_contracts=True,
        )

        self.assertEqual(len(runtime.requests), 1)
        request = runtime.requests[0]
        self.assertTrue(bool(request.include_task_order_contracts))
        self.assertFalse(hasattr(request, "include_task_orders"))
        self.assertEqual(len(packet.task_order_contracts), 1)
        self.assertEqual(int(packet.task_order_contracts[0].shared_core.task_id), 451)
        self.assertFalse(hasattr(packet, "task_orders"))

    def test_multi_agent_runtime_view_default_observation_export_does_not_request_task_orders(self) -> None:
        class _Loader:
            active_roster = []

        class _Runtime:
            def __init__(self) -> None:
                self.requests: list[object] = []

            def export_observation_packet(self, request):
                self.requests.append(request)
                return cooperative_vec_env_module.ef_py.ObservationBatchPacket()

        runtime = _Runtime()
        view = MultiAgentWorldRuntimeView(
            runtime=runtime,
            loader=_Loader(),
            world_index=0,
            action_space=None,
            action_mode="full",
            mission_obs_mode="basic",
            include_proprio=False,
        )

        view.export_packet()

        self.assertEqual(len(runtime.requests), 1)
        request = runtime.requests[0]
        self.assertFalse(hasattr(request, "include_task_order_contracts"))
        self.assertFalse(hasattr(request, "include_mission_commands"))
        self.assertFalse(hasattr(request, "include_leader_intents"))
        self.assertFalse(hasattr(request, "include_pilot_reports"))
        self.assertFalse(hasattr(request, "include_task_orders"))

    def test_cooperative_world_batch_vec_env_batch_runtime_requires_explicit_compatibility_opt_in(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                with self.assertRaisesRegex(RuntimeError, "vec_env\\.batch_runtime"):
                    _ = vec_env.batch_runtime
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_exposes_batch_runtime_as_compatibility_view(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
                runtime_compatibility_enabled=True,
            )
            try:
                self.assertIsNot(vec_env.batch_runtime, vec_env._runtime_adapter)
                self.assertEqual(int(vec_env.batch_runtime.world_count()), int(vec_env.runtime_facade.world_count()))
                self.assertTrue(isinstance(vec_env.batch_runtime, RuntimeCompatibilityView))
                self.assertTrue(hasattr(vec_env.batch_runtime, "export_execution_episode_states_batch"))
                self.assertTrue(hasattr(vec_env.batch_runtime, "execution_episode_controller_ready"))
                self.assertFalse(hasattr(vec_env.batch_runtime, "load_database"))
                self.assertFalse(hasattr(vec_env.batch_runtime, "set_worker_threads"))
                self.assertFalse(hasattr(vec_env.batch_runtime, "make_scenario_loader"))
                with self.assertRaises(AttributeError):
                    _ = vec_env.batch_runtime.load_database
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_smoke(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                vec_env.seed(7)
                obs = vec_env.reset()
                self.assertEqual(obs["instruments"].shape[0], 2)
                self.assertEqual(obs["mission"].shape, (2, mission_observation_dim("nav_v2_formation_v1")))
                self.assertEqual(obs["proprio"].shape, (2, 17))

                actions = np.zeros((2, 17), dtype=np.float32)
                obs, rewards, dones, infos = vec_env.step(actions)
                self.assertEqual(rewards.shape, (2,))
                self.assertEqual(dones.shape, (2,))
                self.assertEqual(len(infos), 2)
                self.assertTrue(np.all(np.isfinite(rewards)))
                self.assertEqual(int(vec_env.slots_per_world), 2)
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_role_mode_exposes_role_semantics(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_role_v1",
            )
            try:
                vec_env.seed(7)
                obs = vec_env.reset()
                self.assertEqual(obs["mission"].shape, (2, mission_observation_dim("nav_v2_formation_role_v1")))
                self.assertAlmostEqual(
                    float(obs["mission"][0][mission_observation_field_index("nav_v2_formation_role_v1", "self_role_code")]),
                    21.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][0][mission_observation_field_index("nav_v2_formation_role_v1", "relative_slot_code")]),
                    11.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(
                        obs["mission"][0][
                            mission_observation_field_index("nav_v2_formation_role_v1", "reference_relative_slot_code")
                        ]
                    ),
                    0.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_role_v1", "self_role_code")]),
                    22.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_role_v1", "relative_slot_code")]),
                    12.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(
                        obs["mission"][1][
                            mission_observation_field_index("nav_v2_formation_role_v1", "reference_relative_slot_code")
                        ]
                    ),
                    11.0,
                    places=6,
                )
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_takeoff_mode_exposes_interval_clearance_semantics(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_takeoff_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_interval_takeoff_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_cooperative_takeoff_v1",
            )
            try:
                vec_env.seed(7)
                obs = vec_env.reset()
                self.assertEqual(obs["mission"].shape, (2, mission_observation_dim("nav_v2_cooperative_takeoff_v1")))
                self.assertAlmostEqual(
                    float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_procedure_code")]),
                    2.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_clearance_code")]),
                    3.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_interval_s")]),
                    6.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "runway_slot_code")]),
                    1.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_procedure_code")]),
                    2.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_clearance_code")]),
                    1.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_interval_s")]),
                    6.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "runway_slot_code")]),
                    1.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "self_role_code")]),
                    22.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(
                        obs["mission"][1][
                            mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "reference_relative_slot_code")
                        ]
                    ),
                    11.0,
                    places=6,
                )
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_interval_director_promotes_wing_clearance_after_gate_open(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_takeoff_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_interval_takeoff_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_cooperative_takeoff_v1",
            )
            try:
                vec_env.seed(7)
                vec_env.reset()
                world = vec_env._worlds[0]
                lead = vec_env._slots[0]
                wing = vec_env._slots[1]
                self.assertIsNotNone(lead)
                self.assertIsNotNone(wing)
                assert lead is not None
                assert wing is not None

                self.assertEqual(int(wing.loader.mission_cmd.get("takeoff_clearance_code", 0)), 1)
                lead.last_inst.ground_speed = 40.0
                lead.last_inst.alt_radar = 0.0
                lead.steps = 200
                wing.steps = 200
                lead.loader._coop_takeoff_roll_start_time_s = 0.0

                world.director.update(world, vec_env._world_slot_states(world), force=True)

                self.assertEqual(int(wing.loader.mission_cmd.get("takeoff_clearance_code", 0)), 3)
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_interval_takeoff_starts_both_aircraft_on_runway_geometry(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_takeoff_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_interval_takeoff_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_cooperative_takeoff_v1",
            )
            try:
                vec_env.seed(7)
                vec_env.reset()
                for slot_state in vec_env._slots[:2]:
                    self.assertIsNotNone(slot_state)
                    assert slot_state is not None
                    truth = slot_state.last_truth
                    loader = slot_state.loader
                    valid_rf, along_m, cross_m, rw_len, rw_wid = loader.get_runway_local_frame(
                        float(truth.x),
                        float(truth.y),
                    )
                    self.assertTrue(bool(valid_rf))
                    self.assertLessEqual(abs(float(cross_m)), 0.5 * float(rw_wid) + 1.0)
                    self.assertLessEqual(abs(float(along_m)), 0.5 * float(rw_len))
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_takeoff_to_cruise_bridge_exposes_route_and_takeoff_semantics(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_takeoff_to_cruise_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_takeoff_to_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_cooperative_takeoff_v1",
            )
            try:
                vec_env.seed(7)
                obs = vec_env.reset()
                self.assertEqual(obs["mission"].shape, (2, mission_observation_dim("nav_v2_cooperative_takeoff_v1")))
                self.assertAlmostEqual(
                    float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "command_code")]),
                    3.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_clearance_code")]),
                    3.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_clearance_code")]),
                    1.0,
                    places=6,
                )
                self.assertGreater(
                    float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "dist_m")]),
                    1000.0,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "form_offset_x_m")]),
                    180.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "form_offset_y_m")]),
                    -90.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "self_role_code")]),
                    22.0,
                    places=6,
                )

                actions = np.zeros((2, 17), dtype=np.float32)
                obs, rewards, dones, infos = vec_env.step(actions)
                self.assertEqual(obs["mission"].shape, (2, 25))
                self.assertEqual(rewards.shape, (2,))
                self.assertEqual(dones.shape, (2,))
                self.assertEqual(len(infos), 2)
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_reuses_cached_step_evaluation(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            cached_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            uncached_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                cached_env.seed(7)
                uncached_env.seed(7)
                cached_env.reset()
                uncached_env.reset()

                cached_slot = cached_env._slots[0]
                uncached_slot = uncached_env._slots[0]
                self.assertIsNotNone(cached_slot)
                self.assertIsNotNone(uncached_slot)
                assert cached_slot is not None
                assert uncached_slot is not None

                cached_loader = cached_slot.loader
                uncached_loader = uncached_slot.loader

                self.assertIsNotNone(cached_loader._runtime_eval_cache.get("step_evaluation"))

                with unittest.mock.patch.object(
                    cached_loader,
                    "_build_step_evaluation_inputs",
                    wraps=cached_loader._build_step_evaluation_inputs,
                ) as mocked_cached_build:
                    cached_reward, cached_terminated, cached_truncated, cached_status = cached_loader.compute_full_step(
                        cached_slot.last_obs,
                        cached_loader.sim,
                        cached_slot.steps,
                        cached_slot.max_steps,
                        truth=cached_slot.last_truth,
                        inst_state=cached_slot.last_inst,
                    )
                    self.assertEqual(mocked_cached_build.call_count, 0)

                uncached_loader.reset_runtime_eval_cache()
                with unittest.mock.patch.object(
                    uncached_loader,
                    "_build_step_evaluation_inputs",
                    wraps=uncached_loader._build_step_evaluation_inputs,
                ) as mocked_uncached_build:
                    uncached_reward, uncached_terminated, uncached_truncated, uncached_status = (
                        uncached_loader.compute_full_step(
                            uncached_slot.last_obs,
                            uncached_loader.sim,
                            uncached_slot.steps,
                            uncached_slot.max_steps,
                            truth=uncached_slot.last_truth,
                            inst_state=uncached_slot.last_inst,
                        )
                    )
                    self.assertGreater(mocked_uncached_build.call_count, 0)

                self.assertAlmostEqual(float(cached_reward), float(uncached_reward), places=6)
                self.assertEqual(bool(cached_terminated), bool(uncached_terminated))
                self.assertEqual(bool(cached_truncated), bool(uncached_truncated))
                self.assertTrue(np.allclose(np.asarray(cached_status, dtype=np.float32), np.asarray(uncached_status, dtype=np.float32), atol=1.0e-6))
            finally:
                cached_env.close()
                uncached_env.close()

    def test_cooperative_world_batch_vec_env_applies_world_director_offsets(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                vec_env.set_leader_overrides(
                    {
                        "leader_form_offset_x": 0.0,
                        "leader_form_offset_y": 0.0,
                        "leader_form_offset_z": 0.0,
                        "wingman_form_offset_x": 220.0,
                        "wingman_form_offset_y": -110.0,
                        "wingman_form_offset_z": 40.0,
                    }
                )
                obs = vec_env.reset()
                self.assertEqual(obs["mission"].shape, (2, mission_observation_dim("nav_v2_formation_v1")))
                self.assertAlmostEqual(
                    float(obs["mission"][0][mission_observation_field_index("nav_v2_formation_v1", "form_offset_x_m")]),
                    0.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_v1", "form_offset_x_m")]),
                    220.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_v1", "form_offset_y_m")]),
                    -110.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_v1", "form_offset_z_m")]),
                    40.0,
                    places=6,
                )

                actions = np.zeros((2, 17), dtype=np.float32)
                obs, rewards, dones, infos = vec_env.step(actions)
                self.assertEqual(rewards.shape, (2,))
                self.assertTrue(np.all(np.isfinite(rewards)))
                self.assertAlmostEqual(
                    float(obs["mission"][0][mission_observation_field_index("nav_v2_formation_v1", "form_offset_x_m")]),
                    0.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_v1", "form_offset_x_m")]),
                    220.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_v1", "form_offset_y_m")]),
                    -110.0,
                    places=6,
                )
                self.assertAlmostEqual(
                    float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_v1", "form_offset_z_m")]),
                    40.0,
                    places=6,
                )
                self.assertEqual(len(infos), 2)
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_runs_short_sb3_rollout(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        if PPO is None:
            self.skipTest("stable_baselines3 is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                model = PPO(
                    "MultiInputPolicy",
                    vec_env,
                    n_steps=2,
                    batch_size=2,
                    n_epochs=1,
                    learning_rate=3.0e-4,
                    gamma=0.99,
                    gae_lambda=0.95,
                    ent_coef=0.0,
                    vf_coef=0.5,
                    max_grad_norm=0.5,
                    device="cpu",
                    verbose=0,
                )
                model.learn(total_timesteps=4)
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_reports_observation_timing(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
                collect_step_timing=True,
                batch_observation_backend="compiled",
            )
            try:
                vec_env.seed(7)
                _obs = vec_env.reset()
                actions = np.zeros((2, 17), dtype=np.float32)
                _obs, _rewards, _dones, infos = vec_env.step(actions)
                timing = infos[0].get("timing", {})
                self.assertIn("obs_execution_observation_batch_ms", timing)
                self.assertIn("obs_mission_input_build_ms", timing)
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_compiled_observation_arrays_are_float32(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
                batch_observation_backend="compiled",
            )
            try:
                obs = vec_env.reset()
                for key in ("instruments", "contacts", "rwr", "mission", "proprio"):
                    self.assertEqual(obs[key].dtype, np.float32)
                obs, _rewards, _dones, _infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
                for key in ("instruments", "contacts", "rwr", "mission", "proprio"):
                    self.assertEqual(obs[key].dtype, np.float32)
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_flattens_step_state_reads(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                read_calls: list[int] = []
                original_read = vec_env._read_slot_state_batch

                def _tracked_read(slot_indices):
                    read_calls.append(len(list(slot_indices)))
                    return original_read(slot_indices)

                vec_env._read_slot_state_batch = _tracked_read  # type: ignore[method-assign]
                vec_env.seed(7)
                vec_env.reset()
                read_calls.clear()
                actions = np.zeros((vec_env.num_envs, 17), dtype=np.float32)
                vec_env.step(actions)
                self.assertEqual(read_calls, [vec_env.num_envs])
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_waits_for_all_slots_before_world_success(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                vec_env.seed(7)
                vec_env.reset()
                slot0 = vec_env._slots[0]
                slot1 = vec_env._slots[1]
                self.assertIsNotNone(slot0)
                self.assertIsNotNone(slot1)
                assert slot0 is not None
                assert slot1 is not None

                call_counts = {0: 0, 1: 0}
                orig0 = slot0.loader.compute_full_step
                orig1 = slot1.loader.compute_full_step

                def _patched_slot0(*args, **kwargs):
                    call_counts[0] += 1
                    reward, terminated, truncated, mission_status = orig0(*args, **kwargs)
                    arr = np.asarray(mission_status, dtype=np.float32).copy()
                    if call_counts[0] == 1:
                        arr[3] = 1.0
                        terminated = True
                    return reward, terminated, truncated, arr

                def _patched_slot1(*args, **kwargs):
                    call_counts[1] += 1
                    reward, terminated, truncated, mission_status = orig1(*args, **kwargs)
                    arr = np.asarray(mission_status, dtype=np.float32).copy()
                    if call_counts[1] == 1:
                        arr[3] = 0.0
                        terminated = False
                        truncated = False
                    else:
                        arr[3] = 1.0
                        terminated = True
                    return reward, terminated, truncated, arr

                with unittest.mock.patch.object(slot0.loader, "compute_full_step", side_effect=_patched_slot0), unittest.mock.patch.object(
                    slot1.loader,
                    "compute_full_step",
                    side_effect=_patched_slot1,
                ):
                    actions = np.zeros((2, 17), dtype=np.float32)
                    _obs, _rewards, dones, infos = vec_env.step(actions)
                    self.assertFalse(bool(np.any(dones)))
                    self.assertAlmostEqual(float(infos[0]["coop_slot_success_latched"]), 1.0, places=6)
                    self.assertAlmostEqual(float(infos[0]["world_done"]), 0.0, places=6)
                    self.assertAlmostEqual(float(infos[0]["world_success"]), 0.0, places=6)
                    self.assertAlmostEqual(float(infos[1]["coop_slot_success_latched"]), 0.0, places=6)

                    _obs, _rewards, dones, infos = vec_env.step(actions)
                    self.assertTrue(bool(np.all(dones)))
                    self.assertAlmostEqual(float(infos[0]["world_done"]), 1.0, places=6)
                    self.assertAlmostEqual(float(infos[0]["world_success"]), 1.0, places=6)
                    self.assertAlmostEqual(float(infos[1]["world_success"]), 1.0, places=6)
                    self.assertFalse(bool(infos[0]["shared_world_reset"]))
                    self.assertFalse(bool(infos[1]["shared_world_reset"]))
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_skips_redundant_director_updates(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                vec_env.seed(7)
                vec_env.reset()
                world = vec_env._worlds[0]
                self.assertFalse(bool(world.director_dirty))
                world.director.update(world, vec_env._world_slot_states(world))
                self.assertFalse(bool(world.director_dirty))
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_step_forces_director_recompute(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                vec_env.seed(7)
                vec_env.reset()
                world = vec_env._worlds[0]
                self.assertFalse(bool(world.director_dirty))
                actions = np.zeros((2, 17), dtype=np.float32)
                with unittest.mock.patch.object(
                    world.director,
                    "update",
                    wraps=world.director.update,
                ) as mocked_update:
                    vec_env.step(actions)
                    self.assertGreaterEqual(mocked_update.call_count, 1)
                    self.assertTrue(any(bool(call.kwargs.get("force", False)) for call in mocked_update.call_args_list))
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_director_reuses_stable_mission_command_mapping(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                vec_env.seed(7)
                vec_env.reset()
                world = vec_env._worlds[0]
                slot0 = vec_env._slots[0]
                slot1 = vec_env._slots[1]
                self.assertIsNotNone(slot0)
                self.assertIsNotNone(slot1)
                assert slot0 is not None
                assert slot1 is not None

                mission_cmd_ids_before = [id(slot0.loader.mission_cmd), id(slot1.loader.mission_cmd)]
                scenario_cmd_ids_before = [
                    id(slot0.loader.scenario_data["mission_command"]),
                    id(slot1.loader.scenario_data["mission_command"]),
                ]

                world.director.update(world, vec_env._world_slot_states(world), force=True)

                self.assertEqual(id(slot0.loader.mission_cmd), mission_cmd_ids_before[0])
                self.assertEqual(id(slot1.loader.mission_cmd), mission_cmd_ids_before[1])
                self.assertEqual(id(slot0.loader.scenario_data["mission_command"]), scenario_cmd_ids_before[0])
                self.assertEqual(id(slot1.loader.scenario_data["mission_command"]), scenario_cmd_ids_before[1])
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_director_still_advances_takeoff_clearance_progression(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_takeoff_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_interval_takeoff_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_cooperative_takeoff_v1",
            )
            try:
                vec_env.seed(7)
                vec_env.reset()
                world = vec_env._worlds[0]
                lead = vec_env._slots[0]
                self.assertIsNotNone(lead)
                assert lead is not None

                lead.last_inst.ground_speed = 40.0
                lead.last_inst.alt_radar = 6.0
                lead.steps = 200
                lead.loader.steps = 200

                world.director.update(world, vec_env._world_slot_states(world), force=True)

                self.assertEqual(int(lead.loader.mission_cmd.get("takeoff_clearance_code", 0)), 5)
                self.assertEqual(int(lead.loader.scenario_data["mission_command"].get("takeoff_clearance_code", 0)), 5)
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_step_syncs_dirty_world_once_before_steady_state(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                vec_env.seed(7)
                vec_env.reset()
                world = vec_env._worlds[0]
                world.command_chain_dirty = True
                sync_calls: list[list[int] | None] = []
                original_sync = vec_env._sync_command_chain_batch

                def _tracked_sync(world_indices=None):
                    sync_calls.append(None if world_indices is None else [int(i) for i in world_indices])
                    return original_sync(world_indices)

                vec_env._sync_command_chain_batch = _tracked_sync  # type: ignore[method-assign]
                actions = np.zeros((vec_env.num_envs, 17), dtype=np.float32)
                vec_env.step(actions)
                self.assertEqual(sync_calls[0], [0])
                self.assertEqual(sync_calls[-1], None)
                self.assertFalse(bool(world.command_chain_dirty))
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_step_skips_redundant_presync_after_steady_state(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                vec_env.seed(7)
                vec_env.reset()
                world = vec_env._worlds[0]
                world.command_chain_dirty = False
                sync_calls: list[list[int] | None] = []
                original_sync = vec_env._sync_command_chain_batch

                def _tracked_sync(world_indices=None):
                    sync_calls.append(None if world_indices is None else [int(i) for i in world_indices])
                    return original_sync(world_indices)

                vec_env._sync_command_chain_batch = _tracked_sync  # type: ignore[method-assign]
                actions = np.zeros((vec_env.num_envs, 17), dtype=np.float32)
                vec_env.step(actions)
                self.assertEqual(sync_calls, [None])
                self.assertFalse(bool(world.command_chain_dirty))
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_skips_stable_command_chain_exports(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                vec_env.seed(7)
                vec_env.reset()
                world = vec_env._worlds[0]

                mission_calls: list[int] = []
                task_calls: list[int] = []
                intent_calls: list[int] = []
                report_calls: list[int] = []

                original_set_mission = vec_env._runtime_adapter.set_mission_commands_batch
                original_set_task = vec_env._runtime_adapter.set_task_orders_maintained_batch
                original_set_intent = vec_env._runtime_adapter.set_leader_intents_batch
                original_set_report = vec_env._runtime_adapter.set_pilot_reports_batch
                original_project_task = cooperative_vec_env_module.project_world_task_order_maintained_assignment
                original_project_intent = cooperative_vec_env_module.project_world_leader_intent_assignment_transport
                original_project_report = cooperative_vec_env_module.project_world_pilot_report_assignment_transport
                projection_calls: list[tuple[str, int, int]] = []

                def _track_mission(assignments):
                    mission_calls.append(len(list(assignments)))
                    return original_set_mission(assignments)

                def _track_task(assignments):
                    materialized = list(assignments)
                    self.assertTrue(all(hasattr(assignment, "task_order") for assignment in materialized))
                    task_calls.append(len(materialized))
                    return original_set_task(materialized)

                def _track_intent(assignments):
                    intent_calls.append(len(list(assignments)))
                    return original_set_intent(assignments)

                def _track_report(assignments):
                    report_calls.append(len(list(assignments)))
                    return original_set_report(assignments)

                def _track_project_intent(assignment, *, world_index, entity_id, compatibility_intent_shell):
                    projection_calls.append(("intent", int(world_index), int(entity_id)))
                    return original_project_intent(
                        assignment,
                        world_index=world_index,
                        entity_id=entity_id,
                        compatibility_intent_shell=compatibility_intent_shell,
                    )

                def _track_project_report(assignment, *, world_index, entity_id, compatibility_report_shell):
                    projection_calls.append(("report", int(world_index), int(entity_id)))
                    return original_project_report(
                        assignment,
                        world_index=world_index,
                        entity_id=entity_id,
                        compatibility_report_shell=compatibility_report_shell,
                    )

                def _track_project_task(assignment, *, world_index, entity_id, compatibility_task_order_shell):
                    projection_calls.append(("task", int(world_index), int(entity_id)))
                    return original_project_task(
                        assignment,
                        world_index=world_index,
                        entity_id=entity_id,
                        compatibility_task_order_shell=compatibility_task_order_shell,
                    )

                vec_env._runtime_adapter.set_mission_commands_batch = _track_mission  # type: ignore[method-assign]
                vec_env._runtime_adapter.set_task_orders_maintained_batch = _track_task  # type: ignore[method-assign]
                vec_env._runtime_adapter.set_leader_intents_batch = _track_intent  # type: ignore[method-assign]
                vec_env._runtime_adapter.set_pilot_reports_batch = _track_report  # type: ignore[method-assign]
                cooperative_vec_env_module.project_world_task_order_maintained_assignment = _track_project_task  # type: ignore[assignment]
                cooperative_vec_env_module.project_world_leader_intent_assignment_transport = _track_project_intent  # type: ignore[assignment]
                cooperative_vec_env_module.project_world_pilot_report_assignment_transport = _track_project_report  # type: ignore[assignment]

                try:
                    world.command_chain_dirty = True
                    vec_env._sync_command_chain_batch([0])
                    first_counts = (
                        sum(mission_calls),
                        sum(task_calls),
                        sum(intent_calls),
                        sum(report_calls),
                    )
                    self.assertGreater(first_counts[0], 0)
                    self.assertGreater(first_counts[1], 0)
                    self.assertGreater(first_counts[2], 0)
                    self.assertGreater(first_counts[3], 0)
                    self.assertFalse(hasattr(vec_env._runtime_adapter, "set_task_orders_batch"))
                    self.assertTrue(any(kind == "task" for kind, _world_index, _entity_id in projection_calls))
                    self.assertTrue(any(kind == "intent" for kind, _world_index, _entity_id in projection_calls))
                    self.assertTrue(any(kind == "report" for kind, _world_index, _entity_id in projection_calls))

                    world.command_chain_dirty = True
                    vec_env._sync_command_chain_batch([0])
                    second_counts = (
                        sum(mission_calls),
                        sum(task_calls),
                        sum(intent_calls),
                        sum(report_calls),
                    )
                    self.assertEqual(first_counts, second_counts)
                    self.assertFalse(hasattr(vec_env._runtime_adapter, "set_task_orders_batch"))
                finally:
                    cooperative_vec_env_module.project_world_task_order_maintained_assignment = original_project_task  # type: ignore[assignment]
                    cooperative_vec_env_module.project_world_leader_intent_assignment_transport = original_project_intent  # type: ignore[assignment]
                    cooperative_vec_env_module.project_world_pilot_report_assignment_transport = original_project_report  # type: ignore[assignment]
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_reset_rearms_command_chain_exports(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                vec_env.seed(7)
                world = vec_env._worlds[0]
                vec_env.reset()
                mission_calls: list[int] = []
                original_set_mission = vec_env._runtime_adapter.set_mission_commands_batch

                def _track_mission(assignments):
                    materialized = list(assignments)
                    mission_calls.append(len(materialized))
                    return original_set_mission(materialized)

                vec_env._runtime_adapter.set_mission_commands_batch = _track_mission  # type: ignore[method-assign]

                world.command_chain_dirty = True
                vec_env._sync_command_chain_batch([0])
                self.assertGreater(sum(mission_calls), 0)
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_isolates_slot_route_randomization(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                vec_env.set_randomization_overrides(
                    {
                        "world_yaw_range": [197.5728614138369, 197.5728614138369],
                        "rotate_mission_heading_with_world": True,
                    }
                )
                vec_env.seed(0)
                vec_env.reset()

                slot0 = vec_env._slots[0]
                slot1 = vec_env._slots[1]
                self.assertIsNotNone(slot0)
                self.assertIsNotNone(slot1)
                assert slot0 is not None
                assert slot1 is not None

                loader0 = slot0.loader
                loader1 = slot1.loader
                wp0_slot0 = dict(loader0.waypoints[0])
                wp0_slot1 = dict(loader1.waypoints[0])
                cached_waypoints_slot0 = loader0.mission_cmd.get("_normalized_waypoints", None)
                cached_waypoints_slot1 = loader1.mission_cmd.get("_normalized_waypoints", None)
                self.assertTrue(bool(loader0.mission_cmd.get("_runtime_waypoint_cache_valid", False)))
                self.assertTrue(bool(loader1.mission_cmd.get("_runtime_waypoint_cache_valid", False)))
                self.assertIsInstance(cached_waypoints_slot0, list)
                self.assertIsInstance(cached_waypoints_slot1, list)
                assert isinstance(cached_waypoints_slot0, list)
                assert isinstance(cached_waypoints_slot1, list)
                cmd_wp0_slot0 = dict(cached_waypoints_slot0[0])
                cmd_wp0_slot1 = dict(cached_waypoints_slot1[0])

                for key in ("x", "y", "z", "radius_m"):
                    self.assertAlmostEqual(float(wp0_slot0[key]), float(cmd_wp0_slot0[key]), places=6)
                    self.assertAlmostEqual(float(wp0_slot1[key]), float(cmd_wp0_slot1[key]), places=6)
                self.assertIsNot(loader0.waypoints, cached_waypoints_slot0)
                self.assertIsNot(loader1.waypoints, cached_waypoints_slot1)
                self.assertEqual(wp0_slot0, wp0_slot1)
            finally:
                vec_env.close()

    def test_cooperative_world_batch_vec_env_rotated_route_starts_near_ownship_heading(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario = _cooperative_cruise_scenario()
            scenario["mission_command"]["randomization"] = {
                "route_generator": {
                    "enabled": True,
                    "waypoint_count_range": [3, 3],
                    "first_leg_heading_delta_deg_range": [-35.0, 35.0],
                    "leg_length_m_range": [15000.0, 15000.0],
                    "route_budget_fraction": 0.8,
                    "turn_angle_deg_range": [0.0, 0.0],
                    "altitude_m_range": [1400.0, 1400.0],
                    "altitude_step_m_range": [0.0, 0.0],
                    "speed_mps_range": [210.0, 210.0],
                    "waypoint_radius_m_range": [1000.0, 1000.0],
                }
            }
            scenario_path = f"{tmpdir}/cooperative_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario, f, ensure_ascii=True)

            vec_env = CooperativeWorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="full",
                mission_obs_mode="nav_v2_formation_v1",
            )
            try:
                vec_env.set_randomization_overrides(
                    {
                        "world_yaw_range": [197.5728614138369, 197.5728614138369],
                        "rotate_mission_heading_with_world": True,
                    }
                )
                vec_env.seed(0)
                vec_env.reset()

                slot0 = vec_env._slots[0]
                self.assertIsNotNone(slot0)
                assert slot0 is not None
                truth = slot0.last_truth
                loader = slot0.loader
                wp0 = loader.waypoints[0]
                dx = float(wp0["x"]) - float(getattr(truth, "x", 0.0))
                dy = float(wp0["y"]) - float(getattr(truth, "y", 0.0))
                bearing = math.degrees(math.atan2(dx, dy)) % 360.0
                heading = float(getattr(truth, "heading", 0.0)) % 360.0
                delta = ((bearing - heading + 180.0) % 360.0) - 180.0
                self.assertLessEqual(abs(delta), 40.0)
            finally:
                vec_env.close()

    def test_cooperative_takeoff_to_cruise_repo_scenario_rotated_route_starts_near_ownship_heading(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")

        scenario_path = resolve_repo_path(
            "scenarios",
            "combined",
            "cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json",
        )
        vec_env = CooperativeWorldBatchVecEnv(
            scenario_path=scenario_path,
            n_envs=1,
            include_visual=False,
            include_proprio=True,
            action_mode="full",
            mission_obs_mode="nav_v2_cooperative_takeoff_v1",
        )
        try:
            vec_env.set_randomization_overrides(
                {
                    "world_yaw_range": [197.5728614138369, 197.5728614138369],
                    "rotate_mission_heading_with_world": True,
                }
            )
            vec_env.seed(0)
            vec_env.reset()

            for slot in vec_env._slots:
                self.assertIsNotNone(slot)
                assert slot is not None
                truth = slot.last_truth
                loader = slot.loader
                self.assertTrue(bool(loader.waypoints))
                wp0 = loader.waypoints[0]
                dx = float(wp0["x"]) - float(getattr(truth, "x", 0.0))
                dy = float(wp0["y"]) - float(getattr(truth, "y", 0.0))
                bearing = math.degrees(math.atan2(dx, dy)) % 360.0
                heading = float(getattr(truth, "heading", 0.0)) % 360.0
                delta = ((bearing - heading + 180.0) % 360.0) - 180.0
                self.assertLessEqual(abs(delta), 10.0)
        finally:
            vec_env.close()

    def test_cooperative_takeoff_to_cruise_landing_repo_scenario_exposes_landing_transition_and_steps(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")

        scenario_path = resolve_repo_path(
            "scenarios",
            "combined",
            "cooperative_takeoff_to_cruise_landing_continuous_train_v1.json",
        )
        vec_env = CooperativeWorldBatchVecEnv(
            scenario_path=scenario_path,
            n_envs=1,
            include_visual=False,
            include_proprio=True,
            action_mode="full",
            mission_obs_mode="nav_v2_cooperative_takeoff_v1",
        )
        try:
            vec_env.set_randomization_overrides(
                {
                    "world_yaw_range": [0.0, 0.0],
                    "rotate_mission_heading_with_world": True,
                }
            )
            vec_env.seed(0)
            obs = vec_env.reset()

            self.assertEqual(int(vec_env.slots_per_world), 2)
            self.assertEqual(obs["mission"].shape, (2, mission_observation_dim("nav_v2_cooperative_takeoff_v1")))
            self.assertAlmostEqual(
                float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "command_code")]),
                3.0,
                places=6,
            )
            self.assertAlmostEqual(
                float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "command_code")]),
                3.0,
                places=6,
            )

            for slot in vec_env._slots:
                self.assertIsNotNone(slot)
                assert slot is not None
                loader = slot.loader
                self.assertTrue(bool(loader.waypoints))
                self.assertIsInstance(loader.post_waypoint_transition, dict)
                self.assertEqual(int(loader.post_waypoint_transition.get("command_code", 0)), 4)
                self.assertEqual(str(loader.post_waypoint_transition.get("phase_name", "")), "landing_ils")

            actions = np.zeros((2, 17), dtype=np.float32)
            obs, rewards, dones, infos = vec_env.step(actions)
            self.assertEqual(obs["mission"].shape, (2, 25))
            self.assertEqual(rewards.shape, (2,))
            self.assertEqual(dones.shape, (2,))
            self.assertEqual(len(infos), 2)
            self.assertTrue(np.all(np.isfinite(rewards)))
        finally:
            vec_env.close()

    def test_cooperative_takeoff_to_cruise_landing_repo_scenario_rotated_route_starts_near_ownship_heading(self) -> None:
        if CooperativeWorldBatchVecEnv is None:
            self.skipTest("gymnasium is not available in the active interpreter")

        scenario_path = resolve_repo_path(
            "scenarios",
            "combined",
            "cooperative_takeoff_to_cruise_landing_continuous_train_v1.json",
        )
        vec_env = CooperativeWorldBatchVecEnv(
            scenario_path=scenario_path,
            n_envs=1,
            include_visual=False,
            include_proprio=True,
            action_mode="full",
            mission_obs_mode="nav_v2_cooperative_takeoff_v1",
        )
        try:
            vec_env.set_randomization_overrides(
                {
                    "world_yaw_range": [197.5728614138369, 197.5728614138369],
                    "rotate_mission_heading_with_world": True,
                }
            )
            vec_env.seed(0)
            vec_env.reset()

            for slot in vec_env._slots:
                self.assertIsNotNone(slot)
                assert slot is not None
                truth = slot.last_truth
                loader = slot.loader
                self.assertTrue(bool(loader.waypoints))
                wp0 = loader.waypoints[0]
                dx = float(wp0["x"]) - float(getattr(truth, "x", 0.0))
                dy = float(wp0["y"]) - float(getattr(truth, "y", 0.0))
                bearing = math.degrees(math.atan2(dx, dy)) % 360.0
                heading = float(getattr(truth, "heading", 0.0)) % 360.0
                delta = ((bearing - heading + 180.0) % 360.0) - 180.0
                self.assertLessEqual(abs(delta), 20.0)
        finally:
            vec_env.close()


if __name__ == "__main__":
    unittest.main()
