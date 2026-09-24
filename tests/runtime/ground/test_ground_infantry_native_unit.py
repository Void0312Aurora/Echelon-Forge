from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

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
_ARNIS_BUNDLE = resolve_repo_path(
    "tests",
    "scenario",
    "fixtures",
    "environment_substrate",
    "arnis_bundle_v1",
    "eastern_plain_infantry_phase1",
    "expected",
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
    assert definition["ground_infantry_capability"] is True
    assert definition["_ground_schema"]["echelon"] == "individual"
    assert definition["_ground_schema"]["platform_family"] == "dismounted_infantry"


def test_ground_platoon_does_not_enter_infantry_movement_without_authored_capability() -> None:
    sim = ef_py.SimulationKernel()
    assert sim.load_database(_DATABASE)
    sim.set_terrain_type("flat")
    platoon_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "Ground_Platoon_MVP",
            400.0,
            100.0,
            0.0,
        )
    )

    command = ef_py.MissionCommand()
    command.active = True
    command.cmd_heading_deg = 90.0
    command.cmd_speed_mps = 1.5
    command.ground_task_mode = ef_py.GroundTaskMode.MoveStatic
    sim.set_command_link(platoon_id, 0.0, 0.0)
    sim.set_mission_command(platoon_id, command)
    before = tuple(sim.get_unit_position(platoon_id))

    sim.step()

    assert tuple(sim.get_unit_position(platoon_id)) == before
    assert tuple(sim.get_unit_velocity(platoon_id)) == (0.0, 0.0, 0.0)


def test_native_infantry_movement_consumes_ground_command_and_terrain_cost() -> None:
    sim = ef_py.SimulationKernel()
    assert sim.load_database(_DATABASE)
    sim.set_terrain_type("flat")
    assert float(sim.get_ground_slope_deg(400.0, 100.0)) == pytest.approx(0.0)
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


def test_native_infantry_stance_changes_movement_cost() -> None:
    sim = ef_py.SimulationKernel()
    assert sim.load_database(_DATABASE)
    sim.set_terrain_type("flat")
    stand_id = int(
        sim.spawn_unit(ef_py.Side.Blue, "Ground_Infantry_Soldier_MVP", 400.0, 100.0, 0.0)
    )
    prone_id = int(
        sim.spawn_unit(ef_py.Side.Blue, "Ground_Infantry_Soldier_MVP", 400.0, 200.0, 0.0)
    )
    for entity_id, stance in (
        (stand_id, ef_py.GroundStance.Stand),
        (prone_id, ef_py.GroundStance.Prone),
    ):
        command = ef_py.MissionCommand()
        command.active = True
        command.cmd_heading_deg = 90.0
        command.cmd_speed_mps = 1.5
        command.ground_task_mode = ef_py.GroundTaskMode.MoveStatic
        command.ground_stance = stance
        sim.set_command_link(entity_id, 0.0, 0.0)
        sim.set_mission_command(entity_id, command)

    sim.step()
    stand_speed = float(sim.get_unit_velocity(stand_id)[0])
    prone_speed = float(sim.get_unit_velocity(prone_id)[0])
    assert stand_speed > prone_speed > 0.0
    assert prone_speed == pytest.approx(stand_speed * 0.35, rel=1.0e-6)


