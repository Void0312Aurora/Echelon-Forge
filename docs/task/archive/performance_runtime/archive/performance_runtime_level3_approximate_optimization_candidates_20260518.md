# Level-3 Approximate Optimization Candidate Set

Status: `2026-05-18` cautious planning draft.  
Scope: after the current Level-1 and Level-2 exact lines reach the end of
their active candidate pool, this document defines the current Level-3
approximate candidate set, drift budgets, and stricter stop rules for the
runtime-performance line.

Related documents:

- [runtime performance optimization ladder](performance_runtime_optimization_ladder_20260518.md)
- [level-2 equivalent algorithm candidate set](performance_runtime_level2_equivalent_algorithm_candidates_20260518.md)
- [level-1 runtime optimization taskboard](performance_runtime_level1_taskboard_20260518.md)

---

## 1. Purpose

This document does not reopen exact optimization by default.

It answers three narrower questions:

1. whether the current runtime-performance line is now allowed to discuss
   approximation at all;
2. which approximate candidates are even eligible to enter work;
3. what drift boundaries and stop rules must be obeyed to keep the line
   controlled and reversible.

Here, “Level 3” means:

- runtime gain may come from explicitly accepted task-visible drift;
- every candidate must say exactly which outputs may drift;
- every candidate must keep a clean exact fallback path;
- no approximation may silently alter reward, termination, safety, or
  kernel-visible control semantics unless that drift is explicitly named and
  approved.

## 2. Why Level 3 Is Now Allowed

The current line has now met the threshold to discuss Level 3 cautiously:

1. Level 1 produced the first confirmed runtime gains and then moved into
   diminishing-return territory;
2. the currently defined Level-2 candidate pool has been consumed:
   `L2-BEHAV-01` frozen, `L2-BEHAV-02` frozen, `L2-EVAL-01` completed, and
   `L2-NAV-01` stands as an earlier exact winning baseline;
3. remaining hotspots still exist, but further exact work is no longer the
   default best use of time without defining a new exact candidate set first;
4. the project has already spent substantial time on the exact line, so future
   runtime work must become more selective.

The default conclusion is therefore:

```text
Level-3 approximate optimization may now be discussed,
but only as opt-in, benchmark-driven, reversible, single-candidate experiments.
```

## 3. Current Level-3 Candidate Pool

The following candidates are ordered from “lowest semantic risk” to “highest
semantic risk that is still discussable.”

### L3-VIS-01: visual observation cadence / resolution reduction

Priority: `P0`

Goal:

- reduce visual-path runtime cost by refreshing visual observations less often,
  reusing the last exact frame between refreshes, and/or increasing the policy
  downsample factor on approved surfaces.

Why this is here:

- visual observations are naturally isolated from reward, termination, and
  command-chain semantics;
- this is the cleanest approximate line because it changes only the policy
  input tensor on `include_visual=True` surfaces;
- the repo already has visual cache/update machinery, so the approximation can
  stay local and reversible.

Allowed approximation changes:

- explicit `visual_update_interval > 1` as a performance-first choice;
- reuse of the last exact visual frame between refresh steps;
- larger visual downsample factors on approved policy surfaces.

Not allowed:

- no changes to non-visual observation channels;
- no changes to reward, termination, mission status, or kernel state;
- no hidden cadence change when `include_visual=False`.

Default drift budget:

- only the `visual` tensor may drift;
- staleness budget and downsample factor must be stated per experiment;
- all non-visual outputs must remain exact.

### L3-OBS-01: contact / RWR observation breadth reduction

Priority: `P1`

Goal:

- reduce policy-observation size and assembly cost by exporting fewer contact
  and/or RWR entries, using a deterministic ranking rule and zero-filled tails.

Why this is here:

- `obs_build` remains a visible runtime slice even after exact cleanup;
- observation breadth is a direct but bounded approximation lever that does not
  require touching kernel state or reward computation;
- it can be toggled at the policy-facing observation boundary.

Allowed approximation changes:

- fixed lower `max_contacts` and/or `max_rwr` budgets on approved surfaces;
- deterministic top-`K` retention by explicit ranking rule such as threat,
  range, confidence, or priority score;
- zero-filled omitted tails to preserve tensor shape contracts where needed.

Not allowed:

- no approximation of truth state, instrument state, reward, or termination;
- no nondeterministic eviction rule;
- no silent change of ranking logic without documentation.

Default drift budget:

- only `contacts` and `rwr` channels may omit low-priority entries;
- mission, reward, termination, and command outputs must remain exact;
- the retained `K` and ranking rule must be stated before implementation.

### L3-PREC-01: policy-facing low-precision export path

Priority: `P1`

Goal:

- reduce bandwidth, bridge, and policy-input cost by exporting selected
  policy-facing tensors in lower precision such as `bf16` or `fp16`, after the
  exact runtime products have already been computed.

Why this is here:

- the remaining runtime line includes observation/export cost, not only kernel
  compute;
- lower precision may help especially on GPU-facing policy paths without
  forcing approximation into the exact runtime core;
