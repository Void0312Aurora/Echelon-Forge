# GPU Exact World-Step Migration Plan

Status: experimental archive retained for follow-on reference.

Maintained-mainline note (2026-04-16):
CPU exact world stepping plus selected GPU helper paths is the maintained
execution baseline. This document remains as research provenance for the
retired exact-step GPU promotion line.

Related:

- [gpu_execution_mainline_integration_checklist.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/gpu_execution_mainline_integration_checklist.md)
- [gpu_execution_runtime_research_and_design.md](/home/void0312/Workshop/CMO/docs/plan/archive/gpu_execution_runtime_research_and_design.md)
- [gpu_exact_world_step_contract.h](/home/void0312/Workshop/CMO/src/gpu/gpu_exact_world_step_contract.h)

## Goal

Migrate the exact execution hot path away from the current CPU-only
`SimulationKernel::step()` loop and toward an optional GPU exact-step backend.

This is not a helper-kernel plan. It is the main-path migration plan.

## Why The Previous Path Plateaued

The maintained Phase 0-4 work improved helper runtimes and learner handoff, but
the exact world step still remains on CPU:

- [world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)
  `step_batch()` still calls `worlds_[i]->step()`
- [world_batch_vec_env.py](/home/void0312/Workshop/CMO/python/rl/world_batch_vec_env.py)
  still performs host-side action handoff, state readback, reward assembly, and
  info packaging
- the maintained `p5` config still defaults to `world_batch_threads=1`

As a result, the project is still bounded by CPU exact stepping and host control
flow, not by visual or observation helpers.

## Migration Boundary

The target is exact ECS-state parity, not packed-flight approximation.

Allowed basis:

- [gpu_exact_world_step_contract.h](/home/void0312/Workshop/CMO/src/gpu/gpu_exact_world_step_contract.h)
- exact state extraction/apply in
  [world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)

Explicitly not sufficient:

- [gpu_world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/gpu/gpu_world_batch_runtime.cpp)
  packed-flight stepping
- helper-only GPU paths for visual, observation, shaping, or interaction

## Phase Structure

### Phase 0: Freeze The Exact-State Contract

Objective:

- make exact state extraction, apply, packing, and parity signatures testable
- define the first reproducible parity harness before any new GPU kernel work

Frozen tasks:

- [x] Keep [gpu_exact_world_step_contract.h](/home/void0312/Workshop/CMO/src/gpu/gpu_exact_world_step_contract.h)
  as the canonical state boundary for the first exact-step migration pass.
- [x] Expose packed exact-state extract/apply helpers to Python.
- [x] Add apply-signature helpers that intentionally ignore `world_time_s`,
  `entity_id`, and `environment_sample`, the derived fields not restored by the
  current public apply path.
- [x] Add regression tests that prove live-world exact state can be extracted,
  stepped away, and restored to the same apply-signature.
- [x] Fix `time_step_s` restore so the contract does not silently drop that
  field on apply.

Exit criteria:

- exact state contract is scriptable from Python tests
- packed exact state can round-trip through a live `WorldBatchRuntime`
- any future GPU backend can be validated against the same apply-signature

### Phase 1: Build A CPU Shadow Parity Runner

Objective:

- create a reference harness that runs CPU exact step and records per-step
  apply-signatures, observations, and terminal metadata

Tasks:

- add a diagnostic runner that:
  - extracts exact state at step 0
  - records apply-signatures per step
  - records learner-facing outputs per step
- support fixed-seed replay batches for `p5`-style single-aircraft worlds
- define tolerated drift rules:
  - exact-state apply-signature: zero mismatch
  - learner-facing floats: explicit tolerance table only where unavoidable

Exit criteria:

- one command can produce a CPU parity trace for a fixed seed
- that trace is archived and reusable against future GPU step implementations

### Phase 2: GPU Exact-Step Prototype For The Current Single-Aircraft Contract

Objective:

- implement a first GPU exact-step kernel for the state covered by
  `ExactWorldStepStateV1`

Tasks:

- convert `ExactWorldStepStateV1` into GPU-friendly SoA buffers
- add exact environment sampling inputs needed by the current state contract
- implement single-step GPU kernels for:
  - command/control lag state update
  - force/aero intermediate update
  - translational/rotational integration
  - instrument/ground derived state refresh
- keep this in shadow mode only

Exit criteria:

- GPU kernel can advance the exact-state contract for one step
- CPU vs GPU shadow comparison runs on fixed seeds without mainline write-back

