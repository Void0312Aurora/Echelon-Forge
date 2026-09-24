"""Generate deterministic launch-decision compatibility fixtures.

The manifest is tracked in the repository, while tensor/checkpoint/replay
artifacts are kept outside a checkout.  The generator is intentionally small:
it captures the owner-contract boundary and optimizer/replay envelope without
requiring a full training run or a mutable simulator state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import torch

# Allow direct execution from any current directory before importing the
# repository-owned contract module.
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def _active_hybrid_configs(repo_root: Path) -> list[dict[str, Any]]:
    root = repo_root / "examples" / "config" / "training" / "active" / "air_combat"
    records: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        policy_kwargs = payload.get("hyperparameters", {}).get("policy_kwargs", {})
        if policy_kwargs.get("hybrid_action_spec") != "air_combat_hybrid_v1":
            continue
        contract = resolve_launch_decision_contract(payload)
        records.append(
            {
                "path": path.relative_to(repo_root).as_posix(),
                "sha256": _sha256(path),
                "mode": contract.mode.value,
                "explicit_mode": bool(contract.explicit_mode),
                "event_head_enabled": float(policy_kwargs.get("hybrid_event_head_lr_scale", 0.0) or 0.0)
                > 0.0,
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


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise RuntimeError(f"refusing to overwrite different fixture: {path}")
        return
    path.write_bytes(payload)


def _torch_bytes(payload: Any) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    torch.save(payload, buffer, _use_new_zipfile_serialization=False)
    raw = buffer.getvalue()
    # Legacy torch serialization embeds process-specific decimal storage IDs.
    # Replace those IDs with stable ordinal tokens so the fixture hash is
    # reproducible across Python processes while remaining torch-loadable.
    storage_ids = re.findall(rb"X\x0d\x00\x00\x00([0-9]{13})", raw)
    unique_ids = sorted(set(storage_ids))
    for ordinal, storage_id in enumerate(unique_ids, start=1):
        raw = raw.replace(storage_id, f"{ordinal:013d}".encode("ascii"))
    return raw


def _make_profile_artifacts(root: Path, mode: LaunchDecisionMode) -> dict[str, Any]:
    profile_root = root / mode.value
    seed = 7000 + list(LaunchDecisionMode).index(mode)
    state_dict = {
        # Keep one tensor storage so legacy torch serialization is stable across
        # processes; semantic parameter roles remain recorded in the contract.
        "event_parameter_snapshot": torch.tensor(
            [[-0.25, 0.35], [0.01, -0.02], [0.0, 0.5]],
            dtype=torch.float32,
        ),
        "owner_contract": resolve_launch_decision_contract(_fixture_config(mode)).as_dict(),
    }
    optimizer_state = {
        "state": {},
        "param_groups": [
            {
                "name": role,
                "lr": 3.0e-5,
                "lr_scale": 1.0,
                "parameter_roles": [role],
            }
            for role in resolve_launch_decision_contract(_fixture_config(mode)).trainable_parameter_roles
        ],
    }
    observations = torch.arange(24, dtype=torch.float32).reshape(3, 8) / 10.0
    replay_rows = [
        {
            "seed": int(seed_value),
            "episode": int(episode),
            "mode": mode.value,
            "launch_window_open": bool((seed_value + episode) % 2),
            "fire_once_accepted": bool(episode == 2),
        }
        for seed_value in SEEDS
        for episode in range(EPISODES_PER_SEED)
    ]

    files = {
        "state_dict": f"{mode.value}/policy_state.pt",
        "optimizer_state": f"{mode.value}/optimizer_state.pt",
        "observations": f"{mode.value}/observations.pt",
        "replay": f"{mode.value}/replay.jsonl",
    }
    _write_bytes(root / files["state_dict"], _torch_bytes(state_dict))
    _write_bytes(root / files["optimizer_state"], _torch_bytes(optimizer_state))
    _write_bytes(root / files["observations"], _torch_bytes(observations))
    replay_bytes = (
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in replay_rows)
    ).encode("utf-8")
    _write_bytes(root / files["replay"], replay_bytes)
    return {
        "seed": seed,
        "files": files,
        "sha256": {key: _sha256(root / relative) for key, relative in files.items()},
        "state_dict_keys": sorted(state_dict),
        "optimizer_parameter_roles": [
            role
            for role in resolve_launch_decision_contract(_fixture_config(mode)).trainable_parameter_roles
        ],
        "replay_rows": len(replay_rows),
        "observation_shape": list(observations.shape),
        "dtype": "float32",
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
        "fixture_root": str(output_root),
        "active_hybrid_configs": _active_hybrid_configs(repo_root),
        "profiles": profile_records,
    }


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
        if existing != manifest:
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
