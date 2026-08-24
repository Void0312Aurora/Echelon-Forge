# Cordis Simulation Composition Kernel Current Status — 2026-08-17

Status: `2026-08-23` P2-B production-provider migration, P2-C0
projection/catalog-lock, P2-C1 default-profile Cordis/native, P3-A default
system-contribution migration, P3-B default-profile projection, P4-A default
backend-provider migration, P5-A default CPU-exact composition evidence, and
P6-A default-profile Cordis package maturation, P7-A default CPU-exact host and
batch parity, and P8-A migration closure are accepted. The bounded default
CPU-exact program is closed and archived; current authority is the maintained
runtime composition baseline. Broader profiles/providers, Node, CUDA parity,
external plugin distribution, and complete replay remain held residuals.

Language:

- English canonical: `cordis_simulation_composition_kernel_current_status_20260817.md`
- Chinese companion: [cordis_simulation_composition_kernel_current_status_20260817.zh.md](cordis_simulation_composition_kernel_current_status_20260817.zh.md)

Document kind: `task`
Lifecycle: `archived`
Canonical: `docs/architecture/work/archive/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_current_status_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-23`

Parent: [Cordis Simulation Composition Kernel](README.md)

Contract baseline:
[P1-B manifest and resolution contract](cordis_simulation_composition_contract_20260817.md).

## Change At This Checkpoint

- created and validated an owner-local active architecture subproject;
- established the Experiment Face as experiment-intent authority, an explicit
  runtime projection seam, Cordis as the required long-term declarative
  composition control plane, owner-specific implementation admission, and the
  native composition kernel as deterministic realization/lifecycle authority;
- defined a host-neutral manifest, deterministic freeze, evidence, and offline
  deployment direction;
- split the program into finite, independently accepted slices while retaining
  a Cordis producer/native vertical path as an overall closure requirement and
  treating Node hosting as conditional;
- completed the source-grounded P1-A census of constructors, setters, raw
  captures, service refs, system registrations, backend selection, lifecycle,
  stage registries, bindings, build ownership, and relevant tests;
- classified 7 replaceable providers, 3 kernel-owned service/event objects, 83
  central component registrations, 34 active system registrations, 30 exact
  stages, 5 maintained stage-node manifests, and 3 Python runtime tiers;
- made the raw environment capture, split backend admission/materialization,
  and three scheduling truth surfaces hard P1-B constraints;
- implemented a host-neutral requested/resolved manifest contract with five
  scopes, 13 stable service keys, stable failure codes, explicit service
  bindings, compatibility rules, and self-excluding SHA-256 identity;
- added generated schema and default compatibility fixtures covering 11
  providers, 83 components, and 34 systems, plus a fail-closed invalid matrix
  and permutation-stability tests;
- added an isolated `ef_composition` static library with no engine, facade,
  Flecs, binding, or Cordis dependency;
- implemented closed requested/resolved JSON ingestion, native SHA-256
  recomputation, typed-scope guards, frozen factory identity, lifecycle state
  transitions, scoped transactional construction, typed generation handles,
  failure rollback, replacement-aware barrier rebuild, handover admission,
  deterministic reverse disposal, value-snapshot identity accessors, serialized
  lifecycle control, reentrant wrapper lifetime retention, full plugin/factory
  identity checks, in-process semantic service-type identity checks, and
  idempotent shutdown;
- passed 15 focused native lifecycle cases with 443 assertions and 41 default
  simulation smoke cases with 889 assertions; world-batch compatibility also
  verifies snapshot-owned visual scenes across shutdown; composition architecture/contract
  tests are 32 passed with one toolchain-dependent `g++` skip;
- migrated the default model/event/service ownership into admitted native
  providers and a composition-root builder; systems now resolve replaceable
  services through generation-aware Flecs refs rather than registration-time
  raw captures;
- implemented the bounded P4-A default backend-provider seam: `RuntimeFacade`
  no longer names or constructs `FlecsCpuBackend`, while the native provider
  catalog rejects unknown, diagnostics-only, unmaintained, mismatched, duplicate,
  or capability-invalid requests before invoking a factory. Independent
  `gpt-5.6-sol` / `max` review returned P0/P1/P2 = 0/0/0.
