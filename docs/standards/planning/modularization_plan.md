# Modularization Plan

Language:
- English canonical: `planning/modularization_plan.md`
- Chinese companion: [modularization_plan.zh.md](modularization_plan.zh.md)

Status: `2026-06-10` active planning document with current-layout notes; not a
current runtime contract.

This document remains active, but it must now be read under the maintained
standards tree:

- [Standards Overview](../README.md)
- [Joint Command and Modeling Baseline](../joint/command_and_modeling_baseline.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)
- [Service Profile Overview](../services/README.md)

This page is a roadmap for how the project could be modularized further for
maintainability and model replacement.

It is not the authoritative description of how the current runtime already
works. That authority belongs to the maintained workflow and standards
documents.

## Purpose

The modularization plan exists to answer a future-facing question:

`How should the codebase be split if we continue separating stable core,
replaceable models, and domain-specific specialization?`

That means the directory map and interfaces below should be read as target
structure, not as proof that every module already exists in final form.

## Current Implemented Domain Roots

The repository now has real domain owner roots in the source tree. This keeps
the plan active, but it changes how the target map should be read: the current
roots are evidence of ownership direction, not proof that every domain has the
same runtime maturity.

Current implemented roots:

- `src/components/domains/`
  - current owners: `air/`, `naval/`, `ground/`
  - role: domain-owned ECS components, command/tasking extensions, platform
    DTOs, and narrow combat/status slices
  - boundary: shared shells still live under `src/components/{combat,command,tasking}`;
    new domain-specific component slices should go under
    `src/components/domains/<domain>/`
- `src/systems/domains/`
  - current owners: `air/`, `naval/`
  - role: domain-owned runtime system registration and per-tick behavior
  - boundary: there is no released `ground/` runtime system owner here yet;
    ground movement, sensing, fires, damage, and terrain-control runtime remain
    held until their interfaces and acceptance gates exist
- `src/models/domains/`
  - current owners: `air/`, `naval/`, `ground/`
  - role: domain-owned replaceable model implementations, adapters, and explicit
    placeholder routes consumed by shared models
  - boundary: ground model ownership is limited to unit-factory capability
    evidence and explicit effects placeholder routing, not full land-domain
    runtime maturity

New domains should extend these `domains/<domain>/` roots only when they have a
real component, system, or model owner. Do not add empty production owner roots,
demo domains, or teaching shells as standards evidence.

The older shared or transitional roots still matter:

- `src/components/combat`, `src/components/command`, and `src/components/tasking`
  remain the shared component shells.
- `src/systems/combat`, `src/systems/physics`, and `src/systems/systems` remain
  shared or transitional runtime areas.
- `src/models/weapons` and `src/models/systems` remain shared model areas that
  route into domain adapters where those adapters exist.

This means the target map below is still useful for future cleanup, but the
current codebase already uses `src/*/domains/<domain>/` as the preferred place
for domain-owned specialization.

## Goals

- separate stable core from replaceable models
- allow unit definitions, sensor models, and effects logic to change without
  rewriting engine foundations
- keep complexity low by modularizing only where variability is likely to pay
  for itself

## Principles

- one-way dependencies: `core -> systems -> interfaces`, with no intentional
  back edges
- data definitions should stay separate from execution logic
- replaceable modules should sit behind small explicit interfaces
- domain-neutral core should come first; service and platform specialization
  should not leak upward

These are planning principles, not a claim that the repository already satisfies
them everywhere.

## Target Module Map

### `core/`

- purpose: simulation lifecycle, time step, entity lifecycle, world access
- target ownership: `SimulationKernel`, reset/step flow, entity registry,
  deterministic time
- target dependency direction: depends on `components/` only

### `components/`

- purpose: pure data components
- target ownership: `Transform`, `Velocity`, `Sensor`, `Health`, `Score`,
  `Weapon`, and similar data carriers
- target dependency direction: no higher-level dependency
- current domain convention: domain-specific slices belong under
  `src/components/domains/<domain>/`; shared component shells stay outside the
  domain roots

### `systems/`

- purpose: execution systems such as control, movement, sensor scan, guidance,
  and damage
