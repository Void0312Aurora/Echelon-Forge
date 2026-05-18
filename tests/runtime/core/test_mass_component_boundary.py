from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


class MassComponentBoundaryTests(unittest.TestCase):
    def test_mass_properties_total_tracks_mass_total_including_stores(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(19)
        self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

        entity_id = kernel.spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            0.0,
            0.0,
            1200.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=180.0,
            vz=0.0,
        )

        initial = kernel.debug_get_mass_state(int(entity_id))
        self.assertEqual(len(initial), 6)
        self.assertGreater(float(initial[2]), 0.0, "expected default loadout to contribute stores mass")
        self.assertAlmostEqual(float(initial[3]), float(initial[4]) + float(initial[1]) + float(initial[2]), places=6)

        kernel.step()
        after = kernel.debug_get_mass_state(int(entity_id))
        self.assertEqual(len(after), 6)
        self.assertAlmostEqual(float(after[0]), float(after[4]), places=6)
        self.assertAlmostEqual(float(after[3]), float(after[5]), places=6)
        self.assertAlmostEqual(float(after[5]), float(after[4]) + float(after[1]) + float(after[2]), places=6)


if __name__ == "__main__":
    unittest.main()
