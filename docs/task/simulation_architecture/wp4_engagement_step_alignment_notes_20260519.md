# WP4-B/C Engagement + Step/Lifecycle Alignment Notes

Status: `2026-05-19` bounded probe completed.

Inputs reviewed:

- [WP4-B/C dispatch sheet](wp4_engagement_step_cluster_20260519.md)
- [WP4 facade alignment](facade_alignment_wp4_20260519.md)
- [WP3 engagement pilot acceptance review](../review/wp3_engagement_pilot_acceptance_review_20260519.md)
- Current `src/runtime/facade/*`
- Current `tests/runtime/facade/`
- Current `tests/runtime/engagement/`

Scope note:

- This probe does not change facade signatures.
- This probe does not edit policy, Gymnasium, Python bindings, or runtime
  scheduler code.
- The current worktree already contains unrelated facade/test/doc changes from
  other workers; this note records evidence from the current working tree and
  does not revert those edits.

## 1. Summary

WP4-B is mostly aligned at the current facade level: engagement export is
facade-shaped, read-only for live track snapshots, preserves include flags, and
retags recent engagement event entity refs for requested world indices.

WP4-C has the basic step/lifecycle projection in place:
`ExecutionBatchStepResult` exposes step results, rewards, terminated/truncated
flags, status vectors, termination reason strings, reward breakdown JSON,
step-info products, controller-state change flags, and an observation packet.

The remaining gaps are semantic clarity rather than missing low-level plumbing:
producer coverage needs to be documented as explicit per-slot coverage,
diagnostics traces inside engagement export are still piggyback evidence rather
than a diagnostics logging surface, reward fact/shaping attribution is not a
typed facade contract, termination reason source is not represented, and
observation snapshot provenance is not yet versioned according to WP2.5.

## 2. WP4-B Engagement Export Findings

### Producer Coverage

Current `EngagementEventPacket` slots exist in
`src/runtime/facade/runtime_facade_types.h`:

| Slot | Current producer | Current status |
|------|------------------|----------------|
| `refs` | Request echo from `EngagementBatchRequest.refs`. | Maintained packet metadata. |
| `trace_ids` | Request echo from `EngagementBatchRequest.trace_ids`. | Maintained packet metadata. |
| `track_packets` | Live `AgentObservation.contacts` converted by facade export. | Maintained live snapshot producer. |
| `launch_requests` | No current producer in facade export. | Placeholder / deferred producer. |
| `launch_events` | `RecentEngagementEvents.launch_events` from each requested world. | Maintained compatibility buffer producer. |
| `munition_lifecycle_packets` | No current producer in facade export. | Placeholder / deferred producer. |
| `effects_events` | `RecentEngagementEvents.effects_events` from each requested world. | Maintained compatibility buffer producer. |
| `damage_reports` | `RecentEngagementEvents.damage_reports` from each requested world. | Maintained compatibility buffer producer. |
| `diagnostics_traces` | Two sources: track diagnostics generated during live export, plus recent traces from the compatibility buffer. | Diagnostics piggyback, not full diagnostics logging. |

This satisfies WP4-B if the two empty slots remain explicitly documented as
deferred producer placeholders. It should not be interpreted as complete
producer coverage for launch requests or munition lifecycle.

### Multi-World `world_index`

Current implementation walks unique requested world indices, pulls recent
events from each requested world, and retags entity references inside recent
events before appending them to the packet.

Retagged refs:

- `LaunchEvent.spawned_munition`
- `EffectsEvent.munition`
- `EffectsEvent.target`
- `DamageReport.target`
- `DiagnosticsTrace.munition`

Current tests cover the important regression: a world-1 missile launch exported
through the facade keeps `spawned_munition.world_index == 1` and carries a trace
whose `munition.world_index == 1`.

Residual risk:

- Recent launch requests and munition lifecycle packets are not in the recent
  buffer, so there is no retagging path for those slots yet.
- `LaunchEvent` itself only carries spawned munition ancestry; it does not carry
  shooter or target refs, so world-safety for shooter/target ancestry depends
  on linked diagnostics or future `LaunchRequest` coverage.

### Diagnostics Piggyback Boundary

Current live-track diagnostics are generated only when
`include_diagnostics_traces` is true and `trace_ids` is non-empty. These traces
carry `trace_id`, `chain_id`, `track_id`, and `observation_packet_version`.
They intentionally leave launch/effects/damage ids at zero when no such events
exist.

