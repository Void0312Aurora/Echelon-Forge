# CUDA-Resident Second Backend Program

Language versions:

- English canonical: `cuda_resident_backend_program_20260729.md`
- Chinese companion: [cuda_resident_backend_program_20260729.zh.md](cuda_resident_backend_program_20260729.zh.md)

- Document type: frozen execution plan
- Lifecycle: maintained
- Owner: exact-runtime / CUDA-resident backend workline
- Branch: `codex/cuda-resident-backend`
- Baseline: `origin/main` at `395e02b7dfeaa87baedb2611ec503d14ab137ce3`
- Date: `2026-07-29`

Status: **RB0 through RB10 are accepted after independent review. RB11 is the
current closure candidate; no promotion is authorized.** Branch-local evidence and
the sole next authorization are recorded in the
[iteration log](cuda_resident_backend_iteration_log_20260729.md).

## 1. Decision

The target is a second runtime backend with device-native state and scheduling.
It is not a CUDA version of Flecs and it is not a sequence of Flecs systems
replaced one by one by CUDA helpers.

The maintained shape is:

```text
RuntimeFacade
    -> IWorldBatchBackend
         -> FlecsCpuBackend
         -> CudaResidentBackend
```

The CPU backend remains the maintained comparison reference. When the CUDA
backend is selected for an admitted execution window, the CUDA backend owns its
declared operational shards for that window. Flecs must not be stepped or
reconstructed after every internal stage. Cross-backend exchange occurs only
through canonical setup, input, barrier, snapshot, observation, and diagnostics
contracts.

## 2. Why A Separate Backend Is Required

The current implementation does not expose a real backend seam:

- `RuntimeFacade` directly owns `std::unique_ptr<WorldBatchRuntime>`.
- `WorldBatchRuntime::step_batch()` advances a vector of Flecs-backed
  `SimulationKernel` worlds.
- `RuntimeBatchConfig` currently carries only world count and worker count.
- GPU observation, visual, shaping, and broadphase paths are helpers with
  host-side request construction and host-visible results.
- `resident_state.unmaintained_candidate` exists as a blocked profile, not as
  an executable backend.
- `DeviceResidentOutputDescriptor` is an additive export-only contract and does
  not authorize state ownership.

A one-for-one migration would preserve the entity/component-oriented materialization
boundary, broad live ranges, feature branching, repeated launches, and host/device
coordination. A separate backend permits backend-specific SoA storage, capability
queues, phase-local intermediate layouts, and kernel specialization.

The architecture change is necessary but not sufficient. Register pressure is
still a kernel property and must be controlled through live-range reduction,
hot/cold separation, specialization, and measured phase boundaries.

## 3. Authority And Relationship To Existing Plans

This plan:

- consumes the accepted WP19 shard, barrier, descriptor, and fail-closed
  vocabulary;
- treats the archived exact-GPU and resident-state plans as provenance only;
- preserves `cpu_exact.reference` as the maintained comparison backend;
- does not change current capability flags during RB0;
- does not reopen the helper-first exact-GPU implementation as the migration
  foundation;
- uses the exact-stage inventory as a semantic/parity ledger, not as the CUDA
  launch graph.

This document is the single candidate execution freeze for the new workline.
Research notes, archived plans, and checklists remain supporting evidence and
do not independently authorize implementation scope.

Primary evidence inputs:

- [RuntimeFacade ownership](../../../src/runtime/facade/runtime_facade.h)
- [RuntimeFacade construction](../../../src/runtime/facade/runtime_facade.cpp)
- [WorldBatchRuntime stepping](../../../src/core/engine/world_batch_runtime.cpp)
- [runtime batch config fields](../../../src/runtime/facade/detail/runtime_batch_config.inc)
- [backend profile contracts](../../../src/runtime/contracts/backend_profile_contracts.h)
- [resident-state parity budget](../../../src/runtime/contracts/parity_budget_contracts.h)
- [exact-stage semantic inventory](../../../src/core/engine/exact_stage_inventory.cpp)
- [`src/gpu` boundary](../../../src/gpu/README.md)
- [WP19 resident-state sync/shard contract](../../task/simulation_architecture/archive/wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.md)
- [WP19 device-output contract](../../task/simulation_architecture/archive/wp19_cuda_resident_state_alignment/wp19_device_resident_output_contract_cluster_20260521.md)
- [archived exact-GPU rearchitecture provenance](../archive/exact_runtime/gpu_exact_world_step_rearchitecture_plan.md)
- [archived resident-state implementation provenance](../archive/exact_runtime/gpu_resident_state_implementation_plan.md)

## 4. Program Objective

