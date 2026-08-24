# Cordis Simulation Composition Kernel Acceptance Contract — 2026-08-17

Status: `2026-08-23` bounded acceptance record; documentation/authority,
composition-census, contract/canonicalization, P2-B native production seam,
P2-C0 projection/catalog-lock, the P2-C1 default-profile Cordis/native slice,
the P3-A default-graph system-contribution slice, the P3-B default-profile
projection, P4-A default backend provider, P5-A default CPU-exact composition
evidence, P6-A package maturation, P7-A host/batch parity, and P8-A migration
closure are accepted within their declared boundaries. The bounded default
CPU-exact program is closed; broader profiles/providers, Node, CUDA, external
plugins, and complete replay remain held residuals.

Language:

- English canonical: `cordis_simulation_composition_kernel_acceptance_20260817.md`
- Chinese companion: [cordis_simulation_composition_kernel_acceptance_20260817.zh.md](cordis_simulation_composition_kernel_acceptance_20260817.zh.md)

Document kind: `task`
Lifecycle: `archived`
Canonical: `docs/architecture/work/archive/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_acceptance_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-23`

Parent: [Cordis Simulation Composition Kernel](README.md)

## Acceptance Boundary

This contract distinguishes bounded native P2-B acceptance from later program
closure. P2-B proves the production provider seam; it does not accept Cordis,
backend, host, or performance migrations that have not been implemented.

## Gate Matrix

| Gate | Required evidence | Reject condition | State |
| --- | --- | --- | --- |
| Documentation and authority | bilingual archived evidence package, maintained standard, completed-work parent route, valid links, synchronized metadata, explicit Experiment projection/Cordis/admission/native authority chain | orphan task, competing composition owner, stale active route, or runtime overclaim | pass |
| Composition census | reproducible inventory of construction, replacement, registration, backend, stage, reset, binding, and test edges | unknown owner or unclassified replacement path remains in migration scope | pass |
| Contract and canonicalization | versioned schema, invalid-input matrix, canonical byte fixtures, permutation-stable hash | discovery/order/host-dependent result or ambiguous provider semantics | pass |
| Native lifecycle | P2-B production provider construction, one failure/teardown rollback path, and no dangling service reference | partial runnable state, stale handle, teardown order ambiguity | accepted bounded P2-B |
| Default behavior parity | one controlled pre/post default-profile state/event/observation/replay comparison | unexplained semantic divergence hidden by tolerance or fallback | accepted bounded P2-B |
| Stage graph integrity | existing stage contract validation, exact default graph comparison, and owner-derived registry admission | plugin order or host event order affects stage execution | accepted bounded P3-A default-graph slice; full semantic-stage/read-write projection remains open |
| Domain profile admission | default compatibility profile capability/policy join and owner-derived contribution bundle; broader minimal/common/air/naval/ground/combined profiles | profile bypasses domain maturity or creates a private lifecycle | accepted bounded P3-B default-profile slice; broader domain profiles planned |
| Backend admission | facade selects an admitted provider with exact profile/provider/version/capability identity; unsupported candidates and construction failures are fail-closed | concrete backend remains construction truth, identity drift is ignored, or rejected profile silently falls back | accepted bounded P4-A default-provider slice; broader provider admission remains open |
| Projection and catalog-lock authority | versioned producer-neutral request DTO, deterministic owner-derived lock, canonical bytes/hashes, category-owner matrix, positive/negative admission cases, and offline high-level-lowering guard | Cordis owns a private catalog, two high-level resolvers exist, or native cannot verify lock identity/selection | accepted bounded P2-C0 |
| Evidence and comparison | exact request/manifest/lock/profile identities, 11 provider versions, 83+2+34 graph identity, exact backend identity, native execution owner, all worlds/five scopes, and strict composition mismatch rejection | comparison proceeds with unexplained composition/catalog-lock/backend/graph/scope mismatch | accepted bounded P5-A default CPU-exact slice; broader profile/backend and complete state replay remain open |
| Cordis conformance | Cordis primitives plus the repository profile/bundle layer lower the real default request through the owner lock into canonical manifest and native realization | native side trusts Cordis without revalidation, Cordis bypasses owner admission, a private Cordis catalog exists, or parity covers only a synthetic manifest fixture | accepted bounded P2-C1 default-profile slice; required default vertical path is included in P8 closure |
| Binding isolation | Python and C++ use the same native execution owner; Node does so if separately admitted | binding owns simulation truth, raw ECS bypass, per-step callback, or Node becomes required for offline native/Python operation | accepted for bounded P7-A native-direct/local-`ef_py` caller evidence; Node remains open |
| Batch and performance | representative startup, memory, throughput, determinism, and teardown measurements | mandatory per-world Node context, hot-path lookup/crossing, or unapproved regression | accepted bounded P7-A 32-world CPU-exact regression envelope; broader hardware/profile characterization remains open |
| Security and provenance | repository-owned/admitted plugin policy for accepted scope | unreviewed external native plugin execution or missing artifact provenance | accepted for repository-built default scope; external artifacts held by `owner.security` |
| Migration closure | caller inventory, removal gates, standards/reference promotion, index/archive sync | dual composition path, permanent undocumented wrapper, stale current route | accepted bounded P8-A closure |

