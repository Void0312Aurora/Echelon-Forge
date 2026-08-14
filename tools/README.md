# Tools README

`tools/` now groups maintained scripts by function instead of keeping every entrypoint at top level.

## Domain Posture

- Most general eval examples here still target air/execution tasks; cooperative/common is covered by the maintained learned-policy and leader diagnostics paths.
- Active training, eval, and diagnostics tools use the runtime-facade/world-batch path. Direct `UniversalEnv` tools are retired outright, not parked in an in-tree archive.
- Naval station pre-fire entries have a maintained scoped gate in `tools/eval/naval_station_policy_eval.py`.
- Ground tasking/schema bootstrap does not yet have a maintained eval or diagnostic runner in `tools/`; do not infer full ground runtime support from this catalog.

## Layout

- `tools/eval/`
  - Model/scripted evaluation entrypoints plus shared eval helpers.
- `tools/diagnostics/`
  - Operator-facing probes, benchmarks, and matrix-style diagnostics.
- `tools/geometry/`
  - Review-only geometry extraction helpers for visualization-derived target
    proxies and human-auditable geometry packets.
- `tools/runners/`
  - Stable runners for JSON contract suites and similar maintained entrypoints.
- `tools/environment/`
  - Pinned environment/scenario data-generator adapters, export, and verification.
- `tools/maintenance/`
  - Workspace audit and cleanup helpers.

## Eval

- [eval_task.py](eval/eval_task.py)
  - Air/execution task evaluator for `stable_flight`, `takeoff_roll`, `centerline`, and `waypoint_nav` across `world_model` and `scripted` backends. It uses the maintained single-world WorldBatchRuntime path, not raw `UniversalEnv`.
- [policy_execution_eval.py](eval/policy_execution_eval.py)
  - Learned execution-policy evaluator for `single` and `cooperative` policies with mode-specific metrics. `single` requires `runtime.world_batch_vec_env=true` and uses WorldBatchRuntime; `cooperative` uses `CooperativeWorldBatchVecEnv`.
- [naval_station_policy_eval.py](eval/naval_station_policy_eval.py)
  - Scoped naval station cooperative gate for stationing, pre-fire ROE hold reward terms, and contact-evidence plumbing. This is not a learned-policy acceptance.
- [task_eval_driver.py](eval/task_eval_driver.py)
  - Shared implementation for single-agent task metrics and backend adapters.
- [eval_utils.py](eval/eval_utils.py)
  - Shared bootstrap, env construction, and stat formatting.
- [world_model_eval_utils.py](eval/world_model_eval_utils.py)
  - Shared checkpoint loading and recurrent world-model rollout helpers.
- [waypoint_eval_utils.py](eval/waypoint_eval_utils.py)
  - Shared waypoint mission-status parsing and geometry metrics.

## Diagnostics

- [benchmark.py](diagnostics/benchmark.py)
  - Unified benchmark CLI for maintained diagnostics families.
- [run_benchmark_suite.py](diagnostics/run_benchmark_suite.py)
  - Unified config-driven entrypoint for maintained benchmark suites under `tools/diagnostics/`.
- [arma_proxy_backend_stub.py](diagnostics/arma_proxy_backend_stub.py)
  - Minimal local TCP backend stub for the first-pass `@EchelonProxy` Arma bridge protocol.
- [diagnose_cooperative_trajectory.py](diagnostics/diagnose_cooperative_trajectory.py)
  - Unified cooperative trajectory replay/export CLI for `takeoff` and `takeoff_to_cruise`.
- [flight_trajectory_diagnostics.py](diagnostics/flight_trajectory_diagnostics.py)
  - Unified flight trajectory diagnostic entry for takeoff-to-landing trajectory export and runway drift sweeps.
- [leader_perf_probe.py](diagnostics/leader_perf_probe.py)
  - Maintained leader-layer throughput probe for `auto/subproc/shared/dummy`.
- [air_combat_weapon_employment_process_probe.py](diagnostics/air_combat_weapon_employment_process_probe.py)
  - Scoped air-combat weapon-employment process probe for debug traces, lethality-chain rows, and hybrid action metrics through a batch=1 `WorldBatchVecEnv` adapter.
