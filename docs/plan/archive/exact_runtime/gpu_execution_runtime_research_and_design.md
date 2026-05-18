# GPU Execution Runtime Research And Design

Status: Closed on 2026-03-24.
Original Phase 0-4 scope is complete at the maintained project level. Any deeper
exact-ECS replacement work is out of scope for this plan.
Follow-on live checklist:
[gpu_execution_mainline_integration_checklist.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/gpu_execution_mainline_integration_checklist.md).

## Goal

Study a realism-preserving GPU path for the current simulator without treating
GPU-ization as a blind rewrite.

This document answers four questions:

- where the current architecture can be GPU-ized without changing simulation
  semantics
- which community patterns are actually relevant to this codebase
- whether current hardware makes a first GPU path realistic
- what the phased implementation plan should be

## Current Codebase Reality

The current execution path is still dominated by CPU-side orchestration and
readback, not by a monolithic physics kernel.

Relevant components:

- fixed-step kernel:
  [src/core/engine/simulation_kernel.cpp](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel.cpp)
- multi-world CPU batch adapter:
  [src/core/engine/world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)
- Python execution env:
  [gym_envs/universal_env.py](/home/void0312/Workshop/CMO/gym_envs/universal_env.py)
- compiled execution observation runtime:
  [src/core/mission/execution_observation_runtime.cpp](/home/void0312/Workshop/CMO/src/core/mission/execution_observation_runtime.cpp)
- compiled execution reward / termination runtime:
  [src/core/mission/execution_step_runtime.cpp](/home/void0312/Workshop/CMO/src/core/mission/execution_step_runtime.cpp)
- sensor narrow phase:
  [src/models/systems/default_sensor_model.cpp](/home/void0312/Workshop/CMO/src/models/systems/default_sensor_model.cpp)
- ARB visual raster:
  [src/systems/visual/visual_system.h](/home/void0312/Workshop/CMO/src/systems/visual/visual_system.h)

Important current constraints:

- `SimulationKernel::step()` is a fixed-step CPU ECS update.
- `WorldBatchRuntime` parallelizes across worlds, not inside one world.
- sensor and visual paths still contain global iteration patterns.
- `UniversalEnv` still reconstructs observations and training-facing products on
  the host side.
- the current build has no CUDA/HIP/SYCL target in
  [CMakeLists.txt](/home/void0312/Workshop/CMO/CMakeLists.txt).

## What GPU-ization Must Not Mean

GPU-ization here should not mean:

- replacing current physics semantics with PhysX / Isaac / another simulator
- moving history, logs, replay, and diagnostics wholesale into VRAM
- copying the current Python/Numpy readback path to the GPU and expecting speed
- porting Flecs entity iteration naively to kernels

Those routes would either break realism, waste VRAM, or preserve the same host
control-plane bottlenecks.

## Community Findings

The main transferable lessons are structural, not product-specific.

### 1. GPU-resident execution only pays when data stays on device

GROMACS documents a "GPU-resident" mode where supported step computation stays
on the GPU instead of repeatedly moving force and coordinate data back and
forth.

Source:

- https://manual.gromacs.org/documentation/2023/manual-2023.pdf

Takeaway for this repo:

- a useful GPU path must keep world state, temporary interaction buffers, and
  observation products resident on device for the hot portion of a step
- repeated device-to-host readback after each micro-stage will erase most gains

### 2. GPU ABM scales by sparse communication, not brute-force all-to-all

FLAME GPU exposes multiple communication strategies, including brute-force,
bucketed, and spatial messaging.

Sources:

- https://flamegpu.com/
- https://docs.flamegpu.com/guide/agent-functions/agent-communication.html

Takeaway for this repo:

- future large-world sensor / communication / visual candidate generation should
  use spatial or bucketed structures
- dense pairwise GPU matrices are the wrong target for campaign-scale growth

### 3. GPU kernels need data-oriented state, not host-oriented objects

Warp is explicitly designed for high-performance simulation kernels and spatial
computing with CPU/GPU execution from one code description.

Source:

- https://nvidia.github.io/warp/

Takeaway for this repo:

- the first prototype can use Warp-style kernels or native CUDA kernels as a
  proving ground
- but the underlying requirement is the same either way: structure-of-arrays
  state and compact buffers

### 4. RL-oriented GPU simulation works when sim tensors stay on device

Isaac-style environments show the practical pattern: simulation device is set
to CUDA, and the "GPU pipeline" is inferred from device placement rather than
through repeated host round-trips.

Source:

- https://docs.robotsfan.com/isaaclab_official/v2.2.1/source/migration/migrating_from_omniisaacgymenvs.html

Takeaway for this repo:

- if a GPU path is meant to accelerate training, the binding layer must expose
  device-resident tensors or a zero-copy handoff
- Numpy-returning bindings are acceptable for diagnostics, but they are not a
  serious training path

## Current Hardware Reality

Current local machine:

- CPU: dual-socket Xeon E5-2696 v4, `88` logical CPUs
- system RAM: `125 GiB`
- GPU: `RTX 3090`
- available VRAM during this survey: about `22.7 GiB`

This matters for design:

- RAM is abundant
- CPU parallelism exists but has already shown limited scaling for single-world
  exact execution
- one `24 GiB` GPU is enough for a meaningful prototype, but only if the GPU
  path is selective and VRAM-aware

## VRAM Budget Reality

VRAM is a constraint, but not the primary blocker for a first exact GPU path.
The blocker is architecture.

### Rough numbers from current observation layout

Current ARB visual tensor:

