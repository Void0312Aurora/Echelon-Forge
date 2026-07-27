"""Cross-layer option-cell parity gate for the opt-in execution episode controller.

This suite closes the exact-runtime coverage precondition named by the
"T4 Census" section of docs/plan/exact_runtime/cpp_exact_runtime_refactor_plan.md:
before any Python stepping-layer retirement, every maintained
``flight_shaping_backend`` option and the post-launch evaluation feature must be
exercised through the opt-in ``execution_episode_controller_mainline`` path and
compared cell-by-cell against the default Python-orchestrated path
(``ScenarioLoader.compute_full_step``).

Cell semantics:

- A **covered** cell (gap reason ``None`` in
  ``EXECUTION_CONTROLLER_OPTION_GAP_MATRIX``) runs one small deterministic
  scenario through BOTH paths and asserts cross-layer parity of the observable
  products: observations, rewards, reward-term breakdowns, mission status,
  termination reasons, and episode transitions (including autoreset).
- A **gap** cell is skipped with the exact gap reason from the matrix, and each
  gap mechanism is pinned by its own evidence test below, so the matrix cannot
  silently rot: if a gap closes in production, the evidence test fails and the
  matrix entry must be flipped to covered.

Numeric tolerances are the ones the existing mainline parity contract already
pins (tests/world_batch/test_world_batch_vec_env_execution_and_observation.py):
observations within 1.0e-5 absolute, scalar rewards and per-term breakdown
values within 1.0e-6 absolute. The census promises behavioral equivalence for
the controller cutover, not bitwise exactness, so these documented tolerances
are the contract; boolean transitions, termination reasons, and reward-term key
sets are compared exactly.

Default-resolution contract (this iteration, FLIP HELD): with the coverage
gate above landed, ``execution_episode_controller_mainline`` now defaults to
*unset* and resolves through
``WorldBatchVecEnv._resolve_execution_episode_controller_mainline_default``.
The resolver evaluates the covered-cell ownership rule (compiled/auto flight
shaping, post-launch assessment not configured, action mode in the
parity-pinned whitelist full/takeoff2/takeoff4, no scripted opponents
declared in the scenario, no second entity side declared in the scenario, no
tier-2 batch-prepare opt-in, runtime episode-controller APIs present), but
the flip itself is DISARMED behind the module constant
``vec_env._CONTROLLER_DEFAULT_FLIP_ARMED = False`` per the owner-delegated
held ruling (2026-07-27): the plan's Acceptance Criteria require the cutover
to improve maintained rollout wall-clock beyond noise, and the measurement
below shows the opposite on this fixture. While the constant is False, EVERY
unset default resolves to the Python-orchestrated path; a cell the rule
would have flipped reports the named reason
'default_off_covered_cell_flip-held-pending-performance'. Explicit
``True``/``False`` keep their exact pre-flip semantics. The tests below pin,
per cell:

- held-flip default resolution: a default-constructed (unset) env on a
  covered cell resolves to the Python path with the flip-held reason and
  produces the same observable products the pre-flip Python-path default
  produced;
- the action-mode axis of the (held) covered-cell rule (the I80 matrix fixed
  ``action_mode="full"``; the whitelist extends to takeoff2/takeoff4 only
  with the same cross-layer parity evidence, driven explicitly on both
  paths);
- excluded cells resolve to the Python path with a named reason and never
  error on previously-working configurations (gpu_host stays HELD on the
  Python path; post-launch-configured runs bind the red line and keep the
  assessment firing on the Python path; air_combat_hybrid_v1 stays with them;
  naval_station3 keeps the Python-owned naval reward surface; scenarios
  declaring scripted opponents keep Python-orchestrated opponent stepping;
  scenarios declaring more than one entity side keep the Python-owned combat
  products; porting these into the controller is separate future work).

Hot-path measurement (this iteration, evidence only, no perf claim): on the
inline option-parity fixture (action_mode="full", compiled backend, 100 steps
per repeat, 5 repeats after a 20-step warmup, median of per-repeat wall time)
on the local Windows dev build (Python 3.12, shared build-local-win):

- n_envs=1: Python path median 0.2443 s/100 steps
  (repeats 0.3019/0.2383/0.2369/0.2443/0.2813); controller mainline median
  0.2973 s/100 steps (repeats 0.2973/0.2869/0.2789/0.3154/0.3007).
- n_envs=8: Python path median 1.8687 s/100 steps
  (repeats 2.2237/2.0728/1.8686/1.8343/1.8687); controller mainline median
  2.4087 s/100 steps (repeats 2.4871/2.6420/2.3044/2.4051/2.4087).

On this micro fixture the controller path measured SLOWER than the Python
path in both regimes. Recorded as-is: these machine-local medians are the
honest input for the plan-level performance acceptance criterion ("compiled
episode cutover must improve maintained execution rollout wall-clock beyond
noise"), which this fixture does not evidence -- and they are the reason the
default flip is HELD (``vec_env._CONTROLLER_DEFAULT_FLIP_ARMED = False``,
owner-delegated ruling 2026-07-27). The arming condition is a
representative-scenario wall-clock improvement beyond noise, owned by the
exact-runtime line per the program's performance boundary.
"""

