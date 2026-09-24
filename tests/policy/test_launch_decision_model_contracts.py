from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from python.rl.policy_algo.model_contracts import (
  LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
  LAUNCH_DECISION_CONTRACT_VERSION_KEY,
  LaunchDecisionContractError,
  LaunchDecisionContributor,
  LaunchDecisionMode,
  LaunchDecisionTrainingScope,
  active_model_contracts_for_config,
  resolve_launch_decision_contract,
  validate_launch_decision_contract,
  validate_training_config_contract,
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


class LaunchDecisionModelContractTests(unittest.TestCase):
  def test_legacy_without_mode_preserves_window_precedence_for_old_configs(self) -> None:
    config = _config(
      hybrid_event_head_lr_scale=10.0,
      hybrid_event_use_window_classifier_head=True,
      hybrid_event_use_stopping_head=True,
    )

    self.assertEqual(validate_launch_decision_contract(config), [])
    contract = resolve_launch_decision_contract(config)

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

  def test_strict_mode_has_single_direct_write_owner(self) -> None:
    config = _config(
      launch_decision_mode=LaunchDecisionMode.DIRECT_BOUNDARY_V1_STRICT.value,
      hybrid_event_head_lr_scale=10.0,
      hybrid_event_use_window_classifier_head=False,
      hybrid_event_use_stopping_head=False,
    )

    contract = resolve_launch_decision_contract(config)

    self.assertEqual(contract.mode, LaunchDecisionMode.DIRECT_BOUNDARY_V1_STRICT)
    self.assertEqual(
      contract.trainable_parameter_roles,
      ("hybrid_event_head",),
    )
    self.assertEqual(
      contract.detached_parameter_roles,
      ("action_net", "policy_trunk", "hmoe_event_slice"),
    )
    self.assertEqual(contract.allowed_training_scopes, (LaunchDecisionTrainingScope.DIRECT_BOUNDARY,))
    self.assertTrue(contract.acceptance_eligible)

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

  def test_flat_and_nested_mode_declarations_must_agree(self) -> None:
    config = _config(
      launch_decision_mode="governed_composed_v1",
      hybrid_event_head_lr_scale=10.0,
    )
    config["launch_decision_mode"] = "legacy_composed_v0"
    violations = validate_launch_decision_contract(config)
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
    contract = resolve_launch_decision_contract(config)
    restored = type(contract).from_dict(contract.as_dict())
    self.assertEqual(restored, contract)
    self.assertEqual(restored.as_dict(), contract.as_dict())

  def test_governed_contract_declares_policy_trunk_with_latent_contributors(self) -> None:
    contract = resolve_launch_decision_contract(
      _config(
        launch_decision_mode="governed_composed_v1",
        hybrid_event_head_lr_scale=10.0,
      )
    )
    self.assertIn("policy_trunk", contract.trainable_parameter_roles)

  def test_current_hybrid_inventory_defaults_to_legacy_and_has_seven_headless_entries(self) -> None:
    modes = []
    head_enabled = 0
    for path in sorted(ACTIVE_AIR_CONFIGS.glob("*.json")):
      payload = json.loads(path.read_text(encoding="utf-8"))
      policy_kwargs = payload.get("hyperparameters", {}).get("policy_kwargs", {})
      if policy_kwargs.get("hybrid_action_spec") != "air_combat_hybrid_v1":
        continue
      contract = resolve_launch_decision_contract(payload)
      modes.append(contract.mode)
      head_enabled += int(float(policy_kwargs.get("hybrid_event_head_lr_scale", 0.0) or 0.0) > 0.0)

    self.assertEqual(len(modes), 14)
    self.assertEqual(head_enabled, 7)
    self.assertEqual(modes, [LaunchDecisionMode.LEGACY_COMPOSED_V0] * 14)

  def test_existing_mechanism_contract_validation_remains_clean_for_active_configs(self) -> None:
    for path in sorted(ACTIVE_AIR_CONFIGS.glob("*.json")):
      with self.subTest(config=path.name):
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_training_config_contract(payload), [])


if __name__ == "__main__":
  unittest.main()
