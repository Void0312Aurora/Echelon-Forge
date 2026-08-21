# Cordis Simulation Composition Kernel Task Clusters

Status: `2026-08-20` finite delivery plan for the
[Cordis Simulation Composition Kernel](README.md); P0, P1-A, and P1-B passed,
P2-A passed as the native lifecycle baseline, and P2-B is implemented pending
independent review and residual evidence.

Language:

- English canonical: `cordis_simulation_composition_kernel_task_clusters_20260817.md`
- Chinese companion: [cordis_simulation_composition_kernel_task_clusters_20260817.zh.md](cordis_simulation_composition_kernel_task_clusters_20260817.zh.md)

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_task_clusters_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-20`

## Boundary Decision

This program introduces Cordis as its long-term declarative composition control
plane, backed by a native composition kernel, versioned low-level manifest,
owner-specific admission locks, provider/lifecycle infrastructure, governed
system contributions, and composition evidence. The Experiment Face continues
to own experiment intent; Cordis owns declarative profile/plugin/service
composition; applicable domain/runtime owners admit implementations; native C++
owns deterministic realization and execution. A Node host is conditional. The
program must preserve one runtime truth path, backend capability admission,
replay identity, and offline C++/Python operation.

Task labels below are local dispatch identifiers. They must not enter public
APIs, runtime strings, schema field names, or production type names.

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A Authority Scaffold` | main thread | n/a | Create the bilingual active subproject, architecture, status, queue, acceptance, archive, and parent routes. | `docs/architecture/work/active/cordis_simulation_composition_kernel/**`, `docs/architecture/README*`, selected bilingual registry rows | runtime code, capability claims | document metadata, local link audit, bilingual pair audit, `git diff --check` | all required files exist and the architecture owner routes this project | serial first cluster | 1 + 1 repair | pass |
| `P1-A Composition Census` | main thread | n/a | Inventory every constructor, setter, raw capture, service ref, system registration, backend selection, reset boundary, stage registry, binding entry, and relevant test. | project current-status/evidence files, optional generated inventory under this subproject | runtime edits, design changes hidden in inventory | reproducible `rg` inventory, direct ownership trace, and cited file-line evidence | each composition edge has owner, scope, replacement rule, and migration disposition | after P0-A | 1 + 1 repair | pass |
| `P1-B Manifest And Resolution Contract` | main thread | n/a | Freeze host-neutral manifest schema, plugin/provider descriptors, service keys, scopes, conflict rules, canonical encoding, versioning, and resolution order. | `src/runtime/contracts/**`, schema producer inputs, `tests/architecture/composition/**`, subproject design updates | provider implementation, Node host, dynamic download | schema freshness, canonical fixture, invalid-manifest matrix, deterministic permutation tests | native and future Cordis producers can target one unambiguous contract | after P1-A | 2 + 1 repair | pass |
| `P2-A Native Lifecycle Kernel` | main thread | n/a | Implement catalog, resolver, validator, scopes, transaction, freeze, typed handles, effects, rollback, and deterministic disposal. | new approved `src/runtime/composition/**`, focused CMake targets, `src/tests/test_composition_lifecycle.cpp`, architecture guards | migrating default providers, systems, backends, bindings, or Cordis in the same slice | focused C++ tests, MSVC AddressSanitizer, failure injection, architecture contract suite | scope isolation, failure atomicity, deterministic resolution, and teardown gates pass | after P1-A/P1-B; serial with P2-B on shared contracts | 3 + 1 repair | pass |
| `P2-B Default Provider Migration` | engine owner | n/a | Move default model, factory, event-store, bridge, and release-service construction behind native providers and a kernel builder; publish the first production resolved-plan identity. | `src/core/engine/**`, `src/models/**` composition entries, approved provider files, focused tests, bounded evidence DTO joins | system-family split, Cordis package, Node host | one controlled behavior/replay baseline, one provider failure/teardown path, repeated create/destroy, no dangling provider capture, identity roundtrip/mismatch tests | default compatibility profile constructs the current kernel without concrete model construction in `SimulationKernel`, and the run exports stable requested/resolved identity | after P2-A; serial with P2-C0 on production identity/contract seams | 3 + 1 repair | implemented / pending independent review |
| `P2-C0 Projection And Catalog-Lock Contract` | future composition-contract owner with category-owner sign-off | n/a | Freeze the producer-neutral `RuntimeCompositionRequest` DTO and deterministic owner-derived `AdmittedCatalogLock` artifact, including versions, canonical bytes, hashes, category authority, provenance, and positive/negative admission rules. | new bounded high-level request/catalog-lock contract inputs under approved `src/runtime/contracts/**`, generators, fixtures, architecture tests, subproject docs | changing P1-B low-level fields, Cordis package implementation, Node host, system migration | schema/header freshness, deterministic lock generation, stable identity, category-owner matrix, unknown/unadmitted/version/provenance rejection, offline low-level-only guard | Cordis has one typed high-level request and one verifiable owner-approved lock; native/Python offline paths cannot lower arbitrary high-level requests | after P2-B production identity is stable | 2 + 1 repair | planned |
| `P2-C1 Cordis Default-Profile Vertical Slice` | future Cordis integration owner | n/a | Use Cordis plugin/context/service/injection/event/effect primitives plus the repository-owned profile/bundle layer to lower the production default request and realize it through the native path. | bounded `packages/cordis-runtime/**`, package manifests/lockfiles, P2-C0 adapters/artifacts, canonical fixtures, end-to-end conformance tests, subproject docs | Node-API hosting, system-family split, external plugins, full SDK ergonomics, hot-path services | Experiment fixture -> request -> Cordis -> manifest/catalog lock -> native realization; canonical bytes/hashes; real provider identity; negative admission; offline-native regression | the real default path proves the complete Experiment projection/Cordis/owner-lock/native chain without a private Cordis catalog | after P2-C0; before any later implementation cluster unless separately authorized | 2 + 1 repair | planned |
| `P3-A System Contribution Migration` | future scheduler owner | n/a | Replace the central all-domain registration list with admitted component/system/stage contributions compiled into the existing scheduler contracts. | `src/systems/**` registration seams, `src/core/engine/simulation_kernel_systems.cpp`, `src/runtime/contracts/**`, composition tests | replacing Flecs, changing semantic lifecycle, private domain pipelines | exact default stage-order parity, manifest validation, graph conflict tests | compatibility profile reproduces the accepted default graph and profiles can omit unneeded families | after P2-C1; earlier independent-stream dispatch requires an explicit architecture-owner amendment proving no shared contract/write-set dependency | 4 + 1 repair | planned |
| `P3-B Capability And Profile Projection` | future cross-domain integration owner | n/a | Lower typed capability/policy requests and compatibility profile names into owner-admitted model/component/system/stage bundles. | owner-approved projection/profile contracts, domain integration tests, composition fixtures | making air/naval/ground labels the permanent ontology, promoting domain maturity, implementing missing behavior | projection validation, forbidden dependency guards, owner contract suites | capability requirements are primary; named domain profiles are explicit compatibility bundles that cannot bypass owner standards | after P2-C0 and P3-A declarations; owner rows may parallel when write sets are disjoint | 2 + 1 repair per bundle family | planned |
| `P4-A Backend Provider Migration` | future backend owner | n/a | Move CPU, CUDA-resident, diagnostics, and future backend selection behind provider admission without changing facade semantics. | `src/runtime/facade/**`, `src/runtime/providers/**`, backend contracts/tests, CMake | new backend semantics, GPU parity relaxation | facade contract tests, backend admission matrix, CPU/CUDA focused parity suites | `RuntimeFacade` no longer constructs a concrete backend and rejected profiles fail before run | after P2-C1; earlier independent-stream dispatch requires an explicit architecture-owner amendment | 3 + 1 repair | planned |
| `P5-A Composition Evidence Expansion` | future evidence owner | n/a | Extend the P2-B/P2-C0/P2-C1 identity baseline with provider versions, graph hash, backend profile, host mode, catalog-lock identity, and scope generation through diagnostics/replay/comparison contracts. | evidence/replay contracts, facade diagnostics, schema generators, focused tests | claiming full replay for unsupported backend/state surfaces | DTO freshness, roundtrip, mismatch rejection, deterministic hash fixtures | maintained runs identify their realized composition/catalog lock and replay rejects unexplained mismatch | after P2-C1 and relevant P3/P4 joins | 2 + 1 repair | planned |
| `P6-A Cordis Package Maturation` | future Cordis integration owner | n/a | Extend the accepted P2-C1 producer with repository-owned profile/bundle packages, configuration overlays, diagnostics, provenance, dependency resolution, and plugin SDK ergonomics over Cordis primitives. | approved `packages/cordis-runtime/**`, workspace manifests/lockfiles, fixtures, docs | simulation stepping in JavaScript, arbitrary external native plugins, replacing owner admission | package tests, projection/schema conformance, canonical parity, provenance and diagnostics tests | maintained Cordis bundles emit only owner-admitted requests accepted identically by the native validator | after P2-C1 and applicable P3/P4 owner contracts | 3 + 1 repair | planned |
| `P6-B Node Host Adapter` | future bindings owner | n/a | Add a Node-API adapter over coarse `RuntimeFacade` use cases and native composition construction if an approved host use case exists. | approved `src/interfaces/node/**`, CMake/package wiring, binding tests | raw ECS exposure, per-stage callbacks, replacing nanobind | if admitted: configure/load/reset/setup/inject/advance/evaluate/export/diagnostics tests and leak/teardown tests | if admitted, Node-hosted runs use the same native runtime and contain no binding call in stage execution | after P6-A and explicit host decision | 3 + 1 repair | conditional / held pending host decision |
| `P7-A Host And Batch Parity` | future integration owner | n/a | Prove native, Python, and Cordis-produced compositions preserve deterministic behavior and batch budgets; include Node only if P6-B is approved. | integration tests, benchmark/probe tools, evidence package, bounded fixes | tuning away semantic mismatches, broad unrelated optimization | producer/host parity matrix, replay comparison, large-batch memory/startup/throughput measurements | frozen profiles satisfy correctness and separately approved regression budgets | after P4-A/P5-A/P6-A; Node rows also require P6-B | 2 + 1 repair | planned |
| `P8-A Migration Closure` | main integration owner | n/a | Remove superseded setters/construction truth, promote stable rules, record accepted scope, split residuals, and synchronize indexes/archive. | affected composition code, architecture standards/reference, subproject acceptance/archive, owner indexes | erasing historical evidence, silently widening plugin admission, treating Cordis as optional completion evidence | full acceptance matrix, Cordis/native vertical conformance, link/bilingual audits, caller inventory, retained compatibility proof | no dual composition path remains; an admitted Cordis producer/native path is maintained; optional Node/external ecosystem residuals have named owners | serial final cluster | 2 + 1 repair | planned |

