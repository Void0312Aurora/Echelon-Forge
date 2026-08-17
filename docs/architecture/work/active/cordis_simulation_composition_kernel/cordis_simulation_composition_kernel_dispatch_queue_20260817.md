# Cordis Simulation Composition Kernel Dispatch Queue — 2026-08-17

Status: `2026-08-17` current queue; P0, P1-A, P1-B, and P2-A passed. P2-B is
the next eligible cluster and has not been dispatched.

Language:

- English canonical: `cordis_simulation_composition_kernel_dispatch_queue_20260817.md`
- Chinese companion: [cordis_simulation_composition_kernel_dispatch_queue_20260817.zh.md](cordis_simulation_composition_kernel_dispatch_queue_20260817.zh.md)

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_dispatch_queue_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-17`

Parent: [Cordis Simulation Composition Kernel](README.md)

## Queue

| Order | Cluster | State | Dispatch condition | Write boundary | Required return |
| --- | --- | --- | --- | --- | --- |
| 1 | `P0-A Authority Scaffold` | pass | completed documentation turn | this subproject, architecture owner README, selected bilingual registry rows | document/link/audit outcomes and exact changed files |
| 2 | `P1-A Composition Census` | pass | P0-A passed | read-only source inventory plus current-status evidence updates | complete ownership/scope/replacement inventory |
| 3 | `P1-B Manifest And Resolution Contract` | pass | P1-A passed and contract write set remains bounded | runtime contract/schema inputs and focused tests | schema decision, fixtures, invalid-manifest matrix, versioning and canonicalization evidence |
| 4 | `P2-A Native Lifecycle Kernel` | pass / independently repaired | P1-A/P1-B gates passed | isolated native composition library, focused C++ test, architecture guard, and CMake/CI wiring | 13 tests/277 assertions in normal MSVC and ASan builds; hash, typed-scope, lifecycle-state, rollback, replacement rebuild, handover, invalidation, and deterministic validation evidence |
| 5 | `P2-B Default Provider Migration` | ready / not dispatched | P2-A passed; engine/provider write set remains bounded | default provider entries, kernel builder, engine construction seams, focused parity/lifetime tests | default behavior/replay parity and removal of concrete model construction/raw capture |
| 6 | all later clusters | held | their declared dependencies pass | task-cluster write sets only | cluster-specific evidence packet |

## Next Dispatch Packet

```text
cluster: P2-B Default Provider Migration
goal: realize the accepted default compatibility profile through production native providers and a kernel builder
write set:
  src/core/engine/** construction and ownership seams
  approved default provider entries adjacent to their model/service owners
  focused lifecycle, behavior, replay, and ownership tests
  bounded design/status updates inside this subproject
non-goals:
  system-family contribution split or central registration-list replacement
  backend or binding migration
  Cordis package or Node host
validation:
  pre/post default behavior and replay comparison
  production provider construction and reverse teardown failure injection
  reset/rebuild and repeated create/destroy lifetime evidence
  no concrete default model construction in SimulationKernel
  no registered system retaining a replaceable provider raw pointer
closure:
  the default profile constructs the current kernel through ef_composition without semantic drift or a second construction truth
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

## Next Queue Update Trigger

Update this queue when P2-B is dispatched or completed, when a cluster is
blocked or re-scoped, or when an accepted result changes the next dependency.
Do not update it merely to record elapsed time.