Build an explicitly selected `CudaResidentBackend` that can execute a bounded
air-execution rollout slice from canonical setup and input packets, retain its
operational state on device across steps, and export canonical snapshots or
device observation views at declared barriers while remaining comparable with
the Flecs CPU reference.

The first promotable slice is deliberately narrow:

- fixed-step air/execution worlds;
- fixed platform-capability manifest;
- action/command, flight control, airframe dynamics, instruments, observation,
  reward, and termination surfaces required by the selected fixture;
- no undeclared dynamic entity families;
- no implicit CPU fallback inside an admitted CUDA window.

## 5. Non-Goals

- CUDA-enabling Flecs or exposing Flecs component storage to device code.
- Porting each exact-stage system to a matching kernel.
- A monolithic `world_step_kernel`.
- Full air, naval, ground, cooperative, sensor, EW, damage, and logistics
  coverage in the first slice.
- Promoting exact-GPU, resident-state, shadow, or device-observation support
  before their profile gates pass.
- Deleting or rewriting archived GPU evidence.
- Adding PyTorch, Python, or policy-library dependencies to the C++ backend.
- Optimizing isolated kernel duration while end-to-end rollout remains slower.

## 6. Backend Contract

The internal backend SPI must be expressed in facade-owned contract types. Its
minimum semantic operations are:

```cpp
class IWorldBatchBackend {
  public:
    virtual BackendCapabilities capabilities() const noexcept = 0;
    virtual void configure(const BackendConfig&) = 0;
    virtual void reset(const BatchWorldSetupRequest&) = 0;
    virtual void inject(const BackendInputBatch&) = 0;
    virtual BackendWindowResult advance(const BackendWindowRequest&) = 0;
    virtual BackendSnapshotResult export_snapshot(const BackendExportRequest&) = 0;
    virtual DeviceObservationResult export_device_observation(
        const DeviceObservationRequest&) = 0;
    virtual BackendDiagnostics diagnostics() const = 0;
    virtual ~IWorldBatchBackend() = default;
};
```

The names above are design placeholders until RB1 completes the current caller
and DTO census. RB1 must not add an unused parallel interface. It must introduce
the SPI and route the existing CPU path through `FlecsCpuBackend` in the same
iteration.

Rules:

1. `RuntimeFacade` remains the public owner; backend implementation types stay
   internal.
2. No Flecs handle, component pointer, CUDA pointer, or backend-specific state
   layout crosses the public facade DTO boundary.
3. Backend selection is explicit and fail-closed.
4. Unsupported scenario capabilities reject admission before setup or stepping.
5. An admitted CUDA window cannot silently call Flecs for missing stages.
6. Host reconstruction is an explicit export operation, not a side effect of
   every step.

## 7. CUDA State Model

`CudaResidentBackend` owns a `CudaWorldStore` with backend-private layouts:

- world offsets and stable `(entity_id, generation)` identity;
- active/free lists and barrier-scoped lifecycle queues;
- hot SoA shards for kinematics, controls, forces, propulsion, fuel, weapons,
  and observation state;
- cold/read-only tables for platform configuration, aerodynamic data, sensor
  configuration, and mission constants;
- capability-specific active queues for aircraft, missiles, sensors, comm, EW,
  and later domain families;
- CSR or bounded ring-buffer storage for contacts, tracks, commands, and events;
- counter-based RNG addressed by seed, world, tick, entity, and event identity;
- per-shard versions, source snapshot identity, and barrier identity.

Static/configuration shards upload at setup or version change. Dynamic shards
remain resident across `advance()` calls. Dirty host input is transferred only
at `input_injection`; host-visible reconstruction occurs only at declared
`window_commit` or `export` barriers.

## 8. Execution Graph And Register-Pressure Rules

The exact-stage inventory defines semantic ordering and comparison points. It
does not determine CUDA kernel count. The initial execution graph has four
phase families:

| Phase | Scope | Materialized boundary |
| --- | --- | --- |
| A | action decoding, command delivery, lag, control preparation | compact control SoA |
| B | aero state, propulsion, forces, rotational and translational integration | committed dynamics SoA |
| C | spatial indexing, guidance, sensors, comm, fuze/effects | sparse candidate/event queues |
| D | instruments and their learner-facing projection, observation, reward, termination, optional visual output | host snapshot or device consumer view |

Phase C is outside the first vertical slice except for the minimum explicitly
required by its fixture.

Every CUDA implementation iteration must record:

- `ptxas` registers per thread;
- spill stores and loads;
- achieved occupancy and resident blocks/warps;
- local/global/shared-memory traffic;
- branch and warp divergence;
- launch count, H2D, D2H, and synchronization time;
- end-to-end rollout time.