## Dispatch Rules

- Every implementation packet maps to exactly one cluster and one bounded write
  set above.
- P0, contract freeze, shared runtime ownership, acceptance, and closure remain
  serial.
- P2-B, P2-C0, and P2-C1 are separate bounded slices but serial on their shared
  production identity, projection, catalog-lock, and default-profile contracts.
  P2-C1 is required for overall program closure; P2-B may retain its own bounded
  native acceptance.
- No implementation cluster after P2-C0 may be released before P2-C1 unless an
  explicit architecture-owner amendment authorizes an independent stream and
  proves that it cannot create or alter a competing lowering/catalog authority.
- Read-only census work may run in parallel with schema design, but findings
  must be integrated before P2 construction begins.
- Two workers must not concurrently edit composition contracts, the same
  provider family, the central stage registry, facade ownership, or status
  authority.
- Domain-profile work may parallel only after common service and stage contracts
  are frozen and write sets are disjoint.
- A cluster that reaches its round cap stops for scope review; it does not create
  an unbounded repair wave.
- Runtime changes require proportionate build, test, parity, lifecycle, and
  evidence validation; documentation-only checks cannot close them.
- Every material implementation or repair cluster receives an independent
  read-only review after its commits are stable. The default matrix covers
  lifecycle/ownership, contract/canonicalization, and integration/CI/docs using
  `gpt-5.6-sol` at `max` reasoning unless an explicit later decision changes the
  review configuration. Unresolved P1 findings block the next cluster.