- this candidate is easier to contain than cadence changes on control logic.

Allowed approximation changes:

- lower-precision export for policy-facing tensors such as `visual`,
  `mission`, `contacts`, `rwr`, or full flattened policy batches;
- lower-precision bridge paths on GPU-oriented surfaces where supported.

Not allowed:

- no lower precision inside kernel state evolution;
- no lower precision inside reward, safety, termination, or command-sync logic;
- no hidden dtype drift on exact reference paths.

Default drift budget:

- only policy-facing exported tensors may quantize;
- exact runtime state and task outcomes must remain exact;
- dtype change and affected tensors must be declared before implementation.

### L3-MISS-01: mission / auxiliary observation cadence reduction

Priority: `P2`

Goal:

- reduce mission-observation and auxiliary-info cost by refreshing selected
  policy-facing fields less often or only on change.

Why this is here:

- after tail tightening, mission and auxiliary observation materialization may
  still matter on some surfaces;
- however, this is semantically riskier than visual-only or breadth-only
  approximation because these channels influence navigation and policy control.

Allowed approximation changes:

- explicit refresh cadence reduction for policy-facing mission or step-info
  fields;
- explicit change-only update rules for selected observation subchannels.

Not allowed:

- no reduced freshness on kernel-visible mission command state;
- no reduced cadence for reward, termination, or safety logic;
- no silent reuse of stale mission products on exact reference surfaces.

Default drift budget:

- only named policy-facing mission/aux fields may become stale;
- maximum staleness must be stated in steps;
- reward, termination, and command semantics must remain exact.

Current restriction:

- this is not a default first approximate candidate;
- it may start only after safer candidates fail to meet the time-budget need.

### Reserved but not active: behavior / command cadence reduction

Status: do not enter the active Level-3 candidate set.

Reason:

- reducing behavior-update cadence or command-sync cadence directly changes the
  freshness of kernel-visible control products;
- that crosses too quickly from “controlled approximation” into
  difficult-to-audit task-semantic drift.

Conclusion:

- until an explicit task-level drift budget is approved, this direction stays
  outside the active Level-3 pool.

## 4. Maximum Iteration Count

Level-3 work must obey a stricter cap than Level 2.

Global rule:

1. each candidate gets at most `1` exploratory implementation round by
   default;
2. a second round may happen only after explicit review of runtime gain and
   behavior drift;
3. one round may not combine multiple approximate candidates;
4. every candidate must stay runtime-toggleable and trivially revertible;
5. if a candidate breaches its drift budget or lacks a clear quality readout,
   it freezes immediately.

Interpretation:

- round one exists to discover whether the approximation is useful at all;
- round two, if approved, is only for tightening or calibration of an already
  accepted approximation;
- Level-3 work should stop earlier than Level 2, not later.

## 5. Entry Rules For Any Iteration

Before implementation starts, every Level-3 candidate must satisfy all of the
following:

1. a benchmark/control surface exists;
2. one primary runtime metric is chosen;
3. one quality or behavior metric is chosen;
4. an explicit drift budget is stated in user-facing terms;
5. a clean exact toggle/rollback path is identified.

### 5.1 Benchmark / control-surface restriction

Default allowed surfaces are intentionally narrow:

1. `world_batch_vec_env` or cooperative runtime benchmarks for runtime gain;
2. one policy or rollout sanity surface that can reveal obvious behavior drift;
3. one exact baseline run kept unchanged for comparison.

### 5.2 Candidate-specific entry gates

`L3-VIS-01` may start only if:

- the target surface actually uses `include_visual=True`; and
- visual refresh or visual transport is a visible runtime slice.

`L3-OBS-01` may start only if:

- `obs_build` remains a visible bottleneck; and
- the target policy surface can tolerate explicit contact/RWR truncation review.

`L3-PREC-01` may start only if:

- policy-facing export or bridge cost is material on the chosen surface; and
- the target hardware/runtime path actually supports the lower-precision mode.

`L3-MISS-01` may start only if:

- safer approximate candidates do not meet the time-budget need; and
- the mission/aux observation tail is still a primary bottleneck on the chosen
  surface.

## 6. Default Order

The current cautious order is:

1. `L3-VIS-01`
2. `L3-OBS-01`
3. `L3-PREC-01`
4. `L3-MISS-01`

Reason:

- move from isolated policy-input drift toward broader control-facing drift;
- spend the cheapest semantic risk first;
- keep mission/aux cadence approximation as a late and explicitly reviewed
  option.

## 7. Mandatory Stop / Rollback Rules

Every Level-3 round must stop or roll back if any of the following happens:

1. runtime gain is too small to justify the declared drift;
2. drift exceeds the predeclared budget;
3. reward, termination, or command semantics change without explicit approval;
4. the implementation cannot be kept behind a clear runtime toggle;
5. the behavior comparison surface does not provide a clear pass/fail readout.

The default Level-3 attitude for this repo is therefore:

```text
Approximation is allowed only when it is explicit,
local, benchmark-justified, quality-bounded, and easy to turn off.
```
