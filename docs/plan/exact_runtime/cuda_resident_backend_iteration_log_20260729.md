# CUDA-Resident Backend Branch Iteration Log

Language versions:

- English canonical: `cuda_resident_backend_iteration_log_20260729.md`
- Chinese companion: [cuda_resident_backend_iteration_log_20260729.zh.md](cuda_resident_backend_iteration_log_20260729.zh.md)

- Document type: branch-local iteration and review ledger
- Lifecycle: maintained while `codex/cuda-resident-backend` is active
- Program authority: [cuda_resident_backend_program_20260729.md](cuda_resident_backend_program_20260729.md)
- Baseline: `395e02b7dfeaa87baedb2611ec503d14ab137ce3`

Status: **RB0 through RB6 are accepted. RB7 is the only currently authorized
implementation iteration. RB8-RB11 remain dependency-gated.**

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

## RB3 - Instance-Owned CUDA Lifecycle Shell

### Frozen write set

- a separate `ef_cuda_resident_backend` target and target-private CUDA compile
  switch;
- the instance-owned `CudaWorldStore` allocation/reset/teardown owner and its
  CUDA-off stub;
- the `CudaResidentBackend` lifecycle shell implementing the internal backend
  SPI while rejecting every semantic operation;
- the CUDA lifecycle metadata allocator, exact test readback/fault seam,
  focused C++ target, architecture tests, and this bilingual status update.

### Non-goals

- no facade takeover, bounded-manifest advertisement, support-flag promotion,
  or implicit Flecs/CPU fallback;
- no content load, setup, input injection, evaluation, advance, export,
  simulation dynamics, kernel graph, or physics state;
- no reuse of older GPU-helper global caches and no claim that lifecycle
  metadata is a maintained runtime backend.

### Result

- `CudaWorldStore` has one non-copyable/non-movable PIMPL owner per backend
  instance. CUDA-off configure/reset fail closed without changing capacity or
  generation.
- CUDA-on lifecycle metadata uses one guarded device allocation containing two
  epochs. Reset first constructs a complete host epoch, copies it once into the
  inactive slot, and switches the active slot only after a successful copy.
  Seed and reset-generation metadata therefore cannot become observably mixed.
- Allocation/release/reset faults are injected per store, not globally. Exact
  device readback proves explicit seeds, empty-seed zeroing, generation values,
  successful reconfiguration, and preservation of the old active allocation
  after failed allocation, reset-copy, or release paths.
- Release clears an owner only after synchronization and `cudaFree` succeed.
  Failed active release preserves the old owner; a replacement that also
  cannot be released remains reachable through `pending_cleanup` for later
  configure/teardown/destructor retry.
- Allocation and reset generations fail closed before `uint64_t` wraparound.
  The backend's required `configuration() noexcept` reads only the scalar
  capacity accessor and cannot copy the diagnostic error string.
- All semantic backend operations remain explicit `logic_error` rejections,
  the compatibility port remains null, and `RuntimeFacade` continues to expose
  no compiled experimental backend or supported manifest.

### Validation

- CUDA-off Release builds of `ef_test`, `ef_py`, and the focused lifecycle
  target: pass. Focused lifecycle: `2/2`, `32` assertions; full `ef_test`:
  `155/155`, `19,329` assertions.
- Related admission/lifecycle Python selection: `9 passed`.
- CUDA-on MSVC/NVCC focused target, which compiles every RB3 production source:
  `2/2`, `95` assertions. Compute Sanitizer memcheck reports `0 errors` and
  `0 bytes leaked in 0 allocations`.
- Changed C++ `clang-format --dry-run -Werror`, changed Python `ruff`, and
  `git diff --check`: pass.
- A CUDA-on build of the full `ef_test` graph remains blocked by pre-existing
  MSVC portability debt in `ef_core` (`__builtin_ctz`, `M_PI`, and related
  existing diagnostics). The focused target deliberately excludes that graph
  while compiling the complete RB3 target; this is an environment/baseline
  limit, not evidence that the full CUDA-on suite passed.

