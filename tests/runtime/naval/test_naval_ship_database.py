from __future__ import annotations

import json
import math
import tempfile
import unittest

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402


# --- DM-N1 naval damage-response profile surface -------------------------------
#
# `NavalDamageResponseProfile` entries live in
# `src/components/domains/naval/combat/damage_naval.h` and
# `src/systems/combat/damage_system_naval.h` resolves one profile per platform.
# The response is observed through `get_unit_damage_state` (the capability
# projection) and `debug_get_naval_weapon_counts` (the mount state it reads).

# `get_unit_damage_state` vector: [mission, mobility, sensor, survivability].
_RESPONSE_MISSION = 0
_RESPONSE_MOBILITY = 1
_RESPONSE_SENSOR = 2
_RESPONSE_SURVIVABILITY = 3

# `debug_get_naval_weapon_counts` vector:
# [mount_count, ready_vls_sam, ready_deck_gun, ready_ciws].
_RESPONSE_COUNT_MOUNTS = 0
_RESPONSE_COUNT_VLS = 1
_RESPONSE_COUNT_GUN = 2
_RESPONSE_COUNT_CIWS = 3

# `NavalWeaponType` code for the CIWS mount at the kernel `fire_naval_weapon`
# boundary (the enum itself is not bound into `ef_py`).
_RESPONSE_CIWS_TYPE_CODE = 3

# DDG-51 hitbox-routed aim points in target-body local metres. Which protected
# systems the shared effects path damages is what makes the naval fire and
# flooding channels reachable at runtime:
#   box 1 forward  (+45, 0, +3): forward_vls / forward_gun / combat_system
#   box 2 midships (  0, 0, +8): aegis_radar / command / data_link
#   box 3 aft      (-35, 0, +2): engineering / aft_vls / fuel
# Only the engineering/fuel family seeds `ongoing_hull_breach` and
# `flooding_severity`, so only the aft aim point exercises the flooding channel.
_RESPONSE_AIM_FORWARD_M = (45.0, 0.0, 3.0)
_RESPONSE_AIM_AFT_ENGINEERING_M = (-35.0, 0.0, 2.0)

_RESPONSE_HIT_DAMAGE = 160.0
_RESPONSE_HIT_FUSE_DISTANCE_M = 80.0


