# CUDA-Resident Runtime Program 2 Iteration Log

Language versions:

- English canonical: `cuda_resident_runtime_program_2_iteration_log_20260731.md`
- Chinese companion: [cuda_resident_runtime_program_2_iteration_log_20260731.zh.md](cuda_resident_runtime_program_2_iteration_log_20260731.zh.md)
- Program authority: [cuda_resident_runtime_program_2_20260731.md](cuda_resident_runtime_program_2_20260731.md)
- Size policy: [cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)

- Branch: `codex/cuda-resident-runtime-program-2`
- Parent: `935926e83b18187c79a6e0be2ca010276c1a6fc4`
- Maintained baseline: `395e02b7dfeaa87baedb2611ec503d14ab137ce3`

Status: **CR2-2a is committed as bf695071 and CR2-2p is committed as dee02146.
CR2-2b is the active, independently reviewable full-window candidate.**
The RB0-RB11 program remains closed without promotion. This ledger records only
the new branch-local program and does not alter maintained support flags.

## CR2-0 candidate — program and size-governance freeze

### Read-only baseline audit

The scoped CUDA-resident inventory was counted from tracked file bytes with
physical `splitlines()` semantics:

| Path | Lines | Classification | Action |
| --- | ---: | --- | --- |
| `src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda.cu` | 2528 | hard-limit violation | split first in CR2-1; no semantic growth |
| `src/tests/test_cuda_resident_replay.cpp` | 919 | review band | freeze growth; split before modification |
| `src/tools/experimental/cuda_resident/cuda_resident_rb9_probe.cpp` | 804 | review band | freeze growth; split or reclassify before expansion |
| `src/runtime/facade/internal/cuda_resident/cuda_world_store.cpp` | 629 | below soft target | may change only within one semantic slice |
| `src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp` | 587 | below soft target | may change only within one semantic slice |
| `src/runtime/facade/internal/cuda_resident/cuda_resident_backend.cpp` | 582 | below soft target | may change only within one semantic slice |

The broader repository has unrelated files above 1000 lines. CR2 does not
silently classify or rewrite those files; the policy applies to the
CUDA-resident scope listed in the machine-readable record.

### Frozen write set

CR2-0 is documentation and guard code only:

- the English/Chinese program pair and iteration log;
- the machine-readable size policy;
- the exact-runtime and parent plan indexes;
- the `.gitattributes` byte-stability rule for the policy JSON; and
- the architecture test that enforces the baseline exception/watch-item rules.

No runtime, CUDA kernel, CMake target, support flag, ABI, or performance data is
changed by CR2-0.
The size guard scans both tracked files and on-disk candidate files under the
declared CR2 artifact prefixes before staging; the independent reviewer checks
the complete staged/untracked write set as well.

### Review gate

An independent reviewer must verify the branch base, exact write set, line/byte
thresholds, baseline exception expiry, and the absence of runtime changes. Only
an `APPROVE` verdict permits one CR2-0 commit. CR2-1 is the sole next
authorization, and it must remove the 2528-line exception before semantic work.

## CR2-1 candidate — physical CUDA translation-unit split

CR2-1 keeps the old kernel bodies, host-visible error behavior, and private
window trace intact while moving the implementation into separate translation
units. The deleted `cuda_world_store_cuda.cu` is not replaced by a larger
coordinator; the new coordinator is a 69-line host wrapper file.

### Exact write set

- Replace the resident CUDA source in `CMakeLists.txt` with eight `.cu` files;
- add one shared internal `.cuh` contract and one shared device-math `.cuh`;
- add the storage, barrier, Phase A, Phase B, Phase D, observation, state
  readback, and window `.cu` files;
- update the CUDA architecture guards and the RB9 ledger source label;
- update the performance contract comment to name the split source family;
- remove the old 2528-line monolith.

No public facade, support flag, ABI, DTO, runtime selection, or CUDA separable
compilation setting is changed. The resident target uses ordinary host wrappers
across translation units; kernels and device helpers remain private to their
own `.cu` file.

### Structural invariants

- Ten kernels remain: Phase A (1), Phase B (3), Phase D (3), observation (2),
  and barrier (1).
- The full private window still launches the six B/D kernels in the same order,
  performs one `cudaDeviceSynchronize()` after the sequence, and preserves
  status/error checks and barrier publication.
- The resource-query helper retains fixed 128-thread occupancy semantics and
  the existing error strings.
- No resident target uses CUDA separable compilation/RDC.

### Size evidence