from __future__ import annotations

import json
import tempfile

import numpy as np
import pytest

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

from gym_envs.universal_env_parts.common import gym as _gym # noqa: E402
from python.env_config import ACTION_MODES, FLIGHT_SHAPING_BACKENDS # noqa: E402
from python.rl.runtime.world_batch.vec_env import ( # noqa: E402
  _CONTROLLER_DEFAULT_FLIP_ARMED,
  WorldBatchVecEnv,
)
from tests.support._world_batch_vec_env_test_support import ( # noqa: E402
  _inline_air_combat_scripted_opponent_scenario,
  _inline_vec_env_scenario,
)


# Single-sourced from python/env_config.py so that adding or removing a
# maintained backend value breaks the completeness gate below until the gap
# matrix is updated with an explicit disposition for the new cell.
MAINTAINED_FLIGHT_SHAPING_BACKENDS: tuple[str, ...] = tuple(FLIGHT_SHAPING_BACKENDS)
POST_LAUNCH_EVALUATION_CELLS: tuple[bool, ...] = (False, True)

GAP_REASON_GPU_HOST_MAINLINE = (
  "execution_episode_controller_mainline requires the compiled flight-shaping "
  "backend mode: flight_shaping_backend='gpu_host' is rejected with a "
  "RuntimeError at WorldBatchVecEnv construction "
  "(python/rl/runtime/world_batch/vec_env.py handle loop guard)."
)
GAP_REASON_POST_LAUNCH_MAINLINE = (
  "post-launch evaluation is hard-disabled under the controller mainline: "
  "_air_combat_post_launch_assessment_should_run returns False whenever "
  "execution_episode_controller_mainline is set "
  "(python/rl/runtime/world_batch/_air_combat_post_launch_mixin.py), so the "
  "assessment can only run on the default Python path."
)

# Cell key: (flight_shaping_backend, post_launch_evaluation_enabled).
# Value: None when the cell is exercised through the controller mainline with
# cross-layer parity asserted, otherwise the exact gap mechanism.
EXECUTION_CONTROLLER_OPTION_GAP_MATRIX: dict[tuple[str, bool], str | None] = {
  ("auto", False): None,
  ("compiled", False): None,
  ("gpu_host", False): GAP_REASON_GPU_HOST_MAINLINE,
  ("auto", True): GAP_REASON_POST_LAUNCH_MAINLINE,
  ("compiled", True): GAP_REASON_POST_LAUNCH_MAINLINE,
  ("gpu_host", True): (
    GAP_REASON_GPU_HOST_MAINLINE + " Additionally: " + GAP_REASON_POST_LAUNCH_MAINLINE
  ),
}

