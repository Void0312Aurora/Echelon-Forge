# Tools Diagnostics README

`tools/diagnostics/` contains ad hoc operator-facing scripts used for investigation and matrix-style sanity checks.

These scripts are intentionally separate from the top-level `tools/` entrypoints because they usually:

- run one-off exploratory sweeps
- depend on local model/checkpoint availability
- print human-oriented summaries instead of stable machine-checked assertions
- help diagnose failures rather than serve as maintained core workflows

Current examples:

- [leader_perf_probe.py](/home/void0312/CMO/tools/diagnostics/leader_perf_probe.py)
  - Quick leader-layer throughput probe for the maintained `auto`, `subproc`, `shared`, and `dummy` baselines.

- [ablate_visual_training_effect.py](/home/void0312/CMO/tools/diagnostics/ablate_visual_training_effect.py)
  - Automates a `visual_downsample` train/eval matrix for visual execution policies and aggregates end metrics by factor.
- [benchmark_visual_resolution.py](/home/void0312/CMO/tools/diagnostics/benchmark_visual_resolution.py)
  - Sweeps `visual_downsample` and reports visual tensor size, rollout-buffer cost, env-step throughput, and visual extractor forward latency proxies.
- [benchmark_spatial_query_phase1.py](/home/void0312/CMO/tools/diagnostics/benchmark_spatial_query_phase1.py)
  - Benchmarks the Phase 1 compiled spatial query path against the legacy Python geometry reference and reports `UniversalEnv` single/vector rollout throughput.
- [benchmark_scenario_compiler_phase2.py](/home/void0312/CMO/tools/diagnostics/benchmark_scenario_compiler_phase2.py)
  - Benchmarks Phase 2 compiler cache and runtime materializer behavior against legacy `json.load + imports merge`, and reports compiled instantiate / `load_compiled_scenario()` cost.
- [benchmark_mission_runtime_phase3.py](/home/void0312/CMO/tools/diagnostics/benchmark_mission_runtime_phase3.py)
  - Benchmarks Phase 3 mission-nav, command-tracking, waypoint reward, approach reward, conditional objective, and safety/termination runtime helpers against the legacy Python formulas.
- [benchmark_world_batch_phase4.py](/home/void0312/CMO/tools/diagnostics/benchmark_world_batch_phase4.py)
  - Benchmarks the current Phase 4 `WorldBatchRuntime` slice against legacy per-world kernel apply and step/read loops, separating `kernel apply` and `step/read` speedups.
- [benchmark_world_batch_vec_env_phase4.py](/home/void0312/CMO/tools/diagnostics/benchmark_world_batch_vec_env_phase4.py)
  - Benchmarks the Phase 4 execution training adapter against `DummyVecEnv + UniversalEnv`, reporting reset cost and `ms/env-step` rollout speedup on the non-visual execution path.
- [benchmark_policy_observation_bridge_phase4.py](/home/void0312/CMO/tools/diagnostics/benchmark_policy_observation_bridge_phase4.py)
  - Benchmarks the Phase 4 policy-observation CUDA bridge with `bridge on/off` A/B runs, reporting isolated policy forward latency, `collect_rollouts()` throughput, `train()` update throughput, and combined `collect + train` cost for observation-only and `p5`-like visual workloads.
    It now also records requested/effective observation, visual, and
    `flight_shaping` backends plus the latest visual/flight-shaping runtime
    stats, and supports `--flight-shaping-backend` for maintained `p5` A/B
    reward-path checks.
- [benchmark_coarse_route_segments.py](/home/void0312/CMO/tools/diagnostics/benchmark_coarse_route_segments.py)
  - Replays real `p5` route rollouts and compares coarse route-leg propagation against fine truth, reporting endpoint error and training-risk proxies by horizon.
- [generate_exact_world_step_parity_trace.py](/home/void0312/CMO/tools/diagnostics/generate_exact_world_step_parity_trace.py)
  - Generates the Phase 1 fixed-seed CPU exact-step parity trace for single-aircraft `p5`-style worlds, archiving step-0 replay state plus per-step apply-signatures, learner-facing truth/instrument observations, terminal metadata, and hidden dynamics surfaces (`environment_sample`, `angular_velocity`, `force_accumulator`, `aero_state`, `control_law_state`, `egi`).
