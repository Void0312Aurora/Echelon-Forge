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
- [diagnose_training_matrix.py](/home/void0312/CMO/tools/diagnostics/diagnose_training_matrix.py)
  - Runs a small evaluation matrix across model/scenario pairs and extracts headline metrics from evaluator output.
- [sanity_check.py](/home/void0312/CMO/tools/diagnostics/sanity_check.py)
  - Performs a low-level kernel/API sanity probe against a spawned unit.
