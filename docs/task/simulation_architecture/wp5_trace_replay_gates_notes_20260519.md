# WP5-C Trace And Replay Gates Notes

Status: `2026-05-19` focused gate pass.

Language:

- English canonical: `wp5_trace_replay_gates_notes_20260519.md`
- Chinese companion: [wp5_trace_replay_gates_notes_20260519.zh.md](wp5_trace_replay_gates_notes_20260519.zh.md)

Inputs:

- [WP5-C trace/replay dispatch](wp5_trace_replay_cluster_20260519.md)
- [WP5 validation harness](validation_harness_wp5_20260519.md)
- [WP4 facade alignment acceptance review](../review/wp4_facade_alignment_acceptance_review_20260519.md)
- [WP4-G facade evidence notes](wp4_facade_evidence_notes_20260519.md)
- [WP4-B/C engagement-step alignment notes](wp4_engagement_step_alignment_notes_20260519.md)

## 1. Decision

WP5-C should gate the replay evidence that exists today without turning deferred
WP2.5/WP4 metadata into false failures. The first gate is
`tests/runtime/engagement/test_trace_replay_gates.py`.

The gate treats `DiagnosticsTrace` as piggyback evidence carried by
`EngagementEventPacket`. It does not introduce or require a dedicated
diagnostics facade query.

## 2. Current Trace Coverage

| Evidence path | Current gate | Status |
|---------------|--------------|--------|
| Launch event ids | Verifies exported launch events carry positive `event_id`/`request_id`, accepted status, spawned munition ref, and non-negative event time. | Maintained compatibility-buffer evidence. |
| Launch diagnostics ancestry | Verifies a diagnostics trace links `launch_event_id`, `launch_request_id`, `chain_id`, and spawned munition. | Piggyback evidence. |
| Effects event ids | Verifies exported effects events carry positive `event_id`, target ref, munition ref, hit outcome, and non-negative detonation time. | Maintained compatibility-buffer evidence. |
| Damage ancestry | Verifies damage report `source_event_id` points at the effects event and carries target/time/damage data. | Maintained compatibility-buffer evidence. |
| Effects/damage diagnostics ancestry | Verifies a diagnostics trace links `effects_event_id`, `damage_report_id`, `chain_id`, and munition. | Piggyback evidence. |
| Per-slot replay sorting | Verifies launch/effects/damage/diagnostics vectors are sorted by the ids exposed today. | Current replay-sortable metadata. |
| Track snapshot evidence | Verifies live track packets expose positive `track_id`, `snapshot_version`, and non-negative `source_time_s`. | Current track-level metadata only. |

The gate intentionally does not assert a complete live
`LaunchEvent -> EffectsEvent -> DamageReport` chain. Current producers can
record launch traces and effects/damage traces in the same export, but the
effects/damage trace is not guaranteed to retain the prior launch id unless the
runtime producer sets `pending_effects_launch_event_id_`. A complete
launch-to-damage ancestry gate is deferred until that producer contract is
maintained rather than incidental.

## 3. Replay Metadata Boundary

| Metadata | Current availability | WP5-C treatment |
|----------|----------------------|-----------------|
| Per-slot ids | `LaunchEvent.event_id`, `EffectsEvent.event_id`, `DamageReport.report_id`, and `DiagnosticsTrace.trace_id`. | Required today. |
| Per-slot sorted export | `SimulationKernel::export_recent_engagement_events()` sorts each slot by the relevant id. | Required today. |
| Track snapshot id | `TrackPacket.snapshot_version` exists for live facade track export. | Required only for track packets. |
| Track source time | `TrackPacket.source_time_s` exists for live facade track export. | Required only for track packets. |
| Diagnostics observation version | `DiagnosticsTrace.observation_packet_version` exists, but is populated for live track diagnostics, not all recent traces. | Presence required, nonzero value not required for all traces. |
| Packet-level snapshot version | Not present on `EngagementEventPacket` or `ObservationBatchPacket`. | Deferred. |
| Packet-level barrier/window id | Not present on current packet DTOs. | Deferred. |
| Packet-level source time | Not present on current packet DTOs. | Deferred. |
| Cross-slot total ordering | No unified event sequence field exists. | Deferred. |

The second gate asserts the deferred packet-level fields are not assumed yet.
This is a guard against accidentally promoting metadata-dependent replay tests
before the DTO support exists.

## 4. Diagnostics Boundary

`DiagnosticsTrace` remains a piggyback field inside engagement export:

- Maintained: callers may request `EngagementEventPacket.diagnostics_traces`
  through `RuntimeFacade::export_engagement_event_packet`.
- Compatibility adapter: `RuntimeFacade::runtime()` and
  `SimulationKernel::export_recent_engagement_events()` remain available for
  legacy tests and low-level evidence production.
- Diagnostics-only: debug damage helpers and raw recent buffers may create
  oracle-like evidence for tests, but they are not policy input surfaces.
- Deferred: no `export_diagnostics_packet`, `export_diagnostics_trace_packet`,
  `export_diagnostics_traces`, or `get_diagnostics_traces` facade method should
  be required by WP5-C.

## 5. Smoke Candidate

Recommended WP5-C focused command:

```bash
python -m pytest -q tests/runtime/engagement/test_trace_replay_gates.py
```

Recommended integration smoke candidate after WP5-A/B decide suite shape:

```bash
python -m pytest -q \
  tests/runtime/engagement/test_trace_replay_gates.py \
  tests/runtime/engagement/test_facade_engagement_evidence_gates.py \
  tests/runtime/engagement/test_live_engagement_event_capture.py \
  tests/runtime/engagement/test_diagnostics_trace_contract.py \
  tests/runtime/facade/test_facade_step_evidence_gates.py
```

Do not promote packet-level snapshot/barrier/source-time checks into smoke
until the maintained facade DTOs carry those fields.

## 6. Deferred Gates

These require runtime semantic or DTO support and should not be solved inside
WP5-C:

- Complete live launch-to-effects-to-damage ancestry when the damage producer
  is not invoked through a maintained launch-aware path.
- Packet-level snapshot provenance for `ObservationBatchPacket` and
  `EngagementEventPacket`.
- Barrier/window/source-time provenance across injection, stage publish,
  window commit, and export visibility.
- Unified cross-slot event ordering for replay comparison.
- Dedicated diagnostics facade query separate from engagement piggyback
  evidence.
