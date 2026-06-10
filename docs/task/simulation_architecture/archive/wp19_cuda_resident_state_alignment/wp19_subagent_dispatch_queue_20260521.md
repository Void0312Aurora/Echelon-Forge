# WP19 Subagent Dispatch Queue

Status: `2026-05-21` closed / accepted.

Language:

- English canonical: `wp19_subagent_dispatch_queue_20260521.md`
- Chinese companion:
  [wp19_subagent_dispatch_queue_20260521.zh.md](wp19_subagent_dispatch_queue_20260521.zh.md)

Use this queue when launching subagents. The main thread owns integration and
final acceptance.

## First Wave

| Stream | Agent type | Model / reasoning | Task | Write scope |
|--------|------------|-------------------|------|-------------|
| `WP19-A` | worker | `gpt-5.4-mini`, xhigh | Verify CUDA/resident-state facts, helper/probe surfaces, support flags, and first-slice candidates. | WP19-A ledger docs and read-only inventory notes only; no runtime behavior changes. |
| `WP19-B` | worker | `gpt-5.4`, high | Preflight a device-resident output contract and identify DTO/test placement without support promotion. | Contract/DTO preflight notes and focused tests if safe; do not edit CUDA helpers. |
| `WP19-C` | worker | `gpt-5.4`, high | Harden or preflight GPU helper/probe diagnostics boundary and non-promotion tests. | GPU helper binding/architecture tests or notes; do not edit sync/shard semantics. |
| `WP19-D` | worker | `gpt-5.4`, xhigh | Build resident-state sync/shard preflight mapped to current runtime evidence. | Sync/shard contract docs/tests only; do not edit CUDA helper implementations. |

## Held Streams

| Stream | Release condition |
|--------|-------------------|
| `WP19-E` | Release after A-D return a safe bounded helper/output slice. |
| `WP19-F` | Release after A-E return mergeable or blocked packets. |

## First-Wave Return State

| Stream | Agent | Return status | Planning consequence |
|--------|-------|---------------|----------------------|
| `WP19-A` | Turing | `preflight-only / pass` | CUDA helper, probe, capability, and `WorldBatchRuntime` facts are frozen in the WP19-A ledger. WP19-E remains preflight unless a bounded host-owned helper slice is selected. |
| `WP19-B` | Singer | `preflight-only / pass` | Additive device-resident descriptor seam is justified, but it must not be embedded in `ObservationBatchPacket`, `EngagementEventPacket`, or `RuntimeCapabilities`. |
| `WP19-C` | Descartes | `pass after standard-env revalidation` | Helper/probe diagnostics guards and tests are tightened. Initial blocker was bare `python` loading a stale global `ef_py`; `bash tools/maintenance/cmo_env.sh` validates the suite. |
| `WP19-D` | Ramanujan | `preflight-only / pass` | Resident-state shard/barrier/ownership baseline is mapped to current runtime evidence. No resident-state promotion is justified. |

Main-thread validation after first wave:

- `git diff --check` passed.
- `python -m py_compile tests/architecture/runtime_facade/test_layering.py tests/test_gpu_runtime_bindings.py tests/architecture/runtime_facade/test_dto_contracts_batch1.py` passed.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade/test_layering.py` passed: `22 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/test_gpu_runtime_bindings.py` passed: `12 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade/test_dto_contracts_batch1.py -k "device_resident or packet"` passed: `2 passed, 4 deselected`.
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP19 --summary` passed.

## Second Wave

| Stream | Agent type | Model / reasoning | Task | Write scope |
|--------|------------|-------------------|------|-------------|
| `WP19-B2` | worker | `gpt-5.4`, high | Implement the additive export-only `DeviceResidentOutputDescriptor` seam with bindings and tests, without attaching it to maintained packets or capability projection. | `src/runtime/facade/runtime_facade_types.h`, `src/interfaces/python/bindings_runtime.cpp`, focused binding/architecture tests, and WP19-B docs only. Do not edit CUDA helper implementations or `WorldBatchRuntime`. |
| `WP19-E1` | worker | `gpt-5.4`, xhigh | Select and, only if safe, implement one host-owned broadphase candidate-list alignment slice with explicit host post-filter evidence. | `src/core/engine/world_batch_runtime.*`, `tests/world_batch/test_world_batch_runtime.py`, and WP19-E docs only. Do not edit facade DTO/bindings or support flags. |

## Second-Wave Return State

| Stream | Agent | Return status | Integration consequence |
|--------|-------|---------------|-------------------------|
| `WP19-B2` | Laplace | `pass` | `DeviceResidentOutputDescriptor` is implemented as a standalone export-only DTO with bindings and focused tests. It is not attached to maintained packets or capability projection. |
| `WP19-E1` | Carver | `pass / evidence-only` | Existing `WorldBatchRuntime` broadphase candidate-list path already satisfies the selected host-owned helper boundary; focused tests now prove `use_gpu=True` preserves host filtering semantics and fail-closed capabilities. |

Main-thread validation after second wave:

- `git diff --check` passed.
- `cmake --build build-workshop --target ef_py -j4` passed.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py` passed: `20 passed`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/runtime_facade/test_dto_contracts_batch1.py -k "device_resident or packet"` passed: `3 passed, 4 deselected`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "candidate or gpu or broadphase or visual or comm or sensor"` passed: `4 passed, 17 deselected`.
- `bash tools/maintenance/cmo_env.sh python -m pytest -q tests/test_gpu_runtime_bindings.py` passed: `12 passed`.
- `python3 tools/maintenance/wp_doc_closure_audit.py --wp WP19 --summary` passed.

## Closure Wave

| Stream | Agent type | Model / reasoning | Task | Write scope |
|--------|------------|-------------------|------|-------------|
| `WP19-F` | worker | `gpt-5.4-mini`, xhigh | Integrate A-E/B2/E1 results, record validation rollup and residuals, sync README/review indexes, bilingual closure docs, and acceptance review. | WP19-F docs, WP19 dispatch queue, README/review indexes, acceptance review, and bilingual companions only. Do not edit runtime implementation. |

## Required Worker Return Packet

```md
Stream:
Status: pass | fail | blocked | preflight-only
Touched files:
Commands run:
Evidence:
Residuals:
Integration notes:
Closure impact:
```

Worker reminder:

- You are not alone in the codebase; do not revert unrelated edits or edits made
  by other workers.
- Keep write scopes disjoint.
- Stop at a named blocker rather than broadening into WP20/WP21 or exact GPU
  promotion.
