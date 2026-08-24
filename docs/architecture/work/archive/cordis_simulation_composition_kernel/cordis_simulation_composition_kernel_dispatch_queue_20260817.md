# Cordis Simulation Composition Kernel Dispatch Queue — 2026-08-17

Status: `2026-08-23` current queue; P0, P1-A, P1-B, P2-A, P2-B, P2-C0,
the P2-C1 default-profile bounded slice, the P3-A default-graph bounded slice,
the P3-B default-profile projection slice, P4-A default-provider slice, P5-A
default CPU-exact composition-evidence slice, P6-A default-profile Cordis
package slice, P7-A default CPU-exact host/batch parity, and P8-A migration
closure are accepted. This queue is closed and archived. Broader profile,
provider, Node-host, CUDA, external-plugin, and replay expansion remains held
under separately named owners.

Language:

- English canonical: `cordis_simulation_composition_kernel_dispatch_queue_20260817.md`
- Chinese companion: [cordis_simulation_composition_kernel_dispatch_queue_20260817.zh.md](cordis_simulation_composition_kernel_dispatch_queue_20260817.zh.md)

Document kind: `task`
Lifecycle: `archived`
Canonical: `docs/architecture/work/archive/cordis_simulation_composition_kernel/cordis_simulation_composition_kernel_dispatch_queue_20260817.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-23`

Parent: [Cordis Simulation Composition Kernel](README.md)

## Queue

| Order | Cluster | State | Dispatch condition | Write boundary | Required return |
| --- | --- | --- | --- | --- | --- |
| 1 | `P0-A Authority Scaffold` | pass | completed documentation turn | this subproject, architecture owner README, selected bilingual registry rows | document/link/audit outcomes and exact changed files |
| 2 | `P1-A Composition Census` | pass | P0-A passed | read-only source inventory plus current-status evidence updates | complete ownership/scope/replacement inventory |
| 3 | `P1-B Manifest And Resolution Contract` | pass | P1-A passed and contract write set remains bounded | runtime contract/schema inputs and focused tests | schema decision, fixtures, invalid-manifest matrix, versioning and canonicalization evidence |
| 4 | `P2-A Native Lifecycle Kernel` | pass / independently repaired | P1-A/P1-B gates passed | isolated native composition library, focused C++ test, architecture guard, and CMake/CI wiring | 14 tests/430 assertions in normal MSVC and ASan builds; hash, typed-scope, lifecycle-state, rollback, serialized replacement rebuild, reentrant lifetime, plugin/factory identity, in-process semantic service-type identity, handover, invalidation, and deterministic validation evidence |
| 5 | `P2-B Default Provider Migration` | accepted bounded slice | P2-A passed; engine/provider write set remains bounded | default provider entries, kernel builder, engine construction seams, focused parity/lifetime tests | controlled default trace parity, one production failure/teardown path, repeated create/destroy, and independent review |
| 6 | `P2-C0 Projection And Catalog-Lock Contract` | accepted bounded slice | P2-B production composition and identity are stable; bounded contract slice is validated | producer-neutral request DTO, owner-derived catalog-lock artifact/generator, identity and negative-admission fixtures | one high-level request contract, one verifiable owner lock, and a guard preventing offline high-level lowering |
| 7 | `P2-C1 Cordis Default-Profile Vertical Slice` | accepted bounded default-profile slice | P2-C0 accepted | bounded Cordis package using Cordis primitives plus repository profile/bundle layer, production adapters, end-to-end fixtures | Experiment fixture -> request -> Cordis -> manifest/lock -> native production realization, including negative admission and offline regression |
| 8 | `P4-A Backend Provider Migration` | accepted bounded default-provider slice | P3-B default-profile projection bounded slice accepted | facade/provider contracts, generated backend request identity, fixtures/tests, CMake/CI, bounded docs | independent P0/P1/P2 = 0/0/0 and reproduced evidence |
| 9 | `P5-A Composition Evidence Expansion` | accepted bounded default CPU-exact slice | P4-A accepted and relevant P2/P3 identity joins available | evidence/replay contracts, facade diagnostics, schema generators, focused tests, CMake/CI, bounded docs | exact request/manifest/lock/profile/provider/backend/graph/world/scope evidence, commit sealing, mismatch rejection, and independent review |
| 10 | `P6-A Cordis Package Maturation` | accepted bounded default-profile package slice | P2-C1/P3/P4/P5 bounded contracts accepted | approved `packages/cordis-runtime/**`, workspace manifests/lockfiles, fixtures, package tests, bounded docs | repository-owned overlays/bundles, LF-stable raw pins, sealed provenance/diagnostics/dependency evidence, canonical native parity, independent P0/P1/P2 = 0/0/0 |
| 11 | `P6-B Node Host Adapter` | conditional / held | P6-A accepted plus explicit host decision | approved Node adapter only | only if admitted: native-owner lifecycle/parity evidence |
| 12 | `P7-A Host And Batch Parity` | accepted bounded default CPU-exact slice | P4-A/P5-A/P6-A accepted; Node rows require P6-B | integration tests, benchmark/probe tools, evidence package, bounded fixes | frozen action/state/event/window/composition-comparison semantics, strict producer/host joins, approved 32-world measurements, independent P0/P1/P2 = 0/0/0 |
| 13 | `P8-A Migration Closure` | accepted bounded closure | required bounded native/Cordis/system/backend/evidence/parity gates accepted | composition callers/truth paths, stable architecture rules, acceptance/archive, owner indexes | full acceptance matrix, removed or explicitly retained compatibility paths, named residual owners, synchronized documentation |
| 14 | all later clusters | held behind declared dependencies | each declared owner dependency passes, or an explicit independent-stream amendment is approved | task-cluster write sets only | cluster-specific evidence packet |

## Accepted Closure Packet

```text
cluster: P8-A Migration Closure
goal: remove superseded composition truth paths, promote accepted stable rules, and route every residual without erasing historical evidence
write set:
  affected composition callers and compatibility seams
  architecture standards/reference, acceptance/archive, and owner indexes
non-goals:
  silently widening profiles/plugins/hosts or treating Cordis as optional
  deleting history or absorbing held Node/external programs into closure
validation:
  full acceptance matrix and Cordis/native vertical conformance
  caller/truth-path inventory, retained compatibility proof, link/bilingual audits
closure:
  no dual composition truth path remains; optional Node/external residuals have
  named owners and cannot weaken the admitted producer/native path
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
- New acceptance or closure claims require implementation evidence.
- P2-C0 froze the only high-level request/catalog-lock authority, P2-C1 proves
  the default Cordis/native path, P3-A owns the default component/system graph
  admission, and P3-B binds the default profile projection while keeping Node hosting, external packaging, and private
  package pipelines out of the accepted slices.
- The bounded closure does not imply broader profile/backend/host or
  external-plugin acceptance. Node hosting remains conditional on a separate
  host decision.

## Archived Queue Rule

This queue has no next eligible item. Future residual work requires a new
active owner packet and must not reopen or edit this historical dependency
sequence as if it were an active dispatch surface.
