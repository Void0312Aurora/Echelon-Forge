from __future__ import annotations

import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from gym_envs.universal_env import UniversalEnv, build_universal_observation  # noqa: E402


def _build_route_result() -> ef_py.SpatialRouteQueryResult:
    geom = ef_py.CompiledScenarioGeometry()
    geom.set_route_leg_origin(0.0, 0.0)

    wp1 = ef_py.SpatialRouteWaypoint()
    wp1.x_m = 10000.0
    wp1.y_m = 0.0
    wp1.z_m = 1200.0
    wp1.altitude_m = 1200.0
    wp1.radius_m = 1000.0
    wp1.speed_mps = 210.0
    wp1.waypoint_mode = "flyover"
    geom.add_route_waypoint(wp1)

    wp2 = ef_py.SpatialRouteWaypoint()
    wp2.x_m = 20000.0
    wp2.y_m = 10000.0
    wp2.z_m = 1200.0
    wp2.altitude_m = 1200.0
    wp2.radius_m = 1000.0
    wp2.speed_mps = 210.0
    wp2.waypoint_mode = "flyby"
    geom.add_route_waypoint(wp2)

    opts = ef_py.SpatialRouteQueryOptions()
    opts.waypoint_index = 0
    opts.own_x_m = 0.0
    opts.own_y_m = 0.0
    opts.own_speed_mps = 210.0
    opts.base_lookahead_m = 1500.0
    opts.lnav_max_intercept_deg = 25.0
    opts.lnav_capture_max_intercept_deg = 45.0
    opts.lnav_capture_xtrack_m = 0.0
    opts.lnav_capture_course_error_deg = 45.0
    opts.lnav_direct_to_final_fix = True
    opts.lnav_bank_limit_deg = 30.0
    opts.lnav_sequence_gate_scale = 0.35
    return geom.query_route_guidance(opts)


def _build_runway_frame_result(*, x_m: float = 0.0, y_m: float = 0.0) -> ef_py.SpatialRunwayFrameResult:
    geom = ef_py.CompiledScenarioGeometry()
    runway = ef_py.SpatialRunwayDefinition()
    runway.runway_id = 1
    runway.name = "Runway_A"
    runway.center_x_m = 0.0
    runway.center_y_m = 0.0
    runway.threshold_x_m = -1250.0
    runway.threshold_y_m = 0.0
    runway.heading_deg = 90.0
    runway.length_m = 2500.0
    runway.width_m = 60.0
    geom.add_runway(runway)
    return geom.query_runway_local_frame(float(x_m), float(y_m))


