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

This iteration is coverage-only: no default flips, no production edits, no
Python layer deletion. Every gap cell recorded here is an open input for the
ownership-move gate that decides tier-1 retirement.
"""

from __future__ import annotations

import json
import tempfile

import numpy as np
import pytest

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

from gym_envs.universal_env_parts.common import gym as _gym # noqa: E402
from python.env_config import FLIGHT_SHAPING_BACKENDS # noqa: E402
from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv # noqa: E402
from tests.support._world_batch_vec_env_test_support import ( # noqa: E402
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


def _make_parity_env(scenario_path: str, *, backend: str, mainline: bool) -> WorldBatchVecEnv:
  return WorldBatchVecEnv(
    scenario_path=scenario_path,
    n_envs=1,
    include_visual=False,
    include_proprio=False,
    execution_step_runtime_mode="compiled",
    flight_shaping_backend=backend,
    execution_episode_controller_mainline=mainline,
  )


def _assert_obs_parity(default_obs, mainline_obs, *, context: str) -> None:
  for key in _OBS_PARITY_KEYS:
    default_arr = np.asarray(default_obs[key])
    mainline_arr = np.asarray(mainline_obs[key])
    assert default_arr.shape == mainline_arr.shape, f"{context}: shape mismatch for key={key}"
    assert np.allclose(default_arr, mainline_arr, atol=_OBS_ATOL), (
      f"{context}: observation mismatch for key={key}; "
      f"max abs diff={float(np.max(np.abs(default_arr - mainline_arr)))}"
    )


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

      default_env.seed(123)
      mainline_env.seed(123)
      default_obs = default_env.reset()
      mainline_obs = mainline_env.reset()
      _assert_obs_parity(default_obs, mainline_obs, context=f"cell={backend}/reset")

      action = np.zeros((1, 17), dtype=np.float32)
      for step_idx in range(4):
        context = f"cell={backend}/step={step_idx}"
        default_obs, default_rewards, default_dones, default_infos = default_env.step(action)
        mainline_obs, mainline_rewards, mainline_dones, mainline_infos = mainline_env.step(action)

        # Episode transitions are exact: same done flags on every step,
        # including the terminal step and the post-autoreset steps.
        assert bool(default_dones[0]) == bool(mainline_dones[0]), (
          f"{context}: episode transition mismatch "
          f"(default={bool(default_dones[0])}, mainline={bool(mainline_dones[0])})"
        )
        assert abs(float(default_rewards[0]) - float(mainline_rewards[0])) <= _SCALAR_ATOL, (
          f"{context}: reward mismatch "
          f"(default={float(default_rewards[0])}, mainline={float(mainline_rewards[0])})"
        )
        assert default_infos[0].get("termination_reason") == mainline_infos[0].get("termination_reason"), (
          f"{context}: termination_reason mismatch"
        )
        assert np.allclose(
          np.asarray(default_infos[0]["mission_status"], dtype=np.float32),
          np.asarray(mainline_infos[0]["mission_status"], dtype=np.float32),
          atol=_OBS_ATOL,
        ), f"{context}: mission_status mismatch"

        default_terms = dict(default_infos[0].get("reward_terms", {}))
        mainline_terms = dict(mainline_infos[0].get("reward_terms", {}))
        assert set(default_terms) == set(mainline_terms), (
          f"{context}: reward term key sets differ "
          f"(default-only={sorted(set(default_terms) - set(mainline_terms))}, "
          f"mainline-only={sorted(set(mainline_terms) - set(default_terms))})"
        )
        for term_key, default_value in default_terms.items():
          assert abs(float(default_value) - float(mainline_terms[term_key])) <= _SCALAR_ATOL, (
            f"{context}: reward term mismatch for {term_key} "
            f"(default={float(default_value)}, mainline={float(mainline_terms[term_key])})"
          )

        _assert_obs_parity(default_obs, mainline_obs, context=context)
    finally:
      default_env.close()
      mainline_env.close()


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