- implemented and accepted bounded P6-A package maturation: the public Cordis
  SDK defines strict repository package/overlay values, resolves four pinned
  dependency nodes deterministically, keeps every raw hash input LF-stable,
  rejects dependency/overlay/path/hash/version forgery, seals provenance to the
  actual request/lock/profile projection, and emits path-free diagnostics only
  after revalidation. Node package tests pass 20/20, the composition architecture
  suite passes 54 with one local `g++`-dependent skip, focused native CTest passes
  4/4, and independent `gpt-5.6-sol` / `max` review returned P0/P1/P2 = 0/0/0.

## Maturity Matrix

| Surface | State | Current evidence | What remains |
| --- | --- | --- | --- |
| Architecture authority | accepted / promoted | [runtime composition baseline](../../../standards/runtime_composition_baseline.md), archived evidence package, parent route, and document validation | owner-approved amendments only |
| Composition census | P1-A pass | [source-grounded census](cordis_simulation_composition_census_20260817.md) with owner/scope/replacement/disposition tables | keep census guard synchronized until generated evidence replaces it |
| Manifest contract | P1-B pass / repaired | requested/resolved generated schemas, pure C++ value types, canonical fixtures, invalid corpus, deterministic tests, and native requested/resolved hash recomputation | keep producer/schema/header parity guarded; prove byte-equivalent Cordis output and artifact provenance before external admission |
| Native lifecycle kernel | P2-A pass / production-enabling substrate | `ef_composition`, typed-scope guards, immutable factory metadata, lifecycle state machine, scoped transactions, replacement-aware rebuild, handover admission, identity accessors, rollback/disposal tests, CI wiring, and MSVC ASan evidence | real registry handover and broader native acceptance evidence |
| Model/provider migration | P2-B accepted bounded slice | 11-provider default catalog, embedded resolved-plan input, private native root-service accessors, production identity/generation accessors, operation locking, leased raw-world quarantine, fail-closed rebuild guards, bounded trace/failure/lifetime evidence, and smoke/lifecycle evidence | later binding migration and broader provider packages |
| System composition | P3-A accepted bounded default-graph slice | owner-derived registry validates counts, identities, dependency edges, and stage order; native conformance separately checks the frozen default artifact before realization | profile-specific omission, complete semantic-stage/read-write joins, and broader package admission |
| Capability/profile projection | P3-B accepted bounded default-profile slice | versioned projection contract joins request capabilities/policies, owner catalog entries, 83 component identities, and 34 native system-order entries; Cordis/native conformance revalidate the join | additional profiles, complete semantic-stage/read-write metadata, external package admission |
| Backend composition | P4-A accepted bounded default-provider slice | `RuntimeFacade` materializes the maintained CPU-exact backend through a native provider catalog derived from the generated resolved manifest; focused native admission and fail-before-factory tests pass; independent review returned P0/P1/P2 = 0/0/0 | broader maintained profiles, CUDA parity, diagnostics/provider evidence |
| Composition evidence | P5-A accepted bounded default CPU-exact slice | versioned schema/generator binds request, requested/resolved manifest, catalog lock, profile projection, 11 provider versions, exact CPU backend, the 83+2+34 executable graph, all worlds/five scopes, and native execution-owner identity; direct composition comparison rejects unexplained mismatch | broader profiles/backends, complete state replay, caller-language/module-origin attestation, external packages |
| Projection/catalog-lock control plane | P2-C0 accepted bounded slice | producer-neutral request and owner-derived lock schemas, generated fixtures, canonical identity recomputation, negative admission matrix, native revalidation, and offline low-level-only guard exist | P2-C1/P3-B default-profile joins are accepted bounded slices; broader profiles remain residual |
| Cordis control plane | P2-C1/P3-B/P6-A accepted bounded default-profile package slice | strict package/overlay schemas and SDK exports pin Cordis `4.0.0-rc.8`, package lock, profile module/bundle, and default overlay; deterministic resolution, LF-stable raw hashes, sealed provenance, diagnostics, and unchanged native admission are green; independent review returned P0/P1/P2 = 0/0/0 | broader/truth-changing profiles need owner admission; external signing/plugins, broader backend parity, and Node host remain |
| Host and batch parity | P7-A accepted bounded default CPU-exact slice | Cordis artifacts pass native conformance; native-direct and local-`ef_py` rows match one frozen action/state/event/window/composition-comparison reference and exact composition identities; 32-world cold/warm, loaded reset, current/high-water RSS, teardown residual, and throughput gates pass; independent review returned P0/P1/P2 = 0/0/0 | Node row held behind P6-B; broader profiles/backends, CUDA parity, multi-run leak characterization, and complete replay remain |
| Node host | absent | Node-API is only a candidate host boundary | approved binding target and lifecycle/parity tests |
| Runtime acceptance | accepted bounded default CPU-exact closure | default behavior, systems, backend, evidence, Cordis producer, native/Python parity, caller inventory, retired-surface proof, standard promotion, and archive routing | named held residuals require separate admission |