- [compare_exact_world_step_shadow_trace.py](/home/void0312/CMO/tools/diagnostics/compare_exact_world_step_shadow_trace.py)
  - Replays a Phase 1 parity trace through the Phase 2 exact-step prototype in both CPU-reference and GPU-shadow modes, then reports prototype drift against the archived CPU trace plus CPU-vs-GPU shadow agreement across both learner-facing and hidden-dynamics surfaces.
- [generate_exact_world_step_system_trace.py](/home/void0312/CMO/tools/diagnostics/generate_exact_world_step_system_trace.py)
  - Generates the frozen exact-system inventory trace for the re-architecture line, archiving the initial packed exact state, the first-scope stage-contract inventory, and per-stage snapshots after every traceable system (`CommandLinkMovement` through `MassUpdate`).
- [compare_exact_world_step_system_trace.py](/home/void0312/CMO/tools/diagnostics/compare_exact_world_step_system_trace.py)
  - Replays a system-stage trace through the manual exact-stage CPU pipeline and diffs every stage independently, including normalized packed-state component digests and the frozen stage-contract inventory so the first diverging exact component can be identified immediately.
- [compare_exact_world_step_command_lane_slice.py](/home/void0312/CMO/tools/diagnostics/compare_exact_world_step_command_lane_slice.py)
  - Replays the first data-oriented exact CPU executor slice (`CommandLinkMovement` through `CommandLag`) from packed exact state and compares it against the archived `CommandLag` stage in a system trace, while intentionally stripping runtime-only `sim_time` fields that the current apply path does not restore.
- [compare_exact_world_step_control_aero_slice.py](/home/void0312/CMO/tools/diagnostics/compare_exact_world_step_control_aero_slice.py)
  - Replays the second data-oriented exact CPU executor slice (`FlightControl` through `ComputeAeroState`), chained after the command-lane slice, and compares it against the archived `ComputeAeroState` stage while stripping runtime-only `sim_time` fields from the comparison record.
- [compare_exact_world_step_force_ground_slice.py](/home/void0312/CMO/tools/diagnostics/compare_exact_world_step_force_ground_slice.py)
  - Replays the third data-oriented exact CPU executor slice (`ComputeForces` through `GroundContact`), chained after the command-lane and control/aero slices, and compares it against the archived `GroundContact` stage while stripping runtime-only `sim_time` fields from the comparison record.
- [compare_exact_world_step_front_half_slice.py](/home/void0312/CMO/tools/diagnostics/compare_exact_world_step_front_half_slice.py)
  - Replays the Phase D front-half executor (`CommandLinkMovement` through `GroundContact`) through either the exact CPU chain or the new CUDA backend, then compares the resulting `GroundContact` surface and packed-state digests against the archived system trace.
- [compare_exact_world_step_aircraft_tail_slice.py](/home/void0312/CMO/tools/diagnostics/compare_exact_world_step_aircraft_tail_slice.py)
  - Replays the Phase D aircraft-tail executor (`RotationalIntegrate` through `MassUpdate`), chained after the command-lane, control/aero, and force/ground slices, through either the exact CPU chain or the CUDA backend, then compares the resulting `MassUpdate` surface and packed-state digests against the archived system trace.
- [compare_exact_world_step_aircraft_chain_cuda.py](/home/void0312/CMO/tools/diagnostics/compare_exact_world_step_aircraft_chain_cuda.py)
  - Replays the resident aircraft-only Phase D CUDA chain, keeping `CommandLane` on CPU and running `FlightControl` through `MassUpdate` on a single CUDA path, then compares the resulting `MassUpdate` surface and packed-state digests against the archived aircraft-only system trace.
- [generate_exact_world_step_missile_guidance_trace.py](/home/void0312/CMO/tools/diagnostics/generate_exact_world_step_missile_guidance_trace.py)
  - Generates a dedicated exact CPU `MissileGuidance` trace for mixed aircraft+missile worlds, archiving both the initial packed exact state and the post-guidance stage record for the missile/target pair.
