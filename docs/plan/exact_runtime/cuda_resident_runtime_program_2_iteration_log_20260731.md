# CUDA-Resident Runtime Program 2 Iteration Log

Language versions:

- English canonical: `cuda_resident_runtime_program_2_iteration_log_20260731.md`
- Chinese companion: [cuda_resident_runtime_program_2_iteration_log_20260731.zh.md](cuda_resident_runtime_program_2_iteration_log_20260731.zh.md)
- Program authority: [cuda_resident_runtime_program_2_20260731.md](cuda_resident_runtime_program_2_20260731.md)
- Size policy: [cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)

- Branch: `codex/cuda-resident-runtime-program-2`
- Parent: `935926e83b18187c79a6e0be2ca010276c1a6fc4`
- Maintained baseline: `395e02b7dfeaa87baedb2611ec503d14ab137ce3`

Status: **CR2-0 candidate freeze; independent review and commit are pending.**
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
