from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from textwrap import dedent

from python.testing.runtime import build_dir, resolve_repo_path


_REPO_ROOT = resolve_repo_path()
_BUILD_DIR = build_dir()
_DB_PATH = resolve_repo_path("examples", "config", "database")
_SCENARIO_PATH = resolve_repo_path("scenarios", "test", "test_aero.json")
_F16_PATH = resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json")
_ENGINE_PATH = resolve_repo_path("examples", "config", "database", "aircraft", "modules", "engines", "f110_ge_129.json")


def _run_probe(script: str) -> dict[str, float]:
  env = os.environ.copy()
  env["CMO_BUILD_DIR"] = _BUILD_DIR
  proc = subprocess.run(
    [sys.executable, "-c", script],
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
    import sys
    from python.testing.runtime import configure_sim_log_level
    configure_sim_log_level("error")
    import ef_py
    from gym_envs.scenario_loader import ScenarioLoader

    DB_PATH = r"{_DB_PATH}"
    SCENARIO_PATH = r"{_SCENARIO_PATH}"

    def make_action(throttle, stick_pitch=0.0, stick_roll=0.0):
      pa = ef_py.PilotAction()
      pa.active = True
      pa.throttle = float(throttle)
      pa.stick_pitch = float(stick_pitch)
      pa.stick_roll = float(stick_roll)
      pa.rudder = 0.0
      pa.gear_handle = 0.0
      pa.flaps = 0.0
      pa.speedbrake = 0.0
      pa.brake = 0.0
      pa.brake_left = False
      pa.brake_right = False
      pa.radar_active = False
      pa.radar_scan_az = 0.0
      pa.radar_scan_el = 0.0
      pa.tms_up = False
      pa.master_arm = False
      pa.fire_weapon = False
      pa.fire_gun = False
      pa.weapon_select_id = 0
      pa.program_chaff = False
      pa.program_flare = False
      pa.jettison_emergency = False
      return pa

    def spawn():
      sim = ef_py.SimulationKernel()
      assert sim.load_database(DB_PATH)
      loader = ScenarioLoader(sim)
      agent_id = int(loader.load_scenario(SCENARIO_PATH, seed=0))
      assert agent_id > 0
      return sim, agent_id

    def sample(sim, agent_id):
      inst = sim.get_instrument_state(agent_id)
      fd = sim.get_flight_dynamics_debug_view(agent_id)
      obs = sim.get_agent_observation(agent_id)
      fuel = sim.get_unit_fuel(agent_id)
      return {{
        "ias": float(getattr(inst, "ias", 0.0)),
        "aoa": float(getattr(inst, "aoa", 0.0)),
        "alpha_dot": float(getattr(fd, "alpha_dot_dps", 0.0)),
        "g": float(getattr(inst, "g_load", 0.0)),
        "rpm": float(getattr(inst, "engine_rpm", 0.0)),
        "fuel_flow": float(getattr(inst, "fuel_flow", 0.0)),
        "throttle_obs": float(getattr(obs, "throttle", 0.0)),
        "throttle_pos": float(getattr(inst, "throttle_pos", 0.0)),
        "throttle_state": float(getattr(fd, "throttle_state", 0.0)),
        "ab_state": float(getattr(fd, "ab_state", 0.0)),
        "current_tsfc": float(getattr(fd, "current_tsfc", 0.0)),
        "current_thrust_n": float(getattr(fd, "current_thrust_n", 0.0)),
        "stall_progress": float(getattr(fd, "stall_progress", 0.0)),
        "pitch_break_active": 1.0 if bool(getattr(fd, "pitch_break_active", False)) else 0.0,
        "alt": float(getattr(inst, "alt_baro", 0.0)),
        "vvi": float(getattr(inst, "vvi", 0.0)),
        "pitch": float(getattr(inst, "pitch", 0.0)),
        "fuel_internal": float(getattr(inst, "fuel_internal", 0.0)),
        "fuel_external": float(getattr(inst, "fuel_external", 0.0)),
        "fuel_internal_api": float(fuel[0]) if len(fuel) > 0 else 0.0,
        "fuel_external_api": float(fuel[2]) if len(fuel) > 2 else 0.0,
      }}

    def emit_result(payload):
      sys.stdout.write(json.dumps(payload))
      sys.stdout.flush()
      os._exit(0)
    """
  )


class FlightDynamicsRuntimeGuardTests(unittest.TestCase):
  def test_spawn_succeeds_with_and_without_flight_dynamics_tuning_config(self) -> None:
    default_spawn = _run_probe(
      _probe_prelude()
      + dedent(
        """
        sim = ef_py.SimulationKernel()
        assert sim.load_database(DB_PATH)
        entity_id = int(sim.spawn_unit(
          ef_py.Side.Blue,
          "F-16C_Block50",
          0.0, 0.0, 1000.0,
          0.0, 0.0, 0.0,
          200.0, 0.0, 0.0,
        ))
        inst = sim.get_instrument_state(entity_id)
        emit_result({
          "entity_id": entity_id,
          "ias": float(getattr(inst, "ias", 0.0)),
        })
        """
      )
    )
    self.assertGreater(default_spawn["entity_id"], 0)
    self.assertGreaterEqual(default_spawn["ias"], 0.0)

    with tempfile.TemporaryDirectory(prefix="cmo_fd_p1a_") as tmpdir:
      db_dir = os.path.join(tmpdir, "db")
      aircraft_dir = os.path.join(db_dir, "aircraft")
      units_dir = os.path.join(aircraft_dir, "units")
      engines_dir = os.path.join(aircraft_dir, "modules", "engines")
      os.makedirs(units_dir, exist_ok=True)
      os.makedirs(engines_dir, exist_ok=True)

      with open(_F16_PATH, "r", encoding="utf-8") as f:
        unit_data = json.load(f)
      with open(_ENGINE_PATH, "r", encoding="utf-8") as f:
        engine_data = json.load(f)

      unit_data.setdefault("airframe", {})
      unit_data["airframe"]["tuning"] = {
        "enabled": True,
        "cl_alpha_per_deg": 0.11,
        "pitch_break_onset_deg": 15.5,
        "pitch_break_full_deg": 26.0,
        "mach_breakpoints": [0.0, 0.9, 1.2],
        "cd0_add_vs_mach": [0.0, 0.01, 0.03],
      }
      engine_data.setdefault("engine", {})
      engine_data["engine"]["tuning"] = {
        "enabled": True,
        "tau_spool_up_s": 2.0,
        "tau_spool_down_s": 1.3,
        "tau_ab_light_s": 0.8,
        "tau_ab_extinguish_s": 0.4,
        "throttle_ab_threshold": 0.88,
        "tsfc_mil_kg_per_nh": 0.76,
        "tsfc_ab_kg_per_nh": 1.90,
      }

      tuned_unit_path = os.path.join(units_dir, "f16c_block50.json")
      tuned_engine_path = os.path.join(engines_dir, "f110_ge_129.json")
      with open(tuned_unit_path, "w", encoding="utf-8") as f:
        json.dump(unit_data, f)
      with open(tuned_engine_path, "w", encoding="utf-8") as f:
        json.dump(engine_data, f)

      tuned_spawn = _run_probe(
        _probe_prelude()
        + dedent(
          f"""
          sim = ef_py.SimulationKernel()
          assert sim.load_database(r"{db_dir}")
          entity_id = int(sim.spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            0.0, 0.0, 1000.0,
            0.0, 0.0, 0.0,
            200.0, 0.0, 0.0,
          ))
          inst = sim.get_instrument_state(entity_id)
          emit_result({{
            "entity_id": entity_id,
            "ias": float(getattr(inst, "ias", 0.0)),
          }})
          """
        )
      )
      self.assertGreater(tuned_spawn["entity_id"], 0)
      self.assertGreaterEqual(tuned_spawn["ias"], 0.0)

  def test_throttle_step_shows_spool_up_trend(self) -> None:
    result = _run_probe(
      _probe_prelude()
      + dedent(
        """
        sim, agent_id = spawn()
        idle = make_action(0.0)
        full = make_action(1.0)

        for _ in range(10):
          sim.set_pilot_action(agent_id, idle)
          sim.step()
        before = sample(sim, agent_id)

        sim.set_pilot_action(agent_id, full)
        sim.step()
        early = sample(sim, agent_id)

        for _ in range(39):
          sim.set_pilot_action(agent_id, full)
          sim.step()
        late = sample(sim, agent_id)

        emit_result({
          "before_rpm": before["rpm"],
          "early_rpm": early["rpm"],
          "late_rpm": late["rpm"],
          "before_throttle_state": before["throttle_state"],
          "early_throttle_state": early["throttle_state"],
          "late_throttle_state": late["throttle_state"],
          "before_tsfc": before["current_tsfc"],
          "late_tsfc": late["current_tsfc"],
          "early_fuel_flow": early["fuel_flow"],
          "late_fuel_flow": late["fuel_flow"],
          "before_ias": before["ias"],
          "late_ias": late["ias"],
        })
        """
      )
    )

    self.assertGreater(result["early_rpm"], result["before_rpm"] + 1.0)
    self.assertLess(result["early_rpm"], result["late_rpm"] - 1.0)
    self.assertGreater(result["early_throttle_state"], result["before_throttle_state"] + 0.01)
    self.assertGreater(result["late_throttle_state"], result["early_throttle_state"] + 0.01)
    self.assertGreater(result["late_tsfc"], 0.0)
    self.assertGreater(result["late_fuel_flow"], result["early_fuel_flow"] + 1000.0)
    self.assertGreater(result["late_ias"], result["before_ias"] + 1.0)

  def test_afterburner_command_pushes_rpm_fuel_flow_and_speed_above_mil(self) -> None:
    result = _run_probe(
      _probe_prelude()
      + dedent(
        """
        sim, agent_id = spawn()
        mil = make_action(0.85)
        ab = make_action(1.0)

        for _ in range(80):
          sim.set_pilot_action(agent_id, mil)
          sim.step()
        mil_state = sample(sim, agent_id)

        for _ in range(80):
          sim.set_pilot_action(agent_id, ab)
          sim.step()
        ab_state = sample(sim, agent_id)

        emit_result({
          "mil_rpm": mil_state["rpm"],
          "ab_rpm": ab_state["rpm"],
          "mil_ab_state": mil_state["ab_state"],
          "ab_ab_state": ab_state["ab_state"],
          "mil_tsfc": mil_state["current_tsfc"],
          "ab_tsfc": ab_state["current_tsfc"],
          "mil_fuel_flow": mil_state["fuel_flow"],
          "ab_fuel_flow": ab_state["fuel_flow"],
          "mil_ias": mil_state["ias"],
          "ab_ias": ab_state["ias"],
        })
        """
      )
    )

    self.assertGreater(result["ab_rpm"], result["mil_rpm"] + 1.0)
    self.assertGreater(result["ab_ab_state"], result["mil_ab_state"] + 0.05)
    self.assertGreater(result["ab_tsfc"], result["mil_tsfc"] + 0.1)
    self.assertGreater(result["ab_fuel_flow"], result["mil_fuel_flow"] + 1000.0)
    self.assertGreaterEqual(result["ab_ias"], 0.0)

  def test_propulsion_debug_instrument_and_observation_stay_consistent_at_partial_throttle(self) -> None:
    result = _run_probe(
      _probe_prelude()
      + dedent(
        """
        sim, agent_id = spawn()
        cruise = make_action(0.7)

        for _ in range(40):
          sim.set_pilot_action(agent_id, cruise)
          sim.step()

        state = sample(sim, agent_id)
        emit_result({
          "rpm": state["rpm"],
          "fuel_flow": state["fuel_flow"],
          "throttle_obs": state["throttle_obs"],
          "throttle_pos": state["throttle_pos"],
          "throttle_state": state["throttle_state"],
          "ab_state": state["ab_state"],
          "current_tsfc": state["current_tsfc"],
          "current_thrust_n": state["current_thrust_n"],
        })
        """
      )
    )

    expected_obs_throttle = result["throttle_state"] + (0.5 * result["ab_state"])
    self.assertAlmostEqual(result["throttle_pos"], 0.7, delta=0.05)
    self.assertAlmostEqual(result["throttle_obs"], expected_obs_throttle, delta=1.0e-6)
    self.assertAlmostEqual(result["rpm"], result["throttle_state"] * 100.0, delta=1.0)
    self.assertGreater(result["current_thrust_n"], 0.0)
    self.assertGreater(result["current_tsfc"], 0.0)
    self.assertGreater(result["fuel_flow"], 0.0)

  def test_fuel_inventory_decreases_monotonically_with_positive_propulsion_flow(self) -> None:
    result = _run_probe(
      _probe_prelude()
      + dedent(
        """
        sim, agent_id = spawn()
        cruise = make_action(0.7)

        for _ in range(10):
          sim.set_pilot_action(agent_id, cruise)
          sim.step()
        early = sample(sim, agent_id)

        for _ in range(30):
          sim.set_pilot_action(agent_id, cruise)
          sim.step()
        late = sample(sim, agent_id)

        emit_result({
          "early_fuel_flow": early["fuel_flow"],
          "late_fuel_flow": late["fuel_flow"],
          "early_internal": early["fuel_internal"],
          "late_internal": late["fuel_internal"],
          "early_internal_api": early["fuel_internal_api"],
          "late_internal_api": late["fuel_internal_api"],
          "late_external": late["fuel_external"],
          "late_external_api": late["fuel_external_api"],
        })
        """
      )
    )

    self.assertGreater(result["late_fuel_flow"], 0.0)
    self.assertGreaterEqual(result["late_fuel_flow"], result["early_fuel_flow"])
    self.assertLess(result["late_internal"], result["early_internal"])
    self.assertAlmostEqual(result["late_internal"], result["late_internal_api"], delta=0.05)
    self.assertAlmostEqual(result["late_external"], result["late_external_api"], delta=0.05)
    self.assertLess(result["late_internal_api"], result["early_internal_api"])

  def test_flight_dynamics_debug_state_exposes_spool_and_stall_trends(self) -> None:
    result = _run_probe(
      _probe_prelude()
      + dedent(
        """
        sim, agent_id = spawn()

        idle = make_action(0.0)
        full = make_action(1.0)
        for _ in range(20):
          sim.set_pilot_action(agent_id, idle)
          sim.step()
        idle_state = sample(sim, agent_id)

        for _ in range(60):
          sim.set_pilot_action(agent_id, full)
          sim.step()
        full_state = sample(sim, agent_id)

        peak_alpha_dot = 0.0
        peak_stall_progress = 0.0
        pitch_break_seen = 0.0
        pa = make_action(0.2, 1.0)
        for _ in range(120):
          sim.set_pilot_action(agent_id, pa)
          sim.step()
          state = sample(sim, agent_id)
          peak_alpha_dot = max(peak_alpha_dot, abs(state["alpha_dot"]))
          peak_stall_progress = max(peak_stall_progress, state["stall_progress"])
          pitch_break_seen = max(pitch_break_seen, state["pitch_break_active"])

        recovery_min_stall_progress = 999.0
        recovery_alpha_dot_min = 999.0
        pa = make_action(0.5, -0.6)
        for _ in range(120):
          sim.set_pilot_action(agent_id, pa)
          sim.step()
          state = sample(sim, agent_id)
          recovery_min_stall_progress = min(recovery_min_stall_progress, state["stall_progress"])
          recovery_alpha_dot_min = min(recovery_alpha_dot_min, state["alpha_dot"])

        emit_result({
          "idle_throttle_state": idle_state["throttle_state"],
          "full_throttle_state": full_state["throttle_state"],
          "idle_ab_state": idle_state["ab_state"],
          "full_ab_state": full_state["ab_state"],
          "idle_tsfc": idle_state["current_tsfc"],
          "full_tsfc": full_state["current_tsfc"],
          "peak_alpha_dot": peak_alpha_dot,
          "peak_stall_progress": peak_stall_progress,
          "pitch_break_seen": pitch_break_seen,
          "recovery_min_stall_progress": recovery_min_stall_progress,
          "recovery_alpha_dot_min": recovery_alpha_dot_min,
        })
        """
      )
    )

    self.assertGreater(result["full_throttle_state"], result["idle_throttle_state"] + 0.2)
    self.assertGreater(result["full_ab_state"], result["idle_ab_state"] + 0.05)
    self.assertGreater(result["full_tsfc"], result["idle_tsfc"] + 0.1)
    self.assertGreater(result["peak_alpha_dot"], 1.0)
    self.assertGreaterEqual(result["peak_stall_progress"], 0.0)
    self.assertGreaterEqual(result["pitch_break_seen"], 0.0)
    self.assertLess(result["recovery_alpha_dot_min"], -1.0)

  def test_high_aoa_entry_and_recovery_show_observable_trend(self) -> None:
    result = _run_probe(
      _probe_prelude()
      + dedent(
        """
        sim, agent_id = spawn()
        pa = make_action(0.2, 0.2)
        for _ in range(120):
          sim.set_pilot_action(agent_id, pa)
          sim.step()

        max_aoa = -999.0
        max_alpha_dot = 0.0
        max_stall_progress = 0.0
        pitch_break_seen = 0.0
        min_vvi_entry = 999.0
        pa = make_action(0.2, 1.0)
        for _ in range(120):
          sim.set_pilot_action(agent_id, pa)
          sim.step()
          state = sample(sim, agent_id)
          max_aoa = max(max_aoa, state["aoa"])
          max_alpha_dot = max(max_alpha_dot, state["alpha_dot"])
          max_stall_progress = max(max_stall_progress, state["stall_progress"])
          pitch_break_seen = max(pitch_break_seen, state["pitch_break_active"])
          min_vvi_entry = min(min_vvi_entry, state["vvi"])

        at_entry = sample(sim, agent_id)

        min_aoa_recovery = 999.0
        max_vvi_recovery = -999.0
        pa = make_action(0.5, -0.6)
        for _ in range(120):
          sim.set_pilot_action(agent_id, pa)
          sim.step()
          state = sample(sim, agent_id)
          min_aoa_recovery = min(min_aoa_recovery, state["aoa"])
          max_vvi_recovery = max(max_vvi_recovery, state["vvi"])

        recovered = sample(sim, agent_id)

        emit_result({
          "max_aoa_entry": max_aoa,
          "max_alpha_dot": max_alpha_dot,
          "max_stall_progress": max_stall_progress,
          "pitch_break_seen": pitch_break_seen,
          "entry_aoa": at_entry["aoa"],
          "entry_ias": at_entry["ias"],
          "entry_pitch": at_entry["pitch"],
          "min_vvi_entry": min_vvi_entry,
          "min_aoa_recovery": min_aoa_recovery,
          "max_vvi_recovery": max_vvi_recovery,
          "recovered_aoa": recovered["aoa"],
          "recovered_pitch": recovered["pitch"],
        })
        """
      )
    )

    self.assertGreater(result["max_aoa_entry"], 11.0)
    self.assertGreater(result["max_alpha_dot"], 1.0)
    self.assertGreaterEqual(result["max_stall_progress"], 0.0)
    self.assertGreaterEqual(result["pitch_break_seen"], 0.0)
    self.assertGreater(result["entry_pitch"], 60.0)
    self.assertGreater(result["entry_ias"], 100.0)
    self.assertGreater(result["min_aoa_recovery"], -20.0)
    self.assertLess(result["min_aoa_recovery"], result["entry_aoa"] - 8.0)
    self.assertGreater(result["max_vvi_recovery"], result["min_vvi_entry"] - 1.0)
    self.assertLess(result["recovered_pitch"], result["entry_pitch"] - 40.0)

  def test_default_moderate_path_remains_substall_and_finite(self) -> None:
    result = _run_probe(
      _probe_prelude()
      + dedent(
        """
        sim, agent_id = spawn()
        pa = make_action(0.8, 0.25, 0.2)
        max_aoa = 0.0
        max_abs_g = 0.0
        min_rpm = 1.0e9
        max_rpm = -1.0e9
        for _ in range(100):
          sim.set_pilot_action(agent_id, pa)
          sim.step()
          state = sample(sim, agent_id)
          max_aoa = max(max_aoa, abs(state["aoa"]))
          max_abs_g = max(max_abs_g, abs(state["g"]))
          min_rpm = min(min_rpm, state["rpm"])
          max_rpm = max(max_rpm, state["rpm"])
        final = sample(sim, agent_id)
        emit_result({
          "max_aoa": max_aoa,
          "max_abs_g": max_abs_g,
          "min_rpm": min_rpm,
          "max_rpm": max_rpm,
          "final_ias": final["ias"],
          "final_alt": final["alt"],
        })
        """
      )
    )

    self.assertLess(result["max_aoa"], 10.0)
    self.assertLess(result["max_abs_g"], 4.2)
    self.assertGreaterEqual(result["min_rpm"], 0.0)
    self.assertLess(result["max_rpm"], 95.0)
    self.assertGreater(result["final_ias"], 150.0)
    self.assertGreater(result["final_alt"], 900.0)


if __name__ == "__main__":
  unittest.main()
