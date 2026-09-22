"""Stable-Baselines policy checkpoint loading without runtime bootstrap side effects.

Callers own repository/runtime import configuration. Production entry points can
therefore keep the installed-wheel fallback provided by ``configure_repo_imports``,
while diagnostics tools may still fail closed with ``ensure_repo_imports`` before
importing this module.
"""

from __future__ import annotations

import base64
from copy import deepcopy
import json
import zipfile
from typing import Any, Mapping

from python.rl.policy_algo.model_contracts import (
    LaunchDecisionContractError,
    LaunchDecisionOwnerContract,
    resolve_launch_decision_contract,
)


LAUNCH_DECISION_CHECKPOINT_SCHEMA_VERSION = "launch_decision_checkpoint_v1"


class LaunchDecisionMigrationError(ValueError):
    """Raised when checkpoint/optimizer/replay state cannot be reconciled."""


def _tensor_manifest(value: Any) -> dict[str, Any]:
    shape = getattr(value, "shape", None)
    if shape is None:
        return {"shape": None, "dtype": type(value).__name__}
    try:
        normalized_shape = [int(item) for item in shape]
    except Exception as exc:  # pragma: no cover - defensive serialization boundary
        raise LaunchDecisionMigrationError(f"state entry has an unreadable shape: {value!r}") from exc
    return {
        "shape": normalized_shape,
        "dtype": str(getattr(value, "dtype", type(value).__name__)),
    }