- [compare_exact_world_step_missile_guidance_slice.py](/home/void0312/CMO/tools/diagnostics/compare_exact_world_step_missile_guidance_slice.py)
  - Replays the exact missile-guidance slice from packed exact state through either the CPU reference path or the CUDA backend, then compares it against the archived `MissileGuidance` stage, including packed component digests and direct stage-surface agreement.
- [generate_exact_world_step_first_scope_chain_trace.py](/home/void0312/CMO/tools/diagnostics/generate_exact_world_step_first_scope_chain_trace.py)
  - Generates a mixed aircraft+missile trace for the stitched first-scope exact CPU chain, archiving the initial packed state plus the final `MassUpdate` record after all traceable first-scope stages.
- [compare_exact_world_step_first_scope_chain.py](/home/void0312/CMO/tools/diagnostics/compare_exact_world_step_first_scope_chain.py)
  - Replays the stitched first-scope chain from packed exact state and compares it against the archived final stage on mixed aircraft+missile worlds. It now supports a controlled `--gpu-guidance` mode that swaps the `MissileGuidance` slice to the CUDA backend while preserving the current CPU chain order.
- [compare_exact_world_step_first_scope_chain_cuda.py](/home/void0312/CMO/tools/diagnostics/compare_exact_world_step_first_scope_chain_cuda.py)
  - Replays the resident mixed first-scope Phase D CUDA chain through the `WorldBatchRuntime` experimental batch API, keeping `CommandLane` on CPU and running `FlightControl -> GroundContact`, `MissileGuidance`, and `RotationalIntegrate -> MassUpdate` on a single CUDA upload / multi-kernel / single-download path, then compares the resulting final `MassUpdate` surface and packed-state digests against the archived mixed first-scope trace.
    It also supports `--runtime-resident`, which uses the new `WorldBatchRuntime`-level `upload -> replay -> download` carrier, `--runtime-cached-session`, which primes a cached exact-state session and steps it without re-extracting from Flecs, and `--resident`, which bypasses the runtime helper and drives the packed exact-state carrier directly so runtime glue can be separated from device replay.
- [benchmark_exact_world_step_first_scope_chain_cached_session.py](/home/void0312/CMO/tools/diagnostics/benchmark_exact_world_step_first_scope_chain_cached_session.py)
  - Runs a deterministic multi-step aircraft cached-session loop through `WorldBatchRuntime`, now with configurable `world_count`, updates pilot actions every frame, varies write-back cadence, and reports prime cost, cold first-step cost, warm steady-state step cost, final live-world flush correctness, the first divergence step if any remains, and the runtime-owned cached-session timing breakdown (`prime_extract`, update cost, step total, write-back, and embedded chain timings).
    It also supports `--runtime-step-batch-backend`, which replays the same
    fixture through the experimental `WorldBatchRuntime.step_batch()` exact
    backend switch instead of calling the cached-session stepping helper
    directly. That switch is still an explicit opt-in experiment rather than
    the maintained default exact-step path, so benchmark parity here should be
    treated as a regression gate for the experiment, not as proof that the
    default runtime path has changed. The report now also includes explicit
    promotion-threshold checks: CPU-vs-test speedup ratios, write-back burden
    ratios, blocker labels, and a final `promotion_ready` verdict for the
    experimental runtime switch.
- [benchmark_exact_world_step_first_scope_chain_cached_session_matrix.py](/home/void0312/CMO/tools/diagnostics/benchmark_exact_world_step_first_scope_chain_cached_session_matrix.py)
  - Sweeps the cached-session benchmark across larger first-scope aircraft batch sizes and aggregates the broader runtime/backend gate: warm chain total, upload, command-lane, write-back, per-state steady-state cost, the first CPU divergence step for each batch size, and the derived write-back-vs-chain/runtime-step ratios that quantify whether the experimental `step_batch()` backend is promotion-worthy. It now also supports `--runtime-step-batch-backend` so the same batch-size sweep can be run through the explicit runtime switch instead of the direct helper.
