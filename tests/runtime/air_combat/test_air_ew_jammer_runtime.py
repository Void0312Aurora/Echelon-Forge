"""Runtime evidence for the cockpit jammer switch reaching the radar model.

The native EW owner keys the installed pod from the PilotAction ECM panel;
the existing sensor model then applies its noise-jamming suppression to the
hostile radar scan. These tests pin that end-to-end path, not the
suppression coefficients themselves (those remain an uncalibrated sensing
proxy owned by systems/sensing).
"""

from __future__ import annotations

import ef_py
import pytest

from python.runtime_bootstrap import resolve_repo_path


DATABASE = resolve_repo_path("examples", "config", "database")
_STEP_S = 0.05
_WINDOW_S = 30.0


def _hostile_track_frames(*, separation_m: float, transmit: bool, mode: int) -> tuple[int, int, object]:
    kernel = ef_py.SimulationKernel()
    assert kernel.load_database(DATABASE)
    kernel.reset(7)
    kernel.set_time_step(_STEP_S)
    blue = int(
        kernel.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 0.0, 200.0, 0.0)
    )
    red = int(
        kernel.spawn_unit(
            ef_py.Side.Red, "F-16C_Block50", 0.0, separation_m, 5000.0, 180.0, 0.0, 0.0, 0.0, -200.0, 0.0
        )
    )
    blue_action = ef_py.PilotAction()
    blue_action.active = True
    blue_action.throttle = 0.6
    blue_action.jammer_transmit = transmit
    blue_action.jammer_mode = mode
    red_action = ef_py.PilotAction()
    red_action.active = True
    red_action.throttle = 0.6

    steps = int(round(_WINDOW_S / _STEP_S))
    tracked = 0
    for _ in range(steps):
        kernel.set_pilot_action(blue, blue_action)
        kernel.set_pilot_action(red, red_action)
        kernel.step()
        contacts = kernel.get_agent_observation(red).contacts
        if any(int(contact.id) == blue for contact in contacts):
            tracked += 1
    return tracked, steps, kernel.get_instrument_state(blue)


def test_noise_jamming_denies_the_hostile_radar_track_beyond_burn_through() -> None:
    # Head-on at 60 km closing to ~50 km: outside the sensor model's burn-through
    # range for the gen-4 suite, inside the APG-68 detection range.
    clear, steps, clear_inst = _hostile_track_frames(separation_m=60000.0, transmit=False, mode=0)
    jammed, _, jammed_inst = _hostile_track_frames(separation_m=60000.0, transmit=True, mode=0)

    assert clear > steps // 2, "premise: the hostile radar tracks an unjammed target"
    assert clear_inst.jammer_transmitting is False
    assert jammed_inst.jammer_transmitting is True
    assert jammed_inst.jammer_mode == 0
    assert jammed == 0


@pytest.mark.parametrize("mode", [0, 1])
def test_noise_jamming_track_denial_is_range_dependent(mode: int) -> None:
    # From 40 km the closure passes inside burn-through, so the radar regains
    # the track part-way through the window instead of never or always.
    jammed, steps, _ = _hostile_track_frames(separation_m=40000.0, transmit=True, mode=mode)
    clear, _, _ = _hostile_track_frames(separation_m=40000.0, transmit=False, mode=mode)
    assert clear == steps
    assert 0 < jammed < clear


def test_drfm_technique_is_admitted_but_has_no_radar_effect_yet() -> None:
    # Residual pin: the sensor model only implements noise suppression. DRFM
    # is accepted by the native owner and reported, but does not change the
    # hostile track until a deception model is admitted.
    clear, _, _ = _hostile_track_frames(separation_m=60000.0, transmit=False, mode=2)
    drfm, _, inst = _hostile_track_frames(separation_m=60000.0, transmit=True, mode=2)
    assert inst.jammer_transmitting is True
    assert inst.jammer_mode == 2
    assert drfm == clear
