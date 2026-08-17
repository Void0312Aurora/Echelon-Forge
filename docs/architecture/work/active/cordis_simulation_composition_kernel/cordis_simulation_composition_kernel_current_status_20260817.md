# Cordis Simulation Composition Kernel Current Status — 2026-08-17

Status: `2026-08-17` P2-A native lifecycle baseline plus independent-review
repair; composition ownership and migration edges are classified, the P1-B
contract and isolated native realization kernel passed, P2-B is next, and no
Cordis integration is claimed.

Language:

- English canonical: `cordis_simulation_composition_kernel_current_status_20260817.md`
- Chinese companion: [cordis_simulation_composition_kernel_current_status_20260817.zh.md](cordis_simulation_composition_kernel_current_status_20260817.zh.md)

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_current_status_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

Parent: [Cordis Simulation Composition Kernel](README.md)

Contract baseline:
[P1-B manifest and resolution contract](cordis_simulation_composition_contract_20260817.md).

## Change At This Checkpoint

- created and validated an owner-local active architecture subproject;
- established Cordis as the long-term composition control plane rather than the
  deterministic stage executor;
- established a native composition kernel as the realization and lifecycle
  authority;
- defined a host-neutral manifest, deterministic freeze, evidence, and offline
  deployment direction;
- split the program into finite contract, native, migration, Cordis, host,
  parity, and closure clusters;
- completed the source-grounded P1-A census of constructors, setters, raw
  captures, service refs, system registrations, backend selection, lifecycle,
  stage registries, bindings, build ownership, and relevant tests;
- classified 7 replaceable providers, 3 kernel-owned service/event objects, 82
  central component registrations, 34 active system registrations, 30 exact
  stages, 5 maintained stage-node manifests, and 3 Python runtime tiers;
- made the raw environment capture, split backend admission/materialization,
  and three scheduling truth surfaces hard P1-B constraints;
- implemented a host-neutral requested/resolved manifest contract with five
  scopes, 12 stable service keys, stable failure codes, explicit service
  bindings, compatibility rules, and self-excluding SHA-256 identity;
- added generated schema and default compatibility fixtures covering 11
  providers, 82 components, and 34 systems, plus a fail-closed invalid matrix
  and permutation-stability tests;
- added an isolated `ef_composition` static library with no engine, facade,
  Flecs, binding, or Cordis dependency;
- implemented closed requested/resolved JSON ingestion, native SHA-256
  recomputation, typed-scope guards, frozen factory identity, lifecycle state
  transitions, scoped transactional construction, typed generation handles,
  failure rollback, replacement-aware barrier rebuild, handover admission,
  deterministic reverse disposal, identity accessors, and idempotent shutdown;
- passed 13 focused C++ test cases with 286 assertions in the normal MSVC build
  and under MSVC AddressSanitizer; composition architecture/contract tests are
  20 passed with one toolchain-dependent `g++` skip;
- did not migrate default providers, kernel/facade constructors, system
  registration, backend selection, bindings, Cordis packages, or Node hosting.

## Maturity Matrix

| Surface | State | Current evidence | What remains |
| --- | --- | --- | --- |
| Architecture authority | P0 pass / project active | parent README, target architecture, parent route, and document validation | later promotion of accepted runtime rules |
| Composition census | P1-A pass | [source-grounded census](cordis_simulation_composition_census_20260817.md) with owner/scope/replacement/disposition tables | keep census guard synchronized until generated evidence replaces it |
| Manifest contract | P1-B pass / repaired | requested/resolved generated schemas, pure C++ value types, canonical fixtures, invalid corpus, deterministic tests, and native requested/resolved hash recomputation | keep producer/schema/header parity guarded; prove byte-equivalent Cordis output and artifact provenance before external admission |
| Native lifecycle kernel | P2-A pass / isolated / repaired | `ef_composition`, typed-scope guards, immutable factory metadata, lifecycle state machine, scoped transactions, replacement-aware rebuild, handover admission, identity accessors, rollback/disposal tests, CI wiring, and MSVC ASan evidence | integrate real default providers in P2-B; add migration-specific reset/replay and real registry handover evidence before broad native acceptance |
| Model/provider migration | absent | existing interfaces and setters | provider factories, kernel builder, lifetime-safe consumption |
| System composition | absent | static registration and stage manifests coexist | contribution contract and graph compilation |
| Backend composition | partial baseline | semantic backend interface and capability contracts exist | provider selection and facade construction migration |
| Composition evidence | absent | existing replay/diagnostic infrastructure is available | manifest and graph identity integration |
| Cordis control plane | absent | external architecture reference only | package workspace, plugin SDK, manifest producer, conformance tests |
| Node host | absent | Node-API is only a candidate host boundary | approved binding target and lifecycle/parity tests |
| Runtime acceptance | partial | P2-A proves the isolated lifecycle boundary | default behavior, systems, backend, evidence, Cordis, hosts, parity, and closure gates |

## Verified Baseline Facts

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
12. the P1-B default compatibility manifest deterministically represents 11
    providers, 82 component registrations, and 34 system registrations.
13. P1-B resolution is deliberately resource-free: it proves structural and
    semantic determinism but cannot grant stage, backend, domain, capability, or
    artifact admission owned by later runtime joins.
14. P2-A can parse and revalidate the frozen default fixture, but native
    realization currently uses test factories; production default providers
    have not moved behind the catalog.
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
| dual model ownership through `unique_ptr`, singleton refs, and captured pointers | correctness and use-after-free | migrate production defaults to P2-A scoped handles and remove raw capture | P2-B |
| central static system list | extensibility and profile ambiguity | contribution descriptors compiled into stage contracts | P3 |
| direct concrete backend construction | backend evolution and test isolation | backend provider admission | P4 |
| multiple potential manifest producers | divergent composition truth | canonical schema, native revalidation, stable hash | P1/P6 |
| asynchronous Cordis lifecycle | nondeterministic teardown if copied directly | native dependency-safe lifecycle transaction | P2/P6 |
| per-world host overhead | world-batch scale risk | shared resolved profile plus lightweight native world scopes | P2/P7 |
| cross-language call temptation | throughput and determinism risk | architecture guard and call-graph test | P6/P7 |
| plugin provenance and trust | supply-chain and truth-authority risk | separate admission/signing/sandbox program before external plugins | deferred |
| compatibility wrappers | permanent dual path risk | explicit owner, evidence, and removal gate | all migration phases |

## Recommended Next Action Order

1. migrate the default profile through P2-B providers and a kernel builder,
   with behavior/replay parity and removal of raw provider capture;
2. add migration-specific reset, repeated rebuild, and lifetime evidence;
3. split system and backend composition;
4. make composition identity part of evidence;
5. add the Cordis producer and only then the Node host;
6. run host/backend/batch parity and retire dual paths.

## Explicitly Refused Claims

- Cordis integration is not implemented; P2-A is a host-neutral native
  prerequisite, not Cordis itself.
- The current runtime is not plugin-composed.
- The proposed architecture does not make simulation faster by itself.
- Existing interfaces do not prove lifecycle-safe replacement.
- A successful Cordis plugin load will not by itself prove runtime admission.
- Documentation acceptance will not count as runtime, parity, replay, or
  performance acceptance.