- [generate_exact_world_step_cached_session_multistep_trace.py](/home/void0312/CMO/tools/diagnostics/generate_exact_world_step_cached_session_multistep_trace.py)
  - Generates a fixed-seed per-step/per-stage exact CPU trace for the cached-session benchmark fixture, now with configurable `world_count`, archiving the pre-step state plus every traceable stage from `CommandLinkMovement` through `MassUpdate` for each step.
- [compare_exact_world_step_cached_session_multistep.py](/home/void0312/CMO/tools/diagnostics/compare_exact_world_step_cached_session_multistep.py)
  - Replays the same cached-session fixture through CPU or GPU cached sessions, compares each step against the archived `MassUpdate` record, and, when needed, localizes the first repeated-step divergence with per-world slice-level checks for `CommandLane`, `FrontHalf`, `MissileGuidance`, and `AircraftTail`, plus an internal `FrontHalf` split into `FlightControl`, `ClearForces`, `ComputeAeroState`, `ComputeForces`, `ComputeAerodynamics`, and `GroundContact`.
    On aircraft-only traces it now switches to a no-missile tail drill-down and
    can localize the first broader-batch drift down to
    `RotationalIntegrate/LeapfrogIntegrate/NavigationSystem/UpdateInstruments/FuelConsumption/MassUpdate`.
    It also supports `--runtime-step-batch-backend`, so the archived multistep
    trace can be replayed through the same experimental runtime backend switch
    that now drives `step_batch()`. As with the benchmark, this mode is meant
    to validate the explicit experiment boundary and should not be read as the
    maintained training/runtime default.
- [ef_gpu_visual_phase0_probe](/home/void0312/CMO/src/tools/gpu_visual_phase0_probe.cpp)
  - C++ phase-0 GPU front-end probe for the visual path. It reports CUDA availability, VRAM footprint estimates for ARB tensors, batched CPU-authoritative visual throughput, host-readback GPU throughput, and device-resident GPU throughput through the new `GpuVisualRuntime` scaffolding. It now supports `--terrain off|cpu|gpu`.
- [ef_gpu_execution_observation_phase0_probe](/home/void0312/CMO/src/tools/gpu_execution_observation_phase0_probe.cpp)
  - C++ phase-0 GPU probe for batched execution-observation packing. It compares CPU reference packing, host-readback GPU packing, and device-resident GPU packing for `instrument/contact/rwr/mission` products, and supports `--mission-mode basic|nav_v1|nav_v2`.
- [ef_gpu_flight_shaping_phase0_probe](/home/void0312/CMO/src/tools/gpu_flight_shaping_phase0_probe.cpp)
  - C++ phase-0 GPU probe for batched `flight shaping` reward terms. It compares CPU reference shaping, host-readback GPU shaping, and device-resident GPU shaping for the compiled flight shaping products.
- [ef_gpu_interaction_broadphase_phase0_probe](/home/void0312/CMO/src/tools/gpu_interaction_broadphase_phase0_probe.cpp)
  - C++ phase-0 GPU probe for Phase 3 `interaction broadphase`. It compares CPU exact candidate generation against a CUDA uniform-grid/hash broadphase, checks exact-superset semantics, and reports host-readback versus device-resident throughput plus overflow behavior.
- [ef_gpu_sensor_candidate_phase0_probe](/home/void0312/CMO/src/tools/gpu_sensor_candidate_phase0_probe.cpp)
  - C++ phase-0 GPU probe for Phase 3 `sensor candidate generation`. It specializes the generic broadphase to per-sensor range queries and checks exact-superset semantics against the CPU range-gated sensor reference.
- [ef_gpu_comm_candidate_phase0_probe](/home/void0312/CMO/src/tools/gpu_comm_candidate_phase0_probe.cpp)
  - C++ phase-0 GPU probe for Phase 3 `communication candidate generation`. It uses network-partitioned broadphase queries and checks exact-superset semantics against the current CPU datalink peer reference.
- [ef_gpu_visual_candidate_phase0_probe](/home/void0312/CMO/src/tools/gpu_visual_candidate_phase0_probe.cpp)
  - C++ phase-0 GPU probe for Phase 3 `visual object candidate generation`. It compares a finite-range exact CPU frustum candidate reference against broadphase range candidates and checks no-miss superset behavior.