_OBS_PARITY_KEYS = ("instruments", "contacts", "rwr", "mission")
_OBS_ATOL = 1.0e-5
_SCALAR_ATOL = 1.0e-6

# ---------------------------------------------------------------------------
# Default-flip action-mode axis (covered-cell rule; the flip itself is HELD,
# see vec_env._CONTROLLER_DEFAULT_FLIP_ARMED). The I80 matrix above fixes
# ``action_mode="full"``; the covered-cell rule extends controller ownership
# to additional action modes only with the same cross-layer parity evidence,
# pinned per mode below via explicit opt-in on both paths (whitelist
# polarity: a new maintained action mode defaults to the Python path until
# it earns its own parity pin).
# ``air_combat_hybrid_v1`` is excluded by the owner-delegated scope ruling
# (post-launch assessment and the event-action machinery ride that mode).
# ``naval_station3`` is excluded on direct evidence: the naval reward surface
# (e.g. ``naval_station_error_penalty``,
# tests/runtime/naval/test_naval_station_policy_surface.py) is
# Python/tier-1-owned and the controller path does not reproduce it.
# Single-sourced against python/env_config.py ACTION_MODES so a new maintained
# action mode breaks the completeness gate until it gets an explicit
# covered/excluded disposition here.
# ---------------------------------------------------------------------------
DEFAULT_FLIP_COVERED_ACTION_MODES: tuple[str, ...] = (
  "full",
  "takeoff2",
  "takeoff4",
)
DEFAULT_FLIP_EXCLUDED_ACTION_MODES: dict[str, str] = {
  "air_combat_hybrid_v1": (
    "excluded from the default flip: post-launch assessment and the air-combat "
    "event-action machinery ride this mode and the controller mainline "
    "hard-disables the assessment; the default resolution returns "
    "'default_off_action_mode_air_combat_hybrid_v1'"
  ),
  "naval_station3": (
    "excluded from the default flip: the naval reward surface (e.g. "
    "naval_station_error_penalty) is Python/tier-1-owned and the controller "
    "path does not reproduce it "
    "(tests/runtime/naval/test_naval_station_policy_surface.py); the default "
    "resolution returns 'default_off_action_mode_naval_station3'"
  ),
}
_PARITY_ACTION_DIMS: dict[str, int] = {
  "full": 17,
  "takeoff2": 2,
  "takeoff4": 4,
}

# (flight_shaping_backend, action_mode) cells the covered-cell ownership rule
# WOULD flip to controller ownership. While the flip is held
# (vec_env._CONTROLLER_DEFAULT_FLIP_ARMED is False), each cell is pinned to
# resolve to the Python path with the flip-held reason and to reproduce the
# pre-flip Python-path products exactly.
DEFAULT_FLIP_COVERED_CELLS: tuple[tuple[str, str], ...] = (
  ("auto", "full"),
  ("compiled", "full"),
  ("compiled", "takeoff2"),
  ("compiled", "takeoff4"),
)

# Constructor-kwargs surfaces that must keep the Python path under the default
# resolution, with the exact named reason the resolution reports. These are
# the regression pins that no previously-working configuration errors or
# changes path because of the flip.
DEFAULT_FLIP_PYTHON_PATH_CELLS: dict[str, tuple[dict[str, object], str]] = {
  "gpu_host_backend": (
    {"flight_shaping_backend": "gpu_host"},
    "default_off_flight_shaping_backend_gpu_host",
  ),
  "post_launch_assessment_configured": (
    {
      "air_combat_post_launch_assessment_enabled": True,
      "air_combat_post_launch_assessment_max_steps": 4,
    },
    "default_off_post_launch_assessment_configured",
  ),
  "air_combat_hybrid_action_mode": (
    {"action_mode": "air_combat_hybrid_v1"},
    "default_off_action_mode_air_combat_hybrid_v1",
  ),
  "naval_station_action_mode": (
    {"action_mode": "naval_station3"},
    "default_off_action_mode_naval_station3",
  ),
  "shadow_compare_diagnostic": (
    {"execution_episode_controller_shadow_compare": True},
    "default_off_shadow_compare",
  ),
  "tier2_batch_prepare_opt_in": (
    {"execution_step_batch_prepare": True},
    "default_off_execution_step_batch_prepare",
  ),
}

