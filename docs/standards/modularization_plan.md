# Modularization Plan

This document remains active, but it must now be read under the new standards tree:

- [Standards Overview](/home/void0312/Workshop/CMO/docs/standards/README.md)
- [Joint Baseline](/home/void0312/Workshop/CMO/docs/standards/joint/command_and_modeling_baseline.md)
- [Service Profiles](/home/void0312/Workshop/CMO/docs/standards/services/README.md)

This document outlines a minimal, staged plan to modularize the project for
maintainability and swap-in/out of unit models, sensors, and combat logic.

## Goals
- Separate stable core from replaceable models.
- Allow swapping unit definitions, sensor models, and effects logic without
  changing the engine core.
- Keep complexity low: modularize only where variability is needed.

## Principles
- One-way dependencies: core -> systems -> interfaces (no back edges).
- Data definitions are separate from execution logic.
- Replaceable modules live behind small, explicit interfaces.
- Domain-neutral core comes first; service and platform specialization should not leak upward.

## Module Map (Target)

### core/
- Purpose: simulation lifecycle, time step, entity lifecycle, world access.
- Owns: SimulationKernel, reset/step, entity registry, deterministic time.
- Depends on: components/ only.

### components/
- Purpose: pure data components (no logic).
- Owns: Transform, Velocity, Sensor, Health, Score, Weapon, etc.
- Depends on: nothing.

### systems/
- Purpose: system execution (control, movement, sensor scan, guidance, damage).
- Owns: system registration and update logic.
- Depends on: core/, components/.

### interfaces/
- Purpose: external APIs (Python, web, CLI tools).
- Owns: bindings and data translation only.
- Depends on: core/.

### content/
- Purpose: data-driven definitions for units, weapons, sensors, scenarios.
- Owns: UnitDefinition, WeaponDefinition, SensorDefinition, ScenarioConfig.
- Depends on: none (data only).

### standards/
- Purpose: modeling baseline and domain/service profiles.
- Owns: joint/common core, service profiles, platform/task specialization docs.
- Depends on: none (documentation source of truth).

### models/
- Purpose: replaceable behavior models (effects, sensors, guidance).
- Owns: concrete implementations behind interfaces.
- Depends on: components/ (and possibly core/ for world access).

## Replaceable Interfaces (Stable)

### IUnitFactory
- Responsibility: spawn entities from UnitDefinition.
- Inputs: UnitDefinition, initial state.
- Outputs: entities with component bundles attached.

### IEffectsModel
- Responsibility: resolve hit, damage, and score changes.
- Inputs: attacker, target, event context.
- Outputs: state deltas (health, score, destruction events).

### ISensorModel
- Responsibility: produce detections from environment state.
- Inputs: sensor owner, environment snapshot.
- Outputs: ContactList (detections with consistent conventions).

## Component Bundles
- AirUnitBundle: Transform, Velocity, FlightModel, Sensor, Health, Score.
- MissileBundle: Transform, Velocity, Missile, Sensor (seeker), Health.
- FacilityBundle: Transform, Health, Sensor (optional).

Bundles are created by IUnitFactory using UnitDefinition.

## Staged Migration Plan

### Stage 1: Documentation and Boundaries
- Document conventions (angles, units, sensor semantics).
- Define the target module map (this document).

### Stage 2: Unit Definitions and Factory
- Introduce UnitDefinition data structs under content/.
- Implement a basic UnitFactory in models/ to spawn bundles.
- Update SimulationKernel spawn_unit to delegate to UnitFactory.

### Stage 3: Effects Model
- Introduce IEffectsModel interface.
- Move damage logic from systems/damage_system.h into an EffectsModel
  implementation (systems call the interface).

### Stage 4: Sensor Model
- Introduce ISensorModel interface.
- Move detection math into model implementation; system only schedules scans.

### Stage 5: Optional Refinement
- Add scenario configs (content/).
- Add alternate models (low/medium/high fidelity) and selection per scenario.

## Ownership and Constraints
- Core should not include model headers directly; use forward interfaces.
- Systems should not depend on interfaces/.
- Interfaces should not mutate internal state except through core APIs.

## Non-Goals (for now)
- Full plugin system or dynamic loading.
- ECS replacement or distributed architecture changes.
- Deep refactors of rendering/visualization.

## Standards Alignment

From the new documentation baseline, future modularization should respect:

- `joint/common core` stays above service-specific semantics
- service profiles explain organization and control patterns
- platform/task semantics stay in domain-specific modules and adapters

That means future code should avoid pushing air-specific terms into global core modules when the concept is really:

- common command relationship
- common task organization
- service-specific tactical grouping
