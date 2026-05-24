from __future__ import annotations

import copy
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index  # noqa: E402
from python.rl.runtime.multi_agent_runtime import MultiAgentWorldRuntimeView  # noqa: E402


def _cooperative_scenario() -> dict:
    return {
        "scenario_name": "multi_agent_runtime_smoke",
        "environment": {
            "time_step": 0.05,
            "terrain_type": "legacy",
            "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
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
            },
            {
                "name": "Wing",
                "type": "Aircraft",
                "side": "Blue",
                "is_agent": True,
                "pos": [-1550.0, -120.0, 1200.0],
                "vel": [0.0, 180.0, 0.0],
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
                },
                {
                    "entity": "Wing",
                    "role_code": 22,
                    "formation_role_id": "Wingman",
                    "relative_slot_code": 12,
                    "reference_entity": "Lead",
                },
            ],
        },
    }


class _ActionSpaceStub:
    def __init__(self) -> None:
        self.low = np.asarray(
            [-1.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            dtype=np.float32,
        )
        self.high = np.asarray(
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            dtype=np.float32,
        )
        self.shape = self.low.shape


class MultiAgentRuntimeViewTests(unittest.TestCase):
    def test_loader_exposes_active_roster_helpers(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        loader = ScenarioLoader(sim)
        agent_id = loader.load_scenario_data(copy.deepcopy(_cooperative_scenario()), seed=37)
        self.assertIsNotNone(agent_id)

        self.assertEqual(len(loader.active_roster), 2)
        wing = loader.get_active_roster_member(entity_name="Wing")
        self.assertIsNotNone(wing)
        self.assertEqual(str(wing.formation_role_id), "Wingman")
        refs = loader.get_active_roster_refs(world_index=0)
        self.assertEqual(len(refs), 2)
        self.assertEqual([int(ref.world_index) for ref in refs], [0, 0])

    def test_multi_agent_runtime_view_builds_per_entity_observations(self) -> None:
        runtime = ef_py.WorldBatchRuntime(1)
        self.assertTrue(runtime.load_database(resolve_repo_path("examples", "config", "database")))
        loader = ScenarioLoader(runtime.world_compatibility_quarantine(0))
        loader.load_scenario_data(copy.deepcopy(_cooperative_scenario()), seed=41)

        lead = loader.get_active_roster_member(entity_name="Lead")
        wing = loader.get_active_roster_member(entity_name="Wing")
        self.assertIsNotNone(lead)
        self.assertIsNotNone(wing)
        runtime.world_compatibility_quarantine(0).set_command_link(int(lead.entity_id), 0.0, 0.0)
        runtime.world_compatibility_quarantine(0).set_command_link(int(wing.entity_id), 0.0, 0.0)

        lead_cmd = ef_py.MissionCommand()
        lead_cmd.command_code = 2
        lead_cmd.cmd_heading_deg = 90.0
        lead_cmd.cmd_altitude_m = 1200.0
        lead_cmd.cmd_speed_mps = 180.0
        lead_cmd.formation_id = 17
        lead_cmd.form_offset_x = 0.0
        lead_cmd.form_offset_y = 0.0
        lead_cmd.form_offset_z = 0.0
        lead_cmd.active = True

        wing_cmd = ef_py.MissionCommand()
        wing_cmd.command_code = 2
        wing_cmd.cmd_heading_deg = 90.0
        wing_cmd.cmd_altitude_m = 1200.0
        wing_cmd.cmd_speed_mps = 180.0
        wing_cmd.formation_id = 17
        wing_cmd.form_offset_x = 180.0
        wing_cmd.form_offset_y = -90.0
        wing_cmd.form_offset_z = 30.0
        wing_cmd.active = True

        assign0 = ef_py.WorldMissionCommandAssignment()
        assign0.world_index = 0
        assign0.entity_id = int(lead.entity_id)
        assign0.command = lead_cmd
        assign1 = ef_py.WorldMissionCommandAssignment()
        assign1.world_index = 0
        assign1.entity_id = int(wing.entity_id)
        assign1.command = wing_cmd
        runtime.set_mission_commands_batch([assign0, assign1])

        view = MultiAgentWorldRuntimeView(
            runtime=runtime,
            loader=loader,
            world_index=0,
            action_space=_ActionSpaceStub(),
            action_mode="full",
            mission_obs_mode="nav_v2_formation_v1",
            include_proprio=False,
        )
        obs_by_entity_id = view.build_observations()
        formation_x = mission_observation_field_index("nav_v2_formation_v1", "form_offset_x_m")
        formation_y = mission_observation_field_index("nav_v2_formation_v1", "form_offset_y_m")
        formation_z = mission_observation_field_index("nav_v2_formation_v1", "form_offset_z_m")

        self.assertEqual(set(obs_by_entity_id.keys()), {int(lead.entity_id), int(wing.entity_id)})
        self.assertEqual(obs_by_entity_id[int(lead.entity_id)]["mission"].shape, (mission_observation_dim("nav_v2_formation_v1"),))
        self.assertEqual(obs_by_entity_id[int(wing.entity_id)]["mission"].shape, (mission_observation_dim("nav_v2_formation_v1"),))
        self.assertAlmostEqual(float(obs_by_entity_id[int(lead.entity_id)]["mission"][formation_x]), 0.0, places=6)
        self.assertAlmostEqual(float(obs_by_entity_id[int(wing.entity_id)]["mission"][formation_x]), 180.0, places=6)
        self.assertAlmostEqual(float(obs_by_entity_id[int(wing.entity_id)]["mission"][formation_y]), -90.0, places=6)
        self.assertAlmostEqual(float(obs_by_entity_id[int(wing.entity_id)]["mission"][formation_z]), 30.0, places=6)

    def test_multi_agent_runtime_view_routes_actions_per_entity(self) -> None:
        runtime = ef_py.WorldBatchRuntime(1)
        self.assertTrue(runtime.load_database(resolve_repo_path("examples", "config", "database")))
        loader = ScenarioLoader(runtime.world_compatibility_quarantine(0))
        loader.load_scenario_data(copy.deepcopy(_cooperative_scenario()), seed=43)

        lead = loader.get_active_roster_member(entity_name="Lead")
        wing = loader.get_active_roster_member(entity_name="Wing")
        self.assertIsNotNone(lead)
        self.assertIsNotNone(wing)
        runtime.world_compatibility_quarantine(0).set_command_link(int(lead.entity_id), 0.0, 0.0)
        runtime.world_compatibility_quarantine(0).set_command_link(int(wing.entity_id), 0.0, 0.0)

        view = MultiAgentWorldRuntimeView(
            runtime=runtime,
            loader=loader,
            world_index=0,
            action_space=_ActionSpaceStub(),
            action_mode="full",
            mission_obs_mode="nav_v2",
            include_proprio=False,
        )
        actions = {
            int(lead.entity_id): np.zeros((17,), dtype=np.float32),
            int(wing.entity_id): np.asarray(
                [0.15, -0.2, 0.05, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                dtype=np.float32,
            ),
        }

        assignments = view.apply_actions(actions)

        self.assertEqual(len(assignments), 2)
        by_entity = {int(assign.entity_id): assign for assign in assignments}
        self.assertIn(int(lead.entity_id), by_entity)
        self.assertIn(int(wing.entity_id), by_entity)
        self.assertAlmostEqual(float(by_entity[int(lead.entity_id)].action.throttle), 0.0, places=6)
        self.assertAlmostEqual(float(by_entity[int(wing.entity_id)].action.stick_pitch), 0.15, places=6)
        self.assertAlmostEqual(float(by_entity[int(wing.entity_id)].action.stick_roll), -0.2, places=6)
        self.assertAlmostEqual(float(by_entity[int(wing.entity_id)].action.rudder), 0.05, places=6)
        self.assertAlmostEqual(float(by_entity[int(wing.entity_id)].action.throttle), 0.7, places=6)


if __name__ == "__main__":
    unittest.main()
