from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from textwrap import dedent

from python.testing.runtime import build_dir, resolve_repo_path


_REPO_ROOT = resolve_repo_path()
_BUILD_DIR = build_dir()
_DB_PATH = resolve_repo_path("examples", "config", "database")
_F16_PATH = resolve_repo_path(
    "examples",
    "config",
    "database",
    "aircraft",
    "units",
    "f16c_block50.json",
)
_ENGINE_PATH = resolve_repo_path(
    "examples",
    "config",
    "database",
    "aircraft",
    "modules",
    "engines",
    "f110_ge_129.json",
)


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


def _probe_prelude(db_path: str) -> str:
    return dedent(
        f"""
        import json
        import os
        import sys
        from python.testing.runtime import configure_sim_log_level

        configure_sim_log_level("error")

        import ef_py

        DB_PATH = r"{db_path}"

        def make_action(throttle, stick_pitch=0.0):
            pa = ef_py.PilotAction()
            pa.active = True
            pa.throttle = float(throttle)
            pa.stick_pitch = float(stick_pitch)
            pa.stick_roll = 0.0
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

        def spawn_kernel_and_entity():
            sim = ef_py.SimulationKernel()
            assert sim.load_database(DB_PATH), DB_PATH
            entity_id = int(sim.spawn_unit(
                ef_py.Side.Blue,
                "F-16C_Block50",
                0.0, 0.0, 1200.0,
                0.0, 0.0, 0.0,
                200.0, 0.0, 0.0,
            ))
            assert entity_id > 0
            return sim, entity_id

        def sample(sim, entity_id):
            inst = sim.get_instrument_state(entity_id)
            fd = sim.get_flight_dynamics_debug_view(entity_id)
            return {{
                "ias": float(getattr(inst, "ias", 0.0)),
                "aoa": float(getattr(inst, "aoa", 0.0)),
                "rpm": float(getattr(inst, "engine_rpm", 0.0)),
                "fuel_flow": float(getattr(inst, "fuel_flow", 0.0)),
                "throttle_state": float(getattr(fd, "throttle_state", 0.0)),
                "ab_state": float(getattr(fd, "ab_state", 0.0)),
                "current_tsfc": float(getattr(fd, "current_tsfc", 0.0)),
                "stall_progress": float(getattr(fd, "stall_progress", 0.0)),
                "pitch_break_active": 1.0 if bool(getattr(fd, "pitch_break_active", False)) else 0.0,
            }}

        def emit_result(payload):
            sys.stdout.write(json.dumps(payload))
            sys.stdout.flush()
            os._exit(0)
        """
    )


def _make_tuned_database(
    *,
    airframe_tuning: dict | None = None,
    engine_tuning: dict | None = None,
) -> tuple[str, str]:
    tmpdir = tempfile.mkdtemp(prefix="cmo_fd_tuning_")
    db_dir = os.path.join(tmpdir, "db")
    units_dir = os.path.join(db_dir, "aircraft", "units")
    engines_dir = os.path.join(db_dir, "aircraft", "modules", "engines")
    os.makedirs(units_dir, exist_ok=True)
    os.makedirs(engines_dir, exist_ok=True)

    with open(_F16_PATH, "r", encoding="utf-8") as f:
        unit_data = json.load(f)
    with open(_ENGINE_PATH, "r", encoding="utf-8") as f:
        engine_data = json.load(f)

    unit_data.setdefault("airframe", {})
    unit_data["airframe"]["tuning"] = airframe_tuning or {
        "enabled": True,
        "alpha_stall_clean_deg": 6.0,
        "alpha_stall_flaps_full_deg": 8.0,
        "alpha_peak_offset_deg": 3.0,
        "alpha_deep_offset_deg": 5.0,
        "pitch_break_onset_deg": 5.5,
        "pitch_break_full_deg": 8.5,
        "pitch_break_cm_nose_down": -0.5,
    }

    engine_data.setdefault("engine", {})
    engine_data["engine"]["tuning"] = engine_tuning or {
        "enabled": True,
        "throttle_ab_threshold": 0.55,
        "tau_spool_up_s": 0.6,
        "tau_spool_down_s": 0.5,
        "tau_ab_light_s": 0.25,
        "tau_ab_extinguish_s": 0.2,
        "tsfc_mil_kg_per_nh": 0.76,
        "tsfc_ab_kg_per_nh": 1.90,
    }

    with open(os.path.join(units_dir, "f16c_block50.json"), "w", encoding="utf-8") as f:
        json.dump(unit_data, f)
    with open(os.path.join(engines_dir, "f110_ge_129.json"), "w", encoding="utf-8") as f:
        json.dump(engine_data, f)

    return tmpdir, db_dir


