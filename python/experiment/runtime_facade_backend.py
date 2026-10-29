"""Fail-closed experiment backend for the maintained ``RuntimeFacadeAdapter``.

The adapter invokes an explicit maintained setup callback once, dispatches
actions through an explicit maintained callback, owns one ``step_batch``
boundary, and reads packets through maintained Agent refs. Native identity is
read from the bound facade's ``native_snapshot_facts`` method unless a test or
specialized owner is injected.

The adapter enables native branch/checkpoint methods only when the caller
provides an explicit Agent-action owner for the opaque child. The C++ facade
owns state transfer and stable entity handles; this module only translates
session actions into caller-owned native assignments.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Protocol

from python.experiment.runtime_candidate import (
    RuntimeNativeBranchAdmission,
    RuntimeCandidateError,
    RuntimeSnapshotFacts,
    RuntimeStepResult,
)
from python.experiment.contracts import content_digest
from python.tasking_contracts.common.agent_contracts import OBS_FACADE_OBSERVATION_PACKET
from python.experiment.runtime_facade_observation import RuntimeFacadeAgentObservationProvider


class RuntimeFacadeIdentityOwner(Protocol):
    """Native owner of the complete identity for the maintained facade world."""

    def snapshot_facts(self) -> RuntimeSnapshotFacts: ...


class RuntimeFacadeNativeIdentityOwner:
    """Reads authoritative identity facts from the maintained C++ facade."""

    def __init__(self, runtime: object, world_index: int = 0) -> None:
        self._runtime = runtime
        self._world_index = world_index

    def snapshot_facts(self) -> RuntimeSnapshotFacts:
        value = getattr(self._runtime, "native_snapshot_facts")(self._world_index)
        return RuntimeSnapshotFacts(
            step=int(getattr(value, "step")),
            state_digest=str(getattr(value, "state_digest")),
            event_cursor=int(getattr(value, "event_cursor")),
            rng_digest=str(getattr(value, "rng_digest")),
            terminated=bool(getattr(value, "terminated")),
        )


ActionApplier = Callable[[object, tuple[tuple[str, str], ...]], None]
BranchActionApplier = Callable[[object, tuple[tuple[str, str], ...]], Sequence[object]]
BranchRefFactory = Callable[[object, str, object], object]
SetupApplier = Callable[[object], Mapping[str, object]]
RewardReader = Callable[
    [object, tuple[tuple[str, str], ...], RuntimeSnapshotFacts, RuntimeSnapshotFacts],
    Mapping[str, int],
]


class RuntimeFacadeCandidateBackend:
    """Project one maintained facade world into the runtime-candidate contract.

    ``setup_applier`` performs maintained setup once and returns exactly one
    ref per session Agent. ``action_applier`` translates experiment actions
    into maintained facade assignments. The backend calls
    ``RuntimeFacadeAdapter.step_batch`` exactly once per accepted transition.
    ``identity_owner`` reads authoritative state identity before and after it.
    """

    required_observation_provenance = OBS_FACADE_OBSERVATION_PACKET
    supports_fork = False
    supports_checkpoints = False
    supports_agent_observation_refs = True

    def __init__(
        self,
        runtime: object,
        *,
        agent_ids: tuple[str, ...],
        setup_applier: SetupApplier,
        action_applier: ActionApplier,
        branch_action_applier: BranchActionApplier | None = None,
        branch_ref_factory: BranchRefFactory | None = None,
        world_index: int = 0,
        identity_owner: RuntimeFacadeIdentityOwner | None = None,
        reward_reader: RewardReader,
        config_digest: str | None = None,
    ) -> None:
        self._validate_runtime(runtime)
        if (
            type(agent_ids) is not tuple
            or not agent_ids
            or any(type(agent_id) is not str or not agent_id for agent_id in agent_ids)
            or len(set(agent_ids)) != len(agent_ids)
        ):
            raise RuntimeCandidateError("RuntimeFacade Agent ids must be unique and non-empty")
        if not callable(setup_applier):
            raise RuntimeCandidateError("RuntimeFacade setup applier must be callable")
        if not callable(action_applier):
            raise RuntimeCandidateError("RuntimeFacade action applier must be callable")
        if branch_action_applier is not None and not callable(branch_action_applier):
            raise RuntimeCandidateError("RuntimeFacade branch action applier must be callable")
        if branch_ref_factory is not None and not callable(branch_ref_factory):
            raise RuntimeCandidateError("RuntimeFacade branch ref factory must be callable")
        if identity_owner is None and not callable(getattr(runtime, "native_snapshot_facts", None)):
            raise RuntimeCandidateError(
                "RuntimeFacade backend requires native_snapshot_facts binding"
            )
        if identity_owner is not None and not callable(getattr(identity_owner, "snapshot_facts", None)):
            raise RuntimeCandidateError(
                "RuntimeFacade backend requires a native identity owner"
            )
        if not callable(reward_reader):
            raise RuntimeCandidateError("RuntimeFacade reward reader must be callable")
        if config_digest is not None and (type(config_digest) is not str or not config_digest):
            raise RuntimeCandidateError("RuntimeFacade config digest must be a non-empty string")
        self._runtime = runtime
        if isinstance(world_index, bool) or not isinstance(world_index, int) or world_index < 0:
            raise RuntimeCandidateError("RuntimeFacade world index must be a non-negative integer")
        self._world_index = world_index
        self._agent_ids = agent_ids
        self._action_applier = action_applier
        self._branch_action_applier = branch_action_applier
        self._branch_ref_factory = branch_ref_factory
        self._identity_owner = identity_owner or RuntimeFacadeNativeIdentityOwner(runtime)
        self._reward_reader = reward_reader
        try:
            agent_refs = setup_applier(runtime)
        except Exception as exc:
            raise RuntimeCandidateError("maintained RuntimeFacade setup was rejected") from exc
        if not isinstance(agent_refs, Mapping) or set(agent_refs) != set(agent_ids):
            raise RuntimeCandidateError(
                "RuntimeFacade setup must return exactly one maintained ref per Agent"
            )
        if any(agent_refs[agent_id] is None for agent_id in agent_ids):
            raise RuntimeCandidateError("RuntimeFacade setup returned an empty Agent ref")
        stable_agent_refs = dict(agent_refs)
        self._observation_provider = RuntimeFacadeAgentObservationProvider(
            runtime,
            lambda handle, agent_id: stable_agent_refs[agent_id]
            if handle is None or self._branch_ref_factory is None
            else self._branch_ref_factory(handle, agent_id, stable_agent_refs[agent_id]),
            agent_ids,
        )
        if config_digest is not None:
            # RuntimeCandidateSession binds this optional owner-supplied
            # protocol digest when present; otherwise it uses its own digest.
            self.config_digest = config_digest
        self._last_facts: RuntimeSnapshotFacts | None = None

    @property
    def supports_fork(self) -> bool:
        return self._branch_action_applier is not None and callable(
            getattr(self._runtime, "fork_native_branch", None)
        )

    @property
    def supports_checkpoints(self) -> bool:
        return self.supports_fork

    @staticmethod
    def _validate_runtime(runtime: object) -> None:
        if not callable(getattr(runtime, "apply_world_setup", None)):
            raise RuntimeCandidateError(
                "RuntimeFacade backend requires maintained setup bindings"
            )
        if not callable(getattr(runtime, "step_batch", None)):
            raise RuntimeCandidateError(
                "RuntimeFacade backend requires maintained step bindings"
            )
        capabilities = getattr(runtime, "capabilities", None)
        if callable(capabilities):
            capabilities = capabilities()
        has_observation_request = callable(getattr(runtime, "read_observation_packet", None)) or callable(
            getattr(runtime, "export_observation_packet", None)
        )
        if capabilities is not None and hasattr(capabilities, "has_observation_batch_request"):
            has_observation_request = bool(capabilities.has_observation_batch_request)
        if not has_observation_request:
            raise RuntimeCandidateError(
                "RuntimeFacade backend requires maintained observation request bindings"
            )
        has_packet = callable(getattr(runtime, "read_observation_packet", None)) or callable(
            getattr(runtime, "export_observation_packet", None)
        )
        if capabilities is not None and hasattr(capabilities, "has_export_observation_packet"):
            has_packet = bool(capabilities.has_export_observation_packet)
        if not has_packet:
            raise RuntimeCandidateError(
                "RuntimeFacade backend requires maintained observation packet bindings"
            )

    @property
    def agent_ids(self) -> tuple[str, ...]:
        return self._agent_ids

    def initial_snapshot(self) -> RuntimeSnapshotFacts:
        facts = self._read_facts()
        if facts.step != 0:
            raise RuntimeCandidateError(
                "RuntimeFacade identity owner must start at step 0"
            )
        self._last_facts = facts
        return facts

    def step(self, actions: tuple[tuple[str, str], ...]) -> RuntimeStepResult:
        pairs = tuple(actions)
        if (
            len(pairs) != len(self._agent_ids)
            or any(
                type(pair) is not tuple
                or len(pair) != 2
                or type(pair[0]) is not str
                or type(pair[1]) is not str
                or not pair[0]
                or not pair[1]
                for pair in pairs
            )
            or {agent_id for agent_id, _ in pairs} != set(self._agent_ids)
        ):
            raise RuntimeCandidateError(
                "RuntimeFacade action set must cover exactly the session Agents"
            )
        pairs = tuple(sorted(pairs))
        if self._last_facts is None:
            raise RuntimeCandidateError("RuntimeFacade backend was stepped before initialization")
        before = self._read_facts()
        if before != self._last_facts:
            raise RuntimeCandidateError(
                "RuntimeFacade native state changed outside the session step boundary"
            )
        try:
            self._action_applier(self._runtime, pairs)
            self._runtime.step_batch()
        except Exception as exc:
            raise RuntimeCandidateError(
                "maintained RuntimeFacade action or step was rejected"
            ) from exc
        after = self._read_facts()
        if after.step != before.step + 1:
            raise RuntimeCandidateError(
                "RuntimeFacade identity owner did not advance exactly one step"
            )
        try:
            rewards = self._reward_reader(self._runtime, pairs, before, after)
        except Exception as exc:
            raise RuntimeCandidateError(
                "maintained RuntimeFacade reward reader failed"
            ) from exc
        if not isinstance(rewards, Mapping) or set(rewards) != set(self._agent_ids):
            raise RuntimeCandidateError(
                "RuntimeFacade reward reader must cover exactly the session Agents"
            )
        self._last_facts = after
        return RuntimeStepResult(snapshot=after, rewards=dict(rewards))

    def fork_branch(
        self,
        snapshot: RuntimeSnapshotFacts,
        intervention: tuple[tuple[str, str], ...],
        label: str,
        horizon: int,
    ) -> RuntimeNativeBranchAdmission:
        if not self.supports_fork:
            raise RuntimeCandidateError(
                "RuntimeFacade native branch requires an explicit branch action owner"
            )
        current = self._read_facts()
        if current != snapshot:
            raise RuntimeCandidateError("RuntimeFacade parent snapshot changed before fork")
        child = self._fork_native(self._intervention_digest(intervention, label, horizon), horizon)
        return self._admission(child, snapshot)

    def step_branch(
        self, handle: object, actions: tuple[tuple[str, str], ...]
    ) -> RuntimeStepResult:
        if not self.supports_fork:
            raise RuntimeCandidateError("RuntimeFacade native branch capability is unavailable")
        before = self._branch_facts(handle)
        try:
            assignments = self._branch_action_applier(handle, actions)  # type: ignore[misc]
            if isinstance(assignments, (str, bytes)) or not isinstance(assignments, Sequence):
                raise RuntimeCandidateError(
                    "RuntimeFacade branch action owner must return native assignments"
                )
            if len(assignments) != len(self._agent_ids):
                raise RuntimeCandidateError(
                    "RuntimeFacade branch action owner must return one assignment per Agent"
                )
            if not bool(getattr(handle, "step_pilot_actions")(list(assignments))):
                raise RuntimeCandidateError("RuntimeFacade native branch rejected episode step")
        except RuntimeCandidateError:
            raise
        except Exception as exc:
            raise RuntimeCandidateError(
                "RuntimeFacade branch action translation or step was rejected"
            ) from exc
        after = self._branch_facts(handle)
        if after.step != before.step + 1:
            raise RuntimeCandidateError(
                "RuntimeFacade native branch did not advance exactly one step"
            )
        try:
            rewards = self._reward_reader(handle, actions, before, after)
        except Exception as exc:
            raise RuntimeCandidateError("maintained RuntimeFacade branch reward reader failed") from exc
        if not isinstance(rewards, Mapping) or set(rewards) != set(self._agent_ids):
            raise RuntimeCandidateError(
                "RuntimeFacade branch reward reader must cover exactly the session Agents"
            )
        return RuntimeStepResult(snapshot=after, rewards=dict(rewards))

    def checkpoint_branch(
        self, handle: object | None, snapshot: RuntimeSnapshotFacts
    ) -> RuntimeNativeBranchAdmission:
        if not self.supports_checkpoints:
            raise RuntimeCandidateError("RuntimeFacade does not support native checkpoints")
        if handle is None:
            if self._read_facts() != snapshot:
                raise RuntimeCandidateError("RuntimeFacade checkpoint source snapshot changed")
            child = self._fork_native(self._checkpoint_digest(snapshot), 1)
        else:
            if self._branch_facts(handle) != snapshot:
                raise RuntimeCandidateError("RuntimeFacade branch checkpoint source changed")
            child = getattr(handle, "checkpoint")()
        return self._admission(child, snapshot)

    def fork_from_branch(
        self,
        handle: object,
        snapshot: RuntimeSnapshotFacts,
        intervention: tuple[tuple[str, str], ...],
        label: str,
        horizon: int,
    ) -> RuntimeNativeBranchAdmission:
        if not self.supports_fork:
            raise RuntimeCandidateError("RuntimeFacade native branch capability is unavailable")
        if self._branch_facts(handle) != snapshot:
            raise RuntimeCandidateError("RuntimeFacade branch snapshot changed before fork")
        child = getattr(handle, "fork_native_branch")(
            self._intervention_digest(intervention, label, horizon), horizon
        )
        return self._admission(child, snapshot)

    def observation_refs(self, handle: object | None = None) -> Mapping[str, object]:
        return self._observation_provider.observation_refs(handle)

    def observation_packet_reader(self, handle: object | None = None) -> object:
        return self._observation_provider.observation_packet_reader(handle)

    def _fork_native(self, intervention_digest: str, horizon: int) -> object:
        child = getattr(self._runtime, "fork_native_branch")(
            self._world_index, intervention_digest, horizon
        )
        if child is None or not bool(getattr(child, "valid")()):
            raise RuntimeCandidateError("RuntimeFacade native child admission was rejected")
        return child

    @staticmethod
    def _branch_facts(handle: object) -> RuntimeSnapshotFacts:
        try:
            value = getattr(handle, "snapshot_facts")()
            return RuntimeSnapshotFacts(
                step=int(getattr(value, "step")),
                state_digest=str(getattr(value, "state_digest")),
                event_cursor=int(getattr(value, "event_cursor")),
                rng_digest=str(getattr(value, "rng_digest")),
                terminated=bool(getattr(value, "terminated")),
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise RuntimeCandidateError("RuntimeFacade native branch returned incomplete facts") from exc

    @staticmethod
    def _admission(handle: object, snapshot: RuntimeSnapshotFacts) -> RuntimeNativeBranchAdmission:
        if handle is None or not bool(getattr(handle, "valid")()):
            raise RuntimeCandidateError("RuntimeFacade native child admission was rejected")
        facts = RuntimeFacadeCandidateBackend._branch_facts(handle)
        if facts != snapshot:
            raise RuntimeCandidateError("RuntimeFacade native clone changed the source identity")
        return RuntimeNativeBranchAdmission(snapshot=facts, handle=handle)

    @staticmethod
    def _intervention_digest(
        intervention: tuple[tuple[str, str], ...], label: str, horizon: int
    ) -> str:
        return content_digest(
            "experiment.runtime-facade-intervention",
            {"intervention": [[a, v] for a, v in intervention], "label": label, "horizon": horizon},
        )

    @staticmethod
    def _checkpoint_digest(snapshot: RuntimeSnapshotFacts) -> str:
        return content_digest(
            "experiment.runtime-facade-checkpoint",
            {"step": snapshot.step, "state_digest": snapshot.state_digest, "rng_digest": snapshot.rng_digest},
        )

    def _read_facts(self) -> RuntimeSnapshotFacts:
        try:
            facts = self._identity_owner.snapshot_facts()
        except Exception as exc:
            raise RuntimeCandidateError(
                "RuntimeFacade native identity owner failed"
            ) from exc
        if not isinstance(facts, RuntimeSnapshotFacts):
            raise RuntimeCandidateError(
                "RuntimeFacade native identity owner returned incomplete facts"
            )
        if (
            type(facts.step) is not int
            or facts.step < 0
            or type(facts.event_cursor) is not int
            or facts.event_cursor < 0
            or type(facts.terminated) is not bool
        ):
            raise RuntimeCandidateError(
                "RuntimeFacade native identity facts contain invalid counters or status"
            )
        if (
            type(facts.state_digest) is not str
            or type(facts.rng_digest) is not str
            or len(facts.state_digest) != 64
            or len(facts.rng_digest) != 64
            or any(character not in "0123456789abcdef" for character in facts.state_digest)
            or any(character not in "0123456789abcdef" for character in facts.rng_digest)
        ):
            raise RuntimeCandidateError(
                "RuntimeFacade native identity facts contain malformed digests"
            )
        return facts


__all__ = [
    "ActionApplier",
    "BranchActionApplier",
    "BranchRefFactory",
    "RewardReader",
    "RuntimeFacadeCandidateBackend",
    "RuntimeFacadeIdentityOwner",
    "RuntimeFacadeNativeIdentityOwner",
    "SetupApplier",
]