_STAGE1_C2_SCENARIO = resolve_repo_path(
  "scenarios",
  "air_combat",
  "1v1",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
)

requires_gym = pytest.mark.skipif(_gym is None, reason="WorldBatchVecEnv requires gymnasium")


def test_gap_matrix_covers_every_maintained_option_cell() -> None:
  expected_cells = {
    (backend, post_launch)
    for backend in MAINTAINED_FLIGHT_SHAPING_BACKENDS
    for post_launch in POST_LAUNCH_EVALUATION_CELLS
  }
  assert set(EXECUTION_CONTROLLER_OPTION_GAP_MATRIX) == expected_cells, (
    "EXECUTION_CONTROLLER_OPTION_GAP_MATRIX must enumerate every maintained "
    "flight_shaping_backend x post-launch-evaluation cell; update the matrix "
    "with an explicit covered/gap disposition for the changed option set."
  )
  for cell, reason in EXECUTION_CONTROLLER_OPTION_GAP_MATRIX.items():
    assert reason is None or (isinstance(reason, str) and reason.strip()), (
      f"gap cell {cell!r} must carry a non-empty mechanism description"
    )


def _write_parity_scenario(tmpdir: str) -> str:
  scenario_data = _inline_vec_env_scenario()
  # max_steps=2 so a 4-step run crosses one full episode boundary: step 1
  # mid-episode, step 2 terminal (truncation), steps 3-4 post-autoreset.
  scenario_data["meta"]["max_steps"] = 2
  scenario_path = f"{tmpdir}/inline_option_parity_scenario.json"
  with open(scenario_path, "w", encoding="utf-8") as f:
    json.dump(scenario_data, f, ensure_ascii=True)
  return scenario_path


def _make_parity_env(
  scenario_path: str,
  *,
  backend: str,
  mainline: bool | None,
  action_mode: str = "full",
  **extra_kwargs,
) -> WorldBatchVecEnv:
  kwargs = dict(
    scenario_path=scenario_path,
    n_envs=1,
    include_visual=False,
    include_proprio=False,
    action_mode=action_mode,
    execution_step_runtime_mode="compiled",
    flight_shaping_backend=backend,
  )
  if mainline is not None:
    # Explicit request: pre-flip semantics. ``None`` omits the kwarg so the
    # env exercises the new default resolution.
    kwargs["execution_episode_controller_mainline"] = mainline
  kwargs.update(extra_kwargs)
  return WorldBatchVecEnv(**kwargs)


def _assert_obs_parity(default_obs, mainline_obs, *, context: str) -> None:
  for key in _OBS_PARITY_KEYS:
    default_arr = np.asarray(default_obs[key])
    mainline_arr = np.asarray(mainline_obs[key])
    assert default_arr.shape == mainline_arr.shape, f"{context}: shape mismatch for key={key}"
    assert np.allclose(default_arr, mainline_arr, atol=_OBS_ATOL), (
      f"{context}: observation mismatch for key={key}; "
      f"max abs diff={float(np.max(np.abs(default_arr - mainline_arr)))}"
    )


