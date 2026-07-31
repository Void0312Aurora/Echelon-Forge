# CUDA-Resident Runtime Program 2 Iteration Log

Language versions:

- English canonical: `cuda_resident_runtime_program_2_iteration_log_20260731.md`
- Chinese companion: [cuda_resident_runtime_program_2_iteration_log_20260731.zh.md](cuda_resident_runtime_program_2_iteration_log_20260731.zh.md)
- Program authority: [cuda_resident_runtime_program_2_20260731.md](cuda_resident_runtime_program_2_20260731.md)
- Size policy: [cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)

- Branch: `codex/cuda-resident-runtime-program-2`
- Parent: `935926e83b18187c79a6e0be2ca010276c1a6fc4`
- Maintained baseline: `395e02b7dfeaa87baedb2611ec503d14ab137ce3`

Status: **CR2-1 implementation candidate; independent review and commit are
pending.**
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