- [event_credit_head_probe.py](diagnostics/event_credit_head_probe.py)
  - Unified first-event credit-head diagnostic entry for fixed-batch fitting and online update-path isolation.
- [fire_timing_fault_localization_probe.py](diagnostics/fire_timing_fault_localization_probe.py)
  - Unified fire-timing fault-localization entry for structural toy, real update-path, chain-breakpoint, learnability-audit, and legal-window launch-position sweep probes.
- [trace_training_nonfinite_source.py](diagnostics/trace_training_nonfinite_source.py)
  - Focused cooperative training NaN/Inf tracer that reconstructs the maintained cooperative flow and stops with a JSON report.
- [README.md](diagnostics/README.md)
  - Diagnostics catalog and scope notes.

## Geometry

- [airframe_geometry_review.py](geometry/airframe_geometry_review.py)
  - Generates review-only airframe geometry manifests from retained glTF audit
    assets. The current F-16 slice records source, hashes, axes, public-size
    scaling, and the gap between the visual outer-shape candidate and the
    existing axis-aligned damage boxes. It also emits first-pass low-fidelity
    outer-region candidates, component-binding reports, review-point distance
    diagnostics, an offline HTML packet, and top/side/front SVG overlays. It
    does not create runtime collision meshes or real aircraft-structure
    authority.

## Runners

- [run_scenario_contract.py](runners/run_scenario_contract.py)
  - Runs one or more JSON contracts from `tests/contracts/`, or a checked-in suite manifest such as `tests/smoke/ci_contract_suite.json`.
- [run_pytest_suite.py](runners/run_pytest_suite.py)
  - Runs a checked-in pytest suite manifest such as `tests/smoke/ci_smoke_suite.json` and fails early on stale path entries.
  - Suite entries may be directories, files, or pytest node IDs such as `tests/foo/test_bar.py::test_case`; node ID entries still validate the base path before invoking pytest.
- [run_contract_batches.py](runners/run_contract_batches.py)
  - Runs grouped JSON contract batches from `tests/contracts/` by `--group` (`chain`, `unit`, `route_generator`, `same_process`, `sim_kernel`), or all maintained groups by default. The `--default-group sim_kernel` convenience selects the `sim_kernel` group without spelling `--group`.
- [measure_test_coverage.py](runners/measure_test_coverage.py)
  - Generates retained Python `coverage` and optional C++ `gcovr` reports from a checked-in pytest suite manifest. Use a coverage-instrumented CMake build for C++ reports so Python tests exercise the instrumented `ef_py` binding instead of reporting doctest-only coverage.

## Environment Generation and Integration

- [arnis/README.md](environment/arnis/README.md)
  - Pinned Arnis `v3.0.0` plus the CMO patch behind one `prepare / export /
    verify` entrypoint. It emits continuous metric `arnis_cmo_bundle.v1` data
    before Minecraft quantization, runs CMO manifest/catalog validation, and
    provides explicitly non-runtime continuous-field and true-scale static-scene
    previews. Static placement is provenance-bound and unresolved roofs,
    bridges, or subsurface profiles remain held; no terrain runtime, movement,
    LOS, cover, or combat is released.

## Maintenance

- [redundancy_audit.py](maintenance/redundancy_audit.py)
  - Audits duplicate/temp-like workspace content.
- [cleanup_redundancy.py](maintenance/cleanup_redundancy.py)
  - Dry-run or apply cleanup for cache/temp artifacts.
- [isolate_repro_workspace.sh](maintenance/isolate_repro_workspace.sh)
  - Moves selected experiment/dataset directories aside to create a smaller repro workspace.
- [translate_docs_batch.py](maintenance/translate_docs_batch.py)
  - Audits bilingual coverage and batch-translates Markdown doc peers with an OpenAI-compatible API.
- [internal_code_governance](maintenance/internal_code_governance/)
  - Audits added production and documentation lines for work-tracking codes or
    opaque lettered-phase identifiers; CI blocks high-confidence source/runtime
    violations while documentation findings remain warnings during remediation.
## Retirement Register

`tools/archive/` no longer exists. Keeping retired one-shot probes in the
working tree costs review attention on every census and gives nothing that git
history does not already provide, so retirement now means deletion plus this
register. Recover any entry with `git show <commit>:<path>`.

### Retired 2026-08-14 — closed A2 maintenance-governance chain

