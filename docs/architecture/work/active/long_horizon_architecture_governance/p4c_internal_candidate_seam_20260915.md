# P4-C Internal Candidate Seam

Status: `2026-09-19` implementation candidate; focused repair pass and
candidate-scope independent review complete.
This packet records the first P4-C integration slice after the independently
passed P4-B dark/shadow handoff. It is evidence for an internal candidate only,
not production acceptance.

Parent subproject: [Long-Horizon Architecture Governance](README.md)

Document kind: `evidence`
Lifecycle: `maintained`
Owner: `runtime integration`

## Scope

This slice adds a build-tree-only `RuntimeKernelCandidate` that binds one real
`SimulationKernel` to the accepted `RuntimeHostCandidate` and the P4-B owner
registry. Its `RuntimeKernelCandidateFacadeAdapter` supplies the existing
world-batch-shaped setup/step/query surface without owning a second host,
kernel, or publication pointer.

The native adapter enforces:

- one host-issued initial publication in `Dark` or `Shadow` mode;
- a sealed composition fingerprint (`requested`, `resolved`, executable graph,
  and five scope generations) that is compared after every candidate operation;
- `RuntimeWorldRef` and `RuntimeEntityRef` validation before every world/entity
  operation;
- a host shadow capability plus truth/read-only lease around mutating and
  observing operations;
- terminal-phase admission closes truth-mutating leases at the host boundary;
  reset remains the only terminal transition path;
- native episode action routing through the P4-B coordinator and native
  `SimulationKernel::step`, rather than a Python reset/step authority;
- terminal-action to explicit-reset routing through the same host-bound
  capability, with receipt-driven world/entity generation advancement;
- terminal receipts in the focused probe are emitted by an explicit native
  test hook, never inferred from caller payload bytes;
- candidate-generated action idempotency keys remain monotonic across reset;
- the initial plan hash is fail-closed against the sealed resolved composition;
- deterministic stale-incarnation, stale-world-generation and stale-entity-
  generation rejection;
- idempotent teardown through the host terminal lifecycle.
- strict native receipt canonicalization, replay/idempotency retention and
  bounded receipt budget in the Python shadow fence;
- native snapshot digests derived from serialized kernel world state;
- a non-reentrant target transfer fence around owner import and shared kernel
  lifetime retention across deferred host settlement;
- facade batch failure returns the successful prefix, matching the maintained
  per-request result shape rather than claiming atomic rollback.

The Python `EpochReferenceFence` mirrors the public value-contract shape for
shadow probes. It updates world/entity generations only from a native episode
receipt and rejects bare, cross-host, or stale references.

## Changed Surfaces

| Surface | Candidate-only implementation | Production boundary |
| --- | --- | --- |
| Native host/kernel seam | `src/runtime/host/integration/runtime_kernel_candidate.{h,cpp}` | build-tree source; not installed |
| Native world-batch/facade adapter | `src/runtime/host/integration/runtime_kernel_candidate_facade.{h,cpp}` | non-owning adapter; no production caller |
| Native target | `ef_runtime_kernel_candidate` | static target; no install/export entry |
| Native shadow test | `src/tests/test_runtime_kernel_candidate.cpp` | `ef_runtime_kernel_candidate_test` only |
| Python shadow reference | `python/rl/runtime/world_batch/candidate_adapter.py` | not imported by maintained `adapter.py` |
| Python contract gate | `tests/architecture/runtime_host/test_runtime_kernel_candidate_contract.py` | static boundary and fence checks |

## Verification

All commands were executed in the isolated `codex/long-horizon-governance-architecture`
worktree with the VS 2022 x64 developer environment.

```powershell
cmd /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x64 && cmake --build build-long-horizon-p4c --target ef_runtime_host_candidate_test ef_runtime_kernel_candidate_test -j 4'
ctest --test-dir build-long-horizon-p4c -R 'runtime_(kernel_candidate|host_candidate)' --output-on-failure
$env:CMO_BUILD_DIR=(Resolve-Path 'build-long-horizon-p4c').Path
python -m pytest tests/architecture/composition/test_runtime_host_candidate_contract.py tests/architecture/composition/test_runtime_state_transfer_candidate_contract.py tests/architecture/composition/test_runtime_composition_migration_closure.py tests/architecture/runtime_host/test_runtime_kernel_candidate_contract.py tests/architecture/composition/test_native_composition_lifecycle_contract.py -q
```

Observed results:

- MSVC/Ninja build: `ef_runtime_host_candidate_test` and
  `ef_runtime_kernel_candidate_test` linked successfully.
- focused CTest: `3/3` passed (`runtime_host_candidate`,
  `runtime_kernel_candidate`, and host boundary).
- native P4-C candidate: `3` test cases, `44/44` assertions passed, including
  shadow-mode batch setup, episode step, terminal-to-reset receipt flow,
  terminal write rejection, post-reset step, plan/composition binding, stale
  incarnation/generation rejection and teardown.
- focused Python host/state-transfer/composition/P4-C gates: `42 passed`,
  including strict receipt canonicalization/replay, receipt-only generation
  updates, the explicitly inventoried
  build-tree-only manifest caller, and production-boundary checks.
- real `SimulationKernel` replacement rollback: `1` case, `40/40` assertions
  passed; the final owner-row deadline drove durable owner compensation,
  restored the old active epoch and native ECS/RNG pre-images, retained the
  old result lease, and left no candidate/quarantine/orphan. The target WAL
  contained at least twelve durable `aborted` owner records.
- independent review (`gpt-5.6-sol`, `max`): `PASS` for the P4-C
  build-tree/internal candidate scope, with no remaining Critical/High/Medium
  or Low finding. The final main-thread rerun reproduced the native `44/44`,
  CTest `3/3`, and Python `42 passed` results after the receipt-acknowledge
  increment.

## Explicit Non-Claims

This packet does not claim:

- migration of `python/rl/runtime/world_batch/adapter.py`, maintained
  `RuntimeFacade`, bindings, examples, or diagnostics callers;
- full maintained-facade parity or a complete caller inventory refresh;
- production package/wheel inclusion, production publication, or rebuild
  retirement;
- cross-process WAL locking, released-version N-1 fixtures, or production
  ArtifactLedger qualification;
- complete recovery transfer, stress/resource qualification, process restart,
  or a P5-D package/cutover rollback drill. The replacement failure path above
  is candidate-owned test evidence only.
- source-level `wheel.packages = ["python", ...]` remains broad, but the
  candidate module is explicitly excluded by `tool.scikit-build.wheel.exclude`;
  it is not imported by maintained runtime code.

Those remain P4-C review residuals or later P5 gates. The current candidate is
therefore `implementation-ready-for-independent-review`, not an accepted
cluster and not a production truth path.
