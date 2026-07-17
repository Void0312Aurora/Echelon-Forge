from __future__ import annotations

import json
import tempfile
from typing import Any
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import torch # noqa: E402,F401

import ef_py # noqa: E402

from gym_envs.universal_env_parts import NAVAL_STATION3_ACTION_FAMILY # noqa: E402
from python.rl.runtime.world_batch import command_chain_cache # noqa: E402
from python.rl.runtime.world_batch.command_chain_cache import ( # noqa: E402
  project_world_leader_intent_maintained_assignment,
  project_world_mission_command_maintained_assignment,
  project_world_pilot_report_maintained_assignment,
  project_world_task_order_maintained_assignment,
)
import python.rl.runtime.world_batch.adapter as world_batch_adapter_module # noqa: E402
import python.rl.runtime.world_batch_vec_env as vec_env_module # noqa: E402
from python.rl.policy_algo.device_dict_rollout_buffer import DeviceDictRolloutBuffer # noqa: E402
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO # noqa: E402
from python.rl.runtime.shared_memory_vec_env import SharedMemorySubprocVecEnv # noqa: E402
from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv # noqa: E402
from python.mission_obs_taxonomy import ( # noqa: E402
  mission_observation_dim,
  mission_observation_field_index,
)
from tests.support._leader_env_runtime_test_support import CounterDictEnv # noqa: E402
from tests.support._world_batch_vec_env_test_support import ( # noqa: E402
  _controller_runtime_state_matches_loader_state,
  _inline_air_combat_scripted_opponent_scenario,
  _inline_vec_env_maritime_scenario,
  _inline_vec_env_route_transition_scenario,
  _inline_vec_env_scenario,
  _legacy_step_result_state_with_poisoned_report_fields,
)


