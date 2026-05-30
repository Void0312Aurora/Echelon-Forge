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

Shared support code for maintained diagnostics now starts to live in:

- [benchmark.py](benchmark.py)
  - Unified benchmark CLI. This is the primary single-benchmark entrypoint; prefer `--family ...`.
- [benchmarks/](benchmarks)
  - Maintained benchmark family implementations. New benchmark logic should land here, not in new top-level `benchmark_*_phaseN.py` files.
- [common.py](common.py)
  - Shared JSON IO, timing aggregation, and GPU runtime stats helpers for diagnostics/benchmark scripts.
- [run_benchmark_suite.py](run_benchmark_suite.py)
  - Optional configuration-driven suite runner built on top of the unified benchmark CLI and `family` dispatch.
- [cooperative_trajectory_base.py](cooperative_trajectory_base.py)
  - Shared cooperative trajectory env/model bootstrap, trace capture, and plotting helpers for maintained cooperative diagnostics.

Current maintained diagnostics:

- [leader_perf_probe.py](leader_perf_probe.py)
  - Quick leader-layer throughput probe for the maintained `auto`, `subproc`, `shared`, and `dummy` baselines.
- [ablate_visual_training_effect.py](ablate_visual_training_effect.py)
  - Automates a `visual_downsample` train/eval matrix for visual execution policies and aggregates end metrics by factor.
- [arma_proxy_backend_stub.py](arma_proxy_backend_stub.py)
  - Minimal line-protocol TCP stub for the local `game/` Arma bridge. It acknowledges `begin_session`, consumes `host_frame`, and emits synthetic `proxy_state` payloads for `echelon_bridge.dll`.
- [arma_proxy_backend_echelon_env.py](arma_proxy_backend_echelon_env.py)
  - `UniversalEnv`-backed line-protocol TCP backend for the same Arma bridge. It anchors backend truth to the Arma host-frame position/orientation while stepping authoritative flight state inside Echelon Forge.
- `spatial_query`
  - Compiled spatial-query vs legacy geometry benchmark.
- `scenario_compiler`
  - Scenario compiler cache / instantiate / load benchmark.
- `mission_runtime`
  - Mission runtime helper microbenchmark.
- `world_batch_runtime`
  - WorldBatchRuntime kernel-apply and step/read benchmark.
- `world_batch_vec_env`
  - WorldBatchVecEnv training-adapter benchmark.
- `policy_observation_bridge`
  - Policy-observation bridge benchmark.
- `visual_resolution`
  - Visual downsample sweep benchmark.
- `coarse_route_segments`
  - Coarse route-segment error benchmark.
- [diagnose_cooperative_trajectory.py](diagnose_cooperative_trajectory.py)
  - Unified cooperative trajectory replay/export CLI. Use `--task takeoff` or `--task takeoff_to_cruise` to emit task-specific PNG + JSON diagnostics from one maintained entrypoint.
- [diagnose_runway_drift_sweep.py](diagnose_runway_drift_sweep.py)
  - Parameterized takeoff ground-roll drift sweep used to quantify off-runway behavior across seeds, winds, and policy choices.
- [diagnose_takeoff_to_landing_trajectory.py](diagnose_takeoff_to_landing_trajectory.py)
  - Single-episode trajectory exporter for the continuous takeoff-to-landing task, with PNG + JSON outputs for scripted/model comparisons.

Recommended maintained entrypoint for multiple benchmarks:

- [run_benchmark_suite.py](run_benchmark_suite.py)
  - Optional preset runner for repeatable multi-job benchmark suites.
- [benchmark.py](benchmark.py)
  - Primary single benchmark entrypoint. Use `--family` to select the benchmark family.

Frozen experimental GPU helper phase-0 probes:

- [ef_gpu_visual_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_visual_phase0_probe.cpp)
  - C++ phase-0 GPU front-end probe for the visual path.
- [ef_gpu_execution_observation_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_execution_observation_phase0_probe.cpp)
  - C++ phase-0 GPU probe for batched execution-observation packing.
- [ef_gpu_flight_shaping_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_flight_shaping_phase0_probe.cpp)
  - C++ phase-0 GPU probe for batched `flight shaping` reward terms.
- [ef_gpu_interaction_broadphase_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_interaction_broadphase_phase0_probe.cpp)
  - C++ phase-0 GPU probe for interaction broadphase.
- [ef_gpu_sensor_candidate_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_sensor_candidate_phase0_probe.cpp)
  - C++ phase-0 GPU probe for sensor candidate generation built on the retained broadphase helper.
- [ef_gpu_comm_candidate_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_comm_candidate_phase0_probe.cpp)
  - C++ phase-0 GPU probe for communication candidate generation built on the retained broadphase helper.
- [ef_gpu_visual_candidate_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_visual_candidate_phase0_probe.cpp)
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

Run multiple maintained benchmarks from one config:

```bash
./.venv/bin/python tools/diagnostics/run_benchmark_suite.py \
  --config examples/config/diagnostics/benchmark_suite_runtime_phase14_mainline.json \
  --json-out /tmp/runtime_phase14_mainline.json
```

Run one benchmark family through the unified CLI:

```bash
./.venv/bin/python tools/diagnostics/benchmark.py \
  --family world_batch_vec_env \
  --n-envs 8 --steps 128 --reset-iters 24 --mission-obs-mode nav_v2 --action-mode full
```

Run the local Arma proxy backend stub:

```bash
./.venv/bin/python tools/diagnostics/arma_proxy_backend_stub.py \
  --host 127.0.0.1 \
  --port 8765 \
  --start-position 1200 3400 1500 \
  --speed-mps 220 \
  --log-requests
```

Run the env-backed Arma proxy backend:

```bash
./.venv/bin/python tools/diagnostics/arma_proxy_backend_echelon_env.py \
  --host 127.0.0.1 \
  --port 8765 \
  --scenario scenarios/stable_flight/stable_flight.json \
  --action-mode full \
  --mission-obs-mode basic
```

Show family-specific help:

```bash
./.venv/bin/python tools/diagnostics/benchmark.py \
  --family world_batch_vec_env \
  --family-help
```

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

Maintenance note:

- New maintained benchmark logic should extend `tools/diagnostics/benchmarks/` plus `benchmark_registry.py`.
- Do not add new phase-named top-level benchmark scripts.
- Cooperative trajectory diagnostics should extend `tools/diagnostics/diagnose_cooperative_trajectory.py` plus `cooperative_trajectory_base.py`, not reintroduce per-task wrapper scripts.
- Longer task-specific trajectory or sweep diagnostics should live here only if they remain maintained operational tools; otherwise archive them instead of leaving them under `tests/`.
