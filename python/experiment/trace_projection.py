"""Audited projections of canonical experiment traces for downstream consumers.

The experiment trace remains the authority. This module only projects its
immutable transition records into a consumer-labelled table; it does not add
observations, infer rewards, or replace the runtime checkpoint authority.

Splits are assigned at the session level. Consequently every branch and every
descendant in one manifest stays in one split, which prevents branch ancestry
from leaking between training and evaluation. The serialized projection is a
deterministic compatibility export that PPO, BC, world-model, and evaluation
adapters can consume without each inventing a second trace schema.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from python.experiment.contracts import ContractError, content_digest
from python.experiment.trace import TraceManifest


TRACE_PROJECTION_SCHEMA_VERSION = "echelon_forge.experiment_trace_projection.v1"
CONSUMERS: tuple[str, ...] = ("bc", "evaluation", "ppo", "world_model")
SPLITS: tuple[str, ...] = ("evaluation", "training")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def _strict_int(value: Any, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContractError(f"{name} must be a non-negative integer")


def _strict_text(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a non-empty string")


def _strict_digest(value: Any, name: str) -> None:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ContractError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True)
class SeedSplit:
    """Explicit disjoint seed sets used by one projection."""

    training: tuple[int, ...]
    evaluation: tuple[int, ...]

    def __post_init__(self) -> None:
        for name, values in (("training", self.training), ("evaluation", self.evaluation)):
            if not isinstance(values, tuple) or not values:
                raise ContractError(f"{name} seeds must be a non-empty tuple")
            if any(
                isinstance(value, bool) or not isinstance(value, int) or value < 0
                for value in values
            ):
                raise ContractError(f"{name} seeds must be non-negative integers")
            if values != tuple(sorted(set(values))):
                raise ContractError(f"{name} seeds must be sorted and unique")
        if set(self.training) & set(self.evaluation):
            raise ContractError("training and evaluation seeds must be disjoint")

    def split_for(self, seed: int) -> str:
        if seed in self.training:
            return "training"
        if seed in self.evaluation:
            return "evaluation"
        raise ContractError(f"seed {seed} is absent from the declared split")

    def to_payload(self) -> dict[str, list[int]]:
        return {"training": list(self.training), "evaluation": list(self.evaluation)}


@dataclass(frozen=True)
class ProjectionRow:
    """One canonical transition with lineage and split metadata attached."""

    split: str
    seed: int
    session_digest: str
    manifest_digest: str
    policy_ref: str
    evidence_label: str
    branch_digest: str
    parent_branch_digest: str | None
    branch_depth: int
    branch_label: str
    step: int
    source_snapshot_digest: str
    target_snapshot_digest: str
    actions: tuple[tuple[str, str], ...]
    rewards: tuple[tuple[str, int], ...]
    terminated: bool
    observation_provenance: str

    def __post_init__(self) -> None:
        if self.split not in SPLITS:
            raise ContractError(f"split must be one of {SPLITS}")
        _strict_int(self.seed, "seed")
        for name, value in (
            ("session_digest", self.session_digest),
            ("manifest_digest", self.manifest_digest),
            ("branch_digest", self.branch_digest),
            ("source_snapshot_digest", self.source_snapshot_digest),
            ("target_snapshot_digest", self.target_snapshot_digest),
        ):
            _strict_digest(value, name)
        if self.parent_branch_digest is not None:
            _strict_digest(self.parent_branch_digest, "parent_branch_digest")
        _strict_int(self.branch_depth, "branch_depth")
        _strict_int(self.step, "step")
        for name, pairs in (("actions", self.actions), ("rewards", self.rewards)):
            if not isinstance(pairs, tuple) or not pairs:
                raise ContractError(f"{name} must be a non-empty tuple")
            if any(not isinstance(pair, tuple) or len(pair) != 2 for pair in pairs):
                raise ContractError(f"{name} entries must be pairs")
            agents = [pair[0] for pair in pairs]
            if agents != sorted(set(agents)):
                raise ContractError(f"{name} must be sorted by unique agent")
        if any(not isinstance(agent, str) or not agent for agent, _ in self.actions):
            raise ContractError("action agent ids must be non-empty strings")
        if any(
            not isinstance(agent, str)
            or not agent
            or isinstance(value, bool)
            or not isinstance(value, int)
            for agent, value in self.rewards
        ):
            raise ContractError("reward pairs must contain integer values")
        if tuple(agent for agent, _ in self.actions) != tuple(agent for agent, _ in self.rewards):
            raise ContractError("rewards must cover the action agents in the same order")
        if not isinstance(self.terminated, bool):
            raise ContractError("terminated must be a bool")
        _strict_text(self.policy_ref, "policy_ref")
        _strict_text(self.evidence_label, "evidence_label")
        _strict_text(self.branch_label, "branch_label")
        _strict_text(self.observation_provenance, "observation_provenance")

    def to_payload(self) -> dict[str, Any]:
        return {
            "split": self.split,
            "seed": self.seed,
            "session_digest": self.session_digest,
            "manifest_digest": self.manifest_digest,
            "policy_ref": self.policy_ref,
            "evidence_label": self.evidence_label,
            "branch_digest": self.branch_digest,
            "parent_branch_digest": self.parent_branch_digest,
            "branch_depth": self.branch_depth,
            "branch_label": self.branch_label,
            "step": self.step,
            "source_snapshot_digest": self.source_snapshot_digest,
            "target_snapshot_digest": self.target_snapshot_digest,
            "actions": [[agent, value] for agent, value in self.actions],
            "rewards": [[agent, value] for agent, value in self.rewards],
            "terminated": self.terminated,
            "observation_provenance": self.observation_provenance,
        }


@dataclass(frozen=True)
class TraceProjection:
    """Deterministic, lineage-preserving compatibility export."""

    consumer: str
    split_spec: SeedSplit
    manifest_digests: tuple[str, ...]
    rows: tuple[ProjectionRow, ...]

    def __post_init__(self) -> None:
        if self.consumer not in CONSUMERS:
            raise ContractError(f"consumer must be one of {CONSUMERS}")
        if not isinstance(self.split_spec, SeedSplit):
            raise ContractError("split_spec must be a SeedSplit")
        if not isinstance(self.manifest_digests, tuple) or not self.manifest_digests:
            raise ContractError("manifest_digests must be a non-empty tuple")
        if any(_DIGEST.fullmatch(value) is None for value in self.manifest_digests):
            raise ContractError("manifest_digests must contain lowercase SHA-256 digests")
        if tuple(sorted(set(self.manifest_digests))) != self.manifest_digests:
            raise ContractError("manifest_digests must be sorted and unique")
        if not isinstance(self.rows, tuple) or not all(
            isinstance(row, ProjectionRow) for row in self.rows
        ):
            raise ContractError("rows must be a tuple of ProjectionRow")
        if any(row.manifest_digest not in self.manifest_digests for row in self.rows):
            raise ContractError("every row must belong to a declared manifest")

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": TRACE_PROJECTION_SCHEMA_VERSION,
            "consumer": self.consumer,
            "split_spec": self.split_spec.to_payload(),
            "manifest_digests": list(self.manifest_digests),
            "rows": [row.to_payload() for row in self.rows],
        }

    @property
    def digest(self) -> str:
        return content_digest("experiment.trace-projection", self._payload_without_digest())

    def to_payload(self) -> dict[str, Any]:
        return {**self._payload_without_digest(), "projection_digest": self.digest}

    def compatibility_records(self) -> tuple[dict[str, Any], ...]:
        """Return immutable row payloads for PPO/BC/world-model/evaluation adapters."""

        return tuple(row.to_payload() for row in self.rows)


def _require_keys(value: Any, expected: frozenset[str], name: str) -> None:
    if not isinstance(value, Mapping):
        raise ContractError(f"{name} must be a mapping")
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown or missing:
        raise ContractError(f"{name} keys differ: unknown={unknown}, missing={missing}")


def projection_from_payload(payload: Mapping[str, Any]) -> TraceProjection:
    """Decode a projection export and reject schema, digest, or shape drift."""

    _require_keys(
        payload,
        frozenset(
            {
                "schema_version",
                "consumer",
                "split_spec",
                "manifest_digests",
                "rows",
                "projection_digest",
            }
        ),
        "projection",
    )
    if payload["schema_version"] != TRACE_PROJECTION_SCHEMA_VERSION:
        raise ContractError("unsupported trace projection schema")
    split_payload = payload["split_spec"]
    _require_keys(split_payload, frozenset({"training", "evaluation"}), "split_spec")
    if not all(isinstance(values, list) for values in split_payload.values()):
        raise ContractError("split_spec values must be lists")
    rows_payload = payload["rows"]
    if not isinstance(rows_payload, list):
        raise ContractError("projection rows must be a list")
    row_keys = frozenset(
        {
            "split",
            "seed",
            "session_digest",
            "manifest_digest",
            "policy_ref",
            "evidence_label",
            "branch_digest",
            "parent_branch_digest",
            "branch_depth",
            "branch_label",
            "step",
            "source_snapshot_digest",
            "target_snapshot_digest",
            "actions",
            "rewards",
            "terminated",
            "observation_provenance",
        }
    )
    rows = []
    for raw in rows_payload:
        _require_keys(raw, row_keys, "projection row")
        if not isinstance(raw["actions"], list) or not isinstance(raw["rewards"], list):
            raise ContractError("projection row pairs must be lists")
        actions = tuple(tuple(pair) for pair in raw["actions"])
        rewards = tuple(tuple(pair) for pair in raw["rewards"])
        rows.append(ProjectionRow(**{**raw, "actions": actions, "rewards": rewards}))
    projection = TraceProjection(
        consumer=payload["consumer"],
        split_spec=SeedSplit(
            training=tuple(split_payload["training"]),
            evaluation=tuple(split_payload["evaluation"]),
        ),
        manifest_digests=tuple(payload["manifest_digests"]),
        rows=tuple(rows),
    )
    if payload["projection_digest"] != projection.digest:
        raise ContractError("projection digest does not match its canonical payload")
    return projection


def project_manifests(
    manifests: tuple[TraceManifest, ...],
    split_spec: SeedSplit,
    *,
    consumer: str,
) -> TraceProjection:
    """Project manifests while enforcing seed, policy, evidence, and lineage gates."""

    if not isinstance(manifests, tuple) or not manifests:
        raise ContractError("manifests must be a non-empty tuple")
    if not isinstance(split_spec, SeedSplit):
        raise ContractError("split_spec must be a SeedSplit")
    if consumer not in CONSUMERS:
        raise ContractError(f"consumer must be one of {CONSUMERS}")
    manifest_digests: list[str] = []
    seed_owners: dict[int, str] = {}
    policy_ref: str | None = None
    evidence_label: str | None = None
    rows: list[ProjectionRow] = []
    for manifest in manifests:
        if not isinstance(manifest, TraceManifest):
            raise ContractError("manifests must contain TraceManifest values")
        digest = manifest.digest
        if digest in manifest_digests:
            raise ContractError("duplicate manifest")
        split = split_spec.split_for(manifest.session.seed)
        owner = seed_owners.setdefault(manifest.session.seed, digest)
        if owner != digest:
            raise ContractError("one seed cannot produce multiple manifests")
        if policy_ref is None:
            policy_ref = manifest.policy_ref
        elif manifest.policy_ref != policy_ref:
            raise ContractError("projection cannot mix policy identities")
        if evidence_label is None:
            evidence_label = manifest.session.evidence_label
        elif manifest.session.evidence_label != evidence_label:
            raise ContractError("projection cannot mix evidence labels")
        manifest_digests.append(digest)
        for trace in manifest.branches:
            for transition in trace.transitions:
                rows.append(
                    ProjectionRow(
                        split=split,
                        seed=manifest.session.seed,
                        session_digest=manifest.session.digest,
                        manifest_digest=digest,
                        policy_ref=manifest.policy_ref,
                        evidence_label=manifest.session.evidence_label,
                        branch_digest=trace.branch.digest,
                        parent_branch_digest=trace.branch.parent_digest,
                        branch_depth=trace.branch.depth,
                        branch_label=trace.branch.label,
                        step=transition.step,
                        source_snapshot_digest=transition.source_snapshot_digest,
                        target_snapshot_digest=transition.target_snapshot_digest,
                        actions=transition.actions,
                        rewards=transition.rewards,
                        terminated=transition.terminated,
                        observation_provenance=transition.observation_provenance,
                    )
                )
    if not rows:
        raise ContractError("projection needs at least one transition")
    rows.sort(
        key=lambda row: (
            row.split,
            row.seed,
            row.session_digest,
            row.branch_depth,
            row.branch_digest,
            row.step,
        )
    )
    return TraceProjection(
        consumer=consumer,
        split_spec=split_spec,
        manifest_digests=tuple(sorted(manifest_digests)),
        rows=tuple(rows),
    )


__all__ = [
    "CONSUMERS",
    "SPLITS",
    "TRACE_PROJECTION_SCHEMA_VERSION",
    "ProjectionRow",
    "SeedSplit",
    "TraceProjection",
    "project_manifests",
    "projection_from_payload",
]
