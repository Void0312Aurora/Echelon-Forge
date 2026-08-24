# Runtime Composition Baseline

Status: `2026-08-23` maintained architecture standard promoted from the accepted
bounded Cordis simulation-composition program.

Language:

- English canonical: `runtime_composition_baseline.md`
- Chinese companion: [runtime_composition_baseline.zh.md](runtime_composition_baseline.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/runtime_composition_baseline.md`
Owner: `architecture/runtime-composition`
Last verified: `2026-08-23`

Related authority:

- [Simulation system architecture design](simulation_system_architecture_design.md)
- [Runtime workflow and contract baseline](runtime_workflow_and_contract_baseline.md)
- [Archived Cordis composition program](../work/archive/cordis_simulation_composition_kernel/README.md)

## Accepted Boundary

The maintained baseline is the repository-owned `builtin.default_compatibility`
profile on the `cpu_exact.reference` backend. Experiment intent is lowered by
the repository Cordis producer, joined to owner admission, emitted as canonical
requested/resolved artifacts, revalidated by native C++, and executed only by
the native runtime. Python is an admitted caller of that native runtime; it is
not a second simulation owner.

This standard does not admit additional profiles, providers, CUDA parity, a
Node host, external plugin distribution, or state-complete replay.

## Authority Chain

The maintained direction is singular:

1. The Experiment Face owns experiment intent.
2. `@echelon-forge/cordis-runtime` owns the admitted high-level default-profile
   lowering and repository package/provenance layer.
3. Category owners admit descriptors into the versioned catalog lock. Cordis
   cannot invent or privately admit model, system, backend, domain, evidence,
   or security implementations.
4. The requested and resolved low-level manifests are the producer/native
   interchange. Native code reparses and revalidates their identities and
   owner joins.
5. `build_default_simulation_composition` is the single admitted production
   entry and `build_default_simulation_composition_impl` is the single native
   model/service realization function. The documented test-only publication-
   failure wrapper delegates to that realizer. `materialize_default_world_batch_backend`
   is the maintained backend-provider materializer.
6. `SimulationKernel::step` and the native stage/runtime owners remain the only
   deterministic execution authority. Cordis and bindings never execute a
   semantic stage callback.

## Construction And Compatibility Rules

- `SimulationKernel(std::string resolved_manifest_json)` is the explicit native
  manifest bridge.
- `SimulationKernel()` is retained for established C++/Python diagnostics and
  compatibility callers, but it must explicitly supply the generated default
  resolved artifact to the same native builder. Empty input must never mean
  "select a hidden default."
- `WorldBatchRuntime` is an internal native-backend wrapper. Maintained host
  code enters through `RuntimeFacade`, whose concrete backend is selected only
  by the admitted backend-provider catalog.
- A constructor, setter, binding, package, or environment variable must not
  become another model/service/system/backend composition truth source.
- The test-only publication-failure seam must use the generated default
  artifact and the shared native realizer. It may inject only the named staged
  publication failure and must not become a runtime configuration surface.
- The retired model replacement setters must remain absent. A future
  replacement protocol requires an owner-approved lifecycle/rebuild contract;
  reintroducing an ad hoc setter is forbidden.

## Graph, Lifecycle, And Evidence Rules

- Owner-derived contribution registries and the admitted catalog lock own
  component/system/provider membership; file discovery and Cordis package
  discovery do not grant admission.
- Realization is deterministic, transactional, generation-checked, and
  reverse-disposed. Failed construction cannot publish partial services.
- Truth-affecting rebuild is allowed only at its declared barrier and is closed
  after raw-world exposure or world mutation according to the native lifecycle
  contract.
- Maintained evidence binds request, catalog lock, profile projection,
  requested/resolved manifests, provider versions, executable graph, backend,
  worlds/scopes, and the native execution owner. Replay/comparison fails closed
  on unexplained mismatch.
- Host parity compares native-direct and local Python callers with frozen
  semantics and separately approved performance budgets. Caller language does
  not alter execution ownership.

## Security And Extension Rule

The accepted security boundary is repository-built and owner-admitted code with
sealed package provenance. External native artifacts are not admitted by this
baseline. Signing, distribution, ABI trust, sandboxing, remote catalogs, and
marketplace policy require a separately approved security program.

## Held Residuals

| Residual | Owner | Activation gate |
| --- | --- | --- |
| Node host adapter | `interfaces/node` | explicit approved host use case and P6-B dispatch |
| broader profiles/providers | `architecture/runtime-composition` plus category owners | owner admission and profile/provider parity evidence |
| CUDA backend parity | `runtime/backend` | separate exact-runtime CUDA admission and parity gate |
| external plugin distribution/signing | `owner.security` | authenticity, ABI, distribution, and trust policy |
| complete state replay | `runtime/evidence` | state-complete replay contract beyond composition compatibility |

Held residuals cannot weaken the default producer/native path and are not
implicitly accepted by future use of the word "plugin" or "Cordis."

## Executable Governance

The P8 closure record is
[`default_runtime_composition_migration_closure.v1.json`](../../../tests/architecture/composition/fixtures/default_runtime_composition_migration_closure.v1.json).
It is regenerated and validated by
[`runtime_composition_migration_closure.py`](../../../tools/maintenance/runtime_composition_migration_closure.py).
The guard inventories maintained callers, binds the accepted authority hashes,
proves the retired surfaces absent, and rejects re-sealed authority, caller,
setter, residual-owner, or Node-admission forgery.

Changes to this baseline require the relevant owner, regenerated closure
evidence, Cordis/native vertical conformance, focused native/Python tests, and
documentation/link validation.
