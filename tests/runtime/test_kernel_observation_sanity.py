from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


class KernelObservationSanityTests(unittest.TestCase):
    def test_spawned_unit_exposes_health_and_fire_fields(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(42)

        entity_id = kernel.spawn_unit(
            ef_py.Side.Blue,
            "Aircraft",
            0.0,
            0.0,
            1000.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=100.0,
            vy=0.0,
            vz=0.0,
        )

        health = kernel.get_unit_health(entity_id)
        self.assertIsInstance(health, list)
        self.assertEqual(len(health), 2)

        obs = kernel.get_agent_observation(entity_id)
        self.assertTrue(hasattr(obs, "health"))
        self.assertTrue(hasattr(obs, "can_fire"))


if __name__ == "__main__":
    unittest.main()
