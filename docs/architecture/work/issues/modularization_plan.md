# System Modularization Issue Plan

Language:
- English canonical: `modularization_plan.md`
- Chinese companion: not maintained (English-only work surface).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/architecture/work/issues/modularization_plan.md`
Owner: `architecture/system-modularization`
Last verified: `2026-08-08`

Status: draft owner-local issue plan based on the current source layout. It is
not a runtime contract or an implementation work package.

## Authorization Boundary

This document does not authorize code moves, directory creation, interface
creation or removal, build changes, runtime behavior changes, or the start of an
implementation task. Each admitted change requires a separately reviewed work
package with exact scope, dependency impact, tests, compatibility behavior, and
acceptance evidence.

## Authority And Evidence Order

This issue is subordinate to the current
[strict simulation-system architecture baseline](../../standards/simulation_system_architecture_design.md).
The baseline defines normative architecture laws, layer ownership, domain
extension admission, and validation gates. The
[Architecture owner README](../../README.md) is the current authority route.

Use the following order when this issue conflicts with another source:

1. the strict architecture baseline for normative architecture laws;
2. current source and executable tests for implemented facts;
3. this draft for candidate gaps and possible sequencing only.

This issue neither amends the strict baseline nor promotes any candidate route
to maintained architecture. Turning a candidate into implementation work must
create a separately authorized scoped package under
`docs/architecture/work/active/`.

## Purpose And Scope

The issue asks a narrower question than the retired legacy page:

`Which remaining ownership and dependency gaps prevent the current modules from
matching the strict architecture baseline?`

It covers:

- verified `src/*/domains/<domain>/` ownership roots;
- existing replaceable-model interfaces and their current composition points;
- the missing Ground system owner;
- dependency rules needed to evaluate later moves.

It does not define a second architecture baseline, a new plugin system, or a
new all-domain runtime stack.

## Verified Current Domain Roots

| Root | Current domain owners | Verified role | Current limitation |
| --- | --- | --- | --- |
| [`src/components/domains/`](../../../../src/components/domains/README.md) | `air`, `naval`, `ground` | Domain-owned ECS data, command/tasking extensions, platform data, and narrow combat/status slices. | Ground is a static G0/G1 command/tasking and placeholder component surface, not full land runtime. |
| [`src/systems/domains/`](../../../../src/systems/domains/README.md) | `air`, `naval` | Released per-tick domain systems for air flight behavior and naval motion/operations. | There is no `src/systems/domains/ground/` owner. |
| [`src/models/domains/`](../../../../src/models/domains/README.md) | `air`, `naval`, `ground` | Domain model implementations, adapters, and explicit placeholder routes consumed by shared defaults. | Ground contains an effects placeholder route, not maintained movement, sensing, fires, damage, or terrain models. |

Shared and transitional roots remain real implementation surfaces:

- `src/components/{combat,command,tasking}` contain shared carriers and
  compatibility aggregations;
- `src/systems/{combat,physics,systems}` contain shared or not-yet-relocated
  system owners;
- `src/models/{core,systems,weapons}` contain the default unit factory, sensor,
  effects, guidance, and related shared implementations.

The existence of a domain directory proves only that a named owner slice
exists. It does not prove equal domain maturity, release a missing system owner,
or authorize moving shared code.

## Existing Replaceable Interfaces

The earlier plan incorrectly described these interfaces as future work. All
three exist in `src/core/interfaces/`, have current implementations, and can be
replaced through `SimulationKernel` setters.

| Interface | Current contract and implementation | Remaining issue |
| --- | --- | --- |
| [`IUnitFactory`](../../../../src/core/interfaces/unit_factory.h) | Resolves `UnitDefinition` records and spawns Flecs entities. [`DefaultUnitFactory`](../../../../src/models/core/default_unit_factory.h) is constructed by `SimulationKernel`; `set_unit_factory(...)` is available. | The current API is name/Flecs-oriented. The strict baseline's capability-composition target is a later convergence problem, not a missing-interface task. |
| [`IEffectsModel`](../../../../src/core/interfaces/effects_model.h) | Defines `on_proximity_hit(...)`. [`default_effects_model.cpp`](../../../../src/models/weapons/default_effects_model.cpp) implements it and routes domain consequences; `set_effects_model(...)` is available. | Naval and Ground domain routes are intentionally limited; the Ground route preserves placeholder/finalization behavior and does not constitute ground damage runtime. |
| [`ISensorModel`](../../../../src/core/interfaces/sensor_model.h) | Defines `scan(...)`. [`default_sensor_model.cpp`](../../../../src/models/systems/default_sensor_model.cpp) implements it, including a Naval maritime adapter; `set_sensor_model(...)` is available. | There is no admitted Ground sensing system/model family. A new implementation requires the baseline's domain-extension evidence. |

`UnitDefinition` also already exists in
[`src/content/unit_definition.h`](../../../../src/content/unit_definition.h).
Therefore, later work must refine or compose the existing contract rather than
claim to introduce it for the first time.

## Ground System Gap

The current Ground surface is deliberately incomplete:

- [`src/components/domains/ground/`](../../../../src/components/domains/ground/README.md)
  owns static command/tasking fields and placeholder combat data;
- [`src/models/domains/ground/default_effects_ground_domain.h`](../../../../src/models/domains/ground/default_effects_ground_domain.h)
  is an explicit placeholder route;
- [`src/systems/combat/damage_system_ground.h`](../../../../src/systems/combat/damage_system_ground.h)
  is a no-op include/register shell and explicitly does not claim maintained
  Ground damage behavior;
- `src/systems/domains/ground/` does not exist.

Consequently, this issue must not present Ground movement, sensing, fires,
damage, terrain control, or a complete land-domain tick loop as implemented.
Before any Ground system owner can be admitted, a separate work package must
name its stage coverage, components, consumed and produced packets, read/write
sets, clock and latency policy, facade visibility, compatibility behavior, and
parity/regression tests, as required by the strict baseline.

## Dependency Rules

Arrows in this section mean `consumer -> provider`. There is no valid single
chain such as `core -> systems -> interfaces`; that notation conflates
composition ownership with low-level dependency direction.

The candidate modularization must preserve these owner rules:

1. `components`, `runtime/contracts`, and `content` provide data contracts and
   do not own per-tick behavior, facade APIs, or bindings.
2. `core/interfaces` defines replaceable abstractions. It may consume the data
   types required by the current contracts, but it must not depend on concrete
   default model implementations.
3. `models -> core/interfaces + components/content/contracts`: models implement
   replaceable behavior and must not register ECS systems or own lifecycle.
4. `systems -> components + approved model interfaces/refs`: systems schedule
   ECS mutation and must not depend on external bindings, training glue,
   `runtime/facade`, or a sibling domain as a shortcut.
5. `core/engine -> systems + core/interfaces + data contracts`: the engine owns
   world lifecycle and composition. Today it also constructs default models;
   that is an explicit current coupling, not evidence that models belong to the
   engine layer.
6. `runtime/facade -> core/engine + runtime/contracts`, and external
   `interfaces -> runtime/facade + contracts`. External adapters translate
   formats; they do not mutate raw ECS state or become hidden runtime owners.

Any proposed move must state both the dependency it removes and the new legal
dependency it introduces. Moving a file without changing its owner or include
direction is not architectural closure.

## Candidate Work Packages

The following are unapproved candidates, ordered by prerequisite rather than
commitment:

### Candidate A: Pin Existing Composition Contracts

- inventory the three existing interfaces, default implementations, kernel
  construction paths, setters, and tests;
- identify direct concrete-model includes that remain at the composition edge;
- propose a bounded composition change only if it reduces a measured boundary
  violation without changing behavior.

### Candidate B: Ground System Admission Design

- decide whether the first real Ground runtime slice is movement, sensing,
  fires, damage, or terrain;
- define one stage-local contract and its evidence instead of creating an empty
  `src/systems/domains/ground/` tree;
- keep the existing no-op damage shell and effects placeholder explicitly
  non-authoritative until that slice passes its admission gates.

### Candidate C: Transitional Root Cleanup

- inventory shared files before assigning a domain owner;
- preserve common contracts outside domain roots;
- move only behavior with a demonstrated single-domain owner and update build,
  include, and architecture tests in the same authorized slice.

### Candidate D: Capability-Composition Convergence

- reconcile the existing `IUnitFactory` and `UnitDefinition` path with the
  strict baseline's `CapabilityBundle` / `spawn_platform(...)` target;
- define compatibility for `spawn_unit(type_name)` before changing its public
  surface;
- do not treat the illustrative target as an already accepted ABI.

## Admission And Stop Rules

A candidate may be promoted only when its work package provides:

- exact file ownership and dependency changes;
- current and target include/build graphs;
- stage, packet, clock, and facade implications where runtime is involved;
- compatibility and rollback behavior;
- focused architecture tests plus relevant runtime/build evidence.

Stop if the proposal merely creates empty directories, renames existing
interfaces, duplicates the strict baseline, or moves domain terminology into
shared core without a cross-domain contract.

## Non-Goals

- a plugin marketplace or dynamic loading framework;
- ECS replacement or distributed-runtime redesign;
- declaring Ground runtime maturity from DTOs or placeholders;
- redesigning the strict architecture baseline inside this issue;
- authorizing any implementation described above.

## Related Evidence

- [Strict simulation-system architecture baseline](../../standards/simulation_system_architecture_design.md)
- [Architecture owner README](../../README.md)
- [Document lifecycle policy](../../../engineering/documentation/standards/document_lifecycle_policy.md)
- [`SimulationKernel` composition](../../../../src/core/engine/simulation_kernel.cpp)
- [Domain-separation architecture tests](../../../../tests/architecture/structural_boundaries/test_domain_separation_boundaries.py)
