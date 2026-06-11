from __future__ import annotations

import argparse
import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.env_config import infer_include_visual_from_train_config, resolve_env_settings # noqa: E402
from python.runtime_compat import normalize_runtime_compatibility_enabled # noqa: E402


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
    "runtime_compatibility_enabled": None,
  }
  base.update(overrides)
  return argparse.Namespace(**base)


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
        "runtime_compatibility_enabled": "yes",
      }
    }

    resolved = resolve_env_settings(train_config, _make_args())
    self.assertEqual(resolved["mission_obs_mode"], "nav_v2")
    self.assertEqual(resolved["execution_step_runtime_mode"], "compiled")
    self.assertEqual(resolved["step_info_mode"], "terminal")
    self.assertEqual(resolved["flight_shaping_backend"], "gpu_host")
    self.assertEqual(resolved["temporal_history_len"], 16)
    self.assertTrue(resolved["runtime_compatibility_enabled"])

  def test_resolve_env_settings_accepts_domain_neutral_shaping_backend_alias(self) -> None:
    train_config = {
      "env": {
        "include_proprio": True,
        "mission_obs_mode": "naval_screen_station_v1",
        "action_mode": "naval_station3",
        "shaping_backend": " GPU_HOST ",
      }
    }

    resolved = resolve_env_settings(train_config, _make_args())
    self.assertEqual(resolved["flight_shaping_backend"], "gpu_host")

  def test_resolve_env_settings_accepts_air_combat_c2_roe_mission_obs_mode(self) -> None:
    resolved = resolve_env_settings(
      {"env": {"mission_obs_mode": "AIR_COMBAT_C2_ROE_V1"}},
      _make_args(),
    )

    self.assertEqual(resolved["mission_obs_mode"], "air_combat_c2_roe_v1")

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

  def test_resolve_env_settings_rejects_legacy_runtime_mode(self) -> None:
    with self.assertRaisesRegex(ValueError, "execution_step_runtime_mode='legacy' has been removed"):
      resolve_env_settings(
        {
          "env": {
            "execution_step_runtime_mode": "legacy",
          }
        },
        _make_args(),
      )

  def test_resolve_env_settings_rejects_legacy_flight_shaping_backend(self) -> None:
    with self.assertRaisesRegex(ValueError, "flight_shaping_backend='legacy' has been removed"):
      resolve_env_settings(
        {
          "env": {
            "flight_shaping_backend": "legacy",
          }
        },
        _make_args(),
      )

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
    self.assertFalse(resolved["runtime_compatibility_enabled"])

  def test_resolve_env_settings_defaults_runtime_compatibility_to_false(self) -> None:
    resolved = resolve_env_settings({}, _make_args())
    self.assertIsNone(resolved["execution_step_runtime_mode"])
    self.assertFalse(resolved["runtime_compatibility_enabled"])

  def test_runtime_compatibility_enabled_rejects_ambiguous_strings(self) -> None:
    with self.assertRaisesRegex(ValueError, "Unknown runtime_compatibility_enabled"):
      normalize_runtime_compatibility_enabled("maybe")

    with self.assertRaisesRegex(ValueError, "Unknown runtime_compatibility_enabled"):
      resolve_env_settings(
        {"env": {"runtime_compatibility_enabled": "legacy-ish"}},
        _make_args(),
      )

  def test_resolve_env_settings_accepts_dedicated_naval_action_mode(self) -> None:
    resolved = resolve_env_settings(
      {"env": {"action_mode": "naval_station3"}},
      _make_args(),
    )
    self.assertEqual(resolved["action_mode"], "naval_station3")

  def test_resolve_env_settings_accepts_air_combat_hybrid_action_mode(self) -> None:
    resolved = resolve_env_settings(
      {"env": {"action_mode": "air_combat_hybrid_v1"}},
      _make_args(),
    )
    self.assertEqual(resolved["action_mode"], "air_combat_hybrid_v1")

  def test_resolve_env_settings_rejects_invalid_optional_runtime_mode(self) -> None:
    with self.assertRaisesRegex(ValueError, "Unknown execution_step_runtime_mode"):
      resolve_env_settings(
        {"env": {"execution_step_runtime_mode": "bad-mode"}},
        _make_args(),
      )

    with self.assertRaisesRegex(ValueError, "Unknown flight_shaping_backend"):
      resolve_env_settings(
        {"env": {"flight_shaping_backend": "bad-backend"}},
        _make_args(),
      )

    with self.assertRaisesRegex(ValueError, "Unknown flight_shaping_backend"):
      resolve_env_settings(
        {"env": {"shaping_backend": "bad-backend"}},
        _make_args(),
      )


if __name__ == "__main__":
  unittest.main()
