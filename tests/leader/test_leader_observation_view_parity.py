"""Numeric parity pin for the leader observation build (T8 I56 repair round).

``build_observation`` (C13/TL15 in the G4 truth-leak inventory) was migrated onto
the declared observation view — its own-ship ``truth.x/y`` reads now flow through
``gym_envs.observation_view.own_ship_field`` — in the I56 independent-review
repair round. No pre-existing numeric test exercised this function (the review
disproved the earlier "stable_baselines3-gated parity" claim), so this test is
the parity harness: the expected literals below were produced by running the
fae17eb8 *baseline* (pre-migration) ``build_observation`` — extracted via
``git show fae17eb8:gym_envs/leader_env_parts/decision_runtime/observations.py``
— on these exact synthetic inputs (inventory §7.5). The migrated function must
reproduce them element-exactly, so any drift in the own-ship read path (field
name, default, order, coercion) or in the assembly math goes red here.

The loader fakes are deliberately sensitive to the own-ship ``x``/``y`` values
(ILS / runway-frame / beacon results depend on them), and the ``defaults``
scenario uses a truth object *without* ``x``/``y`` so the ``getattr(..., 0.0)``
default semantics of ``own_ship_field`` are pinned too. The second test proves
the pin is load-bearing and that the reads really flow through the declared view:
corrupting ``observation_view.own_ship_field`` via monkeypatch (the I50-style
patch seam) changes the output.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from gym_envs import observation_view  # noqa: E402
from gym_envs.leader_env_parts.decision_runtime import observations  # noqa: E402


class _FakeEnv:
  def __init__(self, loader, inst, truth, *, steps: int, dt: float):
    self.unwrapped = SimpleNamespace(
      loader=loader,
      steps=steps,
      sim=SimpleNamespace(get_time_step=lambda: dt),
    )
    self._inst = inst
    self._truth = truth

  def _current_execution_runtime_state(self):
    return self._inst, self._truth


def _raise_no_beacon(*_args, **_kwargs):
  raise RuntimeError("no beacon")


def _scenario_full() -> _FakeEnv:
  loader = SimpleNamespace(
    scenario_data={},
    mission_cmd={"target_altitude": 3000.0, "target_speed": 210.0, "command_code": 4},
    pilot_report=SimpleNamespace(report_type=3, status_value=2.5, timestamp_s=1.5),
    task_order=SimpleNamespace(
      task_type=2,
      station_type=3,
      coordination_mode=1,
      anchor_x_m=15000.0,
      anchor_y_m=-9000.0,
      on_station_time_s=120.0,
      fuel_bingo_override_kg=600.0,
    ),
    mission_phase_name="approach_armed",
    leader_intent=SimpleNamespace(phase_id=9),
    c2_task_id=4,
    c2_on_station_elapsed_s=45.0,
    get_mission_observation=lambda mode, truth=None, inst=None: [0.125 * i for i in range(16)],
    # x/y-sensitive fakes: a wrong own-ship read (field, default, order) changes
    # the ILS / runway-frame / beacon results and reds the pins below.
    get_ils_observation=lambda x, y, alt: [
      1.0,
      0.25 + 1e-6 * x,
      -0.5 + 1e-6 * y,
      3500.0 + 0.001 * x + 0.002 * y + 0.0001 * alt,
    ],
    get_runway_local_frame=lambda x, y: (True, 100.0 + 0.01 * x, -25.0 + 0.01 * y, 2500.0, 45.0),
    _nearest_ils_beacon=lambda x, y: {"heading": 87.0 + 1e-4 * (x + y)},
  )
  inst = SimpleNamespace(
    ias=145.5,
    ground_speed=142.25,
    alt_radar=850.0,
    alt_baro=1220.5,
    vvi=-3.5,
    heading=92.5,
    ground_track=90.25,
    roll=1.5,
    pitch=2.25,
    beta=0.125,
    r=0.0625,
    gear_pos=1.0,
    missiles_remaining=4.0,
    rwr_active=True,
    fuel_internal=1800.0,
    fuel_external=400.0,
  )
  truth = SimpleNamespace(x=1234.5, y=-567.25)
  return _FakeEnv(loader, inst, truth, steps=10, dt=0.5)


def _scenario_defaults() -> _FakeEnv:
  loader = SimpleNamespace(
    scenario_data={},
    mission_cmd={"command_code": 0},
    pilot_report=None,
    task_order=None,
    mission_phase_name="",
    get_mission_observation=lambda mode, truth=None, inst=None: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    get_ils_observation=lambda x, y, alt: [0.5, 0.25],
    get_runway_local_frame=lambda x, y: (False, 12.0, 34.0, 0.0, 0.0),
    _nearest_ils_beacon=_raise_no_beacon,
  )
  inst = SimpleNamespace(fuel_internal=100.0)
  # No x/y on truth: the own_ship_field(truth, ..., 0.0) defaults must fire with
  # exactly the baseline getattr(truth, ..., 0.0) semantics.
  truth = SimpleNamespace()
  return _FakeEnv(loader, inst, truth, steps=0, dt=0.05)


# Expected outputs produced by the fae17eb8 baseline build_observation on the
# exact fakes above (see module docstring; one-off dual-run evidence in the
# inventory §7.5). Do NOT regenerate from the live function when this reds —
# a red here means the migrated read path drifted from the baseline behavior.
_EXPECTED: dict[str, dict[str, list[float]]] = {
  "full": {
    "ownship": [145.5, 142.25, 850.0, 1220.5, -3.5, 92.5, 90.25, 1.5, 2.25, 0.125, 0.0625, 1.0],
    "task": [4.0, 2.0, 3.0, 9.0, 3000.0, 210.0, 16143.1181640625, 28.991649627685547, 75.0, 2.0],
    "navigation": [0.5, 0.625, 0.75, 0.875, 1.0, 1.125, 1.25, 1.375, 1.5, 1.625],
    "terminal": [
      3500.22216796875,
      0.2512345016002655,
      -0.5005672574043274,
      112.34500122070312,
      -30.672500610351562,
      5.43327522277832,
      1.0,
      1.0,
    ],
    "link": [3.0, 2.5, 3.5, 2.0, 4.0, 1.0],
  },
  "defaults": {
    "ownship": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "task": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
    "navigation": [5.0, 6.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "terminal": [0.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "link": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
  },
}

_SCENARIOS = {"full": _scenario_full, "defaults": _scenario_defaults}


@pytest.mark.parametrize("scenario", sorted(_SCENARIOS))
def test_build_observation_matches_fae17eb8_baseline_pinned_outputs(scenario: str) -> None:
  out = observations.build_observation(_SCENARIOS[scenario]())
  expected = _EXPECTED[scenario]
  assert set(out) == set(expected)
  for key in sorted(expected):
    assert out[key].dtype == np.float32, f"{scenario}/{key}: dtype drifted"
    pinned = np.asarray(expected[key], dtype=np.float32)
    assert np.array_equal(out[key], pinned), (
      f"{scenario}/{key}: migrated build_observation drifted from the fae17eb8 "
      f"baseline pin.\n  expected: {pinned.tolist()}\n  actual  : {out[key].tolist()}"
    )


def test_parity_pin_is_load_bearing_via_view_seam(monkeypatch: pytest.MonkeyPatch) -> None:
  # Prove (a) the own-ship reads really flow through the declared observation
  # view (the monkeypatch seam is observation_view.own_ship_field, resolved
  # dynamically at call time per the I50 no-import-time-binding rule) and (b) the
  # pinned comparison above is load-bearing: corrupting the view face changes the
  # output, so a read-path drift cannot pass the pins silently.
  baseline = observations.build_observation(_scenario_full())
  original = observation_view.own_ship_field
  monkeypatch.setattr(
    observation_view, "own_ship_field", lambda truth, field, default: original(truth, field, default) + 1.0
  )
  corrupted = observations.build_observation(_scenario_full())
  assert not np.array_equal(corrupted["terminal"], baseline["terminal"]), (
    "corrupting observation_view.own_ship_field did not change the terminal block; "
    "the own-ship reads no longer flow through the declared view"
  )
  assert not np.array_equal(corrupted["task"], baseline["task"]), (
    "corrupting observation_view.own_ship_field did not change the task block; "
    "the own-ship reads no longer flow through the declared view"
  )
