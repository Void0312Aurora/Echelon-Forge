"""Runtime-candidate session adapter with an explicit native branch seam.

This module is the bounded P3 runtime adapter. It owns no runtime state and
imports no runtime, gym, or binding package. A backend owns
the authoritative world and supplies identity facts before and after each
step; this adapter only validates those facts and projects them into the
experiment-layer contracts.

The route is deliberately narrower than :class:`ReferenceSession`:

* setup/step identity and transition provenance are recorded;
* sibling fork is enabled only when a backend exposes the native branch seam;
* saved native checkpoints restore into fresh continuation branches;
* a backend that omits or contradicts state identity is rejected rather than
  replaced with a Python-generated pseudo-snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Mapping, Protocol, Sequence

from python.experiment.contracts import BranchRef
from python.experiment.contracts import POLICY_INPUT_PROVENANCE_LABELS
from python.experiment.contracts import SessionSpec
from python.experiment.contracts import SnapshotRef
from python.experiment.contracts import Transition
from python.experiment.contracts import content_digest
from python.experiment.trace import BranchTrace
from python.experiment.trace import TraceManifest


RUNTIME_CANDIDATE_BACKEND = "runtime_candidate"


class RuntimeCandidateError(RuntimeError):
    """Raised when a candidate operation or backend result is inadmissible."""


@dataclass(frozen=True)
class RuntimeSnapshotFacts:
    """Identity facts produced by the authoritative backend.

    The adapter accepts facts but never constructs a state payload.  The
    backend must advance ``step`` exactly once for each accepted transition.
    """

    step: int
    state_digest: str
    event_cursor: int
    rng_digest: str
    terminated: bool = False


@dataclass(frozen=True)
class RuntimeStepResult:
    """One backend step result with post-step identity facts."""

    snapshot: RuntimeSnapshotFacts
    rewards: Mapping[str, int]


@dataclass(frozen=True)
class RuntimeNativeBranchAdmission:
    """Native branch admission facts plus an opaque backend-owned child handle."""

    snapshot: RuntimeSnapshotFacts
    handle: object


class RuntimeCandidateBackend(Protocol):
    """Minimal owner-facing backend seam for the P3-A selected slice."""

    def initial_snapshot(self) -> RuntimeSnapshotFacts: ...

    def current_snapshot(self) -> RuntimeSnapshotFacts:
        """Live native identity of the baseline world, read without side effects."""
        ...

    def step(self, actions: tuple[tuple[str, str], ...]) -> RuntimeStepResult: ...


class RuntimeNativeBranchBackend(Protocol):
    """Optional native sibling branch surface.

    The backend owns the branch handle and all state-transfer authority. The
    experiment layer only receives a child identity and feeds later actions
    back through that handle.
    """

    def fork_branch(
        self,
        snapshot: RuntimeSnapshotFacts,
        intervention: tuple[tuple[str, str], ...],
        label: str,
        horizon: int,
    ) -> RuntimeNativeBranchAdmission: ...

    def step_branch(
        self, handle: object, actions: tuple[tuple[str, str], ...]
    ) -> RuntimeStepResult: ...


class RuntimeNativeCheckpointBackend(RuntimeNativeBranchBackend, Protocol):
    """Optional native checkpoint/descendant seam; handles never carry Python state."""

    def checkpoint_branch(
        self, handle: object | None, snapshot: RuntimeSnapshotFacts
    ) -> RuntimeNativeBranchAdmission: ...

    def fork_from_branch(
        self,
        handle: object,
        snapshot: RuntimeSnapshotFacts,
        intervention: tuple[tuple[str, str], ...],
        label: str,
        horizon: int,
    ) -> RuntimeNativeBranchAdmission: ...


class RuntimeAgentObservationRefBackend(Protocol):
    """Optional owner seam for the current Agent's maintained observation refs."""

    supports_agent_observation_refs: bool

    def observation_refs(self, handle: object | None = None) -> Mapping[str, object]: ...


class RuntimeAgentObservationPacketBackend(Protocol):
    """Optional owner seam for reading packets from a selected branch handle."""

    def observation_packet_reader(self, handle: object | None = None) -> object: ...