- [ef_gpu_world_batch_phase0_probe](/home/void0312/CMO/src/tools/gpu_world_batch_phase0_probe.cpp)
  - C++ phase-0 GPU probe for Phase 4 `GPU batch world stepping`. It compares CPU packed-state multi-world stepping against host-readback GPU stepping, device-resident GPU stepping, and CUDA Graph replay, while checking fixed-seed exact equivalence.
- [diagnose_training_matrix.py](/home/void0312/CMO/tools/diagnostics/diagnose_training_matrix.py)
  - Runs a small evaluation matrix across model/scenario pairs and extracts headline metrics from evaluator output.
- [sanity_check.py](/home/void0312/CMO/tools/diagnostics/sanity_check.py)
  - Performs a low-level kernel/API sanity probe against a spawned unit.

## GPU Phase 0 Build

The experimental GPU scaffolding is opt-in. To build it:

```bash
cmake -S . -B build-gpu -DEF_ENABLE_CUDA_EXPERIMENTS=ON
cmake --build build-gpu --target ef_gpu_visual_phase0_probe -j
cmake --build build-gpu --target ef_gpu_execution_observation_phase0_probe -j
cmake --build build-gpu --target ef_gpu_flight_shaping_phase0_probe -j
cmake --build build-gpu --target ef_gpu_interaction_broadphase_phase0_probe -j
cmake --build build-gpu --target ef_gpu_sensor_candidate_phase0_probe -j
cmake --build build-gpu --target ef_gpu_comm_candidate_phase0_probe -j
cmake --build build-gpu --target ef_gpu_visual_candidate_phase0_probe -j
cmake --build build-gpu --target ef_gpu_world_batch_phase0_probe -j
```

Example probe run:

```bash
./build-gpu/ef_gpu_visual_phase0_probe --frames 512 --objects 64 --envs 16 --history-steps 2048 --terrain off
./build-gpu/ef_gpu_visual_phase0_probe --frames 64 --objects 64 --envs 16 --terrain gpu
./build-gpu/ef_gpu_execution_observation_phase0_probe --frames 128 --envs 1024 --contacts 8 --rwr 4 --max-contacts 16 --max-rwr 8 --mission-mode nav_v2
./build-gpu/ef_gpu_flight_shaping_phase0_probe --frames 256 --envs 4096
./build-gpu/ef_gpu_interaction_broadphase_phase0_probe --worlds 16 --entities 1024 --queries 256 --cell-size 5000 --bucket-count 32768 --bucket-capacity 64
./build-gpu/ef_gpu_sensor_candidate_phase0_probe --worlds 16 --targets 1024 --sensors 256 --cell-size 5000 --bucket-count 32768 --bucket-capacity 64
./build-gpu/ef_gpu_comm_candidate_phase0_probe --worlds 16 --nodes 1024 --networks 2 --cell-size 10000 --bucket-count 32768 --bucket-capacity 64
./build-gpu/ef_gpu_visual_candidate_phase0_probe --worlds 16 --objects 1024 --cameras 64 --far-range 25000 --cell-size 5000 --bucket-count 32768 --bucket-capacity 64
./build-gpu/ef_gpu_world_batch_phase0_probe --frames 32 --worlds 4096 --steps 256
```

`--envs` now controls both the VRAM footprint estimate and the actual number of
worlds rendered per batch-frame in the benchmark.

Current phase-1 experimental constraint:

- `--terrain off`
  - runs the batched CUDA object-raster path and compares it against the CPU batch adapter on the same object-only semantics
- `--terrain cpu`
  - keeps terrain enabled, but forces the experimental path to fall back to the CPU reference for control and agreement checks
- `--terrain gpu`
  - runs the batched CUDA terrain+object path against the CPU reference on the same legacy terrain snapshot

Exact-step diagnostics also expose packed combat surfaces through
`ef_py.exact_world_step_state_v1_combat_surfaces_packed(...)`, which is useful
for debugging `Missile` and `ContactList` parity without unpacking raw binary
state by hand.
