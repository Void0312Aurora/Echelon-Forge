# Architecture test proof levels

Issue: #125
Owner: architecture maintainers

## Evidence vocabulary

| Level | What a pass establishes | What it does not establish |
|---|---|---|
| Literal | Expected spelling is present/absent | Renamed symbols, aliases, runtime activation |
| Lexical/source shape | Patterns in the scanned source subset | C++ parsing, macro expansion, configured targets |
| AST/static semantic | Python syntax/import or a resolved literal graph | Arbitrary dynamic imports, runtime call reachability |
| Compiler/link | The configured target compiles/links its admitted contracts | Every configuration or runtime ordering |
| Contract/behavior | A real object rejects/accepts tested inputs or reproduces a workload | Untested domains and timing conditions |
| Process/integration | Native/binding/process paths agree for a bounded workload | General performance or whole-system correctness |

## Maintained key invariant inventory

Paths are repository-relative. This table describes evidence per invariant;
test-file counts are neither collected-case counts nor counts of substring tests.

| Invariant / owner | Cheap guard and level | Stronger evidence / acceptance authority | Remaining limit |
|---|---|---|---|
| Facade/backend isolation / runtime facade | `tests/architecture/runtime_facade/test_design_boundary_gates.py`: lexical and literal | `src/tests/test_world_batch_backend_contract.cpp`, `tests/runtime/facade/test_runtime_facade_core.py`: native contract and live binding | Name checks can miss renamed/macro owners; native probes cover admitted backend, not all extensions |
| World-batch Python owner / RL runtime | `test_world_batch_owner_imports.py`: AST imports plus literal shim | Runtime facade/vec-env suites and #60 dependency AST graph | Nonliteral dynamic import aliases are not resolved; negative alias fixtures cover admitted static syntax |
| Candidate exclusion / runtime host | `test_runtime_kernel_candidate_contract.py`: mixed literal build claims and Python contract behavior | #60 target graph now rejects transitive candidate links; native candidate/parity targets qualify shadow behavior | Source CMake graph does not evaluate conditions/variables; configured Linux/Windows compilation remains necessary |
| Stable-ID creation / kernel and platform factory | `test_key_entity_stamping_guard.py`: lexical creation shapes | `src/tests/test_stable_entity_identity.cpp` and `tests/runtime/air_combat/test_stable_entity_identity_draws.py`: lifecycle and raw-ID-recycling outcome behavior | Creation order intentionally changes serials; stochastic site correlations remain |
| Stochastic helper ownership / kernel | `test_stochastic_draw_guard.py`: explicit source-shape scanner | Golden RNG stream and native identity tests; #124 subprocess fault probes | Scanner is not a compiler; fatal defects still kill a non-isolated worker |
| Dependency direction / architecture | `tools/architecture/dependency_inventory.py` + `dependency_policy.py`: AST imports, lexical includes, source CMake graph | Existing negative reverse-edge, cycle and transition-growth fixtures | No parallel scanner; conditional includes and runtime plugin loads remain outside static proof |
| Declared versus installed scheduler / kernel | Composition registry/source contracts: declared metadata | #127 native installed-system/phase/pipeline diagnostics and runtime topology/hash tests | Candidate, active, and phase orders are distinct; declaration SHA is not a runtime schedule SHA |
| Snapshot producer / air EW | Prior numeric-marker literal checks | #128 native writer/reflection and Python semantic producer tests | Integer compatibility marker is retained; semantic owner is authoritative |
| Cross-host semantics / runtime composition | Schemas/hashes: contract integrity | P7 native + Python + Cordis live probe against frozen behavior | Raw ID allocation is not a physical semantic; historical comparison verifies consistent world/entity roles first |
| Fatal native boundaries / kernel | Shared preflight predicate and source guards | #124 actual abort subprocesses, catchable Python rejection, replacement worker | No automatic supervision/checkpoint recovery |
| Tuning ownership / air content | X-macro/declaration/pinned-field guard: source shape | #122 loaded fields and actual aerodynamic coefficient tests | Provisional defaults are not calibrated scientific truth |

## Highest-value strengthening in this change

The source CMake graph now checks transitive production reachability into candidate
targets and rejects a renamed intermediate adapter. The existing Python AST owner
scanner rejects aliased static shim imports and ignores comments. These reuse
#60's inventory rather than adding another dependency scanner.

P7's frozen comparison now validates the one-entity-per-world initial/action/final
references before normalizing handles to world roles. Live native/Python integer
IDs remain exactly compared. Negative fixtures reject an action/final reference
to a different entity, an incorrect world, and altered physical output. The
frozen physical reference and its digest are not re-recorded. This removes a
census-dependent false failure while making reference consistency explicit.

## Lane ownership and cost

The existing `tests/suites/architecture_guard_suite.json` owns pre-merge boundary
checks; `governance_audit_suite.json` owns on-demand documentation/authority audit.
Use `python tools/runners/audit_test_authority.py --format markdown --output report.md`
to derive the complete live file-to-suite inventory, scan references, and current
ownership. Its derived report does not certify runtime properties.

The new static negative cases reuse existing inventories and add no native build.
P7 remains in the existing Linux composition qualification lane; its live case
requires the composition evidence executable, Cordis conformance executable,
Node and local ef_py. Missing prerequisites cause a visible skip, not a claimed
pass. #124 process probes and #136 CUDA qualification have their own bounded
runtime tests. Promote or remove a cheap guard only when its replacement covers
the same failure audience and explicitly records its limits.
