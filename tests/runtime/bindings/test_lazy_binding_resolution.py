from __future__ import annotations

import importlib
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from python.runtime_bootstrap import build_dir, ensure_repo_imports


REPO_ROOT = Path(__file__).resolve().parents[3]


class LazyBindingResolutionTests(unittest.TestCase):
  def _load_module_from_path(self, module_name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    self.assertIsNotNone(spec)
    self.assertIsNotNone(spec.loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

  def test_common_import_prefers_repo_build_ef_py(self) -> None:
    ensure_repo_imports()

    sys.modules.pop("ef_py", None)
    sys.modules.pop("tools.diagnostics.common", None)

    common = importlib.import_module("tools.diagnostics.common")
    ef_py = importlib.import_module("ef_py")

    expected_root = Path(build_dir()).resolve()
    module_path = Path(str(getattr(ef_py, "__file__", ""))).resolve()

    # NOTE(I57): tools.diagnostics.common resolves ef_py lazily through the
    # private `_ef_py()` helper in this lineage (no eager module-level `ef_py`
    # attribute; no production consumer references `common.ef_py`). Assert the
    # resolution API this lineage actually exposes -- `_ef_py()` must return the
    # same repo-build ef_py module object -- which preserves the original intent
    # ("common prefers the repo-build ef_py") without weakening it.
    self.assertIs(common._ef_py(), ef_py)
    self.assertTrue(str(module_path).startswith(str(expected_root)))
    self.assertTrue(hasattr(ef_py, "ConditionalObjectiveProperty"))
    self.assertTrue(hasattr(ef_py, "WorldBatchRuntime"))

  def test_objective_common_modules_delay_enum_resolution_until_runtime_use(self) -> None:
    class _StubEfPy:
      pass

    ensure_repo_imports()

    for name in (
      "gym_envs.scenario_loader.common",
      "python.scenario.compiler.common",
    ):
      sys.modules.pop(name, None)

    with mock.patch.dict(sys.modules, {"ef_py": _StubEfPy()}):
      loader_common = self._load_module_from_path(
        "_diagnostics_loader_common_stubbed",
        "gym_envs/scenario_loader/common.py",
      )
      compiler_common = self._load_module_from_path(
        "_diagnostics_compiler_common_stubbed",
        "python/scenario/compiler/common.py",
      )

      with self.assertRaisesRegex(AttributeError, "ConditionalObjectiveProperty"):
        loader_common.OBJECTIVE_PROPERTY_MAP["altitude"]
      with self.assertRaisesRegex(AttributeError, "ConditionalObjectiveProperty"):
        compiler_common._OBJECTIVE_PROPERTY_MAP["altitude"]

  def test_world_batch_command_chain_cache_delays_binding_resolution_until_snapshot_use(self) -> None:
    class _StubEfPy:
      MissionCommand = staticmethod(lambda: SimpleNamespace(command_code=0))

    ensure_repo_imports()
    sys.modules.pop("python.rl.runtime.world_batch.command_chain_cache", None)

    with mock.patch.dict(sys.modules, {"ef_py": _StubEfPy()}):
      command_chain_cache = self._load_module_from_path(
        "_diagnostics_command_chain_cache_stubbed",
        "python/rl/runtime/world_batch/command_chain_cache.py",
      )

      self.assertTupleEqual(command_chain_cache.MISSION_COMMAND_FIELDS, ("command_code",))
      self.assertIsNone(command_chain_cache.task_order_snapshot(None))
      with self.assertRaisesRegex(RuntimeError, r"ef_py\.TaskOrder\(\)"):
        command_chain_cache.task_order_snapshot(SimpleNamespace(task_id=1))
      with self.assertRaisesRegex(RuntimeError, r"ef_py\.LeaderIntent\(\)"):
        command_chain_cache.leader_intent_snapshot(SimpleNamespace(phase_id=1))
      with self.assertRaisesRegex(RuntimeError, r"ef_py\.PilotReport\(\)"):
        command_chain_cache.pilot_report_snapshot(SimpleNamespace(report_type=1))

  def test_reward_metadata_delays_objective_shaping_binding_until_conditional_objectives_exist(self) -> None:
    class _StubEfPy:
      class ConditionalObjectiveProperty:
        Unknown = object()

      class ConditionalObjectiveOp:
        GreaterEqual = object()

      class ConditionalObjectiveTargetKind:
        Literal = object()

      @staticmethod
      def ConditionalObjectiveSpec():
        return SimpleNamespace(reward_bonus=0.0, conditions=[])

      @staticmethod
      def ConditionalObjectiveCondition():
        return SimpleNamespace(
          property_code=None,
          op_code=None,
          target_kind=None,
          target_scale=0.0,
          target_value=0.0,
        )

    ensure_repo_imports()

    for name in (
      "python.scenario.compiler.common",
      "python.scenario.compiler.reward_metadata",
    ):
      sys.modules.pop(name, None)

    with mock.patch.dict(sys.modules, {"ef_py": _StubEfPy()}):
      reward_metadata = importlib.import_module("python.scenario.compiler.reward_metadata")

      self.assertIsNone(reward_metadata._build_objective_shaping_config({}, required=False))
      compiled = reward_metadata._compile_conditional_objectives(
        [{"type": "conditional", "reward": 25.0, "conditions": []}]
      )
      self.assertEqual(len(compiled), 1)
      with self.assertRaisesRegex(RuntimeError, r"ef_py\.ObjectiveShapingConfig\(\)"):
        reward_metadata._build_objective_shaping_config({}, required=True)


if __name__ == "__main__":
  unittest.main()