### Independent review and repair history

1. Initial review blocked ignored `cudaFree` results/owner loss, a two-copy
   reset that could expose new seeds with an old generation, host-only tests
   that could not detect no-op device writes, an allocating path under
   `configuration() noexcept`, and generation wraparound.
2. The allocator was replaced by the single-allocation double-buffer design;
   release ownership became status-aware and retryable; exact device readback,
   per-instance allocation/reset-copy/release faults, and exhaustion tests were
   added. This structurally removed the second-`cudaMalloc` leak window rather
   than merely masking it.
3. `/root/rb3_lifecycle_review` independently reran the repaired candidate and
   approved staged raw hash `7ce020d5e055302d3ac38c85e85e42ab2af37f0c`
   (stable patch-id `1c6bc2c884077796b2dc97341d10f999fcb98b7c`) with
   zero blocking or non-blocking findings.

Verdict: **accepted for one RB3 commit**. The next authorized work is RB4 only:
setup/reset, input injection, device clock and shard versions, the RB2-frozen
partial-sync/window/export barriers, and explicit minimal-fixture snapshot
reconstruction. RB4 must retain zero hidden Flecs stepping/fallback and may not
implement RB5-RB7 dynamics or advertise the bounded manifest early.

## RB4 - Fixed-Air Resident State And Barrier Shell

### Frozen write set

- the shared fixed-air fixture identity/schema contract consumed independently
  by the CPU reference test and the CUDA candidate;
- backend-private double-slot SoA state for identity, selected pilot controls,
  kinematics, clock, snapshot/barrier identity, and shard versions;
- setup/reset, selected input injection, stage publish, disabled partial sync,
  window commit, and explicit minimal snapshot reconstruction;
- focused CUDA-on/CUDA-off tests, the CPU reference identity test, architecture
  guards, kernel resource reporting, CMake wiring, and this bilingual status
  update.

### Non-goals

- no Phase A/B/D dynamics, instruments, observation, reward, termination, event
  production, learner device view, facade takeover, or manifest/support
  advertisement;
- no Flecs stepping, `WorldBatchRuntime` call, CPU fallback, per-stage host
  write-back, or claim that the current partial export satisfies the complete
  RB2 comparison/host-truth contract;
- no zero-copy claim: full-slot D2D staging is the explicit transactional RB4
  baseline and remains an optimization target for later measured iterations.

### Result

- Setup creates the same baseline-locked `(world_index, entity_id, generation)`
  identity as an independent `FlecsCpuBackend` reference without either test
  calling the other backend. Repeated setup increments entity generation.
- One device allocation owns two lifecycle epochs and two packed SoA state
  slots. Every reset, input, stage, and window mutation is constructed in an
  inactive slot. Each operation changes the active slot only after its
  applicable copies succeed; input, stage, and window additionally require the
  narrow barrier kernel, synchronization, and overflow status readback to
  succeed.
- The input barrier commits selected pilot controls. Stage publish advances only
  barrier identity. Partial sync remains disabled. Window commit advances the
  device clock and only versions actually materialized in RB4; unimplemented
  dynamics/episode/output shards remain version `0`.
- Explicit export reconstructs typed clock, snapshot identity, lineage,
  kinematics, and an exact field-set envelope. It reports both the RB2-required
  visible shards and the smaller materialized RB4 set, so contract satisfaction,
  comparison eligibility, and host truth remain false until later phases fill
  the complete contract. Pilot controls do not leak through export.
- State readback is private to export/testing and checks host setup state before
  any D2H. Configure-only, reset-only, and failed-setup states therefore fail
  closed instead of reading uninitialized device storage; zero capacity yields
  an explicit empty snapshot.
- `RuntimeFacade` still advertises no compiled experimental backend, supported
  manifest, resident-state support, exact-GPU support, or device observation
  view.

### Validation and resource evidence

