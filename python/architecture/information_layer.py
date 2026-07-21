"""G4 information-state layer declaration facility (Unified Architecture Program T8).

Kernel Invariant G4 states that "every observation/reward consumer declares its
information-state layer" (architecture design doc §15; layer table in §3). This
module is the lightweight, zero-runtime-overhead mechanism that makes that
declaration load-bearing on the Python-owned maintained surface:

* A maintained consumer declares three module-level constants
  (:data:`REQUIRED_DECLARATION_ATTRS`): ``INFORMATION_LAYER_CONSUMED``,
  ``INFORMATION_LAYER_PRODUCED``, and ``SEMANTIC_STAGE``. Each is a tuple of
  authoritative vocabulary strings. These are plain metadata assignments, so
  there is no per-step or import-time cost beyond the tuple literal.
* :data:`MAINTAINED_INFORMATION_LAYER_CONSUMERS` is the G5-style registry of
  dotted module paths that must carry such a declaration. It is the union of
  :data:`VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS` (consumers whose leaf reads
  now flow through the declared observation view, additionally ban-gated) and
  :data:`DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS` (adjudicated consumers
  that carry a declaration but keep their own reads for now). Extension is
  registration: a later slice converges a deferred consumer by moving its path
  from the deferred tuple into the converged tuple.
* :func:`validate_information_layer_declaration` is the shared checker used by
  the architecture test today, and reusable by a future AST/import gate when G4
  enforcement moves "from documentation to AST gates" (design doc §15).

The vocabularies below are reused verbatim from the I32 stage-contract whitelist
in ``python/rl/runtime/world_batch/core.py`` (pinned by
``tests/world_batch/test_world_batch_core.py``). No new layer or stage name is
invented here; the architecture test cross-checks this module against that
whitelist so drift in either direction fails fast.
"""

from __future__ import annotations

from collections.abc import Sequence


# G4 six-layer information-state vocabulary (architecture design doc §3
# information-state table). Identical to ``_AUTHORITATIVE_INFORMATION_LAYERS`` in
# ``tests/world_batch/test_world_batch_core.py`` and the layer strings declared
# by ``BATCH_STEP_STAGES`` in ``python/rl/runtime/world_batch/core.py``.
AUTHORITATIVE_INFORMATION_LAYERS: frozenset[str] = frozenset({
    "World Truth",
    "Sensed State",
    "Track State",
    "Shared Tactical Picture",
    "Agent Observation",
    "Decision Belief",
})

# Canonical P0-P10 semantic-stage vocabulary (architecture design doc §6),
# reused by the ``SEMANTIC_STAGE`` declaration. Identical to
# ``_AUTHORITATIVE_SEMANTIC_STAGES`` in ``tests/world_batch/test_world_batch_core.py``.
CANONICAL_SEMANTIC_STAGES: frozenset[str] = frozenset({
    "P0 ContentCompile",
    "P1 WorldSetup",
    "P2 TaskingIntent",
    "P3 CommandDelivery",
    "P4 PlatformControl",
    "P5 PhysicsStep",
    "P6 SenseTrackLink",
    "P7 FireControlLaunch",
    "P8 MunitionLifecycle",
    "P9 EffectsDamage",
    "P10 ObservationExport",
})

# Module-level constant names every maintained consumer must declare.
REQUIRED_DECLARATION_ATTRS: tuple[str, ...] = (
    "INFORMATION_LAYER_CONSUMED",
    "INFORMATION_LAYER_PRODUCED",
    "SEMANTIC_STAGE",
)

# Consumers whose leaf reads flow through the declared observation view: the
# eight migrated in the second slice (§6 -- the V4/V5/V6 census consumers, the
# own-ship reward-input builders they sit beside, and the two repair-round
# additions: active universal policy-observation assembly and the waypoint
# reward-input builder), plus the leader decision-runtime observation producer
# migrated in the T8 third-slice repair round (I56 §7.5) after the independent
# review disproved its deferral rationale -- its own-ship x/y reads are
# token-isomorphic to own_ship_field, and numeric parity with the fae17eb8
# baseline is pinned by tests/leader/test_leader_observation_view_parity.py.
# These are the ban-gated set (no raw World-Truth reads may remain).
_VIEW_CONVERGED_CONSUMERS: tuple[str, ...] = (
    "gym_envs.scenario_loader.mission_observation",
    "gym_envs.scenario_loader.reward_runtime.air_combat",
    "gym_envs.scenario_loader.reward_runtime.naval",
    "gym_envs.scenario_loader.reward_runtime.safety",
    "gym_envs.scenario_loader.reward_runtime.shaping_inputs",
    "gym_envs.scenario_loader.reward_runtime.objectives",
    "gym_envs.universal_env_parts.observations",
    "gym_envs.scenario_loader.navigation_runtime.waypoint_rewards",
    "gym_envs.leader_env_parts.decision_runtime.observations",
)