### Phase 3: Optional WorldBatchRuntime Exact GPU Backend

Objective:

- add an optional backend under `WorldBatchRuntime` that can execute exact GPU
  world steps for eligible worlds

Tasks:

- add backend selection to `WorldBatchRuntime`
- keep CPU fallback trivial
- support mixed-mode validation:
  - CPU mainline with GPU shadow
  - GPU mainline with CPU audit

Exit criteria:

- `WorldBatchRuntime` can run exact GPU step behind an explicit runtime switch
- fallback to CPU exact step remains one config change

### Phase 4: Training-Path Reattachment

Objective:

- reconnect `p5` training to the exact GPU world-step backend after parity is
  demonstrated

Tasks:

- reduce host action/reward/info handoff around the new backend
- re-evaluate `batch_observation_backend=gpu_host` only after exact step stays
  on device long enough to matter
- measure end-to-end `collect + train` again

Exit criteria:

- maintained `p5` shows material rollout-side gains, not only learner-side wins

Current follow-on note:

- the active Phase E runtime-switch follow-on is now tracked in
  [gpu_exact_world_step_rearchitecture_plan.md](/home/void0312/Workshop/CMO/docs/plan/archive/gpu_exact_world_step_rearchitecture_plan.md)
- as of `2026-03-27`, that experimental `WorldBatchRuntime.step_batch()`
  backend holds parity on the deterministic cached-session fixture, keeps warm
  write-back at `0.0 ms`, removes in-step D2H materialization, and now also
  drives `chain_command_lane_ms` to `0.0` on the benchmark-style quiescent
  path while reusing a smaller resident `pilot + world_time` projection for the
  covered replay; the latest no-missile resident replay follow-on now also
  skips the guidance counter, kernel launch, and counter-readback overhead
  entirely on no-missile rows; the newest quiescent sync+replay fusion then
  collapses the covered aircraft-only runtime step to one H2D copy plus one
  replay launch and lifts the warm runtime-step speedup sweep on
  `world_count=1,4,16` to roughly `0.194x / 0.197x / 0.583x`; the subsequent
  stream-based resident follow-on now also replaces the remaining
  `cudaDeviceSynchronize()` hot-path calls with a dedicated cache stream plus
  reusable timing events; the latest raw resident-projection follow-on now also
  feeds that `pilot + world_time` batch through a reusable pinned host buffer
  and lets the no-missile graph keep a fixed memcpy source instead of updating
  node params every step. The newest resident clean-path follow-on then lets
  quiescent/no-missile steps advance `world_time_s` directly inside the device
  carrier so the covered hot path can skip projection H2D entirely, and the
  next pass wraps that device-only replay in its own cached CUDA graph to claw
  back most of the launch overhead from the first direct-kernel version. A
  stable rerun `world_count=1,4,16` runtime-step matrix now lands around
  `0.111 ms / 0.096 ms / 0.099 ms` warm runtime-step time with warm chain
  totals near `0.078 ms / 0.079 ms / 0.082 ms`, keeps warm write-back,
  `chain_command_lane_ms`, and `chain_host_to_device_ms` at `0.0`, and
  measures approximate warm runtime-step speedups of `0.121x / 0.193x /
  0.466x`; this keeps the projection path effectively exhausted on the covered
  runtime-step experiment, but the backend still does not clear CPU-vs-GPU
  promotion gates
- it remains explicitly experimental and is still blocked on CPU-vs-GPU
  slowdown rather than correctness or write-back burden

## Known Gaps At Plan Start

- `world_time_s` is extractable but not fully restorable through the current
  public kernel API
- exact-state extraction/apply existed in C++ but had no Python parity harness
- packed-flight GPU stepping is not a substitute for exact ECS parity

## First-Phase Implementation Status

Landed with this plan:

- packed exact-state export/import helpers in the Python bindings
- exact apply-signature helpers in
  [gpu_exact_world_step_contract.cpp](/home/void0312/Workshop/CMO/src/gpu/gpu_exact_world_step_contract.cpp)
- `time_step_s` restore in
  [world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)
- optional-component presence restore in
  [world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)
- exact-state roundtrip regression in
  [test_gpu_runtime_bindings.py](/home/void0312/Workshop/CMO/tests/test_gpu_runtime_bindings.py)

Phase 1 foundation now also landed:

- CPU parity trace runner in
  [generate_exact_world_step_parity_trace.py](/home/void0312/Workshop/CMO/tools/diagnostics/generate_exact_world_step_parity_trace.py)