- CUDA-on MSVC/NVCC focused target: `4/4`, `233` assertions. Compute Sanitizer
  memcheck: `0 errors`, `0 bytes leaked in 0 allocations`.
- `ptxas` for `apply_barrier_kernel`: `30` registers/thread, `0` spill stores,
  `0` spill loads, `0`-byte stack frame, `0` barriers. Runtime API reports 128
  threads/block, 12 active blocks and 48 active warps per SM, with theoretical
  occupancy `1.0` on the local RTX 3090. These are resource/theoretical values,
  not achieved-counter measurements.
- Nsight Systems on the focused, readback-heavy fault-test workload recorded 3
  barrier kernels totaling `6,176 ns` (median `1,984 ns`), 4 D2D copies totaling
  `5,409 ns`, 18 H2D copies totaling `11,170 ns`, and 38 D2H copies totaling
  `59,522 ns`. Cold allocation and diagnostic exports dominate this test trace;
  it is not production performance evidence.
- Nsight Compute counter collection was blocked by `ERR_NVGPUCTRPERM`; achieved
  occupancy, divergence, and memory-counter claims are therefore deliberately
  deferred rather than inferred.
- CUDA-off full `ef_test`: `158/158`, `19,346` assertions; CUDA-off focused
  target: `4/4`, `35` assertions. Related admission/lifecycle architecture
  selection: `7 passed`. Changed C++ clang-format, changed Python ruff, and
  `git diff --check`: pass.
- The focused CUDA-on target compiles every RB4 production source. The full
  CUDA-on `ef_test` graph remains outside this claim because of the pre-existing
  MSVC portability debt already recorded under RB3.

### Independent review and repair history

1. `/root/rb4_state_review` first blocked versions assigned to empty
   dynamics/episode shards and export evidence that mislabeled the complete RB2
   required set as already materialized. Required/materialized evidence was
   separated, empty shard versions remain zero, and incomplete host truth is
   explicit.
2. Re-review blocked D2H from uninitialized post-configure slots and an export
   envelope that omitted `seed`, `reset_generation`, and `source_barrier_id`.
   Host setup gating plus configure/reset/failed-setup rejection tests closed the
   first path; exact field-set equality closed the second.
3. The reviewer approved implementation raw hash
   `a65387063425f2fe867b2eaee9898acfbe29716d` (stable patch-id
   `f2deb2a3ade9a6ddf810631ff8024a0d39aa59e9`) with zero blocking and zero
   non-blocking findings.

Verdict: **accepted for one RB4 commit**. The next authorized work is RB5 only:
implement Phase A for the same bounded fixed-air slice, produce stage-local
CPU-reference parity and a fresh register/spill report, and continue rejecting
unsupported control features. RB5 must not absorb Phase B airframe dynamics or
Phase D output projection and must not advertise the bounded manifest early.

## RB5 - Phase A Direct-Pilot Preparation

### Frozen write set

- a shared direct-pilot Phase A fixture contract with frozen inputs, expected
  filtered outputs, deadband, rudder sign, and CPU `ecs_ftime_t` precision rule;
- backend-private prepared-control SoA fields, validity/manual-takeover flags,
  phase versions, device kernel resource query, and the Phase A stage transaction;
- backend active-assignment canonicalization matching the maintained CPU command
  surface, while keeping raw controls separate from prepared controls;
- `phase_a_ready` freshness gating between input, stage publish, and window commit;
- CUDA-on/CUDA-off CPU and CUDA tests, unsupported radar/weapon rejection,
  architecture guards, CMake wiring, and this bilingual ledger update.

### Non-goals

- no Phase B airframe dynamics, propulsion, forces, surfaces/actuators,
  instruments, observation, reward, termination, events, mission commands, or
  learner/device projection;
- no Flecs stepping from the CUDA candidate, CPU fallback, per-stage host
  write-back, facade takeover, capability-manifest promotion, or support-flag
  changes;
- no performance claim from this stage-local trace and no `--maxrregcount` or
  launch-bound tuning before end-to-end evidence.

