from __future__ import annotations

import copy
import json
import math
import os
import tempfile
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402
from gym_envs.scenario_loader import ScenarioLoader # noqa: E402
from python.scenario.compiler import ( # noqa: E402
  CompiledScenario as PackagedCompiledScenario,
)
from python.scenario.compiler import ScenarioCompiler as PackagedScenarioCompiler # noqa: E402
from python.scenario_compiler import ( # noqa: E402
  DEFAULT_TERRAIN_TYPE,
  ScenarioCompiler,
  TERRAIN_TYPE_SOURCE_COMPATIBILITY,
  TERRAIN_TYPE_SOURCE_DEFAULT,
  TERRAIN_TYPE_SOURCE_EXPLICIT,
)
from python.scenario.runtime import prepare_scenario_world_layout # noqa: E402


def _sample_scenario() -> dict:
  return {
    "scenario_name": "scenario_compiler_test",
    "imports": [{"file": "examples/config/prefabs/airbase_large_runway45.json"}],
    "environment": {
      "time_step": 0.05,
      "max_steps": 10,
      "terrain_type": "flat",
      "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
    },
    "mission_command": {
      "command_code": 4,
      "target_heading": 90.0,
      "target_altitude": 0.0,
      "target_speed": 82.0,
      "landing_mode": "ils_final",
      "reference_runway": "Runway 09",
      "threshold_crossing_height_m": 15.0,
    },
    "entities": [
      {
        "name": "Blue_F16",
        "type": "F-16C_Block50",
        "side": "Blue",
        "pos": [-4500.0, 0.0, 172.15775811444114],
        "vel": [82.0, 0.0, 0.0],
        "heading": 90.0,
        "is_agent": True,
      }
    ],
    "objectives": [],
    "rewards": {"survival": 0.0},
  }


def _sample_route_template_scenario() -> dict:
  return {
    "scenario_name": "scenario_compiler_route_template_test",
    "environment": {
      "time_step": 0.05,
      "max_steps": 10,
      "terrain_type": "flat",
      "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
      "randomization": {
        "world_yaw_range": [15.0, 15.0],
        "world_yaw_origin": [0.0, 0.0],
        "rotate_mission_heading_with_world": True,
      },
    },
    "mission_command": {
      "command_code": 3,
      "target_heading": 90.0,
      "target_altitude": 1200.0,
      "target_speed": 180.0,
      "waypoint_mode": "flyby",
      "randomization": {
        "waypoint_templates": [
          [
            {"x": 1000.0, "y": 0.0, "altitude_m": 1200.0, "speed_mps": 180.0, "radius_m": 600.0},
            {"x": 2000.0, "y": 500.0, "altitude_m": 1200.0, "speed_mps": 180.0, "radius_m": 600.0},
          ],
          [
            {"x": 800.0, "y": -300.0, "altitude_m": 1250.0, "speed_mps": 170.0, "radius_m": 550.0},
            {"x": 2200.0, "y": -900.0, "altitude_m": 1250.0, "speed_mps": 170.0, "radius_m": 550.0},
          ],
        ]
      },
    },
    "entities": [
      {
        "name": "Blue_F16",
        "type": "F-16C_Block50",
        "side": "Blue",
        "pos": [0.0, 0.0, 1200.0],
        "vel": [0.0, 180.0, 0.0],
        "heading": 90.0,
        "is_agent": True,
      }
    ],
    "objectives": [],
    "rewards": {"survival": 0.0},
  }


def _sample_maritime_scenario(configured: bool) -> dict:
  scenario = _sample_scenario()
  if configured:
    scenario["environment"]["maritime"] = {
      "sea_state": 3.0,
      "wave_heading_deg": 45.0,
      "wave_period_s": 7.5,
    }
  return scenario


def _sample_explicit_calm_maritime_scenario() -> dict:
  scenario = _sample_scenario()
  scenario["environment"]["maritime"] = {
    "sea_state": 0.0,
    "wave_heading_deg": 135.0,
    "wave_period_s": 11.0,
  }
  return scenario