| Module | Lines |
| --- | ---: |
| `cuda_world_store_cuda_internal.cuh` | 291 |
| `cuda_world_store_cuda_math.cuh` | 139 |
| `cuda_world_store_cuda_storage.cu` | 547 |
| `cuda_world_store_cuda_barrier.cu` | 264 |
| `cuda_world_store_cuda_phase_a.cu` | 204 |
| `cuda_world_store_cuda_phase_b.cu` | 497 |
| `cuda_world_store_cuda_phase_d.cu` | 231 |
| `cuda_world_store_cuda_observation.cu` | 174 |
| `cuda_world_store_cuda_state_readback.cu` | 271 |
| `cuda_world_store_cuda_window.cu` | 69 |

The CR2-0 2528-line exception is now empty in the machine-readable policy. The
919-line replay test and 804-line RB9 probe remain frozen watch items.

### Validation evidence

- Visual Studio/CUDA 13.0, `CMAKE_CUDA_ARCHITECTURES=86`, Release build:
  `ef_cuda_resident_lifecycle_test`, `ef_cuda_resident_replay_test`, and
  `ef_cuda_resident_rb9_cuda_probe` all compile and link.
- Lifecycle executable: 11/11 test cases, 527/527 assertions passed.
- Replay executable: 3/3 test cases, 47/47 assertions passed.
- RB9 CUDA probe ran on an NVIDIA GeForce RTX 3090 (SM 8.6). Its existing
  hold reasons remain explicit: full-facade invocation is unavailable,
  learner/device consumption is unavailable, GPU counters report
  `ERR_NVGPUCTRPERM`, and identity-inclusive reset determinism is diagnostic.
- CUDA-off configuration succeeded; the CPU lifecycle/replay targets built and
  passed (11/11 with 66 assertions; 3/3 with 14 assertions). The complete
  CUDA-off probe target was not built because the unrelated `ef_core` graph
  currently fails MSVC compilation at existing portability errors such as
  `__builtin_ctz` and `M_PI`.
- Architecture/size/performance/Phase A/B/D focused tests: 31 passed; Ruff and
  `git diff --check` passed.
- The complete `tests/architecture/runtime_profiles` run was 52 passed and 15
  failures; every failure was the existing Windows `g++`-not-found snippet
  environment (`WinError 2`), outside CR2-1's changed paths.

### Independent review gate

Fresh reviewer `/root/cr2_split_review` returned **`APPROVE`** after checking the
complete staged/unstaged/untracked write set, normalized kernel/function-body
comparisons against the RB11 monolith, CMake device-link topology, size policy,
and the focused build/test evidence. The reviewer found no CR2-1 blocker. The
exact write set above is now authorized for one CR2-1 commit; no merge, push, or
promotion follows from this commit.

## CR2-2a candidate — RB9 probe session split

### Scope and frozen behavior

This sub-iteration is structural only. The RB9 executable keeps its existing
CPU/CUDA lane selection, mode matrix, private phase sequence, JSON schema,
trace signatures, unavailable reasons, and hold reasons. Historical evidence
under cuda_resident_rb9_evidence_20260730 is untouched. No full-window SPI,
facade, support flag, learner contract, or performance claim is added.

### Exact write set

- add cuda_resident_rb9_probe_session.h with the small ProbeSession/Mode/
  WindowTiming interface;
- add cuda_resident_rb9_probe_session.cpp with the lane-specific session
  storage, setup/reset, window execution, digest, and diagnostics;
- remove the duplicated session implementation and helper functions from
  cuda_resident_rb9_probe.cpp;
- compile the new implementation in both RB9 CMake targets;
- update the performance architecture guard to inspect the moved CUDA sequence;
- remove the resolved probe watch item from the machine-readable size policy;
- update the English/Chinese program plans and this iteration ledger.

### Size and validation evidence

The probe is 567 physical lines, the new session implementation is 255 lines,
and the interface header is 45 lines. Both implementation files are below the
700-line soft target; the replay test remains the sole review-band watch item.
Focused architecture tests passed: 27 size/performance/Phase A/B/D tests and
20 contract/lifecycle/closure/replay tests. CUDA Release (VS2022, CUDA 13.0,
SM86) reconfigured and built the probe, lifecycle, and replay targets; lifecycle
passed 11/11 cases and 527/527 assertions, replay passed 3/3 and 47/47, and the
probe smoke run returned zero on the RTX 3090 with the existing private-surface
hold reasons unchanged. The CUDA-off probe target remains blocked by unrelated
ef_core MSVC portability errors (__builtin_ctz, M_PI, and follow-on diagnostics).
An isolated MSBuild ClCompile pass with project references disabled successfully
compiled the CPU probe, the new session implementation, and the replay harness.

### Independent review gate

Fresh reviewer /root/cr2_2a_review returned **APPROVE** after checking the
complete staged/unstaged/untracked write set, all ten migrated observable
strings, CPU/CUDA operation order and timing boundary, both CMake lanes, line
counts, focused tests/build evidence, and the untouched historical RB9
evidence. No CR2-2a blocker was found. This verdict authorizes one CR2-2a
commit; it does not authorize merge, push, promotion, CR2-2b semantics, or a
historical evidence rewrite.