def test_native_infantry_consumes_arnis_raster_and_stops_on_water() -> None:
    bundle = Path(_ARNIS_BUNDLE)
    manifest = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
    elevation_artifact = next(
        artifact for artifact in manifest["artifacts"] if artifact["kind"] == "elevation_raster"
    )
    landcover_artifact = next(
        artifact for artifact in manifest["artifacts"] if artifact["kind"] == "landcover_raster"
    )
    shape = tuple(int(value) for value in elevation_artifact["shape"])
    landcover = np.memmap(
        bundle / landcover_artifact["path"], dtype="u1", mode="r", shape=shape
    )
    water_row, water_col = next(
        (row, col)
        for row in range(shape[0])
        for col in range(shape[1])
        if int(landcover[row, col]) == 80
    )
    cropland_row, cropland_col = next(
        (row, col)
        for row in range(shape[0])
        for col in range(shape[1])
        if int(landcover[row, col]) == 40
    )
    tree_row, tree_col = next(
        (row, col)
        for row in range(shape[0])
        for col in range(shape[1])
        if int(landcover[row, col]) == 10
    )
    origin_x, origin_y = elevation_artifact["metadata"]["origin_xy_m"]
    step_x, step_y = elevation_artifact["metadata"]["step_xy_m"]

    sim = ef_py.SimulationKernel()
    assert sim.load_database(_DATABASE)
    assert sim.load_arnis_terrain_bundle(str(bundle))
    overlay_path = bundle.parent / "field_overlay.json"
    assert sim.load_arnis_field_overlay(str(overlay_path))
    assert not sim.load_arnis_field_overlay(str(overlay_path / "missing"))
    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    tree_entry = next(entry for entry in overlay["entries"] if entry["overlay_kind"] == "tree_line")
    settlement_entry = next(
        entry for entry in overlay["entries"] if entry["overlay_kind"] == "settlement_anchor"
    )
    min_x = min(origin_x, origin_x + (shape[1] - 1) * step_x)
    min_y = min(origin_y, origin_y + (shape[0] - 1) * step_y)
    tree_points = tree_entry["geometry"]["points"]
    tree_x = sum(point[0] for point in tree_points[:4]) / min(4, len(tree_points))
    tree_y = sum(point[1] for point in tree_points[:4]) / min(4, len(tree_points))
    tree_semantics = sim.get_ground_field_semantic_observation(
        min_x + tree_x, min_y + tree_y
    )
    assert float(tree_semantics[0]) == 1.0
    assert float(tree_semantics[1]) == pytest.approx(0.0)
    assert float(tree_semantics[5]) == 1.0
    settlement_point = settlement_entry["geometry"]["point"]
    settlement_semantics = sim.get_ground_field_semantic_observation(
        min_x + settlement_point[0], min_y + settlement_point[1]
    )
    assert float(settlement_semantics[0]) == 1.0
    assert float(settlement_semantics[3]) == pytest.approx(0.0)
    assert float(settlement_semantics[6]) == 1.0
    # A failed candidate must not clear the already admitted provider raster.
    assert not sim.load_arnis_terrain_bundle(str(bundle / "missing_candidate"))
    water_sample = sim.get_ground_terrain_observation(
        origin_x + water_col * step_x, origin_y + water_row * step_y
    )
    crop_sample = sim.get_ground_terrain_observation(
        origin_x + cropland_col * step_x, origin_y + cropland_row * step_y
    )
    tree_sample = sim.get_ground_terrain_observation(
        origin_x + tree_col * step_x, origin_y + tree_row * step_y
    )
    assert int(water_sample[1]) == 4  # IEnvironmentModel::SurfaceType::Water
    assert int(crop_sample[1]) == 3  # IEnvironmentModel::SurfaceType::SoftDirt
    assert int(sim.get_ground_terrain_observation(0.0, 100.0)[1]) == 4
    assert int(sim.get_ground_terrain_observation(0.0, 0.0)[1]) == 2
    arnis_slope = float(sim.get_ground_slope_deg(0.0, 0.0))
    assert math.isfinite(arnis_slope)
    assert arnis_slope >= 0.0
    river_transition = sim.get_ground_transition_observation(-200.0, 100.0, 200.0, 100.0)
    assert float(river_transition[0]) == 1.0
    assert float(river_transition[1]) == 0.0
    assert int(river_transition[2]) == 4
    assert float(river_transition[3]) == 1.0
    assert float(river_transition[4]) == 0.0
    assert float(river_transition[5]) == 0.0
    assert float(river_transition[6]) == pytest.approx(400.0)
    bridge_transition = sim.get_ground_transition_observation(-200.0, 0.0, 200.0, 0.0)
    assert float(bridge_transition[0]) == 1.0
    assert float(bridge_transition[1]) == 1.0
    assert int(bridge_transition[2]) == 2
    assert float(bridge_transition[3]) == 0.0
    assert float(bridge_transition[4]) == 0.0
    assert float(bridge_transition[5]) == 1.0
    assert float(bridge_transition[6]) == pytest.approx(400.0)
    assert math.isfinite(float(water_sample[0]))
    assert math.isfinite(float(crop_sample[0]))
    assert 0.0 <= float(crop_sample[3]) <= 1.0
    assert 0.0 <= float(crop_sample[4]) <= 1.0
    assert float(tree_sample[4]) > float(crop_sample[4])
    water_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "Ground_Infantry_Soldier_MVP",
            origin_x + water_col * step_x,
            origin_y + water_row * step_y,
            0.0,
        )
    )
    cropland_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "Ground_Infantry_Soldier_MVP",
            origin_x + cropland_col * step_x,
            origin_y + cropland_row * step_y,
            0.0,
        )
    )
    tree_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "Ground_Infantry_Soldier_MVP",
            origin_x + tree_col * step_x,
            origin_y + tree_row * step_y,
            0.0,
        )
    )
    bridge_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "Ground_Infantry_Soldier_MVP",
            0.0,
            0.0,
            0.0,
        )
    )
    for entity_id in (water_id, cropland_id, tree_id, bridge_id):
        command = ef_py.MissionCommand()
        command.active = True
        command.cmd_heading_deg = 90.0
        command.cmd_speed_mps = 1.5
        command.ground_task_mode = ef_py.GroundTaskMode.MoveStatic
        sim.set_command_link(entity_id, 0.0, 0.0)
        sim.set_mission_command(entity_id, command)

    sim.step()
    assert tuple(sim.get_unit_velocity(water_id)) == (0.0, 0.0, 0.0)
    assert float(sim.get_unit_velocity(cropland_id)[0]) > 0.0
    assert 0.0 < float(sim.get_unit_velocity(tree_id)[0]) < float(
        sim.get_unit_velocity(cropland_id)[0]
    )
    assert float(sim.get_unit_velocity(bridge_id)[0]) > 0.0

    boundary_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "Ground_Infantry_Soldier_MVP",
            -180.0,
            100.0,
            0.0,
        )
    )
    boundary_command = ef_py.MissionCommand()
    boundary_command.active = True
    boundary_command.cmd_heading_deg = 90.0
    boundary_command.cmd_speed_mps = 2000.0
    boundary_command.ground_task_mode = ef_py.GroundTaskMode.MoveStatic
    sim.set_command_link(boundary_id, 0.0, 0.0)
    sim.set_mission_command(boundary_id, boundary_command)
    boundary_before = tuple(sim.get_unit_position(boundary_id))
    sim.step()
    assert tuple(sim.get_unit_velocity(boundary_id)) == (0.0, 0.0, 0.0)
    assert tuple(sim.get_unit_position(boundary_id)) == boundary_before