The A2 candidate, source, release, and retained-artifact producers formed a
self-referential maintenance graph after the damage-model review had closed.
The one runtime invariant they protected now uses a small test-local fixture,
so keeping the generators, router, hash-pin checker, and their tests would only
preserve the closed workflow. The last complete tree is `c0e4f31f`.

| Path | Purpose | Recover |
| --- | --- | --- |
| `tools/maintenance/damage_model.py` | Unified router for the closed A2 governance workflow. | `git show c0e4f31f:tools/maintenance/damage_model.py` |
| `tools/maintenance/candidate_artifacts/` | Candidate scaffold and Stage B/C artifact producers. | `git ls-tree -r c0e4f31f -- tools/maintenance/candidate_artifacts` |
| `tools/maintenance/release_governance/` | Release-readiness and provenance gates for the candidate chain. | `git ls-tree -r c0e4f31f -- tools/maintenance/release_governance` |
| `tools/maintenance/source_governance/` | Source admission, payload, and rights-policy producers. | `git ls-tree -r c0e4f31f -- tools/maintenance/source_governance` |
| `tools/maintenance/retained_artifacts/` | Manifest/hash integrity checker for the retained A2 packet. | `git ls-tree -r c0e4f31f -- tools/maintenance/retained_artifacts` |

### Retired 2026-08-14 — CUDA-resident measurement toolchain

The CUDA-resident backend was promoted as an explicit opt-in maintained
backend, but its finite CP measurement campaign did not become a permanent
runtime dependency. The report generators, parsers, and native capture probes
were therefore deleted after the live backend contracts and parity tests were
separated from the frozen evidence package. The final integrated measurement
tree is recoverable from `2b4d3788`.

| Path | Purpose | Recover |
| --- | --- | --- |
| `tools/diagnostics/cuda_resident_*.py` | One-shot report generation, parsing, evidence validation, and campaign comparison. | `git ls-tree -r 2b4d3788 -- tools/diagnostics/cuda_resident_*.py` |
| `src/tools/experimental/cuda_resident/` | Native CUDA measurement and capture probes. | `git ls-tree -r 2b4d3788 -- src/tools/experimental/cuda_resident` |
| `tests/fixtures/runtime_profiles/cuda_resident_program_2/` | Pre- and post-promotion frozen measurement reports and decisions. | `git ls-tree -r 2b4d3788 -- tests/fixtures/runtime_profiles/cuda_resident_program_2` |

All entries below were retired at commit `3ac600a6` (the last commit in which
they exist), after a four-column reference audit found no reference from
`tests/`, CI, a maintained (Tier A/B) document, or another `tools/` entrypoint.

### Retired 2026-08-13 — `tools/archive/` (whole directory)

