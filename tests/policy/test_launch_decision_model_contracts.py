from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from python.rl.policy_algo.model_contracts import (
  LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
  LAUNCH_DECISION_CONTRACT_VERSION_KEY,
  LaunchDecisionConfigProvenance,
  LaunchDecisionContractError,
  LaunchDecisionContributor,
  LaunchDecisionMode,
  LaunchDecisionTrainingScope,
  active_model_contracts_for_config,
  resolve_launch_decision_contract,
  validate_launch_decision_contract,
  validate_training_config_contract,
)
from tools.maintenance.generate_launch_decision_fixtures import (
  _active_hybrid_configs,
  _source_revision,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
ACTIVE_AIR_CONFIGS = REPO_ROOT / "examples" / "config" / "training" / "active" / "air_combat"


def _config(**policy_kwargs: Any) -> dict[str, Any]:
  if "launch_decision_mode" in policy_kwargs or "launch_decision_owner_mode" in policy_kwargs:
    policy_kwargs.setdefault(
      LAUNCH_DECISION_CONTRACT_VERSION_KEY,
      LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
    )
  return {
    "policy": "HierarchicalMoEExecutionPolicy",
    "hyperparameters": {
      "policy_kwargs": {
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "hmoe_residual_scale": 0.18,
        **policy_kwargs,
      },
    },
  }


def _resolve(config: dict[str, Any]):
  return resolve_launch_decision_contract(config, require_legacy_provenance=False)


def _init_fixture_repo(root: Path) -> Path:
  subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
  subprocess.run(
    ["git", "-C", str(root), "config", "user.email", "fixture@example.invalid"],
    check=True,
  )
  subprocess.run(
    ["git", "-C", str(root), "config", "user.name", "Fixture Test"],
    check=True,
  )
  config_path = (
    root
    / "examples"
    / "config"
    / "training"
    / "active"
    / "air_combat"
    / "fixture.json"
  )
  config_path.parent.mkdir(parents=True, exist_ok=True)
  config_path.write_text(
    json.dumps(_config(hybrid_event_head_lr_scale=10.0), sort_keys=True) + "\n",
    encoding="utf-8",
  )
  subprocess.run(["git", "-C", str(root), "add", "."], check=True)
  subprocess.run(
    ["git", "-C", str(root), "commit", "-m", "fixture baseline"],
    check=True,
    capture_output=True,
  )
  return config_path


class LaunchDecisionModelContractTests(unittest.TestCase):
  def test_legacy_without_mode_preserves_window_precedence_for_frozen_legacy(self) -> None:
    config = _config(
      hybrid_event_head_lr_scale=10.0,
      hybrid_event_use_window_classifier_head=True,
      hybrid_event_use_stopping_head=True,
    )

    self.assertEqual(
      validate_launch_decision_contract(config, require_legacy_provenance=False),
      [],
    )
    contract = _resolve(config)

    self.assertEqual(contract.mode, LaunchDecisionMode.LEGACY_COMPOSED_V0)
    self.assertFalse(contract.explicit_mode)
    self.assertEqual(contract.compatibility_mode, "legacy_window_precedence")
    self.assertEqual(contract.compatibility_precedence, "window_classifier_before_stopping")
    self.assertIn(LaunchDecisionContributor.WINDOW_CLASSIFIER_ADAPTER, contract.contributors)
    self.assertEqual(
      contract.ignored_contributors,
      (LaunchDecisionContributor.STOPPING_ADAPTER,),
    )
    self.assertEqual(contract.allowed_training_scopes, (LaunchDecisionTrainingScope.COMPATIBILITY,))
    self.assertFalse(contract.acceptance_eligible)

  def test_markerless_legacy_requires_exact_provenance_when_enforced(self) -> None:
    config = _config(hybrid_event_head_lr_scale=10.0)
    frozen = LaunchDecisionConfigProvenance(
      source_revision="abc123",
      path="examples/config/training/active/air_combat/frozen.json",
      sha256="1" * 64,
    )
    self.assertEqual(
      validate_launch_decision_contract(
        config,
        provenance=frozen,
        legacy_provenance_allowlist=(frozen,),
        require_legacy_provenance=True,
      ),
      [],
    )
    changed = LaunchDecisionConfigProvenance(
      source_revision=frozen.source_revision,
      path=frozen.path,
      sha256="2" * 64,
    )
    violations = validate_launch_decision_contract(
      config,
      provenance=changed,
      legacy_provenance_allowlist=(frozen,),
      require_legacy_provenance=True,
    )
    self.assertTrue(any("unmarked_nonlegacy_config" in item.reason for item in violations))

  def test_fixture_inventory_reads_declared_revision_not_dirty_worktree(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      root = Path(temp_dir)
      config_path = _init_fixture_repo(root)
      frozen_revision = _source_revision(root, "HEAD")
      committed_bytes = config_path.read_bytes()

      config_path.write_text(
        json.dumps(_config(hybrid_event_head_lr_scale=0.0), sort_keys=True) + "\n",
        encoding="utf-8",
      )
      self.assertNotEqual(config_path.read_bytes(), committed_bytes)

      records = _active_hybrid_configs(root, frozen_revision)

      self.assertEqual(len(records), 1)
      self.assertEqual(records[0]["source_revision"], frozen_revision)
      self.assertEqual(
        records[0]["sha256"],
        hashlib.sha256(committed_bytes).hexdigest(),
      )
      self.assertNotEqual(
        records[0]["sha256"],
        hashlib.sha256(config_path.read_bytes()).hexdigest(),
      )

  def test_fixture_source_revision_rejects_unknown_and_non_commit(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
      root = Path(temp_dir)
      _init_fixture_repo(root)

      with self.assertRaises(subprocess.CalledProcessError):
        _source_revision(root, "definitely-not-a-revision")

      blob = subprocess.run(
        ["git", "-C", str(root), "hash-object", "-w", "--stdin"],
        input="not a commit\n",
        check=True,
        capture_output=True,
        text=True,
      ).stdout.strip()
      with self.assertRaises(subprocess.CalledProcessError):
        _source_revision(root, blob)

  def test_strict_mode_has_single_direct_write_owner(self) -> None:
    config = _config(
      launch_decision_mode=LaunchDecisionMode.DIRECT_BOUNDARY_V1_STRICT.value,
      hybrid_event_head_lr_scale=10.0,
      hybrid_event_use_window_classifier_head=False,
      hybrid_event_use_stopping_head=False,
    )

    contract = _resolve(config)

    self.assertEqual(contract.mode, LaunchDecisionMode.DIRECT_BOUNDARY_V1_STRICT)
    self.assertEqual(contract.trainable_parameter_roles, ("hybrid_event_head",))
    self.assertEqual(
      contract.detached_parameter_roles,
      ("action_net", "policy_trunk", "hmoe_event_slice"),
    )
    self.assertEqual(contract.allowed_training_scopes, (LaunchDecisionTrainingScope.DIRECT_BOUNDARY,))
    self.assertTrue(contract.acceptance_eligible)

  def test_governed_and_legacy_include_policy_trunk_but_auxiliary_does_not(self) -> None:
    governed = _resolve(
      _config(
        launch_decision_mode="governed_composed_v1",
        hybrid_event_head_lr_scale=10.0,
      )
    )
    legacy = _resolve(_config(hybrid_event_head_lr_scale=10.0))
    auxiliary = _resolve(
      _config(
        launch_decision_mode="auxiliary_only_v1",
        hybrid_event_head_lr_scale=0.0,
      )
    )
    self.assertEqual(
      governed.trainable_parameter_roles,
      ("action_net", "policy_trunk", "hmoe_event_slice", "hybrid_event_head"),
    )
    self.assertEqual(
      legacy.trainable_parameter_roles,
      ("action_net", "policy_trunk", "hmoe_event_slice", "hybrid_event_head"),
    )
    self.assertEqual(auxiliary.trainable_parameter_roles, ("auxiliary_heads",))
    self.assertIn("policy_trunk", auxiliary.detached_parameter_roles)

  def test_hybrid_action_spec_string_name_and_mode_forms_are_identical(self) -> None:
    contracts = []
    for spec in (
      "air_combat_hybrid_v1",
      {"name": "air_combat_hybrid_v1"},
      {"mode": "air_combat_hybrid_v1"},
    ):
      config = _config(
        launch_decision_mode="governed_composed_v1",
        hybrid_event_head_lr_scale=10.0,
      )
      config["hyperparameters"]["policy_kwargs"]["hybrid_action_spec"] = spec
      contracts.append(_resolve(config))
    self.assertEqual(contracts[0].contributors, contracts[1].contributors)
    self.assertEqual(contracts[0].contributors, contracts[2].contributors)
    self.assertEqual(contracts[0].trainable_parameter_roles, contracts[1].trainable_parameter_roles)
    self.assertEqual(contracts[0].trainable_parameter_roles, contracts[2].trainable_parameter_roles)

  def test_hybrid_action_spec_malformed_unknown_and_missing_reject_explicit_owner(self) -> None:
    for spec in ({}, {"name": "wrong"}, {"name": "a", "mode": "b"}, 42, None):
      with self.subTest(spec=spec):
        config = _config(
          launch_decision_mode="governed_composed_v1",
          hybrid_event_head_lr_scale=10.0,
        )
        if spec is None:
          config["hyperparameters"]["policy_kwargs"].pop("hybrid_action_spec")
        else:
          config["hyperparameters"]["policy_kwargs"]["hybrid_action_spec"] = spec
        self.assertTrue(validate_launch_decision_contract(config))
        with self.assertRaises(LaunchDecisionContractError):
          resolve_launch_decision_contract(config)

  def test_strict_mode_rejects_missing_head_and_adapters(self) -> None:
    config = _config(
      launch_decision_mode="direct_boundary_v1_strict",
      hybrid_event_use_window_classifier_head=True,
      hybrid_event_use_stopping_head=False,
    )

    violations = validate_launch_decision_contract(config)
    paths = {violation.path for violation in violations}
    self.assertIn("hyperparameters.policy_kwargs.hybrid_event_head_lr_scale", paths)
    self.assertIn("hyperparameters.policy_kwargs.hybrid_event_use_window_classifier_head", paths)
    with self.assertRaises(LaunchDecisionContractError):
      resolve_launch_decision_contract(config)

  def test_explicit_mode_requires_persisted_contract_version(self) -> None:
    config = _config(
      launch_decision_mode="governed_composed_v1",
      hybrid_event_head_lr_scale=10.0,
    )
    config["hyperparameters"]["policy_kwargs"].pop(LAUNCH_DECISION_CONTRACT_VERSION_KEY)
    violations = validate_launch_decision_contract(config)
    self.assertTrue(any("persisted contract version" in item.reason for item in violations))

  def test_version_only_and_wrong_version_reject(self) -> None:
    version_only = _config()
    version_only["hyperparameters"]["policy_kwargs"][LAUNCH_DECISION_CONTRACT_VERSION_KEY] = (
      LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION
    )
    wrong = _config(
      launch_decision_mode="governed_composed_v1",
      hybrid_event_head_lr_scale=10.0,
    )
    wrong["hyperparameters"]["policy_kwargs"][LAUNCH_DECISION_CONTRACT_VERSION_KEY] = "wrong"
    self.assertTrue(validate_launch_decision_contract(version_only))
    self.assertTrue(validate_launch_decision_contract(wrong))

  def test_flat_and_nested_mode_declarations_allow_equal_and_reject_different(self) -> None:
    equal = _config(
      launch_decision_mode="governed_composed_v1",
      hybrid_event_head_lr_scale=10.0,
    )
    equal["launch_decision_mode"] = "governed_composed_v1"
    equal["policy_kwargs"] = {
      "launch_decision_mode": "governed_composed_v1",
      LAUNCH_DECISION_CONTRACT_VERSION_KEY: LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
    }
    self.assertEqual(validate_launch_decision_contract(equal), [])

    different = _config(
      launch_decision_mode="governed_composed_v1",
      hybrid_event_head_lr_scale=10.0,
    )
    different["launch_decision_mode"] = "legacy_composed_v0"
    violations = validate_launch_decision_contract(different)
    self.assertTrue(any("Repeated launch-decision declarations" in item.reason for item in violations))

  def test_new_governed_mode_rejects_competing_adapters(self) -> None:
    config = _config(
      launch_decision_mode="governed_composed_v1",
      hybrid_event_head_lr_scale=10.0,
      hybrid_event_use_window_classifier_head=True,
      hybrid_event_use_stopping_head=True,
    )

    violations = validate_launch_decision_contract(config)
    self.assertTrue(any("competing window and stopping adapters" in item.reason for item in violations))
    self.assertTrue(any("adapter_coupled_v1" in item.expected for item in violations))

  def test_adapter_coupled_mode_requires_exactly_one_adapter(self) -> None:
    empty = _config(
      launch_decision_mode="adapter_coupled_v1",
      hybrid_event_head_lr_scale=10.0,
    )
    both = _config(
      launch_decision_mode="adapter_coupled_v1",
      hybrid_event_head_lr_scale=10.0,
      hybrid_event_use_window_classifier_head=True,
      hybrid_event_use_stopping_head=True,
    )

    self.assertTrue(validate_launch_decision_contract(empty))
    self.assertTrue(validate_launch_decision_contract(both))

  def test_owner_contract_round_trip_is_stable(self) -> None:
    config = _config(
      launch_decision_mode="governed_composed_v1",
      hybrid_event_head_lr_scale=10.0,
    )
    contract = _resolve(config)
    restored = type(contract).from_dict(contract.as_dict())
    self.assertEqual(restored, contract)
    self.assertEqual(restored.as_dict(), contract.as_dict())

  def test_current_hybrid_inventory_defaults_to_legacy_and_has_seven_headless_entries(self) -> None:
    modes = []
    head_enabled = 0
    eligibility = []
    for path in sorted(ACTIVE_AIR_CONFIGS.glob("*.json")):
      payload = json.loads(path.read_text(encoding="utf-8"))
      policy_kwargs = payload.get("hyperparameters", {}).get("policy_kwargs", {})
      spec = policy_kwargs.get("hybrid_action_spec")
      spec_name = spec if isinstance(spec, str) else spec.get("name", spec.get("mode")) if isinstance(spec, dict) else None
      if spec_name != "air_combat_hybrid_v1":
        continue
      contract = _resolve(payload)
      modes.append(contract.mode)
      eligibility.append(contract.acceptance_eligible)
      head_enabled += int(float(policy_kwargs.get("hybrid_event_head_lr_scale", 0.0) or 0.0) > 0.0)

    self.assertEqual(len(modes), 14)
    self.assertEqual(head_enabled, 7)
    self.assertEqual(modes, [LaunchDecisionMode.LEGACY_COMPOSED_V0] * 14)
    self.assertEqual(eligibility, [False] * 14)

  def test_existing_mechanism_contract_validation_remains_clean_for_active_configs(self) -> None:
    for path in sorted(ACTIVE_AIR_CONFIGS.glob("*.json")):
      with self.subTest(config=path.name):
        payload = json.loads(path.read_text(encoding="utf-8"))
        # This lane predates C4 provenance-aware loading and only verifies the
        # existing mechanism gates remain clean.
        violations = validate_training_config_contract(payload)
        non_provenance = [
          item for item in violations if item.path != "launch_decision_provenance"
        ]
        self.assertEqual(non_provenance, [])


if __name__ == "__main__":
  unittest.main()
