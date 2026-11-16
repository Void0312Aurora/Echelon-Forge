"""Single-surface RuntimeFacade packet export for learner sidecars.

This is a narrow consumer boundary over the existing trace projection and
numeric EpisodeStore adapter. It admits one Air execution surface, one Agent,
one fixed seed/split, and explicitly selected branch digests. It never creates
RunReceipt, input-lock semantics, or production admission evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from python.experiment.contracts import ContractError, canonical_bytes, content_digest
from python.experiment.numeric_observation_adapter import (
    AgentObservationSeries,
    ActionEncoder,
    NumericExportReceipt,
    RewardEncoder,
    build_numeric_exports,
    write_episode_store,
)
from python.experiment.trace_projection import TraceProjection


AIR_RUNTIME_FACADE_SURFACE = "air.execution.runtime_facade.v1"
RUNTIME_FACADE_TRAINING_EXPORT_SCHEMA = "echelon_forge.runtime_facade_training_export.v1"
_RUNTIME_EXPORT_SIDECAR = "runtime_facade_training_export.json"
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_ALLOWED_EVIDENCE = frozenset({"runtime_candidate"})
_ALLOWED_SPLIT = "training"


@dataclass(frozen=True)
class RuntimeFacadeTrainingExportReceipt:
    root_dir: str
    metadata_path: str
    metadata_digest: str
    episode_paths: tuple[str, ...]
    surface_id: str
    projection_digest: str
    agent_id: str
    seed: int
    split: str
    branch_digests: tuple[str, ...]


def _digest(value: object, name: str) -> None:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ContractError(f"{name} must be a lowercase SHA-256 digest")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"runtime facade export sidecar is unreadable: {path}") from exc
    if not isinstance(value, dict):
        raise ContractError("runtime facade export sidecar must contain an object")
    return value


def _canonical_load(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"runtime facade export sidecar is unreadable: {path}") from exc
    if not isinstance(value, dict) or raw != canonical_bytes(value) + b"\n":
        raise ContractError("runtime facade export sidecar is not canonical")
    return value


def _validate_request(
    projection: TraceProjection,
    observation_sources: Mapping[tuple[str, str], AgentObservationSeries],
    *,
    agent_id: str,
    selected_branch_digests: Sequence[str],
    seed: int,
    split: str,
    surface_id: str,
) -> tuple[str, ...]:
    if not isinstance(projection, TraceProjection):
        raise ContractError("projection must be a TraceProjection")
    if surface_id != AIR_RUNTIME_FACADE_SURFACE:
        raise ContractError("surface is not the admitted Air RuntimeFacade surface")
    if not isinstance(agent_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_]*", agent_id):
        raise ContractError("agent_id must match [a-z0-9][a-z0-9_]*")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ContractError("seed must be a non-negative integer")
    if split != _ALLOWED_SPLIT:
        raise ContractError("training sidecar split must be training")
    selected = tuple(selected_branch_digests)
    if not selected or len(set(selected)) != len(selected):
        raise ContractError("selected branch digests must be non-empty and unique")
    if any(_DIGEST.fullmatch(value) is None for value in selected):
        raise ContractError("selected branch digests must be lowercase SHA-256 digests")
    rows = tuple(row for row in projection.rows if row.branch_digest in set(selected))
    if not rows:
        raise ContractError("selected branch digests identify no projected rows")
    if any(row.seed != seed for row in rows):
        raise ContractError("selected branch rows do not match fixed seed")
    if any(row.split != split for row in rows):
        raise ContractError("selected branch rows do not match fixed split")
    if any(row.evidence_label not in _ALLOWED_EVIDENCE for row in rows):
        raise ContractError("projection is not admitted Air RuntimeFacade evidence")
    if any(
        tuple(agent for agent, _ in row.actions) != (agent_id,)
        or tuple(agent for agent, _ in row.rewards) != (agent_id,)
        for row in rows
    ):
        raise ContractError("projection contains another Agent or mixed action authority")
    for branch_digest in selected:
        branch_rows = [row for row in rows if row.branch_digest == branch_digest]
        if not branch_rows:
            raise ContractError("selected branch digest is not represented")
        if any(row.branch_depth > 0 and not row.parent_branch_digest for row in branch_rows):
            raise ContractError("selected branch has incomplete ancestry")
    supplied = set(observation_sources)
    expected = {(row.manifest_digest, row.branch_digest) for row in rows}
    if supplied != expected:
        raise ContractError("observation source branches do not match selected projection branches")
    for key, source in observation_sources.items():
        if not isinstance(source, AgentObservationSeries):
            raise ContractError("observation sources must contain AgentObservationSeries")
        if source.agent_id != agent_id:
            raise ContractError("observation source Agent does not match export Agent")
        if any(packet.provenance != "facade_observation_packet" for packet in source.packets):
            raise ContractError("observation source lacks facade observation provenance")
    return tuple(sorted(selected))


def export_runtime_facade_training_sidecar(
    projection: TraceProjection,
    observation_sources: Mapping[tuple[str, str], AgentObservationSeries],
    *,
    agent_id: str,
    selected_branch_digests: Sequence[str],
    seed: int,
    split: str,
    action_encoder: ActionEncoder,
    reward_encoder: RewardEncoder,
    root_dir: str,
    surface_id: str = AIR_RUNTIME_FACADE_SURFACE,
) -> RuntimeFacadeTrainingExportReceipt:
    """Persist one admitted Air RuntimeFacade packet projection for training."""

    selected = _validate_request(
        projection,
        observation_sources,
        agent_id=agent_id,
        selected_branch_digests=selected_branch_digests,
        seed=seed,
        split=split,
        surface_id=surface_id,
    )
    exports = build_numeric_exports(
        projection,
        observation_sources,
        agent_id=agent_id,
        selected_branch_digests=selected,
        action_encoder=action_encoder,
        reward_encoder=reward_encoder,
    )
    if any(item.observation_provenance != "facade_observation_packet" for item in exports):
        raise ContractError("numeric export lacks facade observation provenance")
    if any(item.seed != seed or item.split != split for item in exports):
        raise ContractError("numeric export crossed fixed seed or split")
    numeric_receipt: NumericExportReceipt = write_episode_store(exports, root_dir)
    numeric_sidecar = _load_json(Path(numeric_receipt.metadata_path))
    numeric_metadata_digest = numeric_sidecar.get("metadata_digest")
    _digest(numeric_metadata_digest, "numeric metadata_digest")
    numeric_without_digest = dict(numeric_sidecar)
    numeric_without_digest.pop("metadata_digest", None)
    if content_digest("experiment.numeric-export", numeric_without_digest) != numeric_metadata_digest:
        raise ContractError("numeric export metadata digest does not match")
    episodes = tuple(numeric_sidecar.get("episodes", ()))
    if not episodes:
        raise ContractError("numeric export sidecar contains no episodes")
    branch_ancestry = []
    for branch_digest in selected:
        branch_rows = [row for row in projection.rows if row.branch_digest == branch_digest]
        branch_ancestry.append(
            {
                "branch_digest": branch_digest,
                "parent_branch_digest": branch_rows[0].parent_branch_digest,
                "branch_depth": branch_rows[0].branch_depth,
                "branch_label": branch_rows[0].branch_label,
            }
        )
    payload: dict[str, Any] = {
        "schema_version": RUNTIME_FACADE_TRAINING_EXPORT_SCHEMA,
        "surface_id": surface_id,
        "agent_id": agent_id,
        "seed": seed,
        "split": split,
        "projection_digest": projection.digest,
        "manifest_digests": sorted({row.manifest_digest for row in projection.rows if row.branch_digest in selected}),
        "branch_digests": list(selected),
        "branch_ancestry": branch_ancestry,
        "packet_provenance": "facade_observation_packet",
        "numeric_metadata_digest": numeric_metadata_digest,
        "episodes": list(episodes),
    }
    metadata_digest = content_digest("experiment.runtime-facade-training-export", payload)
    payload["metadata_digest"] = metadata_digest
    metadata_path = Path(numeric_receipt.root_dir) / _RUNTIME_EXPORT_SIDECAR
    metadata_path.write_bytes(canonical_bytes(payload) + b"\n")
    return RuntimeFacadeTrainingExportReceipt(
        root_dir=numeric_receipt.root_dir,
        metadata_path=str(metadata_path),
        metadata_digest=metadata_digest,
        episode_paths=numeric_receipt.episode_paths,
        surface_id=surface_id,
        projection_digest=projection.digest,
        agent_id=agent_id,
        seed=seed,
        split=split,
        branch_digests=selected,
    )


def load_runtime_facade_training_sidecar(
    root_dir: str,
    *,
    projection_digest: str,
    agent_id: str,
    seed: int,
    split: str,
    branch_digests: Sequence[str],
) -> dict[str, Any]:
    """Read and revalidate a RuntimeFacade learner sidecar and its identity."""

    _digest(projection_digest, "projection_digest")
    expected_branches = tuple(sorted(branch_digests))
    if not expected_branches or any(_DIGEST.fullmatch(value) is None for value in expected_branches):
        raise ContractError("branch_digests must contain lowercase SHA-256 digests")
    payload = _canonical_load(Path(root_dir) / _RUNTIME_EXPORT_SIDECAR)
    expected_keys = {
        "schema_version", "surface_id", "agent_id", "seed", "split",
        "projection_digest", "manifest_digests", "branch_digests", "packet_provenance",
        "branch_ancestry", "numeric_metadata_digest", "episodes", "metadata_digest",
    }
    if set(payload) != expected_keys:
        raise ContractError("runtime facade export sidecar keys differ")
    metadata_digest = payload["metadata_digest"]
    _digest(metadata_digest, "metadata_digest")
    without = dict(payload)
    without.pop("metadata_digest")
    if content_digest("experiment.runtime-facade-training-export", without) != metadata_digest:
        raise ContractError("metadata digest does not match sidecar payload")
    if payload["schema_version"] != RUNTIME_FACADE_TRAINING_EXPORT_SCHEMA:
        raise ContractError("unsupported runtime facade export schema")
    if payload["surface_id"] != AIR_RUNTIME_FACADE_SURFACE:
        raise ContractError("sidecar surface is not admitted Air RuntimeFacade")
    if payload["projection_digest"] != projection_digest:
        raise ContractError("sidecar projection digest mismatch")
    if payload["agent_id"] != agent_id or payload["seed"] != seed or payload["split"] != split:
        raise ContractError("sidecar fixed identity mismatch")
    if tuple(payload["branch_digests"]) != expected_branches:
        raise ContractError("sidecar branch ancestry mismatch")
    ancestry = payload["branch_ancestry"]
    if not isinstance(ancestry, list) or tuple(item.get("branch_digest") for item in ancestry) != expected_branches:
        raise ContractError("sidecar branch ancestry records mismatch")
    if any(
        not isinstance(item.get("branch_depth"), int)
        or item.get("branch_depth") < 0
        or (item.get("branch_depth") > 0 and not item.get("parent_branch_digest"))
        for item in ancestry
    ):
        raise ContractError("sidecar branch ancestry is incomplete")
    if payload["packet_provenance"] != "facade_observation_packet":
        raise ContractError("sidecar packet provenance is not facade observation")
    if not isinstance(payload["episodes"], list) or not payload["episodes"]:
        raise ContractError("sidecar episodes must be non-empty")
    for episode in payload["episodes"]:
        if not isinstance(episode, Mapping):
            raise ContractError("sidecar episode metadata is invalid")
        if episode.get("projection_digest") != projection_digest:
            raise ContractError("episode projection digest mismatch")
        if episode.get("agent_id") != agent_id or episode.get("seed") != seed:
            raise ContractError("episode fixed identity mismatch")
        if episode.get("split") != split or episode.get("observation_provenance") != payload["packet_provenance"]:
            raise ContractError("episode split or provenance mismatch")
        if episode.get("branch_digest") not in expected_branches:
            raise ContractError("episode branch digest is not selected")
    return payload


__all__ = [
    "AIR_RUNTIME_FACADE_SURFACE",
    "RUNTIME_FACADE_TRAINING_EXPORT_SCHEMA",
    "RuntimeFacadeTrainingExportReceipt",
    "export_runtime_facade_training_sidecar",
    "load_runtime_facade_training_sidecar",
]