## Historical Baseline Facts (pre-P2-B, captured 2026-08-17)

The following facts describe the pre-migration census. They are retained for
traceability and must not be read as the current P2-B implementation state.

1. `SimulationKernel` constructs concrete default models and related services.
2. `SimulationKernel` manually tears down the world and model/service owners.
3. model setters update selected Flecs singleton refs but do not provide one
   uniform provider-restart protocol.
4. `GroundContactSystem` captures the environment-model pointer supplied during
   registration.
5. the central system-registration function installs multiple domain families
   in an explicit ordered list.
6. `WorldBatchRuntime` creates one complete `SimulationKernel` per world.
7. `RuntimeFacade` constructs the CPU backend directly despite the presence of
   `IWorldBatchBackend`.
8. maintained stage contracts already define deterministic graph semantics that
   Cordis must not replace.
9. no maintained Cordis, Node package, or Node-API integration surface is
   present in the inspected repository tree.
10. executable registration, exact-stage inventory, and maintained stage-node
    manifests are three distinct, partially overlapping truth surfaces.
11. provider setters have no inspected production caller outside their
    declarations/definitions and architecture documentation, but this lowers
    only compatibility risk; it does not make the current replacement semantics
    safe.
12. the default compatibility manifest deterministically represents 11
    providers, 83 component registrations, and 34 system registrations.
13. P1-B resolution is deliberately resource-free: it proves structural and
    semantic determinism but cannot grant stage, backend, domain, capability, or
    artifact admission owned by later runtime joins.
14. P2-A could parse and revalidate the frozen default fixture, but native
    realization in that baseline used test factories; P2-B has since moved the
    production default providers behind the catalog.
15. P2-A now independently recomputes requested/resolved hashes against the
    frozen canonical field rules and rejects stale/tampered identities; external
    Cordis/native producer trust still requires byte-equivalent conformance and
    artifact provenance evidence.
16. Typed handles invalidate on successful generation replacement, but lifecycle
    rebuild and stop must run at a governed quiescent barrier; callers must not
    retain the raw pointer returned by `try_get()` across that barrier.
17. Independent review is mandatory for material composition iterations. The
    default matrix covers lifecycle/ownership, contract/canonicalization, and
    integration/CI/documentation; unresolved P1 findings block the next cluster.

## Residual Register

| Residual | Risk | Required disposition | Owner phase |
| --- | --- | --- | --- |
| residual raw dependency references in long-lived provider-owned services | correctness and use-after-free | retain kernel operation lock for current path; migrate remaining long-lived dependencies to handles and add replay/fault-injection evidence | P2-C1/P2-C2 |
| raw Flecs compatibility lease permanently closes provider rebuild | extensibility and accidental retention of the broad ECS surface | keep the lease explicit and operation-lock-backed; migrate remaining consumers to typed kernel/facade operations before introducing a reopenable world-reconfiguration lease | P2-C2/P3 |
| remaining profile-specific system package selection | extensibility and profile ambiguity | extend the accepted owner-derived registry with populated semantic-stage/read-write joins and profile projection; keep native owner admission | P6/P7 |
| broader backend-provider admission beyond the maintained CPU-exact default | backend evolution and parity risk | add owner-approved provider/profile contracts and evidence without silently promoting diagnostics or unmaintained candidates | P4/P5/P7 |
| caller-language or physical-module host attestation | provenance overclaim risk | keep P5-A host identity scoped to the native execution owner; define a separate module-origin contract only if a later admitted use case requires it | P6/P7 or separate host decision |
| MSVC Release optimization of `bindings_runtime.cpp` can remain in one translation unit for over an hour | build reproducibility and developer throughput | split or otherwise bound the template-heavy binding translation unit and prove a clean unmodified Release `ef_py` build; the local `/Od /Ob0` edge override is regression-only evidence | build infrastructure / binding owner |
| Experiment/Cordis/native authority overlap | competing composition truth | explicit intent projection, owner catalog lock, canonical request, native revalidation | P2-C0/P2-C1/P3/P6 |
| asynchronous Cordis lifecycle | nondeterministic teardown if copied directly | native dependency-safe lifecycle transaction | P2/P6 |
| per-world host overhead | world-batch scale risk | shared resolved profile plus lightweight native world scopes | P2/P7 |
| cross-language call temptation | throughput and determinism risk | architecture guard and call-graph test | P6/P7 |
| plugin provenance and trust | supply-chain and truth-authority risk | separate admission/signing/sandbox program before external plugins | deferred |
| compatibility wrappers | permanent dual path risk | explicit owner, evidence, and removal gate | all migration phases |

