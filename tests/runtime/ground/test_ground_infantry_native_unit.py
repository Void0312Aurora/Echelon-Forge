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


def test_native_infantry_movement_consumes_ground_command_and_terrain_cost() -> None:
    sim = ef_py.SimulationKernel()
    assert sim.load_database(_DATABASE)
    sim.set_terrain_type("flat")
    entity_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "Ground_Infantry_Soldier_MVP",
            400.0,
            100.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )
    )

    command = ef_py.MissionCommand()
    command.active = True
    command.cmd_heading_deg = 90.0
    command.cmd_speed_mps = 1.5
    command.ground_task_mode = ef_py.GroundTaskMode.MoveStatic
    # Remove transport latency so this focused unit test observes the native
    # movement stage on the next simulation tick.
    sim.set_command_link(entity_id, 0.0, 0.0)
    sim.set_mission_command(entity_id, command)

    # Ground movement is admitted after the existing shared integration stage;
    # the first tick resolves the command into velocity and the next tick drifts.
    sim.step()
    velocity = sim.get_unit_velocity(entity_id)
    assert float(velocity[0]) > 0.0
    assert float(velocity[0]) < 1.5
    position_before_drift = sim.get_unit_position(entity_id)
    sim.step()
    position_after_drift = sim.get_unit_position(entity_id)
    assert float(position_after_drift[0]) > float(position_before_drift[0])
