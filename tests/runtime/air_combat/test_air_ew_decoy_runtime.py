"""Runtime evidence that released expendables can seduce a maintained seeker.

Head-on F-16C pair on the maintained database. Blue fires the AIM-9X (IR) or
the AIM-120C (active radar); Red dispenses flares or chaff from the gen-4 EW
suite for a short burst. The decoy discrimination values the weapons carry are
uncalibrated engineering proxies, so these tests assert only the premise (the
data reaches the missile and the decoys enter the seeker's evaluation) and
non-vacuity over a small seed sweep (some seeds capture, some do not). They
pin no capture fraction.
"""

from __future__ import annotations

import ef_py
import pytest

from python.runtime_bootstrap import resolve_repo_path


DATABASE = resolve_repo_path("examples", "config", "database")
_STEP_S = 0.05
_BURST_STEPS = 40
_MAX_FLIGHT_STEPS = 400
_SEEDS = range(12)

# F-16C_Block50 default loadout stations.
_AIM_120C_STATION = 1
_AIM_9X_STATION = 2


def _engagement(
    seed: int, *, station: int, separation_m: float, release_flare: bool, release_chaff: bool
) -> dict:
    kernel = ef_py.SimulationKernel()
    assert kernel.load_database(DATABASE)
    kernel.reset(seed)
    kernel.set_time_step(_STEP_S)
    blue = int(
        kernel.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 0.0, 200.0, 0.0)
    )
    red = int(
        kernel.spawn_unit(
            ef_py.Side.Red, "F-16C_Block50", 0.0, separation_m, 5000.0, 180.0, 0.0, 0.0, 0.0, -200.0, 0.0
        )
    )
    kernel.set_unit_ammo(blue, 4, 4)
    blue_action = ef_py.PilotAction()
    blue_action.active = True
    blue_action.throttle = 0.6
    blue_action.weapon_select_id = station
    red_action = ef_py.PilotAction()
    red_action.active = True
    red_action.throttle = 0.6

    for _ in range(80):
        kernel.set_pilot_action(blue, blue_action)
        kernel.set_pilot_action(red, red_action)
        kernel.step()
        if any(int(contact.id) == red for contact in kernel.get_agent_observation(blue).contacts):
            break
    missile = int(kernel.fire_missile(blue, red))
    assert missile > 0, "premise: blue launches on its radar track"
    launched = kernel.debug_get_missile_runtime_state(missile)

    captured = False
    evaluated = 0
    for step in range(_MAX_FLIGHT_STEPS):
        red_action.program_flare = release_flare and step < _BURST_STEPS
        red_action.program_chaff = release_chaff and step < _BURST_STEPS
        kernel.set_pilot_action(blue, blue_action)
        kernel.set_pilot_action(red, red_action)
        kernel.step()
        if not kernel.is_unit_active(missile):
            break
        state = kernel.debug_get_missile_runtime_state(missile)
        evaluated = int(state["evaluated_decoy_count"])
        if int(state["target_id"]) != red:
            captured = True
            break
    return {
        "sensor_type": int(launched["sensor_type"]),
        "rejection": float(launched["seeker_decoy_rejection"]),
        "cell_m": float(launched["seeker_resolution_cell_m"]),
        "evaluated": evaluated,
        "captured": captured,
        "red_health": list(kernel.get_unit_health(red)) if kernel.is_unit_active(red) else None,
    }


@pytest.mark.parametrize(
    ("station", "separation_m", "flare", "seeker"),
    [
        (_AIM_9X_STATION, 8000.0, True, ef_py.SensorType.Infrared),
        (_AIM_120C_STATION, 15000.0, False, ef_py.SensorType.Radar),
    ],
    ids=["aim9x_flare", "aim120c_chaff"],
)
def test_expendables_seduce_some_but_not_all_seeds(
    station: int, separation_m: float, flare: bool, seeker: ef_py.SensorType
) -> None:
    runs = [
        _engagement(seed, station=station, separation_m=separation_m, release_flare=flare, release_chaff=not flare)
        for seed in _SEEDS
    ]
    for run in runs:
        assert run["sensor_type"] == int(seeker), run
        # Premise: the weapon data reached the missile and decoys were drawn.
        assert 0.0 < run["rejection"] < 1.0, run
        assert run["cell_m"] > 0.0, run
        assert run["evaluated"] >= 1, run
    captured = sum(1 for run in runs if run["captured"])
    assert 0 < captured < len(runs), [run["captured"] for run in runs]


@pytest.mark.parametrize(
    ("station", "separation_m"),
    [(_AIM_9X_STATION, 8000.0), (_AIM_120C_STATION, 15000.0)],
    ids=["aim9x", "aim120c"],
)
def test_no_release_means_no_capture(station: int, separation_m: float) -> None:
    for seed in range(3):
        run = _engagement(seed, station=station, separation_m=separation_m, release_flare=False, release_chaff=False)
        assert run["evaluated"] == 0, run
        assert run["captured"] is False, run


def test_wrong_physics_expendable_never_captures() -> None:
    # Chaff against the IR AIM-9X: never eligible, never drawn.
    for seed in range(3):
        run = _engagement(seed, station=_AIM_9X_STATION, separation_m=8000.0, release_flare=False, release_chaff=True)
        assert run["evaluated"] == 0, run
        assert run["captured"] is False, run
