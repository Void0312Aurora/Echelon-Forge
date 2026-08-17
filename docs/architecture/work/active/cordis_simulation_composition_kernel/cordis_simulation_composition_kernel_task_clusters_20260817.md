# Cordis Simulation Composition Kernel Task Clusters

Status: `2026-08-17` finite delivery plan for the
[Cordis Simulation Composition Kernel](README.md); P0, P1-A, and P1-B passed,
P2-A passed as an isolated native lifecycle baseline, and P2-B is next.

Language:

- English canonical: `cordis_simulation_composition_kernel_task_clusters_20260817.md`
- Chinese companion: [cordis_simulation_composition_kernel_task_clusters_20260817.zh.md](cordis_simulation_composition_kernel_task_clusters_20260817.zh.md)

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_task_clusters_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

## Boundary Decision

This program may introduce a Cordis control plane, native composition kernel,
versioned manifest, provider and lifecycle infrastructure, governed system
contributions, composition evidence, and an optional Node host. It must preserve
the maintained simulation architecture: native deterministic stage execution,
one runtime truth path, backend capability admission, replay identity, and
offline C++/Python operation.

Task labels below are local dispatch identifiers. They must not enter public
APIs, runtime strings, schema field names, or production type names.

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A Authority Scaffold` | main thread | n/a | Create the bilingual active subproject, architecture, status, queue, acceptance, archive, and parent routes. | `docs/architecture/work/active/cordis_simulation_composition_kernel/**`, `docs/architecture/README*`, selected bilingual registry rows | runtime code, capability claims | document metadata, local link audit, bilingual pair audit, `git diff --check` | all required files exist and the architecture owner routes this project | serial first cluster | 1 + 1 repair | pass |
| `P1-A Composition Census` | main thread | n/a | Inventory every constructor, setter, raw capture, service ref, system registration, backend selection, reset boundary, stage registry, binding entry, and relevant test. | project current-status/evidence files, optional generated inventory under this subproject | runtime edits, design changes hidden in inventory | reproducible `rg` inventory, direct ownership trace, and cited file-line evidence | each composition edge has owner, scope, replacement rule, and migration disposition | after P0-A | 1 + 1 repair | pass |
| `P1-B Manifest And Resolution Contract` | main thread | n/a | Freeze host-neutral manifest schema, plugin/provider descriptors, service keys, scopes, conflict rules, canonical encoding, versioning, and resolution order. | `src/runtime/contracts/**`, schema producer inputs, `tests/architecture/composition/**`, subproject design updates | provider implementation, Node host, dynamic download | schema freshness, canonical fixture, invalid-manifest matrix, deterministic permutation tests | native and future Cordis producers can target one unambiguous contract | after P1-A | 2 + 1 repair | pass |
| `P2-A Native Lifecycle Kernel` | main thread | n/a | Implement catalog, resolver, validator, scopes, transaction, freeze, typed handles, effects, rollback, and deterministic disposal. | new approved `src/runtime/composition/**`, focused CMake targets, `src/tests/test_composition_lifecycle.cpp`, architecture guards | migrating default providers, systems, backends, bindings, or Cordis in the same slice | focused C++ tests, MSVC AddressSanitizer, failure injection, architecture contract suite | scope isolation, failure atomicity, deterministic resolution, and teardown gates pass | after P1-A/P1-B; serial with P2-B on shared contracts | 3 + 1 repair | pass |
| `P2-B Default Provider Migration` | future engine owner | n/a | Move default model, factory, event-store, bridge, and release-service construction behind native providers and a kernel builder. | `src/core/engine/**`, `src/models/**` composition entries, approved provider files, focused tests | system-family split, Node/Cordis integration | default behavior/replay baseline, lifecycle tests, no dangling provider capture | default compatibility profile constructs the current kernel without concrete model construction in `SimulationKernel` | after P2-A; serial with P3-A when engine registration files overlap | 3 + 1 repair | ready |
| `P3-A System Contribution Migration` | future scheduler owner | n/a | Replace the central all-domain registration list with admitted component/system/stage contributions compiled into the existing scheduler contracts. | `src/systems/**` registration seams, `src/core/engine/simulation_kernel_systems.cpp`, `src/runtime/contracts/**`, composition tests | replacing Flecs, changing semantic lifecycle, private domain pipelines | exact default stage-order parity, manifest validation, graph conflict tests | compatibility profile reproduces the accepted default graph and profiles can omit unneeded families | after P2-B and P1-B | 4 + 1 repair | planned |
| `P3-B Domain Composition Profiles` | future cross-domain integration owner | n/a | Define minimal, common, air, naval, ground, and combined-domain profiles with explicit capability and extension-point admission. | owner-approved profile/config contracts, domain integration tests, composition fixtures | promoting domain maturity, implementing missing domain behavior | profile validation, forbidden dependency guards, domain contract suites | each profile has explicit contributions and cannot bypass owner standards | after P3-A declarations; domain rows may parallel when write sets are disjoint | 2 + 1 repair per profile family | planned |
| `P4-A Backend Provider Migration` | future backend owner | n/a | Move CPU, CUDA-resident, diagnostics, and future backend selection behind provider admission without changing facade semantics. | `src/runtime/facade/**`, `src/runtime/providers/**`, backend contracts/tests, CMake | new backend semantics, GPU parity relaxation | facade contract tests, backend admission matrix, CPU/CUDA focused parity suites | `RuntimeFacade` no longer constructs a concrete backend and rejected profiles fail before run | after P2-A/P1-B; may parallel P3-B if contracts do not overlap | 3 + 1 repair | planned |
| `P5-A Composition Evidence` | future evidence owner | n/a | Export requested/resolved manifest identity, provider versions, graph hash, backend profile, host mode, and scope generation through diagnostics/replay/comparison contracts. | evidence/replay contracts, facade diagnostics, schema generators, focused tests | claiming full replay for unsupported backend/state surfaces | DTO freshness, roundtrip, mismatch rejection, deterministic hash fixtures | maintained runs identify their realized composition and replay rejects unexplained mismatch | after P1-B and at least P2-B/P3-A | 2 + 1 repair | planned |
| `P6-A Cordis Control-Plane Package` | future Cordis integration owner | n/a | Add repository-owned Cordis packages, plugin descriptors, configuration loading, dependency resolution, and canonical manifest emission. | approved `packages/cordis-runtime/**`, Node workspace manifests/lockfiles, fixtures, docs | simulation stepping in JavaScript, arbitrary external native plugins | package tests, schema conformance, canonical-byte parity with native fixtures | Cordis emits only manifests accepted identically by the native validator | after P1-B and native validator stability | 3 + 1 repair | planned |
| `P6-B Node Host Adapter` | future bindings owner | n/a | Add a Node-API adapter over coarse `RuntimeFacade` use cases and native composition construction. | approved `src/interfaces/node/**`, CMake/package wiring, binding tests | raw ECS exposure, per-stage callbacks, replacing nanobind | configure/load/reset/setup/inject/advance/evaluate/export/diagnostics tests, leak/teardown tests | Node-hosted runs use the same native runtime and contain no binding call in stage execution | after P6-A and P2/P4 native ownership | 3 + 1 repair | planned |
| `P7-A Host And Batch Parity` | future integration owner | n/a | Prove native, Python, and Node hosts realize equivalent admitted compositions and preserve batch-scale determinism and performance budgets. | integration tests, benchmark/probe tools, evidence package, bounded fixes | tuning away semantic mismatches, broad unrelated optimization | host parity matrix, replay comparison, large-batch memory/startup/throughput measurements | frozen profiles satisfy correctness and separately approved regression budgets | after P4-A/P5-A/P6-B | 2 + 1 repair | planned |
| `P8-A Migration Closure` | main integration owner | n/a | Remove superseded setters/construction truth, promote stable rules, record accepted scope, split residuals, and synchronize indexes/archive. | affected composition code, architecture standards/reference, subproject acceptance/archive, owner indexes | erasing historical evidence, silently widening plugin admission | full acceptance matrix, link/bilingual audits, caller inventory, retained compatibility proof | no dual composition path remains and every residual has a maintained owner | serial final cluster | 2 + 1 repair | planned |

## Dispatch Rules

- Every implementation packet maps to exactly one cluster and one bounded write
  set above.
- P0, contract freeze, shared runtime ownership, acceptance, and closure remain
  serial.
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
python tools/maintenance/translate_docs_batch.py audit --root docs --strict-bilingual-only
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
- Node host tests once P6-B exists;
- representative multi-world startup, memory, and step-throughput probes.

## Acceptance Criteria

- One versioned composition contract is shared by native and Cordis producers.
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
- implement P2-B without starting system-family, backend, Cordis, or binding
  migration in the same slice;
- preserve the existing default behavior/replay baseline and eliminate the
  environment-model raw capture before claiming provider replacement safety.

Follow-on:

- provider and system migration;
- backend admission migration;
- composition evidence;
- Cordis package and Node host;
- plugin SDK ergonomics and development tooling.

Deferred to separately accepted programs:

- public plugin marketplace;
- remote package registry and automatic downloads;
- sandboxing untrusted native plugins;
- distributed multi-process simulation ownership;
- truth-affecting live hot reload;
- general replacement of current bindings or ECS.