def _assert_cross_layer_parity(
  reference_env: WorldBatchVecEnv,
  candidate_env: WorldBatchVecEnv,
  *,
  action_dim: int,
  cell_label: str,
) -> None:
  """Seed/reset both envs and assert 4-step cross-layer product parity.

  ``reference_env`` is the Python-orchestrated path; ``candidate_env`` is the
  controller-owned path (explicitly requested or default-resolved).
  """
  reference_env.seed(123)
  candidate_env.seed(123)
  reference_obs = reference_env.reset()
  candidate_obs = candidate_env.reset()
  _assert_obs_parity(reference_obs, candidate_obs, context=f"cell={cell_label}/reset")

  action = np.zeros((1, int(action_dim)), dtype=np.float32)
  for step_idx in range(4):
    context = f"cell={cell_label}/step={step_idx}"
    reference_obs, reference_rewards, reference_dones, reference_infos = reference_env.step(action)
    candidate_obs, candidate_rewards, candidate_dones, candidate_infos = candidate_env.step(action)

    # Episode transitions are exact: same done flags on every step,
    # including the terminal step and the post-autoreset steps.
    assert bool(reference_dones[0]) == bool(candidate_dones[0]), (
      f"{context}: episode transition mismatch "
      f"(reference={bool(reference_dones[0])}, candidate={bool(candidate_dones[0])})"
    )
    assert abs(float(reference_rewards[0]) - float(candidate_rewards[0])) <= _SCALAR_ATOL, (
      f"{context}: reward mismatch "
      f"(reference={float(reference_rewards[0])}, candidate={float(candidate_rewards[0])})"
    )
    assert reference_infos[0].get("termination_reason") == candidate_infos[0].get("termination_reason"), (
      f"{context}: termination_reason mismatch"
    )
    assert np.allclose(
      np.asarray(reference_infos[0]["mission_status"], dtype=np.float32),
      np.asarray(candidate_infos[0]["mission_status"], dtype=np.float32),
      atol=_OBS_ATOL,
    ), f"{context}: mission_status mismatch"

    reference_terms = dict(reference_infos[0].get("reward_terms", {}))
    candidate_terms = dict(candidate_infos[0].get("reward_terms", {}))
    assert set(reference_terms) == set(candidate_terms), (
      f"{context}: reward term key sets differ "
      f"(reference-only={sorted(set(reference_terms) - set(candidate_terms))}, "
      f"candidate-only={sorted(set(candidate_terms) - set(reference_terms))})"
    )
    for term_key, reference_value in reference_terms.items():
      assert abs(float(reference_value) - float(candidate_terms[term_key])) <= _SCALAR_ATOL, (
        f"{context}: reward term mismatch for {term_key} "
        f"(reference={float(reference_value)}, candidate={float(candidate_terms[term_key])})"
      )

    _assert_obs_parity(reference_obs, candidate_obs, context=context)


@requires_gym
@pytest.mark.parametrize(
  ("backend", "post_launch"),
  sorted(EXECUTION_CONTROLLER_OPTION_GAP_MATRIX),
  ids=lambda value: str(value).lower(),
)
def test_option_cell_cross_layer_parity(backend: str, post_launch: bool) -> None:
  gap_reason = EXECUTION_CONTROLLER_OPTION_GAP_MATRIX[(backend, post_launch)]
  if gap_reason is not None:
    pytest.skip(gap_reason)

  with tempfile.TemporaryDirectory() as tmpdir:
    scenario_path = _write_parity_scenario(tmpdir)
    default_env = _make_parity_env(scenario_path, backend=backend, mainline=False)
    mainline_env = _make_parity_env(scenario_path, backend=backend, mainline=True)
    try:
      # The covered cells ride the compiled flight-shaping mode; pin the
      # resolution so an 'auto' remap would be caught here, not silently.
      assert default_env.envs[0].loader._flight_shaping_backend_mode() == "compiled"
      assert mainline_env.envs[0].loader._flight_shaping_backend_mode() == "compiled"
      _assert_cross_layer_parity(
        default_env,
        mainline_env,
        action_dim=_PARITY_ACTION_DIMS["full"],
        cell_label=str(backend),
      )
    finally:
      default_env.close()
      mainline_env.close()


