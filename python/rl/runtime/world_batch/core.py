"""WorldBatchCore: stage contracts and execution mode plugin infrastructure.

Defines the batch processing stage contract model per the amended stage
contract model (architecture design doc §6.1) and the execution mode plugin
registry (G5: extension is registration).

Layering (G2): this module sits in the substrate ring and must not import
domain semantics (``gym_envs``) at module scope or inside any method body.
Domain-specific callables (for example the air-combat event-action finalizer)
are injected once at plugin construction by the higher-ring caller.

Hot-path guarantee: plugin resolution and domain-callable injection happen
once at construction; stage-contract validation happens once at import.
The per-step hook bodies contain no imports, no registry lookups, and no
exception-based dispatch (pinned by disassembly tests).

Stage anchors: each declared stage is anchored in
``WorldBatchVecEnv.step_wait`` with a ``# [stage:<name>]`` comment; a source
structure test asserts the anchor sequence equals ``BATCH_STEP_STAGES``
order, keeping the declarations load-bearing instead of decorative.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, ClassVar, Mapping

from python.tasking_contracts.runtime_contract import ScenarioLoaderRuntime


class WorldBatchCore:
    """Measured slice-1 owners shared by the maintained batch modes.

    The first extraction is deliberately data-plane only.  A maintained
    facade observation packet is decoded once here, the evidence metadata
    projection is shared by the single/leader runtime wrappers, and the
    per-loader truth/instrument fields are recorded as a mirror of that
    packet.  Mode-specific episode ownership stays with the existing callers
    and their already-registered ``ExecutionModePlugin`` hooks.

    ``ScenarioLoaderRuntime`` is the I73 structural seam at the loader's
    ``sim`` handle.  ``loader_runtime`` names that boundary without adding a
    new runtime method or bypassing the facade observation-packet path.
    """

    @staticmethod
    def loader_runtime(loader: Any) -> ScenarioLoaderRuntime:
        """Return the typed ``ScenarioLoader.sim`` seam unchanged.

        The maintained proxy is the sole production provider.  Keeping this
        helper as a plain attribute read preserves the old ``AttributeError``
        behavior for malformed test doubles while giving the slice a concrete
        I73-owned return type.
        """

        runtime: ScenarioLoaderRuntime = getattr(loader, "sim")
        return runtime

    @staticmethod
    def extract_observation_batch(
        packet: Any,
        *,
        consumer: str,
        require_payload: bool = True,
        missing_message: str | None = None,
    ) -> tuple[list[Any], list[Any]]:
        """Extract agent-observation and instrument arrays from one packet.

        The facade packet remains the only maintained observation read owner.
        ``require_payload=False`` is reserved for the cooperative reset/read
        compatibility path, whose existing behavior permits an empty packet
        and lets its slot-level caller decide what to do.
        """

        truth_items = list(getattr(packet, "agent_observations", []) or [])
        instrument_items = list(getattr(packet, "instrument_states", []) or [])
        if require_payload and (not truth_items or not instrument_items):
            raise RuntimeError(
                missing_message
                or (
                    f"{consumer} did not return the maintained observation "
                    "packet payload required by its consumers"
                )
            )
        return truth_items, instrument_items

    @staticmethod
    def extract_observation_pair(
        packet: Any,
        *,
        consumer: str,
        missing_message: str | None = None,
    ) -> tuple[Any, Any]:
        """Extract the first truth/instrument pair with fail-closed payload."""

        truth_items, instrument_items = WorldBatchCore.extract_observation_batch(
            packet,
            consumer=consumer,
            missing_message=missing_message,
        )
        return truth_items[0], instrument_items[0]

    @staticmethod
    def record_observation_state(handle: Any, *, truth: Any, inst: Any) -> None:
        """Record the latest packet values on an environment mirror.

        ``handle`` may be a single-world handle, leader handle, or cooperative
        slot state.  Counter advancement and episode/reward ownership remain
        in each caller because those semantics differ between the three modes.
        """

        handle.last_truth = truth
        handle.last_inst = inst

    @staticmethod
    def runtime_window_evidence_info(window_evidence: Any) -> dict[str, Any]:
        """Project maintained window evidence into the existing info shape.

        This is the exact common projection previously duplicated by the
        single-world and leader wrappers.  Missing optional packet members keep
        their historical empty/default values.
        """

        engagement_barrier_id = ""
        if window_evidence.engagement_packet is not None:
            engagement_barrier_id = str(
                getattr(window_evidence.engagement_packet, "barrier_id", "") or ""
            )
        return {
            "barrier_ids": [
                str(getattr(record, "barrier_id", "") or "")
                for record in list(window_evidence.barrier_trace)
            ],
            "event_barrier_id": engagement_barrier_id,
            "observation_barrier_id": str(
                getattr(window_evidence.observation_packet, "barrier_id", "") or ""
            ),
            "observation_provenance": str(
                getattr(
                    getattr(window_evidence.observation_packet, "provenance", None),
                    "source_label",
                    "",
                )
                or ""
            ),
            "engagement_provenance": str(
                getattr(
                    getattr(window_evidence.engagement_packet, "packet_provenance", None),
                    "source_label",
                    "",
                )
                or ""
            ),
            "diagnostics_provenance": str(
                getattr(
                    getattr(window_evidence.engagement_packet, "diagnostics_provenance", None),
                    "source_label",
                    "",
                )
                or ""
            ),
            "cadence_reason": str(window_evidence.cadence_reason),
            "uses_compat_fallback": bool(window_evidence.uses_compat_fallback),
        }


@dataclass(frozen=True)
class SubStage:
    """Event-driven or sub-cadence execution segment inside a stage (§6.1
    ``sub_graph`` entry)."""

    name: str
    semantic_stages: tuple[str, ...]
    clock_domain: str
    read_set: frozenset[str]
    write_set: frozenset[str]


@dataclass(frozen=True)
class StageContract:
    """Batch step stage declaration per the §6.1 stage contract amendment.

    Field mapping to the amendment: ``semantic_stages`` is the amendment's
    ``semantic_stage`` field, tuple-valued here because the measured Python
    step loop contains execution segments that span multiple semantic stages
    (for example ``command_sync`` spans P2/P3 and ``reward_episode`` performs
    P1 world-setup writes through episode autoreset); declaring the span is
    preferred over under-declaring. All stage identifiers use the
    authoritative ``P<n> <Name>`` vocabulary from the design document's
    canonical lifecycle table; information layers use the G4 six-layer
    vocabulary from the same document.
    """

    name: str
    semantic_stages: tuple[str, ...]
    read_set: frozenset[str]
    write_set: frozenset[str]
    clock_domain: str
    information_layer_consumed: tuple[str, ...]
    information_layer_produced: tuple[str, ...]
    extension_points: tuple[str, ...]
    sub_graph: tuple[SubStage, ...] = field(default=())


# Declared in the execution order of the ``WorldBatchVecEnv.step_wait``
# stage anchors (source-structure test enforces the match).
BATCH_STEP_STAGES: tuple[StageContract, ...] = (
    StageContract(
        name="action_prepare",
        semantic_stages=("P4 PlatformControl",),
        read_set=frozenset({
            "policy_action",
            "world_instrument_state",
            "action_gate_state",
            "truth_cache",
        }),
        write_set=frozenset({
            "pilot_action_assignments",
            "action_gate_state",
            "last_action_state",
        }),
        clock_domain="outer_step",
        information_layer_consumed=("Agent Observation",),
        information_layer_produced=(),
        extension_points=(),
    ),
    StageContract(
        name="physics_step",
        semantic_stages=("P5 PhysicsStep",),
        read_set=frozenset({
            "pilot_action_assignments",
            "kernel_command_state",
        }),
        write_set=frozenset({
            "world_truth_state",
            "world_instrument_state",
        }),
        clock_domain="outer_step",
        information_layer_consumed=(),
        information_layer_produced=("World Truth",),
        extension_points=(),
    ),
    StageContract(
        name="state_read",
        semantic_stages=("P10 ObservationExport",),
        read_set=frozenset({
            "world_truth_state",
            "world_instrument_state",
        }),
        write_set=frozenset({
            "truth_cache",
            "instrument_cache",
        }),
        clock_domain="outer_step",
        information_layer_consumed=("World Truth",),
        information_layer_produced=("Agent Observation",),
        extension_points=(),
    ),
    StageContract(
        name="behavior_update",
        semantic_stages=("P2 TaskingIntent",),
        read_set=frozenset({
            "truth_cache",
            "instrument_cache",
            "step_counters",
        }),
        write_set=frozenset({
            "loader_behavior_state",
            "command_chain_state",
            "step_counters",
            "action_gate_state",
        }),
        clock_domain="outer_step",
        information_layer_consumed=("Agent Observation",),
        information_layer_produced=(),
        extension_points=(
            "execution_mode_plugin.finalize_post_step_truth",
            "execution_mode_plugin.update_post_step_behavior",
        ),
    ),
    StageContract(
        name="command_sync",
        semantic_stages=("P2 TaskingIntent", "P3 CommandDelivery"),
        read_set=frozenset({
            "command_chain_state",
            "command_snapshot_cache",
            "truth_cache",
        }),
        write_set=frozenset({
            "kernel_command_state",
            "command_snapshot_cache",
        }),
        clock_domain=(
            "outer_step (post behavior_update); event-driven re-entries on "
            "naval station action mutation and episode autoreset"
        ),
        information_layer_consumed=("Agent Observation",),
        information_layer_produced=(),
        extension_points=(
            "execution_mode_plugin.skip_post_behavior_command_sync",
        ),
    ),
    StageContract(
        name="observation_build",
        semantic_stages=("P10 ObservationExport",),
        read_set=frozenset({
            "truth_cache",
            "instrument_cache",
            "visual_cache",
            "world_visual_state",
            "loader_behavior_state",
        }),
        write_set=frozenset({
            "observation_batch",
            "loader_eval_cache",
            "visual_cache",
            "device_view_cache",
        }),
        clock_domain="outer_step",
        information_layer_consumed=("Agent Observation",),
        information_layer_produced=("Agent Observation",),
        extension_points=(),
        sub_graph=(
            SubStage(
                name="visual_refresh",
                semantic_stages=("P10 ObservationExport",),
                clock_domain="every visual_update_interval outer steps",
                read_set=frozenset({"world_visual_state", "step_counters"}),
                write_set=frozenset({"visual_cache", "device_view_cache"}),
            ),
        ),
    ),
    StageContract(
        name="flight_shaping",
        semantic_stages=("P10 ObservationExport",),
        read_set=frozenset({"loader_eval_cache"}),
        write_set=frozenset({"loader_eval_cache"}),
        clock_domain="outer_step (gpu_host flight-shaping backend only)",
        information_layer_consumed=(),
        information_layer_produced=(),
        extension_points=(),
    ),
    StageContract(
        name="reward_episode",
        semantic_stages=("P10 ObservationExport", "P1 WorldSetup"),
        read_set=frozenset({
            "observation_batch",
            "truth_cache",
            "instrument_cache",
            "loader_eval_cache",
            "loader_behavior_state",
            "step_counters",
            "episode_accounting",
        }),
        write_set=frozenset({
            "reward_buffer",
            "done_buffer",
            "info_buffer",
            "episode_accounting",
            "loader_behavior_state",
            "world_setup_state",
            "truth_cache",
            "instrument_cache",
            "observation_batch",
        }),
        clock_domain=(
            "outer_step; event-driven sub-stages on air-combat hybrid "
            "weapon release and on episode termination/truncation"
        ),
        information_layer_consumed=("Agent Observation",),
        information_layer_produced=(),
        extension_points=(),
        sub_graph=(
            SubStage(
                name="post_launch_assessment",
                semantic_stages=(
                    "P4 PlatformControl",
                    "P5 PhysicsStep",
                    "P10 ObservationExport",
                ),
                clock_domain="event-driven (air-combat hybrid weapon release)",
                read_set=frozenset({
                    "truth_cache",
                    "instrument_cache",
                    "loader_behavior_state",
                    "action_gate_state",
                    "step_counters",
                }),
                write_set=frozenset({
                    "world_truth_state",
                    "world_instrument_state",
                    "truth_cache",
                    "instrument_cache",
                    "kernel_command_state",
                    "loader_behavior_state",
                    "step_counters",
                    "observation_batch",
                }),
            ),
            SubStage(
                name="episode_autoreset",
                semantic_stages=("P1 WorldSetup", "P10 ObservationExport"),
                clock_domain="event-driven (episode termination/truncation)",
                read_set=frozenset({
                    "episode_accounting",
                    "loader_behavior_state",
                }),
                write_set=frozenset({
                    "world_setup_state",
                    "world_truth_state",
                    "world_instrument_state",
                    "truth_cache",
                    "instrument_cache",
                    "observation_batch",
                    "kernel_command_state",
                    "command_snapshot_cache",
                    "loader_behavior_state",
                    "step_counters",
                    "episode_accounting",
                }),
            ),
        ),
    ),
)

BATCH_STEP_STAGE_NAMES: frozenset[str] = frozenset(
    stage.name for stage in BATCH_STEP_STAGES
)


# ---------------------------------------------------------------------------
# Execution mode plugin protocol
# ---------------------------------------------------------------------------

class ExecutionModePlugin:
    """Stage-local adapter for execution-mode-specific batch step behavior.

    Subclasses override the hook methods that differ between execution modes.
    Plugin instances are resolved once at vec-env construction and stored as
    direct attribute references — the hot path never performs registry
    lookups or imports.

    ``stage_bindings`` maps each hook to the stage contract that declares it
    as an extension point; the mapping is validated against
    ``BATCH_STEP_STAGES`` at import time (see
    ``validate_stage_extension_points``).
    """

    mode_name: str = ""

    stage_bindings: ClassVar[Mapping[str, str]] = MappingProxyType({
        "finalize_post_step_truth": "behavior_update",
        "update_post_step_behavior": "behavior_update",
        "skip_post_behavior_command_sync": "command_sync",
    })

    def update_post_step_behavior(
        self,
        handle: Any,
        sim_time: float,
        truth: Any,
        inst: Any,
    ) -> None:
        """behavior_update stage: update loader behaviors after the physics
        step.

        The default calls ``handle.loader.update_behaviors``.
        """
        handle.loader.update_behaviors(
            sim_time, truth=truth, inst=inst, sync_to_kernel=False,
        )

    @property
    def skip_post_behavior_command_sync(self) -> bool:
        """command_sync stage gate: whether the post-behavior command-chain
        sync is owned by the mode.

        When ``True``, the generic step loop skips its own
        ``_sync_command_chain_batch`` call because the mode's reward stage
        handles it.
        """
        return False

    def finalize_post_step_truth(
        self,
        env_idx: int,
        handle: Any,
        truth_before: Any,
    ) -> None:
        """behavior_update stage: called after truth/inst caches are
        refreshed, before the behavior update.

        The execution plugin uses this to finalize air-combat event-action
        info when the action mode is ``air_combat_hybrid``.  The default is
        a no-op.
        """


def validate_stage_extension_points(
    stages: tuple[StageContract, ...],
    hook_stage_bindings: Mapping[str, str],
    plugin_base: type = ExecutionModePlugin,
) -> None:
    """Fail-fast consistency check between stage contracts and plugin hooks.

    Ensures every ``extension_points`` entry on a stage corresponds to
    exactly one plugin hook bound to that stage, and vice versa.  Runs once
    at import — never on the hot path.
    """
    declared: dict[str, str] = {}
    for stage in stages:
        for point in stage.extension_points:
            if point in declared:
                raise ValueError(
                    f"extension point {point!r} declared by multiple stages: "
                    f"{declared[point]!r} and {stage.name!r}"
                )
            declared[point] = stage.name

    stage_names = {stage.name for stage in stages}
    unknown_stages = set(hook_stage_bindings.values()) - stage_names
    if unknown_stages:
        raise ValueError(
            f"plugin stage_bindings reference undeclared stages: "
            f"{sorted(unknown_stages)}"
        )

    missing_hooks = [
        hook for hook in hook_stage_bindings if not hasattr(plugin_base, hook)
    ]
    if missing_hooks:
        raise ValueError(
            f"plugin stage_bindings reference missing hooks: {missing_hooks}"
        )

    expected = {
        f"execution_mode_plugin.{hook}": stage_name
        for hook, stage_name in hook_stage_bindings.items()
    }
    if declared != expected:
        raise ValueError(
            f"stage extension_points {declared!r} do not match plugin "
            f"stage_bindings {expected!r}"
        )


validate_stage_extension_points(
    BATCH_STEP_STAGES, ExecutionModePlugin.stage_bindings,
)


# ---------------------------------------------------------------------------
# Plugin registry (G5)
# ---------------------------------------------------------------------------

_execution_mode_registry: dict[str, Callable[..., ExecutionModePlugin]] = {}


def register_execution_mode(
    name: str,
    factory: Callable[..., ExecutionModePlugin],
) -> None:
    """Register an execution mode plugin factory.

    Raises ``ValueError`` on duplicate registration (fail-fast, G5).
    """
    if name in _execution_mode_registry:
        raise ValueError(
            f"execution mode {name!r} is already registered; "
            f"registered modes: {sorted(_execution_mode_registry)}"
        )
    _execution_mode_registry[name] = factory


def resolve_execution_mode(name: str, **kwargs: Any) -> ExecutionModePlugin:
    """Resolve a registered execution mode plugin by name.

    Raises ``ValueError`` when *name* has not been registered (fail-fast).
    """
    factory = _execution_mode_registry.get(name)
    if factory is None:
        raise ValueError(
            f"unknown execution mode {name!r}; "
            f"registered modes: {sorted(_execution_mode_registry)}"
        )
    return factory(**kwargs)


def registered_execution_modes() -> list[str]:
    """Return a sorted list of currently registered mode names."""
    return sorted(_execution_mode_registry)


# ---------------------------------------------------------------------------
# Standard execution plugin
# ---------------------------------------------------------------------------

class StandardExecutionPlugin(ExecutionModePlugin):
    """Execution-mode plugin for single-agent WorldBatchVecEnv.

    All configuration (including the domain-owned air-combat event finalizer
    callable) is injected once at construction.  The per-step hook bodies
    perform attribute reads and direct calls only — no imports, no dict
    lookups, no exception control flow.
    """

    mode_name = "execution"

    def __init__(
        self,
        *,
        is_air_combat_hybrid: bool = False,
        air_combat_event_finalizer: Callable[..., Any] | None = None,
    ) -> None:
        self._is_air_combat_hybrid: bool = bool(is_air_combat_hybrid)
        if self._is_air_combat_hybrid and not callable(air_combat_event_finalizer):
            raise ValueError(
                "air_combat_hybrid execution mode requires an injected "
                "air_combat_event_finalizer callable (resolved once at "
                "construction; core must not import domain modules)"
            )
        self._air_combat_event_finalizer = air_combat_event_finalizer

    def finalize_post_step_truth(
        self,
        env_idx: int,
        handle: Any,
        truth_before: Any,
    ) -> None:
        # Parity with the pre-extraction inline code: for hybrid action modes
        # the finalizer is called unconditionally each step; it accepts and
        # handles truth_before=None itself.
        if self._is_air_combat_hybrid:
            self._air_combat_event_finalizer(
                handle.loader,
                truth_before=truth_before,
                truth_after=handle.last_truth,
            )


def _standard_execution_factory(**kwargs: Any) -> StandardExecutionPlugin:
    return StandardExecutionPlugin(**kwargs)


register_execution_mode("execution", _standard_execution_factory)


# ---------------------------------------------------------------------------
# Cooperative execution plugin
# ---------------------------------------------------------------------------

class CooperativePlugin(ExecutionModePlugin):
    """Execution-mode plugin consumed by ``CooperativeWorldBatchVecEnv``.

    Resolved once at vec-env construction via ``resolve_execution_mode("cooperative")``.
    The cooperative step loop routes its per-slot behavior-update call through
    ``update_post_step_behavior`` and gates the post-behavior command-chain sync
    on ``skip_post_behavior_command_sync``.

    All hooks equal the base-class defaults: cooperative semantics require plain
    ``update_behaviors`` (never ``update_command_chain_only``), always sync the
    command chain after behavior updates, and have no ``finalize_post_step_truth``
    decision point (the constructor rejects air-combat hybrid action modes).
    """

    mode_name = "cooperative"


def _cooperative_factory(**_kwargs: Any) -> CooperativePlugin:
    return CooperativePlugin()


register_execution_mode("cooperative", _cooperative_factory)


# ---------------------------------------------------------------------------
# Leader execution plugin
# ---------------------------------------------------------------------------

class LeaderPlugin(ExecutionModePlugin):
    """Execution-mode plugin consumed by ``LeaderWorldBatchExecutionRuntimeGroup``.

    Resolved once at group construction via ``resolve_execution_mode("leader")``.
    The leader group routes its per-env behavior-update call through
    ``update_post_step_behavior`` and gates the post-behavior command-chain sync
    on ``skip_post_behavior_command_sync``.

    All hooks equal the base-class defaults: the leader group's own decision
    points are structurally identical to the base behavior (plain
    ``update_behaviors``, always sync, no finalizer).  The inner
    ``WorldBatchVecEnv`` that owns the physics step has its own
    ``StandardExecutionPlugin`` for execution-mode-specific routing
    (air-combat hybrid finalization).
    """

    mode_name = "leader"


def _leader_factory(**_kwargs: Any) -> LeaderPlugin:
    return LeaderPlugin()


register_execution_mode("leader", _leader_factory)


__all__ = [
    "BATCH_STEP_STAGE_NAMES",
    "BATCH_STEP_STAGES",
    "CooperativePlugin",
    "ExecutionModePlugin",
    "LeaderPlugin",
    "StageContract",
    "StandardExecutionPlugin",
    "SubStage",
    "WorldBatchCore",
    "register_execution_mode",
    "registered_execution_modes",
    "resolve_execution_mode",
    "validate_stage_extension_points",
]
