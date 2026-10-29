"""Versioned experiment-layer contracts for sessions, snapshots, and branches.

This module owns the branch vocabulary of the simulation experiment platform
(``docs/architecture/work/active/simulation_experiment_platform/README.md``):
which session a result came from, which state a branch started at, which
intervention distinguishes sibling branches, and which observation surface a
transition was allowed to read.

Boundary rules:

1. Durable execution authority is not owned here. ``ExperimentRequest``,
   ``ResolvedCompositionPlan``, ``RunReceipt``, and the native
   ``StateCheckpoint`` belong to the long-horizon architecture governance
   program. A :class:`SnapshotRef` is a reference to backend state, never a
   checkpoint payload, and nothing here persists state.
2. Identities are SHA-256 digests over the float-free subset of the
   ``echelon_forge.canonical_json.v2`` profile, domain-separated per contract
   kind. For integers, strings, booleans, null, lists, and objects that profile
   reduces to sorted-key compact UTF-8 JSON; a test pins byte equality with the
   authority implementation. Floats are rejected rather than re-implementing
   the profile's number rules.
3. Fail closed: every contract validates at construction, and
   :func:`from_payload` rejects unknown, missing, or mistyped fields and any
   other schema version.
4. Standard library plus the neutral contract layer only. Importing this
   module must not pull ``ef_py``, gym, SB3, torch, ``python.rl``, or
   ``tools``. Maintained policy-input labels come from their owner,
   ``python.tasking_contracts.common.agent_contracts``. Fixed open-loop protocols
   can explicitly declare that no policy observation was read; their evaluator
   diagnostics do not become policy input or a maintained observation packet.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, fields
from typing import Any, Mapping

from python.tasking_contracts.common.agent_contracts import (
    LAW14_MAINTAINED_READ_LABEL_ALLOWLIST,
)

CONTRACT_SCHEMA_VERSION = "echelon_forge.experiment.v1"
DIGEST_DOMAIN_PREFIX = b"echelon-forge-experiment-v1\x00"

#: Evidence labels a session may carry. None of them claims maintained runtime
#: authority; ``runtime_candidate`` marks an adapter run that still awaits its
#: acceptance gate.
EVIDENCE_LABELS: tuple[str, ...] = ("synthetic", "toy", "runtime_candidate")

#: Fixed open-loop protocols read no policy observation. Diagnostic evaluator
#: reads are separate from policy inputs and must not claim a maintained packet.
FIXED_PROTOCOL_PROVENANCE = "fixed_protocol_no_policy_observation"
POLICY_INPUT_PROVENANCE_LABELS: tuple[str, ...] = (
    *LAW14_MAINTAINED_READ_LABEL_ALLOWLIST,
    FIXED_PROTOCOL_PROVENANCE,
)

MAX_EXACT_INTEGER = 9_007_199_254_740_991

_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9_]*\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SURROGATE = re.compile("[\ud800-\udfff]")


class ContractError(ValueError):
    """Raised when an experiment contract value fails closed."""


def _check_canonical_value(value: Any, path: str) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if abs(value) > MAX_EXACT_INTEGER:
            raise ContractError(f"{path}: integer outside the exact cross-language range")
        return
    if isinstance(value, float):
        raise ContractError(f"{path}: floats are outside the experiment digest profile")
    if isinstance(value, str):
        if not value.isascii() and _SURROGATE.search(value):
            raise ContractError(f"{path}: lone UTF-16 surrogate")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _check_canonical_value(item, f"{path}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractError(f"{path}: object keys must be strings")
            _check_canonical_value(key, f"{path}.<key>")
            _check_canonical_value(item, f"{path}.{key}")
        return
    raise ContractError(f"{path}: unsupported value {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """Encode ``value`` with the float-free canonical JSON v2 subset."""

    _check_canonical_value(value, "$")
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def content_digest(domain: str, payload: Mapping[str, Any]) -> str:
    """Domain-separated SHA-256 over the canonical payload bytes."""

    if not domain or "\x00" in domain:
        raise ContractError("digest domain must be a non-empty string without NUL")
    return hashlib.sha256(
        DIGEST_DOMAIN_PREFIX + domain.encode("utf-8") + b"\x00" + canonical_bytes(payload)
    ).hexdigest()


def _require_identifier(value: Any, name: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ContractError(f"{name} must match [a-z0-9][a-z0-9_]*, got {value!r}")


def _require_text(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a non-empty string")


def _require_digest(value: Any, name: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ContractError(f"{name} must be a lowercase SHA-256 digest")


def _require_count(value: Any, name: str, *, minimum: int = 0) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{name} must be an integer >= {minimum}, got {value!r}")
    if value > MAX_EXACT_INTEGER:
        raise ContractError(f"{name} exceeds the exact cross-language range")


def _require_agent_ids(value: Any, name: str) -> None:
    if not isinstance(value, tuple) or not value:
        raise ContractError(f"{name} must be a non-empty tuple")
    for agent_id in value:
        _require_identifier(agent_id, f"{name} entry")
    if list(value) != sorted(set(value)):
        raise ContractError(f"{name} must be strictly increasing and unique")


def _require_agent_pairs(value: Any, name: str, *, allow_empty: bool, numeric: bool) -> None:
    if not isinstance(value, tuple) or (not value and not allow_empty):
        raise ContractError(f"{name} must be a{' ' if allow_empty else ' non-empty '}tuple")
    keys = []
    for pair in value:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ContractError(f"{name} entries must be (agent_id, value) pairs")
        agent_id, item = pair
        _require_identifier(agent_id, f"{name} agent id")
        if numeric:
            if isinstance(item, bool) or not isinstance(item, int):
                raise ContractError(f"{name} values must be integers")
            _check_canonical_value(item, name)
        else:
            _require_text(item, f"{name} value")
        keys.append(agent_id)
    if keys != sorted(set(keys)):
        raise ContractError(f"{name} must be sorted by unique agent id")


def _pairs_to_payload(pairs: tuple[tuple[str, Any], ...]) -> list[list[Any]]:
    return [[agent_id, item] for agent_id, item in pairs]


def _pairs_from_payload(value: Any, name: str) -> tuple[tuple[str, Any], ...]:
    if not isinstance(value, list) or not all(
        isinstance(pair, list) and len(pair) == 2 for pair in value
    ):
        raise ContractError(f"{name} must be a list of [agent_id, value] pairs")
    return tuple((pair[0], pair[1]) for pair in value)


class _Contract:
    """Shared payload, digest, and decoding behavior for contract dataclasses."""

    KIND: str = ""
    _TUPLE_FIELDS: frozenset[str] = frozenset()
    _PAIR_FIELDS: frozenset[str] = frozenset()

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"kind": self.KIND, "schema_version": CONTRACT_SCHEMA_VERSION}
        for item in fields(self):  # type: ignore[arg-type]
            value = getattr(self, item.name)
            if item.name in self._PAIR_FIELDS:
                value = _pairs_to_payload(value)
            elif item.name in self._TUPLE_FIELDS:
                value = list(value)
            payload[item.name] = value
        return payload

    @property
    def digest(self) -> str:
        cached = self.__dict__.get("_digest_cache")
        if cached is None:
            cached = content_digest(f"experiment.{self.KIND}", self.to_payload())
            object.__setattr__(self, "_digest_cache", cached)
        return cached

    @classmethod
    def _from_fields(cls, payload: Mapping[str, Any]) -> "_Contract":
        expected = {item.name for item in fields(cls)}  # type: ignore[arg-type]
        present = set(payload) - {"kind", "schema_version"}
        unknown = sorted(present - expected)
        missing = sorted(expected - present)
        if unknown:
            raise ContractError(f"{cls.KIND}: unknown fields {unknown}")
        if missing:
            raise ContractError(f"{cls.KIND}: missing fields {missing}")
        values: dict[str, Any] = {}
        for name in expected:
            value = payload[name]
            if name in cls._PAIR_FIELDS:
                value = _pairs_from_payload(value, name)
            elif name in cls._TUPLE_FIELDS:
                if not isinstance(value, list):
                    raise ContractError(f"{cls.KIND}.{name} must be a list")
                value = tuple(value)
            values[name] = value
        return cls(**values)


@dataclass(frozen=True)
class SessionSpec(_Contract):
    """What a session runs: backend, scenario, configuration, seed, and agents.

    ``scenario_ref`` and ``config_digest`` identify inputs; resolving them into
    an executable plan is owned by the runtime composition authority, not here.
    """

    KIND = "session-spec"
    _TUPLE_FIELDS = frozenset({"agent_ids"})

    session_id: str
    backend: str
    scenario_ref: str
    config_digest: str
    seed: int
    agent_ids: tuple[str, ...]
    evidence_label: str

    def __post_init__(self) -> None:
        _require_identifier(self.session_id, "session_id")
        _require_identifier(self.backend, "backend")
        _require_text(self.scenario_ref, "scenario_ref")
        _require_digest(self.config_digest, "config_digest")
        _require_count(self.seed, "seed")
        _require_agent_ids(self.agent_ids, "agent_ids")
        if self.evidence_label not in EVIDENCE_LABELS:
            raise ContractError(f"evidence_label must be one of {EVIDENCE_LABELS}")


@dataclass(frozen=True)
class SnapshotRef(_Contract):
    """Reference to backend state at one step; it carries no state payload.

    ``state_digest``, ``event_cursor``, and ``rng_digest`` are produced by the
    backend that owns the state. Two refs are the same state only when every
    component matches.
    """

    KIND = "snapshot-ref"

    session_digest: str
    step: int
    state_digest: str
    event_cursor: int
    rng_digest: str

    def __post_init__(self) -> None:
        _require_digest(self.session_digest, "session_digest")
        _require_count(self.step, "step")
        _require_digest(self.state_digest, "state_digest")
        _require_count(self.event_cursor, "event_cursor")
        _require_digest(self.rng_digest, "rng_digest")


@dataclass(frozen=True)
class BranchRef(_Contract):
    """One node of the branch timeline: origin snapshot, parent, intervention.

    A root branch has no parent and no intervention. A child branch names its
    parent digest and the per-agent intervention that distinguishes it from
    its siblings, so ancestry and intervention are both part of its identity.
    """

    KIND = "branch-ref"
    _PAIR_FIELDS = frozenset({"intervention"})

    origin_snapshot_digest: str
    origin_step: int
    session_digest: str
    parent_digest: str | None
    depth: int
    intervention: tuple[tuple[str, str], ...] = field(default=())
    label: str = "baseline"

    def __post_init__(self) -> None:
        _require_digest(self.origin_snapshot_digest, "origin_snapshot_digest")
        _require_count(self.origin_step, "origin_step")
        _require_digest(self.session_digest, "session_digest")
        _require_count(self.depth, "depth")
        _require_identifier(self.label, "label")
        _require_agent_pairs(self.intervention, "intervention", allow_empty=True, numeric=False)
        if self.parent_digest is None:
            if self.depth != 0 or self.intervention:
                raise ContractError("a root branch has depth 0 and no intervention")
        else:
            _require_digest(self.parent_digest, "parent_digest")
            if self.depth < 1 or not self.intervention:
                raise ContractError("a child branch needs depth >= 1 and an intervention")

    @classmethod
    def root(cls, snapshot: SnapshotRef, *, label: str = "baseline") -> "BranchRef":
        return cls(
            origin_snapshot_digest=snapshot.digest,
            origin_step=snapshot.step,
            session_digest=snapshot.session_digest,
            parent_digest=None,
            depth=0,
            label=label,
        )

    @classmethod
    def child(
        cls,
        parent: "BranchRef",
        snapshot: SnapshotRef,
        *,
        intervention: tuple[tuple[str, str], ...],
        label: str,
    ) -> "BranchRef":
        if snapshot.session_digest != parent.session_digest:
            raise ContractError("a child branch must stay in its parent's session")
        if snapshot.step < parent.origin_step:
            raise ContractError("a child branch cannot start before its parent's origin")
        return cls(
            origin_snapshot_digest=snapshot.digest,
            origin_step=snapshot.step,
            session_digest=snapshot.session_digest,
            parent_digest=parent.digest,
            depth=parent.depth + 1,
            intervention=intervention,
            label=label,
        )



@dataclass(frozen=True)
class DecisionWindow(_Contract):
    """A candidate decision point: where to branch, how far, and for whom."""

    KIND = "decision-window"
    _TUPLE_FIELDS = frozenset({"agent_ids"})

    session_digest: str
    start_step: int
    horizon: int
    agent_ids: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        _require_digest(self.session_digest, "session_digest")
        _require_count(self.start_step, "start_step")
        _require_count(self.horizon, "horizon", minimum=1)
        _require_agent_ids(self.agent_ids, "agent_ids")
        _require_identifier(self.reason, "reason")


@dataclass(frozen=True)
class Transition(_Contract):
    """One step on one branch, bound to its source and target state identity.

    Rewards are integers in the backend's declared reward units so the record
    stays inside the float-free digest profile. ``observation_provenance``
    must be an admitted policy-input label; diagnostics and raw truth may not
    feed a recorded decision.
    """

    KIND = "transition"
    _PAIR_FIELDS = frozenset({"actions", "rewards"})

    branch_digest: str
    step: int
    source_snapshot_digest: str
    target_snapshot_digest: str
    actions: tuple[tuple[str, str], ...]
    rewards: tuple[tuple[str, int], ...]
    terminated: bool
    observation_provenance: str

    def __post_init__(self) -> None:
        _require_digest(self.branch_digest, "branch_digest")
        _require_count(self.step, "step")
        _require_digest(self.source_snapshot_digest, "source_snapshot_digest")
        _require_digest(self.target_snapshot_digest, "target_snapshot_digest")
        if self.source_snapshot_digest == self.target_snapshot_digest:
            raise ContractError("a transition must change the snapshot identity")
        _require_agent_pairs(self.actions, "actions", allow_empty=False, numeric=False)
        _require_agent_pairs(self.rewards, "rewards", allow_empty=False, numeric=True)
        if [agent for agent, _ in self.rewards] != [agent for agent, _ in self.actions]:
            raise ContractError("rewards must cover exactly the acting agents")
        if not isinstance(self.terminated, bool):
            raise ContractError("terminated must be a bool")
        if self.observation_provenance not in POLICY_INPUT_PROVENANCE_LABELS:
            raise ContractError(
                f"observation provenance {self.observation_provenance!r} is not an admitted "
                f"policy input; expected one of {POLICY_INPUT_PROVENANCE_LABELS}"
            )


_CONTRACTS: dict[str, type[_Contract]] = {
    contract.KIND: contract
    for contract in (SessionSpec, SnapshotRef, BranchRef, DecisionWindow, Transition)
}


def from_payload(payload: Mapping[str, Any]) -> _Contract:
    """Rebuild a contract from its payload, failing closed on any drift."""

    if not isinstance(payload, Mapping):
        raise ContractError("payload must be a mapping")
    if payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise ContractError(f"schema_version must be {CONTRACT_SCHEMA_VERSION!r}")
    contract = _CONTRACTS.get(payload.get("kind"))  # type: ignore[arg-type]
    if contract is None:
        raise ContractError(f"unknown contract kind {payload.get('kind')!r}")
    return contract._from_fields(payload)


__all__ = [
    "CONTRACT_SCHEMA_VERSION",
    "EVIDENCE_LABELS",
    "FIXED_PROTOCOL_PROVENANCE",
    "POLICY_INPUT_PROVENANCE_LABELS",
    "BranchRef",
    "ContractError",
    "DecisionWindow",
    "SessionSpec",
    "SnapshotRef",
    "Transition",
    "canonical_bytes",
    "content_digest",
    "from_payload",
]