# T8 third slice (I56): the deferred aggregator/leader/guidance consumers, now
# adjudicated and each carrying a G4 declaration but keeping their own reads.
# They are declaration-gated (they appear in MAINTAINED_INFORMATION_LAYER_CONSUMERS
# below) but NOT ban-gated (their raw truth reads are intentional and not yet
# view-converged). The adjudication (see t8_g4_truth_leak_inventory.md §7):
#   * step_evaluation / execution mainline -- stage-bundling orchestrators whose
#     own-ship reads feed reward/observation input-DTO assembly; declared, not
#     migrated (orchestrators bundling DTOs, not leaf observation reads).
#   * python.rl.tasking.leader_tasking -- the scripted C2/leader director
#     (maintained doctrine). Declaring it is neutral (python.architecture), but
#     migration is forbidden: routing its reads through gym_envs.observation_view
#     would introduce a python.rl -> gym_envs reverse dependency.
#   * navigation_runtime.guidance -- the shared route-guidance helper spanning
#     command-delivery (autopilot target) and reward support; migration deferred
#     until a command/guidance read owner exists (an observation view is not the
#     right owner for command-delivery reads).
DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS: tuple[str, ...] = (
    "gym_envs.scenario_loader.step_evaluation",
    "gym_envs.scenario_loader.execution_runtime.mainline",
    "python.rl.tasking.leader_tasking",
    "gym_envs.scenario_loader.navigation_runtime.guidance",
)

# G5 registry: every maintained observation/reward consumer that carries a G4
# declaration. It is the union of the view-converged consumers (ban-gated) and
# the declared-but-deferred consumers (declaration-gated only). The declaration
# gate checks every entry here; the truth-read-ban gate checks only the converged
# subset. Extension is registration: a later slice converges a deferred consumer
# by moving its path out of DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS into
# the converged tuple (this union is unchanged).
MAINTAINED_INFORMATION_LAYER_CONSUMERS: tuple[str, ...] = (
    *_VIEW_CONVERGED_CONSUMERS,
    *DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS,
)

# T8 second slice (declaration-view convergence). The declared observation-view
# owner module is the layer-tagged read owner that legitimately performs the raw
# World-Truth / Track-State / Shared-Tactical-Picture / engagement-evidence reads
# on behalf of the migrated consumers (it consumes truth and produces the policy
# observation read faces). It carries its own G4 declaration and is the sole
# whitelist for the truth-read-ban gate: a declared read owner may read truth,
# the consumers may not. Per G2 the owner sits at the gym_envs parent-package
# layer -- the common lower layer of both consumer subpackages (scenario_loader
# and universal_env_parts) -- so neither takes a lateral sibling import.
MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS: tuple[str, ...] = (
    "gym_envs.observation_view",
)

# Consumers migrated onto the declared observation view. The G4 truth-read-ban
# gate forbids raw World-Truth attribute reads (``truth.<attr>`` and
# ``getattr(truth, ...)``) in each of these modules, since their leaf reads flow
# through MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS. The eight first/second-slice
# consumers plus the leader observation producer converged in the I56 repair
# round. A later slice converges another declared-but-deferred consumer by
# moving its path from the deferred tuple into the converged tuple.
VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS: tuple[str, ...] = _VIEW_CONVERGED_CONSUMERS


def validate_information_layer_declaration(
    *,
    consumed: Sequence[str],
    produced: Sequence[str],
    semantic_stage: Sequence[str],
    consumer: str = "<consumer>",
) -> list[str]:
    """Return a list of human-readable violations for one G4 declaration.

    An empty list means the declaration is well-formed: both layer tuples use
    only :data:`AUTHORITATIVE_INFORMATION_LAYERS`, ``SEMANTIC_STAGE`` uses only
    :data:`CANONICAL_SEMANTIC_STAGES`, and the consumer names at least one
    consumed or produced layer and at least one semantic stage. Pure function,
    no imports or runtime state — safe to call from an AST gate.
    """
    violations: list[str] = []

    for label, values in (
        ("INFORMATION_LAYER_CONSUMED", consumed),
        ("INFORMATION_LAYER_PRODUCED", produced),
    ):
        if not isinstance(values, tuple):
            violations.append(
                f"{consumer}: {label} must be a tuple, got {type(values).__name__}"
            )
            continue
        for layer in values:
            if layer not in AUTHORITATIVE_INFORMATION_LAYERS:
                violations.append(
                    f"{consumer}: {label} uses non-authoritative information layer {layer!r}"
                )

    if isinstance(consumed, tuple) and isinstance(produced, tuple) and not consumed and not produced:
        violations.append(
            f"{consumer}: must declare at least one consumed or produced information layer"
        )

    if not isinstance(semantic_stage, tuple):
        violations.append(
            f"{consumer}: SEMANTIC_STAGE must be a tuple, got {type(semantic_stage).__name__}"
        )
    else:
        for stage in semantic_stage:
            if stage not in CANONICAL_SEMANTIC_STAGES:
                violations.append(
                    f"{consumer}: SEMANTIC_STAGE uses non-canonical semantic stage {stage!r}"
                )
        if not semantic_stage:
            violations.append(
                f"{consumer}: SEMANTIC_STAGE must declare at least one canonical semantic stage"
            )

    return violations


