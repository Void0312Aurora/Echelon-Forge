<!-- Machine-translated draft generated on 2026-05-18 from docs/task/diagnostics_eval/diagnostics_modularization_20260515.zh.md. Review before treating this file as authoritative. -->

# Diagnostics Consolidation and Modularization Plan

Status: Phase 1, Phase 2, Phase 3, Phase 4 completed.

Date: `2026-05-15`

## 1. Background

`tools/diagnostics/` currently carries multiple responsibilities:

- Performance benchmarks for runtime / compiler / env adapter
- Training numerical issues and non-finite tracking
- Specialized trajectory diagnostics and visualization
- Small-scale train/eval matrices and probes

The directory structure itself is reasonable, but the number of scripts and duplication of implementation has grown noticeably. Currently, there are about 16 Python scripts in this directory, totaling approximately 7k lines. If we continue with the approach of "creating a new standalone script for each problem," maintenance costs will continue to rise.

## 2. Confirmed Findings

### 2.1 The directory's role is not the problem; the issue is the lack of a shared base

Most scripts in `tools/diagnostics/` are not formal product entry points; rather, they are:

- Probes that operators can manually trigger
- Benchmarks based on local checkpoints / builds
- Specialized diagnostics aimed at human-readable summaries rather than stable test assertions

Therefore, they are unsuitable for simply moving back to the repo root, nor for merging everything into a single CLI.

The problem lies in:

- Identical repo bootstrap, path resolution, JSON output, and timing aggregation are repeatedly implemented across multiple scripts
- This duplication has not been consolidated into a shared base
- Signs of "the same type of helper function being copied more than twice" have already started to appear

### 2.2 Confirmed Duplication Clusters

#### A. Benchmark bootstrap / JSON output duplication

The following benchmark families each implement their own `json_out` output and path creation:

- `scenario_compiler`
- `world_batch_runtime`
- `world_batch_vec_env`
- `visual_resolution`
- `coarse_route_segments`
- `analyze_cooperative_observation_scales.py`

In addition, several scripts repeatedly implement:

- Repo root injection
- `ensure_repo_imports()`
- `resolve_repo_path()` / `os.path.abspath()` combinations

#### B. Timing aggregation duplication

The following implementations each implement their own timing dict merge/average:

- `leader_perf_probe.py`
- `world_batch_vec_env`

The semantics of this logic are very similar and should be extracted into a shared utility.

#### C. GPU runtime stats duplication

The following benchmark families essentially copy the same set of GPU runtime stats reading logic:

- `policy_observation_bridge`
- `world_batch_vec_env`

Involving:

- `_gpu_device_info_dict()`
- `_visual_stats_dict()`
- `_flight_shaping_stats_dict()`

#### D. Small JSON config loading duplication

The following implementations each implement their own local `_load_json()`:

- `coarse_route_segments`
- `analyze_cooperative_observation_scales.py`

This capability is semantically similar to `load_json_config()` in `tools/eval/sb3_eval_base.py`, but the current directory does not reuse it.

### 2.3 Areas Not Directly Addressed in This Round

This round does **not**:

- Forcefully merge all benchmarks into a single CLI
- Rewrite `trace_training_nonfinite_source.py`
- Merge `leader_perf_probe.py` into phase benchmarks
- Rewrite the chart semantics of cooperative trajectory diagnostics

Reasons:

- Although these scripts have boilerplate duplication, their business logic varies significantly
- Forced merging would significantly increase regression risk
- At this stage, the higher benefit is "extracting the base + partial migration"

## 3. Phased Freeze Plan

### 3.1 Phase 1: Diagnostics Common Base Extraction

Goals:

- Establish reusable shared utility modules for `tools/diagnostics/`
- First, consolidate low-risk, highly duplicated foundational capabilities

Freeze scope:

- Repo/bootstrap common helpers
- JSON config loading
- JSON output persistence
- Timing dict merge/average
- GPU runtime stats reading

Proposed addition:

- `tools/diagnostics/common.py`

Acceptance criteria:

- The new shared module must cover the duplicated logic of at least 4 existing scripts
- Must not change the core output schema of existing benchmarks

Implementation results:

- Added [tools/diagnostics/common.py](../../../tools/diagnostics/common.py)
- Consolidated shared capabilities:
  - JSON config loading
  - JSON output persistence
  - Timing dict merge/average
  - GPU / visual / flight-shaping runtime stats

### 3.2 Phase 2: Initial Benchmark / Probe Migration

Goals:

- Migrate the first batch of highly duplicated scripts to the shared base

Freeze scope:

- `world_batch_vec_env`
- `policy_observation_bridge`
- `world_batch_runtime`
- `scenario_compiler`
- `visual_resolution`
- `coarse_route_segments`
- `analyze_cooperative_observation_scales.py`
- `leader_perf_probe.py`

Acceptance criteria:

- Old CLI parameters remain compatible
- `--help` works
- `py_compile` works

Implementation results:

- Migrated to shared base / family implementation layer:
  - [tools/diagnostics/benchmarks/world_batch_vec_env.py](../../../tools/diagnostics/benchmarks/world_batch_vec_env.py)
  - [tools/diagnostics/benchmarks/policy_observation_bridge.py](../../../tools/diagnostics/benchmarks/policy_observation_bridge.py)
  - [tools/diagnostics/leader_perf_probe.py](../../../tools/diagnostics/leader_perf_probe.py)
  - [tools/diagnostics/benchmarks/scenario_compiler.py](../../../tools/diagnostics/benchmarks/scenario_compiler.py)
  - [tools/diagnostics/benchmarks/world_batch_runtime.py](../../../tools/diagnostics/benchmarks/world_batch_runtime.py)
  - [tools/diagnostics/benchmarks/visual_resolution.py](../../../tools/diagnostics/benchmarks/visual_resolution.py)
  - [tools/diagnostics/benchmarks/coarse_route_segments.py](../../../tools/diagnostics/benchmarks/coarse_route_segments.py)
  - [tools/diagnostics/analyze_cooperative_observation_scales.py](../../../tools/diagnostics/analyze_cooperative_observation_scales.py)

Completed smoke tests:

- `python -m py_compile tools/diagnostics/common.py ...`
- `./.venv/bin/python tools/diagnostics/benchmark.py --family world_batch_vec_env --family-help`
- `./.venv/bin/python tools/diagnostics/benchmark.py --family policy_observation_bridge --family-help`
- `./.venv/bin/python tools/diagnostics/leader_perf_probe.py --help`

Current known environment limitations:

- The `ef_py` bound to the current workspace lacks `ConditionalObjectiveProperty`
- Therefore, the following scripts fail before `--help` when importing `scenario_compiler` / `UniversalEnv`, which is not a behavioral change introduced by this refactoring:
  - `scenario_compiler`
  - `analyze_cooperative_observation_scales.py`

### 3.3 Phase 3: Documentation Backfill and Future Candidate Organization

Goals:

- Update `tools/diagnostics/README.md`
- Document areas that have been consolidated and those still pending

Current progress:

- [tools/diagnostics/README.md](../../../tools/diagnostics/README.md) has been supplemented with shared base description
- Completed tail-end organization for this round:
  - `tools/diagnostics/diagnose_training_matrix.py` has been demoted and migrated to [tools/archive/diagnose_training_matrix.py](../../../tools/archive/diagnose_training_matrix.py)
  - `tools/diagnostics/sanity_check.py` has been consolidated into the formal runtime test [tests/runtime/test_kernel_observation_sanity.py](../../../tests/runtime/test_kernel_observation_sanity.py)

Future candidates:

- Extract a second-layer base for subprocess/matrix-type tools
- Add clearer deprecation notes for archived tools as needed
- Continue consolidating repo/bootstrap boilerplate

### 3.4 Phase 4: Benchmark Configuration-Driven Entry Point

Goals:

- Avoid requiring users to remember a large number of benchmark script names
- Establish "multiple benchmarks sharing a single configuration entry point" as the recommended usage

Freeze scope:

- Add a generic benchmark suite runner
- Provide at least one example suite configuration
- Update documentation to preferentially recommend the generic entry point

Explicitly not done:

- Immediately delete existing benchmark implementation scripts
- Rewrite the internal logic of each benchmark in this phase

Implementation results:

- Added [tools/diagnostics/run_benchmark_suite.py](../../../tools/diagnostics/run_benchmark_suite.py)
- Added example configuration [examples/config/diagnostics/benchmark_suite_runtime_phase14_mainline.json](../../../examples/config/diagnostics/benchmark_suite_runtime_phase14_mainline.json)
- README and tool overview have been switched to preferentially recommend the configuration-driven entry point

Completed smoke tests:

- `python -m py_compile tools/diagnostics/run_benchmark_suite.py`
- `./.venv/bin/python tools/diagnostics/run_benchmark_suite.py --help`
- `./.venv/bin/python tools/diagnostics/run_benchmark_suite.py --config examples/config/diagnostics/benchmark_suite_runtime_phase14_mainline.json --fail-fast`

Smoke test observations:

- `spatial_query_phase1` executes successfully under the suite runner
- `world_batch_phase4` fails because the current workspace's `ef_py` lacks `ConditionalObjectiveProperty`
- This indicates that the generic entry point itself is usable; the current failure is due to environment dependencies of specific benchmarks, not the suite runner

## 4. Documentation Constraints

This document is the only freeze plan document for the modularization effort of `tools/diagnostics` in this round.

Requirements for future work:

- First, backfill this document; do not add additional parallel plan documents
- If specialized documentation is added, it should only record experimental details and not duplicate the role of phased planning.
