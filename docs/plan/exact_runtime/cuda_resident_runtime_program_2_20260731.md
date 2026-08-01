# CUDA-Resident Runtime Program 2

Language versions:

- English canonical: `cuda_resident_runtime_program_2_20260731.md`
- Chinese companion: [cuda_resident_runtime_program_2_20260731.zh.md](cuda_resident_runtime_program_2_20260731.zh.md)
- Size policy: [cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)
- Iteration log: [cuda_resident_runtime_program_2_iteration_log_20260731.md](cuda_resident_runtime_program_2_iteration_log_20260731.md)

- Document type: new explicit continuation program after RB11 closure
- Branch: `codex/cuda-resident-runtime-program-2`
- Parent closure: `935926e83b18187c79a6e0be2ca010276c1a6fc4`
- Maintained baseline: `395e02b7dfeaa87baedb2611ec503d14ab137ce3`
- Date: `2026-07-31`

Status: **CR2-2a is independently approved and committed as bf695071;
CR2-2p is independently approved and committed as dee02146; CR2-2b is the
active full-window candidate. The previous RB0-RB11 program remains
closed without promotion. This program may either produce promotion-grade
evidence or close again; it does not reopen maintained support by itself.**

## 1. Objective and boundary

The objective is to turn the branch-local CUDA-resident experiment into a
measurable, facade-equivalent candidate, while preserving the architectural
decision that this is a second backend with its own device-native state and
scheduling. It is not a sequence of Flecs systems rewritten as CUDA helpers.

The program must prove, in order:

1. the resident implementation can be decomposed into reviewable modules;
2. CPU and CUDA can execute the same declared full-window contract through
   equivalent invocation surfaces;
3. learner/device consumers can consume the result without hidden host
   validation readback;
4. selected-slice parity and reset identity are releasable rather than
   quarantined diagnostics;
5. register, spill, occupancy, memory, and divergence evidence exists for the
   actual end-to-end window; and
6. any performance decision includes small batches and rollout cost, not only
   an isolated kernel or a private phase sequence.

Until every gate is accepted, the maintained CPU backend remains the default,
all resident support flags remain false, and RuntimeFacade does not select this
branch. A successful CR2 gate authorizes a separate promotion proposal; it
does not silently merge or publish one.

## 2. Size governance (mandatory)

The physical line count is measured from tracked file bytes after checkout,
using `splitlines()`; formatting or line-compression tricks do not waive the
rule. The policy is machine-readable and guarded by
`test_cuda_resident_program_2_size_policy.py`.

| Scope | Soft target | Review band | Hard limit |
| --- | ---: | ---: | ---: |
| `.cpp`, `.cc`, `.cu`, `.cxx` implementation module | 700 lines | 800 lines | 1000 lines |
| `.h`, `.hpp`, `.cuh` contract/header module | 600 lines | 800 lines | 1000 lines |
| CUDA-resident test/probe module | 700 lines | 800 lines | 1000 lines |

The 1000-line value is a hard ceiling for CR2-owned modules, not a target.
Crossing the soft target requires an explicit split decision in the iteration
log; crossing the review band blocks unrelated semantic growth. A module that
already exceeds the hard limit can exist only as a named, expiring migration
exception and must be the first structural work item.

CR2-0 recorded one hard-limit migration exception for the 2528-line
`cuda_world_store_cuda.cu`. CR2-1 removes that file from the current tree and
does not carry the exception forward. The current CUDA implementation inventory
is:

| Module | Role | Lines |
| --- | --- | ---: |
| `cuda_world_store_cuda_internal.cuh` | shared layout, allocation, and wrapper contract | 291 |
| `cuda_world_store_cuda_math.cuh` | shared device math helpers | 139 |
| `cuda_world_store_cuda_storage.cu` | allocation/layout, metadata, and fixture storage | 547 |
| `cuda_world_store_cuda_barrier.cu` | barrier kernel and resource query | 264 |
| `cuda_world_store_cuda_phase_a.cu` | Phase A kernel and publication | 204 |
| `cuda_world_store_cuda_phase_b.cu` | Phase B kernels and launch wrappers | 497 |
| `cuda_world_store_cuda_phase_d.cu` | Phase D kernels and launch wrappers | 231 |
| `cuda_world_store_cuda_observation.cu` | diagnostic plus CR2-3 lease pack and consumer | 441 |
| `cuda_world_store_cuda_state_readback.cu` | host state readback | 271 |
| `cuda_world_store_cuda_window.cu` | private full-window orchestration | 69 |