class FlightDynamicsTuningRuntimeTests(unittest.TestCase):
    def test_default_and_explicit_tuning_paths_spawn_and_step(self) -> None:
        default_result = _run_probe(
            _probe_prelude(_DB_PATH)
            + dedent(
                """
                sim, entity_id = spawn_kernel_and_entity()
                for _ in range(5):
                    sim.set_pilot_action(entity_id, make_action(0.6))
                    sim.step()
                state = sample(sim, entity_id)
                emit_result({
                    "entity_id": float(entity_id),
                    "ias": state["ias"],
                    "rpm": state["rpm"],
                    "stall_progress": state["stall_progress"],
                })
                """
            )
        )

        self.assertGreater(default_result["entity_id"], 0.0)
        self.assertGreaterEqual(default_result["ias"], 0.0)
        self.assertGreaterEqual(default_result["rpm"], 0.0)
        self.assertGreaterEqual(default_result["stall_progress"], 0.0)

        tuned_tmpdir, tuned_db_dir = _make_tuned_database()
        self.addCleanup(shutil.rmtree, tuned_tmpdir, True)
        tuned_result = _run_probe(
            _probe_prelude(tuned_db_dir)
            + dedent(
                """
                sim, entity_id = spawn_kernel_and_entity()
                for _ in range(5):
                    sim.set_pilot_action(entity_id, make_action(0.6))
                    sim.step()
                state = sample(sim, entity_id)
                emit_result({
                    "entity_id": float(entity_id),
                    "ias": state["ias"],
                    "rpm": state["rpm"],
                    "stall_progress": state["stall_progress"],
                })
                """
            )
        )

        self.assertGreater(tuned_result["entity_id"], 0.0)
        self.assertGreaterEqual(tuned_result["ias"], 0.0)
        self.assertGreaterEqual(tuned_result["rpm"], 0.0)
        self.assertGreaterEqual(tuned_result["stall_progress"], 0.0)

    def test_explicit_tuning_changes_propulsion_and_stall_observability(self) -> None:
        tuned_tmpdir, tuned_db_dir = _make_tuned_database()
        self.addCleanup(shutil.rmtree, tuned_tmpdir, True)

        default_result = _run_probe(
            _probe_prelude(_DB_PATH)
            + dedent(
                """
                sim, entity_id = spawn_kernel_and_entity()
                level = make_action(0.7)
                for _ in range(60):
                    sim.set_pilot_action(entity_id, level)
                    sim.step()
                level_state = sample(sim, entity_id)

                high_aoa = make_action(0.3, 0.65)
                max_stall_progress = 0.0
                pitch_break_seen = 0.0
                for _ in range(80):
                    sim.set_pilot_action(entity_id, high_aoa)
                    sim.step()
                    state = sample(sim, entity_id)
                    max_stall_progress = max(max_stall_progress, state["stall_progress"])
                    pitch_break_seen = max(pitch_break_seen, state["pitch_break_active"])

                emit_result({
                    "ab_state": level_state["ab_state"],
                    "current_tsfc": level_state["current_tsfc"],
                    "rpm": level_state["rpm"],
                    "max_stall_progress": max_stall_progress,
                    "pitch_break_seen": pitch_break_seen,
                })
                """
            )
        )

        tuned_result = _run_probe(
            _probe_prelude(tuned_db_dir)
            + dedent(
                """
                sim, entity_id = spawn_kernel_and_entity()
                level = make_action(0.7)
                for _ in range(60):
                    sim.set_pilot_action(entity_id, level)
                    sim.step()
                level_state = sample(sim, entity_id)

                high_aoa = make_action(0.3, 0.65)
                max_stall_progress = 0.0
                pitch_break_seen = 0.0
                for _ in range(80):
                    sim.set_pilot_action(entity_id, high_aoa)
                    sim.step()
                    state = sample(sim, entity_id)
                    max_stall_progress = max(max_stall_progress, state["stall_progress"])
                    pitch_break_seen = max(pitch_break_seen, state["pitch_break_active"])

                emit_result({
                    "ab_state": level_state["ab_state"],
                    "current_tsfc": level_state["current_tsfc"],
                    "rpm": level_state["rpm"],
                    "max_stall_progress": max_stall_progress,
                    "pitch_break_seen": pitch_break_seen,
                })
                """
            )
        )

        self.assertLess(default_result["ab_state"], 0.05)
        self.assertGreater(tuned_result["ab_state"], default_result["ab_state"] + 0.10)
        self.assertGreater(tuned_result["current_tsfc"], default_result["current_tsfc"] + 0.20)
        self.assertGreater(tuned_result["rpm"], default_result["rpm"] + 5.0)
        self.assertGreater(
            tuned_result["max_stall_progress"],
            default_result["max_stall_progress"] + 0.01,
        )
        self.assertGreater(tuned_result["pitch_break_seen"], default_result["pitch_break_seen"])

    def test_stall_state_retains_memory_during_brief_unload_and_clears_with_sustained_recovery(self) -> None:
        tuned_tmpdir, tuned_db_dir = _make_tuned_database(
            airframe_tuning={
                "enabled": True,
                "alpha_stall_clean_deg": 4.0,
                "alpha_stall_flaps_full_deg": 5.0,
                "alpha_peak_offset_deg": 1.0,
                "alpha_deep_offset_deg": 2.0,
                "pitch_break_onset_deg": 4.2,
                "pitch_break_full_deg": 5.5,
                "pitch_break_cm_nose_down": -0.7,
            }
        )
        self.addCleanup(shutil.rmtree, tuned_tmpdir, True)
        result = _run_probe(
            _probe_prelude(tuned_db_dir)
            + dedent(
                """
                sim, entity_id = spawn_kernel_and_entity()

                level = make_action(0.7)
                for _ in range(60):
                    sim.set_pilot_action(entity_id, level)
                    sim.step()

                entry = make_action(0.2, 1.0)
                brief_recovery = make_action(0.5, -0.35)
                sustained_recovery = make_action(0.85, -0.5)

                peak_stall_progress = 0.0
                peak_time_in_stall = 0.0
                peak_pitch_break = 0.0
                for _ in range(120):
                    sim.set_pilot_action(entity_id, entry)
                    sim.step()
                    state = sample(sim, entity_id)
                    debug = sim.get_flight_dynamics_debug_view(entity_id)
                    peak_stall_progress = max(peak_stall_progress, state["stall_progress"])
                    peak_time_in_stall = max(
                        peak_time_in_stall,
                        float(getattr(debug, "time_in_stall_s", 0.0)),
                    )
                    peak_pitch_break = max(
                        peak_pitch_break,
                        1.0 if bool(getattr(debug, "pitch_break_active", False)) else 0.0,
                    )

                for _ in range(6):
                    sim.set_pilot_action(entity_id, brief_recovery)
                    sim.step()
                brief_state = sample(sim, entity_id)
                brief_debug = sim.get_flight_dynamics_debug_view(entity_id)

                recovery_min_stall_progress = 999.0
                recovery_min_time_in_stall = 999.0
                recovery_pitch_break_cleared = 0.0
                for _ in range(240):
                    sim.set_pilot_action(entity_id, sustained_recovery)
                    sim.step()
                    state = sample(sim, entity_id)
                    debug = sim.get_flight_dynamics_debug_view(entity_id)
                    recovery_min_stall_progress = min(recovery_min_stall_progress, state["stall_progress"])
                    recovery_min_time_in_stall = min(
                        recovery_min_time_in_stall,
                        float(getattr(debug, "time_in_stall_s", 0.0)),
                    )
                    if not bool(getattr(debug, "pitch_break_active", False)):
                        recovery_pitch_break_cleared = 1.0

                emit_result({
                    "peak_stall_progress": peak_stall_progress,
                    "peak_time_in_stall": peak_time_in_stall,
                    "peak_pitch_break": peak_pitch_break,
                    "brief_stall_progress": brief_state["stall_progress"],
                    "brief_pitch_break": 1.0 if bool(getattr(brief_debug, "pitch_break_active", False)) else 0.0,
                    "brief_time_in_stall": float(getattr(brief_debug, "time_in_stall_s", 0.0)),
                    "recovery_min_stall_progress": recovery_min_stall_progress,
                    "recovery_min_time_in_stall": recovery_min_time_in_stall,
                    "recovery_pitch_break_cleared": recovery_pitch_break_cleared,
                })
                """
            )
        )

        self.assertGreater(result["peak_stall_progress"], 0.20)
        self.assertGreater(result["peak_time_in_stall"], 1.0)
        self.assertGreater(result["peak_pitch_break"], 0.0)
        self.assertGreater(result["brief_stall_progress"], 0.10)
        self.assertGreater(result["brief_time_in_stall"], 1.0)
        self.assertGreater(result["brief_pitch_break"], 0.0)
        self.assertLess(result["brief_stall_progress"], result["peak_stall_progress"] - 0.05)
        self.assertLess(result["recovery_min_stall_progress"], 0.02)
        self.assertLess(result["recovery_min_time_in_stall"], 0.05)
        self.assertEqual(result["recovery_pitch_break_cleared"], 1.0)


if __name__ == "__main__":
    unittest.main()