## Required Validation Families

### Architecture and dependency

- ownership and forbidden-include tests;
- one composition authority guard;
- no cross-language stage-call guard;
- no direct concrete model/backend construction at retired locations;
- no task-label leakage into production identifiers.

### Contract

- schema generation and freshness;
- accepted and rejected manifest corpus;
- canonical serialization across host/platform implementations;
- dependency/conflict/capability resolution matrix;
- stable service-key and version compatibility tests.

### Lifecycle

- construction and reverse dependency teardown;
- constructor failure at every resource index;
- nested scope isolation;
- reset, resize, backend failure, and shutdown;
- repeated create/destroy and sanitizer/leak checks where supported;
- no dangling pointer after provider or scope transition.

### Simulation parity

- deterministic state and event trace under the default compatibility profile;
- observation/action/reward/termination equivalence;
- exact-stage graph identity;
- replay and comparison mismatch handling;
- CPU and admitted CUDA profile parity under existing backend contracts.

### Host and performance

- standalone C++ and Python operation with Node absent;
- Cordis producer lifecycle, failure, and conformance from P2-C1 onward;
- Node host lifecycle and exception translation only if P6-B is admitted;
- no Node/Python/IPC frame in maintained step call graphs;
- large world-batch startup, memory, step, reset, and teardown probes;
- cold and warm composition measurements separated from step throughput.

## Evidence Package Requirements

Final acceptance must retain:

- baseline revision and toolchain;
- manifest/schema versions and fixture hashes;
- resolved composition and stage graph identities;
- exact validation commands and outcomes;
- host/backend/profile matrix;
- performance environment and raw measurements;
- failure-injection matrix;
- known residuals and forbidden claims;
- accepted removal/compatibility decisions;
- synchronized documentation and archive routes.

## Partial Acceptance

P2-B may be accepted as a bounded native slice once its six blockers are closed:
native provider construction without concrete kernel ownership/raw capture,
one controlled behavior/replay comparison, one production failure/teardown
rollback path, repeated create/destroy, stable identity/generation, and final
independent review with no unresolved P1/P0. The remaining rows below belong to
P2-C0, P2-C1, later implementation clusters, or overall program closure.

## Bounded Acceptance Record — 2026-08-22

P2-B is accepted at the native production seam: the default provider catalog,
controlled parity trace, production failure/teardown rollback, repeated
create/destroy evidence, stable requested/resolved identity, and independent
`gpt-5.6-sol/max` review are all green (`P0=0`, `P1=0`). P2-C0 is accepted as
the producer-neutral request and owner-derived catalog-lock contract: generated
schemas/fixtures, canonical identity recomputation, negative admission,
native revalidation, and the offline low-level-only guard are green.

This acceptance does not claim broader Cordis profiles, backend parity, Node
host, external artifact signing, or overall program closure. The P2-C1
default-profile producer/native slice is accepted as a bounded slice; broader
profile/bundle coverage and the remaining residuals stay open.

P3-A is accepted as a bounded default-graph slice. The owner-derived registry
replaces the central component/system calls, validates 83 component rows and 34
manifest system rows against the frozen resolved artifact, and explicitly owns
the two kernel pre-update reset systems outside that manifest row set. Native
and Python composition regression, exact registration-order parity, CTest, and
the P3-A composition/structural guards are green. The repository-wide
include-direction ratchet still has one pre-existing smoke-test violation. This
does not yet admit profile-specific
package omission, complete semantic-stage/read-write declarations for all
systems, or external package trust.

P3-B is accepted as a bounded default-profile projection slice. The versioned
profile projection contract binds the named compatibility profile to its
capability/policy set, all six owner-admitted catalog categories, the 83
component contribution identities, and the 34-entry native system order. The
Cordis producer emits the projection only after the request/lock join; native
conformance rechecks the same identities before constructing `SimulationKernel`.
Negative fixtures cover profile forgery, capability/policy substitution, owner
forgery, and execution-order tampering. Complete semantic-stage/read-write
metadata, additional domain profiles, and external packages remain open.

P4-A is accepted as a bounded default-provider slice. `RuntimeFacade`
materializes the maintained `cpu_exact.reference` backend only through the
generated profile/provider/version/capability admission path, rejects unsupported
identity before factory invocation, and closes factory exceptions without a
fallback backend. Broader providers, CUDA parity, and multi-profile catalogs
remain open.