- fixed-seed parity trace regression evidence, now treated as a historical
  archived diagnostic reference rather than a maintained `tests/diagnostics`
  entry

Current Phase 1 note:

- the archived replay blob is a raw packed state payload intended for replay,
  not a canonical byte-stable serialization; the stable comparison surface is
  the per-step apply-signature and learner-facing trace records

Phase 2 initial foundation now landed:

- exact prototype SoA/runtime scaffolding in
  [gpu_exact_world_step_runtime.h](/home/void0312/Workshop/CMO/src/gpu/gpu_exact_world_step_runtime.h),
  [gpu_exact_world_step_runtime.cpp](/home/void0312/Workshop/CMO/src/gpu/gpu_exact_world_step_runtime.cpp), and
  [gpu_exact_world_step_runtime_cuda.cu](/home/void0312/Workshop/CMO/src/gpu/gpu_exact_world_step_runtime_cuda.cu)
- packed Python binding for CPU/GPU shadow stepping in
  [python_module.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/python_module.cpp)
- live exact packed-state CPU/GPU tolerance compare and write-back regression in
  [test_gpu_runtime_bindings.py](/home/void0312/Workshop/CMO/tests/test_gpu_runtime_bindings.py)
- fixed-seed shadow replay comparator in
  [compare_exact_world_step_shadow_trace.py](/home/void0312/Workshop/CMO/tools/diagnostics/compare_exact_world_step_shadow_trace.py)
  with historical regression evidence retained as an archived diagnostic
  reference rather than a maintained `tests/diagnostics` entry
- hidden-dynamics debug export for packed/live exact states in
  [python_module.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/python_module.cpp),
  now threaded through both parity-trace generation and shadow-trace replay so
  the comparator can see internal `environment_sample`, `angular_velocity`,
  `force_accumulator`, `aero_state`, `control_law_state`, and `egi` surfaces

Current Phase 2 note:

- this prototype is still a shadow backend with a reduced exact-step update
  surface; it advances command-lag, translational, fuel/mass, and
  instrument/ground refresh through a GPU-friendly SoA, but it is not yet a
  full replacement for `SimulationKernel::step()`
- the fixed-seed comparator now gives two separate answers:
  - whether CPU-reference and GPU-shadow implementations of the prototype agree
    on the same replay blob
  - how far that reduced prototype drifts from the archived exact CPU trace

Current Phase 2 findings from the fresh `8`-step `11,17` replay trace:

- CPU-reference and GPU-shadow replay surfaces now agree to within `0.0` on the
  comparator's learner-facing float surface, and the CPU/GPU replay
  apply-signatures also match step-for-step after deterministic canonicalization
  of the shared SoA outputs. The Phase 2 shadow backend is no longer hiding a
  CPU-vs-GPU hash split.
- the reduced prototype is still materially behind exact CPU stepping, but the
  current drift headline is now materially lower than the last stable Phase 2
  checkpoint:
  - worst absolute drift on the fresh `8`-step `11,17` replay trace is now
    `34.27`, down from the prior `59.82` and far below the first Phase 2 cut
    at `1557.23`
  - total learner-facing mismatches are still roughly flat at `694`; this pass
    improved the dominant angular/aero headline without yet collapsing the long
    tail of smaller mismatches
- the biggest wins in this pass came from:
  - mission-priority target resolution instead of defaulting to legacy
    `MovementCommand`
  - explicit refresh of instrument command bugs from `MissionCommand`
  - propulsion-based instrument fuel flow instead of reusing the fuel-system
    burn-rate proxy
  - navigation/EGI refresh for `lat/lon`, ground-track, and uncertainty surfaces
- the newest improvement in this pass came from moving the prototype off the
  old "attitude follows velocity" shortcut:
  - `ExactWorldStepPrototypeSoA` now carries angular velocity, geometry
    references, force-torque surfaces, and derived G-load state
  - the shadow backend now runs a minimal `control + aero + rotational`
    integration update on both CPU and CUDA before refreshing instruments
  - this was enough to pull `beta/aoa/p-rate` much closer to the exact trace
    without reintroducing CPU-vs-GPU signature drift
- the dominant remaining drift is no longer in command or navigation surfaces.
  The current worst gap is in angular/aero-like derived outputs such as
  `instrument[0].p_deg_s`, `beta_deg`, `aoa_deg`, and related load/rate fields.
- an attempted pass that inferred angular rates and G-load directly from
  transform/velocity deltas regressed the trace; that approach was rolled back
  and should not be reused without a closer match to the actual physics-system
  sign conventions.