def test_native_infantry_ground_rifle_requires_track_and_applies_damage() -> None:
    sim = ef_py.SimulationKernel()
    assert sim.load_database(_DATABASE)
    attacker_id = int(
        sim.spawn_unit(ef_py.Side.Blue, "Ground_Infantry_Soldier_MVP", 0.0, 0.0, 0.0)
    )
    target_id = int(
        sim.spawn_unit(ef_py.Side.Red, "Ground_Infantry_Soldier_MVP", 100.0, 0.0, 0.0)
    )
    sim.set_command_link(attacker_id, 0.0, 0.0)

    initial_weapon = list(sim.get_ground_weapon_state(attacker_id))
    assert initial_weapon[:4] == [1.0, float(int(ef_py.GroundWeaponType.Rifle)), 30.0, 30.0]
    assert initial_weapon[4] == pytest.approx(8.0)
    assert initial_weapon[5] == pytest.approx(300.0)
    assert initial_weapon[6] == pytest.approx(1.0)
    assert initial_weapon[7] == pytest.approx(0.0)

    # A ground rifle cannot release without an explicit local track.
    assert not sim.fire_ground_weapon(
        attacker_id, target_id, int(ef_py.GroundWeaponType.Rifle)
    )
    track = ef_py.Detection()
    track.target_id = target_id
    track.range = 100.0
    track.bearing = 90.0
    track.elevation = 0.0
    track.closing_speed = 0.0
    track.signal_strength = 1.0
    track.snr_db = 20.0
    track.detection_prob_used = 1.0
    track.measured_vr = 0.0
    track.sensor_type = int(ef_py.SensorType.Visual)
    track.local_sensor_hit = True
    track.timestamp = 0.0
    sim.set_contact_list(attacker_id, [track])

    initial = list(sim.get_unit_damage_state(target_id))
    assert sim.fire_ground_weapon(
        attacker_id, target_id, int(ef_py.GroundWeaponType.Rifle)
    )
    after_fire = list(sim.get_unit_damage_state(target_id))
    assert after_fire[0] < initial[0]
    assert after_fire[3] < initial[3]
    after_weapon = list(sim.get_ground_weapon_state(attacker_id))
    assert after_weapon[2] == pytest.approx(29.0)
    assert after_weapon[7] == pytest.approx(0.5)

    # The native weapon owns a cooldown; an immediate second trigger is rejected.
    assert not sim.fire_ground_weapon(
        attacker_id, target_id, int(ef_py.GroundWeaponType.Rifle)
    )