P5-A is accepted as a bounded default CPU-exact composition-evidence slice.
The `runtime_composition_evidence.v1` artifact binds the request, requested and
resolved manifests, catalog lock, profile projection, all 11 provider versions,
the exact backend identity, and the owner-derived executable graph of 83
components, 2 kernel systems, and 34 resolved systems. Every realized world
records all five scopes; a monotonic facade incarnation prevents resize or
`configure_batch` ABA; zero-world evidence fails closed; direct composition
comparison rejects unexplained mismatches. The accepted host fields mean native execution owner
(`native_cpp/native.v1`), including when Python is the coarse caller. They do
not attest caller language or physical module origin. Broader profiles/backends,
complete simulation-state replay, Node, and external package provenance remain
open.

P6-A is accepted as a bounded repository-owned default-profile package slice.
The Cordis package exposes strict package/overlay SDK definitions, resolves the
exact Cordis runtime, profile module, profile bundle, and default overlay in a
deterministic four-node graph, and rejects missing, duplicate, cyclic,
conflicting, unpinned, unsafe-path, non-ASCII, or truth-changing input. All raw
hash inputs and the five bundle artifacts are LF-stable under `-text`; package
provenance binds the descriptor, dependency graph, overlays, producer/package
lock, request, catalog lock, and profile projection, while diagnostics rechecks
the sealed provenance against the actual artifacts before reporting a validated
handoff. The existing native conformance path accepts the unchanged canonical
request/lock/projection/manifests. Independent `gpt-5.6-sol/max` review returned
P0/P1/P2 = 0/0/0. The accepted boundary does not admit broader or truth-changing
profiles, external signing/distribution/plugins, Node hosting, or CUDA parity.

P7-A is accepted as a bounded default CPU-exact host/batch parity slice. Cordis
remains a producer/control plane whose artifacts pass native conformance before
the direct C++ and local `ef_py` rows execute. Both rows match a separately
sealed semantic reference covering non-zero typed actions, state/observations,
window event traces, exact composition, and direct composition comparison. A frozen 32-world budget separates cold/warm
construction and warmed stepping, restores the same loaded workload before
every timed reset, measures current and OS high-water RSS, and gates teardown
residual memory. The validator recomputes derived values and rejects re-sealed
semantic, composition, graph, metric, host/environment, and integer-alias forgeries.
Independent `gpt-5.6-sol/max` review returned P0/P1/P2 = 0/0/0. Node remains
held behind P6-B; broader profiles/backends, CUDA parity, and complete replay
remain held outside the bounded closure.

P8-A is accepted as the bounded migration closure. The native builder no longer
has an implicit empty-manifest fallback; the default constructor explicitly
uses the generated resolved artifact and converges with the explicit
Cordis/native manifest bridge. Production and the documented test-only
publication-failure seam share one internal native realizer. The sealed live
inventory proves seven model setters and concrete construction at retired
kernel/facade locations absent, classifies nine retained caller surfaces, and
revalidates the request, lock, projection, manifests, package bytes/provenance,
composition evidence, and parity evidence before accepting their identities.
Strict schema and focused attack tests reject altered upstream payloads,
unclassified native callers, extra authority/truth fields, and re-sealed
closure forgeries. Stable rules are in the maintained runtime composition
baseline, the work package is archived, and all optional residuals have named
held owners and activation gates.

Native composition, the Cordis producer/native vertical slice, system/profile
composition, backend/evidence integration, and Node hosting may be accepted as
separate bounded slices only if the parent status names the exact accepted
boundary. Native composition acceptance must not imply Cordis or Node
acceptance; Cordis manifest conformance must not imply external plugin trust;
Node host acceptance must not imply performance or backend parity beyond the
tested matrix. Independent slice acceptance prevents a conditional Node or
external-ecosystem decision from blocking native/runtime progress, but it does
not remove the Cordis vertical slice from overall program closure.

The accepted P2-A boundary is the independent `ef_composition` library and its
closed JSON ingestion, native hash revalidation, typed-scope guards, immutable
plugin/factory identity, in-process semantic service-type identity, lifecycle
state machine, transactional scoped construction, generation invalidation, serialized
replacement-aware rebuild, reentrant wrapper lifetime retention, handover
admission, and reverse-disposal behavior. Normal MSVC and MSVC AddressSanitizer
runs each passed 14 tests and 430 assertions; the composition architecture suite
passed 20 tests with one toolchain-dependent skip. Default-provider integration, real Flecs
handover evidence, reset/replay parity, system capture repair, artifact
provenance, external DSO ABI pinning, and all Cordis/host claims remain open.

## Closure Rule

The subproject may close only after every required gate is accepted or moved to
a separately named active/held owner with no dual truth path. Required gates
include default-provider parity, production composition identity, explicit
Experiment-to-runtime projection, a versioned owner-derived catalog lock, and
at least one repository-owned Cordis producer/native realization path. A deferred Node host,
marketplace, remote host, or external-plugin distribution program is compatible
with closure; a deferred P2-C0 contract, P2-C1 Cordis vertical slice, lifecycle, deterministic
composition, evidence identity, or default-profile parity gate is not.

This rule is satisfied for the bounded default CPU-exact scope. It is not an
admission of any held residual.
