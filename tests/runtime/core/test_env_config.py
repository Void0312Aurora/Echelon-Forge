from __future__ import annotations

import argparse
import unittest
from pathlib import Path

import pytest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

from python.env_config import ( # noqa: E402
  ACTION_MODES,
  BATCH_OBSERVATION_BACKENDS,
  BATCH_VISUAL_BACKENDS,
  EXECUTION_STEP_RUNTIME_MODES,
  FLIGHT_SHAPING_BACKENDS,
  STEP_INFO_MODES,
  VALID_ACTION_MODES,
  VALID_BATCH_OBSERVATION_BACKENDS,
  VALID_BATCH_VISUAL_BACKENDS,
  VALID_EXECUTION_STEP_RUNTIME_MODES,
  VALID_FLIGHT_SHAPING_BACKENDS,
  VALID_STEP_INFO_MODES,
  infer_include_visual_from_train_config,
  resolve_env_settings,
)
from python.mission_obs_taxonomy import ( # noqa: E402
  MISSION_OBS_MODE_CODE_BY_NAME,
  MISSION_OBS_MODE_NAMES,
  VALID_MISSION_OBS_MODES,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def _make_args(**overrides):
  base = {
    "include_visual": None,
    "include_proprio": None,
    "mission_obs_mode": None,
    "visual_downsample": None,
    "visual_update_interval": None,
    "temporal_history_len": None,
    "action_mode": None,
    "execution_step_runtime_mode": None,
    "step_info_mode": None,
    "flight_shaping_backend": None,
    "shaping_backend": None,
  }
  base.update(overrides)
  return argparse.Namespace(**base)


# Single env input normalizes to a single resolved field; one assertion shape.
@pytest.mark.parametrize(
  ("env", "field", "expected"),
  [
    pytest.param(
      {"include_proprio": True, "mission_obs_mode": "naval_screen_station_v1",
       "action_mode": "naval_station3", "shaping_backend": " GPU_HOST "},
      "flight_shaping_backend",
      "gpu_host",
      id="domain_neutral_shaping_backend_alias",
    ),
    pytest.param(
      {"mission_obs_mode": "AIR_COMBAT_C2_ROE_V1"},
      "mission_obs_mode",
      "air_combat_c2_roe_v1",
      id="air_combat_c2_roe_mission_obs_mode",
    ),
    pytest.param(
      {"action_mode": "naval_station3"},
      "action_mode",
      "naval_station3",
      id="dedicated_naval_action_mode",
    ),
    pytest.param(
      {"action_mode": "air_combat_hybrid_v1"},
      "action_mode",
      "air_combat_hybrid_v1",
      id="air_combat_hybrid_action_mode",
    ),
  ],
)
def test_resolve_env_settings_normalizes_single_field(env, field, expected) -> None:
  resolved = resolve_env_settings({"env": env}, _make_args())
  assert resolved[field] == expected


# A removed/unknown value must raise ValueError with a specific message.
@pytest.mark.parametrize(
  ("env", "args_overrides", "message"),
  [
    pytest.param(
      {"execution_step_runtime_mode": "legacy"}, {},
      "execution_step_runtime_mode='legacy' has been removed",
      id="legacy_runtime_mode",
    ),
    pytest.param(
      {"flight_shaping_backend": "legacy"}, {},
      "flight_shaping_backend='legacy' has been removed",
      id="legacy_flight_shaping_backend",
    ),
    pytest.param(
      {"execution_step_runtime_mode": "bad-mode"}, {},
      "Unknown execution_step_runtime_mode",
      id="invalid_runtime_mode",
    ),
    pytest.param(
      {"flight_shaping_backend": "bad-backend"}, {},
      "Unknown flight_shaping_backend",
      id="invalid_flight_shaping_backend",
    ),
    pytest.param(
      {"shaping_backend": "bad-backend"}, {},
      "Unknown flight_shaping_backend",
      id="invalid_shaping_backend_alias",
    ),
  ],
)
def test_resolve_env_settings_rejects_value(env, args_overrides, message) -> None:
  with pytest.raises(ValueError, match=message):
    resolve_env_settings({"env": env}, _make_args(**args_overrides))


class EnvConfigTests(unittest.TestCase):
  def test_infer_include_visual_from_train_config_detects_transformer_extractor(self) -> None:
    self.assertTrue(
      infer_include_visual_from_train_config(
        {
          "hyperparameters": {
            "policy_kwargs": {
              "features_extractor_class": "TransformerVisualExtractor",
            }
          }
        }
      )
    )
    self.assertFalse(infer_include_visual_from_train_config({"hyperparameters": {}}))
    self.assertFalse(infer_include_visual_from_train_config(None))

  def test_resolve_env_settings_normalizes_optional_runtime_modes(self) -> None:
    train_config = {
      "env": {
        "include_proprio": True,
        "mission_obs_mode": "NAV_V2",
        "visual_downsample": 2,
        "visual_update_interval": 3,
        "temporal_history_len": 16,
        "action_mode": "full",
        "execution_step_runtime_mode": " Compiled ",
        "step_info_mode": "TERMINAL",
        "flight_shaping_backend": " GPU_HOST ",
      }
    }

    resolved = resolve_env_settings(train_config, _make_args())
    self.assertEqual(resolved["mission_obs_mode"], "nav_v2")
    self.assertEqual(resolved["execution_step_runtime_mode"], "compiled")
    self.assertEqual(resolved["step_info_mode"], "terminal")
    self.assertEqual(resolved["flight_shaping_backend"], "gpu_host")
    self.assertEqual(resolved["temporal_history_len"], 16)
    self.assertNotIn("runtime_compatibility_enabled", resolved)

  def test_resolve_env_settings_prefers_canonical_backend_over_alias(self) -> None:
    train_config = {
      "env": {
        "flight_shaping_backend": "compiled",
        "shaping_backend": "gpu_host",
      }
    }

    resolved = resolve_env_settings(train_config, _make_args())
    self.assertEqual(resolved["flight_shaping_backend"], "compiled")

    resolved = resolve_env_settings(
      {"env": {"shaping_backend": "compiled"}},
      _make_args(flight_shaping_backend="gpu_host"),
    )
    self.assertEqual(resolved["flight_shaping_backend"], "gpu_host")

  def test_resolve_env_settings_normalizes_temporal_history_len(self) -> None:
    resolved = resolve_env_settings(
      {"env": {"temporal_history_len": 0}},
      _make_args(),
    )
    self.assertEqual(resolved["temporal_history_len"], 1)

    resolved = resolve_env_settings(
      {"env": {"temporal_history_len": 4}},
      _make_args(temporal_history_len=8),
    )
    self.assertEqual(resolved["temporal_history_len"], 8)

  def test_resolve_env_settings_allows_empty_optional_override_to_clear_env_value(self) -> None:
    train_config = {
      "env": {
        "execution_step_runtime_mode": "compiled",
        "flight_shaping_backend": "compiled",
      }
    }

    resolved = resolve_env_settings(
      train_config,
      _make_args(
        execution_step_runtime_mode="  ",
        flight_shaping_backend="",
      ),
    )

    self.assertIsNone(resolved["execution_step_runtime_mode"])
    self.assertIsNone(resolved["flight_shaping_backend"])
    self.assertNotIn("runtime_compatibility_enabled", resolved)

  def test_resolve_env_settings_does_not_return_runtime_compatibility_flag(self) -> None:
    resolved = resolve_env_settings({}, _make_args())
    self.assertIsNone(resolved["execution_step_runtime_mode"])
    self.assertNotIn("runtime_compatibility_enabled", resolved)

  def test_runtime_compatibility_enabled_key_is_retired_from_env_settings(self) -> None:
    with self.assertRaisesRegex(ValueError, "runtime_compatibility_enabled has been removed"):
      resolve_env_settings(
        {"env": {"runtime_compatibility_enabled": "legacy-ish"}},
        _make_args(),
      )

    with self.assertRaisesRegex(ValueError, "runtime_compatibility_enabled has been removed"):
      resolve_env_settings(
        {"env": {"runtime_compatibility_enabled": "yes"}},
        _make_args(),
      )

    with self.assertRaisesRegex(ValueError, "runtime_compatibility_enabled has been removed"):
      resolve_env_settings(
        {},
        _make_args(runtime_compatibility_enabled="yes"),
      )


class ModeChoiceSurfaceParityTests(unittest.TestCase):
  """Mode/choice surfaces must derive from their single semantic owners.

  Owners: ``python.mission_obs_taxonomy`` for mission observation modes and
  ``python.env_config`` for action/runtime/step-info/shaping mode tuples.
  """

  def test_validation_sets_derive_from_canonical_ordered_tuples(self) -> None:
    for modes, valid in (
      (ACTION_MODES, VALID_ACTION_MODES),
      (BATCH_OBSERVATION_BACKENDS, VALID_BATCH_OBSERVATION_BACKENDS),
      (BATCH_VISUAL_BACKENDS, VALID_BATCH_VISUAL_BACKENDS),
      (EXECUTION_STEP_RUNTIME_MODES, VALID_EXECUTION_STEP_RUNTIME_MODES),
      (STEP_INFO_MODES, VALID_STEP_INFO_MODES),
      (FLIGHT_SHAPING_BACKENDS, VALID_FLIGHT_SHAPING_BACKENDS),
    ):
      self.assertEqual(frozenset(modes), valid)
      self.assertEqual(len(modes), len(valid), f"duplicate entries in {modes!r}")

  def test_action_modes_pin_canonical_content_and_order(self) -> None:
    # Content pin: adding/removing/renaming an action mode must be a reviewed
    # owner change, and every derived surface follows this tuple.
    expected = ("full", "takeoff2", "takeoff4", "naval_station3", "air_combat_hybrid_v1")
    self.assertEqual(len(ACTION_MODES), 5)
    for idx, name in enumerate(expected):
      self.assertEqual(ACTION_MODES[idx], name)

  def test_mission_obs_mode_names_follow_mode_code_order(self) -> None:
    self.assertEqual(MISSION_OBS_MODE_NAMES, tuple(MISSION_OBS_MODE_CODE_BY_NAME))
    self.assertEqual(set(MISSION_OBS_MODE_NAMES), VALID_MISSION_OBS_MODES)
    codes = [MISSION_OBS_MODE_CODE_BY_NAME[mode] for mode in MISSION_OBS_MODE_NAMES]
    self.assertEqual(codes, sorted(codes))

  def test_training_cli_choices_derive_from_owners(self) -> None:
    from python.training.cli import ACTION_MODE_CHOICES, MISSION_OBS_MODE_CHOICES

    self.assertEqual(MISSION_OBS_MODE_CHOICES, list(MISSION_OBS_MODE_NAMES))
    self.assertEqual(ACTION_MODE_CHOICES, list(ACTION_MODES))

  def test_eval_utils_choices_derive_from_owner(self) -> None:
    from tools.eval.eval_utils import ACTION_MODE_CHOICES as EVAL_ACTION_MODE_CHOICES

    self.assertEqual(EVAL_ACTION_MODE_CHOICES, tuple(ACTION_MODES))

  def test_sb3_eval_base_choices_stay_owner_derived_at_source_level(self) -> None:
    # sb3_eval_base imports torch-backed policy modules, so smoke-safe
    # enforcement checks the source text instead of importing it.
    source = (REPO_ROOT / "tools" / "eval" / "sb3_eval_base.py").read_text(encoding="utf-8")
    self.assertIn("choices=list(ACTION_MODES)", source)
    self.assertIn("choices=list(EXECUTION_STEP_RUNTIME_MODES)", source)
    self.assertIn("choices=list(STEP_INFO_MODES)", source)
    self.assertIn("choices=list(FLIGHT_SHAPING_BACKENDS)", source)
    # Negative guard: a literal choice list starting with the first canonical
    # entry of any owner tuple must not creep back in (either quote style).
    for leading_entry in ("full", "auto", "compiled"):
      self.assertNotIn(f'choices=["{leading_entry}"', source)
      self.assertNotIn(f"choices=['{leading_entry}'", source)

  def test_world_batch_benchmark_uses_semantically_matching_backend_owners(self) -> None:
    source = (
      REPO_ROOT / "tools" / "diagnostics" / "benchmarks" / "world_batch_vec_env.py"
    ).read_text(encoding="utf-8")
    self.assertIn("choices=list(BATCH_VISUAL_BACKENDS)", source)
    self.assertIn("choices=list(BATCH_OBSERVATION_BACKENDS)", source)
    self.assertEqual(source.count("choices=list(FLIGHT_SHAPING_BACKENDS)"), 1)

  def test_world_batch_backend_normalizers_follow_their_owners(self) -> None:
    from python.rl.runtime.world_batch.normalize import (
      normalize_batch_observation_backend,
      normalize_batch_visual_backend,
    )

    for mode in BATCH_OBSERVATION_BACKENDS:
      self.assertEqual(normalize_batch_observation_backend(mode), mode)
    for mode in BATCH_VISUAL_BACKENDS:
      self.assertEqual(normalize_batch_visual_backend(mode), mode)


if __name__ == "__main__":
  unittest.main()
