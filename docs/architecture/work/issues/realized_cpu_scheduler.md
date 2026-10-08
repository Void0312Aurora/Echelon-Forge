# Realized CPU scheduler diagnostics (#127)

The v1 `executable_graph_sha256` remains the identity of **declarative admission
metadata**. It does not attest to Flecs execution. Its frozen 90 component,
3 kernel factory and 35 default factory checks remain in force.

`RuntimeCompositionEvidenceResult.cpu_scheduler_topology_json` supplies one
runtime-derived snapshot per world, with a separately versioned
`echelon_forge.cpu_scheduler_topology.v1` structural SHA-256. It records:

- Every system actually installed by each admitted factory, including kernel
  pre-update nodes and factories that install multiple nodes.
- All installed system paths, queries, execution flags, disabled state and
  recursive `DependsOn` relationships. Anonymous Flecs phase-chain entities are
  represented by dependency structure rather than allocation IDs.
- Candidate order read from the **existing current pipeline query**, without
  progressing the world. Empty-query systems remain candidates. The separate
  active list excludes `EcsEmpty` and is outside the structural digest, since
  entity population changes query applicability.

This supplement is excluded from sealed v1 evidence and its compatibility
comparison. Consumers needing scheduler fidelity must compare its `sha256`
separately. A phase-only mutation preserves the old declaration hash and changes
the scheduler digest; native mutation tests enforce that distinction. This is a
topology snapshot, not a callback execution trace or a complete behavior proof.

## Meaning of each order

`legacy.stage.NN`, `stage_order`, and `after_contribution_id` describe factory
admission order. Their `after` relation is **advisory for execution** unless a
realized phase/dependency or a behavior test establishes the causal edge. A
factory ordinal is neither a Flecs phase nor a producer provenance identifier.

Normal `ecs.progress` places `ClearForces` in `OnLoad`, before `FlightControl`
in `OnUpdate`, despite the opposite factory admission order. Clearing discards
the previous frame's force and torque accumulators before new forces are built.
The bounded test proves this clearing on a force-only entity through both normal
progress and selected exact trace.

The exact-stage inventory is a separately selected set, manually executed with
`ecs_run`. Its trace indices govern that path only. The shared clear-before-
control edge agrees with normal phases; the entire world is **not** claimed
equivalent because the selected trace omits other systems. No pipeline order,
live scheduling policy or replay identity is changed by these diagnostics.
