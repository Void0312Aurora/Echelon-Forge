from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402


class KernelLifecycleGuardTests(unittest.TestCase):
  def test_time_step_and_post_shutdown_calls_fail_closed(self) -> None:
    kernel = ef_py.SimulationKernel()
    original = kernel.get_time_step()

    for value in (0.0, -0.1, math.inf, -math.inf, math.nan):
      with self.subTest(value=value):
        with self.assertRaises(ValueError):
          kernel.set_time_step(value)
    self.assertEqual(kernel.get_time_step(), original)

    kernel.shutdown()
    with self.assertRaises(RuntimeError):
      kernel.reset(7)
    with self.assertRaises(RuntimeError):
      kernel.step()
    with self.assertRaises(RuntimeError):
      kernel.set_time_step(0.1)
    with self.assertRaises(RuntimeError):
      kernel.load_database("examples/config/database")
    with self.assertRaises(RuntimeError):
      kernel.spawn_unit(ef_py.Side.Blue, "Aircraft", 0.0, 0.0, 1000.0)
    with self.assertRaises(RuntimeError):
      kernel.set_wind(10.0, 270.0, 0.0)
    with self.assertRaises(RuntimeError):
      kernel.clear_zones()
    with self.assertRaises(RuntimeError):
      kernel.set_missile_tuning(ef_py.MissileTuning())
    with self.assertRaises(RuntimeError):
      kernel.fire_missile(1, 2)
    with self.assertRaises(RuntimeError):
      kernel.fire_naval_weapon(1, 2, 0)

  def test_world_batch_rejects_duplicate_indices(self) -> None:
    runtime = ef_py.WorldBatchRuntime(1)
    runtime.set_worker_threads(2)

    with self.assertRaises(ValueError):
      runtime.step_worlds([0, 0])
    with self.assertRaises(ValueError):
      runtime.clear_zones_batch([0, 0])

  def test_failed_directory_database_load_does_not_commit_valid_siblings(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
      root = Path(tmp)
      (root / "good.json").write_text(
        '{"name": "Transactional_Load_Must_Not_Commit", "type": "Aircraft"}',
        encoding="utf-8",
      )
      (root / "bad.json").write_text('{"name": "broken"', encoding="utf-8")

      kernel = ef_py.SimulationKernel()
      self.assertFalse(kernel.load_database(str(root)))
      entity_id = kernel.spawn_unit(
        ef_py.Side.Blue,
        "Transactional_Load_Must_Not_Commit",
        0.0,
        0.0,
        1000.0,
      )
      self.assertEqual(entity_id, 0)


if __name__ == "__main__":
  unittest.main()
