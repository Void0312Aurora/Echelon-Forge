"""Trace manifest: one session plus its branch timeline and transitions.

A :class:`TraceManifest` is the experiment-layer record that binds every branch
of one session to the transitions it produced. Its digest is the identity a
report, training projection, or comparison cites. It is evidence about an
experiment, not a ``RunReceipt``; durable run authority stays with the runtime
host owner.

``policy_ref`` names the decision model that produced the baseline actions
(for example a checkpoint id or a scripted policy name), so comparisons can
refuse to mix traces from different policies.

Integrity rules, all enforced at construction:

- every branch belongs to the manifest's session;
- branch digests are unique, at least one root exists, and every child's
  parent is present in the same manifest;
- a child's depth is its parent's plus one, it starts at a snapshot its parent
  recorded reaching (the parent's origin or a transition target), and its
  first transition applies its intervention;
- every agent named in an intervention, action or reward belongs to the
  session;
- each branch's transitions form a contiguous state chain that starts at the
  branch origin, carry that branch's digest, and stop at the first terminal
  transition.

Branches are stored in canonical order (depth, then digest), so the manifest
digest does not depend on the order a caller collected branches in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from python.experiment.contracts import BranchRef
from python.experiment.contracts import ContractError
from python.experiment.contracts import SessionSpec
from python.experiment.contracts import Transition
from python.experiment.contracts import canonical_bytes
from python.experiment.contracts import content_digest
from python.experiment.contracts import from_payload

TRACE_SCHEMA_VERSION = "echelon_forge.experiment_trace.v1"


@dataclass(frozen=True)
class BranchTrace:
    """The ordered transitions recorded on one branch."""

    branch: BranchRef
    transitions: tuple[Transition, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.branch, BranchRef):
            raise ContractError("branch must be a BranchRef")
        if not isinstance(self.transitions, tuple) or not all(
            isinstance(item, Transition) for item in self.transitions
        ):
            raise ContractError("transitions must be a tuple of Transition")
        expected_source = self.branch.origin_snapshot_digest
        expected_step = self.branch.origin_step
        for index, transition in enumerate(self.transitions):
            if transition.branch_digest != self.branch.digest:
                raise ContractError(f"transition {index} belongs to another branch")
            if transition.source_snapshot_digest != expected_source:
                if index == 0:
                    raise ContractError("the first transition must start at the branch origin")
                raise ContractError(f"transition {index} breaks the state chain")
            if transition.step != expected_step:
                raise ContractError(f"transition {index} step breaks the chain")
            if transition.terminated and index != len(self.transitions) - 1:
                raise ContractError(f"transition {index} terminated before the trace ended")
            expected_source = transition.target_snapshot_digest
            expected_step = transition.step + 1

    def to_payload(self) -> dict[str, Any]:
        return {
            "branch": self.branch.to_payload(),
            "transitions": [item.to_payload() for item in self.transitions],
        }


def _canonical_order(branches: tuple[BranchTrace, ...]) -> tuple[BranchTrace, ...]:
    return tuple(sorted(branches, key=lambda trace: (trace.branch.depth, trace.branch.digest)))


def _check_branch_tree(session: SessionSpec, branches: tuple[BranchTrace, ...]) -> None:
    """Reject manifests whose branches do not describe a reachable tree.

    Per-field checks on ``BranchRef`` cannot see the parent, so a decoded
    payload could otherwise claim a fork from a state its parent never
    reached, skip depths, or attribute actions to agents outside the session.
    """

    agents = set(session.agent_ids)
    by_digest = {trace.branch.digest: trace for trace in branches}
    for trace in branches:
        branch = trace.branch
        for agent_id, _ in branch.intervention:
            if agent_id not in agents:
                raise ContractError(f"intervention names agent {agent_id!r} outside the session")
        for index, transition in enumerate(trace.transitions):
            for agent_id, _ in (*transition.actions, *transition.rewards):
                if agent_id not in agents:
                    raise ContractError(
                        f"transition {index} names agent {agent_id!r} outside the session"
                    )
        if branch.parent_digest is None:
            continue
        parent = by_digest[branch.parent_digest]
        if branch.depth != parent.branch.depth + 1:
            raise ContractError("a child branch's depth must be its parent's depth plus one")
        reached = {(parent.branch.origin_snapshot_digest, parent.branch.origin_step)}
        reached.update(
            (transition.target_snapshot_digest, transition.step + 1)
            for transition in parent.transitions
        )
        if (branch.origin_snapshot_digest, branch.origin_step) not in reached:
            raise ContractError(
                "a child branch must start at a state its parent recorded reaching"
            )
        if trace.transitions and not set(branch.intervention) <= set(
            trace.transitions[0].actions
        ):
            raise ContractError("a child branch's first transition must apply its intervention")


@dataclass(frozen=True)
class TraceManifest:
    """All branch traces of one session, in canonical order."""

    session: SessionSpec
    policy_ref: str
    branches: tuple[BranchTrace, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.session, SessionSpec):
            raise ContractError("session must be a SessionSpec")
        if not isinstance(self.policy_ref, str) or not self.policy_ref.strip():
            raise ContractError("policy_ref must be a non-empty string")
        canonical_bytes(self.policy_ref)
        if not isinstance(self.branches, tuple) or not all(
            isinstance(item, BranchTrace) for item in self.branches
        ):
            raise ContractError("branches must be a tuple of BranchTrace")
        session_digest = self.session.digest
        digests: set[str] = set()
        for trace in self.branches:
            if trace.branch.session_digest != session_digest:
                raise ContractError("a branch belongs to another session")
            if trace.branch.digest in digests:
                raise ContractError("duplicate branch in manifest")
            digests.add(trace.branch.digest)
        for trace in self.branches:
            parent = trace.branch.parent_digest
            if parent is not None and parent not in digests:
                raise ContractError("a child branch's parent is missing from the manifest")
        if not any(trace.branch.parent_digest is None for trace in self.branches):
            raise ContractError("a manifest needs at least one root branch")
        _check_branch_tree(self.session, self.branches)
        object.__setattr__(self, "branches", _canonical_order(self.branches))

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": TRACE_SCHEMA_VERSION,
            "session": self.session.to_payload(),
            "policy_ref": self.policy_ref,
            "branches": [trace.to_payload() for trace in self.branches],
        }

    @property
    def digest(self) -> str:
        return content_digest("experiment.trace-manifest", self.to_payload())


def _decode(payload: Mapping[str, Any], expected: type) -> Any:
    contract = from_payload(payload)
    if not isinstance(contract, expected):
        raise ContractError(f"expected {expected.__name__}, got {type(contract).__name__}")
    return contract


def _require_keys(payload: Any, keys: frozenset[str], name: str) -> None:
    if not isinstance(payload, Mapping):
        raise ContractError(f"{name} must be a mapping")
    unknown = sorted(set(payload) - keys)
    missing = sorted(keys - set(payload))
    if unknown:
        raise ContractError(f"{name}: unknown fields {unknown}")
    if missing:
        raise ContractError(f"{name}: missing fields {missing}")


def manifest_from_payload(payload: Mapping[str, Any]) -> TraceManifest:
    """Rebuild a manifest from its payload, failing closed on any drift."""

    _require_keys(
        payload, frozenset({"schema_version", "session", "policy_ref", "branches"}), "manifest"
    )
    if payload["schema_version"] != TRACE_SCHEMA_VERSION:
        raise ContractError(f"schema_version must be {TRACE_SCHEMA_VERSION!r}")
    if not isinstance(payload["branches"], list):
        raise ContractError("manifest branches must be a list")
    branches = []
    for entry in payload["branches"]:
        _require_keys(entry, frozenset({"branch", "transitions"}), "branch trace")
        if not isinstance(entry["transitions"], list):
            raise ContractError("branch trace transitions must be a list")
        branches.append(
            BranchTrace(
                branch=_decode(entry["branch"], BranchRef),
                transitions=tuple(_decode(item, Transition) for item in entry["transitions"]),
            )
        )
    return TraceManifest(
        session=_decode(payload["session"], SessionSpec),
        policy_ref=payload["policy_ref"],
        branches=tuple(branches),
    )


__all__ = [
    "TRACE_SCHEMA_VERSION",
    "BranchTrace",
    "TraceManifest",
    "manifest_from_payload",
]
