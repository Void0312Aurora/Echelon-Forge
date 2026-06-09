<!-- Machine-translated draft generated on 2026-05-18 from docs/task/diagnostics_eval/diagnostics_benchmark_cli_convergence_20260515.zh.md. Review before treating this file as authoritative. -->

# Diagnostics Benchmark CLI Consolidation Plan

Status: Phase 1, Phase 2, Phase 3 completed; only incremental cleanup remains.

Date: `2026-05-15`

## 1. Background

The benchmarks in `tools/diagnostics/` were previously split into several independent scripts according to historical phases, for example:

- `spatial_query`
- `scenario_compiler`
- `mission_runtime`
- `world_batch_runtime`
- `world_batch_vec_env`
- `policy_observation_bridge`

This structure was convenient for rapid validation of specific topics in the early project phase, but over time two obvious issues arose:

- "Phase numbers" leaked into the official entry point layer, and each new phase tended to add another new script.
- Users had to memorize too many script names instead of remembering the capability boundary of a single unified benchmark CLI.

The recently added `run_benchmark_suite.py` solved the problem of "unified invocation of multiple benchmarks". After this round of consolidation, it has been switched to a unified entry point based on family distribution, no longer using phase script paths as part of the formal structure.

## 2. Findings Confirmed

### 2.1 The purpose of benchmarks is performance / behavioral regression, not displaying phase names

The common goals of these benchmarks are:

- Compare speed between old and new implementations
- Compare numerical / behavioral drift between old and new implementations
- Preserve regression baselines for runtime/compiler/vec-env/bridge refactoring

Therefore, "phase1/2/3/4" is more suitable as historical source or metadata of benchmark families, and should no longer dominate the naming of the official CLI.

### 2.2 What can be unified is the entry point, not all measurement logic

These benchmarks measure different objects:

- spatial query microbench
- scenario compiler / instantiate / load path
- mission runtime helper microbench
- world batch runtime kernel apply / step-read
- world batch vec env rollout adapter
- policy-observation bridge on/off comparison

Thus, we should not force all implementations into one monolithic script. But we can unify:

- One official benchmark CLI
- A set of mode / family selection methods
- A shared JSON output and parameter override method

### 2.3 Boundaries of this consolidation round

The actual work completed in this round focuses on the benchmark CLI / family implementation layer consolidation, without:

- Rewriting the core measurement implementation of each benchmark
- Batch rewriting the core measurement implementation of each benchmark
- Handling all old documentation historical links at once

Reasons:

- Establishing a stable official CLI is more important
- Establishing a stable official CLI is more important
- The family implementation layer and official entry point should be consolidated first; backfilling historical documentation can be deferred

## 3. Staged Freeze Plan

### 3.1 Phase 1: Unified benchmark CLI design freeze

Goal:

- Clarify the responsibility boundary of one official benchmark CLI
- Downgrade "phase" from entry point names to internal family / mode metadata

Freeze scope:

- Official entry point naming
- Family / mode parameter design
- Compatibility strategy with existing scripts

Freeze decisions:

- The new official entry point uses `tools/diagnostics/benchmark.py`
- Use `--family` to select a benchmark family, for example:
  - `spatial_query`
  - `scenario_compiler`
  - `mission_runtime`
  - `world_batch_runtime`
  - `world_batch_vec_env`
  - `policy_observation_bridge`
  - `visual_resolution`
- Old `benchmark_*_phaseN.py` scripts are no longer the preferred entry point and will be deleted directly later

### 3.2 Phase 2: Implement unified benchmark CLI and migrate family implementations

Completed:

- Established `tools/diagnostics/benchmark.py` as a unified single benchmark entry point
- Established `tools/diagnostics/benchmark_registry.py` to lazy-load implementation modules by family
- Official benchmark implementations moved to `tools/diagnostics/benchmarks/`
- Temporary compatibility shims have completed their transition mission and will be deleted directly

Verification results:

- `--help` on the new CLI works correctly
- Family distribution works correctly
- Old parameters are still accessible through family implementations

### 3.3 Phase 3: Documentation switch and old entry point deprecation

Goal:

- README and tools overview switch to the new official benchmark CLI
- Old `phase` benchmark scripts degraded to compatibility layer or internal backend

Completed:

- README and `tools/README.md` now prioritize recommending `benchmark.py --family ...`
- `run_benchmark_suite.py` now takes `family` as a first-class input, no longer requiring script paths
- Job names in suite examples have been changed to family names, no longer reinforcing the `phaseN` concept

## 4. Documentation Constraints

## 5. Current Freeze Conclusions

- Only two official entry points remain:
  - `tools/diagnostics/benchmark.py`
  - `tools/diagnostics/run_benchmark_suite.py`
- Official implementation layer resides in `tools/diagnostics/benchmarks/`
- `tools/diagnostics/benchmark_*_phaseN.py` scripts are no longer retained
- For future benchmark additions, a new family implementation should be added, not a new top-level `phaseN` script

This document is the only freeze plan document for the benchmark CLI consolidation effort.
