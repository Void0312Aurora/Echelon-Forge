# Cordis Simulation Composition Kernel

Status: `2026-08-17` active design; P0 authority/documentation, P1-A
composition census, P1-B manifest/resolution contract, and P2-A native
lifecycle baseline passed. P2-B default-provider migration is next.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/README.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

Related authority:

- [Architecture owner](../../../README.md)
- [Simulation system architecture design](../../../standards/simulation_system_architecture_design.md)
- [Runtime workflow and contract baseline](../../../standards/runtime_workflow_and_contract_baseline.md)
- [System modularization issue](../../issues/modularization_plan.md)
- [Runtime facade contract issue](../../issues/runtime_facade_contract_plan.md)
- [Subproject creation standard](../../../../engineering/automation/rules/subproject_creation_standard.md)
- [Current kernel construction](../../../../../src/core/engine/simulation_kernel.cpp)
- [Current system registration](../../../../../src/core/engine/simulation_kernel_systems.cpp)
- [Backend semantic interface](../../../../../src/runtime/facade/internal/world_batch_backend.h)

## Purpose

This subproject introduces Cordis as the long-term composition control plane for
the simulation runtime while preserving C++ as the authority for deterministic
simulation execution. It establishes a versioned composition contract, native
lifecycle kernel, provider model, plugin admission model, evidence identity,
and optional Node/Cordis host without placing JavaScript, asynchronous plugin
dispatch, or cross-language service lookup in the per-step path.

The project is not justified as a short-term refactor or performance shortcut.
Its purpose is to provide a durable architecture for multiple model families,
domain extensions, backend implementations, experiment profiles, bindings, and
future external plugin packages without creating additional truth paths.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Model composition | coupled | `SimulationKernel` constructs default environment, effects, sensor, acoustic, control, guidance, and unit-factory implementations | Existing interfaces permit replacement but do not provide a coherent composition owner |
| Service lifetime | inconsistent | model pointers are published through Flecs refs, while `GroundContactSystem` captures the environment model pointer at registration | Replacing a provider is not a complete lifecycle transition |
| System composition | static | one registration function installs the shared, air, naval, and ground system set in a fixed sequence | Registration order is not a plugin dependency graph or profile contract |
| Backend selection | partially abstracted | `IWorldBatchBackend` exists, but `RuntimeFacade` constructs `FlecsCpuBackend` directly | Backend capability contracts exist without a general provider-selection root |
| Stage semantics | established foundation | maintained stage-node manifests describe semantic stage, read/write shards, clock, latency, synchronization, and barriers | The registry is not yet the sole input to system composition |
| Composition contract | P1-B pass | versioned requested/resolved manifests, stable service keys/scopes/error codes, canonical hashing, default compatibility fixtures, and fail-closed resolution tests | This is a resource-free contract baseline; it does not construct providers or own runtime resources |
| Native lifecycle kernel | P2-A pass | isolated `ef_composition` library, closed native JSON ingestion, catalog/factory metadata validation, scoped transactional realization, typed generation handles, rollback, rebuild, and reverse disposal tests | No default model, service, system, backend, binding, or Cordis producer has migrated to this library |
| Cordis integration | absent | no maintained Cordis, Node-API, or Node package surface exists in the repository | This is a new cross-runtime boundary, not an incremental dependency bump |

## Scope

In scope:

- define a stable `SimulationCompositionManifest` and canonical serialization;
- build a native C++ composition root with explicit application, backend,
  batch, world, and episode scopes;
- move model, service, system-package, and backend construction out of
  `SimulationKernel` and `RuntimeFacade` constructors;
- bind plugin contributions to existing capability, stage, clock, barrier,
  replay, and evidence contracts;
- make composition resolution deterministic, validated, hashable, and frozen
  before maintained simulation execution;
- add a Cordis package that resolves admitted plugins and emits the same
  versioned manifest consumed by the native runtime;
- provide a Node-API host adapter only after the native composition contract is
  stable;