class WorldBatchVecEnvCommandChainTests(unittest.TestCase):
  def test_command_chain_cache_leader_intent_snapshot_uses_named_owner_slice_projections(self) -> None:
    intent = ef_py.LeaderIntent()
    intent.command_code = 3
    intent.cmd_heading_deg = 91.0
    intent.cmd_altitude_m = 1250.0
    intent.cmd_speed_mps = 210.0
    intent.phase_id = ef_py.LeaderPhase.Reposition
    intent.formation_id = 17
    intent.form_offset_x = 120.0
    intent.recovery_base_id = 88
    intent.warfare_role_code = 5
    intent.officer_in_tactical_command = 7001

    snapshot = command_chain_cache.leader_intent_snapshot(intent)

    self.assertIsNotNone(snapshot)
    assert snapshot is not None
    projection_names = tuple(name for name, _fields in snapshot)
    self.assertEqual(
      projection_names,
      (
        "leader_intent_shared_core",
        "leader_intent_air_owner_slice",
        "leader_intent_naval_owner_slice",
      ),
    )
    projection_map = {name: dict(fields) for name, fields in snapshot}
    self.assertEqual(projection_map["leader_intent_shared_core"]["command_code"], 3)
    self.assertEqual(projection_map["leader_intent_shared_core"]["cmd_heading_deg"], 91.0)
    self.assertEqual(projection_map["leader_intent_air_owner_slice"]["phase_id"], ef_py.LeaderPhase.Reposition)
    self.assertEqual(projection_map["leader_intent_air_owner_slice"]["formation_id"], 17)
    self.assertEqual(projection_map["leader_intent_air_owner_slice"]["recovery_base_id"], 88)
    self.assertEqual(projection_map["leader_intent_naval_owner_slice"]["warfare_role_code"], 5)
    self.assertEqual(projection_map["leader_intent_naval_owner_slice"]["officer_in_tactical_command"], 7001)
    self.assertEqual(
      tuple(projection_map["leader_intent_shared_core"].keys()),
      tuple(name for name in dir(ef_py.leader_intent_shared_core(intent)) if not name.startswith("_")),
    )
    self.assertEqual(
      tuple(projection_map["leader_intent_air_owner_slice"].keys()),
      tuple(name for name in dir(ef_py.leader_intent_air_owner_slice(intent)) if not name.startswith("_")),
    )
    self.assertEqual(
      tuple(projection_map["leader_intent_naval_owner_slice"].keys()),
      tuple(name for name in dir(ef_py.leader_intent_naval_owner_slice(intent)) if not name.startswith("_")),
    )

  def test_command_chain_cache_pilot_report_snapshot_uses_named_owner_slice_projections(self) -> None:
    report = ef_py.PilotReport()
    report.report_type = ef_py.CommMsgType.ACK_CANT_DO
    report.sender_id = 101
    report.status_value = 2.5
    report.element_id = 55
    report.phase_id = 8
    report.formation_role_id = 3
    report.formation_error_m = 12.0
    report.warfare_role_code = 9
    report.officer_in_tactical_command = 9002

    snapshot = command_chain_cache.pilot_report_snapshot(report)

    self.assertIsNotNone(snapshot)
    assert snapshot is not None
    projection_names = tuple(name for name, _fields in snapshot)
    self.assertEqual(
      projection_names,
      (
        "pilot_report_shared_core",
        "pilot_report_air_owner_slice",
        "pilot_report_naval_owner_slice",
      ),
    )
    projection_map = {name: dict(fields) for name, fields in snapshot}
    self.assertEqual(
      projection_map["pilot_report_shared_core"]["report_type"],
      ef_py.CommMsgType.ACK_CANT_DO,
    )
    self.assertEqual(projection_map["pilot_report_shared_core"]["sender_id"], 101)
    self.assertEqual(projection_map["pilot_report_air_owner_slice"]["element_id"], 55)
    self.assertEqual(projection_map["pilot_report_air_owner_slice"]["phase_id"], 8)
    self.assertEqual(projection_map["pilot_report_air_owner_slice"]["formation_role_id"], 3)
    self.assertEqual(projection_map["pilot_report_naval_owner_slice"]["warfare_role_code"], 9)
    self.assertEqual(projection_map["pilot_report_naval_owner_slice"]["officer_in_tactical_command"], 9002)
    self.assertEqual(
      tuple(projection_map["pilot_report_shared_core"].keys()),
      tuple(name for name in dir(ef_py.pilot_report_shared_core(report)) if not name.startswith("_")),
    )
    self.assertEqual(
      tuple(projection_map["pilot_report_air_owner_slice"].keys()),
      tuple(name for name in dir(ef_py.pilot_report_air_owner_slice(report)) if not name.startswith("_")),
    )
    self.assertEqual(
      tuple(projection_map["pilot_report_naval_owner_slice"].keys()),
      tuple(name for name in dir(ef_py.pilot_report_naval_owner_slice(report)) if not name.startswith("_")),
    )

  def test_command_chain_cache_task_order_snapshot_uses_named_owner_slice_projections(self) -> None:
    order = ef_py.TaskOrder()
    order.task_id = 8
    order.active = True
    order.priority = 6
    order.issue_time_s = 12.5
    order.element_id = 13
    order.package_id = 21
    order.recovery_base_id = 22
    order.recovery_runway_id = 23
    order.recovery_approach_type = ef_py.RecoveryApproachType.ILS
    order.takeoff_procedure_id = ef_py.TakeoffProcedureType.Interval
    order.takeoff_clearance_id = ef_py.TakeoffClearanceState.ClearedForTakeoff
    order.takeoff_interval_s = 17.5
    order.runway_slot_id = ef_py.RunwaySlotPosition.Right
    order.warfare_role_code = 4
    order.officer_in_tactical_command = 8004

    snapshot = command_chain_cache.task_order_snapshot(order)

    self.assertIsNotNone(snapshot)
    assert snapshot is not None
    projection_names = tuple(name for name, _fields in snapshot)
    self.assertEqual(
      projection_names,
      (
        "task_order_shared_core",
        "task_order_air_owner_slice",
        "task_order_naval_owner_slice",
      ),
    )
    projection_map = {name: dict(fields) for name, fields in snapshot}
    self.assertEqual(projection_map["task_order_shared_core"]["task_id"], 8)
    self.assertEqual(projection_map["task_order_shared_core"]["active"], True)
    self.assertEqual(projection_map["task_order_shared_core"]["priority"], 6)
    self.assertEqual(projection_map["task_order_shared_core"]["issue_time_s"], 12.5)
    self.assertEqual(projection_map["task_order_air_owner_slice"]["element_id"], 13)
    self.assertEqual(projection_map["task_order_air_owner_slice"]["package_id"], 21)
    self.assertEqual(projection_map["task_order_air_owner_slice"]["recovery_base_id"], 22)
    self.assertEqual(projection_map["task_order_air_owner_slice"]["takeoff_interval_s"], 17.5)
    self.assertEqual(projection_map["task_order_naval_owner_slice"]["warfare_role_code"], 4)
    self.assertEqual(projection_map["task_order_naval_owner_slice"]["officer_in_tactical_command"], 8004)
    self.assertEqual(
      tuple(projection_map["task_order_shared_core"].keys()),
      tuple(name for name in dir(ef_py.task_order_shared_core(order)) if not name.startswith("_")),
    )
    self.assertEqual(
      tuple(projection_map["task_order_air_owner_slice"].keys()),
      tuple(name for name in dir(ef_py.task_order_air_owner_slice(order)) if not name.startswith("_")),
    )
    self.assertEqual(
      tuple(projection_map["task_order_naval_owner_slice"].keys()),
      tuple(name for name in dir(ef_py.task_order_naval_owner_slice(order)) if not name.startswith("_")),
    )

  def test_world_batch_vec_env_applies_worker_thread_config(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
        worker_threads=1,
      )
      try:
        self.assertEqual(int(vec_env.runtime_facade.worker_threads()), 1)
        self.assertEqual(int(vec_env.runtime_facade.effective_worker_threads()), 1)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_steps_and_auto_resets(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=True,
      )
      try:
        vec_env.seed(123)
        obs = vec_env.reset()
        self.assertEqual(obs["instruments"].shape, (2, 42))
        self.assertEqual(obs["proprio"].shape, (2, 17))
        self.assertTrue(np.allclose(obs["proprio"], 0.0))

        obs, rewards, dones, infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
        self.assertEqual(rewards.shape, (2,))
        self.assertTrue(np.all(dones == np.asarray([True, True])))
        self.assertIn("terminal_observation", infos[0])
        self.assertIn("episode", infos[0])
        self.assertGreaterEqual(int(infos[0]["episode"]["l"]), 1)
        self.assertTrue(np.allclose(obs["proprio"], 0.0))
        self.assertEqual(vec_env.reset_infos, [{}, {}])
      finally:
        vec_env.close()

  def test_world_batch_vec_env_uses_air_combat_c2_roe_python_owned_mission_observation(self) -> None:
    mode = "air_combat_c2_roe_v1"
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["mission_command"].update(
        {
          "roe_state": 3,
          "wcs_state": 2,
          "authorization_to_fire": True,
          "engage_order_state": 2,
          "shot_policy_state": 1,
          "shot_budget_remaining": 1,
          "pending_assessment": True,
        }
      )
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
        mission_obs_mode=mode,
      )
      try:
        obs = vec_env.reset()
        mission = np.asarray(obs["mission"], dtype=np.float32)
        self.assertEqual(mission.shape, (2, mission_observation_dim(mode)))
        self.assertTrue(
          np.allclose(mission[:, mission_observation_field_index(mode, "roe_state")], 3.0)
        )
        self.assertTrue(
          np.allclose(mission[:, mission_observation_field_index(mode, "wcs_state")], 2.0)
        )
        self.assertTrue(
          np.allclose(mission[:, mission_observation_field_index(mode, "authorization_to_fire")], 1.0)
        )
        self.assertTrue(
          np.allclose(mission[:, mission_observation_field_index(mode, "shot_policy_state")], 1.0)
        )
        self.assertTrue(
          np.allclose(mission[:, mission_observation_field_index(mode, "shot_budget_remaining")], 1.0)
        )
        self.assertTrue(
          np.allclose(mission[:, mission_observation_field_index(mode, "pending_assessment")], 1.0)
        )
      finally:
        vec_env.close()

  def test_world_batch_vec_env_reset_uses_runtime_facade_compatibly(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
      )
      try:
        packet_requests: list[object] = []
        original_read_observation_packet = vec_env._runtime_adapter.read_observation_packet

        def _track_read_observation_packet(refs, **kwargs):
          packet_requests.append(kwargs)
          return original_read_observation_packet(refs, **kwargs)

        def _unexpected_get_agent_observations_batch(_refs):
          raise AssertionError("maintained vec-env observation reads should use export_observation_packet()")

        def _unexpected_get_instrument_states_batch(_refs):
          raise AssertionError("maintained vec-env observation reads should use export_observation_packet()")

        vec_env._runtime_adapter.read_observation_packet = _track_read_observation_packet # type: ignore[method-assign]
        vec_env._runtime_adapter.get_agent_observations_batch = _unexpected_get_agent_observations_batch # type: ignore[method-assign]
        vec_env._runtime_adapter.get_instrument_states_batch = _unexpected_get_instrument_states_batch # type: ignore[method-assign]

        self.assertTrue(hasattr(vec_env, "runtime_facade"))
        self.assertIsNotNone(vec_env.runtime_facade)
        self.assertEqual(int(vec_env.runtime_facade.world_count()), 2)

        vec_env.seed(123)
        obs = vec_env.reset()
        _obs, _rewards, _dones, _infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))

        self.assertEqual(obs["instruments"].shape, (2, 42))
        self.assertEqual(obs["contacts"].shape[0], 2)
        self.assertEqual(obs["mission"].shape[0], 2)
        self.assertIsNotNone(vec_env.envs[0].agent_id)
        self.assertIsNotNone(vec_env.envs[1].agent_id)
        self.assertGreaterEqual(len(packet_requests), 2)
        self.assertTrue(
          all(bool(request.get("include_agent_observations", False)) for request in packet_requests)
        )
        self.assertTrue(
          all(bool(request.get("include_instrument_states", False)) for request in packet_requests)
        )
        self.assertTrue(all("include_mission_commands" not in request for request in packet_requests))
        self.assertTrue(all("include_task_orders" not in request for request in packet_requests))
        self.assertTrue(all("include_task_order_contracts" not in request for request in packet_requests))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_skips_stable_command_chain_exports(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(7)

        mission_calls: list[int] = []
        task_calls: list[int] = []
        intent_calls: list[int] = []
        report_calls: list[int] = []

        original_set_mission = vec_env._runtime_adapter.set_mission_commands_maintained_batch
        original_set_task = vec_env._runtime_adapter.set_task_orders_maintained_batch
        original_set_intent = vec_env._runtime_adapter.set_leader_intents_maintained_batch
        original_set_report = vec_env._runtime_adapter.set_pilot_reports_maintained_batch
        original_project_mission = vec_env_module.project_world_mission_command_maintained_assignment
        original_project_task = vec_env_module.project_world_task_order_maintained_assignment
        original_project_intent = vec_env_module.project_world_leader_intent_maintained_assignment
        original_project_report = vec_env_module.project_world_pilot_report_maintained_assignment
        projection_calls: list[tuple[str, int, int]] = []

        def _track_mission(assignments):
          materialized = list(assignments)
          self.assertTrue(all(hasattr(assignment, "mission_command") for assignment in materialized))
          mission_calls.append(len(materialized))
          return original_set_mission(materialized)

        def _track_task(assignments):
          materialized = list(assignments)
          self.assertTrue(all(hasattr(assignment, "task_order") for assignment in materialized))
          task_calls.append(len(materialized))
          return original_set_task(materialized)

        def _track_intent(assignments):
          materialized = list(assignments)
          self.assertTrue(all(hasattr(assignment, "leader_intent") for assignment in materialized))
          intent_calls.append(len(materialized))
          return original_set_intent(materialized)

        def _track_report(assignments):
          materialized = list(assignments)
          self.assertTrue(all(hasattr(assignment, "pilot_report") for assignment in materialized))
          report_calls.append(len(materialized))
          return original_set_report(materialized)

        def _track_project_mission(assignment, *, world_index, entity_id, compatibility_mission_command_shell):
          projection_calls.append(("mission", int(world_index), int(entity_id)))
          return original_project_mission(
            assignment,
            world_index=world_index,
            entity_id=entity_id,
            compatibility_mission_command_shell=compatibility_mission_command_shell,
          )

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

        vec_env._runtime_adapter.set_mission_commands_maintained_batch = _track_mission # type: ignore[method-assign]
        vec_env._runtime_adapter.set_task_orders_maintained_batch = _track_task # type: ignore[method-assign]
        vec_env._runtime_adapter.set_leader_intents_maintained_batch = _track_intent # type: ignore[method-assign]
        vec_env._runtime_adapter.set_pilot_reports_maintained_batch = _track_report # type: ignore[method-assign]
        vec_env_module.project_world_mission_command_maintained_assignment = _track_project_mission # type: ignore[assignment]
        vec_env_module.project_world_task_order_maintained_assignment = _track_project_task # type: ignore[assignment]
        vec_env_module.project_world_leader_intent_maintained_assignment = _track_project_intent # type: ignore[assignment]
        vec_env_module.project_world_pilot_report_maintained_assignment = _track_project_report # type: ignore[assignment]

        try:
          vec_env.reset()
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
          self.assertFalse(hasattr(vec_env._runtime_adapter, "set_mission_commands_batch"))
          self.assertFalse(hasattr(vec_env._runtime_adapter, "set_task_orders_batch"))
          self.assertFalse(hasattr(vec_env._runtime_adapter, "set_leader_intents_batch"))
          self.assertFalse(hasattr(vec_env._runtime_adapter, "set_pilot_reports_batch"))
          self.assertTrue(any(kind == "mission" for kind, _world_index, _entity_id in projection_calls))
          self.assertTrue(any(kind == "task" for kind, _world_index, _entity_id in projection_calls))
          self.assertTrue(any(kind == "intent" for kind, _world_index, _entity_id in projection_calls))
          self.assertTrue(any(kind == "report" for kind, _world_index, _entity_id in projection_calls))

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
          vec_env_module.project_world_mission_command_maintained_assignment = original_project_mission # type: ignore[assignment]
          vec_env_module.project_world_task_order_maintained_assignment = original_project_task # type: ignore[assignment]
          vec_env_module.project_world_leader_intent_maintained_assignment = original_project_intent # type: ignore[assignment]
          vec_env_module.project_world_pilot_report_maintained_assignment = original_project_report # type: ignore[assignment]
      finally:
        vec_env.close()

  def test_world_batch_vec_env_reset_rearms_command_chain_exports(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(7)

        mission_calls: list[int] = []
        original_set_mission = vec_env._runtime_adapter.set_mission_commands_maintained_batch

        def _track_mission(assignments):
          materialized = list(assignments)
          mission_calls.append(len(materialized))
          return original_set_mission(materialized)

        vec_env._runtime_adapter.set_mission_commands_maintained_batch = _track_mission # type: ignore[method-assign]

        vec_env.reset()
        first_total = sum(mission_calls)
        self.assertGreater(first_total, 0)

        vec_env.reset()
        self.assertGreater(sum(mission_calls), first_total)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_batch_runtime_surface_is_removed_at_runtime(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        with self.assertRaises(AttributeError):
          _ = vec_env.batch_runtime
      finally:
        vec_env.close()

  def test_world_batch_vec_env_exposes_runtime_facade_for_diagnostics(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        self.assertIs(vec_env.runtime_facade, vec_env._runtime_adapter.facade)
        self.assertEqual(int(vec_env.runtime_facade.world_count()), 1)
        self.assertTrue(hasattr(vec_env.runtime_facade, "export_execution_episode_states"))
        self.assertTrue(hasattr(vec_env.runtime_facade, "execution_episode_ready"))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_loader_construction_does_not_require_raw_world_access(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      original_factory = vec_env_module._RuntimeFacadeAdapter._scenario_loader_runtime
      touched_fallback_calls: list[str] = []

      def _proxy_factory(adapter, env_idx):
        class _NoWorldConstructionProxy:
          def get_agent_observation(self, entity_id):
            return adapter.get_agent_observation(int(env_idx), int(entity_id))

          def get_instrument_state(self, entity_id):
            return adapter.get_instrument_state(int(env_idx), int(entity_id))

          def get_time_step(self):
            return adapter.get_time_step(int(env_idx))

          def set_mission_command(self, entity_id, command):
            assignment = ef_py.WorldMissionCommandMaintainedAssignment()
            project_world_mission_command_maintained_assignment(
              assignment,
              world_index=int(env_idx),
              entity_id=int(entity_id),
              compatibility_mission_command_shell=command,
            )
            adapter.set_mission_commands_maintained_batch([assignment])

          def set_task_order(self, entity_id, order):
            assignment = ef_py.WorldTaskOrderMaintainedAssignment()
            project_world_task_order_maintained_assignment(
              assignment,
              world_index=int(env_idx),
              entity_id=int(entity_id),
              compatibility_task_order_shell=order,
            )
            adapter.set_task_orders_maintained_batch([assignment])

          def set_leader_intent(self, entity_id, intent):
            assignment = ef_py.WorldLeaderIntentMaintainedAssignment()
            project_world_leader_intent_maintained_assignment(
              assignment,
              world_index=int(env_idx),
              entity_id=int(entity_id),
              compatibility_intent_shell=intent,
            )
            adapter.set_leader_intents_maintained_batch([assignment])

          def set_pilot_report(self, entity_id, report):
            assignment = ef_py.WorldPilotReportMaintainedAssignment()
            project_world_pilot_report_maintained_assignment(
              assignment,
              world_index=int(env_idx),
              entity_id=int(entity_id),
              compatibility_report_shell=report,
            )
            adapter.set_pilot_reports_maintained_batch([assignment])

          def __getattr__(self, name):
            touched_fallback_calls.append(str(name))
            raise AssertionError(f"loader construction/reset should not require fallback world method {name}")

        return _NoWorldConstructionProxy()

      vec_env_module._RuntimeFacadeAdapter._scenario_loader_runtime = _proxy_factory
      try:
        vec_env = WorldBatchVecEnv(
          scenario_path=scenario_path,
          n_envs=1,
          include_visual=False,
          include_proprio=False,
        )
        try:
          vec_env.seed(123)
          obs = vec_env.reset()
          self.assertEqual(obs["instruments"].shape, (1, 42))
          self.assertEqual(touched_fallback_calls, [])
        finally:
          vec_env.close()
      finally:
        vec_env_module._RuntimeFacadeAdapter._scenario_loader_runtime = original_factory

  def test_world_batch_adapter_loader_runtime_task_order_write_routes_through_maintained_helper(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)
    original_project_task = world_batch_adapter_module.project_world_task_order_maintained_assignment
    project_calls: list[tuple[int, int, Any]] = []
    assignment_batches: list[list[Any]] = []

    def _track_project_task(assignment, *, world_index, entity_id, compatibility_task_order_shell):
      project_calls.append((int(world_index), int(entity_id), compatibility_task_order_shell))
      return original_project_task(
        assignment,
        world_index=world_index,
        entity_id=entity_id,
        compatibility_task_order_shell=compatibility_task_order_shell,
      )

    def _track_set_task_orders_batch(assignments):
      materialized = list(assignments)
      assignment_batches.append(materialized)

    world_batch_adapter_module.project_world_task_order_maintained_assignment = _track_project_task # type: ignore[assignment]
    adapter.set_task_orders_maintained_batch = _track_set_task_orders_batch # type: ignore[method-assign]
    try:
      proxy = adapter._scenario_loader_runtime(0)
      order = ef_py.TaskOrder()
      order.task_id = 23

      proxy.set_task_order(91, order)

      self.assertFalse(hasattr(adapter, "set_task_orders_batch"))
      self.assertEqual(project_calls, [(0, 91, order)])
      self.assertEqual(len(assignment_batches), 1)
      self.assertEqual(len(assignment_batches[0]), 1)
      assignment = assignment_batches[0][0]
      self.assertEqual(int(assignment.world_index), 0)
      self.assertEqual(int(assignment.entity_id), 91)
      self.assertEqual(int(assignment.task_order.shared_core.task_id), 23)
    finally:
      world_batch_adapter_module.project_world_task_order_maintained_assignment = original_project_task # type: ignore[assignment]

  def test_world_batch_adapter_scripted_fire_uses_launch_request_not_pilot_action(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)
    proxy = adapter._scenario_loader_runtime(0)
    mission_batches: list[list[Any]] = []
    launch_batches: list[list[Any]] = []
    pilot_batches: list[list[Any]] = []

    class _Observation:
      health = 1.0

    adapter.get_time_step = lambda _world_index: 0.05 # type: ignore[method-assign]
    adapter.get_agent_observation = lambda _world_index, _entity_id: _Observation() # type: ignore[method-assign]

    def _capture_mission(assignments):
      mission_batches.append(list(assignments))

    def _capture_launch(requests):
      materialized = list(requests)
      launch_batches.append(materialized)
      event = ef_py.LaunchEvent()
      event.request_id = int(materialized[0].request_id)
      event.accepted = True
      event.has_spawned_munition = True
      event.spawned_munition.world_index = int(materialized[0].shooter.world_index)
      event.spawned_munition.entity_id = 9101
      return [event]

    def _capture_pilot(assignments):
      pilot_batches.append(list(assignments))

    adapter.set_mission_commands_maintained_batch = _capture_mission # type: ignore[method-assign]
    adapter.apply_launch_requests_batch = _capture_launch # type: ignore[method-assign]
    adapter.set_pilot_actions_batch = _capture_pilot # type: ignore[method-assign]

    missile_id = proxy.fire_missile(17, 23)

    self.assertEqual(missile_id, 9101)
    self.assertEqual(len(mission_batches), 1)
    self.assertEqual(len(launch_batches), 1)
    self.assertEqual(pilot_batches, [])
    request = launch_batches[0][0]
    self.assertEqual(int(request.shooter.world_index), 0)
    self.assertEqual(int(request.shooter.entity_id), 17)
    self.assertEqual(int(request.target_entity.entity_id), 23)
    self.assertTrue(bool(request.has_target_entity))
    self.assertEqual(str(request.authority), "scripted_opponent")

  def test_world_batch_vec_env_skips_command_sync_for_inactive_terminal_agent(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(5)
        vec_env.reset()
        handle = vec_env.envs[0]

        class _InactiveTruth:
          health = 0.0

        handle.last_truth = _InactiveTruth()
        calls: list[str] = []
        vec_env._runtime_adapter.set_mission_commands_maintained_batch = ( # type: ignore[method-assign]
          lambda assignments: calls.append(f"mission:{len(list(assignments))}")
        )
        vec_env._runtime_adapter.set_task_orders_maintained_batch = ( # type: ignore[method-assign]
          lambda assignments: calls.append(f"task:{len(list(assignments))}")
        )
        vec_env._runtime_adapter.set_leader_intents_maintained_batch = ( # type: ignore[method-assign]
          lambda assignments: calls.append(f"intent:{len(list(assignments))}")
        )
        vec_env._runtime_adapter.set_pilot_reports_maintained_batch = ( # type: ignore[method-assign]
          lambda assignments: calls.append(f"report:{len(list(assignments))}")
        )

        vec_env._sync_command_chain_batch([0])

        self.assertEqual(calls, [])
      finally:
        vec_env.close()

  def test_world_batch_adapter_legacy_task_order_batch_writer_is_removed(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)

    self.assertFalse(hasattr(adapter, "set_task_orders_batch"))
    self.assertFalse(hasattr(adapter, "set_task_orders_batch_compatibility"))

  def test_world_batch_adapter_capability_snapshot_tracks_facade_swaps(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)

    class _TaskOrderCapableFacade:
      def __init__(self) -> None:
        self.batches: list[list[Any]] = []

      def set_task_orders_maintained_batch(self, assignments):
        self.batches.append(list(assignments))

    task_capable = _TaskOrderCapableFacade()
    adapter.facade = task_capable # type: ignore[assignment]

    self.assertTrue(adapter.capabilities.has_set_task_orders_maintained_batch)
    adapter.set_task_orders_maintained_batch([])
    self.assertEqual(task_capable.batches, [[]])

    class _TaskOrderMissingFacade:
      def set_task_orders_batch(self, assignments):
        raise AssertionError("legacy task-order fallback must not be probed")

    adapter.facade = _TaskOrderMissingFacade() # type: ignore[assignment]

    self.assertFalse(adapter.capabilities.has_set_task_orders_maintained_batch)
    with self.assertRaisesRegex(RuntimeError, "requires maintained TaskOrder batch bindings"):
      adapter.set_task_orders_maintained_batch([])

  def test_world_batch_adapter_step_worlds_uses_facade_batch_step_without_raw_runtime_escape(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(2)

    class _FacadeStepOnly:
      def __init__(self) -> None:
        self.step_batch_calls = 0

      def step_batch(self):
        self.step_batch_calls += 1

      def world_count(self):
        return 2

      def runtime(self):
        raise AssertionError("maintained step_worlds must not request raw facade.runtime_compatibility_quarantine()")

    facade = _FacadeStepOnly()
    adapter.facade = facade # type: ignore[assignment]

    adapter.step_worlds([0, 1])

    self.assertEqual(facade.step_batch_calls, 1)

  def test_world_batch_adapter_step_worlds_rejects_partial_raw_runtime_step(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(2)

    class _FacadeWithRawRuntime:
      def step_batch(self):
        raise AssertionError("partial step should not be widened silently")

      def world_count(self):
        return 2

      def runtime(self):
        raise AssertionError("partial maintained step must fail closed before raw runtime")

    adapter.facade = _FacadeWithRawRuntime() # type: ignore[assignment]

    with self.assertRaisesRegex(RuntimeError, "requires a full facade-owned batch step"):
      adapter.step_worlds([1])

  def test_world_batch_adapter_maintained_window_authorizes_explicit_facade_observation_provenance(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)

    class _FacadeWindow:
      def __init__(self) -> None:
        self.requests: list[Any] = []

      def run_window(self, request):
        self.requests.append(request)
        result = ef_py.RuntimeWindowResult()
        result.observation_packet = ef_py.ObservationBatchPacket()
        result.engagement_packet = ef_py.EngagementEventPacket()
        return result

    facade = _FacadeWindow()
    adapter.facade = facade # type: ignore[assignment]
    action = ef_py.PilotAction()
    action.throttle = 0.75

    evidence = adapter.run_maintained_window(
      world_index=0,
      entity_id=42,
      pilot_action=action,
      input_snapshot_version="obs:0:42:7",
      information_state_label="facade_observation_packet",
      decision_model_id="blue-policy",
    )

    self.assertIsNotNone(evidence)
    self.assertEqual(len(facade.requests), 1)
    action_request = list(facade.requests[0].action_requests)[0]
    self.assertEqual(str(action_request.input_snapshot_version), "obs:0:42:7")
    self.assertEqual(str(action_request.action_intent.action_interface.kind), "PilotActionAssignment")
    self.assertEqual(str(action_request.action_intent.action_interface.payload_type), "pilot_action")
    self.assertEqual(str(action_request.action_intent.action_family), "direct_control")

  def test_world_batch_adapter_maintained_window_accepts_explicit_naval_action_family_while_using_pilot_action_transport(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)

    class _FacadeWindow:
      def __init__(self) -> None:
        self.requests: list[Any] = []

      def run_window(self, request):
        self.requests.append(request)
        result = ef_py.RuntimeWindowResult()
        result.observation_packet = ef_py.ObservationBatchPacket()
        result.engagement_packet = ef_py.EngagementEventPacket()
        return result

    facade = _FacadeWindow()
    adapter.facade = facade # type: ignore[assignment]

    evidence = adapter.run_maintained_window(
      world_index=0,
      entity_id=42,
      pilot_action=ef_py.PilotAction(),
      input_snapshot_version="obs:0:42:8",
      information_state_label="facade_observation_packet",
      action_family=NAVAL_STATION3_ACTION_FAMILY,
      decision_model_id="naval-station-policy",
    )

    self.assertIsNotNone(evidence)
    self.assertEqual(len(facade.requests), 1)
    action_request = list(facade.requests[0].action_requests)[0]
    self.assertEqual(str(action_request.action_intent.action_family), NAVAL_STATION3_ACTION_FAMILY)
    self.assertEqual(str(action_request.action_intent.action_interface.kind), "PilotActionAssignment")
    self.assertEqual(str(action_request.action_intent.action_interface.payload_type), "pilot_action")

  def test_world_batch_adapter_maintained_window_rejects_compatibility_provenance_label(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)

    class _FacadeWindow:
      def run_window(self, request):
        raise AssertionError("authorization should fail before runtime window execution")

    adapter.facade = _FacadeWindow() # type: ignore[assignment]

    with self.assertRaisesRegex(RuntimeError, "requires explicit maintained ObservationPacket/DecisionBelief"):
      adapter.run_maintained_window(
        world_index=0,
        entity_id=42,
        pilot_action=ef_py.PilotAction(),
        information_state_label="agent_observation_adapter_projection",
      )

  def test_world_batch_adapter_loader_runtime_task_order_write_requires_maintained_binding(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)
    proxy = adapter._scenario_loader_runtime(0)
    original_ef_py = world_batch_adapter_module.ef_py

    class _NoMaintainedTaskOrderBindings:
      pass

    world_batch_adapter_module.ef_py = _NoMaintainedTaskOrderBindings() # type: ignore[assignment]
    try:
      with self.assertRaisesRegex(RuntimeError, "requires maintained TaskOrder batch bindings"):
        proxy.set_task_order(91, object())
    finally:
      world_batch_adapter_module.ef_py = original_ef_py # type: ignore[assignment]



if __name__ == "__main__":
  unittest.main()
