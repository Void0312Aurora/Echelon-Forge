from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

try:  # noqa: E402
    import ef_py
except ModuleNotFoundError:  # pragma: no cover - local test env may not have the compiled runtime binding
    ef_py = None

if ef_py is not None:  # pragma: no branch
    from python.rl.tasking import bridge as tasking_bridge  # noqa: E402
    from python.rl.tasking import ground_adapter, leader_tasking  # noqa: E402
else:  # pragma: no cover - module-level fallback for collection in incomplete environments
    tasking_bridge = None
    ground_adapter = None
    leader_tasking = None


REPO_ROOT = Path(__file__).resolve().parents[3]


@unittest.skipIf(ef_py is None, "ef_py runtime binding is unavailable in the active interpreter")
class GroundRuntimeLifecycleBridgeTests(unittest.TestCase):
    def test_bridge_dispatches_explicit_ground_profile_without_air_only_fallback(self) -> None:
        loader = SimpleNamespace(
            scenario_data={"tasking_profile": "ground"},
            task_order=ef_py.TaskOrder(),
            mission_cmd={},
        )
        sentinel = object()

        with (
            patch.object(tasking_bridge._ground, "build_kernel_mission_command", return_value=sentinel) as ground_build,
            patch.object(tasking_bridge._air, "build_kernel_mission_command", side_effect=AssertionError("air path should not be used")),
            patch.object(leader_tasking, "build_kernel_mission_command", side_effect=AssertionError("direct leader_tasking path should not be used")),
        ):
            result = tasking_bridge.build_kernel_mission_command(loader)

        self.assertIs(result, sentinel)
        self.assertEqual(ground_build.call_count, 1)
        self.assertIs(tasking_bridge.tasking_profile_for_loader(loader), tasking_bridge.resolve_tasking_profile("ground"))

    def test_bridge_infers_ground_profile_from_army_service_profile(self) -> None:
        task = ef_py.TaskOrder()
        task.service_profile = ef_py.ServiceProfile.Army
        loader = SimpleNamespace(
            scenario_data={},
            task_order=task,
            mission_cmd={
                "command_code": 17,
                "target_heading": 63.0,
                "target_altitude": 120.0,
                "target_speed": 18.0,
                "formation_id": 9,
                "authorization_to_fire": True,
            },
        )

        profile = tasking_bridge.tasking_profile_for_loader(loader)
        cmd = tasking_bridge.build_kernel_mission_command(loader)

        self.assertIs(profile, tasking_bridge.resolve_tasking_profile("ground"))
        self.assertIs(profile.build_kernel_mission_command, ground_adapter.build_kernel_mission_command)
        self.assertIsNot(profile.build_kernel_mission_command, leader_tasking.build_kernel_mission_command)
        self.assertTrue(bool(cmd.active))
        self.assertEqual(int(cmd.command_code), 17)
        self.assertAlmostEqual(float(cmd.cmd_heading_deg), 63.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_altitude_m), 120.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_speed_mps), 18.0, places=6)
        self.assertEqual(int(cmd.formation_id), 9)
        self.assertTrue(bool(cmd.authorization_to_fire))

    def test_non_ground_profile_resolution_remains_compatible(self) -> None:
        air_loader = SimpleNamespace(
            scenario_data={"tasking_profile": "air"},
            task_order=ef_py.TaskOrder(),
            mission_cmd={},
        )
        naval_task = ef_py.TaskOrder()
        naval_task.service_profile = ef_py.ServiceProfile.Navy
        naval_loader = SimpleNamespace(
            scenario_data={},
            task_order=naval_task,
            mission_cmd={},
        )

        self.assertIs(tasking_bridge.tasking_profile_for_loader(air_loader), tasking_bridge.resolve_tasking_profile("air"))
        self.assertIs(tasking_bridge.tasking_profile_for_loader(naval_loader), tasking_bridge.resolve_tasking_profile("naval"))


class GroundRuntimeSourceBridgeTests(unittest.TestCase):
    def test_batch_envs_use_tasking_bridge_for_command_chain_sync(self) -> None:
        runtime_paths = [
            REPO_ROOT / "python" / "rl" / "runtime" / "world_batch_vec_env.py",
            REPO_ROOT / "python" / "rl" / "runtime" / "cooperative_world_batch_vec_env.py",
        ]
        for path in runtime_paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("from python.rl.tasking.bridge import build_kernel_mission_command", text)
            self.assertNotIn("from python.rl.tasking.leader_tasking import build_kernel_mission_command", text)
            self.assertIn("mission_command = build_kernel_mission_command(", text)
            self.assertIn("set_task_orders_batch", text)
            self.assertIn("set_leader_intents_batch", text)
            self.assertIn("set_pilot_reports_batch", text)


if __name__ == "__main__":
    unittest.main()
