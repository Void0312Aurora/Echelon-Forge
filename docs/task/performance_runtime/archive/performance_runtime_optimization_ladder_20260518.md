# Runtime Performance Optimization Ladder

Status: `2026-05-18` active planning freeze.  
Scope: runtime/performance follow-on after the current realism/fidelity freeze.

## 1. Why This Subproject Exists

The current decision is:

- freeze the realism/fidelity deepening line temporarily;
- stop treating deeper realism as the default next investment;
- move the active mainline toward runtime performance measurement and
  optimization.

That shift requires one thing first: a stable rule set for what counts as
implementation optimization, what already counts as algorithm optimization, and
what crosses into approximation or semantic tradeoff territory.

This document is that rule set.

## 2. Working Assumptions

1. Realism is in maintenance mode, not expansion mode, unless a correctness bug
   forces us back into it.
2. Performance work must stay benchmark-driven; no optimization branch should
   be justified by intuition alone.
3. The default escalation order is:

```text
Level 1: implementation optimization
  -> Level 2: equivalent algorithm optimization
  -> Level 3: approximate optimization
```

## 3. Level Definitions

### 3.1 Level 1: Implementation Optimization

Definition:

- Keep the same simulation/task semantics.
- Keep the same externally visible task contract.
- Keep the same logical computation chain.
- Reduce overhead from import order, Python dispatch, allocation, conversion,
  repeated sync, repeated refresh, buffer churn, and avoidable serialization.

Typical forms:

- removing duplicated hot-path work;
- reusing buffers or caches that already exist logically;
- flattening multiple exact API calls into one existing exact batch call;
- reducing Python `dict`/`list`/`numpy` materialization overhead;
- fixing wrong entrypoint/import behavior that forces a slower or stale path.

Non-goal:

- Level 1 is not allowed to change what is computed, only how efficiently the
  current chain is executed.

### 3.2 Level 2: Equivalent Algorithm Optimization

Definition:

- Preserve the task contract and target semantics;
- but change the compute organization or algorithmic structure to get the same
  result more efficiently.

Typical forms:

- replacing per-entity evaluation with exact batched evaluation;
- switching a legacy path to an exact compiled path;
- exact incremental recomputation with explicit invalidation rules;
- changing data structures or traversal strategy while keeping equivalent outputs.

Required evidence:

- before/after benchmark comparison;
- regression checks for the affected task contract;
- explicit note that semantics are intended to remain equivalent.

### 3.3 Level 3: Approximate Optimization

Definition:

- Allow controlled semantic drift or fidelity loss in exchange for runtime gain.

Typical forms:

- lowering update frequencies;
- reducing observation breadth or precision;
- approximating visual/track/sensor products;
- using lower-precision or reduced-resolution products that change observable results.

Required evidence:

- explicit approval that an approximation is acceptable;
- a stated drift budget or acceptance boundary;
- benchmark plus behavior-quality comparison.

## 4. Where Parameter Tuning Belongs

Parameter tuning is not a separate optimization level by itself.

It belongs to different levels depending on what the knob changes:

- `worker_threads`, exact backend selection, or exact batching toggles:
  usually Level 1 supporting work.
- parameters that only unlock an already-equivalent compiled path:
  usually Level 2 supporting work.
- parameters that reduce fidelity, cadence, or observation content:
  Level 3.
- reward weights, mission thresholds, or scenario difficulty settings:
  usually not runtime optimization at all; they are task-design changes unless
  they are explicitly being used as an approximation strategy.

## 5. Escalation Rules

1. Measure first.
   Every optimization discussion should start from a benchmark family, scenario,
   or timing field such as `obs_build_ms`, `state_read_ms`, or
   `behavior_update_ms`.
2. Exhaust Level 1 first on the active hot path.
   If the cost is still dominated by Python assembly, repeated refresh, or
   redundant exact work, do not jump to approximate ideas.
3. Promote to Level 2 only when the remaining bottleneck is structural.
   Example: exact per-slot logic is still too expensive even after
   implementation cleanup.
4. Promote to Level 3 only when Level 1 and Level 2 are insufficient relative
   to the project time budget.
5. Every Level 3 proposal must say exactly what semantics may drift.

## 6. Current Mapping For This Repo

### 6.1 Current Level-1 Bucket

- benchmark/entrypoint correctness;
- hot-path Python allocation and packing cleanup;
- duplicate visual/observation refresh removal;
- exact batch API usage cleanup inside the existing runtime contract;
- `step_info`/info-materialization discipline on the hot path.

### 6.2 Current Level-2 Bucket

- exact batched step-evaluation preparation;
- broader compiled observation/reward export paths;
- exact incremental data-product recomputation;
- larger structural batching of state read / reward / info export.

### 6.3 Current Level-3 Bucket

- lower visual/track refresh rates as a performance-first choice;
- reduced contact counts or observation breadth for speed;
- approximate or decimated sensor/mission products;
- reduced precision paths that change task-visible outputs.

## 7. Current Default Order

The current repo-level order is:

1. keep benchmark and runtime entrypoints correct;
2. do Level-1 implementation optimization on the active runtime chain;
3. only then decide whether an exact algorithm redesign is still needed;
4. only then discuss approximation.

The companion analysis document for the present Level-1 step is:

- [performance_runtime_level1_implementation_analysis_20260518.md](performance_runtime_level1_implementation_analysis_20260518.md)
