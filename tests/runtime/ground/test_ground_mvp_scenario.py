from __future__ import annotations

import json
import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from python.rl.tasking import bridge as tasking_bridge  # noqa: E402


_SCENARIO_PATH = resolve_repo_path(
    "scenarios",
    "ground",
    "ground_platoon_tasking_smoke_v1.json",
)
_DB_PATH = resolve_repo_path("examples", "config", "database")


class GroundMvpScenarioTests(unittest.TestCase):
    def _load_ground_mvp(self) -> tuple[ef_py.SimulationKernel, ScenarioLoader, int]:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))
        loader = ScenarioLoader(sim)
        agent_id = int(loader.load_scenario(_SCENARIO_PATH, seed=20260522))
        return sim, loader, agent_id

    def test_ground_mvp_scenario_loads_tasking_shell(self) -> None:
        sim, loader, agent_id = self._load_ground_mvp()

        self.assertGreater(agent_id, 0)
        self.assertEqual(agent_id, int(loader.entities["Blue_Ground_Platoon_Shell"]))
        self.assertIs(
            tasking_bridge.tasking_profile_for_loader(loader),
            tasking_bridge.resolve_tasking_profile("ground"),
        )

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
        self.assertEqual(int(task.task_group_id), 4301)
        self.assertEqual(int(task.supported_node_id), 4301)
        self.assertEqual(int(task.supporting_node_id), 4301)
        self.assertEqual(task.ground_task_mode, ef_py.GroundTaskMode.OccupyStatic)
        self.assertEqual(int(task.objective_area_id), 4301)
        self.assertEqual(int(task.objective_node_id), 4301)
        self.assertEqual(int(task.ground_commander_id), 4301)
        self.assertAlmostEqual(float(task.tactical_cadence_hz), 1.0)

        self.assertTrue(bool(intent.active))
        self.assertEqual(intent.service_profile, ef_py.ServiceProfile.Army)
        self.assertEqual(intent.task_family, ef_py.TaskFamily.Defend)
        self.assertEqual(intent.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
        self.assertEqual(intent.coordination_mode, ef_py.CoordinationMode.Independent)
        self.assertEqual(int(intent.tactical_unit_id), 4301)
        self.assertEqual(intent.ground_status_phase, ef_py.GroundStatusPhase.OccupyingStatic)
        self.assertEqual(intent.ground_task_mode, ef_py.GroundTaskMode.OccupyStatic)
        self.assertEqual(int(intent.objective_area_id), 4301)
        self.assertEqual(int(intent.objective_node_id), 4301)
        self.assertEqual(int(intent.ground_commander_id), 4301)
        self.assertAlmostEqual(float(intent.tactical_cadence_hz), 1.0)

        self.assertTrue(bool(report.active))
        self.assertEqual(report.service_profile, ef_py.ServiceProfile.Army)
        self.assertEqual(report.task_family, ef_py.TaskFamily.Defend)
        self.assertEqual(report.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
        self.assertEqual(report.coordination_mode, ef_py.CoordinationMode.Independent)
        self.assertEqual(int(report.tactical_unit_id), 4301)
        self.assertEqual(report.ground_status_phase, ef_py.GroundStatusPhase.OccupyingStatic)
        self.assertEqual(report.ground_task_mode, ef_py.GroundTaskMode.OccupyStatic)
        self.assertEqual(int(report.objective_area_id), 4301)
        self.assertEqual(int(report.objective_node_id), 4301)
        self.assertEqual(int(report.ground_commander_id), 4301)
        self.assertAlmostEqual(float(report.tactical_cadence_hz), 1.0)

    def test_ground_mvp_scenario_documents_compatibility_boundary(self) -> None:
        with open(_SCENARIO_PATH, "r", encoding="utf-8") as handle:
            scenario = json.load(handle)

        boundary = scenario["mvp_boundary"]
        entity = scenario["entities"][0]

        self.assertEqual(scenario["tasking_profile"], "ground")
        self.assertEqual(scenario["task_order"]["service_profile"], "Army")
        self.assertEqual(scenario["task_order"]["task_name"], "TASK_OCCUPY")
        self.assertEqual(entity["type"], "Aircraft")
        self.assertEqual(boundary["status"], "tasking_shell_only")
        self.assertEqual(boundary["compatibility_spawn_type"], "Aircraft")

        deferred = set(boundary["deferred_runtime_claims"])
        self.assertIn("runtime-loadable ground unit schema", deferred)
        self.assertIn("ground movement dynamics", deferred)
        self.assertIn("ground sensing, track fusion, or observation export", deferred)
        self.assertIn("direct fire, indirect fire, effects, damage, or suppression", deferred)
        self.assertIn("formal CommandPacket, ObservationPacket, or TrackPacket", deferred)

    def test_ground_mvp_mission_command_uses_ground_compatibility_shell(self) -> None:
        _sim, loader, _agent_id = self._load_ground_mvp()

        cmd = tasking_bridge.build_kernel_mission_command(loader)
        self.assertTrue(bool(cmd.active))
        self.assertEqual(int(cmd.command_code), int(loader.leader_intent.command_code))
        self.assertAlmostEqual(float(cmd.cmd_heading_deg), float(loader.leader_intent.cmd_heading_deg), places=6)
        self.assertAlmostEqual(float(cmd.cmd_altitude_m), float(loader.leader_intent.cmd_altitude_m), places=6)
        self.assertAlmostEqual(float(cmd.cmd_speed_mps), float(loader.leader_intent.cmd_speed_mps), places=6)
        self.assertEqual(int(cmd.formation_id), 0)
        self.assertFalse(bool(cmd.authorization_to_fire))
        self.assertEqual(cmd.ground_task_mode, ef_py.GroundTaskMode.OccupyStatic)
        self.assertEqual(int(cmd.objective_area_id), 4301)
        self.assertEqual(int(cmd.objective_node_id), 4301)
        self.assertEqual(int(cmd.ground_commander_id), 4301)
        self.assertAlmostEqual(float(cmd.tactical_cadence_hz), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
