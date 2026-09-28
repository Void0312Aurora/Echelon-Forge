from __future__ import annotations

from copy import deepcopy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

import torch as th

from python.rl.policy_algo.model_contracts import (
  LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
  LAUNCH_DECISION_CONTRACT_VERSION_KEY,
  LaunchDecisionMode,
  resolve_launch_decision_contract,
)
from python.rl.policy_checkpoint import (
  LaunchDecisionMigrationError,
  _optimizer_manifest,
  _replay_manifest,
  _replay_state_for_model,
  build_launch_decision_checkpoint_envelope,
  launch_decision_config_fingerprint,
  launch_decision_surface_active,
  migrate_launch_decision_checkpoint_envelope,
  validate_launch_decision_checkpoint_envelope,
  validate_loaded_sb3_launch_decision_checkpoint,
  validate_sb3_checkpoint_against_config,
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


def _optimizer_state():
  return {
    "state": {
      "0": {
        "step": th.tensor(1.0),
        "exp_avg": th.tensor([0.25, -0.5]),
        "exp_avg_sq": th.tensor([0.0625, 0.25]),
      },
    },
    "param_groups": [
      {
        "name": "shared",
        "params": [0],
        "lr": 1.0e-3,
        "betas": (0.9, 0.999),
        "eps": 1.0e-8,
      },
    ],
  }


def _resolve(config):
  return resolve_launch_decision_contract(config, require_legacy_provenance=False)


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
    round_trip = translate_launch_decision_config(migrated)
    self.assertEqual(
      round_trip["launch_decision_migration"]["migration_id"],
      "legacy_to_governed_v1",
    )
    self.assertEqual(
      round_trip["launch_decision_migration"]["resolved_mode"],
      LaunchDecisionMode.GOVERNED_COMPOSED_V1.value,
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
      optimizer_state=_optimizer_state(),
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

  def test_migration_metadata_is_persisted_and_consumed_by_sidecar_validation(self) -> None:
    config = _config(launch_decision_mode=LaunchDecisionMode.GOVERNED_COMPOSED_V1.value)
    config["launch_decision_migration"] = {
      "schema_version": "launch_decision_config_migration_v1",
      "source_mode": "legacy_composed_v0",
      "resolved_mode": "governed_composed_v1",
      "source_explicit": False,
      "compatibility_mode": "none",
      "compatibility_precedence": None,
      "migration_id": "legacy_to_governed_v1",
    }
    contract = _resolve(config)
    replay = SimpleNamespace(
      storage="latent",
      capacity=16,
      positives=th.zeros((1, 2)),
      negatives=th.ones((1, 2)),
    )
    model = SimpleNamespace(
      policy=_FakePolicy(),
      window_classifier_replay_enabled=True,
      window_classifier_replay_storage="latent",
      _window_classifier_replay=replay,
      replay_buffer=None,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
      checkpoint = Path(tmpdir) / "model.zip"
      with zipfile.ZipFile(checkpoint, "w") as archive:
        archive.writestr(
          "data",
          json.dumps({"policy_kwargs": config["hyperparameters"]["policy_kwargs"]}),
        )
      sidecar = write_sb3_launch_decision_sidecar(
        str(checkpoint),
        model=model,
        owner_contract=contract,
        source_config_fingerprint=launch_decision_config_fingerprint(config),
        migration=config["launch_decision_migration"],
      )
      payload = json.loads(Path(sidecar).read_text(encoding="utf-8"))
      self.assertEqual(payload["migration"], config["launch_decision_migration"])
      validate_loaded_sb3_launch_decision_checkpoint(
        str(checkpoint), model=model, expected_config=config
      )

      payload["migration"]["migration_id"] = "different_migration"
      Path(sidecar).write_text(json.dumps(payload), encoding="utf-8")
      with self.assertRaisesRegex(LaunchDecisionMigrationError, "migration metadata"):
        validate_loaded_sb3_launch_decision_checkpoint(
          str(checkpoint), model=model, expected_config=config
        )

      payload["migration"] = config["launch_decision_migration"]
      Path(sidecar).write_text(json.dumps(payload), encoding="utf-8")
      replay.positives = th.full((1, 2), 9.0)
      with self.assertRaisesRegex(LaunchDecisionMigrationError, "replay_manifest"):
        validate_loaded_sb3_launch_decision_checkpoint(
          str(checkpoint), model=model, expected_config=config
        )

  def test_optimizer_manifest_rejects_value_and_hyperparameter_drift(self) -> None:
    contract = _resolve(_config())
    envelope = build_launch_decision_checkpoint_envelope(
      state_dict={"x": th.zeros((1,))},
      optimizer_state=_optimizer_state(),
      replay_state=_replay_state(),
      owner_contract=contract,
    )

    for mutator in (
      lambda state: state["state"]["0"].__setitem__("step", th.tensor(2.0)),
      lambda state: state["state"]["0"].__setitem__("exp_avg", th.tensor([0.5, -0.5])),
      lambda state: state["state"]["0"].__setitem__("exp_avg_sq", th.tensor([0.125, 0.25])),
      lambda state: state["param_groups"][0].__setitem__("lr", 2.0e-3),
      lambda state: state["param_groups"][0].__setitem__("betas", (0.8, 0.999)),
    ):
      drifted = deepcopy(envelope)
      mutator(drifted["optimizer_state"])
      with self.assertRaisesRegex(LaunchDecisionMigrationError, "optimizer groups/state differ"):
        validate_launch_decision_checkpoint_envelope(drifted)

    manifest = _optimizer_manifest(_optimizer_state())
    self.assertIn("state_content_fingerprint", manifest)
    self.assertIn("hyperparameters", manifest["groups"][0])

  def test_window_classifier_replay_is_part_of_compatibility_identity(self) -> None:
    replay = SimpleNamespace(
      storage="latent",
      capacity=16,
      positives=th.tensor([[1.0, 2.0]]),
      negatives=th.tensor([[-1.0, -2.0]]),
    )
    model = SimpleNamespace(
      window_classifier_replay_enabled=True,
      _window_classifier_replay=replay,
      replay_buffer=None,
    )
    first = _replay_state_for_model(model)
    replay.positives = th.tensor([[9.0, 2.0]])
    second = _replay_state_for_model(model)
    self.assertNotEqual(
      launch_decision_config_fingerprint(first),
      launch_decision_config_fingerprint(second),
    )
    self.assertEqual(first["storage"], "latent")
    self.assertEqual(first["capacity"], 16)

    missing = SimpleNamespace(
      window_classifier_replay_enabled=True,
      _window_classifier_replay=None,
      replay_buffer=None,
    )
    with self.assertRaisesRegex(LaunchDecisionMigrationError, "replay is enabled"):
      _replay_state_for_model(missing)

    incomplete = SimpleNamespace(
      window_classifier_replay_enabled=True,
      window_classifier_replay_storage="latent",
      _window_classifier_replay=SimpleNamespace(
        storage="latent",
        capacity=16,
        positives=th.zeros((1, 2)),
      ),
      replay_buffer=None,
    )
    with self.assertRaisesRegex(LaunchDecisionMigrationError, "state surface is incomplete"):
      _replay_state_for_model(incomplete)

  def test_replay_manifest_records_nested_observation_shapes(self) -> None:
    replay = SimpleNamespace(
      storage="observation",
      capacity=4,
      positive_observations={"state": th.zeros((2, 3)), "mask": th.ones((2, 1))},
      negative_observations={"state": th.ones((1, 3)), "mask": th.zeros((1, 1))},
    )
    model = SimpleNamespace(
      window_classifier_replay_enabled=True,
      window_classifier_replay_storage="observation",
      _window_classifier_replay=replay,
      replay_buffer=None,
    )
    state = _replay_state_for_model(model)
    manifest = _replay_manifest(state)
    self.assertEqual(manifest["row_shapes"]["positive_rows"]["state"], [2, 3])
    self.assertEqual(manifest["row_shapes"]["negative_rows"]["mask"], [1, 1])

  def test_launch_surface_detection_skips_ordinary_policy(self) -> None:
    ordinary = {
      "policy": "MultiInputPolicy",
      "hyperparameters": {"policy_kwargs": {"features_extractor_class": "TransformerExtractor"}},
    }
    self.assertFalse(launch_decision_surface_active(ordinary))
    self.assertTrue(launch_decision_surface_active(_config()))

    legacy_hmoe = {
      "policy": "HierarchicalMoEExecutionPolicy",
      "hyperparameters": {
        "policy_kwargs": {
          "features_extractor_class": "TransformerExtractor",
          "hmoe_residual_scale": 0.18,
          "hmoe_head_lr_scale": 0.15,
        },
      },
    }
    self.assertFalse(launch_decision_surface_active(legacy_hmoe))
    translated = translate_launch_decision_config(legacy_hmoe)
    self.assertNotIn("launch_decision_migration", translated)
    self.assertNotIn("launch_decision_mode", translated["hyperparameters"]["policy_kwargs"])

  def test_named_extractor_config_fingerprint_is_stable_across_runtime_translation(self) -> None:
    class TemporalTransformerExtractor:
      pass

    serialized = _config(features_extractor_class="TemporalTransformerExtractor")
    runtime = _config(features_extractor_class=TemporalTransformerExtractor)
    self.assertEqual(
      launch_decision_config_fingerprint(serialized),
      launch_decision_config_fingerprint(runtime),
    )

  def test_non_launch_checkpoint_validation_is_an_explicit_noop(self) -> None:
    config = {
      "policy": "MultiInputPolicy",
      "hyperparameters": {"policy_kwargs": {}},
    }
    pre = validate_sb3_checkpoint_against_config("missing-model.zip", config)
    post = validate_loaded_sb3_launch_decision_checkpoint(
      "missing-model.zip",
      model=object(),
      expected_config=config,
    )
    self.assertTrue(pre["skipped"])
    self.assertTrue(post["skipped"])
    self.assertEqual(pre["reason"], "non_launch_policy")
    self.assertEqual(post["reason"], "non_launch_policy")

  def test_translation_rejects_conflicting_flat_and_nested_modes(self) -> None:
    source = _config(hybrid_event_head_lr_scale=10.0)
    source["launch_decision_mode"] = "governed_composed_v1"
    source["hyperparameters"]["policy_kwargs"]["launch_decision_mode"] = "legacy_composed_v0"
    with self.assertRaises(LaunchDecisionConfigMigrationError):
      translate_launch_decision_config(source)

  def test_sb3_sidecar_persists_contract_and_artifact_manifests(self) -> None:
    config = _config(hybrid_event_head_lr_scale=10.0)
    contract = _resolve(config)
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
    contract = _resolve(_config())
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
