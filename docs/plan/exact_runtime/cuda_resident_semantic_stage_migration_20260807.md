# CUDA Resident Semantic Stage Migration

Language:

- English canonical: `cuda_resident_semantic_stage_migration_20260807.md`
- Chinese companion: [cuda_resident_semantic_stage_migration_20260807.zh.md](cuda_resident_semantic_stage_migration_20260807.zh.md)

Status: active migration record, 2026-08-07.

## Scope

The CUDA-resident runtime remains a separate backend. This migration changes
names that describe its private execution graph; it does not replace Flecs
types one by one, add a second public facade, or change the backend-selection
contract.

Primary source paths, kernels, state fields, resource queries, diagnostics, and
maintained navigation use capability names. Historical fixture identifiers and
serialized provenance values are compatibility data and are not silently
rewritten.

## Semantic Mapping

| Semantic primary name | Compatibility definition | Capability |
| --- | --- | --- |
| `control_preparation` | `Phase A` means the legacy control-preparation alias; `phase_a` is its identifier form | filter and publish pilot controls |
| `flight_dynamics` | `Phase B` means the legacy flight-dynamics alias; `phase_b` is its identifier form | compute forces, aerodynamics, and state integration |
| `observation_projection` | `Phase D` means the legacy observation-projection alias; `phase_d` is its identifier form | project instruments, observations, rewards, and episode state |

## Reader And Writer Inventory

The active writers are the CUDA world-store kernels and snapshot projection in
`src/runtime/facade/internal/cuda_resident/`. Active readers are the resident
backend, replay projection, native CUDA tests, architecture contract tests, and
performance probes.

The following values remain compatibility aliases because they can occur in
stored fixtures or evidence:

| Compatibility value | Semantic replacement |
| --- | --- |
| `cuda_resident.phase_a.direct_pilot.v1` | control-preparation fixture schema |
| `cuda_resident.phase_b.airframe_dynamics.v1` | flight-dynamics fixture schema |
| `cuda_resident.phase_d.projection.v1` | observation-projection fixture schema |
| `cuda_resident.rb5_phase_a` | Means the legacy control-preparation backend identity |
| `cuda_resident.rb6_phase_b` | Means the legacy flight-dynamics backend identity |
| `cuda_resident.rb7_phase_d` | Means the legacy observation-projection backend identity |
| `cuda_resident.rb6.explicit_device_reconstruction` | Means the fixed-air snapshot v2 provenance |
| `cuda_resident.rb7.explicit_phase_d_projection` | Means the fixed-air snapshot v3 provenance |
| `cuda_resident.rb7.explicit_d2d_ownership_copy` | Means the device-observation view v1 provenance |

## Transition And Removal Conditions

This slice performs a direct rename for private implementation symbols and
source paths because every in-repository reader and writer is updated together.
No legacy forwarding API is added.

Serialized fixture and provenance values remain read/write compatible. They may
be removed only after a versioned successor exists, readers accept both forms,
writers have emitted the semantic form for a declared support window, and the
old-form compatibility tests can be retired. Until then, production declarations
that expose those exact values must carry `internal-code: compatibility` when
they are edited.

Historical plans and test file names may retain their original labels when they
are needed to locate old evidence. New runtime interfaces and new tests must use
the semantic names above.

The frozen kernel-resource evidence contract and its captured JSON retain their
original kernel identifiers and symbol hashes. They describe a historical
binary, not the renamed current source. A fresh resource claim requires a new
schema version and a new capture; the existing probe must fail closed on the old
trace signature rather than relabeling historical evidence.

## Size Boundary

Every changed implementation module remains below 1000 physical lines. The
oversized parity-budget contract is outside this slice and must be split before
its remaining internal-code identifiers are changed.