- `48 x 96 x 10`
- `float32`
- per frame size:
  `48 * 96 * 10 * 4 = 184,320 bytes`
  which is about `180 KiB`

Implications:

- `128` worlds, one current visual frame each:
  about `22.5 MiB`
- double-buffered:
  about `45 MiB`

That is not a VRAM problem.

### Where VRAM actually becomes expensive

The dangerous terms are:

- long history kept on device
- dense pairwise interaction buffers
- co-locating learner activations, optimizer state, and simulator state on one
  GPU

Example:

- `2048` steps
- `16` envs
- one ARB visual frame per step on device

That alone is about:

- `184,320 * 2048 * 16 ~= 6.03e9 bytes`
- about `5.6 GiB`

Conclusion:

- current state and current-frame products fit
- long histories do not belong in VRAM
- a serious GPU design must keep only the active simulation state and transient
  work buffers on device

## What Actually Deserves GPU-ization First

Not every hot path deserves the same priority.

### Tier 1: immediate candidates for the current single-aircraft pain point

These target the current `p5`-style exact training path directly.

1. ARB visual generation
2. execution observation packing
3. batched route / mission / reward shaping kernels
4. zero-copy device handoff to the learner

Why:

- they are numerically regular
- they are already partly separated from the core kernel
- they operate on dense arrays
- they are closer to current measured bottlenecks than full physics migration

### Tier 2: exact large-world candidates

These matter less for current single-aircraft `p5`, but are mandatory later.

1. sensor broadphase
2. visual object candidate generation
3. communication candidate generation
4. sparse interaction list construction

Why:

- they dominate scaling once entity counts become large
- they are where GPU algorithms can change complexity behavior

### Tier 3: full fixed-step world update

This is the hardest cut:

- force accumulation
- aero
- ground contact
- control
- integration

This is not phase 1.

Reason:

- the current implementation is Flecs/ECS-centric and branch-heavy
- a naive port would preserve complexity while adding rewrite cost
- current single-aircraft pain is not dominated by this layer alone

## Recommended Architecture

The recommended design is not "GPU kernel everywhere." It is a staged,
GPU-resident runtime that mirrors only the hot, array-friendly parts first.

### Core principle

The GPU path should be an optional backend under the existing runtime boundary,
not a replacement of scenario semantics.

Recommended backend structure:

- `SimulationKernel`
  remains the semantic authority
- `GpuExecutionRuntime`
  owns device-resident state mirrors and hot kernels
- `GpuObservationRuntime`
  builds training-facing tensors on device
- `GpuInteractionBroadphase`
  builds sparse candidate lists for sensor / visual / comm paths
- `GpuWorldBatchRuntime`
  steps many worlds or many agents in one launch domain

### Data layout requirement

GPU state must use structure-of-arrays buffers, not Flecs-like object access.

Minimum SoA groups:

- kinematics:
  position, velocity, attitude, angular rate
- controls:
  pilot action, mission command, command-lag state
- environment:
  wind, terrain parameters, runway parameters
- sensors:
  sensor config, contact offsets, candidate list offsets
- mission:
  waypoint targets, approach targets, shaping inputs

### Binding requirement

Training-facing GPUization is not worth doing unless the output can avoid
round-tripping through host Numpy.

Required future interface direction:

- device tensor export via DLPack or equivalent
- optional host readback only for diagnostics and contract testing

## Recommended Phased Plan

### Phase 0: benchmark and boundary setup

Deliverables:

- CMake option for optional CUDA build
- VRAM budget spreadsheet or script for current observation and world state
- microbenchmarks for:
  - ARB visual
  - observation packing
  - host/device transfer

Acceptance:

- exact numerical agreement for current-frame products
- no integration into training yet

### Phase 1: GPU visual runtime

Scope:

- port ARB terrain ray pass and object raster pass to device kernels
- batch multiple worlds / agents per launch
- keep output on device until learner or optional readback

Why phase 1:

- current ARB path is isolated enough
- arithmetic density is high
- current single-aircraft workloads can benefit immediately
- VRAM cost is modest for current-frame visuals

Acceptance:

- tensor shape and semantics equal to current CPU ARB output
- bounded numerical difference only from floating-point ordering

### Phase 2: GPU execution observation runtime

Scope:

- pack instruments, contacts, RWR, mission tensors on device
- fuse current compiled execution observation runtime with device buffers

Why:

- current `UniversalEnv` still pays for readback and observation assembly
- this is the cleanest bridge from exact sim to learner

Acceptance:

- same observation semantics as current CPU path
- measurable reduction in host-side step cost

### Phase 3: GPU interaction broadphase

Scope:

- spatial hash or uniform grid on device
- sparse candidate generation for sensor / visual / comm
- CPU or GPU narrow phase preserving existing formulas

Why:

- not the main current single-aircraft fix
- but the only credible path to later campaign-scale exact acceleration

Acceptance:

- exact candidate superset semantics
- no missed true interactions

### Phase 4: GPU batch world stepping

Scope:

- optional device-resident multi-world stepping path
- kernel fusion or CUDA graph capture for repeated launch topology

Why:

- only worth doing after state mirrors and observation paths exist

Acceptance:

- exact step-to-step equivalence against CPU reference for a fixed seed

## What Should Not Be Done First

Do not start with:

- a full GPU rewrite of `SimulationKernel`
- replacing the core sim with PhysX / Isaac
- dense `N x N` interaction matrices
- keeping replay/history in VRAM
- a same-card "full GPU learner + full GPU simulator + full history" design

Those are either realism risks or poor first cuts for this repo.

## Immediate Recommendation For This Repo

The first practical GPU study should be:

1. `GpuVisualRuntime`
2. `GpuExecutionObservationRuntime`
3. device/host transfer benchmark

Why this order:

- it attacks the current exact execution-layer path directly
- it keeps realism intact
- it avoids an early full-kernel rewrite
- it gives a clean answer on whether this repo can benefit from a GPU-resident
  training-facing path on the current `RTX 3090`

If those two stages do not move the wall-clock meaningfully, then a deeper GPU
rewrite is probably not justified for the current single-aircraft line.

If they do move the wall-clock, then the next serious investment should be the
interaction broadphase for future large-world scaling.

## First Empirical Result

The first phase-1 kernel slices have now been prototyped:

- scope:
  object-only ARB raster
- excluded:
  terrain pass
- tool:
  [gpu_visual_phase0_probe.cpp](/home/void0312/Workshop/CMO/src/tools/gpu_visual_phase0_probe.cpp)

### First cut: naive per-pixel x per-object kernel

Measured result on the local `RTX 3090`:

- `48x96`, `64` objects:
  CPU about `0.08 ms/frame`
  GPU about `0.82 ms/frame`
  about `0.10x` speedup
- `192x384`, `512` objects:
  CPU about `1.37 ms/frame`
  GPU about `17.63 ms/frame`
  about `0.08x` speedup

Output agreement stayed very tight:

- small-case `max_abs_diff` about `6e-8`
- large-case `max_abs_diff` about `9.5e-7`

Most important interpretation:

- the current failure is not mainly host/device transfer
- in the larger case, the CUDA timing split was roughly:
  - H2D about `0.20 ms`
  - kernel about `15.33 ms`
  - D2H about `0.62 ms`

That means the current naive per-pixel x per-object GPU raster is the wrong
algorithmic cut for this workload.

### Second cut: object-centric raster plus device-buffer reuse

The current experimental path was then upgraded to:

- object-centric depth competition
- resolve pass per pixel
- persistent device buffers instead of per-frame `cudaMalloc/cudaFree`

New measured result:

- `48x96`, `64` objects:
  CPU about `0.081 ms/frame`
  GPU about `0.175 ms/frame`
  about `0.46x`
- `192x384`, `512` objects:
  CPU about `1.35 ms/frame`
  GPU about `1.51 ms/frame`
  about `0.89x`

Interpretation:

- the revised algorithm removed most of the earlier waste
- it still does not beat the CPU reference on the current single-frame
  host-readback path
- but it is now close enough at larger workloads to justify the next cut

Updated implication:

- keep the GPU runtime scaffolding
- reject the original naive raster kernel shape
- keep the improved object-centric path as the new baseline
- the next GPU visual attempt should add many-world batching and/or tile/binning
- zero-copy device handoff matters more now, because the core raster path is no
  longer catastrophically slow

### Third cut: many-world batched object raster

The probe was then upgraded from single-world timing to real batched rendering:

- `--envs` now controls worlds per batch-frame, not just VRAM estimates
- the CUDA path accepts a vector of render requests and object lists
- requests and objects are flattened once per batch and rasterized in a single
  launch sequence
- the benchmark compares that CUDA path against a CPU batch adapter using the
  same object-only semantics

Measured result on the local `RTX 3090`:

- `48x96`, `64` objects, `envs=1`:
  CPU batch about `0.099 ms/world-frame`
  GPU batch about `0.166 ms/world-frame`
  about `0.60x`
- `48x96`, `64` objects, `envs=16`:
  CPU batch about `0.128 ms/world-frame`
  GPU batch about `0.100 ms/world-frame`
  about `1.29x`
- `48x96`, `64` objects, `envs=64`:
  CPU batch about `0.104 ms/world-frame`
  GPU batch about `0.084 ms/world-frame`
  about `1.25x`
- `192x384`, `512` objects, `envs=16`:
  CPU batch about `3.055 ms/world-frame`
  GPU batch about `2.512 ms/world-frame`
  about `1.22x`
- `192x384`, `512` objects, `envs=64`:
  CPU batch about `3.443 ms/world-frame`
  GPU batch about `2.724 ms/world-frame`
  about `1.26x`

Output agreement stayed tight:

- all measured cases kept `max_abs_diff` around `9.5e-7` or better

Most important interpretation:

- batching is what finally moved the GPU visual path past CPU parity on this
  workload
- small workloads still lose when the GPU is fed one world at a time
- once the launch carries enough worlds, the current object-only raster is
  already good enough to justify the GPU front-end
- this strengthens the case for the next two cuts:
  - device-resident handoff into the learner path
  - tile/binning to reduce global atomic pressure at higher object densities

### Fourth cut: device-resident output and no-readback path

The next slice added a device-resident batch path:

- the CUDA raster still runs the same object-only semantics
- output stays in the persistent device buffer
- the probe now reports both:
  - `GPU experiment path`: host-readback
  - `GPU device-resident path`: no output copy back to host

Measured result on the local `RTX 3090`:

- `48x96`, `64` objects, `envs=16`:
  - CPU batch about `0.102 ms/world-frame`
  - GPU host-readback about `0.100 ms/world-frame`
  - GPU device-resident about `0.0063 ms/world-frame`
  - about `16.1x` vs CPU
  - about `15.8x` uplift vs the host-readback GPU path
- `192x384`, `512` objects, `envs=16`:
  - CPU batch about `3.180 ms/world-frame`
  - GPU host-readback about `2.579 ms/world-frame`
  - GPU device-resident about `0.0338 ms/world-frame`
  - about `93.9x` vs CPU
  - about `76.2x` uplift vs the host-readback GPU path