class MissionRuntimeTests(unittest.TestCase):
    def test_waypoint_nav_products_match_nav_v2_contract_geometry(self) -> None:
        route_result = _build_route_result()
        self.assertTrue(bool(route_result.valid))

        inputs = ef_py.MissionNavInputs()
        inputs.own_altitude_m = 1200.0
        inputs.truth_heading_deg = 90.0
        inputs.truth_speed_mps = 210.0
        inputs.inst_heading_deg = 90.0
        inputs.inst_ground_track_deg = 90.0
        inputs.inst_ias_mps = 210.0
        inputs.waypoint_altitude_m = 1200.0
        inputs.cdi_full_scale_m = 1000.0

        nav = ef_py.compute_waypoint_mission_nav(route_result, inputs)
        self.assertTrue(bool(nav.valid))
        self.assertAlmostEqual(float(nav.selected_steerpoint), 1.0, places=6)
        self.assertAlmostEqual(float(nav.steerpoint_mode_code), 1.0, places=6)
        self.assertAlmostEqual(float(nav.dist_m), 10000.0, places=4)
        self.assertAlmostEqual(float(nav.bearing_rel_deg), 0.0, places=6)
        self.assertAlmostEqual(float(nav.altitude_delta_m), 0.0, places=6)
        self.assertAlmostEqual(float(nav.cdi_norm), 0.0, places=6)
        self.assertAlmostEqual(float(nav.track_angle_error_deg), 0.0, places=6)
        self.assertAlmostEqual(float(nav.dtg_m), 10000.0, places=4)
        self.assertAlmostEqual(float(nav.next_turn_deg), -45.0, places=4)
        self.assertGreater(float(nav.distance_to_turn_m), 0.0)
        self.assertLess(float(nav.distance_to_turn_m), float(nav.dtg_m))

    def test_command_tracking_error_uses_ground_track_for_waypoint_mode(self) -> None:
        waypoint_err = ef_py.compute_command_tracking_error_deg(90.0, 60.0, 3, 100.0)
        heading_err = ef_py.compute_command_tracking_error_deg(90.0, 60.0, 1, 100.0)
        self.assertAlmostEqual(float(waypoint_err), 10.0, places=6)
        self.assertAlmostEqual(float(heading_err), 30.0, places=6)

    def test_ground_track_error_falls_back_to_heading_when_track_invalid(self) -> None:
        track_err = ef_py.compute_ground_track_error_deg(90.0, 75.0, float("nan"))
        resolved = ef_py.resolve_ground_track_deg(75.0, float("nan"))
        self.assertTrue(math.isclose(float(track_err), 15.0, abs_tol=1.0e-6))
        self.assertTrue(math.isclose(float(resolved), 75.0, abs_tol=1.0e-6))

    def test_mission_observation_contract_matches_nav_v2_shape(self) -> None:
        route_result = _build_route_result()
        inputs = ef_py.MissionObservationInputs()
        inputs.mode_code = 2
        inputs.command_code = 3.0
        inputs.target_heading_deg = 90.0
        inputs.target_altitude_m = 1200.0
        inputs.target_speed_mps = 210.0
        inputs.has_route_guidance = True
        inputs.route_guidance = route_result

        nav_inputs = ef_py.MissionNavInputs()
        nav_inputs.own_altitude_m = 1200.0
        nav_inputs.truth_heading_deg = 90.0
        nav_inputs.truth_speed_mps = 210.0
        nav_inputs.inst_heading_deg = 90.0
        nav_inputs.inst_ground_track_deg = 90.0
        nav_inputs.inst_ias_mps = 210.0
        nav_inputs.waypoint_altitude_m = 1200.0
        nav_inputs.cdi_full_scale_m = 1000.0
        inputs.nav_inputs = nav_inputs

        products = ef_py.compute_mission_observation(inputs)
        self.assertTrue(bool(products.valid))
        self.assertTrue(bool(products.nav_valid))
        self.assertEqual(int(products.mode_code), 2)
        self.assertEqual(len(products.values), 14)
        self.assertAlmostEqual(float(products.values[0]), 3.0, places=6)
        self.assertAlmostEqual(float(products.values[4]), 1.0, places=6)
        self.assertAlmostEqual(float(products.values[5]), 1.0, places=6)
        self.assertAlmostEqual(float(products.values[6]), 10000.0, places=4)
        self.assertAlmostEqual(float(products.values[9]), 0.0, places=6)
        self.assertAlmostEqual(float(products.values[10]), 0.0, places=6)

    def test_mission_observation_contract_returns_zero_nav_tail_without_route_guidance(self) -> None:
        inputs = ef_py.MissionObservationInputs()
        inputs.mode_code = 1
        inputs.command_code = 2.0
        inputs.target_heading_deg = 45.0
        inputs.target_altitude_m = 800.0
        inputs.target_speed_mps = 150.0

        products = ef_py.compute_mission_observation(inputs)
        self.assertTrue(bool(products.valid))
        self.assertFalse(bool(products.nav_valid))
        self.assertEqual(len(products.values), 11)
        self.assertEqual(list(products.values[:4]), [2.0, 45.0, 800.0, 150.0])
        self.assertTrue(all(abs(float(v)) <= 1.0e-9 for v in products.values[4:]))

    def test_mission_observation_nav_v2_formation_v1_appends_slot_offsets(self) -> None:
        route_result = _build_route_result()
        inputs = ef_py.MissionObservationInputs()
        inputs.mode_code = 3
        inputs.command_code = 3.0
        inputs.target_heading_deg = 90.0
        inputs.target_altitude_m = 1200.0
        inputs.target_speed_mps = 210.0
        inputs.form_offset_x = 120.0
        inputs.form_offset_y = -45.0
        inputs.form_offset_z = 30.0
        inputs.has_route_guidance = True
        inputs.route_guidance = route_result

        nav_inputs = ef_py.MissionNavInputs()
        nav_inputs.own_altitude_m = 1200.0
        nav_inputs.truth_heading_deg = 90.0
        nav_inputs.truth_speed_mps = 210.0
        nav_inputs.inst_heading_deg = 90.0
        nav_inputs.inst_ground_track_deg = 90.0
        nav_inputs.inst_ias_mps = 210.0
        nav_inputs.waypoint_altitude_m = 1200.0
        nav_inputs.cdi_full_scale_m = 1000.0
        inputs.nav_inputs = nav_inputs

        products = ef_py.compute_mission_observation(inputs)
        self.assertTrue(bool(products.valid))
        self.assertTrue(bool(products.nav_valid))
        self.assertEqual(int(products.mode_code), 3)
        self.assertEqual(len(products.values), 17)
        self.assertEqual(list(products.values[:4]), [3.0, 90.0, 1200.0, 210.0])
        self.assertAlmostEqual(float(products.values[14]), 120.0, places=6)
        self.assertAlmostEqual(float(products.values[15]), -45.0, places=6)
        self.assertAlmostEqual(float(products.values[16]), 30.0, places=6)

    def test_mission_observation_nav_v2_formation_v1_keeps_offsets_without_route_guidance(self) -> None:
        inputs = ef_py.MissionObservationInputs()
        inputs.mode_code = 3
        inputs.command_code = 2.0
        inputs.target_heading_deg = 45.0
        inputs.target_altitude_m = 800.0
        inputs.target_speed_mps = 150.0
        inputs.form_offset_x = 300.0
        inputs.form_offset_y = -120.0
        inputs.form_offset_z = 20.0

        products = ef_py.compute_mission_observation(inputs)
        self.assertTrue(bool(products.valid))
        self.assertFalse(bool(products.nav_valid))
        self.assertEqual(len(products.values), 17)
        self.assertEqual(list(products.values[:4]), [2.0, 45.0, 800.0, 150.0])
        self.assertTrue(all(abs(float(v)) <= 1.0e-9 for v in products.values[4:14]))
        self.assertAlmostEqual(float(products.values[14]), 300.0, places=6)
        self.assertAlmostEqual(float(products.values[15]), -120.0, places=6)
        self.assertAlmostEqual(float(products.values[16]), 20.0, places=6)

    def test_mission_observation_nav_v2_formation_role_v1_appends_role_semantics(self) -> None:
        route_result = _build_route_result()
        inputs = ef_py.MissionObservationInputs()
        inputs.mode_code = 4
        inputs.command_code = 3.0
        inputs.target_heading_deg = 90.0
        inputs.target_altitude_m = 1200.0
        inputs.target_speed_mps = 210.0
        inputs.form_offset_x = 120.0
        inputs.form_offset_y = -45.0
        inputs.form_offset_z = 30.0
        inputs.self_role_code = 22.0
        inputs.self_formation_role_code = float(int(ef_py.FormationRole.Wingman))
        inputs.relative_slot_code = 12.0
        inputs.reference_relative_slot_code = 11.0
        inputs.has_route_guidance = True
        inputs.route_guidance = route_result

        nav_inputs = ef_py.MissionNavInputs()
        nav_inputs.own_altitude_m = 1200.0
        nav_inputs.truth_heading_deg = 90.0
        nav_inputs.truth_speed_mps = 210.0
        nav_inputs.inst_heading_deg = 90.0
        nav_inputs.inst_ground_track_deg = 90.0
        nav_inputs.inst_ias_mps = 210.0
        nav_inputs.waypoint_altitude_m = 1200.0
        nav_inputs.cdi_full_scale_m = 1000.0
        inputs.nav_inputs = nav_inputs

        products = ef_py.compute_mission_observation(inputs)
        self.assertTrue(bool(products.valid))
        self.assertTrue(bool(products.nav_valid))
        self.assertEqual(int(products.mode_code), 4)
        self.assertEqual(len(products.values), 21)
        self.assertAlmostEqual(float(products.values[14]), 120.0, places=6)
        self.assertAlmostEqual(float(products.values[15]), -45.0, places=6)
        self.assertAlmostEqual(float(products.values[16]), 30.0, places=6)
        self.assertAlmostEqual(float(products.values[17]), 22.0, places=6)
        self.assertAlmostEqual(float(products.values[18]), float(int(ef_py.FormationRole.Wingman)), places=6)
        self.assertAlmostEqual(float(products.values[19]), 12.0, places=6)
        self.assertAlmostEqual(float(products.values[20]), 11.0, places=6)

    def test_mission_observation_nav_v2_cooperative_takeoff_v1_appends_takeoff_semantics(self) -> None:
        route_result = _build_route_result()
        inputs = ef_py.MissionObservationInputs()
        inputs.mode_code = 5
        inputs.command_code = 1.0
        inputs.target_heading_deg = 90.0
        inputs.target_altitude_m = 500.0
        inputs.target_speed_mps = 180.0
        inputs.takeoff_procedure_code = 2.0
        inputs.takeoff_clearance_code = 3.0
        inputs.takeoff_interval_s = 5.0
        inputs.runway_slot_code = 2.0
        inputs.form_offset_x = 120.0
        inputs.form_offset_y = -45.0
        inputs.form_offset_z = 30.0
        inputs.self_role_code = 22.0
        inputs.self_formation_role_code = float(int(ef_py.FormationRole.Wingman))
        inputs.relative_slot_code = 12.0
        inputs.reference_relative_slot_code = 11.0
        inputs.has_route_guidance = True
        inputs.route_guidance = route_result

        nav_inputs = ef_py.MissionNavInputs()
        nav_inputs.own_altitude_m = 1200.0
        nav_inputs.truth_heading_deg = 90.0
        nav_inputs.truth_speed_mps = 210.0
        nav_inputs.inst_heading_deg = 90.0
        nav_inputs.inst_ground_track_deg = 90.0
        nav_inputs.inst_ias_mps = 210.0
        nav_inputs.waypoint_altitude_m = 1200.0
        nav_inputs.cdi_full_scale_m = 1000.0
        inputs.nav_inputs = nav_inputs

        products = ef_py.compute_mission_observation(inputs)
        self.assertTrue(bool(products.valid))
        self.assertTrue(bool(products.nav_valid))
        self.assertEqual(int(products.mode_code), 5)
        self.assertEqual(len(products.values), 25)
        self.assertAlmostEqual(float(products.values[14]), 2.0, places=6)
        self.assertAlmostEqual(float(products.values[15]), 3.0, places=6)
        self.assertAlmostEqual(float(products.values[16]), 5.0, places=6)
        self.assertAlmostEqual(float(products.values[17]), 2.0, places=6)
        self.assertAlmostEqual(float(products.values[18]), 120.0, places=6)
        self.assertAlmostEqual(float(products.values[24]), 11.0, places=6)

    def test_loader_nav_v2_current_contract_still_ignores_formation_offsets(self) -> None:
        scenario = {
            "scenario_name": "p8_mission_observation_contract_probe",
            "environment": {
                "time_step": 0.05,
                "terrain_type": "legacy",
                "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
            },
            "mission_command": {
                "command_code": 2,
                "target_heading": 33.0,
                "target_altitude": 1333.0,
                "target_speed": 177.0,
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

        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        loader = ScenarioLoader(sim)
        agent_id = loader.load_scenario_data(copy.deepcopy(scenario), seed=37)
        self.assertIsNotNone(agent_id)

        loader.mission_cmd["formation_id"] = 19
        loader.mission_cmd["form_offset_x"] = 1111.0
        loader.mission_cmd["form_offset_y"] = -2222.0
        loader.mission_cmd["form_offset_z"] = 3333.0

        truth = sim.get_agent_observation(int(agent_id))
        inst = sim.get_instrument_state(int(agent_id))
        inputs = loader._build_mission_observation_runtime_inputs("nav_v2", truth=truth, inst=inst)
        products = ef_py.compute_mission_observation(inputs)

        self.assertEqual(int(inputs.mode_code), 2)
        self.assertAlmostEqual(float(inputs.command_code), 2.0, places=6)
        self.assertAlmostEqual(float(inputs.target_heading_deg), 33.0, places=6)
        self.assertAlmostEqual(float(inputs.target_altitude_m), 1333.0, places=6)
        self.assertAlmostEqual(float(inputs.target_speed_mps), 177.0, places=6)
        self.assertAlmostEqual(float(inputs.form_offset_x), 1111.0, places=6)
        self.assertAlmostEqual(float(inputs.form_offset_y), -2222.0, places=6)
        self.assertAlmostEqual(float(inputs.form_offset_z), 3333.0, places=6)
        self.assertEqual(len(products.values), 14)
        self.assertEqual(list(products.values[:4]), [2.0, 33.0, 1333.0, 177.0])
        for marker in (1111.0, -2222.0, 3333.0):
            self.assertFalse(
                any(math.isclose(float(value), marker, rel_tol=0.0, abs_tol=1.0e-3) for value in products.values)
            )

    def test_loader_nav_v2_formation_v1_exposes_formation_offsets(self) -> None:
        scenario = {
            "scenario_name": "p8_mission_observation_formation_probe",
            "environment": {
                "time_step": 0.05,
                "terrain_type": "legacy",
                "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
            },
            "mission_command": {
                "command_code": 2,
                "target_heading": 33.0,
                "target_altitude": 1333.0,
                "target_speed": 177.0,
            },
            "entities": [
                {
                    "name": "Wing",
                    "type": "Aircraft",
                    "side": "Blue",
                    "is_agent": True,
                    "pos": [-1400.0, 0.0, 1200.0],
                    "vel": [0.0, 180.0, 0.0],
                    "heading": 90.0,
                }
            ],
        }

        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        loader = ScenarioLoader(sim)
        agent_id = loader.load_scenario_data(copy.deepcopy(scenario), seed=41)
        self.assertIsNotNone(agent_id)

        loader.mission_cmd["formation_id"] = 19
        loader.mission_cmd["form_offset_x"] = 1111.0
        loader.mission_cmd["form_offset_y"] = -2222.0
        loader.mission_cmd["form_offset_z"] = 3333.0

        truth = sim.get_agent_observation(int(agent_id))
        inst = sim.get_instrument_state(int(agent_id))
        inputs = loader._build_mission_observation_runtime_inputs("nav_v2_formation_v1", truth=truth, inst=inst)
        products = ef_py.compute_mission_observation(inputs)

        self.assertEqual(int(inputs.mode_code), 3)
        self.assertAlmostEqual(float(inputs.form_offset_x), 1111.0, places=6)
        self.assertAlmostEqual(float(inputs.form_offset_y), -2222.0, places=6)
        self.assertAlmostEqual(float(inputs.form_offset_z), 3333.0, places=6)
        self.assertEqual(len(products.values), 17)
        self.assertEqual(list(products.values[:4]), [2.0, 33.0, 1333.0, 177.0])
        self.assertAlmostEqual(float(products.values[14]), 1111.0, places=6)
        self.assertAlmostEqual(float(products.values[15]), -2222.0, places=6)
        self.assertAlmostEqual(float(products.values[16]), 3333.0, places=6)

    def test_loader_nav_v2_formation_role_v1_exposes_role_and_reference_semantics(self) -> None:
        scenario = {
            "scenario_name": "p8_mission_observation_role_probe",
            "environment": {
                "time_step": 0.05,
                "terrain_type": "legacy",
                "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
            },
            "mission_command": {
                "command_code": 2,
                "target_heading": 33.0,
                "target_altitude": 1333.0,
                "target_speed": 177.0,
            },
            "entities": [
                {
                    "name": "Lead",
                    "type": "Aircraft",
                    "side": "Blue",
                    "is_agent": True,
                    "pos": [-1500.0, 0.0, 1200.0],
                    "vel": [0.0, 180.0, 0.0],
                    "heading": 90.0,
                },
                {
                    "name": "Wing",
                    "type": "Aircraft",
                    "side": "Blue",
                    "is_agent": True,
                    "pos": [-1700.0, -200.0, 1200.0],
                    "vel": [0.0, 180.0, 0.0],
                    "heading": 90.0,
                },
            ],
            "cooperative_roster": {
                "policy_route": "shared_execution",
                "members": [
                    {"entity": "Lead", "role_code": 21, "formation_role_id": "ElementLead", "relative_slot_code": 11},
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

        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        loader = ScenarioLoader(sim)
        agent_id = loader.load_scenario_data(copy.deepcopy(scenario), seed=43)
        self.assertIsNotNone(agent_id)

        loader.agent_id = int(loader.entities["Wing"])
        loader.mission_cmd["form_offset_x"] = 1111.0
        loader.mission_cmd["form_offset_y"] = -2222.0
        loader.mission_cmd["form_offset_z"] = 3333.0

        truth = sim.get_agent_observation(int(loader.agent_id))
        inst = sim.get_instrument_state(int(loader.agent_id))
        inputs = loader._build_mission_observation_runtime_inputs("nav_v2_formation_role_v1", truth=truth, inst=inst)
        products = ef_py.compute_mission_observation(inputs)

        self.assertEqual(int(inputs.mode_code), 4)
        self.assertAlmostEqual(float(inputs.self_role_code), 22.0, places=6)
        self.assertAlmostEqual(float(inputs.self_formation_role_code), float(int(ef_py.FormationRole.Wingman)), places=6)
        self.assertAlmostEqual(float(inputs.relative_slot_code), 12.0, places=6)
        self.assertAlmostEqual(float(inputs.reference_relative_slot_code), 11.0, places=6)
        self.assertEqual(len(products.values), 21)
        self.assertAlmostEqual(float(products.values[17]), 22.0, places=6)
        self.assertAlmostEqual(float(products.values[18]), float(int(ef_py.FormationRole.Wingman)), places=6)
        self.assertAlmostEqual(float(products.values[19]), 12.0, places=6)
        self.assertAlmostEqual(float(products.values[20]), 11.0, places=6)

    def test_loader_nav_v2_cooperative_takeoff_v1_exposes_takeoff_and_role_semantics(self) -> None:
        scenario = {
            "scenario_name": "p8_mission_observation_takeoff_role_probe",
            "environment": {
                "time_step": 0.05,
                "terrain_type": "legacy",
                "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
            },
            "mission_command": {
                "command_code": 1,
                "target_heading": 90.0,
                "target_altitude": 500.0,
                "target_speed": 180.0,
                "takeoff_procedure_code": 2,
                "takeoff_clearance_code": 3,
                "takeoff_interval_s": 5.0,
                "runway_slot_code": 2,
            },
            "entities": [
                {
                    "name": "Lead",
                    "type": "Aircraft",
                    "side": "Blue",
                    "is_agent": True,
                    "pos": [-1500.0, 0.0, 2.1],
                    "vel": [0.0, 0.0, 0.0],
                    "heading": 90.0,
                },
                {
                    "name": "Wing",
                    "type": "Aircraft",
                    "side": "Blue",
                    "is_agent": True,
                    "pos": [-1700.0, -20.0, 2.1],
                    "vel": [0.0, 0.0, 0.0],
                    "heading": 90.0,
                },
            ],
            "cooperative_roster": {
                "policy_route": "shared_execution",
                "members": [
                    {"entity": "Lead", "role_code": 21, "formation_role_id": "ElementLead", "relative_slot_code": 11},
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

        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        loader = ScenarioLoader(sim)
        agent_id = loader.load_scenario_data(copy.deepcopy(scenario), seed=53)
        self.assertIsNotNone(agent_id)

        loader.agent_id = int(loader.entities["Wing"])
        loader.mission_cmd["form_offset_x"] = 1111.0
        loader.mission_cmd["form_offset_y"] = -2222.0
        loader.mission_cmd["form_offset_z"] = 3333.0

        truth = sim.get_agent_observation(int(loader.agent_id))
        inst = sim.get_instrument_state(int(loader.agent_id))
        inputs = loader._build_mission_observation_runtime_inputs("nav_v2_cooperative_takeoff_v1", truth=truth, inst=inst)
        products = ef_py.compute_mission_observation(inputs)

        self.assertEqual(int(inputs.mode_code), 5)
        self.assertAlmostEqual(float(inputs.takeoff_procedure_code), 2.0, places=6)
        self.assertAlmostEqual(float(inputs.takeoff_clearance_code), 3.0, places=6)
        self.assertAlmostEqual(float(inputs.takeoff_interval_s), 5.0, places=6)
        self.assertAlmostEqual(float(inputs.runway_slot_code), 2.0, places=6)
        self.assertEqual(len(products.values), 25)
        self.assertAlmostEqual(float(products.values[14]), 2.0, places=6)
        self.assertAlmostEqual(float(products.values[15]), 3.0, places=6)
        self.assertAlmostEqual(float(products.values[16]), 5.0, places=6)
        self.assertAlmostEqual(float(products.values[17]), 2.0, places=6)
        self.assertAlmostEqual(float(products.values[21]), 22.0, places=6)
        self.assertAlmostEqual(float(products.values[24]), 11.0, places=6)

    def test_route_guidance_uses_formation_slot_reference_geometry(self) -> None:
        scenario = {
            "scenario_name": "formation_route_guidance_geometry_probe",
            "environment": {
                "time_step": 0.05,
                "terrain_type": "legacy",
                "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
            },
            "mission_command": {
                "command_code": 3,
                "target_heading": 90.0,
                "target_altitude": 1200.0,
                "target_speed": 180.0,
                "form_offset_x": 180.0,
                "form_offset_y": -90.0,
                "form_offset_z": 30.0,
                "waypoint_mode": "flyby",
                "waypoints": [
                    {"x": 10000.0, "y": 0.0, "z": 1200.0, "altitude_m": 1200.0, "radius_m": 800.0},
                    {"x": 20000.0, "y": 0.0, "z": 1200.0, "altitude_m": 1200.0, "radius_m": 800.0},
                ],
            },
            "entities": [
                {
                    "name": "Wing",
                    "type": "Aircraft",
                    "side": "Blue",
                    "is_agent": True,
                    "pos": [0.0, 0.0, 1200.0],
                    "vel": [0.0, 180.0, 0.0],
                    "heading": 90.0,
                }
            ],
        }

        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        loader = ScenarioLoader(sim)
        agent_id = loader.load_scenario_data(copy.deepcopy(scenario), seed=59)
        self.assertIsNotNone(agent_id)

        truth = sim.get_agent_observation(int(agent_id))
        inst = sim.get_instrument_state(int(agent_id))
        result = loader._query_route_guidance_result(truth=truth, inst=inst)
        self.assertIsNotNone(result)
        assert result is not None

        self.assertAlmostEqual(float(result.xtk_m), -90.0, places=4)
        self.assertAlmostEqual(float(result.dist_m), math.hypot(9820.0, -90.0), places=3)

        nav_inputs = loader._mission_nav_inputs(truth, inst, result)
        self.assertIsNotNone(nav_inputs)
        assert nav_inputs is not None
        self.assertAlmostEqual(float(nav_inputs.waypoint_altitude_m), 1230.0, places=6)

    def test_step_info_runtime_reports_on_runway_geometry_only_preliftoff(self) -> None:
        frame = _build_runway_frame_result()
        inputs = ef_py.StepInfoInputs()
        inputs.on_runway = True
        inputs.gear_collapsed = False
        inputs.gear_stress = 0.25
        inputs.alt_agl_m = 1.0
        inputs.on_ground_alt_threshold_m = 2.5
        inputs.airborne_alt_threshold_m = 5.0
        inputs.has_runway_frame = True
        inputs.runway_frame = frame
        inputs.runway_width_margin_m = 2.0
        inputs.runway_length_margin_m = 0.0

        products = ef_py.compute_step_info_runtime(inputs)
        self.assertTrue(bool(products.valid))
        self.assertTrue(bool(products.on_runway))
        self.assertFalse(bool(products.gear_collapsed))
        self.assertAlmostEqual(float(products.gear_stress), 0.25, places=6)
        self.assertTrue(bool(products.on_ground))
        self.assertFalse(bool(products.airborne))
        self.assertTrue(bool(products.preliftoff))
        self.assertTrue(bool(products.has_runway_frame))
        self.assertTrue(bool(products.on_runway_geom))
        self.assertAlmostEqual(float(products.runway_cross_m), 0.0, places=6)
        self.assertAlmostEqual(float(products.runway_along_m), 0.0, places=6)

    def test_step_info_runtime_clears_on_runway_geom_when_airborne(self) -> None:
        frame = _build_runway_frame_result(x_m=10.0, y_m=0.0)
        inputs = ef_py.StepInfoInputs()
        inputs.on_runway = True
        inputs.gear_collapsed = True
        inputs.gear_stress = 0.5
        inputs.alt_agl_m = 12.0
        inputs.on_ground_alt_threshold_m = 2.5
        inputs.airborne_alt_threshold_m = 5.0
        inputs.has_runway_frame = True
        inputs.runway_frame = frame

        products = ef_py.compute_step_info_runtime(inputs)
        self.assertTrue(bool(products.valid))
        self.assertFalse(bool(products.on_ground))
        self.assertTrue(bool(products.airborne))
        self.assertFalse(bool(products.preliftoff))
        self.assertTrue(bool(products.has_runway_frame))
        self.assertFalse(bool(products.on_runway_geom))
        self.assertTrue(bool(products.gear_collapsed))
        self.assertAlmostEqual(float(products.gear_stress), 0.5, places=6)


class RewardRuntimeTests(unittest.TestCase):
    def test_waypoint_reward_terms_match_clipped_distance_and_cross_track(self) -> None:
        inputs = ef_py.WaypointRewardInputs()
        inputs.valid = True
        inputs.waypoint_index = 1
        inputs.waypoint_count = 2
        inputs.is_flyover = False
        inputs.has_guidance = True
        inputs.passed_fix = False
        inputs.dist_m = 14134.712341288418
        inputs.xtk_m = -9989.499135140415
        inputs.dtg_m = 14134.712341288418
        inputs.waypoint_radius_m = 1000.0
        inputs.leg_len_m = 10000.0
        inputs.lead_turn_m = 0.0
        inputs.sequence_gate_m = 1000.0
        inputs.has_prev_dist = False
        inputs.route_length_m = 20000.0
        inputs.distance_weight = -0.00004
        inputs.distance_clip_m = 6000.0
        inputs.cross_track_weight = -0.35
        inputs.cross_track_deadband_m = 250.0
        inputs.cross_track_norm_m = 1500.0
        inputs.cross_track_power = 1.5
        inputs.cross_track_clip = 2.0

        reward = ef_py.compute_waypoint_reward_terms(inputs)
        self.assertTrue(bool(reward.valid))
        self.assertAlmostEqual(float(reward.waypoint_distance), -0.24, places=6)
        self.assertAlmostEqual(float(reward.waypoint_cross_track), -0.9899494936611665, places=6)
        self.assertFalse(bool(reward.arrived))

    def test_intermediate_flyby_does_not_arrive_while_still_far_from_sequence_gate(self) -> None:
        inputs = ef_py.WaypointRewardInputs()
        inputs.valid = True
        inputs.waypoint_index = 0
        inputs.waypoint_count = 7
        inputs.is_flyover = False
        inputs.has_guidance = True
        inputs.passed_fix = False
        inputs.dist_m = 4000.0
        inputs.xtk_m = 0.0
        inputs.dtg_m = 4000.0
        inputs.waypoint_radius_m = 1500.0
        inputs.leg_len_m = 6000.0
        inputs.lead_turn_m = 10091.058970603393
        inputs.sequence_gate_m = 3500.0
        inputs.has_prev_dist = False
        inputs.route_length_m = 70000.0

        reward = ef_py.compute_waypoint_reward_terms(inputs)
        self.assertTrue(bool(reward.valid))
        self.assertFalse(bool(reward.arrived))

    def test_approach_reward_terms_produce_improvement_and_capture_bonus(self) -> None:
        inputs = ef_py.ApproachRewardInputs()
        inputs.valid = True
        inputs.ils_valid = True
        inputs.ils_loc_dev = 0.1
        inputs.ils_gs_dev = 0.1
        inputs.ils_dme_m = 9000.0
        inputs.has_prev_loc = True
        inputs.prev_loc_abs = 0.3
        inputs.has_prev_gs = True
        inputs.prev_gs_abs = 0.4
        inputs.has_prev_dme = True
        inputs.prev_dme_m = 9100.0
        inputs.localizer_improve_weight = 2.0
        inputs.glideslope_improve_weight = 2.0
        inputs.dme_progress_weight = 1.0
        inputs.dme_progress_localizer_band = 0.2
        inputs.dme_progress_glideslope_band = 0.2
        inputs.capture_bonus = 5.0
        inputs.capture_localizer_band = 0.2
        inputs.capture_glideslope_band = 0.2

        reward = ef_py.compute_approach_reward_terms(inputs)
        self.assertTrue(bool(reward.valid))
        self.assertAlmostEqual(float(reward.approach_localizer_improve), 0.4, places=6)
        self.assertAlmostEqual(float(reward.approach_glideslope_improve), 0.6, places=6)
        self.assertAlmostEqual(float(reward.approach_dme_progress), 25.0, places=6)
        self.assertAlmostEqual(float(reward.approach_capture_bonus), 5.0, places=6)
        self.assertTrue(bool(reward.next_prev_valid))
        self.assertFalse(bool(reward.clear_history))

    def test_approach_reward_terms_clear_history_when_ils_invalid(self) -> None:
        inputs = ef_py.ApproachRewardInputs()
        inputs.valid = True
        inputs.ils_valid = False
        inputs.has_prev_loc = True
        inputs.prev_loc_abs = 0.5
        inputs.has_prev_gs = True
        inputs.prev_gs_abs = 0.5
        inputs.has_prev_dme = True
        inputs.prev_dme_m = 10000.0
        inputs.sink_rate_weight = -2.0
        inputs.curr_alt_agl_m = 10.0
        inputs.flare_agl_m = 20.0
        inputs.sink_rate_mps = 4.0
        inputs.sink_rate_deadband_mps = 1.0
        inputs.sink_rate_norm_mps = 2.0
        inputs.sink_rate_power = 2.0

        reward = ef_py.compute_approach_reward_terms(inputs)
        self.assertTrue(bool(reward.valid))
        self.assertTrue(bool(reward.clear_history))
        self.assertFalse(bool(reward.next_prev_valid))
        self.assertTrue(math.isclose(float(reward.landing_sink_rate_penalty), -4.5, rel_tol=1.0e-6, abs_tol=1.0e-6))

    def test_flight_shaping_terms_update_takeoff_flags_and_progress(self) -> None:
        inputs = ef_py.FlightShapingRuntimeInputs()
        inputs.truth_altitude_m = 120.0
        inputs.truth_speed_mps = 95.0
        inputs.prev_altitude_m = 100.0
        inputs.prev_ias_mps = 80.0
        inputs.curr_ias_mps = 100.0
        inputs.curr_alt_baro_m = 120.0
        inputs.curr_alt_agl_m = 4.0
        inputs.curr_gear_fraction = 0.5
        inputs.curr_roll_deg = 2.0
        inputs.curr_pitch_deg = 10.0
        inputs.curr_beta_deg = 0.0
        inputs.curr_yaw_rate_deg_s = 0.0
        inputs.curr_g_load = 1.0
        inputs.step_count = 30
        inputs.target_altitude_m = 500.0
        inputs.target_speed_mps = 150.0
        inputs.heading_error_deg = 2.0
        inputs.ground_track_error_deg = 0.0
        inputs.preliftoff = True
        inputs.on_runway_task = True
        inputs.airborne = False
        inputs.liftoff_awarded = False
        inputs.gear_bonus_awarded = False
        inputs.altitude_progress_weight = 0.05
        inputs.speed_progress_weight = 0.02
        inputs.liftoff_bonus = 5.0
        inputs.liftoff_speed_threshold_mps = 80.0
        inputs.liftoff_alt_threshold_m = 3.0
        inputs.rotation_reward_weight = 0.5
        inputs.rotation_speed_threshold_mps = 80.0
        inputs.rotation_alt_threshold_m = 5.0
        inputs.rotation_pitch_cap_deg = 15.0
        inputs.heading_error_weight = -0.1
        inputs.heading_hold_deadband_deg = 3.0
        inputs.heading_hold_bonus = 1.0
        inputs.speed_reward_weight = 0.01

        reward = ef_py.compute_flight_shaping_terms(inputs)
        self.assertTrue(bool(reward.valid))
        self.assertAlmostEqual(float(reward.altitude_progress), 1.0, places=6)
        self.assertAlmostEqual(float(reward.speed_progress), 0.4, places=6)
        self.assertAlmostEqual(float(reward.liftoff_bonus), 5.0, places=6)
        self.assertTrue(bool(reward.next_liftoff_awarded))
        self.assertAlmostEqual(float(reward.rotation_reward), 5.0, places=6)
        self.assertAlmostEqual(float(reward.heading_error_penalty), -0.2, places=6)
        self.assertAlmostEqual(float(reward.heading_hold_bonus), 1.0, places=6)
        self.assertAlmostEqual(float(reward.speed_reward), 0.95, places=6)

    def test_flight_shaping_terms_cover_runway_and_airborne_tracking_terms(self) -> None:
        inputs = ef_py.FlightShapingRuntimeInputs()
        inputs.truth_altitude_m = 250.0
        inputs.truth_speed_mps = 140.0
        inputs.prev_altitude_m = 240.0
        inputs.prev_ias_mps = 130.0
        inputs.curr_ias_mps = 140.0
        inputs.curr_alt_baro_m = 230.0
        inputs.curr_alt_agl_m = 40.0
        inputs.curr_gear_fraction = 0.0
        inputs.curr_roll_deg = 20.0
        inputs.curr_pitch_deg = 5.0
        inputs.curr_beta_deg = 4.0
        inputs.curr_yaw_rate_deg_s = 3.0
        inputs.curr_g_load = 1.4
        inputs.step_count = 10
        inputs.target_altitude_m = 300.0
        inputs.target_speed_mps = 160.0
        inputs.heading_error_deg = 10.0
        inputs.ground_track_error_deg = 6.0
        inputs.preliftoff = True
        inputs.on_runway_task = True
        inputs.airborne = True
        inputs.has_runway_cross_m = True
        inputs.runway_cross_m = 5.0
        inputs.runway_width_m = 50.0
        inputs.ils_valid = True
        inputs.ils_loc_dev = 0.2
        inputs.altitude_error_weight = -1.0
        inputs.altitude_error_target_m = 200.0
        inputs.altitude_error_deadband_m = 0.0
        inputs.altitude_error_norm_m = 10.0
        inputs.speed_error_weight = -2.0
        inputs.speed_error_target_mps = 120.0
        inputs.speed_error_deadband_mps = 0.0
        inputs.speed_error_norm_mps = 10.0
        inputs.roll_abs_weight = -1.0
        inputs.roll_abs_deadband_deg = 0.0
        inputs.roll_abs_norm_deg = 20.0
        inputs.beta_abs_weight = -0.5
        inputs.beta_abs_deadband_deg = 0.0
        inputs.beta_abs_norm_deg = 4.0
        inputs.runway_centerline_penalty_min_ias_mps = 0.0
        inputs.runway_centerline_penalty_max_ias_mps = 200.0
        inputs.runway_centerline_m_penalty_weight = -2.0
        inputs.runway_centerline_m_norm_m = 5.0
        inputs.departure_centerline_max_alt_agl_m = 100.0
        inputs.departure_centerline_reward_weight = 1.0
        inputs.departure_centerline_reward_band_m = 10.0
        inputs.departure_track_reward_weight = 2.0
        inputs.departure_track_reward_band_deg = 12.0
        inputs.alignment_reward_weight = 0.5
        inputs.mission_alignment_min_alt_m = 120.0

        reward = ef_py.compute_flight_shaping_terms(inputs)
        self.assertTrue(bool(reward.valid))
        self.assertAlmostEqual(float(reward.altitude_error_penalty), -3.0, places=6)
        self.assertAlmostEqual(float(reward.speed_error_penalty), -4.0, places=6)
        self.assertAlmostEqual(float(reward.roll_abs_penalty), -1.0, places=6)
        self.assertAlmostEqual(float(reward.beta_abs_penalty), -0.5, places=6)
        self.assertAlmostEqual(float(reward.runway_centerline_m_penalty), -1.4, places=6)
        self.assertAlmostEqual(float(reward.departure_centerline_reward), 0.5, places=6)
        self.assertAlmostEqual(float(reward.departure_track_reward), 1.0, places=6)
        self.assertAlmostEqual(float(reward.alignment_reward), 0.4, places=6)


def _inline_observation_scenario() -> dict:
    return {
        "scenario_name": "execution_observation_runtime_inline",
        "meta": {
            "max_steps": 4,
        },
        "environment": {
            "time_step": 0.05,
            "terrain_type": "legacy",
            "wind": {
                "speed_mps": 4.0,
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


class ExecutionObservationRuntimeTests(unittest.TestCase):
    def test_agent_observation_live_tracks_expose_radar_source_and_friend_hostile_classification(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))

        lead = sim.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, 0.0, 1200.0, 0.0, 0.0, 0.0, 0.0, 180.0, 0.0)
        sim.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, 4000.0, 1200.0, 180.0, 0.0, 0.0, 0.0, -180.0, 0.0)
        sim.spawn_unit(ef_py.Side.Red, "F-16C_Block50", 0.0, 8000.0, 1200.0, 180.0, 0.0, 0.0, 0.0, -180.0, 0.0)

        obs = None
        for _ in range(80):
            sim.step()
            obs = sim.get_agent_observation(int(lead))
            if len(getattr(obs, "contacts", [])) >= 2:
                break

        self.assertIsNotNone(obs)
        contacts = list(getattr(obs, "contacts", []))
        self.assertGreaterEqual(len(contacts), 2)
        sources = {int(getattr(track, "source", 0)) for track in contacts}
        classes = {int(getattr(track, "classification", 0)) for track in contacts}
        self.assertTrue(sources.issubset({1, 3}))
        self.assertTrue(any(int(getattr(track, "source", 0)) in {1, 3} for track in contacts))
        self.assertIn(1, classes)
        self.assertIn(2, classes)

    def test_agent_observation_live_tracks_expose_datalink_source_for_shared_contact(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))

        lead = sim.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, 0.0, 1200.0, 0.0, 0.0, 0.0, 0.0, 180.0, 0.0)
        wing = sim.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 4000.0, 0.0, 1200.0, 90.0, 0.0, 0.0, 180.0, 0.0, 0.0)
        foe = sim.spawn_unit(ef_py.Side.Red, "F-16C_Block50", 12000.0, 0.0, 1200.0, 270.0, 0.0, 0.0, -180.0, 0.0, 0.0)

        lead_contact_ids = set()
        wing_obs = None
        for _ in range(120):
            sim.step()
            lead_obs = sim.get_agent_observation(int(lead))
            wing_obs = sim.get_agent_observation(int(wing))
            lead_contact_ids = {int(getattr(track, "id", 0)) for track in getattr(lead_obs, "contacts", [])}
            wing_tracks = {
                int(getattr(track, "id", 0)): track
                for track in getattr(wing_obs, "contacts", [])
            }
            if int(foe) in lead_contact_ids and int(foe) in wing_tracks and int(getattr(wing_tracks[int(foe)], "source", 0)) == 3:
                break

        self.assertIn(int(foe), lead_contact_ids)
        self.assertIsNotNone(wing_obs)
        wing_tracks = {
            int(getattr(track, "id", 0)): track
            for track in getattr(wing_obs, "contacts", [])
        }
        self.assertIn(int(foe), wing_tracks)
        self.assertEqual(int(getattr(wing_tracks[int(foe)], "source", 0)), 3)
        self.assertEqual(int(getattr(wing_tracks[int(foe)], "classification", 0)), 2)

    def test_execution_contact_runtime_contract_drops_source_and_classification(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        sim.reset(23)

        lead = sim.spawn_unit(ef_py.Side.Blue, "Aircraft", 0.0, 0.0, 1200.0, 90.0, 0.0, 0.0, 0.0, 180.0, 0.0)
        truth = sim.get_agent_observation(int(lead))
        inst = sim.get_instrument_state(int(lead))

        _inst_vec, contacts, _rwr = ef_py.compute_execution_observation_runtime_numpy(
            inst,
            truth,
            0.0,
            0.0,
            0.0,
            0.0,
            4,
            0,
        )
        contacts = np.asarray(contacts, dtype=np.float32)
        self.assertEqual(contacts.shape, (4, 5))

        source = Path(
            resolve_repo_path("src", "core", "mission", "runtime", "execution_observation_runtime.cpp")
        ).read_text(encoding="utf-8")
        self.assertIn("out.contact_values[base + 0u] = sanitize_scalar(track.range);", source)
        self.assertIn("out.contact_values[base + 1u] = sanitize_scalar(track.azimuth);", source)
        self.assertIn("out.contact_values[base + 2u] = sanitize_scalar(track.elevation);", source)
        self.assertIn("out.contact_values[base + 3u] = sanitize_scalar(track.closing_speed);", source)
        self.assertIn("out.contact_values[base + 4u] = sanitize_scalar(track.time_since_update);", source)
        self.assertNotIn("track.source", source)
        self.assertNotIn("track.classification", source)

    def test_visual_observation_team_channel_marks_friend_and_hostile(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        sim.reset(19)

        lead = sim.spawn_unit(ef_py.Side.Blue, "Aircraft", 0.0, 0.0, 1200.0, 90.0, 0.0, 0.0, 0.0, 180.0, 0.0)
        sim.spawn_unit(ef_py.Side.Blue, "Aircraft", 2000.0, 0.0, 1200.0, 90.0, 0.0, 0.0, 0.0, 180.0, 0.0)
        sim.spawn_unit(ef_py.Side.Red, "Aircraft", 2000.0, 800.0, 1200.0, 90.0, 0.0, 0.0, 0.0, 180.0, 0.0)

        for _ in range(2):
            sim.step()

        arb = np.asarray(sim.get_visual_observation(int(lead)), dtype=np.float32)
        team = arb[..., 8]

        self.assertEqual(arb.shape, (48, 96, 10))
        self.assertGreater(int(np.count_nonzero(team)), 0)
        self.assertIn(1.0, np.unique(team))
        self.assertIn(-1.0, np.unique(team))

    def test_compiled_observation_builder_matches_legacy_observation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_observation_scenario(), f, ensure_ascii=True)

            env = UniversalEnv(
                scenario_path=scenario_path,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="compiled",
            )
            try:
                _obs, _info = env.reset()
                inst = env._last_inst
                truth = env._last_truth
                loader = env.loader

                obs_compiled = build_universal_observation(
                    loader,
                    inst,
                    truth,
                    mission_obs_mode=env.mission_obs_mode,
                    max_contacts=env.max_contacts,
                    max_rwr=env.max_rwr,
                    include_proprio=False,
                    last_action=None,
                    action_space=env.action_space,
                    steps=int(env.steps),
                    max_steps=int(env.max_steps),
                )

                loader.use_compiled_execution_step_runtime = False
                obs_legacy = build_universal_observation(
                    loader,
                    inst,
                    truth,
                    mission_obs_mode=env.mission_obs_mode,
                    max_contacts=env.max_contacts,
                    max_rwr=env.max_rwr,
                    include_proprio=False,
                    last_action=None,
                    action_space=env.action_space,
                    steps=int(env.steps),
                    max_steps=int(env.max_steps),
                )

                self.assertTrue(np.allclose(obs_compiled["instruments"], obs_legacy["instruments"]))
                self.assertTrue(np.allclose(obs_compiled["contacts"], obs_legacy["contacts"]))
                self.assertTrue(np.allclose(obs_compiled["rwr"], obs_legacy["rwr"]))
                self.assertTrue(np.allclose(obs_compiled["mission"], obs_legacy["mission"]))

                ils_vec = loader.get_ils_observation(float(truth.x), float(truth.y), float(inst.alt_baro))
                inst_vec, contacts, rwr = ef_py.compute_execution_observation_runtime_numpy(
                    inst,
                    truth,
                    float(ils_vec[0]),
                    float(ils_vec[1]),
                    float(ils_vec[2]),
                    float(ils_vec[3]),
                    int(env.max_contacts),
                    int(env.max_rwr),
                )
                self.assertEqual(np.asarray(inst_vec, dtype=np.float32).shape, (42,))
                self.assertEqual(np.asarray(contacts, dtype=np.float32).shape, (env.max_contacts, 5))
                self.assertEqual(np.asarray(rwr, dtype=np.float32).shape, (env.max_rwr, 4))
                self.assertTrue(np.allclose(np.asarray(inst_vec, dtype=np.float32), obs_legacy["instruments"]))
            finally:
                env.close()


class ExecutionFrameRuntimeTests(unittest.TestCase):
    def test_fused_runtime_matches_separate_contracts(self) -> None:
        route_result = _build_route_result()
        runway_frame = _build_runway_frame_result()
        self.assertTrue(bool(route_result.valid))
        self.assertTrue(bool(runway_frame.valid))

        mission_inputs = ef_py.MissionObservationInputs()
        mission_inputs.mode_code = 2
        mission_inputs.command_code = 3.0
        mission_inputs.target_heading_deg = 90.0
        mission_inputs.target_altitude_m = 1200.0
        mission_inputs.target_speed_mps = 210.0
        mission_inputs.has_route_guidance = True
        mission_inputs.route_guidance = route_result

        nav_inputs = ef_py.MissionNavInputs()
        nav_inputs.own_altitude_m = 1200.0
        nav_inputs.truth_heading_deg = 90.0
        nav_inputs.truth_speed_mps = 210.0
        nav_inputs.inst_heading_deg = 90.0
        nav_inputs.inst_ground_track_deg = 90.0
        nav_inputs.inst_ias_mps = 210.0
        nav_inputs.waypoint_altitude_m = 1200.0
        nav_inputs.cdi_full_scale_m = 1000.0
        mission_inputs.nav_inputs = nav_inputs

        step_info_inputs = ef_py.StepInfoInputs()
        step_info_inputs.on_runway = True
        step_info_inputs.gear_collapsed = False
        step_info_inputs.gear_stress = 0.25
        step_info_inputs.alt_agl_m = 1.0
        step_info_inputs.on_ground_alt_threshold_m = 2.5
        step_info_inputs.airborne_alt_threshold_m = 5.0
        step_info_inputs.has_runway_frame = True
        step_info_inputs.runway_frame = runway_frame
        step_info_inputs.runway_width_margin_m = 2.0
        step_info_inputs.runway_length_margin_m = 0.0

        safety_inputs = ef_py.SafetyRuntimeInputs()
        safety_inputs.finite_state_valid = True
        safety_inputs.health = 100.0
        safety_inputs.survival_reward = 0.02
        safety_inputs.airborne = True
        safety_inputs.aoa_valid = True
        safety_inputs.aoa_abs_deg = 5.0
        safety_inputs.g_abs = 1.0
        safety_inputs.curr_alt_agl_m = 100.0
        safety_inputs.roll_abs_deg = 2.0
        safety_inputs.pitch_abs_deg = 1.0
        safety_inputs.runway_surface_phase = False
        safety_inputs.on_runway_task = False
        safety_inputs.gear_stress = 0.0
        safety_inputs.off_runway_steps = 0
        safety_inputs.time_step_s = 0.05

        exec_inputs = ef_py.ExecutionStepRuntimeInputs()
        exec_inputs.safety = safety_inputs
        exec_inputs.truncated = False

        shaping_inputs = ef_py.FlightShapingRuntimeInputs()
        shaping_inputs.truth_altitude_m = 1200.0
        shaping_inputs.truth_speed_mps = 210.0
        shaping_inputs.prev_altitude_m = 1180.0
        shaping_inputs.prev_ias_mps = 200.0
        shaping_inputs.curr_ias_mps = 210.0
        shaping_inputs.curr_alt_baro_m = 1200.0
        shaping_inputs.curr_alt_agl_m = 50.0
        shaping_inputs.curr_gear_fraction = 0.0
        shaping_inputs.curr_roll_deg = 2.0
        shaping_inputs.curr_pitch_deg = 3.0
        shaping_inputs.curr_beta_deg = 0.5
        shaping_inputs.curr_yaw_rate_deg_s = 0.2
        shaping_inputs.curr_g_load = 1.0
        shaping_inputs.target_altitude_m = 1500.0
        shaping_inputs.target_speed_mps = 250.0
        shaping_inputs.altitude_progress_weight = 0.01

        fused_inputs = ef_py.ExecutionFrameRuntimeInputs()
        fused_inputs.has_mission_observation = True
        fused_inputs.mission_observation = mission_inputs
        fused_inputs.has_step_info = True
        fused_inputs.step_info = step_info_inputs
        fused_inputs.has_execution_step = True
        fused_inputs.execution_step = exec_inputs
        fused_inputs.has_flight_shaping = True
        fused_inputs.flight_shaping = shaping_inputs

        fused = ef_py.compute_execution_frame_runtime(fused_inputs)
        separate_mission = ef_py.compute_mission_observation(mission_inputs)
        separate_step_info = ef_py.compute_step_info_runtime(step_info_inputs)
        separate_execution = ef_py.compute_execution_step_runtime(exec_inputs)
        separate_shaping = ef_py.compute_flight_shaping_terms(shaping_inputs)

        self.assertTrue(bool(fused.valid))
        self.assertTrue(bool(fused.mission_observation_evaluated))
        self.assertTrue(bool(fused.step_info_evaluated))
        self.assertTrue(bool(fused.execution_step_evaluated))
        self.assertTrue(bool(fused.flight_shaping_evaluated))
        self.assertEqual(list(fused.mission_observation.values), list(separate_mission.values))
        self.assertEqual(bool(fused.step_info.on_runway_geom), bool(separate_step_info.on_runway_geom))
        self.assertAlmostEqual(float(fused.step_info.runway_cross_m), float(separate_step_info.runway_cross_m), places=6)
        self.assertAlmostEqual(float(fused.execution_step.safety.survival), float(separate_execution.safety.survival), places=6)
        self.assertEqual(bool(fused.execution_step.terminated), bool(separate_execution.terminated))
        self.assertAlmostEqual(float(fused.flight_shaping.altitude_progress), float(separate_shaping.altitude_progress), places=6)


if __name__ == "__main__":
    unittest.main()
