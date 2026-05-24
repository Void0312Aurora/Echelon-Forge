from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402

from python.rl.profile.air_profile import build_kernel_mission_command as build_air_mission_command  # noqa: E402
from python.rl.profile.naval_profile import build_kernel_mission_command as build_naval_mission_command  # noqa: E402
from gym_envs.scenario_loader.runtime_state import apply_execution_episode_state  # noqa: E402


class MissionCommandRoeFieldTests(unittest.TestCase):
    def test_python_bindings_expose_roe_and_engagement_authority_fields(self) -> None:
        cmd = ef_py.MissionCommand()
        cmd.roe_state = 2
        cmd.engagement_authority_holder_id = 4101
        cmd.engagement_authority_grantor_id = 3101
        cmd.threat_state = 5
        cmd.assigned_target_track_id = 4401
        cmd.assigned_target_source_id = 5101
        cmd.assigned_target_snapshot_time_s = 12.5

        intent = ef_py.LeaderIntent()
        intent.roe_state = 3
        intent.engagement_authority_holder_id = 4201
        intent.engagement_authority_grantor_id = 3201
        intent.threat_state = 6
        intent.assigned_target_track_id = 4501
        intent.assigned_target_source_id = 5201
        intent.assigned_target_snapshot_time_s = 13.5

        self.assertEqual(int(cmd.roe_state), 2)
        self.assertEqual(int(cmd.engagement_authority_holder_id), 4101)
        self.assertEqual(int(cmd.engagement_authority_grantor_id), 3101)
        self.assertEqual(int(cmd.threat_state), 5)
        self.assertEqual(int(cmd.assigned_target_track_id), 4401)
        self.assertEqual(int(cmd.assigned_target_source_id), 5101)
        self.assertAlmostEqual(float(cmd.assigned_target_snapshot_time_s), 12.5, places=6)
        self.assertEqual(int(intent.roe_state), 3)
        self.assertEqual(int(intent.engagement_authority_holder_id), 4201)
        self.assertEqual(int(intent.engagement_authority_grantor_id), 3201)
        self.assertEqual(int(intent.threat_state), 6)
        self.assertEqual(int(intent.assigned_target_track_id), 4501)
        self.assertEqual(int(intent.assigned_target_source_id), 5201)
        self.assertAlmostEqual(float(intent.assigned_target_snapshot_time_s), 13.5, places=6)

    def test_air_profile_build_kernel_mission_command_propagates_roe_fields(self) -> None:
        leader_intent = SimpleNamespace(
            command_code=2,
            cmd_heading_deg=67.0,
            cmd_altitude_m=2100.0,
            cmd_speed_mps=205.0,
            roe_state=2,
            engagement_authority_holder_id=7101,
            engagement_authority_grantor_id=7001,
            assigned_target_id=4401,
            authorization_to_fire=True,
        )
        loader = SimpleNamespace(
            mission_cmd={
                "command_code": 2,
                "target_heading": 123.0,
                "target_altitude": 3100.0,
                "target_speed": 222.0,
                "roe_state": 1,
                "engagement_authority_holder_id": 6101,
                "engagement_authority_grantor_id": 6001,
                "assigned_target_id": 4001,
                "authorization_to_fire": False,
            },
            leader_intent=leader_intent,
            task_order=None,
            waypoints=[],
        )

        cmd = build_air_mission_command(loader)
        self.assertEqual(int(cmd.roe_state), 2)
        self.assertEqual(int(cmd.engagement_authority_holder_id), 7101)
        self.assertEqual(int(cmd.engagement_authority_grantor_id), 7001)
        self.assertEqual(int(cmd.assigned_target_id), 4401)
        self.assertTrue(bool(cmd.authorization_to_fire))

    def test_naval_profile_build_kernel_mission_command_propagates_roe_fields(self) -> None:
        task = ef_py.TaskOrder()
        task.service_profile = ef_py.ServiceProfile.Navy
        task.task_family = ef_py.TaskFamily.Escort
        task.coordination_mode = ef_py.CoordinationMode.Screen
        task.station_heading_deg = 35.0
        task.station_radius_m = 14000.0
        task.target_speed_mps = 12.5
        task.target_altitude_m = 0.0

        agent_member = type("_Member", (), {"entity_id": 5101, "reference_entity_id": 5201})()
        loader = type(
            "_Loader",
            (),
            {
                "scenario_data": {
                    "mission_command": {
                        "reference_entity_id": 6201,
                        "station_radius_m": 16000.0,
                        "station_bearing_deg": 75.0,
                        "target_heading": 80.0,
                        "target_speed": 14.0,
                        "roe_state": 3,
                        "engagement_authority_holder_id": 8201,
                        "engagement_authority_grantor_id": 8101,
                        "assigned_target_id": 8301,
                        "threat_state": 7,
                        "assigned_target_track_id": 8301,
                        "assigned_target_source_id": 5101,
                        "assigned_target_snapshot_time_s": 24.5,
                        "authorization_to_fire": True,
                    }
                },
                "task_order": task,
                "mission_cmd": {
                    "roe_state": 1,
                    "engagement_authority_holder_id": 7201,
                    "engagement_authority_grantor_id": 7101,
                    "assigned_target_id": 7301,
                    "threat_state": 4,
                    "assigned_target_track_id": 7301,
                    "assigned_target_source_id": 4101,
                    "assigned_target_snapshot_time_s": 20.0,
                    "authorization_to_fire": False,
                },
                "agent_id": 5101,
                "active_roster": [agent_member],
                "get_active_roster_member": staticmethod(lambda entity_id=None, entity_name=None: agent_member),
            },
        )()

        cmd = build_naval_mission_command(loader)

        self.assertEqual(int(cmd.roe_state), 3)
        self.assertEqual(int(cmd.engagement_authority_holder_id), 8201)
        self.assertEqual(int(cmd.engagement_authority_grantor_id), 8101)
        self.assertEqual(int(cmd.assigned_target_id), 8301)
        self.assertEqual(int(cmd.threat_state), 7)
        self.assertEqual(int(cmd.assigned_target_track_id), 8301)
        self.assertEqual(int(cmd.assigned_target_source_id), 5101)
        self.assertAlmostEqual(float(cmd.assigned_target_snapshot_time_s), 24.5, places=6)
        self.assertTrue(bool(cmd.authorization_to_fire))

    def test_execution_episode_controller_post_transition_roundtrip_preserves_roe_fields(self) -> None:
        controller = ef_py.ExecutionEpisodeController()

        episode_state = ef_py.ExecutionEpisodeState()
        episode_state.has_mission_command = True
        episode_state.mission_command.command_code = 3
        episode_state.mission_command.cmd_heading_deg = 90.0
        episode_state.mission_command.cmd_altitude_m = 1200.0
        episode_state.mission_command.cmd_speed_mps = 180.0
        episode_state.mission_command.roe_state = 1
        episode_state.mission_command.engagement_authority_holder_id = 4001
        episode_state.mission_command.engagement_authority_grantor_id = 3001
        episode_state.mission_command.assigned_target_id = 3501
        episode_state.mission_command.threat_state = 4
        episode_state.mission_command.assigned_target_track_id = 3501
        episode_state.mission_command.assigned_target_source_id = 4001
        episode_state.mission_command.assigned_target_snapshot_time_s = 10.0
        episode_state.mission_command.authorization_to_fire = False
        episode_state.mission_command.active = True
        episode_state.has_mission_command_json = True
        episode_state.mission_command_json = json.dumps(
            {
                "command_code": 3,
                "roe_state": 1,
                "engagement_authority_holder_id": 4001,
                "engagement_authority_grantor_id": 3001,
                "assigned_target_id": 3501,
                "threat_state": 4,
                "assigned_target_track_id": 3501,
                "assigned_target_source_id": 4001,
                "assigned_target_snapshot_time_s": 10.0,
                "authorization_to_fire": False,
                "target_altitude": 1200.0,
                "target_heading": 90.0,
                "target_speed": 180.0,
                "waypoint_mode": "flyby",
                "waypoints": [
                    {"x": -1350.0, "y": 0.0, "z": 1200.0, "radius_m": 1200.0},
                ],
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        route_waypoint = ef_py.SpatialRouteWaypoint()
        route_waypoint.x_m = -1350.0
        route_waypoint.y_m = 0.0
        route_waypoint.z_m = 1200.0
        route_waypoint.radius_m = 1200.0
        route_waypoint.altitude_m = 1200.0
        route_waypoint.speed_mps = 180.0
        route_waypoint.waypoint_mode = "flyby"
        episode_state.route_waypoints = [route_waypoint]
        episode_state.waypoint_index = 0
        episode_state.has_post_waypoint_transition_json = True
        episode_state.post_waypoint_transition_json = json.dumps(
            {
                "command_code": 2,
                "phase_name": "post_route",
                "target_altitude": 900.0,
                "target_heading": 45.0,
                "target_speed": 160.0,
                "roe_state": 2,
                "engagement_authority_holder_id": 5001,
                "engagement_authority_grantor_id": 4501,
                "assigned_target_id": 5501,
                "threat_state": 6,
                "assigned_target_track_id": 5501,
                "assigned_target_source_id": 5001,
                "assigned_target_snapshot_time_s": 11.5,
                "authorization_to_fire": True,
                "transition_reward": 10.0,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        controller.import_state(episode_state)

        env_state = ef_py.StepEvaluationBatchEnvState()
        env_state.steps = 1
        env_state.truth_x = -1400.0
        env_state.truth_y = 0.0
        env_state.truth_z = 1200.0
        env_state.truth_speed = 180.0
        env_state.has_safety = True
        env_state.safety.finite_state_valid = True
        env_state.safety.health = 100.0
        env_state.safety.survival_reward = 0.02

        env_state.has_waypoint = True
        env_state.waypoint.valid = True
        env_state.waypoint.waypoint_index = 0
        env_state.waypoint.waypoint_count = 1
        env_state.waypoint.dist_m = 50.0
        env_state.waypoint.waypoint_radius_m = 1200.0
        env_state.waypoint.has_prev_dist = True
        env_state.waypoint.prev_dist_m = 120.0
        env_state.waypoint.progress_weight = 0.1
        env_state.waypoint.distance_weight = -0.001
        env_state.waypoint.reached_bonus = 20.0

        result = controller.step_result(ef_py.StepEvaluationBatchConfig(), env_state)

        self.assertTrue(bool(result.valid))
        self.assertEqual(int(result.controller_state.mission_command.roe_state), 2)
        self.assertEqual(int(result.controller_state.mission_command.engagement_authority_holder_id), 5001)
        self.assertEqual(int(result.controller_state.mission_command.engagement_authority_grantor_id), 4501)
        self.assertEqual(int(result.controller_state.mission_command.assigned_target_id), 5501)
        self.assertEqual(int(result.controller_state.mission_command.threat_state), 6)
        self.assertEqual(int(result.controller_state.mission_command.assigned_target_track_id), 5501)
        self.assertEqual(int(result.controller_state.mission_command.assigned_target_source_id), 5001)
        self.assertAlmostEqual(
            float(result.controller_state.mission_command.assigned_target_snapshot_time_s),
            11.5,
            places=6,
        )
        self.assertTrue(bool(result.controller_state.mission_command.authorization_to_fire))

        mission_json = json.loads(str(result.controller_state.mission_command_json))
        self.assertEqual(int(mission_json["roe_state"]), 2)
        self.assertEqual(int(mission_json["engagement_authority_holder_id"]), 5001)
        self.assertEqual(int(mission_json["engagement_authority_grantor_id"]), 4501)
        self.assertEqual(int(mission_json["assigned_target_id"]), 5501)
        self.assertEqual(int(mission_json["threat_state"]), 6)
        self.assertEqual(int(mission_json["assigned_target_track_id"]), 5501)
        self.assertEqual(int(mission_json["assigned_target_source_id"]), 5001)
        self.assertAlmostEqual(float(mission_json["assigned_target_snapshot_time_s"]), 11.5, places=6)
        self.assertTrue(bool(mission_json["authorization_to_fire"]))

    def test_runtime_state_fallback_preserves_threat_and_assigned_target_provenance(self) -> None:
        episode_state = ef_py.ExecutionEpisodeState()
        episode_state.has_mission_command = True
        episode_state.has_mission_command_json = False
        episode_state.mission_command.command_code = 3
        episode_state.mission_command.assigned_target_id = 9101
        episode_state.mission_command.threat_state = 8
        episode_state.mission_command.assigned_target_track_id = 9101
        episode_state.mission_command.assigned_target_source_id = 5101
        episode_state.mission_command.assigned_target_snapshot_time_s = 33.25
        episode_state.mission_command.authorization_to_fire = False
        episode_state.mission_command.active = True

        loader = SimpleNamespace(
            agent_id=None,
            steps=0,
            scenario_data={},
            route_waypoints=[],
            waypoints=[],
            waypoint_idx=0,
            waypoint_total_route_length_m=0.0,
            _waypoint_prev_dist_m=None,
            _waypoint_leg_origin_x=0.0,
            _waypoint_leg_origin_y=0.0,
            prev_alt=0.0,
            prev_speed=0.0,
            liftoff_awarded=False,
            gear_bonus_awarded=False,
            off_runway_steps=0,
            _approach_prev_dme_m=None,
            _approach_prev_loc_abs=None,
            _approach_prev_gs_abs=None,
            post_waypoint_transition=None,
            mission_phase_name="idle",
            _cached_route_ref_id=None,
            last_reward_breakdown={},
            last_termination_reason="idle",
            task_order=None,
            leader_intent=None,
            _rebuild_spatial_geometry=lambda: None,
        )

        apply_execution_episode_state(loader, episode_state)

        self.assertEqual(int(loader.mission_cmd["assigned_target_id"]), 9101)
        self.assertEqual(int(loader.mission_cmd["threat_state"]), 8)
        self.assertEqual(int(loader.mission_cmd["assigned_target_track_id"]), 9101)
        self.assertEqual(int(loader.mission_cmd["assigned_target_source_id"]), 5101)
        self.assertAlmostEqual(float(loader.mission_cmd["assigned_target_snapshot_time_s"]), 33.25, places=6)


if __name__ == "__main__":
    unittest.main()