No universal register cap is frozen in advance. Each kernel declares a target
occupancy shape from measured work. `--maxrregcount` or `__launch_bounds__` may
be used only when an A/B result shows that reduced residency cost does not move
work into material local-memory spills.

Required design controls:

- split hot and cold fields;
- specialize by admitted capability family rather than branch over all Flecs
  component combinations;
- keep diagnostics outputs out of the training fast path;
- materialize compact phase-local intermediates where this shortens live ranges;
- fuse only when removed memory traffic exceeds lost occupancy or added spills;
- use stable entity/event ordering and counter-based RNG so launch scheduling
  cannot become simulation truth.

## 9. Ownership, Sync, And Parity

The accepted WP19 vocabulary remains authoritative:

- `input_injection`: canonical setup/action/command deltas become visible;
- `stage_publish`: backend-local and not host-maintained by default;
- `window_commit`: declared backend shards become a committed backend snapshot;
- `export`: canonical host snapshot or device output descriptor becomes
  consumable;
- counterfactual/replay barriers remain comparison/export surfaces, not implicit
  ownership transfers.

The profile-owned selected-slice budget frozen by RB2 must carry the complete
barrier mapping below:

| Barrier | Candidate-backend rule |
| --- | --- |
| `input_injection` | Canonical setup/action/command deltas enter the admitted backend window. |
| `stage_publish` | Backend-local diagnostic checkpoint only; it cannot independently satisfy maintained parity. |
| `partial_sync_commit` | Used only for a profile-declared reconstructed shard; absent such a declaration, no partial host truth exists. |
| `window_commit` | Declared resident shards receive committed backend snapshot and shard versions. |
| `export` | Host snapshot or device output becomes consumable with source snapshot, provenance, and lifetime metadata. |

For the CUDA candidate, CPU is the reference implementation, not a concurrent
writer. Parity runs execute the same frozen input trace independently through
both backends and compare at declared barriers. They do not synchronize Flecs
components after every CUDA stage.

Numeric state is exact by default. Any tolerated field family requires an
explicit comparator and threshold in the profile-owned parity budget. Event
order, snapshot identity, barrier identity, schema, provenance, termination,
and capability admission remain exact.

RB2 owns the candidate profile id, selected-slice field inventory, comparator
and tolerance declarations, and the complete barrier set. RB4 implements those
barriers. RB5-RB7 produce parity evidence against that already-frozen budget.
RB8 only adds replay/shadow consumers of the budget; it must not define the
budget after implementation has begun.

## 10. Iteration Protocol

The workline follows the existing repository discipline:

```text
analyze -> freeze write set/non-goals -> implement -> focused validation
        -> independent read-only review -> repair/re-review
        -> one commit -> landing-ledger registration
```

Branch-local labels `RB<n>` identify candidate work packages. They are not
central `I<n>` acceptance claims. When a reviewed commit is landed, it receives
the next available central iteration row in
`docs/plan/repository_consolidation/README.md`. This avoids allocating stale
global numbers while the branch evolves independently.

Each RB iteration must:

- start from a clean worktree and refresh `origin/main` ancestry;
- inventory callers and current behavior before edits;
- freeze an exact write set and explicit non-goals;
- produce one independently reviewable commit;
- keep CUDA-disabled builds and the CPU default unchanged unless that iteration
  explicitly owns a reviewed promotion;
- record focused commands, results, diff statistics, remaining gaps, reviewer
  revision, findings, and verdict;
- stop without commit if a blocking finding or required validation remains.

## 11. Candidate Iteration Queue