## CR2-2p candidate — real Flecs CPU lane portability prerequisite

### Scope and exact write set

CR2-2b cannot claim a real CPU/CUDA common surface while the maintained
`FlecsCpuBackend` graph does not compile under the selected VS2022 toolchain.
This prerequisite is isolated from the full-window semantics and contains only:

- replace GCC-only `__builtin_ctz` with the C++20 `std::countr_zero` equivalent;
- move `environment_model.h` out of the `IControlModel` class body and update
  the two stale nested-type spellings to the intended global interface;
- enable the existing `M_PI` formulas for `ef_core` on MSVC without changing
  their values; and
- add a focused architecture guard plus this English/Chinese ledger update.

No CUDA source, resident contract, support flag, facade selection, performance
result, or CR2-2b runner/probe file belongs to this commit.

### Validation and size evidence

VS2022 Release successfully built `ef_core`, `ef_facade`, and the candidate real
Flecs full-window CPU probe. That probe loaded `examples/config/database` outside
the runner and completed two windows with exit code zero. The wider `ef_test`
build advanced past the corrected core/control-model units but remains blocked
by separate pre-existing MSVC issues in test-owned headers (for example
`kalman_seeker.h` uses `M_PI` outside `ef_core`). These unrelated failures are
not expanded into this prerequisite.

`control_model.h` is 28 lines and `default_control_model.cpp` is 542 lines.
`world_batch_runtime.cpp` was already 1207 lines before this candidate and is
1208 after adding `<bit>`; it is a pre-existing non-CR2-owned hard-limit debt,
not a new module or an exception hidden by the CR2 policy. This prerequisite
does not split that owner because doing so would mix structural refactoring with
the narrow portability unblock; the debt remains explicitly visible.

### Independent review gate

An independent reviewer verified the exact staged subset, API/type intent,
bit-scan equivalence, MSVC definition scope, focused build evidence, and the
absence of CR2-2b semantic files, returning **`APPROVE`**. CR2-2p was committed
as `dee02146`; it does not authorize merge, push, promotion, or CR2-2b itself.

## CR2-2b candidate — one full-window SPI for both real lanes

### Scope and exact write set

CR2-2b adds a backend-neutral, synchronous runner over the existing
`IWorldBatchBackend`; it does not add a second facade or a support/admission
surface. The runner owns the one declared sequence:

```text
setup → input_injection → evaluation(empty) → advance(WorldBatch) → export
```

The CUDA backend's `advance` calls `CudaWorldStore::advance_window()`, which
automatically publishes an injected stage and commits the window. The store's
explicit state machine is `awaiting_input → input_injected → stage_published →
awaiting_input`; failed publish stays `input_injected`, failed commit stays
`stage_published` so retry cannot republish, and reinjection is rejected until
commit/reset/setup. The runner poisons a session after any failure and records a
stable operation/failure code and last completed surface barrier.

The write set is limited to the full-window contract/runner, CUDA backend/store
state transition, conformance tests, two lane probe targets using one probe
source, the pure-JSON CPU/CUDA comparator, focused architecture guards, and
this plan/ledger update. CPU database loading remains outside the runner.
The historical RB9 probe/session and `cuda_resident_rb9_evidence_20260730`
remain untouched; no learner lease or performance claim is introduced.

### Size and validation evidence

All new CR2-2b implementation/test/probe modules are below the 700-line soft
target: contract 105, runner 242/30, probe 179, comparator 76, conformance test
365, and architecture guard 87 lines. The existing 919-line replay test did not
grow. The changed resident host modules are 665 (`cuda_world_store.cpp`) and 586
(`cuda_resident_backend.cpp`), both below the soft target.

The CUDA Release target (VS2022, CUDA 13.0, SM86) built and ran the full-window
probe, which completed two windows and nine surface operations. The CPU Release
target built `ef_core`, `ef_facade`, and the real `FlecsCpuBackend` probe after
CR2-2p; it loaded the database outside the runner and completed the same trace.
The automated comparator parsed both stdout streams as pure JSON and confirmed
equal surface id, trace signature, and all nine operation/request/window/
success/barrier records; lane/backend identifiers remained intentionally
different. The full-window doctest passed 5/5 cases and 122/122 assertions on
CUDA and 5/5 cases and 105/105 assertions on the CUDA-off stub; the lifecycle
suite passed 11/11 and 528/528 after the stricter injection guard, and replay
passed 3/3 and 47/47.

### Independent review gate

The complete staged/unstaged/untracked CR2-2b write set must be reviewed by a
fresh independent agent for the common sequence, state-machine retry semantics,
pure-JSON comparison evidence, exact CMake lane topology, support-flag
invariance, historical evidence preservation, and all size limits. Only
`APPROVE` permits one CR2-2b commit.