- Follow the
  [Subagent Usage Policy](../../../../engineering/automation/standards/subagent_usage_policy.md)
  whenever work is delegated.

## Worker Packet Requirements

```text
cluster:
status: pass | partial | blocked | failed
baseline revision and configuration:
touched files:
commands and outcomes:
composition/lifecycle claims proven:
determinism or replay impact:
performance evidence:
remaining paths:
behavior risks:
integration notes:
```

Every packet must also state whether it introduced or removed a composition
truth source, cross-language call, provider replacement path, compatibility
wrapper, or runtime dependency.

## Validation Plan

Documentation boundary:

```powershell
git diff --check -- docs/architecture
python tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/engineering/documentation/reference/bilingual_document_clusters.json
python tools/maintenance/translate_docs_batch.py clusters --root docs --registry docs/engineering/documentation/reference/bilingual_document_clusters.json
```

P1 and later clusters must add exact commands after the affected targets are
known. The minimum expected runtime matrix includes:

- focused C++ lifecycle and composition tests;
- architecture ownership and forbidden-dependency tests;
- manifest schema and canonical-hash fixtures;
- default CPU behavior and replay comparison;
- backend admission and CPU/CUDA parity where applicable;
- Python binding regression tests;
- Cordis producer lifecycle/conformance tests from P2-C1 onward;
- Node host tests only if P6-B is explicitly admitted;
- representative multi-world startup, memory, and step-throughput probes.