def _state_dict_manifest(state_dict: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(state_dict, Mapping):
        raise LaunchDecisionMigrationError("checkpoint state_dict must be a mapping")
    return {
        str(key): _tensor_manifest(value)
        for key, value in sorted(state_dict.items(), key=lambda item: str(item[0]))
    }


def _optimizer_manifest(optimizer_state: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(optimizer_state, Mapping):
        raise LaunchDecisionMigrationError("optimizer_state must be a mapping")
    groups = optimizer_state.get("param_groups")
    if not isinstance(groups, (list, tuple)):
        raise LaunchDecisionMigrationError(
            "optimizer_state.param_groups is missing; optimizer compatibility cannot be inferred"
        )
    names = [str(group.get("name", f"group_{index}")) for index, group in enumerate(groups) if isinstance(group, Mapping)]
    if len(names) != len(groups):
        raise LaunchDecisionMigrationError("optimizer_state.param_groups contains a non-mapping group")
    return {
        "group_names": names,
        "group_count": len(names),
        "state_keys": sorted(str(key) for key in (optimizer_state.get("state", {}) or {}).keys()),
    }


def _replay_manifest(replay_state: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(replay_state, Mapping):
        raise LaunchDecisionMigrationError("replay_state must be a mapping")
    required = ("schema_version", "storage", "capacity")
    missing = [key for key in required if key not in replay_state]
    if missing:
        raise LaunchDecisionMigrationError(
            "replay_state is missing identity fields: " + ", ".join(missing)
        )
    return {
        "schema_version": str(replay_state["schema_version"]),
        "storage": str(replay_state["storage"]),
        "capacity": int(replay_state["capacity"]),
        "keys": sorted(str(key) for key in replay_state.keys()),
    }


def build_launch_decision_checkpoint_envelope(
    *,
    state_dict: Mapping[str, Any],
    optimizer_state: Mapping[str, Any],
    replay_state: Mapping[str, Any],
    owner_contract: LaunchDecisionOwnerContract | Mapping[str, Any],
    source_config_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Build a serializable envelope with explicit state/optimizer/replay identity."""

    try:
        contract = (
            owner_contract
            if isinstance(owner_contract, LaunchDecisionOwnerContract)
            else LaunchDecisionOwnerContract.from_dict(owner_contract)
        )
    except (TypeError, ValueError) as exc:
        raise LaunchDecisionMigrationError(f"invalid owner contract: {exc}") from exc
    envelope = {
        "schema_version": LAUNCH_DECISION_CHECKPOINT_SCHEMA_VERSION,
        "owner_contract": contract.as_dict(),
        "source_config_fingerprint": source_config_fingerprint,
        "state_dict": dict(state_dict),
        "state_dict_manifest": _state_dict_manifest(state_dict),
        "optimizer_state": dict(optimizer_state),
        "optimizer_manifest": _optimizer_manifest(optimizer_state),
        "replay_state": dict(replay_state),
        "replay_manifest": _replay_manifest(replay_state),
    }
    validate_launch_decision_checkpoint_envelope(envelope)
    return envelope


def validate_launch_decision_checkpoint_envelope(
    envelope: Mapping[str, Any],
    *,
    expected_contract: LaunchDecisionOwnerContract | Mapping[str, Any] | None = None,
) -> LaunchDecisionOwnerContract:
    """Validate schema, contract, tensor shapes, optimizer groups, and replay identity."""

    if not isinstance(envelope, Mapping):
        raise LaunchDecisionMigrationError("checkpoint envelope must be a mapping")
    if envelope.get("schema_version") != LAUNCH_DECISION_CHECKPOINT_SCHEMA_VERSION:
        raise LaunchDecisionMigrationError(
            "unsupported launch-decision checkpoint schema: "
            f"{envelope.get('schema_version')!r}"
        )
    try:
        contract = LaunchDecisionOwnerContract.from_dict(envelope["owner_contract"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LaunchDecisionMigrationError(f"invalid checkpoint owner contract: {exc}") from exc
    if expected_contract is not None:
        try:
            expected = (
                expected_contract
                if isinstance(expected_contract, LaunchDecisionOwnerContract)
                else LaunchDecisionOwnerContract.from_dict(expected_contract)
            )
        except (TypeError, ValueError) as exc:
            raise LaunchDecisionMigrationError(f"invalid expected owner contract: {exc}") from exc
        if contract.mode != expected.mode:
            raise LaunchDecisionMigrationError(
                f"checkpoint mode {contract.mode.value!r} does not match expected {expected.mode.value!r}; "
                "provide a named migration before loading"
            )

    state_dict = envelope.get("state_dict")
    actual_state_manifest = _state_dict_manifest(state_dict)
    if actual_state_manifest != envelope.get("state_dict_manifest"):
        raise LaunchDecisionMigrationError("state_dict keys/shapes differ from the recorded checkpoint manifest")
    optimizer_state = envelope.get("optimizer_state")
    actual_optimizer_manifest = _optimizer_manifest(optimizer_state)
    if actual_optimizer_manifest != envelope.get("optimizer_manifest"):
        raise LaunchDecisionMigrationError("optimizer groups/state differ from the recorded optimizer manifest")
    replay_state = envelope.get("replay_state")
    actual_replay_manifest = _replay_manifest(replay_state)
    if actual_replay_manifest != envelope.get("replay_manifest"):
        raise LaunchDecisionMigrationError("replay identity differs from the recorded replay manifest")
    return contract


def migrate_launch_decision_checkpoint_envelope(
    envelope: Mapping[str, Any],
    *,
    target_contract: LaunchDecisionOwnerContract | Mapping[str, Any],
    migration_id: str,
) -> dict[str, Any]:
    """Perform an explicit mode migration while preserving state artifacts exactly."""

    if not str(migration_id or "").strip():
        raise LaunchDecisionMigrationError("checkpoint mode changes require a non-empty migration_id")
    source = validate_launch_decision_checkpoint_envelope(envelope)
    try:
        target = (
            target_contract
            if isinstance(target_contract, LaunchDecisionOwnerContract)
            else LaunchDecisionOwnerContract.from_dict(target_contract)
        )
    except (TypeError, ValueError) as exc:
        raise LaunchDecisionMigrationError(f"invalid target owner contract: {exc}") from exc
    migrated = deepcopy(dict(envelope))
    migrated["owner_contract"] = target.as_dict()
    migrated["migration"] = {
        "schema_version": "launch_decision_checkpoint_migration_v1",
        "source_mode": source.mode.value,
        "target_mode": target.mode.value,
        "migration_id": str(migration_id),
        "state_artifacts_preserved": True,
    }
    validate_launch_decision_checkpoint_envelope(migrated, expected_contract=target)
    return migrated


def inspect_sb3_launch_decision_checkpoint(model_path: str) -> dict[str, Any]:
    """Read the serialized policy owner mode from an SB3 zip without loading tensors."""

    zip_path = model_path if model_path.endswith(".zip") else f"{model_path}.zip"
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            data = json.loads(zf.read("data").decode("utf-8"))
    except Exception as exc:
        raise LaunchDecisionMigrationError(f"cannot inspect checkpoint data: {exc}") from exc
    policy_kwargs = data.get("policy_kwargs", {})
    if not isinstance(policy_kwargs, Mapping):
        raise LaunchDecisionMigrationError("checkpoint data.policy_kwargs is not a mapping")
    config = {"hyperparameters": {"policy_kwargs": dict(policy_kwargs)}}
    try:
        contract = resolve_launch_decision_contract(config)
    except LaunchDecisionContractError as exc:
        raise LaunchDecisionMigrationError(f"checkpoint owner contract is invalid: {exc}") from exc
    return {
        "schema_version": LAUNCH_DECISION_CHECKPOINT_SCHEMA_VERSION,
        "mode": contract.mode.value,
        "owner_contract": contract.as_dict(),
        "policy_kwargs": dict(policy_kwargs),
    }


def validate_sb3_checkpoint_against_config(
    model_path: str,
    train_config: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail closed when a checkpoint's owner mode differs from a run config."""

    metadata = inspect_sb3_launch_decision_checkpoint(model_path)
    try:
        expected = resolve_launch_decision_contract(train_config)
    except LaunchDecisionContractError as exc:
        raise LaunchDecisionMigrationError(f"training owner contract is invalid: {exc}") from exc
    if metadata["mode"] != expected.mode.value:
        raise LaunchDecisionMigrationError(
            f"checkpoint mode {metadata['mode']!r} differs from training mode {expected.mode.value!r}; "
            "run an explicit checkpoint migration first"
        )
    return metadata


def _historical_policy_class_override(model_path: str):
    zip_path = model_path if model_path.endswith(".zip") else f"{model_path}.zip"
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            data = json.loads(zf.read("data").decode("utf-8"))
            serialized = data.get("policy_class", {})
            if not isinstance(serialized, dict) or ":serialized:" not in serialized:
                return None
            blob = base64.b64decode(serialized[":serialized:"])
    except Exception:
        return None

    if b"HierarchicalMoEExecutionPolicy" in blob:
        from python.rl.policy_algo.policies import HierarchicalMoEExecutionPolicy

        return HierarchicalMoEExecutionPolicy
    if b"SquashedMultiInputPolicy" in blob:
        from python.rl.policy_algo.policies import SquashedMultiInputPolicy

        return SquashedMultiInputPolicy
    return None


def load_sb3_policy(
    model_path: str,
    *,
    algo: str,
    device: str,
    env: Any | None = None,
    expected_config: Mapping[str, Any] | None = None,
):
    """Load a maintained SB3 policy, including historical custom policy classes."""
    load_path = model_path[:-4] if model_path.endswith(".zip") else model_path
    algo_name = str(algo).strip()
    if expected_config is not None:
        validate_sb3_checkpoint_against_config(model_path, expected_config)
    policy_class = _historical_policy_class_override(model_path)
    custom_objects = {"policy_class": policy_class} if policy_class is not None else None
    if algo_name in ("auto", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO

        try:
            return AdaptiveKLPPO.load(load_path, env=env, device=device, custom_objects=custom_objects)
        except Exception:
            if algo_name != "auto":
                raise
    from stable_baselines3 import PPO

    return PPO.load(load_path, env=env, device=device, custom_objects=custom_objects)


__all__ = [
    "LAUNCH_DECISION_CHECKPOINT_SCHEMA_VERSION",
    "LaunchDecisionMigrationError",
    "build_launch_decision_checkpoint_envelope",
    "inspect_sb3_launch_decision_checkpoint",
    "load_sb3_policy",
    "migrate_launch_decision_checkpoint_envelope",
    "validate_launch_decision_checkpoint_envelope",
    "validate_sb3_checkpoint_against_config",
]
