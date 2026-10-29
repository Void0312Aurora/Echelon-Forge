"""Standard-library reference session over small deterministic worlds.

This is the P2 reference backend of the simulation experiment platform. Its
tests define what any later runtime adapter must satisfy: identical inputs give
identical traces, restoring a recorded snapshot reproduces the continuation,
and forking never mutates the parent or a sibling branch.

It is deliberately not a simulator. A :class:`ReferenceWorld` supplies an
immutable state, an integer reward law, and termination; the session owns the
branch timeline around it. The default :class:`DelayedCommitmentWorld` shares
its reward law with :mod:`python.experiment.counterfactual_toy` so the session
and the closed-form rollout cannot drift apart. All evidence it produces is
labelled ``toy`` or ``synthetic`` by the world, never ``runtime``.

Snapshots are kept in memory only, keyed by their :class:`SnapshotRef` digest,
and a branch may fork only from a snapshot recorded on its parent. Nothing is
persisted and no checkpoint format is defined here; durable state authority
belongs to the native runtime host.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Hashable, Mapping, Protocol

from python.experiment.contracts import BranchRef
from python.experiment.contracts import SessionSpec
from python.experiment.contracts import SnapshotRef
from python.experiment.contracts import Transition
from python.experiment.contracts import content_digest
from python.experiment.counterfactual_toy import COMMIT
from python.experiment.counterfactual_toy import HOLD
from python.experiment.counterfactual_toy import REWARD_UNITS_PER_POINT
from python.experiment.counterfactual_toy import advance_commit_ages
from python.experiment.counterfactual_toy import agent_step_rewards
from python.experiment.trace import BranchTrace
from python.experiment.trace import TraceManifest

REFERENCE_BACKEND = "reference_toy"
REFERENCE_SCENARIO = "toy:delayed_commitment"
ACTIONS: Mapping[str, int] = {"hold": HOLD, "commit": COMMIT}


class SessionError(RuntimeError):
    """Raised when a reference-session operation is not admissible."""


class ReferenceWorld(Protocol):
    """A small deterministic world the reference session can branch over.

    States must be immutable and hashable. ``encode_state`` must be a pure,
    integer-only projection that determines every future reward, because the
    session uses it as the state identity that forks and convergence rely on.
    """

    scenario_ref: str
    actions: tuple[str, ...]
    evidence_label: str
    reward_units_per_point: int

    def config_payload(self) -> Mapping[str, Any]: ...

    def initial_state(self, seed: int, agent_count: int) -> Hashable: ...

    def encode_state(self, state: Hashable) -> Mapping[str, Any]: ...

    def step(
        self, state: Hashable, actions: tuple[str, ...]
    ) -> tuple[Hashable, tuple[int, ...], bool]: ...


@dataclass(frozen=True)
class DelayedCommitmentWorld:
    """The canary toy: hold pays now, commitment pays after a delay."""

    max_steps: int = 64
    scenario_ref: str = REFERENCE_SCENARIO
    actions: tuple[str, ...] = tuple(ACTIONS)
    evidence_label: str = "toy"
    reward_units_per_point: int = REWARD_UNITS_PER_POINT

    def __post_init__(self) -> None:
        if isinstance(self.max_steps, bool) or not isinstance(self.max_steps, int) or self.max_steps < 1:
            raise SessionError("max_steps must be a positive integer")

    def config_payload(self) -> Mapping[str, Any]:
        return {"max_steps": self.max_steps}

    def initial_state(self, seed: int, agent_count: int) -> tuple[int, tuple[int, ...]]:
        return (0, (0,) * agent_count)

    def encode_state(self, state: tuple[int, tuple[int, ...]]) -> Mapping[str, Any]:
        step, commit_ages = state
        return {"step": step, "commit_ages": list(commit_ages)}

    def step(
        self, state: tuple[int, tuple[int, ...]], actions: tuple[str, ...]
    ) -> tuple[tuple[int, tuple[int, ...]], tuple[int, ...], bool]:
        step, commit_ages = state
        codes = tuple(ACTIONS[name] for name in actions)
        rewards = agent_step_rewards(codes, commit_ages)
        successor = (step + 1, advance_commit_ages(codes, commit_ages))
        return successor, rewards, step + 1 >= self.max_steps


@dataclass(frozen=True)
class _Node:
    state: Hashable
    step: int
    terminated: bool


@dataclass
class _BranchRecord:
    ref: BranchRef
    head: SnapshotRef
    nodes: dict[str, _Node]
    transitions: list[Transition]
    pending_intervention: tuple[tuple[str, str], ...]


class ReferenceSession:
    """In-memory branch timeline over one reference world."""

    def __init__(self, spec: SessionSpec, policy_ref: str, world: ReferenceWorld) -> None:
        self._spec = spec
        self._policy_ref = policy_ref
        self._world = world
        self._session_digest = spec.digest
        self._rng_digest = content_digest("experiment.reference-rng", {"seed": spec.seed})
        initial = _Node(world.initial_state(spec.seed, len(spec.agent_ids)), 0, False)
        origin = self._snapshot(initial)
        root = BranchRef.root(origin)
        self._branches: dict[str, _BranchRecord] = {
            root.digest: _BranchRecord(root, origin, {origin.digest: initial}, [], ())
        }
        self._baseline = root

    @classmethod
    def open(
        cls,
        *,
        session_id: str,
        seed: int,
        agent_ids: tuple[str, ...],
        policy_ref: str,
        world: ReferenceWorld | None = None,
    ) -> "ReferenceSession":
        world = DelayedCommitmentWorld() if world is None else world
        spec = SessionSpec(
            session_id=session_id,
            backend=REFERENCE_BACKEND,
            scenario_ref=world.scenario_ref,
            config_digest=content_digest("experiment.reference-config", world.config_payload()),
            seed=seed,
            agent_ids=agent_ids,
            evidence_label=world.evidence_label,
        )
        return cls(spec, policy_ref, world)

    @property
    def spec(self) -> SessionSpec:
        return self._spec

    @property
    def baseline(self) -> BranchRef:
        return self._baseline

    @property
    def world(self) -> ReferenceWorld:
        return self._world

    def head(self, branch: BranchRef) -> SnapshotRef:
        return self._record(branch).head

    def is_terminated(self, branch: BranchRef) -> bool:
        record = self._record(branch)
        return record.nodes[record.head.digest].terminated

    def trace(self, branch: BranchRef) -> BranchTrace:
        record = self._record(branch)
        return BranchTrace(branch=record.ref, transitions=tuple(record.transitions))

    def branch_return(self, branch: BranchRef) -> float:
        """Undiscounted total reward of the branch, in world points."""

        total = sum(
            reward for item in self._record(branch).transitions for _, reward in item.rewards
        )
        return total / self._world.reward_units_per_point

    def fork(
        self,
        parent: BranchRef,
        snapshot: SnapshotRef,
        *,
        intervention: Mapping[str, str],
        label: str,
    ) -> BranchRef:
        """Start a child branch from a snapshot recorded on ``parent``."""

        record = self._record(parent)
        node = record.nodes.get(snapshot.digest)
        if node is None:
            raise SessionError("snapshot was not recorded on the parent branch")
        if node.terminated:
            raise SessionError("cannot fork from a terminal snapshot")
        pairs = self._action_pairs(intervention, require_all=False)
        child = BranchRef.child(parent, snapshot, intervention=pairs, label=label)
        if child.digest in self._branches:
            raise SessionError("an identical branch already exists")
        self._branches[child.digest] = _BranchRecord(
            child, snapshot, {snapshot.digest: node}, [], pairs
        )
        return child

    def step(
        self,
        branch: BranchRef,
        actions: Mapping[str, str],
        *,
        observation_provenance: str,
    ) -> Transition:
        """Advance one branch by one step; other branches are untouched."""

        record = self._record(branch)
        node = record.nodes[record.head.digest]
        if node.terminated:
            raise SessionError("branch has terminated")
        pairs = self._action_pairs(actions, require_all=True)
        if record.pending_intervention and not set(record.pending_intervention) <= set(pairs):
            raise SessionError("the first branch step must apply the branch intervention")
        state, rewards, terminated = self._world.step(node.state, tuple(name for _, name in pairs))
        successor = _Node(state, node.step + 1, bool(terminated))
        target = self._snapshot(successor)
        transition = Transition(
            branch_digest=record.ref.digest,
            step=node.step,
            source_snapshot_digest=record.head.digest,
            target_snapshot_digest=target.digest,
            actions=pairs,
            rewards=tuple(zip(self._spec.agent_ids, rewards, strict=True)),
            terminated=successor.terminated,
            observation_provenance=observation_provenance,
        )
        record.nodes[target.digest] = successor
        record.transitions.append(transition)
        record.head = target
        record.pending_intervention = ()
        return transition

    def manifest(self) -> TraceManifest:
        return TraceManifest(
            session=self._spec,
            policy_ref=self._policy_ref,
            branches=tuple(self.trace(record.ref) for record in self._branches.values()),
        )

    def _record(self, branch: BranchRef) -> _BranchRecord:
        record = self._branches.get(branch.digest) if isinstance(branch, BranchRef) else None
        if record is None:
            raise SessionError("unknown branch for this session")
        return record

    def _action_pairs(
        self, actions: Mapping[str, str], *, require_all: bool
    ) -> tuple[tuple[str, str], ...]:
        if not isinstance(actions, Mapping):
            raise SessionError("actions must be a mapping of agent id to action name")
        known = set(self._spec.agent_ids)
        given = set(actions)
        if not given <= known or (require_all and given != known) or (not require_all and not given):
            raise SessionError(f"actions must name agents from {self._spec.agent_ids}")
        for name in actions.values():
            if name not in self._world.actions:
                raise SessionError(
                    f"unknown action {name!r}; expected one of {self._world.actions}"
                )
        return tuple((agent, actions[agent]) for agent in self._spec.agent_ids if agent in actions)

    def _snapshot(self, node: _Node) -> SnapshotRef:
        return SnapshotRef(
            session_digest=self._session_digest,
            step=node.step,
            state_digest=content_digest(
                "experiment.reference-state",
                {
                    "world": self._world.encode_state(node.state),
                    "step": node.step,
                    "terminated": node.terminated,
                },
            ),
            event_cursor=node.step,
            rng_digest=self._rng_digest,
        )


__all__ = [
    "ACTIONS",
    "REFERENCE_BACKEND",
    "REFERENCE_SCENARIO",
    "DelayedCommitmentWorld",
    "ReferenceSession",
    "ReferenceWorld",
    "SessionError",
]
