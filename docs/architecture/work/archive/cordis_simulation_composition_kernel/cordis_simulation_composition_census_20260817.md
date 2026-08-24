# Cordis Simulation Composition Census — 2026-08-17

Status: `2026-08-17` P1-A composition census passed; this is a historical,
pre-P2-B source-grounded baseline, not the current runtime implementation or a
frozen P1-B schema. Current implementation status is tracked separately.

Language:

- English canonical: `cordis_simulation_composition_census_20260817.md`
- Chinese companion: [cordis_simulation_composition_census_20260817.zh.md](cordis_simulation_composition_census_20260817.zh.md)

Document kind: `reference`
Lifecycle: `archived`
Canonical: `docs/architecture/work/archive/cordis_simulation_composition_kernel/cordis_simulation_composition_census_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

Parent: [Cordis Simulation Composition Kernel](README.md)

## Decision Summary

The present runtime has useful seams but no single composition authority.
`SimulationKernel` owns concrete default providers and services,
`register_components_and_systems()` owns a fixed cross-domain Flecs graph,
`RuntimeFacade` chooses a concrete CPU backend, and host bindings expose three
different runtime tiers. Stage semantics are described by two additional
registries that do not generate the Flecs registration graph.

This makes a native composition kernel necessary even if Cordis is introduced:
Cordis can resolve and describe an admitted composition, but native code must
revalidate it, own resources, compile the executable graph, freeze truth-affecting
choices, and perform deterministic rollback and disposal. Replacing the current
constructors with JavaScript or Cordis callbacks would move the ownership problem
without solving it.

The P1-B contract must therefore define one canonical resolved manifest and one
native realization path. Existing constructors, setters, registration lists,
backend selection, and raw binding tiers become compatibility inputs or migration
targets; none may remain a second maintained composition truth.

## Verification Boundary And Method

Inspected surfaces:

- native kernel construction, shutdown, reset, stepping, and model setters;
- model/factory/service interfaces, default makers, Flecs singleton references,
  raw captures, and consumers;
- component and system registration, exact-stage inventory, and maintained
  stage-node manifests;
- world-batch construction and world-layout/reset behavior;
- backend SPI, facade construction, backend admission, and CUDA-resident candidate;
- Python module, `SimulationKernel`, `WorldBatchRuntime`, and `RuntimeFacade`
  bindings;
- CMake ownership and focused architecture/runtime tests.

Representative reproducible commands, executed from the repository root:

```powershell
rg -n "make_default_|DefaultUnitFactory|WeaponReleaseService|set_.*_model|set_unit_factory" src/core src/models
rg -n "Ref>|\.get\(\)|\[env\]|IEnvironmentModel \*|IWeaponReleaseService" src/core src/systems src/models
rg -n "register_.*system|ecs\.component<|ecs\.set<.*Ref>" src/core/engine/simulation_kernel_systems.cpp
rg -n "ExactStepStageDescriptor|stage_node_manifest_registry_seed|\.node_id =" src/core/engine src/runtime/contracts
rg -n "make_unique<FlecsCpuBackend>|IWorldBatchBackend|CudaResidentBackend|admit_backend_request" src/runtime
rg -n "class_<SimulationKernel|class_<WorldBatchRuntime|class_<runtime::RuntimeFacade" src/interfaces/python
rg -n "SimulationKernel|WorldBatchRuntime|RuntimeFacade|stage_node_manifest|cuda_resident" tests
```

The inventory uses text search followed by direct control-flow and ownership
inspection. It does not claim whole-program alias proof, dynamic trace coverage,
or an AST-generated dependency graph. Those stronger checks belong in P2/P3
guards after the production composition types exist.

## Quantitative Baseline

| Surface | Observed baseline | Interpretation |
| --- | ---: | --- |
| kernel-owned replaceable model/factory providers | 7 | environment, unit factory, effects, sensor, acoustic, control, guidance |
| kernel-owned service/event objects | 3 | engagement event store, weapon-release damage bridge, weapon-release service |
| published Flecs singleton service/model refs | 7 | six model refs plus engagement recorder; unit factory is consumed through the release service |
| component registration calls in the central function | 83 | component availability is fixed by one constructor-time path |
| active system registration calls in the central function | 34 | common, air, naval, ground, combat, EW, and logistics families are installed together |
| exact-step stage descriptors | 30 | ordered trace/step inventory; only a subset has detailed contract descriptors |
| maintained stage-node manifest seed entries | 5 | semantic lifecycle slice, not a complete executable system graph |
| Python-visible runtime ownership tiers | 3 | `SimulationKernel`, `WorldBatchRuntime`, and `RuntimeFacade` |

Counts are navigation aids, not capability claims. A count change must trigger a
census review until generated composition evidence replaces this manual baseline.

## Construction And Ownership Inventory

| Edge | Current owner and construction | Publication / consumer rule | Scope and replacement rule | Migration disposition |
| --- | --- | --- | --- | --- |
| environment model | `SimulationKernel` calls `make_default_environment_model()` in `simulation_kernel.cpp:42-53` | `EnvironmentModelRef` is published; many physics, model, sensor, guidance, and world-layout consumers read it, but ground contact also captures a raw pointer | world lifetime; `set_environment_model()` replaces the owner and singleton ref during an active kernel | provider key with world scope; prohibit episode-time replacement; remove raw capture before compatibility setter retirement |
| unit factory | `SimulationKernel` constructs `DefaultUnitFactory` | not published as a Flecs ref; `SimulationKernelWeaponReleaseService` holds a reference to the owning `unique_ptr` | world lifetime; setter replacement is observed because the service references the `unique_ptr` object, not its current pointee | typed provider/handle; construct release service from an explicit dependency rather than an owner-member alias |
| effects model | default maker owned by `SimulationKernel` | `EffectsModelRef`; common damage and debug effects APIs resolve the current ref | world lifetime; setter updates singleton ref | world-scoped immutable provider in frozen graphs; compatibility replacement only at a governed barrier before execution |
| sensor model | default maker owned by `SimulationKernel` | `SensorModelRef`; sensor system resolves the current ref | world lifetime; setter updates singleton ref | model provider contribution bound to sensor capability/stage contracts |
| acoustic model | default maker owned by `SimulationKernel` | `AcousticModelRef`; sonar system resolves the current ref | world lifetime; setter updates singleton ref | model provider contribution bound to acoustic/naval capability contracts |
| control model | default maker owned by `SimulationKernel` | `ControlModelRef`; air-control system resolves the current ref | world lifetime; setter updates singleton ref | model provider contribution bound to control and exact-stage contracts |
| guidance model | default maker owned by `SimulationKernel` | `GuidanceModelRef`; guidance system resolves the current ref | world lifetime; setter updates singleton ref | model provider contribution bound to guidance/combat contracts |
| engagement event store | concrete object owned by `SimulationKernel` | recorder ref is published; guidance, damage, structural, and ground-contact paths record through it | store persists with the world; `reset()` clears episode events | split world-scoped recorder service from episode-scoped event state and generation |
| weapon-release damage bridge | concrete object owned by `SimulationKernel` | passed by reference into weapon-release service | world lifetime; manually destroyed before models | explicit service provider with declared dependency on effects/damage surfaces |
| weapon-release service | concrete `SimulationKernelWeaponReleaseService` owned by `SimulationKernel` | pilot and naval release systems capture/use `IWeaponReleaseService&` | world lifetime; no public replacement API; depends on factory owner alias, tuning, RNG, recorders, and bridge | scoped service provider with complete dependency declaration and native lifetime ordering |

Default model makers are located in the existing model-owner directories, while
the ownership decision is centralized in
[`simulation_kernel.cpp`](../../../../../src/core/engine/simulation_kernel.cpp).
The target provider catalog must preserve model owners and capability admission;
it must not turn the composition package into a new owner of model semantics.

## Lifecycle And Reset Boundaries

| Boundary | Current behavior | Composition implication |
| --- | --- | --- |
| kernel construction | creates all default providers/services, registers all components/systems, disables `ResupplyLogic`, then calls `reset(42)` | construction, graph compilation, and first episode initialization are fused |
| normal step | calls `ecs.progress(time_step)`; exact-stage tracing has a separate guarded path | maintained hot path is native and must remain free of Cordis/Node callbacks |
| episode reset | clears engagement events, deletes `SimObject` entities, resets ECS clock, and reseeds RNG | providers, systems, environment configuration, and backend remain world scope; entities/time/RNG/event generation are episode scope |
| batch resize | allocates one complete `SimulationKernel` for every new world | resolved application/profile data should be shareable, while mutable world resources remain isolated |
| batch setup | applies layout/configuration and then resets each world with deterministic seed mapping | setup is a governed pre-episode transition, not plugin hot reload |
| shutdown | ends trace, deletes entities, resets ECS, then manually resets services/models in a fixed order | native composition transaction must derive reverse dependency disposal and prove failure rollback |

The current reset behavior is compatible with a four-level target: application
catalog, backend/batch, world, and episode. It is not compatible with treating
every Cordis scope as an independent runtime callback. Scope mapping must be
explicit in the manifest and realized natively.

## Raw Capture And Replacement Hazards

The highest-confidence correctness defect is the environment edge:

1. `SimulationKernel::register_components_and_systems()` passes
   `environment_model_.get()` to `register_ground_contact_system()`.
2. `GroundContactSystem` captures that `IEnvironmentModel*` in its Flecs run
   lambda.
3. `SimulationKernel::set_environment_model()` can destroy the old owner and
   publish a new `EnvironmentModelRef`.
4. Other consumers read the current singleton ref, while ground contact retains
   the old address.

The result is inconsistent replacement semantics and a possible dangling
pointer. P2/P3 may fix the immediate defect before all provider migration is
complete, but the final rule is stronger: truth-affecting services are resolved
to generation-checked native handles during graph realization and are immutable
while an episode graph is active.

The weapon-release service does not have the same immediate stale-pointee bug
because it references the `unit_factory_` owner slot. It still encodes hidden
lifetime coupling and therefore remains a migration target.

## System Registration Inventory

The central registration path installs the following active calls in order:

| Family | Registration calls |
| --- | --- |
| command/control | `register_command_link_system`, `register_action_mapping_system`, `register_command_lag_system`, `register_control_system` |
| air/physics | `register_force_clear_system`, `register_aero_state_system`, `flight_dynamics::register_propulsion_system`, `register_force_system`, `flight_dynamics::register_actuator_system`, `register_aerodynamics_system`, `register_ground_contact_system`, `register_rotational_integration_system`, `register_leapfrog_integration_system` |
| motion/navigation | `register_ship_motion_system`, `register_submarine_motion_system`, `register_navigation_system` |
| sensing/C2 | `register_sensor_system`, `register_sonar_system`, `register_track_manager_system`, `register_data_link_system`, `register_embarked_air_ops_system` |
| combat/effects | `register_guidance_system`, `register_pilot_weapon_release_system`, `register_naval_mission_weapon_release_system`, `register_damage_system_common`, `register_aircraft_damage_system`, `register_structural_failure_system`, `register_structural_consequence_system`, `register_naval_damage_system`, `register_ground_damage_system` |
| observation/EW/logistics | `register_instrument_system`, `register_ew_system`, `register_logistics_system`, `register_naval_logistics_system` |

Only ground-contact registration receives a replaceable model as a raw pointer.
Pilot and naval weapon-release registration receive a service reference. Most
other calls receive only the Flecs world and discover singleton services during
execution.

The list is an implementation order, not an admitted dependency graph. Every
world receives the combined family set even if its content/profile does not use
all domains. P3 must replace this list with native contributions whose component,
service, stage, capability, read/write, conflict, and ordering requirements are
validated before Flecs registration. Cordis package order must never become
system execution order.

## Three Scheduling Truth Surfaces

| Surface | Current purpose | Coverage | Required target disposition |
| --- | --- | --- | --- |
| `simulation_kernel_systems.cpp` | constructs the executable Flecs component/system graph | 83 component calls and 34 active registration calls | generated/realized from admitted native contributions |
| `exact_stage_inventory.cpp` | exact-step trace inventory and detailed contracts for selected stages | 30 descriptors; detailed contracts cover a selected exact subset | consume the same canonical node identities and reject unresolved parity gaps |
| `stage_node_manifest_registry.h` | maintained causal/runtime semantic manifests | 5 nodes for the maintained selected slice | remain semantic authority and become an admission input, not a parallel executable graph |

These surfaces are deliberately not declared equivalent today. A P1-B schema
must distinguish semantic stage identity, executable system contribution, and
trace/evidence projection while giving them stable join keys. P3 acceptance must
prove that one resolved composition produces the Flecs graph and the evidence
views; it must not merely synchronize three hand-edited lists.

## Backend Composition Inventory

| Edge | Current state | Migration disposition |
| --- | --- | --- |
| semantic backend SPI | `IWorldBatchBackend` defines configuration, content, reset, setup, injection, evaluation, advance, export, and diagnostics surfaces | keep as the facade semantic seam; provider factories must return this interface |
| CPU realization | both `RuntimeFacade` constructors directly create `FlecsCpuBackend` | move to admitted backend provider selected from the resolved native manifest |
| CUDA-resident candidate | `CudaResidentBackend` implements the SPI but remains candidate/experimental and is used through bounded probes/tests | catalog visibility must not imply admission; preserve fail-closed profile contracts |
| request admission | backend profile contracts and `admit_backend_request()` validate requests, but admission does not construct or replace the backend | unify request validation and provider materialization in one transaction while retaining separate evidence for requested versus realized profile |
| capabilities | facade capability reporting is intentionally fail-closed for unmaintained GPU operation | composition cannot promote capabilities; it may only realize already-admitted profiles |

The key gap is not lack of an interface; it is the split between static admission
contracts and constructor-time materialization. P4 must close that split without
allowing Cordis discovery to promote an experimental backend.

## Binding And Host Inventory

[`python_module.cpp`](../../../../../src/interfaces/python/python_module.cpp)
assembles command, core, episode, runtime, and GPU binding groups. The maintained
Python module exposes:

| Tier | Current exposure | Composition risk and target policy |
| --- | --- | --- |
| `SimulationKernel` | direct construction, reset, step, shutdown, setup/configuration, and diagnostic surfaces | raw kernel construction can bypass a future facade composition policy; retain only as an explicit native compatibility profile or narrow test surface |
| `WorldBatchRuntime` | direct batch construction, setup, reset, step, and related batch operations | second host-visible construction path must consume the same resolved profile and cannot own independent defaults |
| `RuntimeFacade` | primary semantic API, configuration, admission, setup, stepping, export, replay, and evidence | target host boundary and owner of composition request/result DTOs, while realization remains in native composition code |

No maintained Node package or Node-API target exists. A future Node host should
bind the coarse facade/composition construction boundary, not expose Flecs or
introduce stage callbacks. Python and standalone C++ must remain fully usable
without Node or Cordis installed.

## Build And Test Ownership

Current CMake ownership separates content, core, facade, and Python module
targets. `ef_py` links the facade and core surfaces, so a future native
composition library should be independently linkable by core/facade and should
not depend on bindings or a Node package.

Existing evidence relevant to migration includes:

| Evidence surface | What it currently proves | Gap for composition work |
| --- | --- | --- |
| kernel lifecycle guards and teardown stability tests | active/shutdown guards and repeated create/reset/step/destroy behavior | no provider dependency rollback, generation-handle, or failed-construction matrix |
| stage-node manifest architecture tests | manifest validation, maintained visibility, barriers, and selected-slice rules | no generation of the full executable graph |
| facade contract-boundary tests | fail-closed facade/GPU separation | no provider materialization parity |
| CUDA-resident profile/admission tests | candidate profiles remain bounded and rejected when unsupported | no admitted runtime provider selection |
| binding surface tests | maintained Python DTO and method shapes | no cross-host composition parity or raw-tier retirement policy |
| world-batch tests | deterministic world use and facade adapter behavior | no shared resolved-profile memory/startup evidence |

P2 and later tests must add deterministic permutation resolution, duplicate and
conflict rejection, dependency-cycle diagnostics, failed-provider rollback,
reverse-order disposal, scope isolation, generation mismatch rejection, default
profile replay parity, and composition identity round trips.

## Risk Register

| ID | Risk | Severity | Evidence | Required control |
| --- | --- | --- | --- | --- |
| `CEN-01` | stale/dangling environment pointer after model replacement | high correctness | setter updates singleton ref while ground contact captures raw pointer | remove raw capture; freeze or generation-check handles |
| `CEN-02` | constructor monolith remains a second composition truth | high architecture | concrete model/service construction in `SimulationKernel` | builder realized only from validated manifest |
| `CEN-03` | three scheduling descriptions drift | high determinism/evidence | central registration, exact inventory, semantic manifest seed | canonical node identities and generated/validated joins |
| `CEN-04` | admitted backend request differs from realized constructor backend | high capability integrity | facade always creates CPU backend | one admission/materialization transaction with requested/resolved evidence |
| `CEN-05` | direct binding tiers bypass composition policy | medium-high governance | three Python-visible runtime tiers | one native resolver; explicit compatibility profiles; retirement gates |
| `CEN-06` | manual teardown order or partial construction leaks resources | medium-high lifetime | fixed owner reset order | transactional construction and dependency-derived reverse disposal |
| `CEN-07` | every world pays for the combined graph/providers | medium scale | full kernel allocated per batch world | shared immutable resolution plus scoped per-world realization and benchmarks |
| `CEN-08` | plugin discovery is mistaken for semantic admission | high authority | backend candidates and stage contracts already use fail-closed policy | native revalidation; Cordis cannot promote capabilities or stages |

## P1-B Contract Requirements Derived From The Census

P1-B must settle the following before P2 implementation:

1. A versioned, host-neutral `SimulationCompositionManifest` with canonical
   encoding and stable requested/resolved identities.
2. Stable provider, service, system-contribution, backend-profile, capability,
   semantic-stage, executable-node, and evidence-projection identifiers.
3. Explicit application, backend/batch, world, and episode scope mapping;
   scope-capture violations must be invalid manifests.
4. Deterministic provider selection, dependency ordering, duplicate/conflict
   handling, optional contribution rules, and cycle diagnostics independent of
   discovery order.
5. Typed native handles with generation/scope identity; no manifest may require
   a raw owning pointer to survive provider replacement.
6. A system contribution schema that declares components, services, stage join
   keys, read/write state, barriers, conflicts, domain/capability requirements,
   and registration factory.
7. A backend provider contract that joins existing request admission with
   realization without promoting candidate capabilities.
8. A default compatibility profile that exactly names the current seven
   providers, three services, 83 component registrations, and 34 system calls,
   with accepted deviations recorded explicitly.
9. Composition evidence fields for manifest hash, resolver version, provider
   versions, executable graph hash, backend profile, host mode, and scope
   generations.
10. A binding policy that identifies `RuntimeFacade` as the maintained coarse
    host seam and defines the bounded fate of direct kernel/batch constructors.

Production C++ type names and directory layout remain open until P1-B tests prove
the contract. The semantic requirements above are frozen as census outputs; a
later change requires an explicit architecture decision and updated evidence.

## Validation Results

Validation on `2026-08-17` produced:

- targeted audit of this subproject plus the architecture owner: 18 documents,
  110 repository-local links, 0 issues;
- maintained-surface audit: 150 documents, 1,433 links, 0 issues;
- strict maintained bilingual audit: 74/74 pairs synchronized, with no missing
  or diverged peer;
- documentation governance: 23 tests passed using the repository-local
  `ef_py` artifact from the main workspace; pytest then emitted the known
  Windows temporary-directory cleanup warning after a successful exit;
- focused stage/backend architecture tests: 13 passed and 7 could not start
  because the test helper requires `g++`, which is not installed or available
  on this Windows PATH. All seven were environment launch failures, not failed
  assertions;
- `git diff --check`: clean;
- count replay: 83 component registrations, 34 active system registrations,
  30 exact-stage descriptors, and 5 stage-node manifest seed entries.

A full-tree link audit still reports one pre-existing missing target under the
effects review archive, and the full-tree bilingual scan reports historical
single-language documents outside the strict maintained surface. Neither issue
originates from or targets this subproject; they were not modified or claimed
closed here.

## P1-A Closure Assessment

P1-A passes because every requested composition category now has an identified
owner, scope, replacement rule, hazard classification, and migration
disposition: constructors, setters, raw captures, service refs, registration
entries, backend selection, reset boundaries, stage registries, bindings, build
ownership, and relevant tests.

No runtime file was changed. This pass proves that P1-B can begin without hiding
known ownership edges; it does not prove manifest correctness, lifecycle safety,
Cordis feasibility at runtime, behavioral parity, or performance benefit.

At P1-A closure, the next eligible cluster was `P1-B Manifest And Resolution
Contract`, with P2 and all constructor migration held behind its schema,
canonical fixtures, invalid-manifest matrix, and deterministic-resolution gates.
Those gates subsequently passed in the
[P1-B contract baseline](cordis_simulation_composition_contract_20260817.md);
P2-A subsequently passed as an isolated native lifecycle baseline. P2-B
constructor migration is now next and remains bound to this census.
