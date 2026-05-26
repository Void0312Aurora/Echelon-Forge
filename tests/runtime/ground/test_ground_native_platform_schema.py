from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")
_GROUND_UNIT_PATH = resolve_repo_path(
    "examples",
    "config",
    "database",
    "ground",
    "units",
    "ground_platoon_mvp.json",
)
_FACTORY_HEADER = resolve_repo_path("src", "models", "core", "default_unit_factory.h")


class GroundNativePlatformSchemaTests(unittest.TestCase):
    def _spawn_ground(self) -> tuple[ef_py.SimulationKernel, int]:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))
        entity_id = int(
            sim.spawn_unit(
                ef_py.Side.Blue,
                "Ground_Platoon_MVP",
                100.0,
                250.0,
                0.0,
                37.0,
                0.0,
                0.0,
                1.25,
                0.0,
                0.0,
            )
        )
        self.assertGreater(entity_id, 0)
        return sim, entity_id

    def test_ground_unit_type_binding_and_database_spawn_identity(self) -> None:
        sim, entity_id = self._spawn_ground()

        self.assertTrue(hasattr(ef_py.UnitType, "Ground"))
        self.assertEqual(sim.get_unit_type(entity_id), int(ef_py.UnitType.Ground))
        self.assertNotEqual(sim.get_unit_type(entity_id), int(ef_py.UnitType.Aircraft))
        self.assertNotEqual(sim.get_unit_type(entity_id), int(ef_py.UnitType.Ship))
        self.assertNotEqual(sim.get_unit_type(entity_id), int(ef_py.UnitType.Submarine))
        self.assertNotEqual(sim.get_unit_type(entity_id), int(ef_py.UnitType.Facility))
        self.assertNotEqual(sim.get_unit_type(entity_id), int(ef_py.UnitType.C2Node))

    def test_ground_unit_type_overload_uses_native_default_name_after_database_load(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))

        entity_id = int(
            sim.spawn_unit(
                ef_py.Side.Blue,
                ef_py.UnitType.Ground,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            )
        )

        self.assertGreater(entity_id, 0)
        self.assertEqual(sim.get_unit_type(entity_id), int(ef_py.UnitType.Ground))

    def test_ground_native_entity_exposes_static_runtime_inspection_state(self) -> None:
        sim, entity_id = self._spawn_ground()

        self.assertEqual(tuple(sim.get_unit_position(entity_id)), (100.0, 250.0, 0.0))
        self.assertEqual(tuple(sim.get_unit_velocity(entity_id)), (1.25, 0.0, 0.0))
        self.assertAlmostEqual(float(sim.get_unit_heading(entity_id)), 37.0, places=6)
        self.assertEqual(list(sim.get_unit_health(entity_id)), [100.0, 100.0])

        inst = sim.get_instrument_state(entity_id)
        self.assertAlmostEqual(float(inst.heading), 37.0, places=6)
        self.assertAlmostEqual(float(inst.ias), 1.25, places=6)
        self.assertAlmostEqual(float(inst.alt_baro), 0.0, places=6)

    def test_ground_schema_content_and_factory_capability_evidence_stay_movement_deferred(self) -> None:
        with Path(_GROUND_UNIT_PATH).open("r", encoding="utf-8") as handle:
            definition = json.load(handle)
        factory_header = Path(_FACTORY_HEADER).read_text(encoding="utf-8")

        self.assertEqual(definition["name"], "Ground_Platoon_MVP")
        self.assertEqual(definition["type"], "Ground")
        self.assertEqual(definition["_ground_schema"]["service_profile"], "Army")
        self.assertEqual(definition["_ground_schema"]["platform_family"], "dismounted_unit")
        self.assertEqual(definition["_ground_schema"]["doctrine_family"], "land_tactics")
        self.assertEqual(
            definition["_ground_schema"]["mobility_declaration"],
            "ground_mobility_flat_deferred",
        )
        self.assertEqual(
            definition["_ground_schema"]["movement_behavior"],
            "static_or_caller_initial_velocity_only",
        )
        self.assertIn("route following or movement behavior", definition["_deferred_runtime_claims"])
        self.assertIn("ground_mobility_flat_deferred", factory_header)
        self.assertIn("land_tactics", factory_header)
        self.assertIn("movement_behavior_deferred", factory_header)

    def test_malformed_ground_schema_fails_closed_without_substitute_spawn(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))

        with tempfile.TemporaryDirectory() as tmpdir:
            bad_path = Path(tmpdir) / "bad_ground_unit.json"
            bad_path.write_text(
                json.dumps(
                    {
                        "name": "Bad_Ground_Platoon",
                        "type": "GroundUnit",
                        "health": {"current_hp": 1.0, "max_hp": 1.0},
                    }
                ),
                encoding="utf-8",
            )
            self.assertFalse(sim.load_unit_definitions(str(bad_path)))

        rejected_id = int(
            sim.spawn_unit(
                ef_py.Side.Blue,
                "Bad_Ground_Platoon",
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            )
        )
        self.assertEqual(rejected_id, 0)


if __name__ == "__main__":
    unittest.main()
