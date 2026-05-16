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


def _make_tuned_database() -> tuple[str, str]:
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
    unit_data["airframe"]["tuning"] = {
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
    engine_data["engine"]["tuning"] = {
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


if __name__ == "__main__":
    unittest.main()