def _make_geometry() -> ef_py.CompiledScenarioGeometry:
  geom = ef_py.CompiledScenarioGeometry()

  runway = ef_py.SpatialRunwayDefinition()
  runway.runway_id = 7
  runway.name = "Runway 36"
  runway.center_x_m = 0.0
  runway.center_y_m = 0.0
  runway.threshold_x_m = 0.0
  runway.threshold_y_m = -500.0
  runway.heading_deg = 0.0
  runway.length_m = 1000.0
  runway.width_m = 50.0
  runway.elevation_m = 0.0
  runway.glide_slope_deg = 3.0
  runway.localizer_max_deg = 10.0
  runway.glideslope_max_deg = 2.0
  runway.range_m = 10000.0
  geom.add_runway(runway)

  geom.set_route_leg_origin(0.0, 0.0)

  wp1 = ef_py.SpatialRouteWaypoint()
  wp1.x_m = 1000.0
  wp1.y_m = 0.0
  wp1.z_m = 1000.0
  wp1.radius_m = 400.0
  wp1.altitude_m = 1000.0
  wp1.speed_mps = 180.0
  wp1.waypoint_mode = "flyby"
  geom.add_route_waypoint(wp1)

  wp2 = ef_py.SpatialRouteWaypoint()
  wp2.x_m = 2000.0
  wp2.y_m = 1000.0
  wp2.z_m = 900.0
  wp2.radius_m = 350.0
  wp2.altitude_m = 900.0
  wp2.speed_mps = 160.0
  wp2.waypoint_mode = "flyby"
  geom.add_route_waypoint(wp2)
  return geom