### Result

- `prepare_phase_a_controls_kernel` consumes the existing `[pitch, roll, rudder,
  throttle, brake]` raw SoA and writes a separate semantic `[roll, pitch, yaw,
  yaw_cmd]` prepared SoA. Manual takeover uses the maintained strict `> 0.05`
  primary-axis deadband; rudder is negated; the first-order filter uses `tau=.15 s`
  and explicitly mirrors Flecs' current `float` time scalar boundary.
- A submitted pilot assignment canonicalizes `active=true`, matching
  `SimulationKernel::set_pilot_action`; exact-deadband and canonicalized payload
  cases are covered by the shared trace. Prepared values carry validity,
  takeover, and monotonic phase-version metadata without entering the RB2 export
  shard contract.
- Stage publish clones the active slot, runs one specialized Phase A kernel,
  checks device status/synchronization, then applies the existing stage barrier
  before swapping active state. Overflow and non-finite results fail closed.
  Failed copies, kernel status, or barrier commits leave the previous active slot
  visible. A window commit is rejected until a successful Phase A publish; a
  successful window consumes that freshness token.
- Radar, weapon, and other undeclared controls remain rejected. The facade still
  advertises no experimental backend, supported manifest, or fallback path.

### Validation and resource evidence

- CUDA-off Release full `ef_test`: `159/159` test cases and `19,374`
  assertions; RB5 CPU oracle: `1/1`, `28` assertions.
- CUDA-on MSVC/NVCC focused target: `5/5` test cases and `276` assertions.
  `sm_86` `ptxas` reports `apply_barrier_kernel` at `30` registers/thread and
  `prepare_phase_a_controls_kernel` at `34`, both with zero spill stores,
  zero spill loads, and a zero-byte stack frame. Runtime API reports 128
  threads/block, 12 active blocks, 48 active warps, and theoretical occupancy
  `1.0` for Phase A on the local RTX 3090; these are theoretical values, not
  achieved counters.
- Final RB5 Compute Sanitizer memcheck: `0 errors`, `0 bytes leaked in 0
  allocations`. Related architecture selection: `10 passed`; changed C++
  clang-format, changed Python ruff, and `git diff --check`: pass. The Python
  selection was run against the local `ef_py` artifact in the isolated
  CUDA-off build directory.
- The focused CUDA-on target is the supported compilation evidence. The full
  CUDA-on `ef_test` graph remains outside the pass claim because of the
  pre-existing MSVC portability debt recorded under RB3.

### Independent review and repair history

1. The first long-running review attempt was stopped without modifying the
   worktree; a fresh independent read-only review was then run to avoid treating
   an unreturned process as approval.
2. `/root/rb5_review_final` independently inspected the uncommitted candidate and
   returned `APPROVE` with zero blocking findings. It explicitly verified SoA
   order, rudder sign, deadband, float time-step parity, active canonicalization,
   inactive-slot transaction, freshness gate, fail-closed guards, test
   separation, and no manifest/fallback promotion.
3. The reviewer noted one non-blocking documentation opportunity: after a failed
   new input, retaining the old successful active stage is intentional
   transactional behavior. This ledger records that behavior explicitly.

The reviewed code/test staged raw hash is
`fc23a4d34173c0de2b70bc14b70b44caf4b7cf8d` (stable patch-id
`6a8101f6cbaaa4ea63bbf83b1006682a07295722`). The single commit identity is
recorded by the enclosing branch history.

Verdict: **accepted for one RB5 commit**. The next authorized work is RB6 only:
implement the bounded Phase B airframe-dynamics slice without absorbing Phase D
projection or changing facade support claims.

## RB6 — bounded Phase B airframe dynamics (accepted after independent review)

### Frozen write set and non-goals

The candidate write set is limited to the resident-store device layout/API,
the CUDA resident backend's private RB6 export identity, a new Phase-B fixture
contract, focused CPU/CUDA tests, CMake test wiring, architecture guards, and
this bilingual ledger. It does not change the public capability manifest,
facade support projection, CPU backend, or any Phase-D instrument/observation/
reward/termination owner.

