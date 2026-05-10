from __future__ import annotations

import copy
import json
import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402


def _route_transition_scenario() -> dict:
    return {
        "scenario_name": "execution_episode_state_roundtrip",
        "environment": {
            "time_step": 0.05,
            "terrain_type": "legacy",
            "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
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
            "command_code": 3,
            "target_heading": 90.0,
            "target_altitude": 1200.0,
            "target_speed": 180.0,
            "route_ref_id": 77,
            "waypoint_mode": "flyby",
            "waypoints": [
                {"x": -500.0, "y": 0.0, "z": 1200.0, "radius_m": 800.0, "speed_mps": 180.0},
                {"x": 2500.0, "y": 1500.0, "z": 1200.0, "radius_m": 800.0, "speed_mps": 170.0},
            ],
            "post_waypoint_transition": {
                "command_code": 4,
                "target_heading": 90.0,
                "target_altitude": 0.0,
                "target_speed": 82.0,
                "landing_mode": "ils_final",
                "phase_name": "landing_final",
            },
        },
        "entities": [
            {
                "name": "Lead",
                "type": "F-16C_Block50",
                "side": "Blue",
                "is_agent": True,
                "pos": [-1400.0, 0.0, 1200.0],
                "vel": [0.0, 180.0, 0.0],
                "heading": 90.0,
            }
        ],
        "objectives": [],
        "rewards": {},
    }


class ExecutionEpisodeStateTests(unittest.TestCase):
    def test_scenario_loader_exports_execution_episode_state(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        loader = ScenarioLoader(sim)
        agent_id = loader.load_scenario_data(copy.deepcopy(_route_transition_scenario()), seed=19)
        self.assertIsNotNone(agent_id)

        loader.steps = 17
        loader.waypoint_idx = 1
        loader._waypoint_prev_dist_m = 321.5
        loader._waypoint_leg_origin_x = -1400.0
        loader._waypoint_leg_origin_y = 0.0
        loader.waypoint_total_route_length_m = 4200.0
        loader.prev_alt = 1185.0
        loader.prev_speed = 176.0
        loader.liftoff_awarded = True
        loader.gear_bonus_awarded = True
        loader.off_runway_steps = 3
        loader._approach_prev_dme_m = 4567.0
        loader._approach_prev_loc_abs = 0.12
        loader._approach_prev_gs_abs = 0.08
        loader.mission_phase_name = "route_primary"
        loader.last_termination_reason = "Running"
        loader.last_reward_breakdown = {
            "survival": 0.02,
            "waypoint_progress": 1.25,
            "total": 1.27,
        }

        state = loader.build_execution_episode_state()

        self.assertEqual(int(state.agent_id), int(agent_id))
        self.assertEqual(int(state.step_count), 17)
        self.assertTrue(bool(state.has_mission_command))
        self.assertTrue(bool(state.has_mission_command_json))
        self.assertEqual(len(list(state.route_waypoints)), 2)
        self.assertEqual(int(state.waypoint_index), 1)
        self.assertTrue(bool(state.has_waypoint_prev_dist_m))
        self.assertAlmostEqual(float(state.waypoint_prev_dist_m), 321.5, places=6)
        self.assertAlmostEqual(float(state.waypoint_leg_origin_x_m), -1400.0, places=6)
        self.assertAlmostEqual(float(state.waypoint_leg_origin_y_m), 0.0, places=6)
        self.assertAlmostEqual(float(state.prev_altitude_m), 1185.0, places=6)
        self.assertAlmostEqual(float(state.prev_ias_mps), 176.0, places=6)
        self.assertTrue(bool(state.liftoff_awarded))
        self.assertTrue(bool(state.gear_bonus_awarded))
        self.assertEqual(int(state.off_runway_steps), 3)
        self.assertTrue(bool(state.has_approach_prev_dme_m))
        self.assertTrue(bool(state.has_approach_prev_loc_abs))
        self.assertTrue(bool(state.has_approach_prev_gs_abs))
        self.assertTrue(bool(state.has_post_waypoint_transition_json))
        self.assertEqual(str(state.mission_phase_name), "route_primary")
        self.assertTrue(bool(state.has_cached_route_ref_id))
        self.assertEqual(int(state.cached_route_ref_id), 77)
        self.assertEqual(str(state.last_termination_reason), "Running")
        self.assertAlmostEqual(float(state.last_reward_total), 1.27, places=6)

        mission_cmd = json.loads(str(state.mission_command_json))
        self.assertEqual(int(mission_cmd["command_code"]), 3)
        self.assertEqual(len(list(mission_cmd.get("waypoints", []) or [])), 2)

        reward_breakdown = json.loads(str(state.last_reward_breakdown_json))
        self.assertAlmostEqual(float(reward_breakdown["total"]), 1.27, places=6)

    def test_scenario_loader_execution_episode_state_roundtrip_preserves_state(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))

        source_loader = ScenarioLoader(sim)
        agent_id = source_loader.load_scenario_data(copy.deepcopy(_route_transition_scenario()), seed=23)
        self.assertIsNotNone(agent_id)

        source_loader.steps = 9
        source_loader.waypoint_idx = 1
        source_loader._waypoint_prev_dist_m = 278.0
        source_loader._waypoint_leg_origin_x = -1300.0
        source_loader._waypoint_leg_origin_y = 40.0
        source_loader.waypoint_total_route_length_m = 3900.0
        source_loader.prev_alt = 1190.0
        source_loader.prev_speed = 172.5
        source_loader.liftoff_awarded = True
        source_loader.gear_bonus_awarded = False
        source_loader.off_runway_steps = 1
        source_loader._approach_prev_dme_m = 4100.0
        source_loader._approach_prev_loc_abs = 0.22
        source_loader._approach_prev_gs_abs = 0.11
        source_loader.mission_phase_name = "post_turn"
        source_loader.last_termination_reason = "SuccessWaypoint"
        source_loader.last_reward_breakdown = {
            "survival": 0.02,
            "waypoint_reached_bonus": 25.0,
            "total": 25.02,
        }

        exported = source_loader.build_execution_episode_state()

        mirror_loader = ScenarioLoader(sim)
        mirror_loader.apply_execution_episode_state(exported)
        mirrored = mirror_loader.build_execution_episode_state()

        self.assertTrue(bool(ef_py.execution_episode_states_equivalent(exported, mirrored)))
        self.assertEqual(int(mirror_loader.waypoint_idx), 1)
        self.assertAlmostEqual(float(mirror_loader._waypoint_prev_dist_m), 278.0, places=6)
        self.assertEqual(str(mirror_loader.mission_phase_name), "post_turn")
        self.assertEqual(str(mirror_loader.last_termination_reason), "SuccessWaypoint")
        self.assertEqual(int(mirror_loader._cached_route_ref_id), 77)
        self.assertEqual(len(list(mirror_loader.waypoints)), 2)
        self.assertAlmostEqual(float(mirror_loader.last_reward_breakdown["total"]), 25.02, places=6)