## Post-Closure Residual Order

1. extend the accepted default-profile package path only when the declared profile,
   package, and signing residuals are separately bounded;
2. prove broader backend/profile parity only through owner-admitted artifacts;
3. add Node hosting only if separately approved, then add its rows to the
   producer/host/backend/batch parity and retire dual paths.

## P8-A Migration Closure — 2026-08-23

P8-A removed the implicit empty-manifest fallback from the production native
builder. `SimulationKernel()` now explicitly supplies the one generated default
resolved artifact to the same builder used by the explicit Cordis/native
manifest bridge. Seven superseded model-replacement setters, concrete provider
construction in `SimulationKernel`, and concrete backend construction in
`RuntimeFacade` remain absent. Production and the documented test-only
publication-failure seam delegate to one shared internal native realizer.

The sealed closure record binds the accepted request, catalog lock, profile
projection, requested/resolved manifests, package provenance/dependency graph,
composition evidence, and P7 parity evidence. Its live inventory classifies
maintained `RuntimeFacade`, default-kernel compatibility/diagnostic,
`WorldBatchRuntime`, Cordis/native bridge, and test-only fault-injection callers
across nine retained surfaces. Validation recomputes
upstream artifact identities from their payloads and live package bytes;
strict-schema, caller-classification, lexical, underlying-payload, and re-sealed
forgery attacks are rejected. Stable rules were promoted to the runtime
composition baseline, the owner index now routes this package as completed
work, and Node, broader profiles/providers, CUDA, external plugin
signing/distribution, and complete replay have explicit held owners and
activation gates.

## P7-A Implementation Amendment — 2026-08-23

The accepted P7-A slice keeps Cordis in the producer/control-plane role and
runs every emitted artifact through the existing native conformance binary.
Direct C++ and local `ef_py` caller rows then prove exact composition joins and
match a separately sealed semantic reference covering non-zero typed pilot
actions, observations/state, window event traces, and direct composition
comparison. The batch
evidence separates cold and warm construction, measures a 32-world warmed step
loop, reconstructs the same loaded workload before each timed reset, records
current and OS high-water RSS, and gates teardown residual memory. All derived
metrics are recomputed during validation; re-sealed semantic, composition, identity,
metric, host, and environment forgeries are rejected. Independent
`gpt-5.6-sol/max` review returned P0/P1/P2 = 0/0/0.

This acceptance does not add a Node row, widen the admitted profile/backend,
claim CUDA parity, or claim complete replay. Those exclusions remain true after
the bounded program closure.

## P2-B Implementation Amendment — 2026-08-20

The default model, event-store, unit-factory, effects, sensor, acoustic,
control, guidance, damage-bridge, and weapon-release ownership now enters
through the native provider catalog and composition root. `SimulationKernel`
exports production requested/resolved identity, and replaceable system
consumers resolve services from generation-aware Flecs references rather than
registration-time raw captures. The backend provider records the admitted
default profile identity only; backend execution migration remains P4.

This is the production seam required for the next Cordis slices, not a native-
only retreat: P2-C0 will bind request/catalog-lock evidence to this root and
P2-C1 must lower the default request through Cordis primitives plus the
repository profile/bundle layer into this real path. Cordis integration is not
claimed by P2-B.

The lifecycle repair batch now serializes kernel ECS/provider operations with
world rebuild and shutdown, refreshes the complete root-handle set atomically,
exports world-scope generation, and protects remaining raw Flecs access with an
explicit RAII world lease. The lease holds the same operation lock used by
rebuild/shutdown; acquiring one permanently closes the current fail-closed
provider-rebuild barrier. Rebuild is also rejected after provider/world/clock
state mutation, during an exact-stage trace frame, or while managed `SimObject`
entities remain. Compatibility visual scenes carry copied environment snapshots
instead of provider pointers. This is a conservative compatibility quarantine, not a claim
that arbitrary Flecs entities are proven quiescent or that a reopenable world
lease has been implemented.

