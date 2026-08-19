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

This subproject introduces Cordis as the long-term declarative composition
control plane for the simulation runtime while preserving the Experiment Face
as the owner of experiment intent and C++ as the authority for deterministic
resolution, realization, and execution. It establishes an explicit projection
from experiment intent into runtime composition, a versioned low-level
composition contract, owner-specific admission, a native lifecycle kernel,
evidence identity, and an optional Node host without placing JavaScript,
asynchronous plugin dispatch, or cross-language service lookup in the per-step
path.

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
- provide a Node-API host adapter only if P6-B is admitted by a separate host
  decision after the native composition contract is stable;
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

The target is a layered composition architecture:

1. The Experiment Face owns user-visible experiment intent across simulation,
   policy, and evaluation dimensions.
2. A typed runtime projection converts that intent into capability, policy,
   profile, and configuration requirements. The frozen P1-B requested manifest
   remains the canonical low-level interchange contract, not the only future
   authoring abstraction.
3. Cordis is the required long-term declarative composition control plane. It
   exclusively lowers maintained high-level runtime requests through Cordis
   primitives plus a repository-owned, DeepSeek-Harness-style profile/bundle
   layer into the canonical low-level request. Native and Python offline paths
   may consume canonical low-level manifests or generated frozen profiles; they
   do not independently lower arbitrary high-level requests.
4. Model, system, backend, domain, evidence, and security owners admit their own
   implementation categories into an `AdmittedCatalogLock`; a common lifecycle
   registry does not grant semantic admission.
5. A native C++ composition compiler/root revalidates, resolves, realizes, and
   freezes the exact runtime plan, owns resources, and performs deterministic
   teardown and rollback.
6. Flecs, the native scheduler, backends, and episode/runtime owners retain
   executable semantics. Cordis lifecycle events are administrative, and the
   maintained step path contains no Cordis or binding call.

The complete design is in
[Cordis simulation composition architecture](cordis_simulation_composition_kernel_architecture.md).

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Authority and Boundary` | Establish the owner, target architecture, non-goals, task clusters, and acceptance model. | User authorization and inspected repository baseline | Bilingual project documents and parent architecture links pass document gates | pass |
| `P1 Composition Contract` | Freeze manifest schema, service keys, plugin descriptors, scopes, compatibility rules, and deterministic resolution. | P0 accepted | Schema fixtures, validation rules, canonical encoding, and contract tests exist | pass |
| `P2-A Native Lifecycle Kernel` | Implement the isolated C++ catalog, scoped transaction, replacement, rollback, freeze, and deterministic disposal substrate. | P1 contract frozen | Focused native and architecture gates pass | pass |
| `P2-B Default Provider Migration` | Move default model/service construction behind admitted native providers and emit the first production composition identity. | P2-A accepted | Default behavior/replay parity holds, raw provider capture is removed, and the resolved plan is evidence-bearing | implementation / pending review |
| `P2-C0 Projection And Catalog-Lock Contract` | Freeze the producer-neutral `RuntimeCompositionRequest` DTO and owner-derived `AdmittedCatalogLock` artifact, identity, and admission rules. | P2-B production path and identity stable | Cordis has one typed high-level input and one versioned owner-approved catalog lock; offline paths are restricted to canonical low-level artifacts | planned |
| `P2-C1 Cordis Default-Profile Vertical Slice` | Use Cordis primitives plus the repository profile/bundle layer to lower the default request and realize it through the production native path. | P2-C0 accepted | Experiment fixture -> request -> Cordis -> manifest/catalog lock -> native realization passes positive and negative admission cases | planned |
| `P3-A System Contribution Migration` | Compile repository-admitted system packages into the frozen native stage graph. | P2-C1 accepted, unless an explicit independent-stream amendment is approved | Default graph parity holds and no package owns a private pipeline | planned |
| `P3-B Capability And Profile Projection` | Lower capability/policy requests and compatibility profile names into owner-admitted contribution bundles. | P2-C0 and P3-A declaration boundaries stable | Domain labels remain compatibility bundles rather than the permanent composition ontology | planned |
| `P4-A Backend Provider Migration` | Select CPU, CUDA-resident, diagnostics, and future backends through admitted providers. | P2-C1 and backend contracts available | `RuntimeFacade` no longer names a concrete backend and admission remains capability-driven | planned |
| `P5-A Composition Evidence Expansion` | Extend the P2-B/P2-C0/P2-C1 identity baseline across graph, backend, host, replay, and comparison evidence. | production Cordis/native composition exists | Unexplained composition or catalog-lock mismatch is rejected | planned |
| `P6-A Cordis Package Maturation` | Complete repository-owned configuration overlays, profile/bundle packages, diagnostics, provenance, and plugin ergonomics over Cordis primitives. | P2-C1 accepted and owner contracts available | maintained Cordis composition covers admitted production bundles without becoming a hot-path executor | planned |
| `P6-B Node Host Adapter` | Add Node-API hosting only for approved use cases, without changing native/Python availability or step semantics. | P6-A accepted and a host decision approved | Node-hosted runs use the same native owner and parity gates | conditional / held pending host decision |
| `P7-A Host And Batch Parity` | Prove native, Python, and Cordis-produced parity; add Node rows only if P6-B is admitted. | P4-A/P5-A/P6-A accepted | admitted profiles satisfy correctness and approved batch budgets | planned |
| `P8-A Migration Closure` | Remove superseded truth paths, promote stable rules, and close or route residuals. | required native, Cordis, system, backend, evidence, and parity gates accepted | the Cordis program has an admitted producer/native vertical path; optional Node/external ecosystem residuals have named owners | planned |

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
- [Independent program architecture review](../../../reviews/cordis_simulation_composition_program_review_20260817.md)
- [Active-owner response to the program architecture review](../../../reviews/cordis_simulation_composition_program_review_response_20260817.md)

## Outputs And Evidence

Expected maintained outputs include:

- versioned composition schema and canonical fixtures;
- native lifecycle and provider libraries with focused tests;
- default and domain/backend composition profiles;
- generated or validated stage graph and composition hash;
- Cordis package using the same low-level contract and a separately approved
  Node host adapter when required;
- Python, C++, and Cordis-producer parity evidence, plus Node host parity when
  that adapter is admitted;
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
published Flecs singleton refs, 83 central component-registration calls, 34
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
- experiment intent reaches Cordis through an explicit runtime-composition
  projection, and owner-specific admission remains visible in the resolved
  catalog lock;
- at least one repository-owned Cordis default-profile path emits the canonical
  request consumed and revalidated by the native composition compiler;
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
construction behind admitted native providers, preserve the accepted default
behavior/replay baseline, and export the first production composition identity.
P2-C0 follows to freeze the high-level request and owner-derived catalog-lock
artifacts without creating a second resolver. P2-C1 then provides the first
Cordis vertical slice: Cordis primitives plus the repository profile/bundle
layer must lower the default request into the canonical manifest/catalog lock
that native code revalidates and realizes. System-family, backend, and binding
migrations remain separate later slices; Node hosting remains conditional
rather than a closure prerequisite for the Cordis producer/native path.

Long-term residuals include plugin authenticity and distribution policy,
multi-process hosting, remote composition catalogs, third-party compatibility,
and live development reload. They remain governed follow-ons and cannot weaken
determinism, provenance, or offline operation.

## Archive

Historical or superseded task packets move under [archive](archive/README.md)
only after current authority, acceptance, and residual routes are preserved.
Stable architecture rules must be promoted to the architecture standards or
reference surfaces before this active package closes.