class RuntimeKernelCandidateBackend:
    """Maintained Python adapter for the bound native kernel candidate.

    The object passed to this adapter is the
    ``ef_runtime_candidate_py.RuntimeKernelCandidate``
    binding. State identity, RNG position, event ordering, and sibling storage
    all remain native; this class only hashes action envelopes and projects the
    returned native facts into the experiment contracts.
    """

    def __init__(self, native_candidate: object, agent_ids: tuple[str, ...]) -> None:
        self._native = native_candidate
        self._agent_ids = tuple(agent_ids)
        start = getattr(native_candidate, "start", None)
        if not callable(start) or not bool(start()):
            raise RuntimeCandidateError("native kernel candidate failed to start")

    def initial_snapshot(self) -> RuntimeSnapshotFacts:
        return self._facts(getattr(self._native, "snapshot_facts")())

    def current_snapshot(self) -> RuntimeSnapshotFacts:
        return self._facts(getattr(self._native, "snapshot_facts")())

    def branch_snapshot(self, handle: object) -> RuntimeSnapshotFacts:
        return self._facts(getattr(handle, "snapshot_facts")())

    @property
    def agent_ids(self) -> tuple[str, ...]:
        return self._agent_ids

    @property
    def supports_fork(self) -> bool:
        return callable(getattr(self._native, "fork_native", None))

    @property
    def supports_checkpoints(self) -> bool:
        return callable(getattr(self._native, "checkpoint_native", None))

    def step(self, actions: tuple[tuple[str, str], ...]) -> RuntimeStepResult:
        if not bool(getattr(self._native, "step_native")(self._action_digest(actions))):
            raise RuntimeCandidateError("native kernel candidate rejected episode step")
        return RuntimeStepResult(
            snapshot=self.initial_snapshot(),
            rewards={agent_id: 0 for agent_id, _ in actions},
        )

    def fork_branch(
        self,
        snapshot: RuntimeSnapshotFacts,
        intervention: tuple[tuple[str, str], ...],
        label: str,
        horizon: int,
    ) -> RuntimeNativeBranchAdmission:
        current = self.initial_snapshot()
        if current != snapshot:
            raise RuntimeCandidateError("native kernel parent snapshot changed before fork")
        branch = getattr(self._native, "fork_native")(
            self._intervention_digest(intervention, label, horizon), horizon
        )
        if branch is None or not bool(getattr(branch, "valid")()):
            raise RuntimeCandidateError("native kernel sibling branch admission was rejected")
        return RuntimeNativeBranchAdmission(
            snapshot=self._facts(getattr(branch, "snapshot_facts")()), handle=branch
        )

    def checkpoint_branch(
        self, handle: object | None, snapshot: RuntimeSnapshotFacts
    ) -> RuntimeNativeBranchAdmission:
        source = self._native if handle is None else handle
        if self._facts(getattr(source, "snapshot_facts")()) != snapshot:
            raise RuntimeCandidateError("native checkpoint source snapshot changed")
        method = "checkpoint_native" if handle is None else "checkpoint"
        checkpoint = getattr(source, method)()
        return self._admission(checkpoint, snapshot)

    def fork_from_branch(
        self,
        handle: object,
        snapshot: RuntimeSnapshotFacts,
        intervention: tuple[tuple[str, str], ...],
        label: str,
        horizon: int,
    ) -> RuntimeNativeBranchAdmission:
        if self._facts(getattr(handle, "snapshot_facts")()) != snapshot:
            raise RuntimeCandidateError("native branch source snapshot changed")
        child = getattr(handle, "fork_native")(
            self._intervention_digest(intervention, label, horizon), horizon
        )
        return self._admission(child, snapshot)

    def _admission(
        self, handle: object, snapshot: RuntimeSnapshotFacts
    ) -> RuntimeNativeBranchAdmission:
        if handle is None or not bool(getattr(handle, "valid")()):
            raise RuntimeCandidateError("native checkpoint or descendant admission was rejected")
        facts = self._facts(getattr(handle, "snapshot_facts")())
        if facts != snapshot:
            raise RuntimeCandidateError("native clone changed the source state identity")
        return RuntimeNativeBranchAdmission(snapshot=facts, handle=handle)

    def step_branch(
        self, handle: object, actions: tuple[tuple[str, str], ...]
    ) -> RuntimeStepResult:
        if not bool(getattr(handle, "step")(self._action_digest(actions))):
            raise RuntimeCandidateError("native kernel sibling branch rejected episode step")
        return RuntimeStepResult(
            snapshot=self._facts(getattr(handle, "snapshot_facts")()),
            rewards={agent_id: 0 for agent_id, _ in actions},
        )

    @staticmethod
    def _facts(value: object) -> RuntimeSnapshotFacts:
        try:
            facts = RuntimeSnapshotFacts(
                step=int(getattr(value, "step")),
                state_digest=str(getattr(value, "state_digest")),
                event_cursor=int(getattr(value, "event_cursor")),
                rng_digest=str(getattr(value, "rng_digest")),
                terminated=bool(getattr(value, "terminated")),
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise RuntimeCandidateError("native kernel returned incomplete snapshot facts") from exc
        if len(facts.state_digest) != 64 or len(facts.rng_digest) != 64:
            raise RuntimeCandidateError("native kernel returned malformed snapshot digests")
        return facts

    @staticmethod
    def _action_digest(actions: tuple[tuple[str, str], ...]) -> str:
        return content_digest(
            "experiment.runtime-native-action",
            {"actions": [[agent_id, action] for agent_id, action in actions]},
        )

    @staticmethod
    def _intervention_digest(
        intervention: tuple[tuple[str, str], ...], label: str, horizon: int
    ) -> str:
        return content_digest(
            "experiment.runtime-native-intervention",
            {
                "intervention": [[agent_id, action] for agent_id, action in intervention],
                "label": label,
                "horizon": horizon,
            },
        )


@dataclass(frozen=True)
class RuntimeCandidateCapabilities:
    """Capabilities advertised by this bounded adapter."""

    can_step: bool = True
    can_snapshot_restore: bool = False
    can_fork: bool = False
    can_agent_observation_refs: bool = False
    evidence_label: str = "runtime_candidate"


@dataclass
class _Checkpoint:
    snapshot: SnapshotRef
    facts: RuntimeSnapshotFacts
    handle: object


@dataclass
class _BranchState:
    ref: BranchRef
    head: SnapshotRef
    facts: RuntimeSnapshotFacts
    handle: object | None
    transitions: list[Transition]
    pending_intervention: tuple[tuple[str, str], ...] = ()
    terminated: bool = False
    # Set when the native world advanced but the step could not be recorded;
    # the branch's trace no longer describes its native state.
    poisoned: str | None = None
    checkpoints: dict[str, _Checkpoint] = field(default_factory=dict)


class RuntimeCandidateSession:
    """Validate and record a runtime candidate and any admitted native siblings."""

    def __init__(
        self,
        *,
        session_id: str,
        backend_id: str,
        scenario_ref: str,
        config_digest: str,
        seed: int,
        agent_ids: tuple[str, ...],
        policy_ref: str,
        backend: RuntimeCandidateBackend,
    ) -> None:
        backend_digest = getattr(backend, "config_digest", config_digest)
        if backend_digest != config_digest:
            raise RuntimeCandidateError("session config digest differs from backend protocol")
        if getattr(backend, "agent_ids", agent_ids) != agent_ids:
            raise RuntimeCandidateError("session agents differ from backend protocol")
        self._backend = backend
        self._policy_ref = policy_ref
        fork_method = getattr(backend, "fork_branch", None)
        step_branch_method = getattr(backend, "step_branch", None)
        self._native_branch_backend = (
            backend
            if callable(fork_method)
            and callable(step_branch_method)
            and getattr(backend, "supports_fork", True)
            else None
        )
        self._native_checkpoint_backend = (
            backend
            if self._native_branch_backend is not None
            and callable(getattr(backend, "checkpoint_branch", None))
            and callable(getattr(backend, "fork_from_branch", None))
            and getattr(backend, "supports_checkpoints", True)
            else None
        )
        observation_refs_method = getattr(backend, "observation_refs", None)
        self._agent_observation_ref_backend = (
            backend
            if callable(observation_refs_method)
            and getattr(backend, "supports_agent_observation_refs", True)
            else None
        )
        self._capabilities = RuntimeCandidateCapabilities(
            can_fork=self._native_branch_backend is not None,
            can_snapshot_restore=self._native_checkpoint_backend is not None,
            can_agent_observation_refs=self._agent_observation_ref_backend is not None,
        )
        self._spec = SessionSpec(
            session_id=session_id,
            backend=backend_id,
            scenario_ref=scenario_ref,
            config_digest=config_digest,
            seed=seed,
            agent_ids=agent_ids,
            evidence_label="runtime_candidate",
        )
        initial_facts = backend.initial_snapshot()
        initial = self._snapshot_from_facts(initial_facts, expected_step=0)
        if initial.step != 0:
            raise RuntimeCandidateError("backend initial snapshot must be at step 0")
        self._baseline = BranchRef.root(initial)
        self._branches: dict[str, _BranchState] = {
            self._baseline.digest: _BranchState(
                ref=self._baseline,
                head=initial,
                facts=initial_facts,
                handle=None,
                transitions=[],
            )
        }
        self._agent_observation_refs: dict[str, dict[str, list[object]]] = {}
        self._agent_observation_packets: dict[str, dict[str, list[object]]] = {}
        if self._agent_observation_ref_backend is not None:
            self._capture_agent_observation_refs(self._branches[self._baseline.digest])

    @property
    def spec(self) -> SessionSpec:
        return self._spec

    @property
    def baseline(self) -> BranchRef:
        return self._baseline

    @property
    def capabilities(self) -> RuntimeCandidateCapabilities:
        return self._capabilities

    @property
    def has_agent_observation_refs(self) -> bool:
        """Whether the owner supplied maintained refs for Agent packet reads."""

        return self._agent_observation_ref_backend is not None

    def agent_observation_ref_series(
        self, agent_id: str, branch: BranchRef | None = None
    ) -> tuple[object, ...]:
        """Return the explicit ref sequence for one Agent and one branch."""

        if not isinstance(agent_id, str) or agent_id not in self._spec.agent_ids:
            raise RuntimeCandidateError("unknown Agent for observation ref series")
        record = self._record(branch or self._baseline)
        values = self._agent_observation_refs.get(record.ref.digest)
        if values is None or agent_id not in values:
            raise RuntimeCandidateError(
                "runtime candidate has no maintained Agent observation ref source"
            )
        return tuple(values[agent_id])

    def agent_observation_ref_sources(
        self,
        agent_id: str,
        branches: Sequence[BranchRef] | None = None,
    ) -> dict[tuple[str, str], tuple[object, ...]]:
        """Join the current manifest identity to explicit Agent ref series.

        This is a collection boundary only. Callers still choose which keys
        enter :func:`collect_agent_observation_sources` and later learner
        export; the session never exports every branch implicitly.
        """

        selected = tuple(branches) if branches is not None else tuple(
            item.ref for item in self._branches.values()
        )
        manifest_digest = self.manifest().digest
        return {
            (manifest_digest, branch.digest): self.agent_observation_ref_series(agent_id, branch)
            for branch in selected
        }

    def agent_observation_packet_series(
        self, agent_id: str, branch: BranchRef | None = None
    ) -> tuple[object, ...]:
        """Return packets captured at each branch endpoint by the owner."""

        if not isinstance(agent_id, str) or agent_id not in self._spec.agent_ids:
            raise RuntimeCandidateError("unknown Agent for observation packet series")
        record = self._record(branch or self._baseline)
        values = self._agent_observation_packets.get(record.ref.digest)
        if values is None or agent_id not in values:
            raise RuntimeCandidateError(
                "runtime candidate has no maintained Agent observation packet source"
            )
        return tuple(values[agent_id])

    def agent_observation_packet_sources(
        self,
        agent_id: str,
        branches: Sequence[BranchRef] | None = None,
    ) -> dict[tuple[str, str], tuple[object, ...]]:
        """Join selected branch identity to packets captured at each endpoint."""

        if not isinstance(agent_id, str) or agent_id not in self._spec.agent_ids:
            raise RuntimeCandidateError("unknown Agent for observation packet sources")
        selected = tuple(branches) if branches is not None else tuple(
            item.ref for item in self._branches.values()
        )
        manifest_digest = self.manifest().digest
        sources: dict[tuple[str, str], tuple[object, ...]] = {}
        for branch in selected:
            sources[(manifest_digest, branch.digest)] = self.agent_observation_packet_series(
                agent_id, branch
            )
        return sources

    def head(self, branch: BranchRef | None = None) -> SnapshotRef:
        """Return the current backend-owned head for the selected branch."""

        return self._record(branch or self._baseline).head

    def step(
        self,
        actions: Mapping[str, str],
        *,
        observation_provenance: str,
    ) -> Transition:
        """Apply one action through the backend and append a validated transition."""

        return self._step(self._baseline, actions, observation_provenance)

    def step_branch(
        self,
        branch: BranchRef,
        actions: Mapping[str, str],
        *,
        observation_provenance: str,
    ) -> Transition:
        """Advance a native sibling branch through its opaque backend handle."""

        if branch == self._baseline:
            return self.step(actions, observation_provenance=observation_provenance)
        return self._step(branch, actions, observation_provenance)

    def _step(
        self,
        branch: BranchRef,
        actions: Mapping[str, str],
        observation_provenance: str,
    ) -> Transition:
        return self._advance(self._record(branch), actions, observation_provenance)

    def _advance(
        self,
        record: _BranchState,
        actions: Mapping[str, str],
        observation_provenance: str,
    ) -> Transition:
        if record.poisoned is not None:
            raise RuntimeCandidateError(f"runtime candidate branch is unusable: {record.poisoned}")
        if record.terminated:
            raise RuntimeCandidateError("runtime candidate branch has terminated")
        if observation_provenance not in POLICY_INPUT_PROVENANCE_LABELS:
            raise RuntimeCandidateError(
                f"observation provenance {observation_provenance!r} is not admitted"
            )
        required_provenance = getattr(self._backend, "required_observation_provenance", None)
        if required_provenance is not None and observation_provenance != required_provenance:
            raise RuntimeCandidateError("observation provenance differs from backend protocol")
        pairs = self._action_pairs(actions)
        if record.pending_intervention and not set(record.pending_intervention) <= set(pairs):
            raise RuntimeCandidateError("the first branch step must apply the branch intervention")
        # The transition records ``record.head`` as its source, so the native
        # state must still be exactly that one. A spawn or time-step change
        # outside the session would otherwise be attributed to the wrong state.
        live = self._current_facts(record)
        if live is not None and live != record.facts:
            raise RuntimeCandidateError(
                "native state changed outside the session before this step"
            )
        if record.handle is None:
            result = self._backend.step(pairs)
        else:
            if self._native_branch_backend is None:
                raise RuntimeCandidateError("runtime native branch capability is unavailable")
            result = self._native_branch_backend.step_branch(record.handle, pairs)
        # The native world has advanced from here on. Build the whole record,
        # including every Agent observation, before changing session state; if
        # any part fails, the branch can no longer be trusted, so poison it
        # instead of reporting the step as not applied.
        try:
            if not isinstance(result, RuntimeStepResult):
                raise RuntimeCandidateError("backend must return RuntimeStepResult")
            target = self._snapshot_from_facts(
                result.snapshot, expected_step=record.head.step + 1
            )
            rewards = self._reward_pairs(result.rewards)
            transition = Transition(
                branch_digest=record.ref.digest,
                step=record.head.step,
                source_snapshot_digest=record.head.digest,
                target_snapshot_digest=target.digest,
                actions=pairs,
                rewards=rewards,
                terminated=result.snapshot.terminated,
                observation_provenance=observation_provenance,
            )
            captured = self._read_agent_observations(record)
        except Exception as exc:
            record.poisoned = (
                f"step {record.head.step} advanced natively but was not recorded ({exc})"
            )
            raise RuntimeCandidateError(
                f"{record.poisoned}; the branch must be discarded"
            ) from exc
        record.head = target
        record.facts = result.snapshot
        record.terminated = result.snapshot.terminated
        record.pending_intervention = ()
        record.transitions.append(transition)
        self._record_agent_observations(record.ref.digest, captured)
        return transition

    def trace(self, branch: BranchRef) -> BranchTrace:
        record = self._record(branch)
        return BranchTrace(branch=record.ref, transitions=tuple(record.transitions))

    def checkpoint(self, branch: BranchRef | None = None) -> SnapshotRef:
        """Retain an immutable native clone of a running branch's current head.

        Only explicitly saved heads can be restored after the branch advances.
        The selected native producer requires an accepted action boundary.
        """

        if self._native_checkpoint_backend is None:
            raise RuntimeCandidateError("runtime candidate does not support snapshot restore")
        record = self._record(branch or self._baseline)
        if record.terminated:
            raise RuntimeCandidateError("cannot checkpoint a terminal snapshot")
        if record.head.digest not in record.checkpoints:
            admission = self._native_checkpoint_backend.checkpoint_branch(
                record.handle, record.facts
            )
            self._validate_admission(admission, record.facts)
            record.checkpoints[record.head.digest] = _Checkpoint(
                record.head, record.facts, admission.handle
            )
        return record.head

    def manifest(self) -> TraceManifest:
        """Return the current trace projection, including admitted siblings."""

        return TraceManifest(
            session=self._spec,
            policy_ref=self._policy_ref,
            branches=tuple(
                BranchTrace(branch=item.ref, transitions=tuple(item.transitions))
                for item in self._branches.values()
            ),
        )

    def fork(
        self,
        parent: BranchRef,
        snapshot: SnapshotRef,
        *,
        intervention: Mapping[str, str],
        label: str,
        horizon: int = 1,
    ) -> BranchRef:
        """Fork from the current head or an explicitly saved native checkpoint."""

        record = self._fork_record(parent, snapshot, intervention, label, horizon)
        self._publish_branch(record)
        return record.ref

    def _fork_record(
        self,
        parent: BranchRef,
        snapshot: SnapshotRef,
        intervention: Mapping[str, str],
        label: str,
        horizon: int,
        *,
        require_checkpoint: bool = False,
    ) -> _BranchState:
        if self._native_branch_backend is None:
            raise RuntimeCandidateError("runtime candidate does not support branch fork")
        record = self._record(parent)
        if not isinstance(snapshot, SnapshotRef):
            raise RuntimeCandidateError("snapshot must be a SnapshotRef")
        saved = record.checkpoints.get(snapshot.digest)
        if saved is not None and saved.snapshot != snapshot:
            raise RuntimeCandidateError("checkpoint snapshot identity changed")
        if saved is None:
            if require_checkpoint or snapshot != record.head:
                raise RuntimeCandidateError("snapshot was not checkpointed on the parent branch")
            if record.terminated:
                raise RuntimeCandidateError("cannot fork from a terminal snapshot")
        pairs = self._action_pairs(intervention, require_all=False)
        if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 1:
            raise RuntimeCandidateError("native branch horizon must be a positive integer")
        child = BranchRef.child(record.ref, snapshot, intervention=pairs, label=label)
        if child.digest in self._branches:
            raise RuntimeCandidateError("native backend returned a duplicate branch identity")
        facts = saved.facts if saved is not None else record.facts
        handle = saved.handle if saved is not None else record.handle
        if handle is None:
            admission = self._native_branch_backend.fork_branch(facts, pairs, label, horizon)
        else:
            method = getattr(self._native_branch_backend, "fork_from_branch", None)
            if not callable(method):
                raise RuntimeCandidateError("runtime backend does not support descendant fork")
            admission = method(handle, facts, pairs, label, horizon)
        self._validate_admission(admission, facts)
        return _BranchState(
            ref=child,
            head=snapshot,
            facts=admission.snapshot,
            handle=admission.handle,
            transitions=[],
            pending_intervention=pairs,
        )

    @staticmethod
    def _validate_admission(
        admission: RuntimeNativeBranchAdmission, facts: RuntimeSnapshotFacts
    ) -> None:
        if not isinstance(admission, RuntimeNativeBranchAdmission) or admission.handle is None:
            raise RuntimeCandidateError("native branch admission returned incomplete facts")
        if not isinstance(admission.snapshot, RuntimeSnapshotFacts):
            raise RuntimeCandidateError("native branch admission returned invalid snapshot facts")
        if admission.snapshot != facts:
            raise RuntimeCandidateError("native branch admission changed the parent state identity")

    def restore(
        self,
        snapshot: SnapshotRef,
        *,
        parent: BranchRef | None = None,
        intervention: Mapping[str, str] | None = None,
        label: str = "restore",
        horizon: int = 1,
    ) -> BranchRef:
        """Restore a saved checkpoint into a new branch; retain the original trace.

        The caller explicitly supplies the continuation's first-step actions.
        Rewinding an existing trace would invalidate its recorded descendants.
        """

        if self._native_checkpoint_backend is None:
            raise RuntimeCandidateError("runtime candidate does not support snapshot restore")
        if intervention is None:
            raise RuntimeCandidateError("restore requires an explicit first-step intervention")
        record = self._fork_record(
            parent or self._baseline,
            snapshot,
            intervention,
            label,
            horizon,
            require_checkpoint=True,
        )
        self._publish_branch(record)
        return record.ref

    def replay(self, parent: BranchRef, snapshot: SnapshotRef, *, label: str) -> BranchRef:
        """Verify the recorded suffix on a fresh native clone before publishing it.

        Every action, reward, state/event/RNG identity, provenance and terminal
        flag must match. On failure the private replay child is discarded.
        """

        if self._native_checkpoint_backend is None:
            raise RuntimeCandidateError("runtime candidate does not support snapshot restore")
        record = self._record(parent)
        if not isinstance(snapshot, SnapshotRef) or snapshot.digest not in record.checkpoints:
            raise RuntimeCandidateError("snapshot was not checkpointed on the parent branch")
        expected = tuple(item for item in record.transitions if item.step >= snapshot.step)
        if not expected or expected[0].source_snapshot_digest != snapshot.digest:
            raise RuntimeCandidateError("checkpoint has no recorded continuation to replay")
        replay = self._fork_record(
            parent,
            snapshot,
            dict(expected[0].actions),
            label,
            len(expected),
            require_checkpoint=True,
        )
        try:
            self._capture_agent_observation_refs(replay)
            for item in expected:
                actual = self._advance(replay, dict(item.actions), item.observation_provenance)
                if replace(actual, branch_digest=item.branch_digest) != item:
                    raise RuntimeCandidateError(f"native replay diverged at step {item.step}")
        except BaseException:
            # A discarded replay must not leave observations behind: a retry
            # with the same label has the same digest and would append to them.
            self._discard_observations(replay.ref.digest)
            raise
        self._branches[replay.ref.digest] = replay
        return replay.ref

    def _current_facts(self, record: _BranchState) -> RuntimeSnapshotFacts | None:
        """Read the live native identity of ``record`` from its owner.

        Returns ``None`` only when the owner exposes no live identity read for
        this kind of branch; native backends implement ``current_snapshot`` and
        ``branch_snapshot``.
        """

        if record.handle is None:
            reader = getattr(self._backend, "current_snapshot", None)
            args: tuple[object, ...] = ()
        else:
            reader = getattr(self._native_branch_backend, "branch_snapshot", None)
            args = (record.handle,)
        if not callable(reader):
            return None
        try:
            facts = reader(*args)
        except RuntimeCandidateError:
            raise
        except Exception as exc:
            raise RuntimeCandidateError("native identity owner could not report facts") from exc
        if not isinstance(facts, RuntimeSnapshotFacts):
            raise RuntimeCandidateError("native identity owner returned invalid facts")
        return facts

    def _publish_branch(self, record: _BranchState) -> None:
        """Capture the new branch's first observation, then register it."""

        try:
            self._capture_agent_observation_refs(record)
        except BaseException:
            self._discard_observations(record.ref.digest)
            raise
        self._branches[record.ref.digest] = record

    def _discard_observations(self, branch_digest: str) -> None:
        self._agent_observation_refs.pop(branch_digest, None)
        self._agent_observation_packets.pop(branch_digest, None)

    def _read_agent_observations(
        self, record: _BranchState
    ) -> tuple[dict[str, object], dict[str, object] | None] | None:
        """Read every Agent's maintained ref and packet without recording them.

        Returns ``None`` when the backend has no observation-ref capability. Any
        failure raises before anything is stored, so a caller can record all
        Agents or none.
        """

        if self._agent_observation_ref_backend is None:
            return None
        try:
            refs = self._agent_observation_ref_backend.observation_refs(record.handle)
        except Exception as exc:
            raise RuntimeCandidateError(
                "maintained Agent observation ref source failed"
            ) from exc
        if not isinstance(refs, Mapping) or set(refs) != set(self._spec.agent_ids):
            raise RuntimeCandidateError(
                "maintained Agent observation refs must cover exactly the session Agents"
            )
        if any(value is None for value in refs.values()):
            raise RuntimeCandidateError("maintained Agent observation ref cannot be None")
        packet_reader_factory = getattr(self._backend, "observation_packet_reader", None)
        if not callable(packet_reader_factory):
            return dict(refs), None
        packets: dict[str, object] = {}
        for agent_id in self._spec.agent_ids:
            try:
                reader = packet_reader_factory(record.handle)
            except Exception as exc:
                raise RuntimeCandidateError(
                    "maintained Agent observation packet reader failed"
                ) from exc
            read_packet = getattr(reader, "read_observation_packet", None)
            if not callable(read_packet):
                raise RuntimeCandidateError(
                    "maintained Agent observation packet reader is incomplete"
                )
            try:
                try:
                    packet = read_packet(
                        [refs[agent_id]],
                        include_agent_observations=True,
                        include_instrument_states=False,
                    )
                except TypeError:
                    packet = read_packet([refs[agent_id]])
            except Exception as exc:
                raise RuntimeCandidateError(
                    "maintained Agent observation packet capture failed"
                ) from exc
            packets[agent_id] = packet
        return dict(refs), packets

    def _record_agent_observations(
        self,
        branch_digest: str,
        captured: tuple[dict[str, object], dict[str, object] | None] | None,
    ) -> None:
        """Append one already-read observation per Agent; cannot fail partway."""

        if captured is None:
            return
        refs, packets = captured
        branch_refs = self._agent_observation_refs.setdefault(branch_digest, {})
        branch_packets = self._agent_observation_packets.setdefault(branch_digest, {})
        for agent_id in self._spec.agent_ids:
            branch_refs.setdefault(agent_id, []).append(refs[agent_id])
            if packets is not None:
                branch_packets.setdefault(agent_id, []).append(packets[agent_id])

    def _capture_agent_observation_refs(self, record: _BranchState) -> None:
        self._record_agent_observations(record.ref.digest, self._read_agent_observations(record))

    def _reward_pairs(self, rewards: Mapping[str, int]) -> tuple[tuple[str, int], ...]:
        if not isinstance(rewards, Mapping) or set(rewards) != set(self._spec.agent_ids):
            raise RuntimeCandidateError("backend rewards must cover exactly the session agents")
        pairs = tuple(sorted(rewards.items()))
        if any(isinstance(value, bool) or not isinstance(value, int) for _, value in pairs):
            raise RuntimeCandidateError("backend rewards must be integer reward units")
        return pairs

    def _snapshot_from_facts(
        self, facts: RuntimeSnapshotFacts, *, expected_step: int
    ) -> SnapshotRef:
        if not isinstance(facts, RuntimeSnapshotFacts):
            raise RuntimeCandidateError("backend must return RuntimeSnapshotFacts")
        if facts.step != expected_step:
            raise RuntimeCandidateError(
                f"backend snapshot step {facts.step} does not match expected {expected_step}"
            )
        try:
            return SnapshotRef(
                session_digest=self._spec.digest,
                step=facts.step,
                state_digest=facts.state_digest,
                event_cursor=facts.event_cursor,
                rng_digest=facts.rng_digest,
            )
        except (TypeError, ValueError) as exc:
            raise RuntimeCandidateError(f"backend snapshot identity rejected: {exc}") from exc

    def _record(self, branch: BranchRef) -> _BranchState:
        if not isinstance(branch, BranchRef):
            raise RuntimeCandidateError("branch must be a RuntimeCandidate branch reference")
        record = self._branches.get(branch.digest)
        if record is None or record.ref != branch:
            raise RuntimeCandidateError("unknown branch for this runtime candidate session")
        return record

    def _action_pairs(
        self, actions: Mapping[str, str], *, require_all: bool = True
    ) -> tuple[tuple[str, str], ...]:
        if not isinstance(actions, Mapping):
            raise RuntimeCandidateError("actions must be a mapping")
        expected = set(self._spec.agent_ids)
        given = set(actions)
        if require_all and given != expected:
            raise RuntimeCandidateError("actions must cover exactly the session agents")
        if not require_all and (not given or not given <= expected):
            raise RuntimeCandidateError("intervention must name known session agents")
        pairs = tuple(sorted((agent_id, action) for agent_id, action in actions.items()))
        if any(not isinstance(action, str) or not action.strip() for _, action in pairs):
            raise RuntimeCandidateError("actions must contain non-empty strings")
        return pairs


def runtime_config_digest(config_payload: Mapping[str, object]) -> str:
    """Digest a float-free runtime configuration through the shared profile."""

    return content_digest("experiment.runtime-candidate-config", config_payload)


__all__ = [
    "RUNTIME_CANDIDATE_BACKEND",
    "RuntimeCandidateBackend",
    "RuntimeKernelCandidateBackend",
    "RuntimeCandidateCapabilities",
    "RuntimeCandidateError",
    "RuntimeNativeBranchAdmission",
    "RuntimeNativeBranchBackend",
    "RuntimeNativeCheckpointBackend",
    "RuntimeAgentObservationRefBackend",
    "RuntimeCandidateSession",
    "RuntimeSnapshotFacts",
    "RuntimeStepResult",
    "runtime_config_digest",
]
