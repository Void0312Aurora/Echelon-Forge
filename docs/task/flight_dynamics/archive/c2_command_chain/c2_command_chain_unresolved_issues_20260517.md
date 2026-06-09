<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/c2_command_chain/c2_command_chain_unresolved_issues_20260517.zh.md. Review before treating this file as authoritative. -->

# C2 Command Chain and Communication Open Issues Analysis

Status: `2026-05-17` archived open-issues snapshot.

Related documents:

- [Freeze Analysis Baseline](../../c2_command_chain/c2_command_chain_realism_analysis_20260517.md)
- [Current Progress Checkpoint](c2_command_chain_progress_checkpoint_20260517.zh.md)
- [Naval Warfare Advancement Checkpoint](../../naval/naval_progress_checkpoint_20260517.zh.md)

Document positioning:

- Used to separate "issues not yet resolved" from the freeze analysis draft and align with current code progress.
- Only lists issues that still affect next-round implementation decisions, not items already closed.

## 0. Supplement to Current Document Calibration

The more accurate reading approach is:

1. This document lists "remaining closure points", not "capabilities completely absent from the current system".
2. `MissionCommand` fields, profiles, codecs, runtime, and world-batch roundtrip already have a batch of explicit tests locking them down.
3. The `RuntimeFacade` mainline has also entered an adapter gatekeeping state, so "raw runtime scattered straight through the main chain" is no longer current fact.

Therefore, if you look only at the old freeze analysis, you will overestimate current debt; if you look only at the current green line, you will underestimate the remaining compat/contract closure margin.

## I. Items No Longer Current Blockers

The following issues, although raised in the freeze analysis, already have minimal closure and should no longer be treated as "completely untouched" gaps:

1. `PilotAction` unconditionally overwriting `MissionCommand`
   - Current status: Changed to deadband takeover, no longer unconditional silent preemption.
2. Naval `MissionCommand` having no dedicated fields at all
   - Current status: Has minimal station reference fields and completed roundtrip.
3. `Ship` still using `MovementCommand` as the primary authority
   - Current status: Unified primary write direction to `MissionCommand`.
4. `ROE` having only one boolean bit
   - Current status: Has minimal `roe_state + authority holder` and runtime gate.
5. `DataLink` infinite messages per frame
   - Current status: Has dual budgets for messages/reports and drop observability.
6. `MissionCommand` queue being silently overwritten by a second submission
   - Current status: Current mainline verifies FIFO; previous failures were mainly due to test misjudgments.

This means the next round should not waste time proving whether these points "actually exist", but rather shift to "where the current closure still falls short".

## II. Issues Still to Be Resolved

### 2.1 `CommandLink` Still Lacks a True Queue Policy

Current status:

1. `MissionCommand` has a minimal FIFO queue.
2. But `MovementCommand / ActionCommand` still use a refresh/overwrite pending semantic.
3. `CommandLink` still only has fixed delay + independent packet loss, with no priority, jitter, retransmission, or acknowledgment.

Why it still matters:

1. The current `CommandLink` cannot express "high-priority engagement commands queue-jumping, low-priority formation adjustments deferring".
2. It also cannot express "retransmit after loss" or "delay distribution with long tail".
3. This limits subsequent more realistic naval fire-control / tasking experiments.

Suggested next steps:

1. First implement a minimal priority bucket or per-command-type queue policy, rather than a full ACK.
2. Then evaluate whether minimal jitter / retry is needed.

### 2.2 `DataLink` Already Has Budget, but Is Still Not a Network Model

Current status:

1. Has `report/message budget`.
2. Has minimal congestion drop observability.
3. Still operates as an approximate broadcast under single-hop, same network, same side, LOS conditions.

Why it still matters:

1. No relay yet, so over-the-horizon coordination cannot be expressed.
2. No jamming / EMCON interaction yet.
3. No doctrine or state machine for task assignment messages.

Suggested next steps:

1. First do stress supplement tests and budget scaling to confirm budget behavior is stable under more fanout.
2. Then select one small thread to continue:
   - Relay approximation
   - Jamming loss approximation
   - Tasking message priority

Opening three threads simultaneously is not recommended.

### 2.3 Naval Tasking Is Still Not Full Mission-Type Command

Current status:

1. Has minimal naval station field.
2. Has minimal station-hold / screen behavior closed loop.
3. Still lacks true task phase, threat axis, patrol zone, formation duty transition.

Why it still matters:

1. This limits `MissionCommand` progression toward more realistic naval C2.
2. Also limits `ROE / authority / fire-control` interoperation with task state.

Suggested next steps:

1. Do not build a full state machine directly.
2. First select one minimal verifiable semantic to enter `MissionCommand`:
   - threat axis
   - station sector
   - patrol area

