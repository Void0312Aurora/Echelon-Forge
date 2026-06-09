# L2-BEHAV-01: Command-Chain Exact Incremental Recompute Plan

Status: `2026-05-18` active execution entry.  
Scope: covers only `L2-BEHAV-01` and may not expand sideways into other
Level-2 candidates.

Related documents:

- [level-2 equivalent algorithm optimization candidate set](performance_runtime_level2_equivalent_algorithm_candidates_20260518.md)
- [level-1 runtime optimization taskboard](performance_runtime_level1_taskboard_20260518.md)
- [runtime performance optimization ladder](performance_runtime_optimization_ladder_20260518.md)

---

## 1. Boundary Statement

This round changes only the compute organization of the exact command chain.

It may not:

1. change phase-transition cadence;
2. change the task contract of `task_order`, `leader_intent`, or
   `pilot_report`;
3. reduce mission-command freshness as seen by the kernel;
4. introduce any approximate update, cadence reduction, or fidelity tradeoff;
5. expand sideways into waypoint guidance, reward/info tail, or
   scripted-opponent owner rules.

## 2. Current Goal

The goal is intentionally narrow:

- confirm whether current command-chain updates still contain structural
  “full exact rebuild every step” cost;
- if so, convert that work into exact incremental recomputation with explicit
  invalidation rules.

Questions explicitly out of scope for this round:

- whether waypoint guidance should also be batched;
- whether scripted opponents should collapse to once-per-world;
- whether reward/info tail should move into Level 2 next.

## 3. Primary And Secondary Metrics

Primary metric:

- `behavior_update_ms`

Secondary metrics:

- `command_sync_ms`
- `total_ms`

Rule:

- this round is accepted or rejected primarily on `behavior_update_ms`;
- `total_ms` is only a supporting confirmation metric and may not replace the
  primary one.

## 4. Maximum Iteration Count

This candidate is allowed at most `2` implementation rounds.

This document currently corresponds to:

- round `1`: entry measurement plus first implementation
- round `2`: allowed only if round `1` already proves the direction effective

If round `1` is neutral, round `2` does not start by default.

## 5. Entry Threshold

Implementation may begin only if at least one of the following is true:

1. the command-chain sub-slice is expected to account for `>= 15%` of
   cooperative `behavior_update_ms`;
2. structural command-chain duplication has been validated on cooperative and
   at least one batch/single-world reference surface;
3. command-chain is now the last major unverified structural bottleneck on the
   cooperative behavior path.

If none of the above is true, this entry stops at measurement/analysis and may
not move into implementation.

## 6. Current Known Evidence

As of `2026-05-18`, the current working evidence is:

1. Level-1 first-pass work already improved cooperative `command_sync_ms`
   clearly;
2. Level-1 second-pass director tightening was broadly neutral on long-running
   probes;
3. the remaining cooperative `behavior_update_ms` cost looks most likely to
   remain in:
   - command-chain
   - waypoint guidance
4. duplicated scripted-opponent work has been confirmed, but because of
   `target_id` owner ambiguity it is outside the allowed scope of this entry.

Default conclusion:

```text
L2-BEHAV-01 may enter entry measurement now.
It may move into implementation only if measurement continues to support
command-chain as a primary structural sub-slice.
```

### 6.1 Entry-measurement result on `2026-05-18`

Two same-shape reference surfaces have now been measured:

1. cooperative long-running cruise probe
2. single-world batch execution runtime (inline scenario)

Result:

- cooperative:
  - `behavior_update_ms ~= 0.442`
  - command-chain sub-slice about `0.203 ms/step`
  - waypoint sub-slice about `0.130 ms/step`
  - command-chain accounts for about `45.9%` of `behavior_update_ms`
- single-world:
  - `behavior_update_ms ~= 0.158`
  - command-chain sub-slice about `0.136 ms/step`
  - waypoint sub-slice about `0.0056 ms/step`
  - command-chain accounts for about `86.0%` of `behavior_update_ms`

Conclusion:

1. the command-chain sub-slice is clearly above the `>= 15%` entry threshold;
2. the pattern is not a cooperative-only accident;
3. `L2-BEHAV-01` may now move from entry measurement into invalidation-rule
   definition and first implementation.

### 6.2 Round-1 implementation result on `2026-05-18`

Round-1 implementation was attempted with the smallest allowed cut:

- keep scope inside `RuleBasedLeaderPhaseManager.update(...)`;
- try to reuse `leader_intent` on stable steps rather than rebuilding it every
  step;
- do not change cadence, kernel freshness, waypoint guidance, director logic,
  or scripted-opponent ownership.

Verification status:

- semantic regression tests stayed green on the targeted leader/runtime
  surfaces;
