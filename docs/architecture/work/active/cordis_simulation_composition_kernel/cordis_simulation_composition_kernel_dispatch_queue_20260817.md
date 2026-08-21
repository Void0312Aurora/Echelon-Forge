# Cordis Simulation Composition Kernel Dispatch Queue — 2026-08-17

Status: `2026-08-20` current queue; P0, P1-A, P1-B, and P2-A passed. P2-B is
implemented in the active worktree and pending independent review/evidence.

Language:

- English canonical: `cordis_simulation_composition_kernel_dispatch_queue_20260817.md`
- Chinese companion: [cordis_simulation_composition_kernel_dispatch_queue_20260817.zh.md](cordis_simulation_composition_kernel_dispatch_queue_20260817.zh.md)

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_dispatch_queue_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-20`

Parent: [Cordis Simulation Composition Kernel](README.md)

## Queue

| Order | Cluster | State | Dispatch condition | Write boundary | Required return |
| --- | --- | --- | --- | --- | --- |
| 1 | `P0-A Authority Scaffold` | pass | completed documentation turn | this subproject, architecture owner README, selected bilingual registry rows | document/link/audit outcomes and exact changed files |
| 2 | `P1-A Composition Census` | pass | P0-A passed | read-only source inventory plus current-status evidence updates | complete ownership/scope/replacement inventory |
| 3 | `P1-B Manifest And Resolution Contract` | pass | P1-A passed and contract write set remains bounded | runtime contract/schema inputs and focused tests | schema decision, fixtures, invalid-manifest matrix, versioning and canonicalization evidence |
| 4 | `P2-A Native Lifecycle Kernel` | pass / independently repaired | P1-A/P1-B gates passed | isolated native composition library, focused C++ test, architecture guard, and CMake/CI wiring | 14 tests/430 assertions in normal MSVC and ASan builds; hash, typed-scope, lifecycle-state, rollback, serialized replacement rebuild, reentrant lifetime, plugin/factory identity, in-process semantic service-type identity, handover, invalidation, and deterministic validation evidence |
| 5 | `P2-B Default Provider Migration` | implemented / pending independent review | P2-A passed; engine/provider write set remains bounded | default provider entries, kernel builder, engine construction seams, focused parity/lifetime tests | controlled default trace parity, one production failure/teardown path, repeated create/destroy, and independent review |
| 6 | `P2-C0 Projection And Catalog-Lock Contract` | held / planned | P2-B production composition and identity are stable | producer-neutral request DTO, owner-derived catalog-lock artifact/generator, identity and negative-admission fixtures | one high-level request contract, one verifiable owner lock, and a guard preventing offline high-level lowering |
| 7 | `P2-C1 Cordis Default-Profile Vertical Slice` | held / planned | P2-C0 accepted | bounded Cordis package using Cordis primitives plus repository profile/bundle layer, production adapters, end-to-end fixtures | Experiment fixture -> request -> Cordis -> manifest/lock -> native production realization, including negative admission and offline regression |
| 8 | all later clusters | held | P2-C1 accepted and their declared owner dependencies pass, or an explicit independent-stream amendment is approved | task-cluster write sets only | cluster-specific evidence packet |

## Next Dispatch Packet

```text
cluster: P2-B Default Provider Migration
goal: realize the accepted default compatibility profile through production native providers and a kernel builder
write set:
  src/core/engine/** construction and ownership seams
  approved default provider entries adjacent to their model/service owners
  focused lifecycle, behavior, replay, and ownership tests
  bounded composition identity/evidence DTO joins
  bounded design/status updates inside this subproject
non-goals:
  system-family contribution split or central registration-list replacement
  backend or binding migration
  Cordis package or Node host
validation:
  one controlled pre/post default behavior and replay comparison
  one production provider construction and reverse teardown failure path
  repeated kernel create/destroy lifetime evidence
  no concrete default model construction in SimulationKernel
  no registered system retaining a replaceable provider raw pointer
  stable requested/resolved identity exported from the production path
  no unresolved P1/P0 finding in the final independent review
closure:
  the default profile constructs the current kernel through ef_composition without semantic drift or a second construction truth, and leaves stable production identity/evidence seams for P2-C0
```

## Queue Rules

- P1 contract gates are closed; P2-B must treat the accepted contract as an
  input and route any required contract change back through an explicit P1
  amendment.
- P1-A census may be split by model/service, system/stage, backend, and binding
  surfaces, but integration of its ownership table remains serial.
- P1-B must use the accepted census and may not omit an ownership edge merely
  because its migration occurs in a later cluster.
- No implementation cluster may create untracked compatibility paths outside
  its declared write set.
- Any discovered conflict with a maintained architecture standard pauses the
  affected cluster and routes a bounded standards review; the task document
  cannot silently override the standard.
- Acceptance and closure remain unassigned until implementation evidence
  exists.
- P2-C0 is the next strategic slice after P2-B and freezes the only high-level
  request/catalog-lock authority. P2-C1 follows and proves Cordis against the
  production default path while keeping Node hosting, external packaging, and
  system modularization out of the slice.
- Bounded native acceptance does not imply Cordis acceptance. Overall program
  closure does require P2-C1 Cordis/native conformance; Node hosting remains
  conditional on a separate host decision.

## Next Queue Update Trigger

Update this queue when P2-B is dispatched or completed, when P2-C0/P2-C1 become
eligible, when a cluster is blocked or re-scoped, or when an accepted result
changes the next dependency. Do not update it merely to record elapsed time.
