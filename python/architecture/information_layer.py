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
  dotted module paths that must carry such a declaration. Extension is
  registration: a later T8 slice migrates one more consumer by adding its
  declaration and appending its path here.
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

# G5 registry: dotted module paths of maintained observation/reward consumers
# that carry a G4 declaration. This is the first-slice set: the V4/V5/V6 census
# consumers and the own-ship reward-input builders they sit beside, plus the two
# repair-round additions the first-slice census missed — the active universal
# policy-observation assembly path (called by CooperativeWorldBatchVecEnv /
# MultiAgentWorldRuntimeView) and the waypoint reward-input builder. Later T8
# slices append the deferred aggregators (step_evaluation, execution mainline,
# leader tasking, route-guidance helper) once their epistemic layer is
# adjudicated rather than forced.
MAINTAINED_INFORMATION_LAYER_CONSUMERS: tuple[str, ...] = (
    "gym_envs.scenario_loader.mission_observation",
    "gym_envs.scenario_loader.reward_runtime.air_combat",
    "gym_envs.scenario_loader.reward_runtime.naval",
    "gym_envs.scenario_loader.reward_runtime.safety",
    "gym_envs.scenario_loader.reward_runtime.shaping_inputs",
    "gym_envs.scenario_loader.reward_runtime.objectives",
    "gym_envs.universal_env_parts.observations",
    "gym_envs.scenario_loader.navigation_runtime.waypoint_rewards",
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

# Consumers migrated onto the declared observation view this slice. The G4
# truth-read-ban gate forbids raw World-Truth attribute reads (``truth.<attr>``
# and ``getattr(truth, ...)``) in each of these modules, since their leaf reads
# now flow through MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS. This slice migrates
# all eight declared consumers, so the converged set equals the declared-consumer
# registry; a later slice that declares further consumers may migrate them
# incrementally and split this set out.
VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS: tuple[str, ...] = (
    MAINTAINED_INFORMATION_LAYER_CONSUMERS
)


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


__all__ = [
    "AUTHORITATIVE_INFORMATION_LAYERS",
    "CANONICAL_SEMANTIC_STAGES",
    "MAINTAINED_INFORMATION_LAYER_CONSUMERS",
    "MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS",
    "REQUIRED_DECLARATION_ATTRS",
    "VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS",
    "validate_information_layer_declaration",
]