| Path | Purpose | Recover |
| --- | --- | --- |
| `tools/archive/README.md` | Scope note for the archived root-level probe collection. | `git show 3ac600a6:tools/archive/README.md` |
| `tools/archive/README.zh.md` | Chinese companion of the archive scope note. | `git show 3ac600a6:tools/archive/README.zh.md` |
| `tools/archive/analyze_cooperative_observation_scales.py` | Raw single-env observation-scale sampler built directly on `UniversalEnv`. | `git show 3ac600a6:tools/archive/analyze_cooperative_observation_scales.py` |
| `tools/archive/arma_proxy_backend_echelon_env.py` | Raw `UniversalEnv` Arma proxy backend, superseded by the maintained local stub. | `git show 3ac600a6:tools/archive/arma_proxy_backend_echelon_env.py` |
| `tools/archive/batch_api_probe.py` | Manual probe for the C++ batch preparation API. | `git show 3ac600a6:tools/archive/batch_api_probe.py` |
| `tools/archive/check_binding.py` | Manual `ef_py` binding member dump for human inspection. | `git show 3ac600a6:tools/archive/check_binding.py` |
| `tools/archive/coarse_route_segments.py` | Coarse route-segment rollout benchmark on raw `UniversalEnv` and direct policy loading. | `git show 3ac600a6:tools/archive/coarse_route_segments.py` |
| `tools/archive/diagnose_training_matrix.py` | Parser for the legacy `evaluate.py` text summary over small model/scenario matrices. | `git show 3ac600a6:tools/archive/diagnose_training_matrix.py` |
| `tools/archive/legacy_scripts/run_p2_diagnostic_matrix.sh` | Shell wrapper running the legacy P2 stage-A/stage-B diagnostic matrix. | `git show 3ac600a6:tools/archive/legacy_scripts/run_p2_diagnostic_matrix.sh` |
| `tools/archive/legacy_scripts/train_p2_aggressive.sh` | Shell wrapper for a one-off aggressive P2 training configuration. | `git show 3ac600a6:tools/archive/legacy_scripts/train_p2_aggressive.sh` |
| `tools/archive/legacy_test_diagnostics/diagnose_cruise_ood.py` | One-off cruise out-of-distribution episode classifier. | `git show 3ac600a6:tools/archive/legacy_test_diagnostics/diagnose_cruise_ood.py` |
| `tools/archive/legacy_test_diagnostics/diagnose_drop_physics.py` | One-off free-drop physics sanity dump against the C++ kernel. | `git show 3ac600a6:tools/archive/legacy_test_diagnostics/diagnose_drop_physics.py` |
| `tools/archive/legacy_test_diagnostics/diagnose_gear_damage.py` | One-off landing-gear damage-system check. | `git show 3ac600a6:tools/archive/legacy_test_diagnostics/diagnose_gear_damage.py` |
| `tools/archive/legacy_test_diagnostics/diagnose_physics.py` | One-off thrust/drag/friction dump read straight from C++. | `git show 3ac600a6:tools/archive/legacy_test_diagnostics/diagnose_physics.py` |
| `tools/archive/legacy_test_diagnostics/diagnose_reward_v2.py` | One-off investigation of an anomalous `ep_rew_mean`. | `git show 3ac600a6:tools/archive/legacy_test_diagnostics/diagnose_reward_v2.py` |
| `tools/archive/legacy_test_diagnostics/diagnose_takeoff_physics.py` | One-off takeoff-roll physics sanity dump. | `git show 3ac600a6:tools/archive/legacy_test_diagnostics/diagnose_takeoff_physics.py` |
| `tools/archive/legacy_test_diagnostics/diagnose_termination.py` | One-off early-termination cause breakdown for training episodes. | `git show 3ac600a6:tools/archive/legacy_test_diagnostics/diagnose_termination.py` |
| `tools/archive/legacy_test_diagnostics/diagnose_terrain.py` | One-off terrain-classification check at the spawn point. | `git show 3ac600a6:tools/archive/legacy_test_diagnostics/diagnose_terrain.py` |
| `tools/archive/legacy_test_diagnostics/diagnose_training.py` | One-off training-environment health check. | `git show 3ac600a6:tools/archive/legacy_test_diagnostics/diagnose_training.py` |
| `tools/archive/visual_resolution.py` | Visual downsample benchmark backed by raw `UniversalEnv`. | `git show 3ac600a6:tools/archive/visual_resolution.py` |
| `tools/archive/world_batch_runtime.py` | Raw `WorldBatchRuntime` benchmark predating the maintained runtime families. | `git show 3ac600a6:tools/archive/world_batch_runtime.py` |
| `tools/archive/world_batch_vec_env_benchmark.py` | Vec-env throughput benchmark predating the current diagnostics layout. | `git show 3ac600a6:tools/archive/world_batch_vec_env_benchmark.py` |

### Retired 2026-08-13 — one-shot geometry renderers

Both scripts hardcode a single sealed review packet under
`docs/systems/effects/reviews/f16c_target_geometry_20260614/` and pin a
`GENERATED_ON = "2026-06-15"` render date. The packet they produced is sealed,
so re-running them is not a maintained workflow.

| Path | Purpose | Recover |
| --- | --- | --- |
| `tools/geometry/target_geometry_lethality_probability_matrix_plot.py` | Rendered the F-16C lethality probability matrices for the 20260614 review packet. | `git show 3ac600a6:tools/geometry/target_geometry_lethality_probability_matrix_plot.py` |
| `tools/geometry/target_geometry_proxy_independent_variable_heatmap.py` | Rendered proxy-only independent-variable heatmaps for the same packet. | `git show 3ac600a6:tools/geometry/target_geometry_proxy_independent_variable_heatmap.py` |

## Common Usage

