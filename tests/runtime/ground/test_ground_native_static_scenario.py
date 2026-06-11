from __future__ import annotations

import json
import unittest
from pathlib import Path

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader # noqa: E402
from python.rl.tasking import bridge as tasking_bridge # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")
_SCENARIO_PATH = resolve_repo_path(
  "scenarios",
  "ground",
  "ground_platoon_native_static_occupy_v1.json",
)


class GroundNativeStaticScenarioTests(unittest.TestCase):
  def _load(self) -> tuple[dict, ef_py.SimulationKernel, ScenarioLoader, int]:
    path = Path(_SCENARIO_PATH)
    with path.open("r", encoding="utf-8") as handle:
      scenario = json.load(handle)

    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))
    loader = ScenarioLoader(sim)
    agent_id = int(loader.load_scenario(str(path), seed=20260605))
    return scenario, sim, loader, agent_id

  def test_native_static_scenario_loads_ground_identity_and_status_shell(self) -> None:
    scenario, sim, loader, agent_id = self._load()

    self.assertGreater(agent_id, 0)
    self.assertEqual(agent_id, int(loader.entities["Blue_Ground_Platoon_Native_Static_Occupy"]))
    self.assertIs(
      tasking_bridge.tasking_profile_for_loader(loader),
      tasking_bridge.resolve_tasking_profile("ground"),
    )
    self.assertEqual(scenario["entities"][0]["type"], "Ground_Platoon_MVP")
    self.assertEqual(sim.get_unit_type(agent_id), int(ef_py.UnitType.Ground))
    self.assertEqual(tuple(sim.get_unit_position(agent_id)), (75.0, -125.0, 0.0))
    self.assertEqual(tuple(sim.get_unit_velocity(agent_id)), (0.0, 0.0, 0.0))
    self.assertEqual(list(sim.get_unit_health(agent_id)), [100.0, 100.0])

    task = sim.get_task_order(agent_id)
    intent = sim.get_leader_intent(agent_id)
    report = sim.get_pilot_report(agent_id)

    self.assertTrue(bool(task.active))
    self.assertEqual(task.service_profile, ef_py.ServiceProfile.Army)
    self.assertEqual(task.task_family, ef_py.TaskFamily.Defend)
    self.assertEqual(task.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(task.command_relationship, ef_py.CommandRelationship.TACON)
    self.assertEqual(task.authority_scope, ef_py.AuthorityScope.Tactical)
    self.assertEqual(task.coordination_mode, ef_py.CoordinationMode.Independent)
    self.assertEqual(int(task.task_group_id), 4701)
    self.assertEqual(int(task.supported_node_id), 4701)
    self.assertEqual(int(task.supporting_node_id), 4701)

    for status in (intent, report):
      self.assertTrue(bool(status.active))
      self.assertEqual(status.service_profile, ef_py.ServiceProfile.Army)
      self.assertEqual(status.task_family, ef_py.TaskFamily.Defend)
      self.assertEqual(status.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
      self.assertEqual(status.coordination_mode, ef_py.CoordinationMode.Independent)
      self.assertEqual(int(status.task_group_id), 4701)
      self.assertEqual(int(status.tactical_unit_id), 4701)

  def test_native_static_scenario_documents_native_schema_without_movement_release(self) -> None:
    scenario, _sim, loader, _agent_id = self._load()

    boundary = scenario["mvp_boundary"]
    gradient = boundary["realism_gradient"]
    deferred = set(boundary["deferred_runtime_claims"]) | set(gradient["deferred_claims"])

    self.assertEqual(boundary["spawn_surface"], "native_ground_schema")
    self.assertEqual(boundary["runtime_spawn_type"], "Ground_Platoon_MVP")
    self.assertEqual(gradient["grade"], "G1")
    self.assertIn("spawned agent reports UnitType.Ground", gradient["validated_claims"])
    self.assertIn("ground movement dynamics", deferred)
    self.assertIn("route following or movement behavior", deferred)
    self.assertIn("terrain traversal, masking, cover, or line-of-sight", deferred)
    self.assertIn("ground sensing, track fusion, or observation export", deferred)
    self.assertIn("effects, damage, or suppression", deferred)

    cmd = tasking_bridge.build_kernel_mission_command(loader)
    self.assertTrue(bool(cmd.active))
    self.assertEqual(int(cmd.command_code), int(loader.leader_intent.command_code))
    self.assertAlmostEqual(float(cmd.cmd_altitude_m), 0.0, places=6)
    self.assertAlmostEqual(float(cmd.cmd_speed_mps), 0.0, places=6)
    self.assertFalse(bool(cmd.authorization_to_fire))


if __name__ == "__main__":
  unittest.main()