class ScenarioCompilerTests(unittest.TestCase):
  def setUp(self) -> None:
    ScenarioCompiler.clear_cache()
    fd, self._scenario_path = tempfile.mkstemp(prefix="scenario_compiler_", suffix=".json")
    os.close(fd)
    with open(self._scenario_path, "w", encoding="utf-8") as f:
      json.dump(_sample_scenario(), f, ensure_ascii=True)

  def tearDown(self) -> None:
    try:
      os.unlink(self._scenario_path)
    except OSError:
      pass
    ScenarioCompiler.clear_cache()

  def test_compile_path_merges_imports_and_caches(self) -> None:
    compiled1 = ScenarioCompiler.compile_path(self._scenario_path)
    compiled2 = ScenarioCompiler.compile_path(self._scenario_path)

    self.assertIs(compiled1, compiled2)
    self.assertEqual(compiled1.source_path, os.path.abspath(self._scenario_path))
    self.assertGreater(compiled1.zone_count, 0)
    self.assertGreaterEqual(compiled1.entity_count, 1)
    names = [str(ent.get("name", "")) for ent in compiled1.merged_scenario_data.get("entities", []) if isinstance(ent, dict)]
    self.assertIn("Blue_F16", names)

    inst1 = compiled1.instantiate()
    inst2 = compiled1.instantiate()
    inst1["environment"]["zones"].append({"name": "mutated"})
    self.assertEqual(len(inst2["environment"]["zones"]), compiled1.zone_count)

  def test_packaged_import_path_preserves_public_types(self) -> None:
    compiled = PackagedScenarioCompiler.compile_path(self._scenario_path)

    self.assertIs(ScenarioCompiler, PackagedScenarioCompiler)
    self.assertIsInstance(compiled, PackagedCompiledScenario)

  def test_compile_path_rejects_non_object_root(self) -> None:
    with open(self._scenario_path, "w", encoding="utf-8") as f:
      json.dump([], f, ensure_ascii=True)

    with self.assertRaisesRegex(ValueError, "Scenario file must contain a JSON object"):
      ScenarioCompiler.compile_path(self._scenario_path)

  def test_compile_data_rejects_non_list_entities(self) -> None:
    scenario = _sample_scenario()
    scenario["entities"] = {"Blue_F16": scenario["entities"][0]}

    with self.assertRaisesRegex(ValueError, "'entities' must be a list"):
      ScenarioCompiler.compile_data(scenario)

  def test_compile_data_rejects_non_object_entity_entries(self) -> None:
    scenario = _sample_scenario()
    scenario["entities"] = ["Blue_F16"]

    with self.assertRaisesRegex(ValueError, "entities\\[0\\] must be an object"):
      ScenarioCompiler.compile_data(scenario)

  def test_compile_data_rejects_duplicate_entity_names(self) -> None:
    scenario = _sample_scenario()
    scenario["entities"].append(copy.deepcopy(scenario["entities"][0]))

    with self.assertRaisesRegex(ValueError, "duplicate entity name 'Blue_F16'"):
      ScenarioCompiler.compile_data(scenario)

  def test_compile_data_rejects_missing_import(self) -> None:
    scenario = _sample_scenario()
    scenario["imports"] = [{"file": "examples/config/prefabs/does_not_exist.json"}]

    with self.assertRaisesRegex(FileNotFoundError, "Scenario import file not found"):
      ScenarioCompiler.compile_data(scenario)

  def test_compile_data_rejects_invalid_import_prefab_shape(self) -> None:
    fd, prefab_path = tempfile.mkstemp(prefix="scenario_compiler_prefab_", suffix=".json")
    os.close(fd)
    try:
      with open(prefab_path, "w", encoding="utf-8") as f:
        json.dump({"entities": {"Control_Tower": {}}}, f, ensure_ascii=True)
      scenario = _sample_scenario()
      scenario["imports"] = [{"file": prefab_path}]

      with self.assertRaisesRegex(
        ValueError,
        "imported scenario prefab 'entities' must be a list",
      ):
        ScenarioCompiler.compile_data(scenario)
    finally:
      os.unlink(prefab_path)

  def test_instantiate_isolates_nested_runtime_branches(self) -> None:
    compiled = ScenarioCompiler.compile_path(self._scenario_path)

    inst1 = compiled.instantiate()
    inst2 = compiled.instantiate()

    inst1["environment"]["zones"][0]["ils"]["glide_slope_deg"] = 9.0
    inst1["entities"][0]["pos"][0] = 12345.0
    inst1["mission_command"]["post_waypoint_transition"] = {"phase_name": "mutated"}

    self.assertEqual(
      inst2["environment"]["zones"][0]["ils"]["glide_slope_deg"],
      compiled.merged_scenario_data["environment"]["zones"][0]["ils"]["glide_slope_deg"],
    )
    self.assertEqual(
      inst2["entities"][0]["pos"][0],
      compiled.merged_scenario_data["entities"][0]["pos"][0],
    )
    self.assertNotIn("post_waypoint_transition", inst2["mission_command"])
    self.assertNotIn("post_waypoint_transition", compiled.merged_scenario_data["mission_command"])

  def test_instantiate_runtime_isolates_runtime_mutation_branches(self) -> None:
    compiled = ScenarioCompiler.compile_path(self._scenario_path)

    inst1 = compiled.instantiate_runtime()
    inst2 = compiled.instantiate_runtime()

    inst1["environment"]["zones"][0]["heading"] = 222.0
    inst1["entities"][0]["pos"][0] = 54321.0
    inst1["mission_command"]["target_heading"] = 12.0

    self.assertNotEqual(
      inst1["environment"]["zones"][0]["heading"],
      inst2["environment"]["zones"][0]["heading"],
    )
    self.assertNotEqual(
      inst1["entities"][0]["pos"][0],
      inst2["entities"][0]["pos"][0],
    )
    self.assertNotEqual(
      inst1["mission_command"]["target_heading"],
      inst2["mission_command"]["target_heading"],
    )
    self.assertEqual(
      inst2["environment"]["zones"][0]["heading"],
      compiled.merged_scenario_data["environment"]["zones"][0]["heading"],
    )
    self.assertEqual(
      inst2["entities"][0]["pos"][0],
      compiled.merged_scenario_data["entities"][0]["pos"][0],
    )
    self.assertEqual(
      inst2["mission_command"]["target_heading"],
      compiled.merged_scenario_data["mission_command"]["target_heading"],
    )

  def test_instantiate_runtime_context_strips_layout_branches_but_keeps_route_seed_context(self) -> None:
    compiled = ScenarioCompiler.compile_path(self._scenario_path)

    context = compiled.instantiate_runtime_context()

    self.assertIn("environment", context)
    self.assertIn("mission_command", context)
    self.assertIn("_runtime_agent_spawn", context)
    if "entities" in context:
      self.assertTrue(isinstance(context["entities"], list))
      self.assertTrue(all("scripted_agent" in ent for ent in context["entities"]))
    self.assertNotIn("zones", context["environment"])
    self.assertEqual(int(context["environment"]["max_steps"]), 10)
    self.assertAlmostEqual(float(context["environment"]["time_step"]), 0.05, places=6)
    self.assertAlmostEqual(float(context["_runtime_agent_spawn"]["pos"][0]), -4500.0, places=6)
    self.assertAlmostEqual(float(context["_runtime_agent_spawn"]["heading"]), 90.0, places=6)

  def test_instantiate_runtime_context_preserves_lightweight_scripted_entity_context(self) -> None:
    scenario = _sample_scenario()
    scenario["entities"].append(
      {
        "name": "Red_F16",
        "type": "F-16C_Block50",
        "side": "Red",
        "pos": [0.0, 8000.0, 1200.0],
        "vel": [0.0, -180.0, 0.0],
        "heading": 180.0,
        "scripted_agent": {
          "name": "red_scripted_agent",
          "target_name": "Blue_F16",
          "fire_range_m": 9000.0,
        },
      }
    )
    compiled = ScenarioCompiler.compile_data(scenario)

    context = compiled.instantiate_runtime_context()

    self.assertIn("entities", context)
    self.assertEqual(len(context["entities"]), 1)
    self.assertEqual(str(context["entities"][0]["name"]), "Red_F16")
    self.assertEqual(str(context["entities"][0]["scripted_agent"]["name"]), "red_scripted_agent")

  def test_loader_can_load_compiled_scenario(self) -> None:
    compiled = ScenarioCompiler.compile_path(self._scenario_path)

    sim = ef_py.SimulationKernel()
    sim.load_database("examples/config/database")

    loader = ScenarioLoader(sim)
    agent_id = loader.load_compiled_scenario(compiled, seed=0)

    self.assertIsNotNone(agent_id)
    self.assertIs(loader._compiled_scenario, compiled)
    self.assertEqual(loader._scenario_source_path, os.path.abspath(self._scenario_path))
    self.assertGreater(len(loader.ils_beacons), 0)

  def test_runtime_metadata_precompiles_static_runtime_config(self) -> None:
    compiled = ScenarioCompiler.compile_path(self._scenario_path)

    runtime = compiled.runtime_metadata
    self.assertEqual(runtime.mission_command_template["command_code"], 4)
    self.assertEqual(runtime.mission_command_template["recovery_approach_type"], "StraightIn")
    self.assertGreater(len(runtime.ils_beacon_templates), 0)
    self.assertEqual(runtime.safety_reward_config.crash_penalty, -1000.0)
    self.assertFalse(runtime.approach_reward_config.active)
    self.assertGreater(len(runtime.layout_template.zones), 0)
    self.assertGreater(len(runtime.layout_template.spawns), 0)
    self.assertEqual(runtime.layout_template.terrain_type, "flat")
    self.assertAlmostEqual(float(runtime.layout_template.time_step_s), 0.05, places=6)

  def test_runtime_metadata_defaults_missing_terrain_type_to_non_legacy_mainline(self) -> None:
    scenario = _sample_scenario()
    scenario["environment"].pop("terrain_type", None)

    compiled = ScenarioCompiler.compile_data(scenario)

    self.assertEqual(compiled.runtime_metadata.layout_template.terrain_type, DEFAULT_TERRAIN_TYPE)
    self.assertEqual(compiled.runtime_metadata.layout_template.terrain_type_source, TERRAIN_TYPE_SOURCE_DEFAULT)

  def test_runtime_metadata_marks_explicit_legacy_terrain_as_compatibility(self) -> None:
    scenario = _sample_scenario()
    scenario["environment"]["terrain_type"] = "legacy"

    compiled = ScenarioCompiler.compile_data(scenario)

    self.assertEqual(compiled.runtime_metadata.layout_template.terrain_type, "legacy")
    self.assertEqual(
      compiled.runtime_metadata.layout_template.terrain_type_source,
      TERRAIN_TYPE_SOURCE_COMPATIBILITY,
    )

  def test_runtime_metadata_rejects_unknown_terrain_type(self) -> None:
    scenario = _sample_scenario()
    scenario["environment"]["terrain_type"] = "desert"

    with self.assertRaisesRegex(ValueError, "Unknown terrain_type"):
      ScenarioCompiler.compile_data(scenario)

  def test_runtime_metadata_precompiles_waypoint_templates(self) -> None:
    compiled = ScenarioCompiler.compile_data(_sample_route_template_scenario())

    runtime = compiled.runtime_metadata
    self.assertEqual(len(runtime.normalized_waypoint_templates), 2)
    self.assertEqual(len(runtime.waypoint_template_route_ref_ids), 2)
    self.assertEqual(len(runtime.normalized_waypoint_templates[0]), 2)
    self.assertAlmostEqual(float(runtime.normalized_waypoint_templates[0][0]["x"]), 1000.0, places=6)
    self.assertAlmostEqual(float(runtime.normalized_waypoint_templates[1][1]["y"]), -900.0, places=6)
    self.assertGreater(int(runtime.waypoint_template_route_ref_ids[0]), 0)