def test_default_flip_action_mode_dispositions_cover_every_maintained_action_mode() -> None:
  covered = set(DEFAULT_FLIP_COVERED_ACTION_MODES)
  excluded = set(DEFAULT_FLIP_EXCLUDED_ACTION_MODES)
  assert covered.isdisjoint(excluded), (
    "an action mode cannot be both covered by and excluded from the default flip"
  )
  assert covered | excluded == set(ACTION_MODES), (
    "every maintained action mode needs an explicit covered/excluded default-flip "
    "disposition; update DEFAULT_FLIP_COVERED_ACTION_MODES or "
    "DEFAULT_FLIP_EXCLUDED_ACTION_MODES for the changed action-mode set"
  )
  assert covered == set(_PARITY_ACTION_DIMS), (
    "_PARITY_ACTION_DIMS must enumerate exactly the covered action modes"
  )
  for mode, reason in DEFAULT_FLIP_EXCLUDED_ACTION_MODES.items():
    assert isinstance(reason, str) and reason.strip(), (
      f"excluded action mode {mode!r} must carry a non-empty exclusion reason"
    )


@requires_gym
@pytest.mark.parametrize(
  "action_mode",
  [mode for mode in DEFAULT_FLIP_COVERED_ACTION_MODES if mode != "full"],
)
def test_default_flip_action_mode_cell_cross_layer_parity(action_mode: str) -> None:
  """Cross-layer parity for the action modes the default flip newly covers.

  ``action_mode="full"`` is already exercised by the I80 covered cells above;
  this pin extends the same product-parity contract (explicitly-requested
  controller vs explicitly-pinned Python path) to the remaining covered modes.
  """
  with tempfile.TemporaryDirectory() as tmpdir:
    scenario_path = _write_parity_scenario(tmpdir)
    default_env = _make_parity_env(
      scenario_path, backend="compiled", mainline=False, action_mode=action_mode
    )
    mainline_env = _make_parity_env(
      scenario_path, backend="compiled", mainline=True, action_mode=action_mode
    )
    try:
      _assert_cross_layer_parity(
        default_env,
        mainline_env,
        action_dim=_PARITY_ACTION_DIMS[action_mode],
        cell_label=f"compiled/{action_mode}",
      )
    finally:
      default_env.close()
      mainline_env.close()


@requires_gym
@pytest.mark.parametrize(
  ("backend", "action_mode"),
  DEFAULT_FLIP_COVERED_CELLS,
  ids=lambda value: str(value).lower(),
)
def test_default_resolution_holds_python_path_on_covered_cells_while_flip_disarmed(
  backend: str, action_mode: str
) -> None:
  """Held-flip pins for the covered cells (owner-delegated ruling, 2026-07-27).

  The covered-cell resolution logic stays in place, but while
  ``vec_env._CONTROLLER_DEFAULT_FLIP_ARMED`` is False the unset default must
  resolve to the Python-orchestrated path with the flip-held reason, and a
  default-constructed (unset) env must reproduce the pre-flip Python-path
  products exactly (before/after default parity of the HELD default). When
  the exact-runtime line arms the flip (representative-scenario wall-clock
  improvement beyond noise), restore these pins to the controller-ownership
  form: default-resolved env asserts ``mainline is True`` with reason
  'default_on_covered_cells' and parity against an explicit
  ``mainline=False`` env.
  """
  assert _CONTROLLER_DEFAULT_FLIP_ARMED is False, (
    "the covered-cell default flip has been armed: restore the before/after "
    "controller-ownership parity pins for DEFAULT_FLIP_COVERED_CELLS and "
    "update the plan-doc addendum (docs/plan/exact_runtime/"
    "cpp_exact_runtime_refactor_plan.md and .zh.md) with the "
    "representative-scenario wall-clock evidence that armed it"
  )
  with tempfile.TemporaryDirectory() as tmpdir:
    scenario_path = _write_parity_scenario(tmpdir)
    before_env = _make_parity_env(
      scenario_path, backend=backend, mainline=False, action_mode=action_mode
    )
    after_env = _make_parity_env(
      scenario_path, backend=backend, mainline=None, action_mode=action_mode
    )
    try:
      assert before_env.execution_episode_controller_mainline is False
      assert before_env.execution_episode_controller_mainline_resolution == "explicit"
      assert after_env.execution_episode_controller_mainline is False, (
        f"cell=({backend}, {action_mode}) must stay on the Python path while "
        "the default flip is held"
      )
      assert (
        after_env.execution_episode_controller_mainline_resolution
        == "default_off_covered_cell_flip-held-pending-performance"
      )
      assert after_env.execution_episode_controller_mainline_requested is None
      _assert_cross_layer_parity(
        before_env,
        after_env,
        action_dim=_PARITY_ACTION_DIMS[action_mode],
        cell_label=f"default-held/{backend}/{action_mode}",
      )
    finally:
      before_env.close()
      after_env.close()