Run contracts:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/chain/loader_command_chain_takeoff_to_landing.json
```

Run multiple contracts:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py --spec \
  tests/contracts/route_generator/route_generator_v1.json \
  tests/contracts/unit/config/env_config_resolution.json
```

Generate retained smoke coverage reports:

```bash
cmake -S . -B build-coverage -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_C_FLAGS="--coverage -O0 -g" \
  -DCMAKE_CXX_FLAGS="--coverage -O0 -g" \
  -DCMAKE_EXE_LINKER_FLAGS="--coverage" \
  -DCMAKE_SHARED_LINKER_FLAGS="--coverage"
cmake --build build-coverage --target ef_core ef_py ef_test -j4
ctest --test-dir build-coverage -R ef_test_all --output-on-failure
source tools/maintenance/cmo_env.sh
CMO_BUILD_DIR=build-coverage cmo_python tools/runners/measure_test_coverage.py \
  --suite tests/smoke/ci_smoke_suite.json \
  --output-dir coverage-reports \
  --cpp-object-dir build-coverage
```

Run the scoped naval station policy gate:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/eval/naval_station_policy_eval.py \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json \
  --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json \
  --steps 1200
```

Audit and dry-run cleanup:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/maintenance/redundancy_audit.py --roots tests tools scenarios
cmo_python tools/maintenance/cleanup_redundancy.py --roots tests tools --include_named_tmp_dirs
```

Probe leader-layer throughput:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/leader_perf_probe.py \
  --scenario scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json \
  --train_config examples/config/training/p7_leader_layer_c2_reporting_generalization_fast_v1.json \
  --n_envs 4 \
  --leader_steps 24 \
  --vec_backend shared
```

Run a maintained benchmark suite from one config:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/run_benchmark_suite.py \
  --config examples/config/diagnostics/benchmark_suite_runtime_phase14_mainline.json
```

Run one maintained benchmark family:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/benchmark.py \
  --family world_batch_vec_env \
  --n-envs 8 --steps 128 --reset-iters 24
```

Run the air-combat post-launch assessment benchmark through the same maintained entrypoint:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/benchmark.py \
  --family air_combat_post_launch_assessment \
  --episodes 3 --post-steps 240
```

Replay one cooperative trajectory diagnostic:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/diagnose_cooperative_trajectory.py \
  --task takeoff \
  --scenario scenarios/takeoff/cooperative_interval_takeoff_departure_navv2_train_v1.json \
  --train_config examples/config/training/active/cooperative_interval_takeoff_departure_nav_v1.json \
  --model experiments/example/checkpoints/model.zip \
  --output /tmp/cooperative_takeoff_trace.png
```

## Maintenance Guidance

- New task-metric eval behavior should extend `tools/eval/eval_task.py` and `tools/eval/task_eval_driver.py` on maintained runtime paths, not add per-task wrapper scripts.
- New maintained learned-policy evaluation behavior should extend `tools/eval/policy_execution_eval.py` and the shared policy-loading helpers in `tools/eval/sb3_eval_base.py`, not reintroduce split single/cooperative wrappers.
- Shared eval bootstrap should come from `tools.eval.eval_utils`, not copied setup blocks.
- JSON-contract entrypoints should prefer `tools/runners/run_scenario_contract.py` over one-off wrappers.
- Maintained diagnostics should prefer `tools/diagnostics/benchmark.py` for single benchmark families and `tools/diagnostics/run_benchmark_suite.py` for multi-job suites.
- Fire-timing diagnostics should extend `tools/diagnostics/fire_timing_fault_localization_probe.py --mode ...`, not add new air-combat fire-timing top-level probes.
- Flight trajectory diagnostics should extend `tools/diagnostics/flight_trajectory_diagnostics.py --mode ...`, not add task-specific trajectory wrapper CLIs.
- Cooperative trajectory diagnostics should extend `tools/diagnostics/diagnose_cooperative_trajectory.py` and `tools/diagnostics/cooperative_trajectory_base.py`, not add task-specific wrapper CLIs.
- Ad hoc probes and matrix sweeps belong under `tools/diagnostics/`.
- Cleanup/audit helpers belong under `tools/maintenance/`.
- Retire a scratch script by deleting it and adding a Retirement Register row, not by moving it into an in-tree archive directory.