class SpatialQueryRuntimeTests(unittest.TestCase):
  def test_runway_local_frame_matches_heading_convention(self) -> None:
    geom = _make_geometry()
    frame = geom.query_runway_local_frame(12.0, 125.0)

    self.assertTrue(frame.valid)
    self.assertEqual(frame.runway_id, 7)
    self.assertTrue(math.isclose(frame.along_m, 125.0, abs_tol=1.0e-6))
    self.assertTrue(math.isclose(frame.cross_m, 12.0, abs_tol=1.0e-6))
    self.assertTrue(math.isclose(frame.heading_deg, 0.0, abs_tol=1.0e-6))

  def test_ils_query_uses_threshold_crossing_height(self) -> None:
    geom = _make_geometry()
    approach_dist_m = 1500.0
    tch_m = 15.0
    alt_m = tch_m + math.tan(math.radians(3.0)) * approach_dist_m

    ils = geom.query_ils(0.0, -2000.0, alt_m, tch_m)

    self.assertTrue(ils.valid)
    self.assertLess(abs(ils.loc_dev), 1.0e-6)
    self.assertLess(abs(ils.gs_dev), 1.0e-3)
    self.assertTrue(math.isclose(ils.approach_dist_m, approach_dist_m, rel_tol=1.0e-6, abs_tol=1.0e-6))

  def test_route_query_reports_leg_geometry_and_turn_preview(self) -> None:
    geom = _make_geometry()
    opts = ef_py.SpatialRouteQueryOptions()
    opts.waypoint_index = 0
    opts.own_x_m = 100.0
    opts.own_y_m = 100.0
    opts.own_speed_mps = 180.0
    opts.base_lookahead_m = 1500.0
    opts.lnav_max_intercept_deg = 25.0
    opts.lnav_capture_max_intercept_deg = 45.0
    opts.lnav_capture_course_error_deg = 45.0
    opts.lnav_direct_to_final_fix = True
    opts.lnav_bank_limit_deg = 30.0
    opts.lnav_sequence_gate_scale = 0.35

    route = geom.query_route_guidance(opts)

    self.assertTrue(route.valid)
    self.assertEqual(route.idx, 0)
    self.assertEqual(route.count, 2)
    self.assertEqual(route.waypoint_mode, "flyby")
    self.assertTrue(math.isclose(route.desired_track_deg, 90.0, abs_tol=1.0e-6))
    self.assertTrue(math.isclose(route.xtk_m, -100.0, abs_tol=1.0e-6))
    self.assertTrue(math.isclose(route.dtg_m, 900.0, abs_tol=1.0e-6))
    self.assertFalse(route.use_direct_to)
    self.assertFalse(route.direct_to_fix_guidance)
    self.assertGreater(route.lead_turn_m, 0.0)
    self.assertGreater(route.sequence_gate_m, route.waypoint_radius_m)
    self.assertLess(route.next_turn_deg, 0.0)
    self.assertGreater(route.next_turn_abs_deg, 0.0)
    self.assertTrue(
      math.isclose(route.dist_to_next_turn_start_m, max(0.0, route.dtg_m - route.lead_turn_m), abs_tol=1.0e-6)
    )

  def test_route_query_reports_previous_turn_geometry_on_later_leg(self) -> None:
    geom = _make_geometry()
    opts = ef_py.SpatialRouteQueryOptions()
    opts.waypoint_index = 1
    opts.own_x_m = 1300.0
    opts.own_y_m = 300.0
    opts.own_speed_mps = 160.0
    opts.base_lookahead_m = 1200.0
    opts.lnav_max_intercept_deg = 25.0
    opts.lnav_capture_max_intercept_deg = 45.0
    opts.lnav_capture_course_error_deg = 45.0
    opts.lnav_direct_to_final_fix = False
    opts.lnav_bank_limit_deg = 30.0
    opts.lnav_sequence_gate_scale = 0.35

    route = geom.query_route_guidance(opts)

    self.assertTrue(route.valid)
    self.assertEqual(route.idx, 1)
    self.assertEqual(route.count, 2)
    self.assertTrue(route.final_leg)
    self.assertGreater(route.prev_turn_abs_deg, 0.0)
    self.assertTrue(math.isclose(route.prev_turn_abs_deg, 45.0, abs_tol=1.0e-6))
    self.assertTrue(math.isclose(route.xtk_m, 0.0, abs_tol=1.0e-6))
    self.assertGreater(route.distance_from_prev_turn_m, 0.0)
    self.assertTrue(math.isclose(route.distance_from_prev_turn_m, route.along_m, abs_tol=1.0e-6))

  def test_compile_world_layout_tracks_maritime_configuration_presence(self) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
      json.dump(_sample_maritime_scenario(False), handle, ensure_ascii=True)
      no_maritime_path = handle.name
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
      json.dump(_sample_maritime_scenario(True), handle, ensure_ascii=True)
      maritime_path = handle.name

    try:
      compiled_no_maritime = ScenarioCompiler.compile_path(no_maritime_path)
      compiled_maritime = ScenarioCompiler.compile_path(maritime_path)
    finally:
      os.unlink(no_maritime_path)
      os.unlink(maritime_path)

    self.assertFalse(compiled_no_maritime.runtime_metadata.layout_template.maritime_configured)
    self.assertTrue(compiled_maritime.runtime_metadata.layout_template.maritime_configured)
    self.assertAlmostEqual(compiled_maritime.runtime_metadata.layout_template.sea_state, 3.0, places=6)
    self.assertAlmostEqual(compiled_maritime.runtime_metadata.layout_template.wave_heading_deg, 45.0, places=6)
    self.assertAlmostEqual(compiled_maritime.runtime_metadata.layout_template.wave_period_s, 7.5, places=6)

  def test_compile_world_layout_treats_explicit_calm_maritime_as_configured_override(self) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
      json.dump(_sample_explicit_calm_maritime_scenario(), handle, ensure_ascii=True)
      maritime_path = handle.name

    try:
      compiled = ScenarioCompiler.compile_path(maritime_path)
    finally:
      os.unlink(maritime_path)

    layout = compiled.runtime_metadata.layout_template
    self.assertTrue(layout.maritime_configured)
    self.assertAlmostEqual(layout.sea_state, 0.0, places=6)
    self.assertAlmostEqual(layout.wave_heading_deg, 135.0, places=6)
    self.assertAlmostEqual(layout.wave_period_s, 11.0, places=6)

  def test_prepare_scenario_world_layout_defaults_missing_terrain_type_to_non_legacy_mainline(self) -> None:
    scenario = _sample_scenario()
    scenario["environment"].pop("terrain_type", None)

    layout = prepare_scenario_world_layout(
      scenario,
      seed=11,
      rng=np.random.RandomState(11),
      compiled_template=None,
    )

    self.assertEqual(layout.terrain_type, DEFAULT_TERRAIN_TYPE)
    self.assertEqual(layout.terrain_type_source, TERRAIN_TYPE_SOURCE_DEFAULT)

  def test_prepare_scenario_world_layout_preserves_explicit_terrain_type_source(self) -> None:
    scenario = _sample_scenario()
    scenario["environment"]["terrain_type"] = "legacy"

    layout = prepare_scenario_world_layout(
      scenario,
      seed=12,
      rng=np.random.RandomState(12),
      compiled_template=None,
    )

    self.assertEqual(layout.terrain_type, "legacy")
    self.assertEqual(layout.terrain_type_source, TERRAIN_TYPE_SOURCE_COMPATIBILITY)

    scenario["environment"]["terrain_type"] = "flat"
    explicit_layout = prepare_scenario_world_layout(
      scenario,
      seed=13,
      rng=np.random.RandomState(13),
      compiled_template=None,
    )

    self.assertEqual(explicit_layout.terrain_type, DEFAULT_TERRAIN_TYPE)
    self.assertEqual(explicit_layout.terrain_type_source, TERRAIN_TYPE_SOURCE_EXPLICIT)

  def test_prepare_scenario_world_layout_rejects_unknown_terrain_type(self) -> None:
    scenario = _sample_scenario()
    scenario["environment"]["terrain_type"] = "desert"

    with self.assertRaisesRegex(ValueError, "Unknown terrain_type"):
      prepare_scenario_world_layout(
        scenario,
        seed=14,
        rng=np.random.RandomState(14),
        compiled_template=None,
      )


if __name__ == "__main__":
  unittest.main()