Current migration evidence is 15 native lifecycle cases / 443 assertions, 41
simulation smoke cases / 889 assertions, 6 world-batch runtime cases / 55
assertions, 32 composition architecture/contract tests with one toolchain skip,
and 12 include-direction/flat-boundary tests.
The lifecycle repair batch additionally covers generation increments,
managed-entity/provider/clock-state-mutation/raw-world rebuild rejection,
serialized concurrent rebuild requests, getter/setter synchronization,
moved-from lease fail-closed behavior, world-lease serialization against
shutdown, snapshot-only visual rendering after shutdown, and the ABI-compatible
legacy visual field tombstone. The bounded gate now also covers one fixed
ten-step default trace against pre-P2-B commit `a618b423` under the same MSVC
toolchain, one real default-catalog effects-publication failure rollback, and
eight kernel create/destroy cycles. Independent revalidation is green and the
bounded P2-B acceptance is recorded; this does not introduce a generic replay framework or pull CUDA,
backend parity, or the Cordis vertical slice into this slice.

## P2-C0 Projection And Catalog-Lock Contract — 2026-08-21

The first bounded P2-C0 slice is now present in the target worktree and remains
uncommitted as an accepted bounded slice. It adds a producer-neutral
`RuntimeCompositionRequest` contract and an owner-derived
`AdmittedCatalogLock` contract under `src/runtime/contracts/composition/`, a C++
token mirror, a Python generator/validator, canonical fixtures, and a negative
admission matrix. The slice recomputes request identity
`5c2954d6d04c77fe803130db14d7e5b56391dcf51e482c73ac8cd96877698d6f` and lock
identity `ec36d4f134e003e852a87f0dc2edb8095bbd798855d88b099e0174d45efa7f94`;
the owner-authority registry identity is
`5c360890992168709c79fc3b633808d5ff564b52d4f55cd7ee019811ba8d651f`.

The contract is intentionally not a second resolver: it does not lower into
the P1-B manifest, construct providers, introduce Cordis or Node dependencies,
or change the native production path. At this historical P2-C0 checkpoint the
composition architecture suite was `36 passed, 1 skipped`, and native
revalidation was wired into the focused C++ lifecycle target; P2-C1 was the
next dispatch at that time.

## Independent Review — 2026-08-21

The requested independent read-only review used `gpt-5.6-sol` at `max`
reasoning. It found no P0 issue and identified three P1 defects in the initial
slice: request/lock pairs were not cross-bound, request and lock string-array
validation did not match the ASCII/NFC schema constraints, and malformed
shape-complete entries could raise instead of failing closed. These are now
repaired; the composition suite is `36 passed, 1 skipped` and the CLI rejects
an intentionally mismatched request/lock pair.

The owner self-declaration blocker is closed at the repository-contract layer:
`owner_authority_registry.v1` is now a generated, hashed repository authority
artifact, every lock carries its SHA-256, and both builder and validator reject
owner/category forgery or incomplete authority coverage. P2-C0 bounded acceptance
is recorded. Native revalidation now checks the request, lock, authority
registry, canonical bytes, SHA-256 identities, owner/category coverage, required
capabilities, and package provenance hash requirements through `ef_composition`.
Remaining P2 residuals are external artifact signing/attestation and the fact
that the C++ value structs are a JSON-byte boundary rather than a generated
recursive schema type.

## Native Projection Validation Hardening — 2026-08-22

The native revalidation boundary now applies the same lock metadata checks as
the Python/schema contract: `contract_version` must equal the admitted v1
contract, `lock_id` must be a stable identifier, and `lock_version` must be a
semantic version. The focused native test adds negative cases for all three
fields and the direct `<utility>` dependency is explicit.

The current verification is `16/16` native lifecycle cases with `462`
assertions, `40` composition architecture tests passed with one toolchain skip,
and the focused CTest target passes. P2-C0 bounded acceptance is recorded; no
Cordis or Node dependency was introduced.

## P2-C1 Default Profile Vertical Slice — 2026-08-22

