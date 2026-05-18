# Level-2 Equivalent Algorithm Optimization Candidate Set

Status: `2026-05-18` active planning draft.  
Scope: after Level-1 implementation optimization reaches visible diminishing
returns, this document consolidates the current Level-2 candidate set,
iteration boundaries, and stop rules for the runtime-performance line.

Related documents:

- [runtime performance optimization ladder](performance_runtime_optimization_ladder_20260518.md)
- [level-1 implementation optimization analysis](performance_runtime_level1_implementation_analysis_20260518.md)
- [level-1 runtime optimization taskboard](performance_runtime_level1_taskboard_20260518.md)

---

## 1. Purpose

This document no longer discusses Level-1 implementation cleanup.

It answers three narrower questions:

1. whether the current line is ready to move into Level 2;
2. which Level-2 candidates are currently allowed;
3. what iteration boundaries each candidate must obey to prevent another
   round of drift.

Here, “Level 2” means:

- preserve the task contract;
- preserve target semantics exactly;
- allow compute reorganization, batching changes, incremental invalidation
  rules, or exact algorithmic restructuring;
- do not cross into approximation or fidelity tradeoff.

## 2. Why Level 2 Is Now Allowed

The current line has met the conditions to enter Level 2:

1. the first Level-1 pass produced confirmed gains, especially on cooperative
   `command_sync_ms`;
2. the second Level-1 pass was safe but broadly neutral on long-running probes;
3. the remaining cooperative cost now looks more structural inside exact
   behavior organization than Python surface churn;
4. continued open-ended Level-1 digging no longer matches the expected return
   on time.

The default conclusion is therefore:

```text
The active runtime-performance line may now promote from
Level-1 implementation optimization to Level-2 equivalent algorithm optimization.
```

## 3. Current Level-2 Candidate Pool

The following candidates are ordered from “best current default” to “keep in
reserve but do not start first.”

### L2-BEHAV-01: command-chain exact incremental recomputation

Priority: `P0`

Goal:

- convert cooperative/batch command-chain updates from per-step full rebuilds
  into exact incremental recomputation with explicit invalidation rules;
- preserve the semantics of `task_order`, `leader_intent`, `pilot_report`, and
  mission-command visibility.

Why this is here:

- the remaining `behavior_update_ms` hotspot points more toward exact
  command-chain logic than toward orchestration alone;
- if validated, this direction can pay off on both cooperative and batch paths.

Allowed algorithm changes:

- explicit invalidation rules for phase, route, takeoff/recovery gates, and
  override changes;
- rebuilding exact structures only when invalidation conditions are hit;
- replacing per-step full object rewrites with exact reuse or exact incremental
  updates.

Not allowed:

- no behavior-cadence change;
- no skipped phase transitions;
- no “usually equivalent” shortcuts that introduce approximation.

### L2-NAV-01: waypoint-guidance exact batched / structured export

Priority: `P1`

Goal:

- collapse per-slot exact waypoint-guidance queries into a more structured
  batch or shared-export path;
- preserve route guidance, LNAV, and waypoint-sequencing outputs exactly.

Why this is here:

- sub-slice timing still shows waypoint guidance as a visible part of
  cooperative `behavior_update_ms`;
- the shape of the work naturally suggests multi-slot exact query sharing.

Allowed algorithm changes:

- exact batch query paths;
- exact world-shared route-product export and redistribution;
- exact guidance caches with explicit keys and invalidation rules.

Not allowed:

- no lower update cadence for waypoint products;
- no changed definitions for sequence gates, turn lead, or commanded track.

### L2-BEHAV-02: leader/task/report exact object reuse and export restructuring

Priority: `P1`

Goal:

- reduce per-step rebuilding of `leader_intent`, `task_order`, and
  `pilot_report` while keeping semantics equivalent;
- allow exact object reuse, exact field-diff updates, or more structured batch
  export.

Why this is here:

- it is the natural companion direction to `L2-BEHAV-01`;
- if command-chain restructuring only partly pays off, this is the next
  exact behavior-side extension.

Allowed algorithm changes:

- reuse of stable runtime objects;
- exact dirty-bit / version-driven export;
- exact diff-driven update instead of full exact rebuild.

Not allowed:

- no omission of updates that must still be visible to the kernel;
- no reduced freshness on task-contract fields.

Status update (`2026-05-18`):

- two implementation rounds completed on this candidate;
- exact snapshot-driven stable-export skipping was validated as semantically safe
  on both single-world and cooperative paths;
- repeatable benchmark gain remained insufficient after tightening the mission
  snapshot cut, and the cooperative execution surface still did not beat the
  earlier `L2-NAV-01` baseline;
- this candidate is now frozen under the two-round stop rule.

### L2-EVAL-01: reward/info exact tail batching

Priority: `P2`

Goal:

- further structure `compute_full_step(...)` and info export into broader exact
  batching;
- only start after Level-1 `L1-TAIL-01` is clearly exhausted.

Why this is here:

- Level-1 tail tightening already delivered a first confirmed gain;
- if the remaining tail cost is structural exact reward evaluation rather than
  caller-side materialization, it belongs to Level 2.

Current restriction:

- this is not the default first candidate;
- it may start only if renewed measurement shows reward/info tail is once again
  a primary bottleneck.

Status update (`2026-05-18`):

- two implementation rounds completed on this candidate;
- round one removed redundant `ExecutionEpisodeState` materialization from the
  mainline request-build path and produced a repeatable gain on the validated
  `execution_episode_controller_mainline=True` surface;
- round two tightened steady-state loader mirroring so non-structural mainline
  steps stop rebuilding navigation structure shells, producing a second
  repeatable gain on `reward_info_ms`, `loader_consume_ms`, and `total_ms`;
- this candidate is now complete for the current Level-2 pool and should be
  frozen unless a newly measured, still-in-boundary tail hotspot justifies an
  explicit exception round.

### Reserved but not active: scripted-opponent once-per-world merge

Status: keep as an observed possibility, but do not enter the active Level-2
candidate set.

Reason:

- duplicated per-slot `update_scripted_opponents(...)` work has been confirmed
  in cooperative worlds;
- however, different slot loaders may bind the same scripted opponent to
  different `target_id` values;
- that makes this, first, a semantic owner / target-selection problem rather
  than a default equivalent-algorithm optimization.

Conclusion:

- until owner semantics are defined explicitly, this candidate may not be
  promoted into active work.

## 4. Maximum Iteration Count

To prevent another round of drift, Level-2 work must obey a harder round cap.

Global rule:

1. each candidate gets at most `2` implementation rounds;
2. each round may work on only `1` candidate;
3. a round may not expand sideways into a second candidate;
4. if a candidate produces no repeatable gain across `2` rounds, it must be
   frozen.

Interpretation:

- round one proves whether the structural direction is worth anything at all;
- round two is allowed only as a tightening or completion pass on top of a
  first confirmed win;
- if round one is already neutral, round two should not happen by default
  unless finer measurement proves the cut was wrong rather than the direction.

## 5. Entry Rules For Any Iteration

Before implementation starts, every Level-2 candidate must satisfy all of the
following:

1. a benchmark/control surface exists;
2. one primary target metric is chosen;
3. an entry threshold is met;
4. the semantic non-goals are stated explicitly.

### 5.1 Benchmark / control-surface restriction

Only a subset of the following surfaces may be used by default:

1. `world_batch_vec_env`
