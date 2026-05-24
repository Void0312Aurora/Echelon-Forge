from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from python.rl.tasking import bridge as tasking_bridge  # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")
_SCENARIOS = {
    "occupy": resolve_repo_path(
        "scenarios",
        "ground",
        "ground_platoon_static_occupy_v1.json",
    ),
    "support": resolve_repo_path(
        "scenarios",
        "ground",
        "ground_platoon_support_relationship_v1.json",
    ),
}


class GroundRealismGradientMvpScenarioTests(unittest.TestCase):
    def _load(self, key: str) -> tuple[dict[str, Any], ef_py.SimulationKernel, ScenarioLoader, int]:
        path = Path(_SCENARIOS[key])
        with path.open("r", encoding="utf-8") as handle:
            scenario = json.load(handle)

        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))
        loader = ScenarioLoader(sim)
        agent_id = int(loader.load_scenario(str(path), seed=20260524))
        return scenario, sim, loader, agent_id

    def _assert_ground_loader(self, scenario: dict[str, Any], loader: ScenarioLoader, agent_id: int) -> None:
        self.assertGreater(agent_id, 0)
        self.assertEqual(scenario["tasking_profile"], "ground")
        self.assertEqual(scenario["task_order"]["tasking_profile"], "ground")
        self.assertIs(
            tasking_bridge.tasking_profile_for_loader(loader),
            tasking_bridge.resolve_tasking_profile("ground"),
        )

    def _assert_g1_boundary(self, scenario: dict[str, Any]) -> None:
        boundary = scenario["mvp_boundary"]
        gradient = boundary["realism_gradient"]
        deferred = set(gradient["deferred_claims"])

        self.assertEqual(boundary["compatibility_spawn_type"], "Aircraft")
        self.assertEqual(gradient["grade"], "G1")
        self.assertIn("Aircraft spawn shell", gradient["compatibility_shell"])
        for claim in (
            "ground movement dynamics",
            "terrain traversal, masking, cover, or line-of-sight",
            "ground sensing, track fusion, or observation export",
            "direct fires",
            "indirect fires",
            "effects, damage, or suppression",
            "ObservationPacket",
            "TrackPacket",
        ):
            self.assertIn(claim, deferred)

    def _assert_army_status_shell(
        self,
        sim: ef_py.SimulationKernel,
        agent_id: int,
        *,
        expected_task_family: Any,
        expected_command_relationship: Any,
        expected_coordination_mode: Any,
        expected_task_group_id: int,
        expected_supported_node_id: int,
        expected_supporting_node_id: int,
    ) -> None:
        task = sim.get_task_order(agent_id)
        intent = sim.get_leader_intent(agent_id)
        report = sim.get_pilot_report(agent_id)

        self.assertTrue(bool(task.active))
        self.assertEqual(task.service_profile, ef_py.ServiceProfile.Army)
        self.assertEqual(task.task_family, expected_task_family)
        self.assertEqual(task.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
        self.assertEqual(task.command_relationship, expected_command_relationship)
        self.assertEqual(task.authority_scope, ef_py.AuthorityScope.Tactical)
        self.assertEqual(task.coordination_mode, expected_coordination_mode)
        self.assertEqual(int(task.task_group_id), expected_task_group_id)
        self.assertEqual(int(task.supported_node_id), expected_supported_node_id)
        self.assertEqual(int(task.supporting_node_id), expected_supporting_node_id)

        for status in (intent, report):
            self.assertTrue(bool(status.active))
            self.assertEqual(status.service_profile, ef_py.ServiceProfile.Army)
            self.assertEqual(status.task_family, expected_task_family)
            self.assertEqual(status.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
            self.assertEqual(status.coordination_mode, expected_coordination_mode)
            self.assertEqual(int(status.task_group_id), expected_task_group_id)
            self.assertEqual(int(status.tactical_unit_id), expected_supporting_node_id)

    def test_ground_static_occupy_g1_boundary_and_semantics(self) -> None:
        scenario, sim, loader, agent_id = self._load("occupy")

        self._assert_ground_loader(scenario, loader, agent_id)
        self._assert_g1_boundary(scenario)
        self.assertEqual(scenario["task_order"]["service_profile"], "Army")
        self.assertEqual(scenario["task_order"]["task_name"], "TASK_OCCUPY")
        self.assertEqual(scenario["entities"][0]["type"], "Aircraft")
        self.assertEqual(scenario["entities"][0]["pos"], [100.0, 100.0, 0.0])
        self.assertEqual(scenario["environment"]["zones"][0]["name"], "ObjectiveEagle")

        self._assert_army_status_shell(
            sim,
            agent_id,
            expected_task_family=ef_py.TaskFamily.Defend,
            expected_command_relationship=ef_py.CommandRelationship.TACON,
            expected_coordination_mode=ef_py.CoordinationMode.Independent,
            expected_task_group_id=4401,
            expected_supported_node_id=4401,
            expected_supporting_node_id=4401,
        )

    def test_ground_support_relationship_g1_boundary_and_semantics(self) -> None:
        scenario, sim, loader, agent_id = self._load("support")

        self._assert_ground_loader(scenario, loader, agent_id)
        self._assert_g1_boundary(scenario)
        self.assertEqual(scenario["task_order"]["service_profile"], "Army")
        self.assertEqual(scenario["task_order"]["task_name"], "TASK_SUPPORT")
        self.assertEqual(scenario["entities"][0]["type"], "Aircraft")
        self.assertEqual(int(scenario["task_order"]["supported_node_id"]), 4601)
        self.assertEqual(int(scenario["task_order"]["supporting_node_id"]), 4501)

        self._assert_army_status_shell(
            sim,
            agent_id,
            expected_task_family=ef_py.TaskFamily.Defend,
            expected_command_relationship=ef_py.CommandRelationship.Support,
            expected_coordination_mode=ef_py.CoordinationMode.Support,
            expected_task_group_id=4501,
            expected_supported_node_id=4601,
            expected_supporting_node_id=4501,
        )


if __name__ == "__main__":
    unittest.main()
