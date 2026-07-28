from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from textwrap import dedent

from python.runtime_bootstrap import build_dir, resolve_repo_path


_REPO_ROOT = resolve_repo_path()
_BUILD_DIR = build_dir()
_DB_PATH = resolve_repo_path("examples", "config", "database")


def _run_probe(script: str) -> dict[str, object]:
  env = os.environ.copy()
  env["CMO_BUILD_DIR"] = _BUILD_DIR
  proc = subprocess.run(
    [sys.executable, "-u", "-c", script],
    cwd=_REPO_ROOT,
    env=env,
    text=True,
    capture_output=True,
    check=True,
  )
  return json.loads(proc.stdout.strip())


def _probe_prelude() -> str:
  return dedent(
    f"""
    import json
    import os
    from python.runtime_bootstrap import configure_sim_log_level
    configure_sim_log_level("error")
    import ef_py

    DB_PATH = r"{_DB_PATH}"

    def emit(payload):
      print(json.dumps(payload), flush=True)
    """
  )


class RuntimeTeardownStabilityTests(unittest.TestCase):
  def test_kernel_create_step_destroy_loop_stays_stable(self) -> None:
    result = _run_probe(
      _probe_prelude()
      + dedent(
        """
        loops = 12
        for idx in range(loops):
          kernel = ef_py.SimulationKernel()
          kernel.reset(100 + idx)
          entity_id = kernel.spawn_unit(
            ef_py.Side.Blue,
            "Aircraft",
            0.0, 0.0, 1200.0,
            0.0, 5.0, 0.0,
            0.0, 120.0, 0.0,
          )
          kernel.step()
          inst = kernel.get_instrument_state(entity_id)
          assert float(inst.pitch) > 0.0
          del inst
          del kernel

        emit({"loops": loops, "status": "ok"})
        """
      )
    )

    self.assertEqual(result["status"], "ok")
    self.assertEqual(result["loops"], 12)

  def test_kernel_database_observation_and_destroy_stays_stable(self) -> None:
    result = _run_probe(
      _probe_prelude()
      + dedent(
        """
        loops = 6
        last_contact_count = -1
        for idx in range(loops):
          sim = ef_py.SimulationKernel()
          sim.reset(200 + idx)
          assert sim.load_database(DB_PATH)

          own = sim.spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            0.0, 0.0, 3000.0,
            0.0, 0.0, 0.0,
            0.0, 250.0, 0.0,
          )
          foe = sim.spawn_unit(
            ef_py.Side.Red,
            "F-16C_Block50",
            0.0, 20000.0, 3000.0,
            180.0, 0.0, 0.0,
            0.0, -250.0, 0.0,
          )

          det = ef_py.Detection()
          det.target_id = int(foe)
          det.range = 20000.0
          det.bearing = 0.0
          det.elevation = 0.0
          det.closing_speed = 500.0
          det.signal_strength = 1.0
          det.timestamp = 0.0
          sim.set_contact_list(int(own), [det])
          sim.step()

          obs = sim.get_agent_observation(int(own))
          last_contact_count = len(obs.contacts)
          assert last_contact_count >= 0
          del obs
          del sim

        emit({"loops": loops, "last_contact_count": last_contact_count, "status": "ok"})
        """
      )
    )

    self.assertEqual(result["status"], "ok")
    self.assertEqual(result["loops"], 6)
    self.assertGreaterEqual(result["last_contact_count"], 0)


if __name__ == "__main__":
  unittest.main()