- preserve Python/nanobind and standalone C++ deployments without requiring a
  Node runtime;
- support future domain, model, backend, diagnostics, and experiment plugins
  through governed extension points.

Out of scope:

- replacing Flecs as the ECS and state-query engine;
- replacing the deterministic C++ stage scheduler with Cordis events or
  JavaScript callbacks;
- per-step Node, JavaScript, IPC, or dynamic service lookup;
- arbitrary hot replacement of truth-affecting plugins during an episode;
- treating plugin discovery as authority to bypass stage, content, backend,
  evidence, or domain admission gates;
- creating a public plugin marketplace before signing, compatibility,
  provenance, and sandbox policies are accepted;
- claiming performance improvement without representative batch benchmarks.

## Architecture Decision

The target is a dual-layer composition architecture:

1. Cordis is the long-term declarative composition control plane and plugin
   ecosystem boundary.
2. A native C++ composition kernel validates and realizes the resolved
   manifest, owns runtime resources, freezes the executable graph, and performs
   deterministic teardown and rollback.
3. Flecs owns ECS state and registered systems; the existing stage contracts
   own causal-temporal execution semantics.
4. Cordis lifecycle events are administrative events. Simulation events remain
   native, timestamped, ordered, and replayable.
5. The maintained step path contains no Cordis or binding call.

