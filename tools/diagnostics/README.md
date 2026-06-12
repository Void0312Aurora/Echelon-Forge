# Tools Diagnostics README

`tools/diagnostics/` contains operator-facing probes, benchmarks, and matrix
checks that support the maintained CPU-mainline runtime and, when explicitly
requested, the frozen experimental GPU helper line.

Domain posture: diagnostics are still weighted toward air/execution and
cooperative/common runtime work. Naval entries are scoped to the listed station,
screen, and contact-evidence paths. Ground-domain movement, sensing, terrain,
fires, damage, and full runtime diagnostics are not maintained here yet; takeoff
ground-roll wording means runway-phase air/execution behavior.

Runtime posture: maintained diagnostics use `WorldBatchRuntime`,
`WorldBatchVecEnv`, or `CooperativeWorldBatchVecEnv` and align with the
runtime-facade mainline. Diagnostics that directly instantiate `UniversalEnv`
are archive/quarantine material, not active production or acceptance surfaces.

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

Current diagnostics and probes:

- [leader_perf_probe.py](leader_perf_probe.py)
  - Quick leader-layer throughput probe for the maintained `auto`, `subproc`, `shared`, and `dummy` baselines.
- [ablate_visual_training_effect.py](ablate_visual_training_effect.py)
  - Automates a `visual_downsample` train/eval matrix for visual execution policies and aggregates end metrics by factor.
- [air_combat_weapon_employment_process_probe.py](air_combat_weapon_employment_process_probe.py)
  - Scoped air-combat weapon-employment process probe for debug traces, lethality-chain rows, and hybrid action metrics through a batch=1 `WorldBatchVecEnv` adapter.
- [event_credit_head_probe.py](event_credit_head_probe.py)
  - Unified first-event credit-head diagnostic entry. Use `--mode offline_fit`
    for fixed-batch supervised fitting, or `--mode online_update` for
    update-path isolation across PPO, shared actor/features, and credit-head
    losses.
- [fire_timing_fault_localization_probe.py](fire_timing_fault_localization_probe.py)
  - Unified fire-timing fault-localization entry. Use `--mode structural_toy`
    for the abstract grouped-stopping toy, `--mode real_update` for real
    update-path checks, `--mode chain_breakpoint` for fixed-batch breakpoint
    attribution, or `--mode learnability_audit` for oracle fire-timing
    learnability checks.
- [arma_proxy_backend_stub.py](arma_proxy_backend_stub.py)
  - Minimal line-protocol TCP stub for the local `game/` Arma bridge. It acknowledges `begin_session`, consumes `host_frame`, and emits synthetic `proxy_state` payloads for `echelon_bridge.dll`.
- `spatial_query`
  - Compiled spatial-query vs legacy geometry benchmark.
- `scenario_compiler`
  - Scenario compiler cache / instantiate / load benchmark.
- `mission_runtime`
  - Mission runtime helper microbenchmark.
- `world_batch_vec_env`
  - WorldBatchVecEnv training-adapter benchmark.
- `policy_observation_bridge`
  - Policy-observation bridge benchmark.
- `air_combat_post_launch_assessment`
  - Air-combat post-launch assessment rollout benchmark.

- [diagnose_cooperative_trajectory.py](diagnose_cooperative_trajectory.py)
  - Unified cooperative trajectory replay/export CLI. Use `--task takeoff` or `--task takeoff_to_cruise` to emit task-specific PNG + JSON diagnostics from one maintained entrypoint.
- [flight_trajectory_diagnostics.py](flight_trajectory_diagnostics.py)
  - Unified flight trajectory diagnostic entry. Use `--mode takeoff_to_landing` for single-episode route/landing PNG + JSON export, or `--mode runway_drift_sweep` for parameterized ground-roll drift sweeps.
- [trace_training_nonfinite_source.py](trace_training_nonfinite_source.py)
  - Focused cooperative training NaN/Inf tracer. It reconstructs the maintained cooperative flow from `train.py`, patches finite-value probes into the loaded policy/algo, and stops with a JSON report.

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
  --n-envs 8 --steps 128 --reset-iters 24
```

Run the air-combat post-launch assessment benchmark through the same entrypoint:

```bash
./.venv/bin/python tools/diagnostics/benchmark.py \
  --family air_combat_post_launch_assessment \
  --episodes 3 --post-steps 240
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

Typical HEI-backed operator flow for the Arma bridge:

```bash
ssh -N -L 8765:127.0.0.1:8765 HEI
```

Then launch the local Arma side against the forwarded endpoint, for example
with the existing PowerShell helper in `ArmaOnly` mode plus
`-ReuseExistingBackend`.

The former repo-side `UniversalEnv`-backed Arma proxy backend is archived under
`tools/archive/`; it is no longer a maintained diagnostics entrypoint.

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
- Flight trajectory diagnostics should extend `tools/diagnostics/flight_trajectory_diagnostics.py --mode ...`, not add task-specific trajectory wrapper CLIs.
- Fire-timing diagnostics should extend `tools/diagnostics/fire_timing_fault_localization_probe.py --mode ...`, not add new air-combat fire-timing top-level probes.
- Longer task-specific trajectory or sweep diagnostics should live here only if they remain maintained operational tools; otherwise archive them instead of leaving them under `tests/`.