### 2.4 `ROE / authority` Still Not Integrated into Full Task and Communication Chain

Current status:

1. Runtime weapon release can already read minimal `roe_state`.
2. But authority transfer is still not connected to communication, task delegation, or message acknowledgment chain.
3. `DataLink` also lacks a formal `ENGAGE / ENGAGED / WILCO / UNABLE` task message closed loop.

Why it still matters:

1. Without authority flow, many realistic C2 behaviors remain inexpressible.
2. `ROE` also not yet linked with finer-grained IFF / track quality.

Suggested next steps:

1. First implement a minimal message closed loop, e.g.:
   - `AssignTask -> REP_WILCO`
   - `ENGAGE authorization -> holder match`
2. Then decide whether to advance authority transfer.

### 2.5 `MissionCommand` Codec Redundancy Not Yet Resolved

Current status:

1. A batch of common / naval / ROE fields have been added to codec / profile / runtime-state.
2. But C++ `MissionCommandCodec` and Python `build_kernel_mission_command()` are still dual-maintenance paths.

Why it still matters:

1. The more new fields, the higher the drift risk between the two paths.
2. This is starting to become a maintenance cost, not a single-point bug.

Suggested next steps:

1. Do not immediately rewrite into a single new schema.
2. First create a field comparison table and roundtrip contract, identifying fields not yet pinned down by tests.
3. Current focus has shifted from "do naval fields have roundtrip" to:
   - Is the common / naval / air field matrix consistent
   - Is episode state / post-transition JSON backfill continuously aligned

### 2.6 `RuntimeFacade / ScenarioLoader` Compat Surface Not Yet Fully Offloaded

Current status:

1. `RuntimeFacade.runtime()` has been demoted to a compatibility / diagnostics escape hatch by documentation and architecture tests.
2. Python mainline raw runtime/world access has been reined in to explicit adapters.
3. But adapters still serve both as facade and compat runtime fallback, and the `ScenarioLoader` side still retains old proxy entry points.

Why it still matters:

1. If the compat surface continues to expand, it will re-magnify the owner/interface debt of `RuntimeFacade` and `ScenarioLoader`.
2. While such problems may not immediately break behavioral tests, they will continue to dilute the closure boundary between `MissionCommand` and the execution runtime.

Suggested next steps:

1. Continue to push new requirements first as facade-shaped adapter methods, rather than flowing back into raw runtime access.
2. Continue offloading `ScenarioLoader`'s compat facade; do not stuff new state synchronization back into `core.py`.
3. Keep `tests/architecture/runtime_facade/test_layering.py` and world-setup compat tests as gatekeeping lines.

### 2.7 Documentation Calibration Still Needs to Transition from "Freeze Analysis" to "Current Status"

Current status:

1. The original analysis document still retains judgments from the `2026-05-17` freeze point.
2. Some statements have been partially overridden by current implementation progress.

Why it still matters:

1. If subsequent readers look only at the freeze analysis, they will mistakenly believe these points are completely undone.
2. This leads to duplicate verification, mis-scheduling, or incorrect external description.

Suggested next steps:

1. Keep the freeze analysis unchanged.
2. Subsequently update only in sub-project directories as "current progress / open issues".

## III. Directions Most Worth Advancing in Next Round

Sorted by current code surface and risk surface, suggested priority:

1. `DataLink` stress supplement test / budget scaling
   - Rationale: Currently just has budget and counters, most suitable to stabilize first.
2. `CommandLink` minimal priority policy
   - Rationale: Directly improves command chain realism, write set still controllable.
3. `MissionCommand` minimal naval tasking new semantics
   - Rationale: Can push naval C2 one step further from "minimal station".
4. `ROE / authority` minimal message closed loop
   - Rationale: Can deepen the task/communications/weapon chain linkage.
5. `MissionCommand` codec/profile contract reconciliation
   - Rationale: This is maintenance debt, important but not necessarily urgent.
6. `RuntimeFacade / ScenarioLoader` compat offloading closure
   - Rationale: This is already one of the true remaining quantities in the `C2/runtime` direction, not merely a structural side branch.

## IV. Whether It's Worth Re-dispatching Subagents Now

Current suggestion:

1. Main implementation continues to be advanced locally on the mainline.
2. When the next round enters "boundary verification, stress testing, documentation reconciliation", then distribute these sidecar tasks to subagents.

Reasons:

1. Currently `DataLink / CommandLink / MissionCommand` are still in the same high-overlap write set.
2. Spreading implementation further now would make merge costs exceed benefits.
3. More suitable for distribution:
   - Stress supplement test design
   - Roundtrip field reconciliation
   - Documentation calibration review