- `192x384`, `512` objects, `envs=64`:
  - CPU batch about `3.681 ms/world-frame`
  - GPU host-readback about `2.741 ms/world-frame`
  - GPU device-resident about `0.0274 ms/world-frame`
  - about `134.6x` vs CPU
  - about `100.2x` uplift vs the host-readback GPU path

Most important interpretation:

- after batching, the next dominant cost is clearly host readback
- on the current path, the raster itself is already cheap enough that `D2H`
  becomes the main wall-clock tax
- if the downstream learner or observation consumer can read the tensor in
  place on device, the GPU visual path stops being a marginal win and becomes
  a fundamentally different throughput regime
- this does not yet prove full training speedup, because the current probe is
  still isolated from the learner and only benchmarks the visual slice
- it does prove that zero-copy device handoff is no longer optional; it is the
  main lever

### Fifth cut: terrain-aware batched visual raster

Phase 1 originally called for porting both the ARB terrain ray pass and the
object raster pass. That terrain slice is now prototyped too:

- scope:
  batched terrain depth/class pass plus object raster
- environment mode:
  legacy terrain snapshot extracted from
  [default_environment_model.cpp](/home/void0312/Workshop/CMO/src/models/environment/default_environment_model.cpp)
- tool:
  [gpu_visual_phase0_probe.cpp](/home/void0312/Workshop/CMO/src/tools/gpu_visual_phase0_probe.cpp)
  with `--terrain gpu`

Measured result on the local `RTX 3090`:

- `48x96`, `64` objects, `envs=16`, legacy terrain:
  - CPU batch about `0.3755 ms/world-frame`
  - GPU host-readback about `0.1326 ms/world-frame`
  - GPU device-resident about `0.0240 ms/world-frame`
  - about `2.83x` vs CPU on host-readback
  - about `15.65x` vs CPU on device-resident
- `192x384`, `512` objects, `envs=16`, legacy terrain:
  - CPU batch about `7.8267 ms/world-frame`
  - GPU host-readback about `2.7857 ms/world-frame`
  - GPU device-resident about `0.1773 ms/world-frame`
  - about `2.81x` vs CPU on host-readback
  - about `44.14x` vs CPU on device-resident
- `192x384`, `512` objects, `envs=64`, legacy terrain:
  - CPU batch about `7.8651 ms/world-frame`
  - GPU host-readback about `2.7975 ms/world-frame`
  - GPU device-resident about `0.1565 ms/world-frame`
  - about `2.81x` vs CPU on host-readback
  - about `50.27x` vs CPU on device-resident

Output agreement stayed tight:

- all measured cases kept `max_abs_diff` about `9.5e-7`
- mean absolute difference stayed effectively zero at probe precision

Most important interpretation:

- Phase 1 is no longer limited to object-only visuals; the terrain pass now
  has a real CUDA path
- terrain materially raises CPU cost, which makes the GPU path more valuable
  than the earlier object-only host-readback numbers suggested
- batching plus device residency remains the main story
- even with terrain enabled, the dominant avoidable cost on the GPU path is
  still host readback rather than kernel arithmetic

Implication for the roadmap:

- treat Phase 1 visual runtime as substantively complete at the probe level
- do not spend more time polishing visual-only kernels before connecting other
  Tier-1 GPU kernels
- keep the current visual runtime as the Phase 1 baseline while moving on to
  reward / mission / interaction kernels

### Phase 1 mainline integration: world-batch visual helper

Phase 1 is now also wired into the maintained Python/C++ front end:

- new binding:
  `ef_py.compute_world_batch_visual_observation_batch_numpy(...)`
- mainline adapter:
  [world_batch_vec_env.py](/home/void0312/Workshop/CMO/python/rl/world_batch_vec_env.py)
- new adapter setting:
  `batch_visual_backend=auto|legacy|compiled|gpu_host`

What changed:

- `WorldBatchVecEnv` no longer has to build visual observations one world at a
  time only
- when the helper is available, it can batch visual generation across selected
  worlds
- if terrain snapshots differ across worlds, the helper falls back to per-world
  render while preserving output semantics
- `train.py` no longer hard-rejects `world_batch_vec_env + include_visual=True`
  on principle; it now forwards the visual backend choice into the adapter

Validation:

- regression coverage now checks `legacy` vs `compiled` visual equality in
  [test_world_batch_vec_env.py](/home/void0312/Workshop/CMO/tests/world_batch/test_world_batch_vec_env.py)
- direct `ef_py` visual helper validation on the GPU build kept
  `max_abs_diff` around `9.5e-7`

Interpretation:

- Phase 1 is no longer only a probe
- it now has a maintained mainline entry point for the world-batch execution
  adapter
- the current remaining limitation is not API absence, but the same batching
  economics already seen in the probe results

## Execution Observation Batch Probe

The next non-visual GPU slice targeted execution observation packing:

- scope:
  `instrument + contact + rwr` packing first, then `mission observation`
- excluded:
  reward shaping, terrain, visual
- tool:
  [gpu_execution_observation_phase0_probe.cpp](/home/void0312/Workshop/CMO/src/tools/gpu_execution_observation_phase0_probe.cpp)

This slice is deliberately narrower than visual:

- it measures the GPU value of the compiled execution-observation products
- it avoids training integration and Python bindings
- it answers whether this batch packing is worth promoting into the next GPU
  runtime stage

Measured result on the local `RTX 3090`:

- `envs=256`, `contacts=8`, `rwr=4`, padded `16/8`:
  - host-readback GPU about `0.27x`
  - device-resident GPU about `0.27x`