The complete design is in
[Cordis simulation composition architecture](cordis_simulation_composition_kernel_architecture.md).

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Authority and Boundary` | Establish the owner, target architecture, non-goals, task clusters, and acceptance model. | User authorization and inspected repository baseline | Bilingual project documents and parent architecture links pass document gates | pass |
| `P1 Composition Contract` | Freeze manifest schema, service keys, plugin descriptors, scopes, compatibility rules, and deterministic resolution. | P0 accepted | Schema fixtures, validation rules, canonical encoding, and contract tests exist | pass |
| `P2 Native Lifecycle Kernel` | Implement C++ context, provider registry, scoped resources, rollback, freeze, and deterministic disposal. | P1 contract frozen | Native lifecycle tests cover success, failure rollback, scope isolation, and teardown | pass |
| `P3 Kernel Construction Migration` | Move default model and service construction into providers and a kernel builder. | P2 accepted | Default profile preserves current behavior and no system captures replaceable owning pointers | planned |
| `P4 System and Domain Composition` | Convert system families into governed contributions bound to stage manifests and extension points. | P3 default profile stable | Minimal, air, naval, ground, and combined profiles validate without a central all-domain registration list | planned |
| `P5 Backend Composition` | Select CPU, CUDA-resident, diagnostics, and future backends through admitted providers. | P2 and backend contracts available | `RuntimeFacade` no longer names a concrete backend and admission remains capability-driven | planned |
| `P6 Evidence and Replay Identity` | Make composition identity part of diagnostics, replay, comparison, and experiment evidence. | P1 schema and P3/P4 realization | Resolved manifest, provider versions, stage-graph hash, and backend profile are stable evidence fields | planned |
| `P7 Cordis Control Plane` | Implement Cordis plugins, configuration loading, dependency resolution, and manifest emission. | Native contract and canonical encoding frozen | Cordis and native producers generate byte-equivalent admitted manifests for shared fixtures | planned |
| `P8 Node Host and Ecosystem` | Add a Node-API host and governed external-plugin packaging without changing the step path. | P7 accepted and host use cases approved | Node-hosted and Python-hosted runs consume the same native composition and parity gates | planned |
| `P9 Migration and Closure` | Remove superseded setters and construction paths, promote stable rules, and close or split residuals. | P1-P8 acceptance evidence | Parent indexes, standards, reference, acceptance, and archive routes are synchronized | planned |

Phases describe dependency order, not a deadline or a reason to weaken the
long-term target. A phase may be split into bounded implementation slices, but
the architecture decisions above require an explicit replacement decision to
change.

## Task Clusters

- [Source-grounded composition census](cordis_simulation_composition_census_20260817.md)
- [P1-B manifest and resolution contract](cordis_simulation_composition_contract_20260817.md)
- [Finite task-cluster plan](cordis_simulation_composition_kernel_task_clusters_20260817.md)
- [Current status and residual register](cordis_simulation_composition_kernel_current_status_20260817.md)
- [Dispatch queue](cordis_simulation_composition_kernel_dispatch_queue_20260817.md)
- [Acceptance contract](cordis_simulation_composition_kernel_acceptance_20260817.md)

## Outputs And Evidence

Expected maintained outputs include:

- versioned composition schema and canonical fixtures;
- native lifecycle and provider libraries with focused tests;
- default and domain/backend composition profiles;
- generated or validated stage graph and composition hash;
- Cordis package and Node host adapter using the same contract;
- Python, C++, and Node host parity evidence;
- lifecycle, replay, failure-injection, batch-scale, and performance reports;
- architecture guards preventing per-step cross-language calls and dual
  composition truth.

Documentation-only creation of this project proves only that the program and
its gates are established. It does not prove runtime composition capability.

P0 validation on `2026-08-17` recorded zero maintained-link issues, zero link
issues sourced from or targeting this new subproject in the full-tree audit, a
clean strict bilingual registry with `74/74` synchronized pairs, `21` passing
documentation-governance tests, and a clean documentation diff check.

P1-A subsequently recorded the current construction and migration baseline: 7
replaceable model/factory providers, 3 kernel-owned service/event objects, 7
published Flecs singleton refs, 82 central component-registration calls, 34
active system-registration calls, 30 exact-stage descriptors, 5 maintained
stage-node manifest entries, and 3 Python-visible runtime ownership tiers. The
full evidence and limitations are in the composition census.

P1-B then froze the host-neutral requested/resolved contract and default
compatibility fixtures. P2-A now provides an independent native realization
library and focused lifecycle evidence: 14 C++ test cases and 430 assertions
pass in the normal MSVC build and again under MSVC AddressSanitizer. The
architecture composition suite records 20 passed tests and 1 environment skip.
This proves the isolated lifecycle boundary, not integration with the current
simulation constructors or behavioral parity.

## Acceptance Gate

This subproject can be marked accepted only when:

- the default native composition is behaviorally and replay equivalent to the
  accepted pre-migration baseline;
- composition resolution is deterministic and has a stable identity;
- truth-affecting providers and stage contributions are immutable between
  simulation barriers authorized for reconfiguration;
- lifecycle failure injection proves complete rollback and no dangling service
  references;
- `SimulationKernel` and `RuntimeFacade` no longer construct concrete default
  models or backends directly;
- stage ordering remains governed by maintained stage contracts rather than
  Cordis plugin order;
- Python and standalone C++ operation do not require Node;
- the Node/Cordis host, when enabled, does not enter the per-step call graph;
- CPU/CUDA parity and representative world-batch performance gates remain
  within separately frozen tolerances;
- composition provenance is exported through maintained diagnostics and replay
  evidence;
- parent indexes, standards, reference surfaces, and archive routes are
  synchronized without expanding capability claims.

## Residuals And Next Steps

Immediate work is P2-B default-provider migration. It must move the existing
default model, factory, event-store, damage-bridge, and weapon-release service
construction behind admitted native providers while preserving the accepted
default behavior and replay baseline. System-family, backend, binding, and
Cordis migration remain separate later slices.

Long-term residuals include plugin authenticity and distribution policy,
multi-process hosting, remote composition catalogs, third-party compatibility,
and live development reload. They remain governed follow-ons and cannot weaken
determinism, provenance, or offline operation.

## Archive

Historical or superseded task packets move under [archive](archive/README.md)
only after current authority, acceptance, and residual routes are preserved.
Stable architecture rules must be promoted to the architecture standards or
reference surfaces before this active package closes.
