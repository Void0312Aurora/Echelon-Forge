# Tools Diagnostics README

`tools/diagnostics/` contains operator-facing probes, benchmarks, and matrix
checks that support the maintained CPU-mainline runtime and, when explicitly
requested, the frozen experimental GPU helper line.

These scripts are intentionally separate from top-level entrypoints because
they usually:

- run one-off exploratory sweeps
- depend on local model/checkpoint availability
- print human-oriented summaries instead of stable machine-checked assertions
- help diagnose failures rather than serve as maintained core workflows

Current maintained diagnostics:

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
  - Benchmarks the Phase 4 policy-observation bridge. Its default maintained
    case now mirrors the current `p5` mainline, while older mixed/all-GPU-host
    helper cases require an explicit experimental opt-in.
- [benchmark_coarse_route_segments.py](/home/void0312/CMO/tools/diagnostics/benchmark_coarse_route_segments.py)
  - Replays real `p5` route rollouts and compares coarse route-leg propagation against fine truth, reporting endpoint error and training-risk proxies by horizon.
- [diagnose_training_matrix.py](/home/void0312/CMO/tools/diagnostics/diagnose_training_matrix.py)
  - Runs a small evaluation matrix across model/scenario pairs and extracts headline metrics from evaluator output.
- [diagnose_cooperative_takeoff_trajectory.py](/home/void0312/CMO/tools/diagnostics/diagnose_cooperative_takeoff_trajectory.py)
  - Replays one cooperative takeoff world, then exports a PNG + JSON with both aircraft trajectories, altitude/speed traces, and takeoff-clearance timeline.
- [diagnose_cooperative_takeoff_to_cruise_trajectory.py](/home/void0312/CMO/tools/diagnostics/diagnose_cooperative_takeoff_to_cruise_trajectory.py)
  - Replays one cooperative takeoff-to-cruise bridge world, then exports a PNG + JSON with both aircraft trajectories, altitude/speed traces, clearance timeline, and waypoint-progress traces.
- [sanity_check.py](/home/void0312/CMO/tools/diagnostics/sanity_check.py)
  - Performs a low-level kernel/API sanity probe against a spawned unit.

Frozen experimental GPU helper phase-0 probes:

- [ef_gpu_visual_phase0_probe](/home/void0312/CMO/src/tools/experimental/gpu_phase0/gpu_visual_phase0_probe.cpp)
  - C++ phase-0 GPU front-end probe for the visual path.
- [ef_gpu_execution_observation_phase0_probe](/home/void0312/CMO/src/tools/experimental/gpu_phase0/gpu_execution_observation_phase0_probe.cpp)
  - C++ phase-0 GPU probe for batched execution-observation packing.
- [ef_gpu_flight_shaping_phase0_probe](/home/void0312/CMO/src/tools/experimental/gpu_phase0/gpu_flight_shaping_phase0_probe.cpp)
  - C++ phase-0 GPU probe for batched `flight shaping` reward terms.
- [ef_gpu_interaction_broadphase_phase0_probe](/home/void0312/CMO/src/tools/experimental/gpu_phase0/gpu_interaction_broadphase_phase0_probe.cpp)
  - C++ phase-0 GPU probe for interaction broadphase.
- [ef_gpu_sensor_candidate_phase0_probe](/home/void0312/CMO/src/tools/experimental/gpu_phase0/gpu_sensor_candidate_phase0_probe.cpp)
  - C++ phase-0 GPU probe for sensor candidate generation built on the retained broadphase helper.
- [ef_gpu_comm_candidate_phase0_probe](/home/void0312/CMO/src/tools/experimental/gpu_phase0/gpu_comm_candidate_phase0_probe.cpp)
  - C++ phase-0 GPU probe for communication candidate generation built on the retained broadphase helper.
- [ef_gpu_visual_candidate_phase0_probe](/home/void0312/CMO/src/tools/experimental/gpu_phase0/gpu_visual_candidate_phase0_probe.cpp)
  - C++ phase-0 GPU probe for visual-object candidate generation built on the retained broadphase helper.

## GPU Phase 0 Build

The retained GPU helper scaffolding is still opt-in. To build it:

```bash
cmake -S . -B build-gpu -DEF_ENABLE_CUDA_EXPERIMENTS=ON
cmake --build build-gpu --target ef_gpu_visual_phase0_probe -j
cmake --build build-gpu --target ef_gpu_execution_observation_phase0_probe -j
cmake --build build-gpu --target ef_gpu_flight_shaping_phase0_probe -j
cmake --build build-gpu --target ef_gpu_interaction_broadphase_phase0_probe -j
cmake --build build-gpu --target ef_gpu_sensor_candidate_phase0_probe -j
cmake --build build-gpu --target ef_gpu_comm_candidate_phase0_probe -j
cmake --build build-gpu --target ef_gpu_visual_candidate_phase0_probe -j
```

Example probe runs:

```bash
./build-gpu/ef_gpu_visual_phase0_probe --frames 512 --objects 64 --envs 16 --history-steps 2048 --terrain off
./build-gpu/ef_gpu_visual_phase0_probe --frames 64 --objects 64 --envs 16 --terrain gpu
./build-gpu/ef_gpu_execution_observation_phase0_probe --frames 128 --envs 1024 --contacts 8 --rwr 4 --max-contacts 16 --max-rwr 8 --mission-mode nav_v2
./build-gpu/ef_gpu_flight_shaping_phase0_probe --frames 256 --envs 4096
./build-gpu/ef_gpu_interaction_broadphase_phase0_probe --worlds 16 --entities 1024 --queries 256 --cell-size 5000 --bucket-count 32768 --bucket-capacity 64
./build-gpu/ef_gpu_sensor_candidate_phase0_probe --worlds 16 --targets 1024 --sensors 256 --cell-size 5000 --bucket-count 32768 --bucket-capacity 64
./build-gpu/ef_gpu_comm_candidate_phase0_probe --worlds 16 --nodes 1024 --networks 2 --cell-size 10000 --bucket-count 32768 --bucket-capacity 64
./build-gpu/ef_gpu_visual_candidate_phase0_probe --worlds 16 --objects 1024 --cameras 64 --far-range 25000 --cell-size 5000 --bucket-count 32768 --bucket-capacity 64
```