@requires_gym
@pytest.mark.parametrize(
  "cell_name",
  sorted(DEFAULT_FLIP_PYTHON_PATH_CELLS),
)
def test_default_resolution_keeps_python_path_for_excluded_cells(cell_name: str) -> None:
  """Excluded cells must degrade to the Python path with a named reason.

  This is the never-an-error regression pin: previously-working
  configurations (gpu_host, post-launch-configured, air-combat hybrid,
  shadow-compare, tier-2 batch prepare) construct successfully with the kwarg
  unset and keep ``execution_episode_controller_mainline == False``.
  """
  extra_kwargs, expected_reason = DEFAULT_FLIP_PYTHON_PATH_CELLS[cell_name]
  with tempfile.TemporaryDirectory() as tmpdir:
    scenario_path = _write_parity_scenario(tmpdir)
    backend = str(extra_kwargs.get("flight_shaping_backend", "auto"))
    kwargs = {key: value for key, value in extra_kwargs.items() if key != "flight_shaping_backend"}
    env = _make_parity_env(scenario_path, backend=backend, mainline=None, **kwargs)
    try:
      assert env.execution_episode_controller_mainline is False, (
        f"excluded cell {cell_name!r} must keep the Python-orchestrated path"
      )
      assert env.execution_episode_controller_mainline_resolution == expected_reason
      assert env.execution_episode_controller_mainline_requested is None
    finally:
      env.close()


@requires_gym
def test_default_resolution_keeps_python_path_for_scripted_opponent_scenarios() -> None:
  """Scenario-content exclusion pin: scripted opponents stay Python-driven.

  Scripted opponents are Python-orchestrated behavior stepped by
  ``update_behaviors``; the controller mainline replaces that call with
  ``update_command_chain_only``, so a scenario that declares a scripted
  opponent must keep the Python-orchestrated default path (the default-path
  opponent-driving contract itself is pinned by
  tests/world_batch/test_world_batch_vec_env_adapter_surface.py::
  test_world_batch_vec_env_drives_scripted_red_opponent_on_default_path).
  """
  with tempfile.TemporaryDirectory() as tmpdir:
    scenario_path = f"{tmpdir}/inline_scripted_opponent_scenario.json"
    with open(scenario_path, "w", encoding="utf-8") as f:
      json.dump(_inline_air_combat_scripted_opponent_scenario(), f, ensure_ascii=True)
    env = _make_parity_env(scenario_path, backend="compiled", mainline=None)
    try:
      assert env.execution_episode_controller_mainline is False
      assert (
        env.execution_episode_controller_mainline_resolution
        == "default_off_scripted_opponents_declared"
      )
    finally:
      env.close()


