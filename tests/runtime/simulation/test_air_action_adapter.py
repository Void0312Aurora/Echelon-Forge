from __future__ import annotations

import numpy as np
import pytest

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from gym_envs.universal_env_parts import (  # noqa: E402
    AIR_EW_HYBRID_V1_ACTION_MODE,
    AIR_COMBAT_HYBRID_V1_ACTION_MODE,
    build_pilot_action as build_maintained_pilot_action,
)
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


def test_ew_hybrid_action_projects_countermeasure_bits() -> None:
    action = np.zeros((14,), dtype=np.float32)
    action[12] = 1.0
    action[13] = 1.0

    pilot = build_pilot_action(action, action_mode="air_ew_hybrid_v1")

    assert pilot.program_chaff is True
    assert pilot.program_flare is True


@pytest.mark.parametrize(
    "action_mode, index",
    [(AIR_COMBAT_HYBRID_V1_ACTION_MODE, 11), ("air_ew_hybrid_v1", 11)],
)
def test_hybrid_weapon_station_uses_floor_quantization(action_mode: str, index: int) -> None:
    action = np.zeros((12 if action_mode == AIR_COMBAT_HYBRID_V1_ACTION_MODE else 14,), dtype=np.float32)
    action[index] = 1.5

    direct = (
        build_pilot_action(action, action_mode=action_mode)
        if action_mode != AIR_COMBAT_HYBRID_V1_ACTION_MODE
        else None
    )
    maintained = build_maintained_pilot_action(action, action_mode=action_mode)

    assert maintained.weapon_select_id == 1
    if direct is not None:
        assert direct.weapon_select_id == maintained.weapon_select_id


def test_ew_hybrid_action_matches_maintained_transport_for_all_slots() -> None:
    fields = (
        "stick_pitch",
        "stick_roll",
        "rudder",
        "throttle",
        "gear_handle",
        "flaps",
        "speedbrake",
        "brake_left",
        "brake_right",
        "brake",
        "radar_active",
        "radar_scan_az",
        "radar_scan_el",
        "tms_up",
        "master_arm",
        "fire_weapon",
        "fire_gun",
        "weapon_select_id",
        "program_chaff",
        "program_flare",
        "jettison_emergency",
    )
    # Each one-hot vector exercises one slot while keeping the other slots at
    # the canonical neutral value used by both transport owners.
    for index in range(14):
        action = np.zeros((14,), dtype=np.float32)
        action[index] = 1.0
        direct = build_pilot_action(action, action_mode="air_ew_hybrid_v1")
        maintained = build_maintained_pilot_action(action, action_mode=AIR_EW_HYBRID_V1_ACTION_MODE)
        for field in fields:
            assert getattr(direct, field) == getattr(maintained, field), (index, field)
