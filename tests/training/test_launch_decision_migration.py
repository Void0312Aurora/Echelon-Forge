from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import torch as th

from python.rl.policy_algo.model_contracts import (
  LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
  LAUNCH_DECISION_CONTRACT_VERSION_KEY,
  LaunchDecisionMode,
  resolve_launch_decision_contract,
)
from python.rl.policy_checkpoint import (
  LaunchDecisionMigrationError,
  build_launch_decision_checkpoint_envelope,
  migrate_launch_decision_checkpoint_envelope,
  validate_launch_decision_checkpoint_envelope,
  write_sb3_launch_decision_sidecar,
)
from python.training.deps import (
  LaunchDecisionConfigMigrationError,
  translate_launch_decision_config,
)


def _config(**kwargs):
  if "launch_decision_mode" in kwargs or "launch_decision_owner_mode" in kwargs:
    kwargs.setdefault(LAUNCH_DECISION_CONTRACT_VERSION_KEY, LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION)
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


class _FakePolicy:
  def state_dict(self):
    return {"action_net.weight": th.zeros((2, 3))}

  class _Optimizer:
    def state_dict(self):
      return {
        "state": {"0": {"step": th.tensor(1)}},
        "param_groups": [
          {"name": "action", "params": [0], "parameter_roles": ["action_net"]},
        ],
      }

  optimizer = _Optimizer()


class _FakeModel:
  policy = _FakePolicy()

  replay_buffer = None


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
    with self.assertRaisesRegex(LaunchDecisionMigrationError, "no maintained checkpoint conversion"):
      migrate_launch_decision_checkpoint_envelope(
        envelope,
        target_contract=target_contract,
        migration_id="legacy_to_governed_v1",
      )

  def test_translation_rejects_conflicting_flat_and_nested_modes(self) -> None:
    source = _config(hybrid_event_head_lr_scale=10.0)
    source["launch_decision_mode"] = "governed_composed_v1"
    source["hyperparameters"]["policy_kwargs"]["launch_decision_mode"] = "legacy_composed_v0"
    with self.assertRaises(LaunchDecisionConfigMigrationError):
      translate_launch_decision_config(source)

  def test_sb3_sidecar_persists_contract_and_artifact_manifests(self) -> None:
    config = _config(hybrid_event_head_lr_scale=10.0)
    contract = resolve_launch_decision_contract(config)
    with tempfile.TemporaryDirectory() as tmpdir:
      sidecar = write_sb3_launch_decision_sidecar(
        str(Path(tmpdir) / "model"),
        model=_FakeModel(),
        owner_contract=contract,
        source_config_fingerprint="sha256:test-config",
      )
      payload = json.loads(Path(sidecar).read_text(encoding="utf-8"))
      self.assertEqual(payload["owner_contract"], contract.as_dict())
      self.assertIn("state_dict_manifest", payload)
      self.assertIn("optimizer_manifest", payload)
      self.assertIn("replay_manifest", payload)

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