The accepted P2-C0 artifacts now have a repository-owned Cordis producer at
`packages/cordis-runtime`. The package pins `cordis@4.0.0-rc.8`, uses Context,
plugin, event, service, injection, and fiber disposal, rejects unknown profiles,
and lowers the frozen default request through a profile-matched low-level
manifest template. Its CLI recomputes the canonical request SHA-256 and
requires the admitted lock's `request_sha256` before carrying the lock and
lowered manifest to the native conformance seam. Producer metadata records the
pinned Cordis version and raw `package-lock.json` SHA-256; external signing is
still outside this bounded slice.

The new `ef_cordis_runtime_conformance_test` revalidates request/lock/authority,
checks the default request-to-manifest policy/configuration join and exact
lock-to-default selection, ingests the generated requested/resolved manifests,
constructs the production `SimulationKernel` from the supplied resolved artifact,
applies the requested seed/time-step, and executes one step. Local evidence is
nine current Cordis tests, four vertical-slice architecture tests, Python fixture/identity validation,
CTest registration, and native output containing `providers=11`,
`production_generation=1`, the request SHA-256, and the lock SHA-256. This is
the first vertical slice; it does not claim broader profiles, backend parity,
Node hosting, or external plugin admission.
The bounded native seam is not a general arbitrary-low-level-manifest firewall:
profile-specific request/configuration/lock joins are enforced, while a
self-consistent rehashed low-level extension remains a declared P2 residual.

## P3-A System Contribution Migration — 2026-08-22

The former central component and system call lists are now replaced by the
owner-derived registry in `src/core/engine/system_contribution_registry.cpp`
with its systems-layer declaration. It
declares 83 component contributions and 34 system contributions, including
stable contribution IDs, factory IDs, domains, stage-order labels, and dependency edges.
Before touching Flecs, the registry fails closed on duplicate or missing owner
entries, invalid factory/domain metadata, dependency edges that point forward,
and stage-order drift. The native conformance path separately parses and
revalidates the frozen resolved compatibility artifact, including component and
system identity joins, before production realization.
`SimulationKernel` has only the component and system registry entry points; the
two kernel-owned pre-update resets are explicit registry entries outside the
34-row manifest compatibility list. Package/discovery order cannot become the
Flecs execution order and no package receives a private pipeline.

The bounded acceptance covers exact default graph parity, native `ef_test_all`,
composition lifecycle/conformance CTest, 40 composition architecture tests with
one toolchain skip, and the existing Python/native regression. It does not yet
claim profile-specific contribution omission, complete semantic-stage/read-write
joins for all 34 systems, or broader external package admission.

## P3-B Capability And Profile Projection — 2026-08-23

The bounded P3-B slice adds `runtime_profile_projection.v1`: a deterministic,
owner-derived join of the default compatibility profile's capability/policy
requirements, the six catalog-lock categories, the 83 component contribution
identities, and the 34-entry native system registration order. The Python
contract generator and schema emit a canonical fixture with projection identity
`a6983836e82df80805ac3f0f4f4a6975edccf3024d8ff231a67009a596a28c09` and a
negative matrix for profile, capability, policy, owner, component, claim, order,
and schema-invalid type tampering. Catalog rows and each row's capabilities are
normalized by UTF-8 byte order before canonical bytes and identity are minted.

The Cordis producer now lowers and verifies that projection against the frozen
bundle before writing it. The native conformance executable accepts the
projection as an optional artifact and rechecks request/lock identity, owner
catalog entries, component identities, and system order before production
`SimulationKernel` construction. Native revalidation reconstructs the same
normalized payload, rejects unadmitted profile versions and noncanonical array
permutations, and recomputes canonical bytes plus SHA-256. Current evidence is
five profile-contract tests, nine Cordis package tests, four vertical-slice
tests, `45 passed, 1 skipped` across composition architecture, and two focused
CTest cases. This slice keeps capability requirements
primary and treats the named profile as an explicit compatibility alias; it
does not yet admit additional profiles, full semantic-stage/read-write metadata,
or external package trust.

## Final Independent Revalidation Of Bounded P3-B — 2026-08-23

The independent `gpt-5.6-sol` / `max` review of the repaired P3-B worktree
returned `P0=0`, `P1=0`, and `P2=0`. It rechecked the canonical profile,
capability/policy, owner-catalog, component, and native system-order joins plus
the positive/negative Cordis and native handoff. The bounded default-profile
projection is accepted; broader profiles and external package trust remain open.