def test_ground_platoon_does_not_acquire_or_fire_infantry_rifle() -> None:
    sim = ef_py.SimulationKernel()
    assert sim.load_database(_DATABASE)
    platoon_id = int(
        sim.spawn_unit(ef_py.Side.Blue, "Ground_Platoon_MVP", 0.0, 0.0, 0.0)
    )
    target_id = int(
        sim.spawn_unit(
            ef_py.Side.Red, "Ground_Infantry_Soldier_MVP", 100.0, 0.0, 0.0
        )
    )

    assert float(sim.get_ground_weapon_state(platoon_id)[0]) == pytest.approx(0.0)
    track = ef_py.Detection()
    track.target_id = target_id
    track.range = 100.0
    track.local_sensor_hit = True
    sim.set_contact_list(platoon_id, [track])

    assert not sim.fire_ground_weapon(
        platoon_id, target_id, int(ef_py.GroundWeaponType.Rifle)
    )


def test_native_infantry_ground_rifle_mission_command_requires_authority() -> None:
    sim = ef_py.SimulationKernel()
    assert sim.load_database(_DATABASE)
    attacker_id = int(
        sim.spawn_unit(ef_py.Side.Blue, "Ground_Infantry_Soldier_MVP", 0.0, 0.0, 0.0)
    )
    target_id = int(
        sim.spawn_unit(ef_py.Side.Red, "Ground_Infantry_Soldier_MVP", 100.0, 0.0, 0.0)
    )
    sim.set_command_link(attacker_id, 0.0, 0.0)

    track = ef_py.Detection()
    track.target_id = target_id
    track.range = 100.0
    track.bearing = 90.0
    track.detection_prob_used = 1.0
    track.sensor_type = int(ef_py.SensorType.Visual)
    sim.set_contact_list(attacker_id, [track])

    command = ef_py.MissionCommand()
    command.active = True
    command.assigned_target_id = target_id
    command.authorization_to_fire = False
    command.engagement_authority_holder_id = attacker_id
    sim.set_mission_command(attacker_id, command)
    assert not sim.fire_ground_weapon_from_mission_command(attacker_id)

    command.authorization_to_fire = True
    sim.set_mission_command(attacker_id, command)
    assert sim.fire_ground_weapon_from_mission_command(attacker_id)