- target ownership: system registration and update logic
- target dependency direction: depends on `core/` and `components/`
- current domain convention: released domain runtime owners belong under
  `src/systems/domains/<domain>/`; absence of a domain root means runtime
  ownership is still held, not that another domain owns it

### `interfaces/`

- purpose: external APIs such as Python bindings, web surfaces, or CLI tools
- target ownership: bindings and data translation only
- target dependency direction: depends on `core/`

### `content/`

- purpose: data-driven definitions for units, weapons, sensors, and scenarios
- target ownership: `UnitDefinition`, `WeaponDefinition`, `SensorDefinition`,
  `ScenarioConfig`
- target dependency direction: data-only

### `standards/`

- purpose: documentation source of truth for modeling, layering, and ownership
- target ownership: joint/common core, service profiles, workflow bridge docs,
  and specialization docs
- target dependency direction: none

### `models/`

- purpose: replaceable behavior-model implementations
- target ownership: concrete effects, sensor, guidance, or other domain models
  behind interfaces
- target dependency direction: usually `components/`, and possibly `core/` when
  world access is necessary
- current domain convention: domain-owned model adapters and implementations
  belong under `src/models/domains/<domain>/`; shared model routes may remain in
  `src/models/{weapons,systems}` while they dispatch to domain adapters

## Target Replaceable Interfaces

The following interfaces are still planning targets unless a future code change
lands them explicitly.

### `IUnitFactory`

- responsibility: spawn entities from `UnitDefinition`
- inputs: `UnitDefinition` plus initial state
- outputs: entities with appropriate component bundles attached

### `IEffectsModel`

- responsibility: resolve hit, damage, and score effects
- inputs: attacker, target, and event context
- outputs: state deltas such as health, score, or destruction events

### `ISensorModel`

- responsibility: produce detections from environment state
- inputs: sensor owner plus environment snapshot
- outputs: detection lists with maintained conventions

## Example Bundle Targets

These bundles remain examples of the intended direction:

- `AirUnitBundle`: `Transform`, `Velocity`, `FlightModel`, `Sensor`, `Health`,
  `Score`
- `MissileBundle`: `Transform`, `Velocity`, `Missile`, seeker `Sensor`,
  `Health`
- `FacilityBundle`: `Transform`, `Health`, optional `Sensor`

They illustrate factory output shape; they do not assert a finalized ABI.

## Staged Migration Plan

### Stage 1: Documentation And Boundaries

- document conventions and ownership boundaries
- define the target module map in this planning document

### Stage 2: Unit Definitions And Factory

- introduce `UnitDefinition`-style data under `content/`
- implement a basic factory path in `models/`
- move spawning logic toward delegation rather than hardwired construction

### Stage 3: Effects Model

- introduce an `IEffectsModel`-style interface
- move damage and lethality logic behind that interface

### Stage 4: Sensor Model

- introduce an `ISensorModel`-style interface
- move detection math behind a model boundary while systems schedule scans

### Stage 5: Optional Refinement

- add scenario configuration content layers
- add alternate fidelity models and scenario-driven selection

## Ownership And Constraints

Future modularization should preserve the following constraints:

- core modules should avoid depending directly on concrete model headers
- systems should not depend on external-interface layers
- external interfaces should translate data, not become hidden runtime owners
- documentation ownership in `docs/standards/` should stay aligned with code
  ownership boundaries

## Non-Goals For Now

- a full plugin marketplace or dynamic loading system
- ECS replacement or a distributed-architecture rewrite
- deep rendering or visualization refactors

## Standards Alignment

Future modularization should respect the maintained standards tree:

- `joint/common core` stays above service-specific semantics
- service profiles explain organizational and control interpretation
- platform/task semantics stay in specialized modules and adapters
- workflow bridge ownership stays distinct from pure runtime kernels

That means future code should avoid pushing air-specific or naval-specific terms
into global core modules when the concept is really:

- a common command relationship
- a common task-organization anchor
- a service-specific tactical grouping

## Related Documents

- [Standards Overview](../README.md)
- [Runtime Workflow and Contract Baseline](../bridge/runtime_workflow_and_contract_baseline.md)
- [Document Alignment Map](../overview/document_alignment_map.md)
