from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import torch as th

from python.rl.policy_algo.model_contracts import LaunchDecisionMode, resolve_launch_decision_contract
from python.rl.policy_checkpoint import (
  LaunchDecisionMigrationError,
  build_launch_decision_checkpoint_envelope,
  migrate_launch_decision_checkpoint_envelope,
  validate_launch_decision_checkpoint_envelope,
)
from python.training.deps import (
  LaunchDecisionConfigMigrationError,
  translate_launch_decision_config,
)


def _config(**kwargs):
  return {
    "policy": "HierarchicalMoEExecutionPolicy",
    "hyperparameters": {
      "policy_kwargs": {
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "hmoe_residual_scale": 0.25,
        "hmoe_head_lr_scale": 0.35,
        **kwargs,
      },
    },
  }


def _replay_state():
  return {
    "schema_version": "window_classifier_replay_v1",
    "storage": "latent",
    "capacity": 16,
    "positive_rows": [[1.0, 2.0]],
    "negative_rows": [[-1.0, -2.0]],
  }


class LaunchDecisionMigrationTests(unittest.TestCase):
  def test_legacy_config_is_explicit_only_in_memory(self) -> None:
    source = _config(hybrid_event_head_lr_scale=10.0)
    translated = translate_launch_decision_config(source)

    self.assertNotIn("launch_decision_mode", source["hyperparameters"]["policy_kwargs"])
    self.assertEqual(
      translated["hyperparameters"]["policy_kwargs"]["launch_decision_mode"],
      LaunchDecisionMode.LEGACY_COMPOSED_V0.value,
    )
    self.assertEqual(
      translated["launch_decision_migration"]["source_mode"],
      LaunchDecisionMode.LEGACY_COMPOSED_V0.value,
    )

  def test_mode_change_requires_named_migration_and_validates_target(self) -> None:
    source = _config(hybrid_event_head_lr_scale=10.0)
    with self.assertRaises(LaunchDecisionConfigMigrationError):
      translate_launch_decision_config(
        source,
        target_mode=LaunchDecisionMode.GOVERNED_COMPOSED_V1.value,
      )

    migrated = translate_launch_decision_config(
      source,
      target_mode=LaunchDecisionMode.GOVERNED_COMPOSED_V1.value,
      migration_id="legacy_to_governed_v1",
    )
    self.assertEqual(
      migrated["hyperparameters"]["policy_kwargs"]["launch_decision_mode"],
      LaunchDecisionMode.GOVERNED_COMPOSED_V1.value,
    )
    self.assertEqual(
      migrated["launch_decision_migration"]["migration_id"],
      "legacy_to_governed_v1",
    )

  def test_target_conflict_is_not_hidden_by_translation(self) -> None:
    with self.assertRaises(LaunchDecisionConfigMigrationError):
      translate_launch_decision_config(
        _config(
          launch_decision_mode=LaunchDecisionMode.GOVERNED_COMPOSED_V1.value,
          hybrid_event_head_lr_scale=10.0,
          hybrid_event_use_window_classifier_head=True,
          hybrid_event_use_stopping_head=True,
        )
      )

  def test_checkpoint_optimizer_replay_round_trip_and_explicit_migration(self) -> None:
    source_contract = resolve_launch_decision_contract(
      _config(
        launch_decision_mode=LaunchDecisionMode.LEGACY_COMPOSED_V0.value,
        hybrid_event_head_lr_scale=10.0,
      )
    )
    envelope = build_launch_decision_checkpoint_envelope(
      state_dict={
        "action_net.weight": th.zeros((2, 3)),
        "action_net.bias": th.ones((2,)),
      },
      optimizer_state={
        "state": {"0": {"step": th.tensor(1)}},
        "param_groups": [{"name": "shared", "params": [0]}],
      },
      replay_state=_replay_state(),
      owner_contract=source_contract,
      source_config_fingerprint="sha256:test",
    )
    restored = validate_launch_decision_checkpoint_envelope(envelope)
    self.assertEqual(restored, source_contract)

    target_contract = resolve_launch_decision_contract(
      _config(
        launch_decision_mode=LaunchDecisionMode.GOVERNED_COMPOSED_V1.value,
        hybrid_event_head_lr_scale=10.0,
      )
    )
    migrated = migrate_launch_decision_checkpoint_envelope(
      envelope,
      target_contract=target_contract,
      migration_id="legacy_to_governed_v1",
    )
    self.assertTrue(migrated["migration"]["state_artifacts_preserved"])
    self.assertEqual(
      validate_launch_decision_checkpoint_envelope(migrated).mode,
      LaunchDecisionMode.GOVERNED_COMPOSED_V1,
    )
    self.assertEqual(
      migrated["state_dict_manifest"],
      envelope["state_dict_manifest"],
    )

  def test_missing_optimizer_or_replay_identity_fails_actionably(self) -> None:
    contract = resolve_launch_decision_contract(_config())
    with self.assertRaises(LaunchDecisionMigrationError):
      build_launch_decision_checkpoint_envelope(
        state_dict={"x": th.zeros((1,))},
        optimizer_state={"state": {}},
        replay_state=_replay_state(),
        owner_contract=contract,
      )
    with self.assertRaises(LaunchDecisionMigrationError):
      build_launch_decision_checkpoint_envelope(
        state_dict={"x": th.zeros((1,))},
        optimizer_state={"state": {}, "param_groups": []},
        replay_state={"storage": "latent", "capacity": 1},
        owner_contract=contract,
      )


if __name__ == "__main__":
  unittest.main()
