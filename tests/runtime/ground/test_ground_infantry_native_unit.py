from __future__ import annotations

import json
from pathlib import Path

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


_DATABASE = resolve_repo_path("examples", "config", "database")
_UNIT = resolve_repo_path(
    "examples",
    "config",
    "database",
    "ground",
    "units",
    "ground_infantry_soldier_mvp.json",
)


def test_single_infantry_definition_loads_and_spawns_as_native_ground() -> None:
    sim = ef_py.SimulationKernel()
    assert sim.load_database(_DATABASE)

    entity_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "Ground_Infantry_Soldier_MVP",
            10.0,
            20.0,
            0.0,
            90.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )
    )

    assert entity_id > 0
    assert sim.get_unit_type(entity_id) == int(ef_py.UnitType.Ground)
    assert tuple(sim.get_unit_position(entity_id)) == (10.0, 20.0, 0.0)
    assert tuple(sim.get_unit_velocity(entity_id)) == (0.0, 0.0, 0.0)
    assert list(sim.get_unit_health(entity_id)) == [100.0, 100.0]

    definition = json.loads(Path(_UNIT).read_text(encoding="utf-8"))
    assert definition["_ground_schema"]["echelon"] == "individual"
    assert definition["_ground_schema"]["platform_family"] == "dismounted_infantry"