- a later attempt to add a small heading-error bank deadband also regressed the
  replay trace (`34.27 -> 48.77`) and was rolled back. Keep the current Phase 2
  control law on the last stable no-deadband variant unless a replacement is
  validated against the shadow trace.
- the parity harness now records hidden dynamics as well as learner-facing
  truth/instrument/terminal surfaces. On the fresh `8`-step `11,17` replay:
  - CPU-reference and GPU-shadow still agree to within `0.0` on the expanded
    record surface and keep step-for-step apply-signature parity
  - exact CPU drift looks much larger on the expanded surface because the
    comparator can now see internal state that the earlier learner-facing trace
    hid
- after carrying `AeroState` and `ControlLawState` into the SoA, clearing
  prototype torques per step, and writing the rebuilt torque surface back to
  `ForceAccumulator`, the expanded replay headline improved materially:
  `420135.99 -> 230343.75`
- after fixing route-mode lateral reference to use current track rather than
  current heading, and making `ControlLawState` appear dynamically in the
  prototype once the filtered-stick path is active, the expanded replay
  headline improved again:
  `230343.75 -> 168266.05`
- the dominant hidden-surface gap is still inside `force_accumulator`, but the
  worst path moved again and is now
  `hidden_dynamics[0].force_accumulator.torque_pitch_nm`
- total mismatches on the expanded replay record also finally moved down a bit:
  `1184 -> 1168`
- after porting the control-law stick filter to the exact CPU low-pass formula
  (`alpha = dt / (tau + dt)` rather than the prototype's prior exponential
  smoothing), the expanded replay stayed in the same headline range while
  trimming a few more long-tail mismatches:
  - headline max drift moved slightly from `168266.05` to `169855.68`
  - total mismatches moved from `1168` to `1160`
  - CPU/GPU shadow parity remained exact (`max_abs_diff = 0.0`,
    `all_apply_signatures_match = true`)
- two related follow-on experiments were validated and rolled back:
  - routing mission-command targets directly into the reduced prototype's motion
    / guidance path regressed the expanded replay to `198563.23`
  - forcing the shadow backend's `ForceAccumulator` to mirror the live ECS
    `ControlSystem -> ForceClear` ordering more literally regressed the replay
    much harder (`310169.85` headline) before the reduced prototype had proper
    linear-force and aero-refresh parity
- keep the exact control-law low-pass port, but keep the rest of the reduced
  prototype on the last stable torque/motion variant until the missing linear
  force surfaces are modeled; otherwise small local semantic fixes can make the
  full replay drift worse rather than better
- a first pass that threaded thrust plus reconstructed `fx/fy/fz` through the
  reduced prototype did not hold up on the full hidden replay and was rolled
  back:
  - early-step `force_accumulator.f*` mismatches improved locally
  - but late-step drift regressed materially and the headline moved from
    `169855.68` to `230207.55`
  - the prototype should stay on the prior torque-only shadow semantics until
    translational force evolution and ground-contact parity are modeled
- this is not a regression of the learner-facing `34.27` headline; it is the
  first time the trace has exposed the prototype's internal force/torque and
  aero-cache divergence directly

Immediate next implementation targets:

- stop treating force/torque state as opaque: the fresh hidden-dynamics trace
  shows that `force_accumulator` is now the dominant unresolved exact gap
- stop leaving linear force surfaces empty: the prototype still writes
  `force_accumulator.fx/fy/fz = 0` while exact CPU already carries gravity,
  thrust, aero, and ground-contact forces
- improve the prototype's exact force/torque and aerodynamic cache refresh
  before returning to secondary command/nav cleanup
- target the remaining high-impact fields first:
  `force_accumulator` torques and linear forces, `dynamic_pressure`, `beta`,
  `aoa`, `p/q/r`, and load-factor outputs
- focus first on the missing ground-contact/force-system semantics and the
  remaining pitch-torque parity path before adding more secondary derived
  outputs; the current replay still diverges most strongly in
  `force_accumulator.torque_pitch_nm`, `force_accumulator.torque_roll_nm`, and
  the downstream angular/aero surfaces
- add dynamic environment sampling inputs once the current derived-state drift is
  better localized, so terrain/wind refresh does not remain a hidden constant

## Guardrails

- do not route maintained `p5` through packed-flight GPU stepping as a hidden
  replacement
- do not claim exact migration success from helper-kernel speedups
- do not promote any GPU exact-step backend until the parity harness is green
