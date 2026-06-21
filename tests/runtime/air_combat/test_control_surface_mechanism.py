"""RED-phase mechanism tests for the flight control-surface model.

Subproject: docs/task/air_combat/flight_control_surface_model/

These tests assert the CAUSAL MECHANISM that is currently missing, not the
output behavior that already works. The existing FBW rate-command path already
makes the aircraft pitch/roll/yaw when commanded, so a test on "does it pitch"
would already be GREEN and prove nothing.

The missing mechanism is the *physical surface-deflection intermediary*:

    stick -> FBW law -> surface command delta_cmd
          -> actuator dynamics (rate/limit) -> actual deflection delta
          -> control moment  Cm_delta_e * delta  (scaled by q_bar, mach)

Today control moments are synthesized directly as
``M = q_bar * K * (rate_cmd - rate)`` with no surface state in between.

Therefore these tests assert on an observable surface-deflection state that
does not exist yet. They are EXPECTED TO FAIL until the ControlSurfaceState
component, the actuator system, and the surface debug surface are implemented
and ef_py is rebuilt.

Mechanism claims (all currently FALSE):
  M1 surface deflection is an observable runtime state
  M2 a sustained pitch command drives a nonzero elevator deflection
  M3 deflection exhibits actuator lag (gradual, not an instantaneous jump)
  M4 deflection saturates at a finite max travel (does not grow unbounded)

This file deliberately does NOT yet assert the damage->effectiveness coupling
(M5) because that requires confirming a damage-injection path; it is tracked as
a follow-on assertion in the task-cluster doc to avoid over-scoping the RED set.
"""

from __future__ import annotations

import unittest

from python.testing.runtime import configure_sim_log_level, resolve_repo_path


configure_sim_log_level("error")

import ef_py  # noqa: E402
from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")
_SCENARIO_PATH = resolve_repo_path("scenarios", "test", "test_aero.json")

# Surface-deflection debug fields this subproject must expose on the
# flight-dynamics debug view. Named here so the RED failure is a clear missing
# mechanism, not an opaque AttributeError deep in a loop.
_SURFACE_FIELDS = (
    "elevator_deflection",
    "aileron_deflection",
    "rudder_deflection",
)


def _spawn():
    sim = ef_py.SimulationKernel()
    if not sim.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")
    loader = ScenarioLoader(sim)
    agent_id = int(loader.load_scenario(_SCENARIO_PATH, seed=0))
    if agent_id <= 0:
        raise AssertionError("scenario did not spawn an agent")
    return sim, agent_id


def _pilot(*, throttle: float, stick_pitch: float = 0.0, stick_roll: float = 0.0,
           rudder: float = 0.0) -> "ef_py.PilotAction":
    pa = ef_py.PilotAction()
    pa.active = True
    pa.throttle = float(throttle)
    pa.stick_pitch = float(stick_pitch)
    pa.stick_roll = float(stick_roll)
    pa.rudder = float(rudder)
    pa.gear_handle = 0.0
    pa.flaps = 0.0
    pa.speedbrake = 0.0
    pa.brake = 0.0
    return pa


def _surface_deflections(sim, agent_id) -> dict[str, float]:
    view = sim.get_flight_dynamics_debug_view(agent_id)
    out: dict[str, float] = {}
    for field in _SURFACE_FIELDS:
        if not hasattr(view, field):
            raise AssertionError(
                f"flight-dynamics debug view is missing surface field '{field}'. "
                "The control-surface mechanism (ControlSurfaceState + actuator "
                "system + surface debug exposure) is not implemented yet."
            )
        out[field] = float(getattr(view, field))
    return out


class ControlSurfaceMechanismTests(unittest.TestCase):
    def test_m1_surface_deflection_state_is_observable(self) -> None:
        sim, agent_id = _spawn()
        # Just reading the fields proves the mechanism's state exists.
        defl = _surface_deflections(sim, agent_id)
        self.assertEqual(set(defl.keys()), set(_SURFACE_FIELDS))

    def test_m2_sustained_pitch_command_drives_elevator_deflection(self) -> None:
        sim, agent_id = _spawn()
        pa = _pilot(throttle=0.8, stick_pitch=0.5)
        for _ in range(40):
            sim.set_pilot_action(agent_id, pa)
            sim.step()
        defl = _surface_deflections(sim, agent_id)
        self.assertGreater(
            abs(defl["elevator_deflection"]),
            1.0e-3,
            "sustained pitch stick must produce a nonzero elevator deflection",
        )

    def test_actuator_lag_makes_deflection_gradual_not_instant(self) -> None:
        sim, agent_id = _spawn()
        pa = _pilot(throttle=0.8, stick_pitch=1.0)  # full step demand

        sim.set_pilot_action(agent_id, pa)
        sim.step()
        first_step = abs(_surface_deflections(sim, agent_id)["elevator_deflection"])

        for _ in range(60):
            sim.set_pilot_action(agent_id, pa)
            sim.step()
        steady = abs(_surface_deflections(sim, agent_id)["elevator_deflection"])

        self.assertGreater(steady, 1.0e-3, "steady deflection should be nonzero")
        self.assertLess(
            first_step,
            steady * 0.9,
            "actuator lag: a full step demand must not reach steady deflection "
            "in a single timestep",
        )

    def test_m4_deflection_saturates_at_finite_travel(self) -> None:
        sim, agent_id = _spawn()
        pa = _pilot(throttle=0.8, stick_pitch=1.0)
        for _ in range(120):
            sim.set_pilot_action(agent_id, pa)
            sim.step()
        defl = _surface_deflections(sim, agent_id)
        # A real control surface cannot deflect past its mechanical travel.
        # 40 deg is a generous upper bound for any maintained airframe.
        self.assertLessEqual(
            abs(defl["elevator_deflection"]),
            40.0,
            "elevator deflection must saturate at a finite mechanical travel",
        )


if __name__ == "__main__":
    unittest.main()