## P4-A Backend Provider Migration — 2026-08-23

The bounded implementation now derives the default backend request from the
generated resolved native manifest and materializes the maintained
`builtin.backend.flecs_cpu@1.0.0` implementation through a native provider
catalog. Shared provider identity constants are used by both the production
composition provider and facade materializer. `RuntimeFacade` depends only on
the internal backend SPI and no longer names or constructs the concrete Flecs
backend.

Admission fails before factory invocation for unknown schemas/profiles/providers,
diagnostics-only or unmaintained candidate profiles, empty/duplicate/unsupported
capabilities, provider/profile mismatch, duplicate provider identities,
implementation-version drift, and invalid provider capability metadata. Current
local evidence is 8 focused native cases / 71 assertions, 10 focused architecture
cases, the full runtime-facade architecture suite at 76 passed, composition
architecture at 45 passed / 1
skipped, Cordis at 9/9, and three focused CTest targets at 3/3. CI now runs the
P4-A architecture guards alongside the composition suite. Final independent
`gpt-5.6-sol` / `max` review returned P0=0, P1=0, and P2=0, so the bounded
default maintained CPU exact-provider slice is accepted. Broader providers,
CUDA parity, and provider evidence remain outside this acceptance boundary.

The existing `ef_py` artifact used for Python regression was produced after a
local generated-build override disabled optimization only for the pathological
`bindings_runtime.cpp` edge. That build completed in roughly 33 seconds, but it
is not formal Release evidence. A clean MSVC Release attempt on the same
template-heavy translation unit exceeded one hour with sustained single-core
work and approximately 2.4 GiB working set, so Release binding-build closure
remains an explicit infrastructure residual rather than a P4 semantic result.

## Final Independent Revalidation Of Bounded P4-A — 2026-08-23

The independent `gpt-5.6-sol` / `max` review found no actionable issue and
returned `P0=0`, `P1=0`, and `P2=0`. It revalidated exact generated
profile/provider/implementation-version/capability admission, pre-factory
failure closure, factory exception containment, generated-header freshness,
CI wiring, and the native/Cordis/Python architecture evidence. P4-A is accepted
only for the maintained default CPU-exact provider; multi-provider, CUDA,
diagnostics/evidence, and full-catalog work remain later gates.

## Final Independent Revalidation Of P2-B/P2-C0 — 2026-08-22

An independent `gpt-5.6-sol` / `max` review of the pre-P2-C1 P2-B/P2-C0 slice
returned `P0=0`, `P1=0`; P2-C0 bounded acceptance is recorded. This historical
review does not close the P2-C1 gate. It reproduced the native `16/16` and `462`
assertion result and the Python fixture identity checks. The remaining
observations were the declared P2 residuals: recursive configuration remained
represented as canonical JSON bytes, external artifact signing/attestation was
not implemented, and real Cordis lowering belonged to P2-C1.

## Final Independent Revalidation Of Bounded P2-C1 — 2026-08-22

The independent `gpt-5.6-sol` / `max` review of the latest worktree returned
`P0=0`, `P1=0`. It reproduced the MSVC build, CTest conformance/lifecycle,
Cordis package tests, composition architecture tests, Ruff, clang-format, and
the positive/negative native handoff. The default-profile P2-C1 slice is
accepted within its declared boundary. P2 residuals remain for arbitrary
self-consistent rehashed low-level extensions, direct-API post-validation,
cross-host canonical comparator hardening, and external bundle signing/
attestation. At that P2-C1 checkpoint, broader profiles, backend/host parity,
external plugins, and program closure remained unaccepted.

## Explicitly Refused Claims

- Cordis integration is limited to the accepted bounded default-profile
  vertical slice; broader profiles, backend parity, Node hosting, and external
  plugin admission are not accepted. P2-A is its host-neutral native substrate,
  not Cordis itself.
- Cordis will not own experiment intent, semantic implementation admission, or
  deterministic execution; those boundaries are explicit prerequisites for
  introducing it safely.
- The current runtime is not plugin-composed.
- The proposed architecture does not make simulation faster by itself.
- Existing interfaces do not prove lifecycle-safe replacement.
- A successful Cordis plugin load will not by itself prove runtime admission.
- Documentation acceptance will not count as runtime, parity, replay, or
  performance acceptance.