- `envs=256`, `contacts=16`, `rwr=8`, padded `32/16`:
  - host-readback GPU about `0.34x`
  - device-resident GPU about `0.39x`
- `envs=1024`, `contacts=8`, `rwr=4`, padded `16/8`:
  - host-readback GPU about `0.63x`
  - device-resident GPU about `1.02x`
- `envs=4096`, `contacts=8`, `rwr=4`, padded `16/8`:
  - host-readback GPU about `0.76x`
  - device-resident GPU about `1.27x`
- `envs=4096`, `contacts=16`, `rwr=8`, padded `32/16`:
  - host-readback GPU about `0.72x`
  - device-resident GPU about `1.30x`

Output agreement stayed exact in the measured cases:

- `max_abs_diff = 0`
- `mean_abs_diff = 0`

Most important interpretation:

- unlike visual raster, this slice is not compute-heavy enough to justify GPU
  on moderate batches
- the main cost here is host-to-device upload, not the kernel
- this means standalone GPU observation packing is not a first-line production
  win for current `p5` training
- but it does become viable once:
  - batch size is very large, or
  - upstream state is already resident on device

Implication for the roadmap:

- keep the observation kernel as a valid supporting slice
- do not treat it as the next primary win after visual
- the next GPU kernel cut should prefer paths where:
  - arithmetic density is higher, or
  - host-to-device staging can be amortized by already-resident state

### Phase 2 follow-up: mission observation modes

The next Phase-2 increment extended the same experimental runtime with mission
observation products:

- supported modes:
  `basic`, `nav_v1`, `nav_v2`
- tool:
  [gpu_execution_observation_phase0_probe.cpp](/home/void0312/Workshop/CMO/src/tools/gpu_execution_observation_phase0_probe.cpp)
  with `--mission-mode`

Measured result on the local `RTX 3090`:

- `nav_v2`, `envs=1024`, padded `16/8`:
  - host-readback GPU about `0.70x`
  - device-resident GPU about `0.83x`
- `nav_v2`, `envs=4096`, padded `16/8`:
  - host-readback GPU about `0.88x`
  - device-resident GPU about `1.57x`
- `nav_v2`, `envs=16384`, padded `16/8`:
  - host-readback GPU about `0.39x`
  - device-resident GPU about `1.55x`
- `basic`, `envs=4096`, padded `16/8`:
  - host-readback GPU about `0.79x`
  - device-resident GPU about `1.39x`

Output agreement stayed exact in the measured cases:

- `max_abs_diff = 0`
- `mean_abs_diff = 0`

Most important interpretation:

- adding mission observation does not change the Phase-2 story qualitatively
- this slice remains dominated by host-to-device staging
- `device-resident` output is necessary before Phase 2 becomes a compelling
  production win
- compared with the earlier `instrument/contact/rwr`-only slice, mission terms
  improve arithmetic density somewhat, but not enough to make host-readback
  competitive

Implication for the roadmap:

- Phase 2 still was not closed at the probe-only stage
- the next useful work was not more standalone observation micro-optimization
- instead:
  - connect Phase 2 outputs to a real main-chain consumer, or
  - move to more arithmetic-dense kernels such as reward / mission shaping

### Phase 2 integration: WorldBatchVecEnv compiled batch path

The missing Phase-2 step was main-chain integration. That is now in place for
the execution-layer batch adapter:

- integration target:
  [world_batch_vec_env.py](/home/void0312/Workshop/CMO/python/rl/world_batch_vec_env.py)
- new bridge:
  `ef_py.compute_execution_observation_batch_numpy(...)`
- supported backends:
  `legacy`, `compiled`, `gpu_host`, `auto`
- current production default:
  `auto -> compiled`

What changed:

- `WorldBatchVecEnv.reset()` now uses a batched compiled observation path when
  the compiled runtime is enabled
- `WorldBatchVecEnv.step_wait()` now builds the whole observation batch from
  cached state in one call instead of looping through
  `build_universal_observation(...)` per env
- the compiled batch path still preserves loader-side step-evaluation caches by
  running `_prepare_step_evaluation(...)` per env after the batch helper
- regression coverage now explicitly checks `legacy` vs `compiled` observation
  equality on reset and on step

Measured result on the local machine using `WorldBatchVecEnv` with
`mission_obs_mode=nav_v2`, `include_visual=False`, `include_proprio=True`:

- `64 envs`:
  - reset total about `164.33 ms -> 127.46 ms`
  - reset obs build about `11.66 ms -> 6.51 ms`
  - step total about `15.24 ms -> 14.72 ms`
  - step obs build about `6.41 ms -> 6.05 ms`
  - about `1.04x` step wall-clock uplift
  - about `1.06x` step observation-build uplift
- `256 envs`:
  - step total about `74.20 ms -> 67.27 ms`
  - step obs build about `27.53 ms -> 24.10 ms`
  - about `1.10x` step wall-clock uplift
  - about `1.14x` step observation-build uplift

Interpretation:

- this closes Phase 2 as a main-chain integration task for the current CPU
  compiled path
- the gain is real but not dramatic because the compiled batch helper only
  removes part of the per-env Python observation assembly cost
- the earlier probe conclusion still stands:
  `gpu_host` does not become attractive until the surrounding path is
  device-resident too
- from here, the highest-value work is no longer more observation packing
  polish, but either:
  - zero-copy device consumers, or
  - more arithmetic-dense GPU kernels

Updated Phase-2 status:

- completed as a maintained mainline integration for the current CPU compiled
  batch path
- experimental GPU observation packing is also exposed through `ef_py`
- what remains is not batch-observation API work, but full device-resident
  consumer integration

## Flight Shaping Batch Probe