# T8 fourth slice (I60): the C++ runtime facade now exports a declared
# ObservationViewSpec for the TL13 maintained observation seam
# (RuntimeFacade::describe_maintained_observation_view). The two helpers below let
# the G4 facility cross-check that C++ export against the Python single source of
# truth (gym_envs/observation_view.py), so mirroring the layer strings into C++
# cannot silently drift. This is opt-in: nothing in the maintained runtime calls
# them, and the ef_py import is function-local so this module stays import-time
# stdlib-only (the AST G4 gates keep running without a build).

# Attribute names of the structural-fact ObservationViewSpec fields the C++ export
# fills (mirrors the I60 append-only schema fields).
OBSERVATION_VIEW_EXPORT_LAYER_ATTRS: tuple[str, ...] = (
    "information_layer_produced",
    "information_layer_consumed",
    "semantic_stage",
)


def read_maintained_observation_view_export() -> dict[str, object]:
    """Read the C++ facade's declared maintained-observation-view export (opt-in).

    Returns a plain dict of the structural facts the export carries:
    ``schema_version`` / ``view_id`` (str) and ``information_layer_produced`` /
    ``information_layer_consumed`` / ``semantic_stage`` (tuple[str, ...]).

    Imports are function-local so this module stays import-time stdlib-only.
    Raises ``ImportError`` when no local ``ef_py`` build is available; callers
    (e.g. the G4 export-parity architecture test) skip in that case.
    """
    from python.runtime_bootstrap import configure_repo_imports

    configure_repo_imports()
    import ef_py  # noqa: PLC0415  (function-local by design; keeps module stdlib-only)

    spec = ef_py.RuntimeFacade(0).describe_maintained_observation_view()
    return {
        "schema_version": str(spec.schema_version),
        "view_id": str(spec.view_id),
        "information_layer_produced": tuple(spec.information_layer_produced),
        "information_layer_consumed": tuple(spec.information_layer_consumed),
        "semantic_stage": tuple(spec.semantic_stage),
    }


def observation_view_export_parity_violations(
    export: dict[str, object],
    *,
    expected_view_id: str,
    expected_consumed: Sequence[str],
    expected_produced: Sequence[str],
    expected_semantic_stage: Sequence[str],
) -> list[str]:
    """Return violations comparing a C++ export against the Python registry.

    Pure function (no imports, no runtime state): it takes both the C++ export
    (from :func:`read_maintained_observation_view_export`) and the authoritative
    Python-registry declaration and checks that (a) the export is well-formed G4
    vocabulary and (b) it equals the registry declaration exactly (order
    included). An empty list means the C++ mirror and the Python single source of
    truth agree, so the mirror has not drifted.
    """
    violations: list[str] = []

    export_view_id = export.get("view_id")
    if export_view_id != expected_view_id:
        violations.append(
            f"view_id drift: C++ export {export_view_id!r} != registry {expected_view_id!r}"
        )

    export_consumed = tuple(export.get("information_layer_consumed", ()))
    export_produced = tuple(export.get("information_layer_produced", ()))
    export_semantic_stage = tuple(export.get("semantic_stage", ()))

    # (a) the export must itself be a well-formed G4 declaration.
    violations.extend(
        validate_information_layer_declaration(
            consumed=export_consumed,
            produced=export_produced,
            semantic_stage=export_semantic_stage,
            consumer="RuntimeFacade.describe_maintained_observation_view",
        )
    )

    # (b) the export must equal the Python registry declaration exactly.
    for label, exported, expected in (
        ("INFORMATION_LAYER_CONSUMED", export_consumed, tuple(expected_consumed)),
        ("INFORMATION_LAYER_PRODUCED", export_produced, tuple(expected_produced)),
        ("SEMANTIC_STAGE", export_semantic_stage, tuple(expected_semantic_stage)),
    ):
        if exported != expected:
            violations.append(
                f"{label} drift: C++ export {exported!r} != registry {expected!r}"
            )

    return violations


__all__ = [
    "AUTHORITATIVE_INFORMATION_LAYERS",
    "CANONICAL_SEMANTIC_STAGES",
    "DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS",
    "MAINTAINED_INFORMATION_LAYER_CONSUMERS",
    "MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS",
    "OBSERVATION_VIEW_EXPORT_LAYER_ATTRS",
    "REQUIRED_DECLARATION_ATTRS",
    "VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS",
    "observation_view_export_parity_violations",
    "read_maintained_observation_view_export",
    "validate_information_layer_declaration",
]