All current CR2-owned CUDA modules are below the 700-line soft target. The old
monolith remains a historical baseline only; it is not a source or an active
exception.

CR2-3 keeps the host/device lease boundary split into small owners:
`cuda_resident_device_consumer.cpp/.h` (246/49 lines),
`cuda_world_store_device_lease.cpp` (66), and
`cuda_world_store_host_internal.h` (33). The existing host owners remain below
the soft target at 661 lines for `cuda_world_store.cpp` and 636 for
`cuda_resident_backend.cpp`; no size exception is added.

CR2-4a removes the replay-test watch item by splitting its zero-semantic-change
support into `test_cuda_resident_replay_projection.cpp` (611 lines),
`test_cuda_resident_replay_support.cpp` (175), and
`test_cuda_resident_replay_support.h` (58); the assertion/test owner is now
`test_cuda_resident_replay.cpp` (139). No current CR2 watch item remains.

Generated/vendor files and historical documents are outside the module line
limit only when an explicit manifest entry records their provenance. New
tracked evidence, reports, or generated artifacts have a 512 KiB soft limit
and a 1 MiB hard limit; repeated raw traces must remain outside the tracked
write set. CR2 evidence/report/generated files must use one of the declared
`cuda_resident_runtime_program_2_` or `cuda_resident_cr2_` prefixes; the guard
scans both tracked files and on-disk candidate files before staging. No
exception may be used to hide semantic implementation growth.

## 3. Engineering invariants

- The backend owns resident state during an admitted window; no stage-by-stage
  Flecs write-back and no CPU fallback inside a CUDA window.
- Public DTOs and RuntimeFacade contracts are reused at the boundary; private
  SoA types may remain device-owned behind explicit export/consumer leases.
- Every iteration has one bounded semantic scope, an exact write set, focused
  validation, an independent reviewer, and one commit.
- Runtime/support/ABI changes remain fail-closed until the final decision gate.
- `--maxrregcount` is not a substitute for a layout or scheduling fix. Any
  tuning must follow measured resource evidence and preserve the frozen trace.
- Existing RB9 evidence is provenance, not a promotion result; CR2 must rerun
  the missing gates rather than relabeling the old private threshold.

## 4. Iteration queue

| ID | Scope | Exit gate |
| --- | --- | --- |
| CR2-0 | Freeze this program, size policy, exception manifest, and architecture guard. | Completed in `2f34fac6`; policy parses and the reviewed write set is committed. |
| CR2-1 | Split `cuda_world_store_cuda.cu` by layout/allocation, Phase A, Phase B, Phase D, barriers, and device API orchestration without semantic change. | Independently approved by `/root/cr2_split_review` and committed as `db7e6ad4`; no CR2-owned module exceeds 1000 lines; focused C++/CUDA lifecycle, replay, parity, and architecture tests are green. |
| CR2-2a | Split the RB9 probe's lane-specific session into a private implementation module without changing its invocation surface, JSON schema, errors, or phase order. | Completed after independent approval in `bf695071`; probe/session modules are below the soft limit and historical evidence remains untouched. |
| CR2-2p | Unblock the real Flecs CPU lane on VS2022 with only the portable bit scan, intended global environment-model type, and MSVC core math-constant opt-in. | Real `FlecsCpuBackend` graph compiles; focused guard passes; independent review and a separate commit precede CR2-2b. |
| CR2-2b | Define one full-window trace and equivalent CPU/CUDA invocation surface, including setup, input, evaluation, advance, export, and error/barrier semantics. | Independently approved and committed as `607c1f33`; both real lanes consume the same trace through the declared surface. |
| CR2-3 | Add a real device consumer/learner-facing lease and remove hidden host validation from the measured consumer path. | Independently approved and committed as `7da41a2a`; explicit consumer smoke, ownership/lifetime/failure tests, deferred diagnostic readback, and CUDA-on/off validation pass; public support stays closed. |
| CR2-4a | Split the 919-line RB8 replay test into bounded support/projection/test owners without changing its oracle, quarantine, 93-field budget, or historical evidence. | Candidate write set keeps CUDA-on replay 3/3 and 47/47, CUDA-off 3/3 and 14/14, old failure semantics, CMake topology, and size policy equivalent; independent review and one commit required. |
| CR2-4b | Release selected-slice parity and deterministic reset identity from quarantine using real payload evidence and an explicit identity policy. | Identity policy is stable or explicitly excluded; every released field is real or explicitly normalized/excluded; frozen-budget replay passes at each declared barrier; public support remains closed. |
| CR2-5 | Collect ptxas/Nsight resource evidence for the full window: registers, spills, local/shared/global traffic, occupancy, divergence, and launch topology. | Counters are complete or a documented external blocker stops the gate; no tuning claim is made from incomplete counters. |
| CR2-6 | Run production-shaped world-count/mode matrix with rollout and small-batch measurements. | End-to-end benefit survives cold, warm, rollout, export, device-consumer, and small-batch cases; selection policy is evidence-backed. |
| CR2-7 | Make a separately reviewed promotion or closure decision. | Promotion requires a new explicit authorization and integration plan; otherwise record a second closure without changing maintained behavior. |

