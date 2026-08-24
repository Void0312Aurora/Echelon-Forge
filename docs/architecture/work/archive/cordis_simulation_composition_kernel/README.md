# Cordis Simulation Composition Kernel

Status: `2026-08-23` closed bounded default CPU-exact program; P0 authority/documentation, P1-A
composition census, P1-B manifest/resolution contract, and P2-A native
lifecycle baseline passed. P2-B default-provider migration, P2-C0
projection/catalog-lock, P2-C1 default-profile Cordis/native, P3-A default
system-contribution migration, the P3-B default profile projection, P4-A
default backend-provider migration, the bounded P5-A default CPU-exact
composition-evidence slice, the bounded P6-A default-profile Cordis package
maturation slice, the bounded P7-A default CPU-exact host/batch parity slice,
and P8-A migration closure are accepted. Stable rules now live in the
[runtime composition baseline](../../../standards/runtime_composition_baseline.md).
Broader profiles/providers, Node, CUDA parity, external plugin distribution,
and complete replay remain held residuals outside this closure.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `task`
Lifecycle: `archived`
Canonical: `docs/architecture/work/archive/cordis_simulation_composition_kernel/README.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-23`

Related authority:

- [Architecture owner](../../../README.md)
- [Runtime composition baseline](../../../standards/runtime_composition_baseline.md)
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
| Model composition | native provider root | P2-B routes default environment, effects, sensor, acoustic, control, guidance, event-store, release-service, and unit-factory ownership through the admitted native catalog | System-family and broader provider-package expansion remain later slices |
| Service lifetime | generation-governed / fail-closed raw-world quarantine | provider handles are refreshed atomically under wrapper/kernel lifecycle locks; system consumers resolve generation-aware Flecs refs at execution time; remaining raw Flecs access uses an operation-lock-backed RAII lease and permanently closes provider rebuild | Long-lived raw dependency references, typed replacement leases, and broader handover evidence remain residuals |
| System composition | P3-A accepted bounded slice | owner-derived component/system contribution registry validates counts, identities, dependency edges, and stage order; native conformance separately checks the frozen default artifact before realization | profile-specific omission, populated semantic-stage/read-write joins, and broader package admission remain later gates |
| Capability/profile projection | P3-B accepted bounded default-profile slice | versioned profile projection joins capability/policy requirements, owner catalog entries, 83 component contributions, and 34 native system-order entries; Cordis and native conformance revalidate the same join | additional profiles, semantic-stage/read-write metadata, and external package admission remain later gates |
| Backend selection | P4-A accepted bounded default-provider slice | `RuntimeFacade` materializes the generated default CPU-exact request through the native provider catalog; profile, provider, implementation-version, capability, metadata, and construction failures are fail-closed before ownership escapes; independent review returned P0/P1/P2 = 0/0/0 | broader maintained providers, CUDA parity, and evidence expansion |
| Stage semantics | established foundation | maintained stage-node manifests remain semantic authority; the P3-A registry supplies the executable default stage order, while the P3-B projection carries native system order without inventing a second stage ontology | complete semantic-stage/read-write joins remain later gates |
| Composition contract | P1-B pass | versioned requested/resolved manifests, stable service keys/scopes/error codes, canonical hashing, default compatibility fixtures, and fail-closed resolution tests | This is a resource-free contract baseline; it does not construct providers or own runtime resources |
| Native lifecycle kernel | P2-A historical baseline; P2-B native realization now implemented | isolated `ef_composition` library, closed native JSON ingestion, catalog/factory metadata validation, scoped transactional realization, typed generation handles, rollback, rebuild, reverse disposal tests, and the P2-B default-provider realization seam | System-family/backend/binding migration remains later; Cordis producer integration is now the bounded P2-C1 slice |
| Projection and catalog lock | P2-C0 accepted bounded slice | producer-neutral request and owner-derived lock schemas, canonical fixtures, identity recomputation, negative admission matrix, and native `ef_composition` revalidation are wired without lowering into P1-B | P2-C1/P3-B default-profile joins are accepted bounded slices; broader profile/package admission remains residual |
| Cordis integration | P2-C1/P3-B/P6-A accepted bounded default-profile package slice | `packages/cordis-runtime` uses Cordis lifecycle primitives plus a strict repository package/overlay SDK, deterministic four-node dependency resolution, raw-byte pins, canonical provenance, and path-free diagnostics; native conformance validates the unchanged request/lock/projection/manifests; independent review returned P0/P1/P2 = 0/0/0 | truth-changing or broader profiles require owner admission; Node host, external signing/plugins, CUDA, and parity remain later gates |

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
| `P2-B Default Provider Migration` | Move default model/service construction behind admitted native providers and emit the first production composition identity. | P2-A accepted | Default behavior/replay parity holds, raw provider capture is removed, and the resolved plan is evidence-bearing | accepted bounded slice |
| `P2-C0 Projection And Catalog-Lock Contract` | Freeze the producer-neutral `RuntimeCompositionRequest` DTO and owner-derived `AdmittedCatalogLock` artifact, identity, and admission rules. | P2-B production path and identity stable | Cordis has one typed high-level input and one versioned owner-approved catalog lock; offline paths are restricted to canonical low-level artifacts | accepted bounded slice |
| `P2-C1 Cordis Default-Profile Vertical Slice` | Use Cordis primitives plus the repository profile/bundle layer to lower the default request and realize it through the production native path. | P2-C0 accepted | Experiment fixture -> request -> Cordis -> manifest/catalog lock -> native realization passes positive and negative admission cases | accepted bounded default-profile slice; broader expansion residual |
| `P3-A System Contribution Migration` | Compile repository-admitted system packages into the frozen native stage graph. | P2-C1 accepted, unless an explicit independent-stream amendment is approved | Default graph parity holds and no package owns a private pipeline | accepted bounded default-graph slice; broader package/profile admission residual |
| `P3-B Capability And Profile Projection` | Lower capability/policy requests and compatibility profile names into owner-admitted contribution bundles. | P2-C0 and P3-A declaration boundaries stable | Domain labels remain compatibility bundles rather than the permanent composition ontology | accepted bounded default-profile slice; broader profiles residual |
| `P4-A Backend Provider Migration` | Select CPU, CUDA-resident, diagnostics, and future backends through admitted providers. | P2-C1 and backend contracts available | `RuntimeFacade` no longer names a concrete backend and admission remains capability-driven | accepted bounded default-provider slice; broader providers residual |
| `P5-A Composition Evidence Expansion` | Extend the P2-B/P2-C0/P2-C1 identity baseline across graph, backend, native execution owner, replay, and comparison evidence. | production Cordis/native composition exists and P4-A default provider is accepted | Unexplained composition or catalog-lock mismatch is rejected | accepted bounded default CPU-exact slice; broader profiles/backends and caller-language attestation residual |
| `P6-A Cordis Package Maturation` | Complete repository-owned configuration overlays, profile/bundle packages, diagnostics, provenance, and plugin ergonomics over Cordis primitives. | P2-C1 and bounded P5-A accepted; owner contracts available | maintained Cordis composition covers admitted production bundles without becoming a hot-path executor | accepted bounded default-profile package slice; broader/external packages residual |
| `P6-B Node Host Adapter` | Add Node-API hosting only for approved use cases, without changing native/Python availability or step semantics. | P6-A accepted and a host decision approved | Node-hosted runs use the same native owner and parity gates | conditional / held pending host decision |
| `P7-A Host And Batch Parity` | Prove native, Python, and Cordis-produced parity; add Node rows only if P6-B is admitted. | P4-A/P5-A/P6-A accepted | admitted profiles satisfy correctness and approved batch budgets | accepted bounded default CPU-exact slice; Node row held |
| `P8-A Migration Closure` | Remove superseded truth paths, promote stable rules, and close or route residuals. | required native, Cordis, system, backend, evidence, and parity gates accepted | the Cordis program has an admitted producer/native vertical path; optional Node/external ecosystem residuals have named owners | accepted bounded closure |

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
compatibility fixtures. P2-A provided the isolated native realization library;
P2-B now routes the production default kernel through that root, exports
requested/resolved identity and world-scope generation, and allows provider
rebuild only before managed-world mutation or raw Flecs lease exposure. Active
trace frames and managed `SimObject` entities also reject rebuild. Raw Flecs
leases serialize with rebuild/shutdown but are deliberately fail-closed rather
than reopenable. The current focused evidence is recorded in the current-status
document; the bounded P2-C1 default-profile Cordis producer/native vertical
slice is accepted, while broader profile/package expansion remains open.

