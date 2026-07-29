# CUDA-Resident Backend Branch Iteration Log

Language versions:

- English canonical: `cuda_resident_backend_iteration_log_20260729.md`
- Chinese companion: [cuda_resident_backend_iteration_log_20260729.zh.md](cuda_resident_backend_iteration_log_20260729.zh.md)

- Document type: branch-local iteration and review ledger
- Lifecycle: maintained while `codex/cuda-resident-backend` is active
- Program authority: [cuda_resident_backend_program_20260729.md](cuda_resident_backend_program_20260729.md)
- Baseline: `395e02b7dfeaa87baedb2611ec503d14ab137ce3`

Status: **RB0 and RB1 are accepted. RB2 is the only currently authorized
implementation iteration. RB3-RB11 remain dependency-gated.**

This ledger records branch-local evidence. It does not allocate a central
`I<n>` acceptance row and does not claim that a branch commit has landed on the
maintained branch. The enclosing branch history is the source of truth for the
final commit identity of each row.

## RB0 - Program Freeze

- Commit: `e7f3b144` (`docs: freeze CUDA resident backend program (RB0)`).
- Write set: the bilingual program, exact-runtime indexes, parent plan indexes,
  and the selective bilingual-registry record required by the parent indexes.
- Non-goals: no C++, CUDA, Python, CMake, test, runtime-profile, capability-flag,
  or support-projection change.
- Validation: bilingual companion and registry checks, local link audit, and
  `git diff --check` passed.
- Independent review: `/root/rb0_plan_review`, staged patch
  `09593c539c946f19f4b5bf45c90d35f11b6f62b0`, `APPROVE` with zero blockers.

## RB1 - Semantic Backend Seam And CPU Adapter

### Frozen write set

- facade-internal backend SPI, compatibility port, and `FlecsCpuBackend`;
- `RuntimeFacade` ownership and forwarding implementation;
- the shared recent-engagement-event contract needed to keep the semantic SPI
  independent of the Flecs runtime and GPU visual types;
- build registration, C++ contract probes, focused runtime/architecture tests,
  schema freshness metadata, and this ledger/status update.

### Non-goals

- no `CudaResidentBackend`, CUDA allocation, or simulation kernel;
- no backend request/profile admission yet;
- no public support-flag or capability promotion;
- no CPU behavior change, implicit fallback, public ABI expansion, or GPU
  pointer in the semantic backend contract.

### Result

- `RuntimeFacade` now owns `std::unique_ptr<IWorldBatchBackend>` and constructs a
  used `FlecsCpuBackend` composition adapter. `WorldBatchRuntime` remains
  non-polymorphic.
- Semantic request DTOs use pointer-sized, non-owning `VectorBatchView<T>`
  references to live caller vectors. Rvalue-vector construction is deleted, so
  the seam does not copy hot batches or accept temporary containers.
- Read-only execution evaluation maps to backend `evaluate(...) const`; stateful
  advancement remains a separate operation.
- Legacy visual/GPU-shaped calls are quarantined behind
  `IWorldBatchCompatibilityPort` and do not pollute the semantic SPI.
- `RecentEngagementEvents` has one shared contract owner; the engine header is a
  compatibility re-export, with generated schema and Python binding paths
  updated to the same field source.
- CUDA-disabled and CPU-default behavior remain unchanged.

### Validation

- CUDA-off Release build of `ef_test` and `ef_py`: pass.
- `ef_test`: `147/147` test cases, `19,161` assertions passed.
- Runtime-facade architecture/core/counterfactual and DTO-freshness selection:
  `104 passed`.
- Reviewer-requested structural/event selection after repair: `11 passed` both
  locally and in the independent review.
- Changed C++ `clang-format --dry-run -Werror`, changed Python `ruff`, and
  `git diff --check`: pass.

Two wider-suite environment/baseline items are not attributed to RB1 and remain
outside its write set: an unchanged window-loop source-text expectation and an
optional `stable_baselines3` import missing from the local environment.

### Independent review and repair history

1. Initial review blocked a runtime-shaped interface, a mechanically mirrored
   runtime path, polymorphic drift in `WorldBatchRuntime`, and tests that did
   not prove the facade cutover. The implementation was replaced by the
   semantic SPI plus composition adapter.
2. Re-review blocked owning-vector request DTOs and a const-evaluation path that
   mapped to stateful advance. Both were replaced by non-owning views and a
   distinct const backend method. The duplicated event batch definition was
   also consolidated into the shared contract.
3. Final review found two stale structural tests still naming the old event
   definition owner. Their ownership assertions were corrected without
   weakening the SimulationKernel isolation guards.
4. `/root/rb1_backend_review` independently reran the repaired selection and
   approved the staged code/test candidate identified by
   `git hash-object --stdin` as
   `3703fcd6f05a57f38df3c310e2fc595bf9cee849`.

Verdict: **accepted for one RB1 commit**. The next authorized work is RB2 only:
explicit backend request/admission, the candidate capability manifest/profile,
and the profile-owned selected-slice parity/barrier budget. CUDA lifecycle and
dynamics remain forbidden until their later rows are opened.