- benchmark surface family stayed comparable by rerunning the same cooperative
  long-running cruise probe shape and one auxiliary single-world reference.

Measured result:

- cooperative long-running cruise probe, sample A:
  - `behavior_update_ms ~= 0.479`
  - `command_sync_ms ~= 0.083`
  - `total_ms ~= 1.559`
- cooperative long-running cruise probe, sample B:
  - `behavior_update_ms ~= 0.487`
  - `command_sync_ms ~= 0.084`
  - `total_ms ~= 1.579`
- auxiliary single-world reference:
  - `behavior_update_ms ~= 0.080`
  - `command_sync_ms ~= 0.111`
  - `total_ms ~= 0.569`

Comparison against the current cooperative entry baseline:

- entry baseline recorded above: `behavior_update_ms ~= 0.442`,
  `command_sync_ms ~= 0.079`, `total_ms ~= 1.466`
- both round-1 cooperative samples moved `behavior_update_ms` and `total_ms`
  in the wrong direction rather than improving them.

Conclusion:

1. the attempted Python-side stable-key / exact-object reuse added more
   overhead than it removed on the target cooperative surface;
2. the direction was repeatably negative across two same-surface samples, so
   this cut does not satisfy the round-1 acceptance rule;
3. the implementation was therefore reverted and this candidate is frozen at
   round `1` unless new, narrower measurement evidence points to a cheaper
   exact invalidation path.

## 7. Round-1 Execution Order

Round `1` must follow this fixed order:

1. add/refine command-chain sub-slice measurement on the cooperative
   long-running cruise probe;
2. confirm on at least one non-cooperative reference surface that the pattern
   is not a cooperative-only accident;
3. state the exact command-chain invalidation-condition set explicitly;
4. enter implementation only if the entry threshold is met;
5. after implementation, rerun:
   - semantic regression tests
   - cooperative long-running cruise probe
   - at least one auxiliary surface

## 8. Allowed Implementation Directions

Only the following directions are allowed:

1. explicit dirty/invalidation rules for the exact command chain;
2. replacing “rebuild exact objects every step” with “rebuild only on
   invalidation”;
3. reusing stable exact runtime objects and driving updates through field diffs
   or stable export paths;
4. tightening the organization of exact kernel export without changing
   semantics.

## 8.1 Current explicit invalidation-condition set

Based on the current command-chain / leader-tasking code, round one may only
organize work around the following invalidation conditions:

1. `c2_task_name` changes;
2. `mission_phase_name` changes;
3. `waypoint_idx` changes;
4. `post_waypoint_transition` changes presence or content;
5. `task_order` is not built yet;
6. `leader_intent` is not built yet;
7. `pilot_report` is not built yet;
8. report type changes (for example `REP_WILCO -> REP_RTB`);
9. `task_order_overrides` or scenario-level task config changes;
10. task-retask gate outcomes change:
   - scramble complete
   - on-station complete
   - RTB / recover-land gate open
11. hierarchical command-chain activation flips either way.

Round one is not trying to make every part of command-chain logic incremental.

The smaller default goal is:

```text
When none of the invalidation conditions above are hit,
avoid fully rebuilding exact leader/task/report objects on every step.
```

That implies:

- when phase/task state is unchanged, stable exact objects should be reused
  preferentially;
- full retask / rebuild paths should run only when invalidation conditions are
  actually hit.

## 9. Explicitly Forbidden Directions

This round explicitly forbids:

1. reducing update count to gain speed;
2. replacing fresh results with delayed results;
3. bypassing exact phase logic through defaults, shortcuts, or best-effort
   behavior;
4. mixing waypoint guidance, director, or reward/info tail into the same round;
5. introducing scripted-opponent owner semantics.

## 10. Round-1 Acceptance Rule

Round `1` counts as effective only if at least one of the following is true:

1. `behavior_update_ms` improves by `>= 5%`;
2. `behavior_update_ms` improves by a smaller amount, but the direction is
   consistent across two same-surface samples;
3. `behavior_update_ms` improves and `total_ms` moves in the same direction.

At the same time, all of the following must also hold:

1. semantic regression tests stay green;
2. the round stays inside the boundary statement;
3. benchmark surfaces stay comparable.

## 11. Neutral And Freeze Rules

The round is considered neutral if:

1. `behavior_update_ms` changes only slightly and direction is unstable;
2. `behavior_update_ms` improves but `total_ms` is unchanged and there is no
   structural explanation;
3. implementation complexity rises noticeably without enough gain to justify a
   second round.

If round `1` is neutral:

- record the result;
- do not open round `2`;
- freeze this candidate unless new, narrower measurement evidence appears.

If round `2` still fails to produce repeatable gain:

- freeze this candidate formally;
- stop further work on it.