This is acceptable for WP4-B as engagement evidence, but it should remain
labeled as diagnostics piggyback. It is not a full diagnostics logging
framework and should not be used as the sole WP5 trace-conformance surface.

## 3. WP4-C Step/Lifecycle Findings

### Current Coverage

`ExecutionBatchStepResult` currently exposes:

- `step_results`
- `rewards`
- `terminated`
- `truncated`
- `status_vectors`
- `termination_reasons`
- `reward_breakdown_jsons`
- `step_infos`
- `step_info_valid_flags`
- `controller_state_changed_flags`
- `observation_packet`

`RuntimeFacade::step_execution_batch()` derives those fields from
`ExecutionEpisodeControllerStepResult` and then builds an observation packet
from the same `ExecutionBatchStepRequest` refs and include flags.

Current tests verify:

- result vector sizes match one requested step,
- reward mirrors `step_result.reward_total`,
- terminated/truncated mirror the step result,
- status vector mirrors `status0..status3`,
- termination reason mirrors `controller_state.last_termination_reason`,
- reward breakdown JSON mirrors `controller_state.last_reward_breakdown_json`,
- step info and controller-state change flags are surfaced,
- route/post-waypoint phase changes remain in compiled controller state.

### Current Gaps

| Topic | Current state | Gap |
|-------|---------------|-----|
| Reward attribution | Total reward and breakdown JSON are surfaced. | No typed `RewardReport`, no fact-vs-shaping attribution, no term owner/source fields. |
| Termination/truncation | Separate bool vectors and a reason string are surfaced. | No typed reason source distinguishing simulation, orchestration timeout, policy/test truncation, or adapter mirror. |
| Observation snapshot | Step result includes an `ObservationBatchPacket`. | Packet lacks explicit snapshot version, source barrier, or source time metadata. |
| Episode phase ownership | Compiled/controller state carries `mission_phase_name` and `step_count`; facade exports controller state. | No top-level `EpisodeStatus` or authoritative-source marker in `ExecutionBatchStepResult`. |
| Information-state boundary | Observation export remains facade-shaped. | `ObservationViewSpec` / `DecisionBelief` provenance is WP4-A/D/E territory and not represented in this cluster. |

These gaps are consistent with WP4-C planning and should be resolved through
small DTO/documentation increments after WP4-A names settle, not by broad
facade signature churn during this probe.

## 4. Recommended Follow-Up

### WP4-F Documentation / Integration

1. Add a producer coverage table for `EngagementEventPacket` to the WP4
   integration notes, using the coverage status above.
2. Label `launch_requests` and `munition_lifecycle_packets` as deferred
   producer placeholders until a maintained producer exists.
3. Label engagement-export diagnostics as piggyback evidence, not a dedicated
   diagnostics log.
4. Record that `ExecutionBatchStepResult` is currently a projection over
   compiled controller results plus observation packet export.

### WP5 Validation Harness

1. Add a producer-coverage test that asserts current empty slots are
   intentionally empty unless a producer is introduced.
2. Add a multi-world engagement export test that covers effects and damage
   retagging, not only launch-event munition retagging.
3. Add a step-result semantic test that parses `reward_breakdown_jsons` and
   checks the current breakdown remains structurally usable.
4. Add a termination/truncation test after reason-source fields or docs are
   introduced.
5. Add observation snapshot provenance tests after WP2.5 snapshot/version fields
   are represented in facade DTOs.

### Deferred DTO Work

These should not be implemented in this bounded probe:

- `RewardReport` with fact terms, shaping terms, term owner, and source
  snapshot version.
- `TerminationSpec` / `EpisodeStatus` with reason source and authoritative
  lifecycle owner.
- Dedicated diagnostics facade surface separate from engagement piggyback.
- Formal event queue replacement for `RecentEngagementEvents`.

## 5. Suggested Focused Test Commands

Recommended current evidence checks:

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\engagement\test_facade_engagement_export.py tests\runtime\engagement\test_live_engagement_event_capture.py tests\runtime\engagement\test_diagnostics_trace_contract.py tests\runtime\facade\test_runtime_facade.py
```

Broader WP4 smoke after integration:

```powershell
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade tests\runtime\engagement
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\architecture\test_runtime_facade_layering.py
```

## 6. Probe Decision

No code or test patch is recommended in this bounded pass. The current issues
are mostly contract/documentation semantics, and changing facade DTOs now would
risk colliding with WP4-A/WP4-D/WP4-E workers.
