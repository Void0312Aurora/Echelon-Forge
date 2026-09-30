from __future__ import annotations

import numpy as np
import pytest

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from python.simulation.air.action import build_pilot_action  # noqa: E402


def test_full_air_action_projects_to_native_pilot_action() -> None:
    action = np.zeros((17,), dtype=np.float32)
    action[0] = 0.25
    action[1] = -0.2
    action[2] = 0.1
    action[3] = 0.8
    action[5] = 0.75
    action[6] = 0.25
    action[9] = 1.0
    action[13] = 1.0
    action[14] = 1.0
    action[16] = 1.0

    pilot = build_pilot_action(action, action_mode="full")
    assert pilot.active is True
    assert pilot.stick_pitch == pytest.approx(0.25)
    assert pilot.throttle == pytest.approx(0.8)
    assert pilot.flaps == pytest.approx(0.5)
    assert pilot.speedbrake == pytest.approx(0.0)
    assert pilot.radar_active is True
    assert pilot.master_arm is True
    assert pilot.fire_weapon is True
    assert pilot.weapon_select_id == 7


def test_takeoff_action_projects_gear_from_instrument_state() -> None:
    pilot = build_pilot_action(
        np.asarray([0.2, 0.75, -0.1, 0.8], dtype=np.float32),
        action_mode="takeoff4",
        instrument_state=type("Instrument", (), {"alt_radar": 10.0})(),
    )
    assert pilot.stick_pitch == pytest.approx(0.2)
    assert pilot.throttle == pytest.approx(0.8)
    assert pilot.gear_handle == 1.0