CR2-1 through CR2-6 may be repeated as narrowly scoped sub-iterations, but a
single commit may not combine structural decomposition, semantic expansion,
and performance tuning.

### CR2-2a boundary

CR2-2a is a structural-only migration. The executable remains the historical
RB9 probe: CPU and CUDA lane selection, mode matrix, private phase sequence,
JSON keys, trace signatures, unavailable reasons, and hold reasons are frozen.
Only the lane-specific ProbeSession storage/operation implementation moves to
cuda_resident_rb9_probe_session.cpp behind its small header. The CMake targets
compile that module in both lanes. No full-window SPI, public facade, support
flag, learner contract, or performance claim is introduced by this sub-iteration.

### CR2-2p boundary

CR2-2p is a prerequisite-only portability repair. It replaces one GCC-only bit
intrinsic, restores the intended global `IEnvironmentModel` type boundary, and
opts `ef_core` into its existing MSVC `M_PI` definitions. It has its own
architecture guard and commit `dee02146`; it does not contain the full-window
runner or any resident semantic change.

### CR2-2b boundary

CR2-2b is the first semantic full-window slice. The existing
`IWorldBatchBackend` is the only unified surface; a synchronous runner owns
`setup → inject → evaluate(empty) → advance(WorldBatch) → export`. CPU database
loading is external to the runner. CUDA `advance` performs stage publication
and commit behind an explicit three-state window machine, while the runner
reports only the common input/window/export barriers. Failures poison the
runner, and no retry, fallback, device pointer, learner lease, support flag, or
facade selection is added. Two real lane probes compile the same trace source,
and a separate comparator checks pure JSON surface/trace/operation equality.

### CR2-3 boundary

CR2-3 adds a private `cuda_resident.device_observation_lease.v1` input and a
real `cuda_resident.device_consumer_smoke.v1` kernel submission. A lease owns
its D2D-packed values, ids, ready event, device/default-stream identity,
element-stride tensor layout, and allocation/reset/committed-window/source
epoch. A receipt retains the input lease until its own event and output buffers
are released. Repeated submit and await are allowed; retained leases remain
readable across reset and backend destruction. The backend/store remain
single-owner runtime objects, while lease/receipt shared ownership is explicit.

The measured consumer path is acquire → submit → event await. It performs no
consumer-validation D2H and does not call `state_snapshot()` or read device
global versions. The diagnostic materialization performs exactly two D2H
copies only after the relevant cold, warm, or rollout timer is recorded. A
rollout defers all receipt diagnostics until its sample timer closes, so its
reported peak requested bytes include `rollout_windows` lease/output owners.
The general window still has its pre-existing five barrier-status D2H copies
(seven when host export is selected); the zero field therefore names the
device-consumer incremental path, not the whole window. `cudaMalloc` may
implicitly synchronize, and in-flight RAII release can wait on its event. Both
allocation risk and `device_consumer_release_outside_measured_path = true` are
reported explicitly; the issue is left for CR2-5 evidence/tuning rather than
hidden by a zero-sync claim.

Stable failures cover invalid request/lease/receipt, missing committed window,
epoch/device/stream/layout mismatch, lease allocation/pack/event recording,
consumer allocation/launch/event recording, wait, and diagnostic materialize.
The seam remains backend-private: no `IWorldBatchBackend`, RuntimeCapabilities,
admission, support flag, or RuntimeFacade selection change is part of CR2-3.
The historical RB9 evidence directory is not rewritten and no learner-update,
performance-promotion, or tuning conclusion is claimed.

## 5. Promotion and recovery boundary

Promotion is blocked if any of the following remains true: invocation surfaces
are not equivalent; a real learner update loop is unavailable; parity is only a
diagnostic; required counters are unavailable; world-1 or declared small-batch
cases regress without an explicit policy; or the implementation requires a
second public facade/duplicated DTO set.

The branch and worktree remain recoverable throughout CR2. No merge, push,
branch deletion, or worktree deletion is part of this program. A future
cleanup requires a fresh ref/worktree audit and explicit user authorization.