@requires_gym
def test_default_resolution_keeps_python_path_for_multi_side_scenarios() -> None:
  """Scenario-content exclusion pin: hostile-content scenarios stay Python-owned.

  Combat products (e.g. air-combat ``combat_win``/``combat_timeout``
  termination, pinned by tests/runtime/air_combat/test_air_combat_1v1_fixture.py)
  are computed by the Python/tier-1 orchestration and the controller mainline
  does not reproduce them, so any scenario declaring entities on more than
  one side must keep the Python-orchestrated default path even in a covered
  action mode.
  """
  scenario_data = _inline_vec_env_scenario()
  scenario_data["meta"]["max_steps"] = 2
  scenario_data["entities"].append(
    {
      "name": "Red_Target",
      "type": "Aircraft",
      "side": "Red",
      "is_agent": False,
      "pos": [30000.0, 0.0, 1200.0],
      "vel": [0.0, -180.0, 0.0],
      "heading": 270.0,
    }
  )
  with tempfile.TemporaryDirectory() as tmpdir:
    scenario_path = f"{tmpdir}/inline_multi_side_scenario.json"
    with open(scenario_path, "w", encoding="utf-8") as f:
      json.dump(scenario_data, f, ensure_ascii=True)
    env = _make_parity_env(scenario_path, backend="compiled", mainline=None)
    try:
      assert env.execution_episode_controller_mainline is False
      assert (
        env.execution_episode_controller_mainline_resolution
        == "default_off_multi_side_scenario"
      )
    finally:
      env.close()


@requires_gym
def test_gap_mechanism_gpu_host_backend_rejected_by_controller_mainline() -> None:
  """Evidence for the ('gpu_host', *) gap cells.

  If this stops raising, the controller mainline has grown gpu_host support and
  the gap matrix rows for 'gpu_host' must be revisited.
  """
  with tempfile.TemporaryDirectory() as tmpdir:
    scenario_path = _write_parity_scenario(tmpdir)
    with pytest.raises(RuntimeError, match="requires the compiled flight-shaping backend"):
      _make_parity_env(scenario_path, backend="gpu_host", mainline=True)


@requires_gym
def test_gap_mechanism_post_launch_evaluation_disabled_under_controller_mainline() -> None:
  """Evidence for the (*, post_launch=True) gap cells.

  Builds one default-path air-combat env with the post-launch assessment
  enabled and all runtime preconditions primed, confirms the assessment gate
  opens on the default path, then confirms the ``should_run`` guard closes it
  purely because of the ``execution_episode_controller_mainline`` flag. The
  flag flip is a test-only probe of the Python-level guard clause; the env is
  never stepped while the flag is set.

  This iteration additionally pins the default flip's red line here: this env
  leaves ``execution_episode_controller_mainline`` unset, so the assertions
  below double as evidence that a post-launch-configured air-combat run still
  default-resolves onto the Python path with the assessment gate open.
  """
  env = WorldBatchVecEnv(
    scenario_path=_STAGE1_C2_SCENARIO,
    n_envs=1,
    include_visual=False,
    include_proprio=True,
    action_mode="air_combat_hybrid_v1",
    mission_obs_mode="air_combat_c2_roe_v2",
    step_info_mode="full",
    execution_step_runtime_mode="compiled",
    flight_shaping_backend="compiled",
    worker_threads=0,
    air_combat_post_launch_assessment_enabled=True,
    air_combat_post_launch_assessment_max_steps=4,
  )
  try:
    # Red-line regression pin: the kwarg is unset above, so the default
    # resolution must keep this post-launch-configured run on the Python path.
    assert env.execution_episode_controller_mainline is False
    assert (
      env.execution_episode_controller_mainline_resolution
      == "default_off_post_launch_assessment_configured"
    )
    env.reset()
    # Prime the only step-dependent precondition: a recorded weapon release.
    env.envs[0].loader._last_air_combat_event_action_info = {"release_executed": True}
    assert env._air_combat_post_launch_assessment_should_run(
      0, terminated=False, truncated=False
    ), "default-path preconditions did not open the post-launch assessment gate"
    env.execution_episode_controller_mainline = True
    try:
      assert not env._air_combat_post_launch_assessment_should_run(
        0, terminated=False, truncated=False
      ), (
        "post-launch assessment ran under execution_episode_controller_mainline; "
        "the (*, post_launch=True) gap cells in "
        "EXECUTION_CONTROLLER_OPTION_GAP_MATRIX must be revisited"
      )
    finally:
      env.execution_episode_controller_mainline = False
  finally:
    env.close()
