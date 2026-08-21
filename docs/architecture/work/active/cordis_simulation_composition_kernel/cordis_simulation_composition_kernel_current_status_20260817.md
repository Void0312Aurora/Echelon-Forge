# Cordis Simulation Composition Kernel Current Status — 2026-08-17

Status: `2026-08-20` P2-B production-provider migration implementation is
complete after the P2-A native lifecycle baseline and independent-review repair;
the default kernel now constructs through the native composition root, while
Cordis integration is still not claimed pending P2-C0/P2-C1.

Language:

- English canonical: `cordis_simulation_composition_kernel_current_status_20260817.md`
- Chinese companion: [cordis_simulation_composition_kernel_current_status_20260817.zh.md](cordis_simulation_composition_kernel_current_status_20260817.zh.md)

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_current_status_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-20`

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
  tests are 21 passed with one toolchain-dependent `g++` skip;
- migrated the default model/event/service ownership into admitted native
  providers and a composition-root builder; systems now resolve replaceable
  services through generation-aware Flecs refs rather than registration-time
  raw captures; backend execution migration, Cordis packages, and Node hosting
  remain outside this slice.

## Maturity Matrix

| Surface | State | Current evidence | What remains |
| --- | --- | --- | --- |
| Architecture authority | P0 pass / project active | parent README, target architecture, parent route, and document validation | later promotion of accepted runtime rules |
| Composition census | P1-A pass | [source-grounded census](cordis_simulation_composition_census_20260817.md) with owner/scope/replacement/disposition tables | keep census guard synchronized until generated evidence replaces it |
| Manifest contract | P1-B pass / repaired | requested/resolved generated schemas, pure C++ value types, canonical fixtures, invalid corpus, deterministic tests, and native requested/resolved hash recomputation | keep producer/schema/header parity guarded; prove byte-equivalent Cordis output and artifact provenance before external admission |
| Native lifecycle kernel | P2-A pass / production-enabling substrate | `ef_composition`, typed-scope guards, immutable factory metadata, lifecycle state machine, scoped transactions, replacement-aware rebuild, handover admission, identity accessors, rollback/disposal tests, CI wiring, and MSVC ASan evidence | real registry handover and broader native acceptance evidence |
| Model/provider migration | P2-B implemented / pending independent revalidation | 11-provider default catalog, embedded resolved-plan input, private native root-service accessors, production identity/generation accessors, operation locking, leased raw-world quarantine, fail-closed rebuild guards, bounded trace/failure/lifetime evidence, and smoke/lifecycle evidence | final independent revalidation |
| System composition | absent | static registration and stage manifests coexist | contribution contract and graph compilation |
| Backend composition | partial baseline | semantic backend interface and capability contracts exist | provider selection and facade construction migration |
| Composition evidence | P2-B production identity implemented / pending review | `SimulationKernel` exports generated requested/resolved identities and world-rebuild preserves them | request/catalog-lock identities in P2-C0/P2-C1, then graph/backend/host/replay expansion in P5-A |
| Cordis control plane | absent / required target | architecture and P1-B low-level producer contract exist; no high-level request/catalog-lock artifact or repository Cordis package exists | P2-C0 projection/catalog-lock contract, P2-C1 default-profile producer/native vertical slice, then P6-A package maturation |
| Node host | absent | Node-API is only a candidate host boundary | approved binding target and lifecycle/parity tests |
| Runtime acceptance | partial | P2-A proves the isolated lifecycle boundary | default behavior, systems, backend, evidence, Cordis, hosts, parity, and closure gates |

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
| central static system list | extensibility and profile ambiguity | contribution descriptors compiled into stage contracts | P3 |
| direct concrete backend construction | backend evolution and test isolation | backend provider admission | P4 |
| Experiment/Cordis/native authority overlap | competing composition truth | explicit intent projection, owner catalog lock, canonical request, native revalidation | P2-C0/P2-C1/P3/P6 |
| asynchronous Cordis lifecycle | nondeterministic teardown if copied directly | native dependency-safe lifecycle transaction | P2/P6 |
| per-world host overhead | world-batch scale risk | shared resolved profile plus lightweight native world scopes | P2/P7 |
| cross-language call temptation | throughput and determinism risk | architecture guard and call-graph test | P6/P7 |
| plugin provenance and trust | supply-chain and truth-authority risk | separate admission/signing/sandbox program before external plugins | deferred |
| compatibility wrappers | permanent dual path risk | explicit owner, evidence, and removal gate | all migration phases |

## Recommended Next Action Order

1. complete P2-B independent review with behavior/replay parity, repeated
   rebuild, provider failure/teardown, and create/destroy lifetime evidence;
2. execute P2-C0: freeze the producer-neutral high-level request and
   owner-derived catalog-lock artifact/identity, while forbidding a second
   offline high-level resolver;
4. execute P2-C1: lower the default request through Cordis primitives plus the
   repository profile/bundle layer and prove end-to-end native realization and
   negative admission;
5. compile owner-admitted system packages and capability/profile projections;
6. migrate backend selection and expand evidence across graph/backend/host
   surfaces;
7. mature the Cordis package and tooling;
8. add Node hosting only if separately approved, then run applicable
   producer/host/backend/batch parity and retire dual paths.

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
assertions, 21 composition architecture/contract tests with one toolchain skip,
and 12 include-direction/flat-boundary tests.
The lifecycle repair batch additionally covers generation increments,
managed-entity/provider/clock-state-mutation/raw-world rebuild rejection,
serialized concurrent rebuild requests, getter/setter synchronization,
moved-from lease fail-closed behavior, world-lease serialization against
shutdown, snapshot-only visual rendering after shutdown, and the ABI-compatible
legacy visual field tombstone. The bounded gate now also covers one fixed
ten-step default trace against pre-P2-B commit `a618b423` under the same MSVC
toolchain, one real default-catalog effects-publication failure rollback, and
eight kernel create/destroy cycles. P2-B now only awaits final independent
revalidation; it does not introduce a generic replay framework or pull CUDA,
backend parity, or the Cordis vertical slice into this slice.

## Explicitly Refused Claims

- Cordis integration is not implemented; P2-A is its host-neutral native
  substrate, not Cordis itself. This absence limits the current acceptance
  claim but does not make Cordis optional in the target program.
- Cordis will not own experiment intent, semantic implementation admission, or
  deterministic execution; those boundaries are explicit prerequisites for
  introducing it safely.
- The current runtime is not plugin-composed.
- The proposed architecture does not make simulation faster by itself.
- Existing interfaces do not prove lifecycle-safe replacement.
- A successful Cordis plugin load will not by itself prove runtime admission.
- Documentation acceptance will not count as runtime, parity, replay, or
  performance acceptance.