The next GPU slice targeted compiled flight shaping terms:

- scope:
  `compute_flight_shaping_terms`
- excluded:
  waypoint reward, approach reward, mission observation, visual
- tool:
  [gpu_flight_shaping_phase0_probe.cpp](/home/void0312/Workshop/CMO/src/tools/gpu_flight_shaping_phase0_probe.cpp)

This slice is materially different from observation packing:

- more arithmetic per world
- more clipping / power / branch structure
- still fully array-friendly once batched

Measured result on the local `RTX 3090`:

- `envs=4096`:
  - host-readback GPU about `1.04x`
  - device-resident GPU about `1.24x`
- `envs=16384`:
  - host-readback GPU about `1.22x`
  - device-resident GPU about `2.15x`
- `envs=65536`:
  - host-readback GPU about `1.60x`
  - device-resident GPU about `2.81x`

Output agreement stayed exact in the measured cases:

- `max_abs_diff = 0`
- `mean_abs_diff = 0`

Most important interpretation:

- this slice is meaningfully more promising than execution-observation packing
- unlike the observation kernel, it already crosses CPU parity at moderate
  batch sizes even with host readback
- device-resident output still matters, but it is no longer the only reason the
  GPU path wins
- host-to-device upload is still the dominant cost in the current standalone
  probe, which means the upside grows if upstream state ever becomes device
  resident too

Implication for the roadmap:

- keep flight shaping as a first-class GPU kernel candidate
- prioritize similar reward / mission kernels ahead of more observation-only
  packing work
- the next natural cuts are:
  - waypoint reward terms
  - approach reward terms
  - mission observation / route guidance packing

## Interaction Broadphase Probe

Phase 3 starts with exact broadphase candidate generation, not with a full
sensor/visual/comm rewrite:

- scope:
  uniform-grid / hash broadphase on device
- semantics:
  exact superset candidate sets for later narrow phases
- implementation:
  [gpu_interaction_broadphase_runtime.h](/home/void0312/Workshop/CMO/src/gpu/gpu_interaction_broadphase_runtime.h),
  [gpu_interaction_broadphase_runtime.cpp](/home/void0312/Workshop/CMO/src/gpu/gpu_interaction_broadphase_runtime.cpp),
  [gpu_interaction_broadphase_runtime_cuda.cu](/home/void0312/Workshop/CMO/src/gpu/gpu_interaction_broadphase_runtime_cuda.cu)
- tool:
  [gpu_interaction_broadphase_phase0_probe.cpp](/home/void0312/Workshop/CMO/src/tools/gpu_interaction_broadphase_phase0_probe.cpp)

Current first-cut design:

- entities and queries are grouped by world
- entities are inserted into a hashed uniform grid
- queries scan only neighboring cells implied by `range + max_entity_radius`
- the output is a per-query bitset over world-local entity indices
- if any scanned bucket overflows, the query falls back to `all local entities`
  so the exact superset guarantee is preserved

Measured result on the local `RTX 3090`:

- balanced hash, no overflow:
  - command:
    `./build-gpu/ef_gpu_interaction_broadphase_phase0_probe --worlds 16 --entities 1024 --queries 256 --cell-size 5000 --bucket-count 32768 --bucket-capacity 64`
  - CPU exact reference about `92.27 ms`
  - GPU host-readback about `3.89 ms`
  - GPU device-resident about `3.72 ms`
  - about `23.7x` vs CPU on host-readback
  - about `24.8x` vs CPU on device-resident
  - candidate pairs:
    `703062 -> 703062`
  - missing reference pairs:
    `0`
  - overflow buckets / queries:
    `0 / 0`
- stressed hash, forced overflow fallback:
  - command:
    `./build-gpu/ef_gpu_interaction_broadphase_phase0_probe --worlds 16 --entities 1024 --queries 256 --cell-size 5000 --bucket-count 4096 --bucket-capacity 8`
  - CPU exact reference about `124.66 ms`
  - GPU host-readback about `5.14 ms`
  - GPU device-resident about `4.90 ms`
  - about `24.3x` vs CPU on host-readback
  - about `25.4x` vs CPU on device-resident
  - candidate pairs:
    `703062 -> 4194304`
  - missing reference pairs:
    `0`
  - overflow buckets / queries:
    `651 / 4096`
  - expansion factor:
    about `5.97x`

Most important interpretation:

- Phase 3's first cut is technically viable now
- the current uniform-grid/hash path can preserve exact superset semantics
- when the hash is provisioned sanely, the broadphase is not only exact in the
  superset sense but also very tight in the measured synthetic case
- overflow fallback works as intended:
  it inflates false positives, but it does not miss true interactions
- unlike single-aircraft observation packing, this slice already shows the kind
  of large multiplicative gain that matters for future multi-entity scaling

Implication for the roadmap:

- Phase 3 should continue from this broadphase base, not from more visual-only
  work
- the next Phase-3 cuts should specialize this generic broadphase into:
  - sensor candidate generation
  - visual object candidate generation
  - communication candidate generation
- only after those candidate lists exist should narrow-phase GPU work be
  considered

### Phase 3 specialization: sensor candidate generation

The first specialization of the generic broadphase is the sensor path:

- tool:
  [gpu_sensor_candidate_phase0_probe.cpp](/home/void0312/Workshop/CMO/src/tools/gpu_sensor_candidate_phase0_probe.cpp)
- semantics:
  exact superset of range-gated sensor candidates
- current specialization boundary:
  broadphase only uses per-sensor range; FOV / LOS / Doppler remain narrow-phase

Measured result on the local `RTX 3090`:

- command:
  `./build-gpu/ef_gpu_sensor_candidate_phase0_probe --worlds 16 --targets 1024 --sensors 256 --cell-size 5000 --bucket-count 32768 --bucket-capacity 64`
- CPU reference about `107.10 ms`
- GPU host-readback about `15.70 ms`
- GPU device-resident about `15.54 ms`
- about `6.82x` vs CPU on host-readback
- about `6.89x` vs CPU on device-resident
- candidate pairs:
  `1932001 -> 1932001`
- missing reference pairs:
  `0`
- overflow buckets / queries:
  `0 / 0`

Interpretation:

- the generic broadphase base transfers cleanly to the sensor path
- range-gated exact-superset semantics are preserved
- this is already a meaningful acceleration slice for later sensor-system
  integration even before LOS / FOV stay on CPU

### Phase 3 specialization: communication candidate generation

The second specialization targets datalink / comm candidate generation:

- tool:
  [gpu_comm_candidate_phase0_probe.cpp](/home/void0312/Workshop/CMO/src/tools/gpu_comm_candidate_phase0_probe.cpp)
- semantics:
  exact superset of current datalink peers
- current specialization boundary:
  network partitioning is encoded directly into the broadphase world index, while
  line-of-sight horizon remains part of the exact CPU reference

Measured result on the local `RTX 3090`:

- command:
  `./build-gpu/ef_gpu_comm_candidate_phase0_probe --worlds 16 --nodes 1024 --networks 2 --cell-size 10000 --bucket-count 32768 --bucket-capacity 64`
- CPU exact comm reference about `617.74 ms`
- GPU host-readback about `167.32 ms`
- GPU device-resident about `166.59 ms`
- about `3.69x` vs CPU on host-readback
- about `3.71x` vs CPU on device-resident
- candidate pairs:
  `2776625 -> 2801031`
- missing reference pairs:
  `0`
- overflow buckets / queries:
  `0 / 0`
- expansion factor:
  about `1.0088x`

Interpretation:

- network partitioning makes the broadphase specialization useful immediately
- communication candidates stay very tight even before horizon / LOS filtering
- this is a good Phase-3 slice because it attacks a currently `O(N^2)` style
  path in the datalink system without changing semantics

Current Phase-3 status:

- completed at probe level:
  - generic interaction broadphase
  - sensor candidate generation
  - communication candidate generation

### Phase 3 specialization: visual object candidate generation

The final Phase-3 specialization targets visual object candidate generation:

- tool:
  [gpu_visual_candidate_phase0_probe.cpp](/home/void0312/Workshop/CMO/src/tools/gpu_visual_candidate_phase0_probe.cpp)
- semantics:
  exact superset of a finite-range visual-frustum candidate reference
- current specialization boundary:
  the probe uses a finite `far_range_m` and exact CPU frustum reference for
  that range; terrain occlusion and per-pixel raster remain later stages

Measured result on the local `RTX 3090`:

- command:
  `./build-gpu/ef_gpu_visual_candidate_phase0_probe --worlds 16 --objects 1024 --cameras 64 --far-range 25000 --cell-size 5000 --bucket-count 32768 --bucket-capacity 64`
- CPU exact visual candidate reference about `67.39 ms`
- GPU host-readback about `6.24 ms`
- GPU device-resident about `6.13 ms`
- about `10.81x` vs CPU on host-readback
- about `10.99x` vs CPU on device-resident
- candidate pairs:
  `189432 -> 503784`
- missing reference pairs:
  `0`
- overflow buckets / queries:
  `0 / 0`
- expansion factor:
  about `2.66x`

Interpretation:

- the broadphase base also transfers cleanly to visual candidate generation
- this slice intentionally accepts extra false positives because visual frustum
  filtering is deferred to later narrow stages
- the result is still a useful reduction versus current all-object collection
  while preserving the no-miss guarantee for the finite-range reference

Updated Phase-3 status:

- completed at probe level:
  - generic interaction broadphase
  - sensor candidate generation
  - communication candidate generation
  - visual object candidate generation
- Phase 3 is now complete as a probe/runtime-research stage
- what remains after Phase 3 is not more candidate-generation probes, but:
  - specialization into real runtime call sites, or
  - narrow-phase integration for the selected domains

### Phase 3 mainline integration: maintained `ef_py` broadphase API

The generic Phase-3 broadphase is now also exposed through the mainline Python
module:

- bound structs:
  `InteractionEntityPacked`, `InteractionQueryPacked`,
  `InteractionBroadphaseConfig`, `InteractionBroadphaseExperimentStats`
- bound helpers:
  `interaction_broadphase_word_count(...)`
  `build_interaction_broadphase_batch_numpy(...)`
  `last_interaction_broadphase_stats()`

Interpretation:

- Phase 3 is not yet wired into the live sensor/visual/comm systems
- but it is no longer trapped in standalone probes only
- downstream call-site integration can now build on a maintained `ef_py`
  contract instead of ad hoc C++ binaries

### Phase 3 runtime-boundary completion: live candidate helpers and visual call-site use

The remaining Phase-3 runtime work has now been pushed one level closer to the
mainline:

- `WorldBatchRuntime` now exposes maintained live-world candidate helpers:
  - `get_sensor_candidate_ids_batch(...)`
  - `get_visual_candidate_ids_batch(...)`
  - `get_comm_candidate_ids_batch(...)`
- these helpers operate on real `WorldEntityRef` inputs, pack the current
  world state into the Phase-3 broadphase representation, and decode exact
  supersets back into entity-id lists
