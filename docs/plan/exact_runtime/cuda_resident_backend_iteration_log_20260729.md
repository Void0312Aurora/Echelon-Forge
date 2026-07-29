# CUDA-Resident Backend Branch Iteration Log

Language versions:

- English canonical: `cuda_resident_backend_iteration_log_20260729.md`
- Chinese companion: [cuda_resident_backend_iteration_log_20260729.zh.md](cuda_resident_backend_iteration_log_20260729.zh.md)

- Document type: branch-local iteration and review ledger
- Lifecycle: maintained while `codex/cuda-resident-backend` is active
- Program authority: [cuda_resident_backend_program_20260729.md](cuda_resident_backend_program_20260729.md)
- Baseline: `395e02b7dfeaa87baedb2611ec503d14ab137ce3`

Status: **RB0 through RB2 are accepted. RB3 is the only currently authorized
implementation iteration. RB4-RB11 remain dependency-gated.**

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

## RB2 - Candidate Admission And Frozen Parity Contract

### Frozen write set

- explicit backend request/admission DTOs and the facade preflight;
- the bounded fixed-step air-execution capability manifest;
- the existing `resident_state.unmaintained_candidate` profile-owned parity
  budget, selected-slice field descriptors, and barrier rules;
- typed future clock, snapshot, event-order, and export-envelope contracts;
- Python bindings, build registration, C++/Python contract tests, and this
  program/ledger status update.

### Non-goals

- no CUDA backend object, device allocation, store, kernel, or dynamics;
- no active-backend replacement, implicit CPU fallback, or
  `RuntimeBatchConfig` expansion;
- no manifest advertisement by a compiled backend and no public support-flag,
  maintained-profile, or capability promotion;
- no empirical accuracy or performance claim from the preimplementation
  comparator thresholds.

### Result

- CPU reference selection remains the maintained default. Candidate selection
  requires explicit opt-in, exact profile/budget/manifest ownership, a trusted
  compiled-backend signal, and exact supported-manifest advertisement.
  `RuntimeFacade` supplies neither experimental availability nor a supported
  manifest, so candidate selection remains fail-closed.
- The bounded manifest has canonical required, supported, and forbidden feature
  vectors. The known manifest must equal the full canonical object, so deleting
  `communications` from the forbidden set and adding it to supported features
  is rejected.
- The parity budget freezes 11 families and 93 complete descriptors: field
  path, surface owner, current/future status, value kind, and shard. Current DTO
  members and future typed-contract members are compile-time probed.
- `observation.id`, event order, snapshot identity, termination identity, and
  export-envelope identity use exact comparison. Approximate comparators accept
  floating fields only. Kinematics uses `1e-9` absolute / `1e-12` relative;
  instrument, observation, and reward numeric families use `1e-8` / `1e-10`.
  These are frozen parity gates for later measurement, not validated model-error
  bounds.
- Snapshot identity explicitly maps `world_id`, `global_version`, `barrier_id`,
  `barrier_sequence`, `shard_versions`, and typed `lineage`.
- `input_injection`, `stage_publish`, disabled `partial_sync_commit`,
  `window_commit`, and `export` are exact canonical rules. Event and export
  envelope fields are visible/comparable only at `export`; host truth exists
  only there.

### Validation

- CUDA-off Release builds of `ef_test` and `ef_py`: pass.
- `ef_test`: `153/153` test cases and `19,297` assertions passed.
- RB2 C++ selection: `5/5`, `127` assertions; RB2 Python selection: `7 passed`.
- Changed C++ `clang-format --dry-run -Werror`, changed Python `ruff`, and
  `git diff --check`: pass.
- A wider facade selection reported `41 passed, 6 failed`: one unchanged stale
  source-text expectation and five snippet compiles whose existing test helper
  hard-codes a missing worktree-local `build-local-win` Flecs path. Independent
  review reproduced and classified them as outside the RB2 change surface.

### Independent review and repair history

1. Initial review blocked an approximate comparator containing
   `observation.id`, premature event/export visibility, incomplete barrier
   semantics, and string-only selected fields. The contract was replaced by
   typed descriptors, exact canonical barriers, member probes, and mutation
   tests.
2. Re-review found three reproducible false greens: optional manifest expansion,
   incomplete exact snapshot identity, and tests that did not compare full
   descriptor objects. Canonical manifest equality, the complete typed snapshot
   identity, and an independent 93-object expected inventory closed them.
3. `/root/rb2_contract_review` independently reran the repaired candidate and
   approved staged raw hash `c9355e69644a81262df23ebe47e802225b6371c3`
   (stable patch-id `8e3531b8fd071579ac6ea431c18d93f540001e6b`) with
   zero blockers.

Verdict: **accepted for one RB2 commit**. The next authorized work is RB3 only:
an instance-owned `CudaWorldStore`, `CudaResidentBackend` lifecycle shell, and
CUDA-off stubs. RB3 must not advertise the bounded manifest, implement
simulation dynamics, or reuse the global singleton caches in older GPU helper
experiments.