The admitted envelope is an airborne fixed-step slice: `Aircraft`, altitude
`100..10000 m`, speed `50..350 m/s`, bounded lateral/vertical velocity and
attitude, standard-atmosphere/no-environment-assignment, attached-flow
`|alpha| <= 14 deg`, no ground/damage/fuel/mass update, and no dynamic entity
families. Post-stall tables, terrain/ground effect, wind assignments, mission
autopilot, instruments, and learner projection remain fail-closed or out of
scope.

### Implementation

- `CudaWorldDynamicsState` is a separate resident SoA shard carrying angular
  rates, realized actuator positions, engine spool/current thrust, cached
  aerodynamic values, and gear extension. Setup initializes the cold F-16
  fixture constants from a dedicated Phase-B contract; the state is never
  reconstructed through Flecs.
- A window clones the active slot and launches three kernels without a host
  synchronization between them: control/aero-state/propulsion plus gravity and
  thrust; aerodynamic force/moment accumulation; and rotational plus
  leapfrog integration. One status synchronization precedes the declared
  window barrier, and failed inactive-slot work leaves the prior committed
  state visible.
- The export reconstruction now carries dynamics, uses an explicit v2 schema
  and RB6 provenance, and increments the frozen `dynamics` and `episode`
  shard versions at `window_commit`. Phase-D shards are still not falsely
  marked complete.

### Validation and resource evidence

- CUDA-off Release full `ef_test`: `160/160` test cases, `19,456`
  assertions. The independent RB6 CPU oracle runs the exact maintained stage
  sequence and pins both worlds against the RB2 kinematics comparator.
- CUDA-on MSVC/NVCC focused target: `6/6` test cases, `353` assertions,
  including inactive-slot transaction retry, export dynamics, and bounded
  setup rejection. Compute Sanitizer memcheck: `0 errors`.
- `sm_86` `ptxas`: barrier `30`, Phase A `34`, Phase-B control/propulsion
  `66`, Phase-B aerodynamics `66`, and Phase-B integration `64`
  registers/thread; all report zero spill stores/loads. Runtime resource
  queries report theoretical occupancy approximately `0.5833`, `0.5833`, and
  `0.6667` for the three Phase-B kernels at 128 threads/block. The kernels
  retain a 40-byte stack frame reported by ptxas/runtime; no `--maxrregcount`
  or launch-bound constraint is used.
- Focused architecture/ruff/style checks: `13` architecture tests passed,
  Ruff passed, and `git diff --check` passed. The full CUDA-on `ef_test` graph
  remains outside the claim because of the pre-existing MSVC portability debt
  recorded under RB3.

### Independent review and repair history

1. `/root/rb6_phase_b_review` independently inspected the candidate and returned
   `APPROVE` with no blocking finding. It verified the exact write set,
   CPU/CUDA test separation, the three-launch/no-intermediate-host-sync rule,
   envelope guards, shard/export semantics, and the register/resource evidence.
2. The reviewer identified two non-blocking documentation drifts: the CUDA
   comment said two launches, and the focused CMake comment stopped at RB5.
   Both comments were repaired without changing behavior.
3. The same reviewer performed a read-only follow-up and returned `APPROVE`
   again. The follow-up rechecked launch order, zero intermediate host sync,
   the focused architecture guards, and the exact write set; no new finding was
   raised.

The reviewed code/test staged raw hash is
`2b07c57f67b7d868ff20b130d8761c0ee2a6bfef` (stable patch-id
`e86033b1a304cb1c4c0d37b762ba0275338b025e`). The single commit identity is
recorded by the enclosing branch history.

Verdict: **accepted for one RB6 commit**. After that commit, RB7 is the only
authorized work: the bounded Phase D instruments/observation/reward/termination
projection and lifetime-safe device observation export. No replay harness or
performance claim is opened by this verdict.