- the maintained world-batch visual helper now uses
  `get_visual_candidate_ids_batch(...)` before scene collection, so the
  candidate-generation path is no longer probe-only

Validation:

- world-batch runtime regression now checks that:
  - sensor candidates include nearby hostile/friendly aircraft but exclude the
    owner and distant contacts
  - visual candidates include the expected nearby objects
  - communication candidates collapse to same-side/same-network peers only

Updated interpretation:

- Phase 3 is now integrated into maintained runtime boundaries
- visual has a real call-site consumer in the world-batch helper path
- sensor and comm now have real runtime-facing candidate APIs
- what still remains beyond Phase 3 is a deeper replacement of the live
  narrow-phase systems themselves, not broadphase availability

### Phase 4 first cut: GPU batch world stepping

The first Phase-4 slice is now implemented as a packed-state multi-world
stepping probe:

- tool:
  [gpu_world_batch_phase0_probe.cpp](/home/void0312/Workshop/CMO/src/tools/gpu_world_batch_phase0_probe.cpp)
- runtime:
  [gpu_world_batch_runtime.h](/home/void0312/Workshop/CMO/src/gpu/gpu_world_batch_runtime.h)
  [gpu_world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/gpu/gpu_world_batch_runtime.cpp)
  [gpu_world_batch_runtime_cuda.cu](/home/void0312/Workshop/CMO/src/gpu/gpu_world_batch_runtime_cuda.cu)
- scope:
  one controlled packed flight-state per world, device-resident reset/replay,
  and optional CUDA Graph capture of the repeated launch topology
- semantics:
  exact step-to-step equivalence against the CPU reference on the same packed
  state update for a fixed seed

The packed step keeps the runtime slice intentionally narrow:

- command-limited velocity tracking
- wind-applied position integration
- altitude floor / vertical-speed clipping
- fuel burn and mission-time accumulation

This is not yet a full `SimulationKernel` GPU rewrite. It is the smallest
credible Phase-4 slice that exercises:

- device-resident multi-world state
- repeated step sequencing
- CUDA Graph capture
- fixed-seed equivalence checking

Measured result on the local `RTX 3090`:

- command:
  `./build-gpu/ef_gpu_world_batch_phase0_probe --frames 32 --worlds 4096 --steps 256`
- CPU reference:
  about `6.62 ms/frame`
- GPU host-readback direct:
  about `1.80 ms/frame`
- GPU host-readback graph:
  about `1.67 ms/frame`
- GPU device-resident direct:
  about `1.44 ms/frame`
- GPU device-resident graph:
  about `1.24 ms/frame`
- speedup:
  about `3.67x` host-direct,
  `3.96x` host-graph,
  `4.60x` device-direct,
  `5.33x` device-graph
- equivalence:
  `max_abs_diff = 0`

Scaling checks:

- `1024 worlds, 256 steps`
  - CPU about `1.67 ms/frame`
  - GPU device-resident graph about `1.06 ms/frame`
  - about `1.57x`
- `16384 worlds, 256 steps`
  - CPU about `27.81 ms/frame`
  - GPU device-resident graph about `1.72 ms/frame`
  - about `16.21x`

Interpretation:

- the Phase-4 premise is now validated at probe level
- CUDA Graph replay matters, but the larger gain comes from keeping repeated
  multi-world state on device
- this slice scales much more strongly with world count than the earlier
  observation-packing kernels
- the next decision point is not whether Phase 4 is viable, but whether to
  integrate this packed stepping path into a real maintained runtime boundary

Updated Phase-4 status:

- completed at probe/runtime-research level:
  - packed-state device-resident multi-world stepping
  - optional CUDA Graph capture for repeated launch topology
  - fixed-seed exact equivalence checking against CPU reference
- integrated into the mainline Python module as a maintained experimental API:
  - `WorldBatchStepState`
  - `WorldBatchStepExperimentStats`
  - `step_world_batch_state_batch(...)`
  - `step_world_batch_state_batch_reference(...)`
  - `upload_world_batch_step_states(...)`
  - `replay_world_batch_step_device_sequence(...)`
  - `download_world_batch_step_states()`
- not yet completed:
  - integration into `WorldBatchRuntime` or `SimulationKernel`
  - full exact world-step parity with the current ECS simulation core

### Phase 4 runtime-boundary completion: `WorldBatchRuntime` packed-flight stepping

The remaining Phase-4 runtime integration has now been completed at the
`WorldBatchRuntime` boundary:

- new maintained APIs on `WorldBatchRuntime`:
  - `extract_packed_flight_states_batch(...)`
  - `apply_packed_flight_states_batch(...)`
  - `step_packed_flight_states_experiment_batch(...)`
- these APIs bridge live worlds into the packed Phase-4 state:
  - extract state from real entities in current worlds
  - step the packed state through the Phase-4 experiment path
  - optionally write the resulting state back into live worlds

Validation:

- new runtime regression checks:
  - extracted packed states match the Phase-4 CPU reference after repeated steps
  - `step_packed_flight_states_experiment_batch(..., write_back=True)` writes
    back the same state that the reference stepping predicts

Updated interpretation:

- Phase 4 is no longer isolated to a standalone probe
- it now has a maintained runtime boundary inside `WorldBatchRuntime`
- the remaining open item is not API absence, but full parity with the exact
  ECS world-step implementation in `SimulationKernel`

## Decision

Recommended current direction:

- yes to GPU research and staged design
- no to immediate full-kernel GPU rewrite
- no to simulator replacement
- yes to a GPU-resident observation / visual / sparse-interaction roadmap

That is the narrowest path that is still technically serious, realism-safe, and
compatible with the current architecture.
