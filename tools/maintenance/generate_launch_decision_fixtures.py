"""Generate deterministic launch-decision compatibility fixtures.

The tracked manifest contains only semantic, host-independent identity. Binary
fixtures live outside the checkout and are addressed by paths relative to the
selected external root. Policy and optimizer fixtures are real loadable PyTorch
state dictionaries produced by a fixed tiny module whose named submodules map
to the launch-decision parameter roles; they are not hand-built state envelopes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

import torch
from torch import nn

_SCRIPT_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_SCRIPT_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_REPO_ROOT))

from python.rl.policy_algo.model_contracts import (
    LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
    LAUNCH_DECISION_CONTRACT_VERSION_KEY,
    LaunchDecisionMode,
    resolve_launch_decision_contract,
)


SCHEMA_VERSION = "launch_decision_fixture_v1"
DEFAULT_ROOT = Path(r"D:\workshop\Research\Echelon-Forge-fixtures\launch_decision_reorg\v1")
MANIFEST_PATH = Path("tests/fixtures/launch_decision_reorg/v1/manifest.json")
SEEDS = (0, 1, 2)
EPISODES_PER_SEED = 3
STRICT_COUNTER_KEYS = (
    "fire_once_requested_count",
    "fire_once_accepted_count",
    "fire_once_rejected_count",
    "release_count",
    "authorized_release_count",
    "violation_release_count",
    "repeat_release_before_assessment_count",
    "first_release_step",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _source_revision(repo_root: Path, requested: str | None) -> str:
    if requested:
        return requested
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _hybrid_action_name(spec: Any) -> str | None:
    if isinstance(spec, str):
        return spec.strip()
    if isinstance(spec, dict):
        return str(spec.get("name", spec.get("mode", ""))).strip()
    return None


def _active_hybrid_configs(repo_root: Path, source_revision: str) -> list[dict[str, Any]]:
    root = repo_root / "examples" / "config" / "training" / "active" / "air_combat"
    records: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        policy_kwargs = payload.get("hyperparameters", {}).get("policy_kwargs", {})
        if _hybrid_action_name(policy_kwargs.get("hybrid_action_spec")) != "air_combat_hybrid_v1":
            continue
        contract = resolve_launch_decision_contract(
            payload,
            require_legacy_provenance=False,
        )
        sha256 = _sha256_bytes(raw)
        relative_path = path.relative_to(repo_root).as_posix()
        records.append(
            {
                "path": relative_path,
                "sha256": sha256,
                "source_revision": source_revision,
                "mode": contract.mode.value,
                "explicit_mode": bool(contract.explicit_mode),
                "event_head_enabled": float(policy_kwargs.get("hybrid_event_head_lr_scale", 0.0) or 0.0)
                > 0.0,
                "acceptance_eligible": bool(contract.acceptance_eligible),
                "legacy_provenance_eligible": bool(
                    contract.mode == LaunchDecisionMode.LEGACY_COMPOSED_V0
                    and not contract.explicit_mode
                ),
            }
        )
    return records


def _fixture_config(mode: LaunchDecisionMode) -> dict[str, Any]:
    policy_kwargs: dict[str, Any] = {
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "hmoe_residual_scale": 0.18,
        "hybrid_event_head_lr_scale": 10.0,
        LAUNCH_DECISION_CONTRACT_VERSION_KEY: LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
        "launch_decision_mode": mode.value,
        "hybrid_event_use_window_classifier_head": False,
        "hybrid_event_use_stopping_head": False,
    }
    if mode == LaunchDecisionMode.AUXILIARY_ONLY_V1:
        policy_kwargs["hybrid_event_head_lr_scale"] = 0.0
    return {"hyperparameters": {"policy_kwargs": policy_kwargs}}


class _LaunchDecisionFixturePolicy(nn.Module):
    """Small loadable policy-state carrier with production role names."""

    def __init__(self, *, event_head_enabled: bool = True) -> None:
        super().__init__()
        self.policy_trunk = nn.Sequential(nn.Linear(8, 12), nn.Tanh())
        self.action_net = nn.Linear(12, 2)
        self.hmoe_event_slice = nn.Linear(12, 2, bias=False)
        self.hybrid_event_head = nn.Linear(12, 2) if event_head_enabled else None

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        latent = self.policy_trunk(observations)
        logits = self.action_net(latent) + self.hmoe_event_slice(latent)
        if self.hybrid_event_head is not None:
            logits = logits + self.hybrid_event_head(latent)
        return logits


def _role_parameters(policy: _LaunchDecisionFixturePolicy, role: str) -> list[nn.Parameter]:
    module = getattr(policy, role, None)
    if isinstance(module, nn.Module):
        return list(module.parameters())
    return []


def _make_fixture_policy_and_optimizer(
    mode: LaunchDecisionMode,
    *,
    seed: int,
) -> tuple[_LaunchDecisionFixturePolicy, torch.optim.Optimizer, dict[str, Any]]:
    torch.manual_seed(int(seed))
    contract = resolve_launch_decision_contract(
        _fixture_config(mode),
        require_legacy_provenance=False,
    )
    policy = _LaunchDecisionFixturePolicy(event_head_enabled=True)
    groups: list[dict[str, Any]] = []
    for role in contract.trainable_parameter_roles:
        params = _role_parameters(policy, role)
        if not params:
            continue
        groups.append(
            {
                "params": params,
                "name": role,
                "lr_scale": 1.0,
                "parameter_role": role,
            }
        )
    if not groups:
        groups.append(
            {
                "params": list(policy.parameters()),
                "name": "fixture_fallback",
                "lr_scale": 1.0,
                "parameter_role": "fixture_fallback",
            }
        )
    optimizer = torch.optim.Adam(groups, lr=3.0e-5)

    # Populate genuine Adam state deterministically without requiring a training
    # rollout. Zero gradients create optimizer slots while leaving parameters
    # unchanged with the default zero weight decay.
    for group in optimizer.param_groups:
        for parameter in group["params"]:
            parameter.grad = torch.zeros_like(parameter)
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)

    metadata = {
        "owner_contract": contract.as_dict(),
        "optimizer_group_names": [str(group.get("name", "")) for group in optimizer.param_groups],
        "optimizer_parameter_roles": [
            str(group.get("parameter_role", "")) for group in optimizer.param_groups
        ],
    }
    return policy, optimizer, metadata


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise RuntimeError(f"refusing to overwrite different fixture: {path}")
        return
    path.write_bytes(payload)


def _torch_bytes(payload: Any) -> bytes:
    # The zip serializer is deterministic for the fixed tensor/container graph
    # used here and avoids process-specific legacy storage identifiers.
    buffer = BytesIO()
    torch.save(payload, buffer)
    return buffer.getvalue()


def _load_profile_artifacts(
    root: Path,
    mode: LaunchDecisionMode,
    record: dict[str, Any],
) -> None:
    seed = int(record["seed"])
    policy, optimizer, _metadata = _make_fixture_policy_and_optimizer(mode, seed=seed)
    files = record["files"]
    state_dict = torch.load(root / files["state_dict"], map_location="cpu", weights_only=True)
    optimizer_state = torch.load(
        root / files["optimizer_state"],
        map_location="cpu",
        weights_only=True,
    )
    policy.load_state_dict(state_dict, strict=True)
    optimizer.load_state_dict(optimizer_state)
    if sorted(state_dict) != list(record["state_dict_keys"]):
        raise RuntimeError(f"state-dict key drift for {mode.value}")
    if [str(group.get("name", "")) for group in optimizer.param_groups] != list(
        record["optimizer_group_names"]
    ):
        raise RuntimeError(f"optimizer group-name drift for {mode.value}")


def _make_profile_artifacts(root: Path, mode: LaunchDecisionMode) -> dict[str, Any]:
    seed = 7000 + list(LaunchDecisionMode).index(mode)
    policy, optimizer, metadata = _make_fixture_policy_and_optimizer(mode, seed=seed)
    observations = torch.arange(24, dtype=torch.float32).reshape(3, 8) / 10.0

    state_dict = policy.state_dict()
    optimizer_state = optimizer.state_dict()
    files = {
        "state_dict": f"{mode.value}/policy_state.pt",
        "optimizer_state": f"{mode.value}/optimizer_state.pt",
        "observations": f"{mode.value}/observations.pt",
    }
    _write_bytes(root / files["state_dict"], _torch_bytes(state_dict))
    _write_bytes(root / files["optimizer_state"], _torch_bytes(optimizer_state))
    _write_bytes(root / files["observations"], _torch_bytes(observations))

    record = {
        "seed": seed,
        "files": files,
        "sha256": {key: _sha256(root / relative) for key, relative in files.items()},
        "state_dict_keys": sorted(state_dict),
        "optimizer_group_names": metadata["optimizer_group_names"],
        "optimizer_parameter_roles": metadata["optimizer_parameter_roles"],
        "optimizer_state_entry_count": len(optimizer_state.get("state", {})),
        "owner_contract": metadata["owner_contract"],
        "replay_state": "not_applicable_no_window_classifier_adapter",
        "observation_shape": list(observations.shape),
        "dtype": "float32",
    }
    _load_profile_artifacts(root, mode, record)
    return record


def _strict_acceptance_identity() -> dict[str, Any]:
    cells = [
        {"seed": int(seed), "episode": int(episode)}
        for seed in SEEDS
        for episode in range(EPISODES_PER_SEED)
    ]
    return {
        "version": "strict_learned_firing_v1",
        "probe_mode": "model",
        "forced_or_manual_fire_injection": False,
        "lanes": ["deterministic", "stochastic"],
        "coverage": {
            "seeds": list(SEEDS),
            "episodes_per_seed": EPISODES_PER_SEED,
            "required_cells_per_lane": len(cells),
            "cells": cells,
        },
        "counter_keys": list(STRICT_COUNTER_KEYS),
        "per_cell_thresholds": {
            "fire_once_requested_count": {"min": 1},
            "fire_once_accepted_count": {"min": 1},
            "fire_once_rejected_count": {"eq": 0},
            "release_count": {"min": 1},
            "authorized_release_count": {"min": 1},
            "violation_release_count": {"eq": 0},
            "repeat_release_before_assessment_count": {"eq": 0},
            "first_release_step": {"required": True},
        },
        "stochastic_rejection_bound_total": 0,
        "aggregate_success_can_replace_cell_failure": False,
    }


def build_manifest(repo_root: Path, output_root: Path, source_revision: str) -> dict[str, Any]:
    generator_path = Path(__file__).resolve()
    profiles = [
        LaunchDecisionMode.LEGACY_COMPOSED_V0,
        LaunchDecisionMode.DIRECT_BOUNDARY_V1_STRICT,
        LaunchDecisionMode.GOVERNED_COMPOSED_V1,
    ]
    profile_records = {
        mode.value: _make_profile_artifacts(output_root, mode)
        for mode in profiles
    }
    active_configs = _active_hybrid_configs(repo_root, source_revision)
    legacy_allowlist = [
        {
            "source_revision": item["source_revision"],
            "path": item["path"],
            "sha256": item["sha256"],
        }
        for item in active_configs
        if item["legacy_provenance_eligible"]
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "source_revision": source_revision,
        "generator": generator_path.relative_to(repo_root).as_posix(),
        "generator_sha256": _sha256(generator_path),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "device": "cpu",
        "dtype": "float32",
        "seeds": list(SEEDS),
        "episodes_per_seed": EPISODES_PER_SEED,
        "artifact_paths": "external_root_relative_v1",
        "active_hybrid_configs": active_configs,
        "legacy_provenance_allowlist": legacy_allowlist,
        "strict_acceptance_identity": _strict_acceptance_identity(),
        "profiles": profile_records,
    }


def semantic_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return the immutable identity; output-root location is intentionally absent."""

    return json.loads(json.dumps(manifest, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_repo_root())
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--source-revision", default=None)
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_root = (
        args.output_root
        or Path(os.environ.get("EF_LAUNCH_DECISION_FIXTURE_ROOT", str(DEFAULT_ROOT)))
    ).resolve()
    manifest_path = (args.manifest or (repo_root / MANIFEST_PATH)).resolve()
    source_revision = _source_revision(repo_root, args.source_revision)
    manifest = build_manifest(repo_root, output_root, source_revision)

    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if semantic_manifest(existing) != semantic_manifest(manifest):
            raise RuntimeError(
                f"refusing to overwrite a different fixture manifest: {manifest_path}"
            )
        print(json.dumps(existing, indent=2, sort_keys=True))
        return 0

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
