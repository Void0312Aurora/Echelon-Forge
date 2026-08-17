# Cordis Simulation Composition Kernel Acceptance Contract — 2026-08-17

Status: `2026-08-17` acceptance contract; documentation/authority and
composition-census and contract/canonicalization gates passed. The P2-A
isolated native lifecycle baseline is partially accepted; migration-joined
runtime realization remains open.

Language:

- English canonical: `cordis_simulation_composition_kernel_acceptance_20260817.md`
- Chinese companion: [cordis_simulation_composition_kernel_acceptance_20260817.zh.md](cordis_simulation_composition_kernel_acceptance_20260817.zh.md)

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_acceptance_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

Parent: [Cordis Simulation Composition Kernel](README.md)

## Acceptance Boundary

Acceptance means the scoped long-term composition architecture is implemented,
integrated, evidenced, and routed. It does not mean every future third-party
plugin, backend, domain, remote host, or hot-reload mode is accepted.

## Gate Matrix

| Gate | Required evidence | Reject condition | State |
| --- | --- | --- | --- |
| Documentation and authority | bilingual active package, parent route, valid links, synchronized maintained metadata, explicit Experiment projection/Cordis/admission/native authority chain | orphan task, competing composition owner, or runtime overclaim | pass |
| Composition census | reproducible inventory of construction, replacement, registration, backend, stage, reset, binding, and test edges | unknown owner or unclassified replacement path remains in migration scope | pass |
| Contract and canonicalization | versioned schema, invalid-input matrix, canonical byte fixtures, permutation-stable hash | discovery/order/host-dependent result or ambiguous provider semantics | pass |
| Native lifecycle | scope isolation, transactional construction, dependency-safe teardown, rollback, failure injection | partial runnable state, stale handle, teardown order ambiguity | partial: P2-A baseline pass; production migration evidence open |
| Default behavior parity | pre/post default-profile state, event, observation, reward, termination, and replay comparisons | unexplained semantic divergence hidden by tolerance or fallback | planned |
| Stage graph integrity | existing stage contract validation plus exact default graph comparison | plugin order or host event order affects stage execution | planned |
| Domain profile admission | minimal/common/air/naval/ground/combined profile validation against owner contracts | profile bypasses domain maturity or creates a private lifecycle | planned |
| Backend admission | facade selects admitted provider; CPU/CUDA and unsupported-profile gates | concrete backend remains construction truth or rejected profile silently falls back | planned |
| Evidence and replay | P2-B production manifest identity followed by provider/graph/backend/host/catalog identity expansion and mismatch policy | replay/comparison proceeds with unexplained composition mismatch | planned |
| Cordis conformance | repository-owned Cordis default-profile producer and native compatibility producer yield equivalent admitted canonical manifests and native realization | native side trusts Cordis without revalidation, Cordis bypasses owner admission, or private Cordis identity leaks into contract | planned / required for program closure |
| Binding isolation | Python and C++ always use the same native owner; Node does so if separately admitted | binding owns simulation truth, raw ECS bypass, per-step callback, or Node becomes required for offline native/Python operation | planned |
| Batch and performance | representative startup, memory, throughput, determinism, and teardown measurements | mandatory per-world Node context, hot-path lookup/crossing, or unapproved regression | planned |
| Security and provenance | repository-owned/admitted plugin policy for accepted scope | unreviewed external native plugin execution or missing artifact provenance | planned |
| Migration closure | caller inventory, removal gates, standards/reference promotion, index/archive sync | dual composition path, permanent undocumented wrapper, stale current route | planned |

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
- Node/Cordis host lifecycle and exception translation;
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
Experiment-to-runtime projection, owner-specific admission, and at least one
repository-owned Cordis producer/native realization path. A deferred Node host,
marketplace, remote host, or external-plugin distribution program is compatible
with closure; a deferred Cordis vertical slice, lifecycle, deterministic
composition, evidence identity, or default-profile parity gate is not.