## P2-B Acceptance Gate

P2-B is accepted at the native production seam when the following bounded
conditions are met:

- the default provider profile is constructed through the native composition
  root, with no concrete default construction or registration-time raw capture
  left in `SimulationKernel`;
- one controlled default trace is behaviorally/replay equivalent to the
  accepted pre-migration baseline;
- one production provider construction/teardown failure path proves rollback
  and absence of dangling service references;
- repeated kernel create/destroy runs complete without lifecycle drift;
- requested/resolved composition identity and world generation remain stable
  and observable;
- the latest implementation batch passes one independent `gpt-5.6-sol/max`
  review with no unresolved P1/P0 finding.

These are the only P2-B acceptance blockers. The existing lifecycle, lease,
mutation-barrier, ABI, and architecture tests support the gate; they are not a
license to add broader backend, host, or performance requirements to this
slice.

## Program Closure

The bounded default CPU-exact program is closed. Stage/profile contribution,
request/catalog-lock projection, the repository Cordis producer/native path,
default backend admission, composition evidence, and native/Python host/batch
parity are accepted. CUDA and Node were never mandatory closure gates; they
remain separately owned held residuals.

## Residuals And Next Steps

P2-B, P2-C0, P2-C1, P3-A, P3-B default-profile projection, and P4-A default
backend-provider slices are accepted bounded slices. The controlled parity
trace, production failure/teardown path, repeated
create/destroy evidence, native revalidation, independent review, registry
admission, and exact default graph order are recorded and green. P3-A replaces
the central component/system calls with an owner-derived registry; it does not
yet populate every semantic stage/read-write field or admit profile-specific
package omission. P3-B binds the named default compatibility profile to its
capability/policy requirements and the owner lock/native graph; it is not a
general multi-profile resolver. P4-A accepts only the maintained default
CPU-exact provider. P5-A binds that slice to request/manifest/lock/profile,
11 provider versions, the 83+2+34 executable graph, exact backend identity,
all realized worlds and five scopes, and strict composition-comparison evidence.
Its host fields identify the native execution owner (`native_cpp/native.v1`),
not the caller language; Python caller-origin attestation is not claimed.
P6-A now pins the exact Cordis/package-lock/profile module/bundle/default
overlay bytes, resolves a deterministic four-node graph, rejects missing,
duplicate, cyclic, conflicting, or truth-changing package input, and seals
provenance to the actual request/lock/profile projection before emitting
path-free diagnostics. It does not own providers, backend selection, component
  contributions, or system order. Broader P2-C1 profiles/providers, CUDA parity,
  binding migration, external signing/plugins, and complete replay remain
  separate held programs. P7-A adds strict native-direct and
local-`ef_py` caller rows joined to the
Cordis-produced artifacts, a frozen action/state/event/window/composition-comparison
semantic reference, and conservative 32-world cold/warm/reset/RSS/teardown
  budgets. Independent `gpt-5.6-sol/max` review returned P0/P1/P2 = 0/0/0.
  P8-A removed the implicit empty-manifest fallback, sealed a live caller and
  truth-path inventory, proved the retired setter/concrete-construction surfaces
  absent, promoted the maintained standard, and routed every optional residual.

Long-term residuals include plugin authenticity and distribution policy,
multi-process hosting, remote composition catalogs, third-party compatibility,
and live development reload. They remain governed follow-ons and cannot weaken
determinism, provenance, or offline operation.

## Archive

This package is archived implementation and acceptance provenance. Its nested
[archive](archive/README.md) retains earlier superseded local records. Current
authority is the maintained runtime composition baseline; this package must not
be treated as an active task queue.