| ID | Scope | Exit gate |
| --- | --- | --- |
| RB0 | Freeze this plan, current code census, authority links, worktree and branch. Documentation only. | Bilingual companions, indexes, applicable strict registry record, links, `git diff --check`, independent review. |
| RB1 | Introduce the internal backend SPI and used `FlecsCpuBackend`; route the maintained CPU path through it without public behavior or ABI drift. | `RuntimeFacade::runtime_` ownership cuts over to the interface/CPU adapter; move/sizeof tripwires are updated; CUDA-off build, CPU focused parity and architecture guards pass; no backend-specific or unused parallel owner remains in the facade. |
| RB2 | Add explicit backend request/admission, capability-manifest contract, candidate profile id, and profile-owned selected-slice parity budget. CUDA selection remains rejected unless a compiled experimental backend and supported manifest are present. | Default bytes unchanged; missing/unsupported profiles fail closed; selected fields, exact/default comparators, any explicit tolerances, and `input_injection`/`stage_publish`/`partial_sync_commit`/`window_commit`/`export` mapping are frozen; no support-flag promotion. |
| RB3 | Add `CudaResidentBackend` lifecycle shell and `CudaWorldStore` allocation/versioning, with CUDA-off stubs. No simulation dynamics. | Configure/reset/teardown tests; no global singleton cache; sanitizer or ownership checks where available. |
| RB4 | Implement setup/reset, input injection, device clock, shard versions, and the RB2-frozen partial-sync/window/export barrier behavior plus explicit snapshot reconstruction for the minimal fixture. | Fixed-seed reset and identity parity against the RB2 budget; zero hidden Flecs step/fallback; complete barrier/provenance checks. |
| RB5 | Implement Phase A for the bounded air-execution manifest. | Stage-local CPU-reference parity against the RB2 budget; register/spill report; unsupported control features reject admission. |
| RB6 | Implement Phase B airframe dynamics for the same manifest; instruments remain a Phase D output projection. | Fixed replay parity against the RB2 budget at declared comparison points; no per-stage host synchronization; resource report. |
| RB7 | Implement Phase D instruments, observation, reward, termination, and lifetime-safe device observation export. | Host export parity against the RB2 budget; direct device consumer smoke; no snapshot D2D ownership copy disguised as zero-copy. |
| RB8 | Add independent CPU/GPU replay and shadow-comparison harnesses that consume the RB2 parity budget without using shadow results to mutate either backend. | Mismatch localization, deterministic rerun, quarantine behavior, and complete selected-slice budget consumption. |
| RB9 | Establish production-shaped performance and break-even evidence. No semantic expansion. | Worlds `1/4/16/64/256`, P50/P95, transfers, launches, register/spill/occupancy, memory, end-to-end collect metrics. |
| RB10 | Decide continuation: optimize measured phase boundaries, admit a bounded spatial interaction slice, or hold the backend. | End-to-end gain beyond noise at declared eligible batches; no small-batch default regression; owner decision recorded. |
| RB11 | Optional promotion/closure only after all earlier gates. | Maintained profile review, reconstruction/export contract, support projection, rollback path, full validation and independent acceptance. |

RB5-RB7 must not be merged into one oversized iteration. RB10 cannot broaden
into sensor/comm work merely because an isolated broadphase kernel is fast.

## 12. Performance Matrix And Gates

The minimum common matrix is:

- worlds: `1`, `4`, `16`, `64`, `256`;
- fixed bounded air-execution fixture and seeds;
- CPU reference, CUDA resident, and explicit CPU/GPU comparison modes;
- cold first step and warmed steady state;
- host snapshot export disabled/enabled;
- device observation consumer disabled/enabled.

Required measurements:

- full facade/window advance;
- complete rollout collection and, when available, learner consumption;
- P50 and P95 latency;
- H2D, D2H, synchronization, and launch counts;
- per-kernel register, spill, occupancy, divergence, and memory metrics;
- allocated and peak device memory;
- parity and determinism outcomes.

Candidate performance acceptance for RB10 requires a statistically clear
end-to-end gain at declared eligible production batches. A provisional target
is at least 15% faster than the CPU reference at the selected production batch,
with a measured backend-selection threshold for smaller batches. This number is
a program gate, not a performance forecast, and may be re-frozen only from RB9
evidence.

Kernel-only speedup, helper-only timing, or a result that still performs hidden
host reconstruction does not satisfy the gate.

## 13. Stop And Hold Conditions

The workline stops or remains candidate if any of the following persists:

- the backend seam becomes a second public facade or duplicates contract DTOs;
- CUDA admission silently falls back to Flecs within an execution window;
- parity requires per-stage host write-back;
- unsupported capabilities execute through branch-heavy generic kernels instead
  of failing closed;
- register reduction is obtained only by material spill traffic that removes
  the end-to-end gain;
- the backend is faster only in isolated kernels but not in rollout;
- snapshot, barrier, event order, provenance, or lifetime cannot be reconstructed;
- required independent review or validation is unavailable.

In those cases the branch and evidence remain research candidates. Current
maintained CPU behavior and capability flags remain unchanged.

## 14. RB0 Frozen Write Set

RB0 may modify only:

- this English/Chinese plan pair;
- `docs/plan/exact_runtime/README.md` and `.zh.md`;
- `docs/plan/README.md` and `.zh.md`;
- the selective strict bilingual registry record for `plan/README`. The
  `exact_runtime` subtree is outside the current strict registry scope, so its
  two changed pairs are validated directly rather than added by a full-tree
  registry rewrite.

RB0 must not modify C++, CUDA, Python, CMake, tests, runtime profiles, capability
flags, examples, archived plans, or the central accepted iteration ledger.
