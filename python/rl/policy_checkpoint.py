"""Stable-Baselines policy checkpoint loading without runtime bootstrap side effects.

Callers own repository/runtime import configuration. Production entry points can
therefore keep the installed-wheel fallback provided by ``configure_repo_imports``,
while diagnostics tools may still fail closed with ``ensure_repo_imports`` before
importing this module.
"""

from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import zipfile
from typing import Any, Mapping

from python.rl.policy_algo.model_contracts import (
    LaunchDecisionContractError,
    LaunchDecisionOwnerContract,
    resolve_launch_decision_contract,
)


LAUNCH_DECISION_CHECKPOINT_SCHEMA_VERSION = "launch_decision_checkpoint_v1"
LAUNCH_DECISION_SIDECAR_SCHEMA_VERSION = "launch_decision_checkpoint_sidecar_v1"


class LaunchDecisionMigrationError(ValueError):
    """Raised when checkpoint/optimizer/replay state cannot be reconciled."""


def _canonical_fingerprint(value: Any) -> str:
    def normalize(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {
                str(key): normalize(value)
                for key, value in sorted(item.items(), key=lambda pair: str(pair[0]))
            }
        if isinstance(item, (list, tuple)):
            return [normalize(value) for value in item]
        if hasattr(item, "detach") and hasattr(item, "cpu") and hasattr(item, "numpy"):
            array = item.detach().cpu().contiguous().numpy()
            return {
                "shape": [int(value) for value in array.shape],
                "dtype": str(array.dtype),
                "sha256": hashlib.sha256(array.tobytes()).hexdigest(),
            }
        if hasattr(item, "shape") and hasattr(item, "tobytes"):
            array = item
            return {
                "shape": [int(value) for value in array.shape],
                "dtype": str(getattr(array, "dtype", type(array).__name__)),
                "sha256": hashlib.sha256(array.tobytes()).hexdigest(),
            }
        return item

    payload = json.dumps(normalize(value), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _sidecar_path(model_path: str) -> Path:
    return Path(model_path if model_path.endswith(".zip") else f"{model_path}.zip").with_suffix(
        ".launch_decision.json"
    )


def _manifest_only(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": LAUNCH_DECISION_SIDECAR_SCHEMA_VERSION,
        "checkpoint_schema_version": envelope.get("schema_version"),
        "owner_contract": envelope.get("owner_contract"),
        "source_config_fingerprint": envelope.get("source_config_fingerprint"),
        "state_dict_manifest": envelope.get("state_dict_manifest"),
        "optimizer_manifest": envelope.get("optimizer_manifest"),
        "replay_manifest": envelope.get("replay_manifest"),
        "migration": envelope.get("migration"),
    }


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


def _value_manifest(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _value_manifest(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_value_manifest(item) for item in value]
    return _tensor_manifest(value)


def _value_shape(value: Any) -> list[int] | None:
    shape = getattr(value, "shape", None)
    if shape is not None:
        try:
            return [int(item) for item in shape]
        except Exception:
            return None
    if isinstance(value, (list, tuple)):
        if not value:
            return [0]
        nested = _value_shape(value[0])
        return [len(value), *(nested or [])]
    return None


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
    normalized_groups: list[dict[str, Any]] = []
    for index, group in enumerate(groups):
        if not isinstance(group, Mapping):
            raise LaunchDecisionMigrationError("optimizer_state.param_groups contains a non-mapping group")
        params = group.get("params", ())
        if not isinstance(params, (list, tuple)):
            raise LaunchDecisionMigrationError("optimizer parameter ids must be a list")
        roles = group.get("parameter_roles", ())
        if not isinstance(roles, (list, tuple)):
            raise LaunchDecisionMigrationError("optimizer parameter roles must be a list")
        normalized_groups.append(
            {
                "name": str(group.get("name", f"group_{index}")),
                "parameter_ids": [str(item) for item in params],
                "parameter_roles": [str(item) for item in roles],
                "parameter_names": [str(item) for item in group.get("parameter_names", ())],
            }
        )
    if len(normalized_groups) != len(groups):
        raise LaunchDecisionMigrationError("optimizer_state.param_groups contains a non-mapping group")
    state = optimizer_state.get("state", {}) or {}
    if not isinstance(state, Mapping):
        raise LaunchDecisionMigrationError("optimizer_state.state must be a mapping")
    return {
        "groups": normalized_groups,
        "group_names": [group["name"] for group in normalized_groups],
        "group_count": len(normalized_groups),
        "state_keys": sorted(str(key) for key in state),
        "state_shapes": {
            str(key): _value_manifest(value)
            for key, value in sorted(state.items(), key=lambda item: str(item[0]))
        },
        "parameter_roles": sorted(
            {
                role
                for group in normalized_groups
                for role in group["parameter_roles"]
            }
        ),
    }


def _optimizer_state_for_manifest(optimizer: Any, policy: Any) -> Mapping[str, Any]:
    """Add stable parameter names/roles to an optimizer state snapshot."""

    state = deepcopy(optimizer.state_dict())
    groups = state.get("param_groups")
    live_groups = getattr(optimizer, "param_groups", None)
    if not isinstance(groups, list) or not isinstance(live_groups, (list, tuple)):
        return state
    named_parameters = {
        id(parameter): str(name) for name, parameter in policy.named_parameters()
    } if hasattr(policy, "named_parameters") else {}
    role_ids = {}
    role_getter = getattr(policy, "_launch_decision_parameter_ids", None)
    if callable(role_getter):
        for role, parameter_ids in role_getter().items():
            for parameter_id in parameter_ids:
                role_ids.setdefault(int(parameter_id), []).append(str(role))
    if len(groups) != len(live_groups):
        return state
    for index, group in enumerate(groups):
        live_parameters = list(live_groups[index].get("params", ()))
        group["parameter_names"] = [
            named_parameters.get(id(parameter), f"parameter_{position}")
            for position, parameter in enumerate(live_parameters)
        ]
        group["parameter_roles"] = sorted(
            {
                role
                for parameter in live_parameters
                for role in role_ids.get(id(parameter), ())
            }
        )
        group.setdefault("name", f"group_{index}")
    return state


def _replay_manifest(replay_state: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(replay_state, Mapping):
        raise LaunchDecisionMigrationError("replay_state must be a mapping")
    required = ("schema_version", "storage", "capacity")
    missing = [key for key in required if key not in replay_state]
    if missing:
        raise LaunchDecisionMigrationError(
            "replay_state is missing identity fields: " + ", ".join(missing)
        )
    row_fields = {
        str(key): replay_state[key]
        for key in sorted(replay_state)
        if str(key).endswith("rows") or str(key) in {"rows", "data"}
    }
    return {
        "schema_version": str(replay_state["schema_version"]),
        "storage": str(replay_state["storage"]),
        "capacity": int(replay_state["capacity"]),
        "keys": sorted(str(key) for key in replay_state.keys()),
        "row_shapes": {
            key: _value_shape(value)
            for key, value in row_fields.items()
        },
        "rows_fingerprint": _canonical_fingerprint(row_fields),
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
        if contract.as_dict() != expected.as_dict():
            raise LaunchDecisionMigrationError(
                "checkpoint owner contract does not match the expected contract; "
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
    """Re-emit an unchanged envelope; mode-changing conversion is fail-closed."""

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
    if source.as_dict() != target.as_dict():
        raise LaunchDecisionMigrationError(
            f"no maintained checkpoint conversion exists for "
            f"{source.mode.value!r} -> {target.mode.value!r}; "
            f"migration_id={migration_id!r} was recorded but no state conversion was performed"
        )
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


def _contract_from_training_config(train_config: Mapping[str, Any]) -> LaunchDecisionOwnerContract:
    try:
        return resolve_launch_decision_contract(train_config)
    except LaunchDecisionContractError as exc:
        raise LaunchDecisionMigrationError(f"training owner contract is invalid: {exc}") from exc


def launch_decision_config_fingerprint(train_config: Mapping[str, Any]) -> str:
    """Return the stable identity recorded beside an SB3 checkpoint."""

    return _canonical_fingerprint(train_config)


def _replay_state_for_model(model: Any) -> dict[str, Any]:
    replay_buffer = getattr(model, "replay_buffer", None)
    if replay_buffer is None:
        return {
            "schema_version": "sb3_no_replay_v1",
            "storage": "none",
            "capacity": 0,
            "rows": [],
        }
    rows = getattr(replay_buffer, "observations", None)
    return {
        "schema_version": "sb3_replay_buffer_v1",
        "storage": type(replay_buffer).__name__,
        "capacity": int(getattr(replay_buffer, "buffer_size", 0)),
        "rows": [] if rows is None else rows,
    }


def write_sb3_launch_decision_sidecar(
    model_path: str,
    *,
    model: Any,
    owner_contract: LaunchDecisionOwnerContract | Mapping[str, Any],
    source_config_fingerprint: str | None = None,
) -> str:
    """Persist the compatibility envelope that SB3's zip does not contain."""

    policy = getattr(model, "policy", None)
    if policy is None or not hasattr(policy, "state_dict"):
        raise LaunchDecisionMigrationError("cannot write launch-decision sidecar without a policy state_dict")
    optimizer = getattr(policy, "optimizer", None)
    if optimizer is None or not hasattr(optimizer, "state_dict"):
        raise LaunchDecisionMigrationError("cannot write launch-decision sidecar without optimizer state")
    envelope = build_launch_decision_checkpoint_envelope(
        state_dict=policy.state_dict(),
        optimizer_state=_optimizer_state_for_manifest(optimizer, policy),
        replay_state=_replay_state_for_model(model),
        owner_contract=owner_contract,
        source_config_fingerprint=source_config_fingerprint,
    )
    sidecar = _manifest_only(envelope)
    destination = _sidecar_path(model_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(destination)


def _read_sb3_launch_decision_sidecar(model_path: str) -> dict[str, Any]:
    path = _sidecar_path(model_path)
    if not path.exists():
        raise LaunchDecisionMigrationError(
            f"missing launch-decision checkpoint sidecar: {path}; "
            "save a maintained compatibility envelope or run a named migration"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise LaunchDecisionMigrationError(f"invalid launch-decision checkpoint sidecar: {path}") from exc
    if payload.get("schema_version") != LAUNCH_DECISION_SIDECAR_SCHEMA_VERSION:
        raise LaunchDecisionMigrationError(
            f"unsupported launch-decision sidecar schema: {payload.get('schema_version')!r}"
        )
    return payload


def validate_loaded_sb3_launch_decision_checkpoint(
    model_path: str,
    *,
    model: Any,
    expected_config: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare loaded policy/optimizer/replay identities with its sidecar."""

    metadata = validate_sb3_checkpoint_against_config(model_path, expected_config)
    sidecar = _read_sb3_launch_decision_sidecar(model_path)
    policy = getattr(model, "policy", None)
    optimizer = getattr(policy, "optimizer", None) if policy is not None else None
    if policy is None or optimizer is None:
        raise LaunchDecisionMigrationError("loaded checkpoint has no policy/optimizer compatibility surface")
    actual = {
        "state_dict_manifest": _state_dict_manifest(policy.state_dict()),
        "optimizer_manifest": _optimizer_manifest(
            _optimizer_state_for_manifest(optimizer, policy)
        ),
        "replay_manifest": _replay_manifest(_replay_state_for_model(model)),
    }
    for key, value in actual.items():
        if sidecar.get(key) != value:
            raise LaunchDecisionMigrationError(
                f"loaded checkpoint {key} differs from its sidecar; "
                "restore the exact artifact or run a named migration"
            )
    return metadata


def validate_sb3_checkpoint_against_config(
    model_path: str,
    train_config: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail closed when a checkpoint's owner mode differs from a run config."""

    metadata = inspect_sb3_launch_decision_checkpoint(model_path)
    expected = _contract_from_training_config(train_config)
    sidecar = _read_sb3_launch_decision_sidecar(model_path)
    try:
        sidecar_contract = LaunchDecisionOwnerContract.from_dict(sidecar["owner_contract"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LaunchDecisionMigrationError("sidecar owner contract is invalid") from exc
    if sidecar_contract.as_dict() != expected.as_dict() or metadata["owner_contract"] != expected.as_dict():
        raise LaunchDecisionMigrationError(
            f"checkpoint owner contract {metadata['mode']!r} differs from training contract "
            "run an explicit checkpoint migration first"
        )
    expected_fingerprint = launch_decision_config_fingerprint(train_config)
    if sidecar.get("source_config_fingerprint") not in (None, expected_fingerprint):
        raise LaunchDecisionMigrationError(
            "checkpoint sidecar source configuration differs from the requested training configuration; "
            "run an explicit configuration migration first"
        )
    if metadata["owner_contract"] != sidecar_contract.as_dict():
        raise LaunchDecisionMigrationError("SB3 checkpoint and sidecar owner contracts differ")
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
    "LAUNCH_DECISION_SIDECAR_SCHEMA_VERSION",
    "LaunchDecisionMigrationError",
    "build_launch_decision_checkpoint_envelope",
    "inspect_sb3_launch_decision_checkpoint",
    "load_sb3_policy",
    "launch_decision_config_fingerprint",
    "migrate_launch_decision_checkpoint_envelope",
    "validate_launch_decision_checkpoint_envelope",
    "validate_sb3_checkpoint_against_config",
    "validate_loaded_sb3_launch_decision_checkpoint",
    "write_sb3_launch_decision_sidecar",
]