## Acceptance Criteria

- One versioned composition contract is shared by native and Cordis producers.
- Experiment intent, Cordis declarative composition, owner-specific admission,
  and native realization are separate explicit authorities.
- Native resolution and realization are deterministic, transactional, scoped,
  and evidence-bearing.
- Flecs and the native stage scheduler remain simulation execution authorities.
- Concrete default model/backend construction leaves kernel/facade constructors.
- No replaceable provider can leave stale references in registered systems.
- System and domain contributions pass existing stage and capability admission.
- Cordis and Node are absent from maintained per-step call graphs.
- Native and Python operation remain independent of Node installation.
- Host and backend parity failures cannot be hidden by compatibility fallbacks.
- Accepted runtime behavior, docs, indexes, evidence, and archive state agree.

## Residual Map

Immediate:

- use the accepted P1-A census, P1-B contract, and P2-A lifecycle kernel as
  immutable inputs;
- implement P2-B without starting system-family, backend, Cordis-package, or
  binding migration in the same slice, while publishing the first production
  composition identity;
- preserve the existing default behavior/replay baseline and eliminate the
  environment-model raw capture before claiming provider replacement safety;
- dispatch P2-C0 after P2-B to freeze the request/catalog-lock authority, then
  P2-C1 to prove Cordis primitives plus the repository profile/bundle layer
  against the actual default provider path, not against fixtures alone.

Follow-on:

- provider and system migration;
- backend admission migration;
- composition evidence expansion;
- Cordis package maturation and a separately approved Node host;
- plugin SDK ergonomics and development tooling.

Deferred to separately accepted programs:

- public plugin marketplace;
- remote package registry and automatic downloads;
- sandboxing untrusted native plugins;
- distributed multi-process simulation ownership;
- truth-affecting live hot reload;
- general replacement of current bindings or ECS.