class NavalShipDatabaseTests(unittest.TestCase):
  _OPEN_WATER_X = 1_000_000.0
  _OPEN_WATER_Y = 1_000_000.0

  def test_naval_spawn_uses_type_name_resolution_chain_materialization(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(499)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      self._OPEN_WATER_X,
      self._OPEN_WATER_Y,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=10.29,
      vz=0.0,
    )

    self.assertGreater(int(ddg), 0)
    self.assertEqual(kernel.get_unit_type(int(ddg)), int(ef_py.UnitType.Ship))
    self.assertTrue(hasattr(ef_py, "ResolvedPlatformSpawnPlan"))

  def _load_database_with_ship_overrides(self, overrides: dict[str, dict]) -> ef_py.SimulationKernel:
    kernel = ef_py.SimulationKernel()
    kernel.reset(5100 + len(overrides))
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
      json.dump({"units": list(overrides.values())}, handle)
      override_path = handle.name
    self.assertTrue(kernel.load_unit_definitions(override_path))
    return kernel

  def test_ddg_loads_multi_sensor_and_passive_esm_suite(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(500)
    kernel.set_time_step(0.5)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      self._OPEN_WATER_X,
      self._OPEN_WATER_Y,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=10.29,
      vz=0.0,
    )
    emitter = kernel.spawn_unit(
      ef_py.Side.Red,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      self._OPEN_WATER_X,
      self._OPEN_WATER_Y + 80_000.0,
      0.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=-10.29,
      vz=0.0,
    )

    passive_track_seen = False
    esm_warning_seen = False
    for _ in range(60):
      kernel.step()
      obs = kernel.get_agent_observation(int(ddg))
      passive_track_seen = passive_track_seen or any(
        int(track.id) == int(emitter) and int(track.source) == 2
        for track in obs.contacts
      )
      esm_warning_seen = esm_warning_seen or any(int(w.source_id) == int(emitter) for w in obs.rwr_warnings)

    self.assertTrue(passive_track_seen)
    self.assertTrue(esm_warning_seen)

  def test_real_ship_units_spawn_with_public_mass_and_no_aircraft_fuel(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(51)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      3.0,
      heading=90.0,
      pitch=5.0,
      roll=3.0,
      vx=20.0,
      vy=0.0,
      vz=1.0,
    )
    take = kernel.spawn_unit(
      ef_py.Side.Blue,
      "T-AKE-1_USNS_Lewis_and_Clark",
      -5000.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )

    self.assertEqual(kernel.get_unit_type(int(ddg)), int(ef_py.UnitType.Ship))
    self.assertEqual(kernel.get_unit_type(int(take)), int(ef_py.UnitType.Ship))

    ddg_mass = kernel.debug_get_mass_state(int(ddg))
    self.assertEqual(len(ddg_mass), 6)
    self.assertAlmostEqual(float(ddg_mass[0]), 8_362_000.0, delta=1.0)
    self.assertAlmostEqual(float(ddg_mass[1]), 0.0, places=6)
    self.assertAlmostEqual(float(ddg_mass[3]), 8_362_000.0, delta=1.0)
    self.assertAlmostEqual(float(ddg_mass[5]), 8_362_000.0, delta=1.0)
    self.assertEqual([float(v) for v in kernel.get_unit_fuel(int(ddg))], [0.0, 0.0, 0.0, 0.0])
    self.assertAlmostEqual(float(kernel.get_unit_health(int(ddg))[1]), 8362.0, places=6)

    take_mass = kernel.debug_get_mass_state(int(take))
    self.assertAlmostEqual(float(take_mass[0]), 41_000_000.0, delta=1.0)
    self.assertAlmostEqual(float(take_mass[3]), 41_000_000.0, delta=1.0)
    self.assertAlmostEqual(float(kernel.get_unit_health(int(take))[1]), 41000.0, places=6)

    kernel.step()

    ddg_vx, ddg_vy, ddg_vz = kernel.get_unit_velocity(int(ddg))
    self.assertLess(math.hypot(float(ddg_vx), float(ddg_vy)), 20.0)
    self.assertGreater(math.hypot(float(ddg_vx), float(ddg_vy)), 15.43)
    self.assertAlmostEqual(float(ddg_vz), 0.0, places=6)
    self.assertAlmostEqual(float(kernel.get_unit_position(int(ddg))[2]), 0.0, places=6)
    self.assertAlmostEqual(float(kernel.get_unit_heading(int(ddg))), 90.0, places=6)

    for _ in range(1500):
      kernel.step()
    ddg_vx, ddg_vy, _ = kernel.get_unit_velocity(int(ddg))
    self.assertAlmostEqual(math.hypot(float(ddg_vx), float(ddg_vy)), 15.43, places=2)

    kernel.send_message_command(int(ddg), int(take), 1, 1234)
    kernel.step()
    self.assertGreaterEqual(len(kernel.get_unit_messages(int(take))), 1)

  def test_real_ship_units_spawn_with_abstract_naval_stores(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(56)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )
    take = kernel.spawn_unit(
      ef_py.Side.Blue,
      "T-AKE-1_USNS_Lewis_and_Clark",
      -200.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )

    self.assertEqual(
      [float(v) for v in kernel.debug_get_naval_stores(int(ddg))],
      [45.0, 90.0, 72.0, 90.0, 18.0, 30.0],
    )
    self.assertEqual(
      [float(v) for v in kernel.debug_get_naval_stores(int(take))],
      [260.0, 260.0, 140.0, 140.0, 220.0, 220.0],
    )

  def test_underway_replenishment_transfers_abstract_stores_within_window(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(57)
    kernel.set_time_step(1.0)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )
    take = kernel.spawn_unit(
      ef_py.Side.Blue,
      "T-AKE-1_USNS_Lewis_and_Clark",
      -80.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )

    ddg_before = [float(v) for v in kernel.debug_get_naval_stores(int(ddg))]
    take_before = [float(v) for v in kernel.debug_get_naval_stores(int(take))]
    self.assertEqual(kernel.debug_get_resupply_state(int(ddg))[0], 0.0)

    activated = False
    for _ in range(30):
      kernel.step()
      state = [float(v) for v in kernel.debug_get_resupply_state(int(ddg))]
      if state[0] > 0.5:
        activated = True
        self.assertEqual(int(state[1]), 1)
        self.assertEqual(int(state[2]), int(take))
        break
    self.assertTrue(activated)

    ddg_after = [float(v) for v in kernel.debug_get_naval_stores(int(ddg))]
    take_after = [float(v) for v in kernel.debug_get_naval_stores(int(take))]
    self.assertGreater(ddg_after[0], ddg_before[0])
    self.assertGreater(ddg_after[2], ddg_before[2])
    self.assertGreater(ddg_after[4], ddg_before[4])
    self.assertLess(take_after[0], take_before[0])
    self.assertLess(take_after[2], take_before[2])
    self.assertLess(take_after[4], take_before[4])

  def test_underway_replenishment_does_not_start_outside_window(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(58)
    kernel.set_time_step(1.0)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )
    kernel.spawn_unit(
      ef_py.Side.Blue,
      "T-AKE-1_USNS_Lewis_and_Clark",
      -400.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=12.5,
      vy=0.0,
      vz=0.0,
    )

    ddg_before = [float(v) for v in kernel.debug_get_naval_stores(int(ddg))]
    for _ in range(30):
      kernel.step()
    self.assertEqual(kernel.debug_get_resupply_state(int(ddg))[0], 0.0)
    self.assertEqual([float(v) for v in kernel.debug_get_naval_stores(int(ddg))], ddg_before)

  def test_ship_heading_changes_gradually_under_command(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(52)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )
    kernel.set_command_link(int(ddg), 0.0, 0.0)

    cmd = ef_py.MissionCommand()
    cmd.active = True
    cmd.command_code = 3
    cmd.cmd_heading_deg = 0.0
    cmd.cmd_altitude_m = 0.0
    cmd.cmd_speed_mps = 10.29
    kernel.set_mission_command(int(ddg), cmd)

    kernel.step()
    first_heading = float(kernel.get_unit_heading(int(ddg)))
    self.assertLess(first_heading, 90.0)
    self.assertGreater(first_heading, 0.0)

    for _ in range(2250):
      kernel.step()
    final_heading = float(kernel.get_unit_heading(int(ddg)))
    self.assertLess(final_heading, first_heading)
    self.assertTrue(final_heading < 1.0 or final_heading > 359.0)

  def test_ship_mission_command_honors_link_latency_without_starvation(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(53)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )

    cmd = ef_py.MissionCommand()
    cmd.active = True
    cmd.command_code = 3
    cmd.cmd_heading_deg = 0.0
    cmd.cmd_altitude_m = 0.0
    cmd.cmd_speed_mps = 10.29
    kernel.set_mission_command(int(ddg), cmd)

    for _ in range(10):
      kernel.step()
    self.assertAlmostEqual(float(kernel.get_unit_heading(int(ddg))), 90.0, places=6)

    for _ in range(5):
      kernel.step()
    self.assertLess(float(kernel.get_unit_heading(int(ddg))), 90.0)

  def test_ship_near_zero_speed_does_not_turn_without_steerageway(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(54)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=0.1,
      vy=0.0,
      vz=0.0,
    )
    kernel.set_command_link(int(ddg), 0.0, 0.0)

    cmd = ef_py.MissionCommand()
    cmd.active = True
    cmd.command_code = 3
    cmd.cmd_heading_deg = 0.0
    cmd.cmd_altitude_m = 0.0
    cmd.cmd_speed_mps = 0.1
    kernel.set_mission_command(int(ddg), cmd)

    initial_heading = float(kernel.get_unit_heading(int(ddg)))
    for _ in range(120):
      kernel.step()
    final_heading = float(kernel.get_unit_heading(int(ddg)))
    self.assertAlmostEqual(final_heading, initial_heading, delta=0.2)

  def test_ship_sea_state_zero_keeps_level_attitude(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(55)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )

    for _ in range(120):
      kernel.step()
      obs = kernel.get_agent_observation(int(ddg))
      self.assertAlmostEqual(float(getattr(obs, "pitch", 0.0)), 0.0, places=6)
      self.assertAlmostEqual(float(getattr(obs, "roll", 0.0)), 0.0, places=6)

  def test_ship_sea_state_proxy_produces_bounded_pitch_and_roll(self) -> None:
    ddg_override = {
      "name": "DDG-51_Flight_I_USS_Arleigh_Burke",
      "type": "Ship",
      "ship_platform": {
        "displacement_light_kg": 6819000.0,
        "displacement_full_load_kg": 8362000.0,
        "length_m": 153.8,
        "beam_m": 20.4,
        "draft_m": 9.3,
        "height_above_waterline_m": 45.0,
        "max_speed_mps": 15.43,
        "economical_speed_mps": 10.29,
        "range_nm": 4400.0,
        "range_speed_mps": 10.29,
        "max_accel_mps2": 0.14,
        "max_decel_mps2": 0.2,
        "max_turn_rate_deg_s": 2.4,
        "low_speed_turn_factor": 0.3,
        "steerageway_speed_mps": 1.0,
        "sea_state": 5.0,
        "wave_heading_deg": 90.0,
        "wave_period_s": 8.0,
        "max_roll_deg_sea_state_6": 8.0,
        "max_pitch_deg_sea_state_6": 3.0,
        "added_resistance_fraction_sea_state_6": 0.12,
        "crew": 346,
      },
      "health": {"current_hp": 8362.0, "max_hp": 8362.0},
      "sensor_ref": "AN/SPS-67(V)_Surface_Search",
      "has_command_link": True,
      "command_link": {"latency_s": 0.2, "drop_prob": 0.0},
      "has_data_link": True,
      "data_link_network_id": 1,
    }
    kernel = self._load_database_with_ship_overrides(
      {"DDG-51_Flight_I_USS_Arleigh_Burke": ddg_override}
    )

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )

    max_abs_roll = 0.0
    max_abs_pitch = 0.0
    for _ in range(240):
      kernel.step()
      obs = kernel.get_agent_observation(int(ddg))
      max_abs_roll = max(max_abs_roll, abs(float(getattr(obs, "roll", 0.0))))
      max_abs_pitch = max(max_abs_pitch, abs(float(getattr(obs, "pitch", 0.0))))

    self.assertGreater(max_abs_roll, 0.5)
    self.assertGreater(max_abs_pitch, 0.2)
    self.assertLessEqual(max_abs_roll, 8.5)
    self.assertLessEqual(max_abs_pitch, 3.5)

  def test_ship_high_sea_state_reduces_steady_speed(self) -> None:
    base_ship = {
      "name": "DDG-51_Flight_I_USS_Arleigh_Burke",
      "type": "Ship",
      "ship_platform": {
        "displacement_light_kg": 6819000.0,
        "displacement_full_load_kg": 8362000.0,
        "length_m": 153.8,
        "beam_m": 20.4,
        "draft_m": 9.3,
        "height_above_waterline_m": 45.0,
        "max_speed_mps": 15.43,
        "economical_speed_mps": 10.29,
        "range_nm": 4400.0,
        "range_speed_mps": 10.29,
        "max_accel_mps2": 0.14,
        "max_decel_mps2": 0.2,
        "max_turn_rate_deg_s": 2.4,
        "low_speed_turn_factor": 0.3,
        "steerageway_speed_mps": 1.0,
        "wave_heading_deg": 0.0,
        "wave_period_s": 8.0,
        "max_roll_deg_sea_state_6": 8.0,
        "max_pitch_deg_sea_state_6": 3.0,
        "added_resistance_fraction_sea_state_6": 0.12,
        "crew": 346,
      },
      "health": {"current_hp": 8362.0, "max_hp": 8362.0},
      "sensor_ref": "AN/SPS-67(V)_Surface_Search",
      "has_command_link": True,
      "command_link": {"latency_s": 0.2, "drop_prob": 0.0},
      "has_data_link": True,
      "data_link_network_id": 1,
    }

    calm = json.loads(json.dumps(base_ship))
    calm["ship_platform"]["sea_state"] = 0.0
    rough = json.loads(json.dumps(base_ship))
    rough["ship_platform"]["sea_state"] = 6.0

    calm_kernel = self._load_database_with_ship_overrides(
      {"DDG-51_Flight_I_USS_Arleigh_Burke": calm}
    )
    rough_kernel = self._load_database_with_ship_overrides(
      {"DDG-51_Flight_I_USS_Arleigh_Burke": rough}
    )

    calm_ddg = calm_kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=15.43,
      vy=0.0,
      vz=0.0,
    )
    rough_ddg = rough_kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=15.43,
      vy=0.0,
      vz=0.0,
    )

    calm_kernel.set_command_link(int(calm_ddg), 0.0, 0.0)
    rough_kernel.set_command_link(int(rough_ddg), 0.0, 0.0)
    calm_cmd = ef_py.MissionCommand()
    calm_cmd.active = True
    calm_cmd.command_code = 3
    calm_cmd.cmd_heading_deg = 0.0
    calm_cmd.cmd_altitude_m = 0.0
    calm_cmd.cmd_speed_mps = 15.43
    rough_cmd = ef_py.MissionCommand()
    rough_cmd.active = True
    rough_cmd.command_code = 3
    rough_cmd.cmd_heading_deg = 0.0
    rough_cmd.cmd_altitude_m = 0.0
    rough_cmd.cmd_speed_mps = 15.43
    calm_kernel.set_mission_command(int(calm_ddg), calm_cmd)
    rough_kernel.set_mission_command(int(rough_ddg), rough_cmd)

    for _ in range(1500):
      calm_kernel.step()
      rough_kernel.step()

    calm_vx, calm_vy, _ = calm_kernel.get_unit_velocity(int(calm_ddg))
    rough_vx, rough_vy, _ = rough_kernel.get_unit_velocity(int(rough_ddg))
    calm_speed = math.hypot(float(calm_vx), float(calm_vy))
    rough_speed = math.hypot(float(rough_vx), float(rough_vy))
    self.assertGreater(calm_speed, rough_speed)
    self.assertAlmostEqual(calm_speed, 15.43, places=2)
    self.assertLess(rough_speed, 14.3)
    self.assertGreater(calm_speed - rough_speed, 1.0)

  def test_maritime_state_environment_override_takes_precedence_over_platform_default(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(56)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )

    kernel.set_maritime_state(5.0, 90.0, 8.0)
    sea_state, wave_heading_deg, wave_period_s = kernel.get_maritime_state()
    self.assertAlmostEqual(float(sea_state), 5.0, places=6)
    self.assertAlmostEqual(float(wave_heading_deg), 90.0, places=6)
    self.assertAlmostEqual(float(wave_period_s), 8.0, places=6)

    max_abs_roll = 0.0
    max_abs_pitch = 0.0
    for _ in range(240):
      kernel.step()
      obs = kernel.get_agent_observation(int(ddg))
      max_abs_roll = max(max_abs_roll, abs(float(getattr(obs, "roll", 0.0))))
      max_abs_pitch = max(max_abs_pitch, abs(float(getattr(obs, "pitch", 0.0))))

    self.assertGreater(max_abs_roll, 0.5)
    self.assertGreater(max_abs_pitch, 0.2)

  def test_red_surface_combatant_minimal_loads_as_hostile_placeholder(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(56)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    red = kernel.spawn_unit(
      ef_py.Side.Red,
      "Red_Surface_Combatant_Minimal",
      5000.0,
      0.0,
      0.0,
      heading=270.0,
      pitch=0.0,
      roll=0.0,
      vx=-10.29,
      vy=0.0,
      vz=0.0,
    )
    take = kernel.spawn_unit(
      ef_py.Side.Red,
      "T-AKE-1_USNS_Lewis_and_Clark",
      0.0,
      0.0,
      0.0,
      heading=270.0,
      pitch=0.0,
      roll=0.0,
      vx=-10.29,
      vy=0.0,
      vz=0.0,
    )

    self.assertEqual(kernel.get_unit_type(int(red)), int(ef_py.UnitType.Ship))
    self.assertEqual([float(v) for v in kernel.get_unit_fuel(int(red))], [0.0, 0.0, 0.0, 0.0])
    red_mass = kernel.debug_get_mass_state(int(red))
    take_mass = kernel.debug_get_mass_state(int(take))
    self.assertLess(float(red_mass[0]), float(take_mass[0]))
    self.assertLess(float(kernel.get_unit_health(int(red))[1]), float(kernel.get_unit_health(int(take))[1]))
    kernel.step()
    self.assertAlmostEqual(float(kernel.get_unit_heading(int(red))), 270.0, places=3)

  def test_ddg_loads_structured_naval_weapon_mounts(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(57)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )

    counts = kernel.debug_get_naval_weapon_counts(int(ddg))
    self.assertEqual(len(counts), 4)
    self.assertEqual(int(counts[0]), 4)
    self.assertEqual(int(counts[1]), 90)
    self.assertEqual(int(counts[2]), 20)
    self.assertEqual(int(counts[3]), 60)

  def test_ddg_vls_sam_requires_track_and_consumes_inventory(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(58)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )
    red = kernel.spawn_unit(
      ef_py.Side.Red,
      "Aircraft",
      0.0,
      15000.0,
      3000.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=-180.0,
      vz=0.0,
    )

    blocked = int(kernel.fire_missile(int(ddg), int(red)))
    self.assertEqual(blocked, 0)

    det = ef_py.Detection()
    det.target_id = int(red)
    det.range = 15000.0
    det.bearing = 0.0
    det.elevation = 11.0
    det.closing_speed = 180.0
    det.signal_strength = 1.0
    det.sensor_type = int(ef_py.SensorType.Radar)
    det.local_sensor_hit = True
    det.timestamp = 0.0
    kernel.set_contact_list(int(ddg), [det])

    before_counts = kernel.debug_get_naval_weapon_counts(int(ddg))
    first = int(kernel.fire_missile(int(ddg), int(red)))
    after_counts = kernel.debug_get_naval_weapon_counts(int(ddg))
    self.assertGreater(first, 0)
    self.assertEqual(int(before_counts[1]) - 1, int(after_counts[1]))

    second = int(kernel.fire_missile(int(ddg), int(red)))
    self.assertGreater(second, 0)
    after_second_counts = kernel.debug_get_naval_weapon_counts(int(ddg))
    self.assertEqual(int(before_counts[1]) - 2, int(after_second_counts[1]))

  def test_ship_hit_can_enter_intermediate_damage_state_without_immediate_loss(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(59)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    blue = kernel.spawn_unit(
      ef_py.Side.Blue,
      "Aircraft",
      0.0,
      0.0,
      3000.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=200.0,
      vz=0.0,
    )
    ddg = kernel.spawn_unit(
      ef_py.Side.Red,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      2500.0,
      0.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=0.0,
      vz=0.0,
    )

    self.assertTrue(kernel.debug_apply_proximity_hit(int(blue), int(ddg), 120.0, 80.0))

    self.assertTrue(kernel.is_unit_active(int(ddg)))
    damage = kernel.get_unit_damage_state(int(ddg))
    self.assertEqual(len(damage), 4)
    self.assertTrue(any(float(v) < 0.999 for v in damage[:3]))
    health = kernel.get_unit_health(int(ddg))
    self.assertGreater(float(health[0]), 0.0)
    obs = kernel.get_agent_observation(int(ddg))
    self.assertTrue(
      bool(getattr(obs, "health", 0.0) > 0.0)
    )

  def test_ddg_gun_can_fire_with_track_and_reduce_ammo(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(60)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=0.0,
      vz=0.0,
    )
    red = kernel.spawn_unit(
      ef_py.Side.Red,
      "Red_Surface_Combatant_Minimal",
      0.0,
      8000.0,
      0.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=0.0,
      vz=0.0,
    )

    det = ef_py.Detection()
    det.target_id = int(red)
    det.range = 8000.0
    det.bearing = 0.0
    det.elevation = 0.0
    det.closing_speed = 0.0
    det.signal_strength = 1.0
    det.sensor_type = int(ef_py.SensorType.Radar)
    det.local_sensor_hit = True
    det.timestamp = 0.0
    kernel.set_contact_list(int(ddg), [det])

    before = kernel.debug_get_naval_weapon_counts(int(ddg))
    fired = bool(kernel.fire_naval_weapon(int(ddg), int(red), 2))
    after = kernel.debug_get_naval_weapon_counts(int(ddg))
    self.assertTrue(fired)
    self.assertEqual(int(before[2]) - 1, int(after[2]))

  def test_ddg_ciws_can_intercept_close_missile(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(61)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=0.0,
      vz=0.0,
    )
    attacker = kernel.spawn_unit(
      ef_py.Side.Red,
      "Aircraft",
      0.0,
      -1000.0,
      100.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=200.0,
      vz=0.0,
    )

    self.assertTrue(kernel.debug_apply_proximity_hit(int(attacker), int(ddg), 20.0, 10.0))
    missile = kernel.spawn_unit(
      ef_py.Side.Red,
      "Missile",
      0.0,
      1200.0,
      50.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=-250.0,
      vz=0.0,
    )
    det = ef_py.Detection()
    det.target_id = int(missile)
    det.range = 1200.0
    det.bearing = 0.0
    det.elevation = 2.0
    det.closing_speed = 250.0
    det.signal_strength = 1.0
    det.sensor_type = int(ef_py.SensorType.Radar)
    det.local_sensor_hit = True
    det.timestamp = 0.0
    kernel.set_contact_list(int(ddg), [det])

    before = kernel.debug_get_naval_weapon_counts(int(ddg))
    fired = bool(kernel.fire_naval_weapon(int(ddg), int(missile), 3))
    after = kernel.debug_get_naval_weapon_counts(int(ddg))
    self.assertTrue(fired)
    self.assertFalse(kernel.is_unit_active(int(missile)))
    self.assertEqual(int(before[3]) - 1, int(after[3]))

  def test_naval_mission_command_can_trigger_ciws_without_direct_weapon_api(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(63)
    kernel.set_time_step(0.5)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=0.0,
      vz=0.0,
    )
    missile = kernel.spawn_unit(
      ef_py.Side.Red,
      "Missile",
      0.0,
      1000.0,
      50.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=-250.0,
      vz=0.0,
    )

    det = ef_py.Detection()
    det.target_id = int(missile)
    det.range = 1000.0
    det.bearing = 0.0
    det.elevation = 2.0
    det.closing_speed = 250.0
    det.signal_strength = 1.0
    det.sensor_type = int(ef_py.SensorType.Radar)
    det.local_sensor_hit = True
    det.timestamp = 0.0
    kernel.set_contact_list(int(ddg), [det])

    mission = ef_py.MissionCommand()
    mission.active = True
    mission.command_code = 34
    mission.authorization_to_fire = True
    mission.assigned_target_id = int(missile)
    mission.engagement_authority_holder_id = int(ddg)
    kernel.set_mission_command(int(ddg), mission)

    before = kernel.debug_get_naval_weapon_counts(int(ddg))
    for _ in range(4):
      kernel.step()
      after = kernel.debug_get_naval_weapon_counts(int(ddg))
      if int(after[3]) < int(before[3]):
        break
    else:
      after = kernel.debug_get_naval_weapon_counts(int(ddg))

    self.assertLess(int(after[3]), int(before[3]))

  def test_naval_mission_command_ciws_release_survives_named_system_seam(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(64)
    kernel.set_time_step(0.5)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=0.0,
      vz=0.0,
    )
    missile = kernel.spawn_unit(
      ef_py.Side.Red,
      "Missile",
      0.0,
      900.0,
      50.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=-250.0,
      vz=0.0,
    )

    det = ef_py.Detection()
    det.target_id = int(missile)
    det.range = 900.0
    det.bearing = 0.0
    det.elevation = 2.0
    det.closing_speed = 250.0
    det.signal_strength = 1.0
    det.sensor_type = int(ef_py.SensorType.Radar)
    det.local_sensor_hit = True
    det.timestamp = 0.0
    kernel.set_contact_list(int(ddg), [det])

    mission = ef_py.MissionCommand()
    mission.active = True
    mission.command_code = 34
    mission.authorization_to_fire = True
    mission.assigned_target_id = int(missile)
    mission.engagement_authority_holder_id = int(ddg)
    kernel.set_mission_command(int(ddg), mission)

    before = kernel.debug_get_naval_weapon_counts(int(ddg))
    kernel.step()
    after = kernel.debug_get_naval_weapon_counts(int(ddg))

    self.assertLess(int(after[3]), int(before[3]))
    self.assertFalse(kernel.is_unit_active(int(missile)))

  def test_set_mission_command_activates_the_naval_projection(self) -> None:
    """The setter's activation contract must reach NavalCommandIntent too."""
    kernel = ef_py.SimulationKernel()
    kernel.reset(65)
    kernel.set_time_step(0.5)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    ddg = int(
      kernel.spawn_unit(
        ef_py.Side.Blue,
        "DDG-51_Flight_I_USS_Arleigh_Burke",
        0.0,
        0.0,
        0.0,
        heading=90.0,
        pitch=0.0,
        roll=0.0,
        vx=10.29,
        vy=0.0,
        vz=0.0,
      )
    )
    kernel.set_command_link(ddg, 0.0, 0.0)

    mission = ef_py.MissionCommand()
    mission.active = False
    mission.cmd_heading_deg = 0.0
    mission.cmd_speed_mps = 10.29
    kernel.set_mission_command(ddg, mission)
    self.assertTrue(bool(kernel.get_mission_command(ddg).active))

    for _ in range(20):
      kernel.step()
    self.assertLess(float(kernel.get_unit_heading(ddg)), 90.0)

  def test_damage_state_can_continue_degrading_after_initial_hit(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(62)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    blue = kernel.spawn_unit(
      ef_py.Side.Blue,
      "Aircraft",
      0.0,
      0.0,
      1000.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=100.0,
      vz=0.0,
    )
    ddg = kernel.spawn_unit(
      ef_py.Side.Red,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      1500.0,
      0.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=0.0,
      vz=0.0,
    )

    self.assertTrue(kernel.debug_apply_proximity_hit(int(blue), int(ddg), 140.0, 80.0))
    initial = kernel.get_unit_damage_state(int(ddg))
    for _ in range(300):
      kernel.step()
    later = kernel.get_unit_damage_state(int(ddg))

    self.assertLess(float(later[0]), float(initial[0]))
    self.assertLess(float(later[3]), float(initial[3]))

  # --- DM-N1 response-profile tests -------------------------------------------

  def _response_spawn_ddg(self, kernel, y: float) -> int:
    entity_id = int(
      kernel.spawn_unit(
        ef_py.Side.Red,
        "DDG-51_Flight_I_USS_Arleigh_Burke",
        0.0,
        y,
        0.0,
        heading=0.0,
        pitch=0.0,
        roll=0.0,
        vx=0.0,
        vy=0.0,
        vz=0.0,
      )
    )
    self.assertTrue(kernel.is_unit_active(entity_id))
    return entity_id

  def _response_spawn_probe(self, kernel, y: float = 1500.0) -> int:
    return int(
      kernel.spawn_unit(
        ef_py.Side.Blue,
        "Aircraft",
        0.0,
        y,
        0.0,
        heading=180.0,
        pitch=0.0,
        roll=0.0,
        vx=0.0,
        vy=0.0,
        vz=0.0,
      )
    )

  def _response_aim_hit(self, kernel, probe_id: int, target_id: int,
                        aim_m: tuple[float, float, float]) -> None:
    # The local variant is required: `debug_apply_proximity_hit` places the
    # impact at local (0, 0, 2.0) for a non-air target, which is outside the DDG
    # hitboxes, so it cannot select a compartment and cannot reach the
    # breach/flooding family.
    self.assertTrue(
      kernel.debug_apply_local_proximity_hit(
        probe_id,
        target_id,
        aim_m[0],
        aim_m[1],
        aim_m[2],
        _RESPONSE_HIT_DAMAGE,
        _RESPONSE_HIT_FUSE_DISTANCE_M,
      )
    )

  def _response_counts(self, kernel, entity_id: int) -> list[float]:
    counts = kernel.debug_get_naval_weapon_counts(entity_id)
    self.assertEqual(len(counts), 4)
    return [float(value) for value in counts]

  def _response_force_surface_contact(self, kernel, ship_id: int, target_id: int,
                                      range_m: float) -> None:
    detection = ef_py.Detection()
    detection.target_id = int(target_id)
    detection.range = float(range_m)
    detection.bearing = 0.0
    detection.elevation = 0.0
    detection.closing_speed = 0.0
    detection.signal_strength = 1.0
    detection.sensor_type = int(ef_py.SensorType.Radar)
    detection.local_sensor_hit = True
    detection.timestamp = 0.0
    kernel.set_contact_list(ship_id, [detection])

  def _response_state_after_one_second(self, time_step_s: float) -> list[float]:
    kernel = ef_py.SimulationKernel()
    kernel.reset(20260922)
    kernel.set_time_step(time_step_s)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))
    ship_id = self._response_spawn_ddg(kernel, 0.0)
    probe_id = self._response_spawn_probe(kernel)
    self._response_aim_hit(kernel, probe_id, ship_id, _RESPONSE_AIM_AFT_ENGINEERING_M)

    for _ in range(int(round(1.0 / time_step_s))):
      kernel.step()
    return [float(value) for value in kernel.get_unit_damage_state(ship_id)]

  def test_response_profile_projection_is_clamped_and_monotone(self) -> None:
    """The declared profile's projection degrades, never rises, and clamps.

    A forward hit damages the combat-system family, which seeds fire severity and
    drives the mission/sensor channels. The declared coefficients are per-second
    rates, so the honest assertions are: every channel is monotonically
    non-increasing, the affected channels continue to degrade, and all values
    remain inside their capability clamps.
    """
    kernel = ef_py.SimulationKernel()
    kernel.reset(20260921)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))
    ship_id = self._response_spawn_ddg(kernel, 0.0)
    probe_id = self._response_spawn_probe(kernel)

    self._response_aim_hit(kernel, probe_id, ship_id, _RESPONSE_AIM_FORWARD_M)

    initial = [float(v) for v in kernel.get_unit_damage_state(ship_id)]
    self.assertEqual(len(initial), 4)
    self.assertTrue(any(value < 0.999 for value in initial))

    samples = [initial]
    for _ in range(4):
      for _ in range(20):
        kernel.step()
      samples.append([float(v) for v in kernel.get_unit_damage_state(ship_id)])

    labels = ("mission", "mobility", "sensor", "survivability")
    for index, label in enumerate(labels):
      for previous, current in zip(samples, samples[1:]):
        self.assertLessEqual(
          current[index],
          previous[index] + 1.0e-12,
          f"{label} capability must never increase",
        )
      self.assertLessEqual(samples[-1][index], initial[index])

    self.assertLess(samples[-1][_RESPONSE_MISSION], samples[0][_RESPONSE_MISSION])
    self.assertGreaterEqual(samples[-1][_RESPONSE_MISSION], 0.0)
    self.assertLess(samples[-1][_RESPONSE_SENSOR], samples[0][_RESPONSE_SENSOR])
    self.assertLess(samples[-1][_RESPONSE_SURVIVABILITY], samples[0][_RESPONSE_SURVIVABILITY])
    self.assertTrue(kernel.is_unit_active(ship_id))

  def test_breach_driven_flooding_grows_while_fire_decays(self) -> None:
    """Breach ingress and fire decay move the two channel families apart.

    An aft engineering/fuel hit is the only DDG aim point that seeds
    `ongoing_hull_breach`, so this is the reachable runtime instance of the
    breach-to-flooding coupling. Across two equal-length windows the
    flooding-driven channel (mobility) loses more capability per step later than
    earlier, while the fire-driven channel (mission) loses less: flooding
    accumulates toward its ingress/decay balance while fire decays away.
    Survivability carries both, so its ratio sits between the two.
    """
    kernel = ef_py.SimulationKernel()
    kernel.reset(20260921)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))
    ship_id = self._response_spawn_ddg(kernel, 0.0)
    probe_id = self._response_spawn_probe(kernel)

    self._response_aim_hit(kernel, probe_id, ship_id, _RESPONSE_AIM_AFT_ENGINEERING_M)
    hit = [float(v) for v in kernel.get_unit_damage_state(ship_id)]

    # The hit routed to the aft engineering/fuel compartment only, so the
    # radar/command family in the midships hitbox is untouched.
    self.assertEqual(hit[_RESPONSE_SENSOR], 1.0)

    def losses(steps: int) -> tuple[float, float, float]:
      before = [float(v) for v in kernel.get_unit_damage_state(ship_id)]
      for _ in range(steps):
        kernel.step()
      after = [float(v) for v in kernel.get_unit_damage_state(ship_id)]
      return (
        before[_RESPONSE_MISSION] - after[_RESPONSE_MISSION],
        before[_RESPONSE_MOBILITY] - after[_RESPONSE_MOBILITY],
        before[_RESPONSE_SURVIVABILITY] - after[_RESPONSE_SURVIVABILITY],
      )

    early_mission, early_mobility, early_survivability = losses(40)
    late_mission, late_mobility, late_survivability = losses(40)

    for label, value in (
      ("early mission", early_mission),
      ("late mission", late_mission),
      ("early mobility", early_mobility),
      ("late mobility", late_mobility),
      ("early survivability", early_survivability),
      ("late survivability", late_survivability),
    ):
      self.assertGreater(value, 0.0, f"{label} loss must stay positive")

    self.assertGreater(late_mobility, early_mobility)
    self.assertLess(late_mission, early_mission)

    mission_ratio = late_mission / early_mission
    mobility_ratio = late_mobility / early_mobility
    self.assertLess(mission_ratio, 1.0)
    self.assertGreater(mobility_ratio, 1.0)

    survivability_ratio = late_survivability / early_survivability
    self.assertGreater(survivability_ratio, mission_ratio)
    self.assertLess(survivability_ratio, mobility_ratio)

  def test_damage_response_rates_use_elapsed_step_time(self) -> None:
    """Changing the fixed step does not multiply the declared rates by tick count."""
    half_second = self._response_state_after_one_second(0.5)
    one_second = self._response_state_after_one_second(1.0)
    for half_value, one_value in zip(half_second, one_second):
      self.assertAlmostEqual(half_value, one_value, delta=5.0e-5)

  def test_mount_state_is_neutral_on_the_parity_default_profile(self) -> None:
    """The shipped default profile does not consume weapon-mount state.

    `mount_response_weight` is 0.0 on the parity default, so two identically
    damaged hulls evolve identically no matter how many rounds one of them has
    spent. This is the declared-coupling invariant: the mount input is read and
    projected, but it scales nothing until a profile declares a nonzero weight.
    """
    kernel = ef_py.SimulationKernel()
    kernel.reset(20260921)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))
    engaged_id = self._response_spawn_ddg(kernel, 0.0)
    probe_id = self._response_spawn_probe(kernel)
    pristine_id = self._response_spawn_ddg(kernel, 1000.0)

    pristine_counts = self._response_counts(kernel, pristine_id)
    self.assertEqual(int(pristine_counts[_RESPONSE_COUNT_GUN]), 20)
    self.assertEqual(int(pristine_counts[_RESPONSE_COUNT_VLS]), 90)
    self.assertEqual(int(pristine_counts[_RESPONSE_COUNT_CIWS]), 60)

    # Spend a deterministic CIWS burst on the engaged hull only. CIWS fires a
    # fixed three-round burst, so the spent count does not depend on the hull's
    # hit roll. The probe satisfies its close-in tracking requirement at 1500 m.
    self._response_force_surface_contact(kernel, engaged_id, probe_id, 1500.0)
    self.assertTrue(kernel.fire_naval_weapon(engaged_id, probe_id, _RESPONSE_CIWS_TYPE_CODE))
    engaged_counts = self._response_counts(kernel, engaged_id)
    self.assertGreater(
      int(pristine_counts[_RESPONSE_COUNT_CIWS]),
      int(engaged_counts[_RESPONSE_COUNT_CIWS]),
      "the engagement must actually spend mount rounds",
    )
    self.assertEqual(int(engaged_counts[_RESPONSE_COUNT_GUN]), int(pristine_counts[_RESPONSE_COUNT_GUN]))

    # Identical damage on both hulls through a fresh probe, so the engaged hull
    # cannot have lost its hit source to the burst.
    damage_probe_id = self._response_spawn_probe(kernel)
    self._response_aim_hit(kernel, damage_probe_id, engaged_id, _RESPONSE_AIM_AFT_ENGINEERING_M)
    self._response_aim_hit(kernel, damage_probe_id, pristine_id, _RESPONSE_AIM_AFT_ENGINEERING_M)

    engaged_initial = [float(v) for v in kernel.get_unit_damage_state(engaged_id)]
    pristine_initial = [float(v) for v in kernel.get_unit_damage_state(pristine_id)]
    for index in range(4):
      self.assertAlmostEqual(engaged_initial[index], pristine_initial[index], places=9)

    for _ in range(60):
      kernel.step()

    engaged_later = [float(v) for v in kernel.get_unit_damage_state(engaged_id)]
    pristine_later = [float(v) for v in kernel.get_unit_damage_state(pristine_id)]
    for index in range(4):
      self.assertAlmostEqual(engaged_later[index], pristine_later[index], places=9)

    # The damage response is identical despite different mount state, while both
    # hulls kept their distinct mount state throughout.
    self.assertGreater(engaged_initial[_RESPONSE_MOBILITY] - engaged_later[_RESPONSE_MOBILITY], 0.0)
    self.assertEqual(
      int(self._response_counts(kernel, engaged_id)[_RESPONSE_COUNT_CIWS]),
      int(engaged_counts[_RESPONSE_COUNT_CIWS]),
    )
    self.assertEqual(
      int(self._response_counts(kernel, pristine_id)[_RESPONSE_COUNT_CIWS]),
      int(pristine_counts[_RESPONSE_COUNT_CIWS]),
    )


if __name__ == "__main__":
  unittest.main()
