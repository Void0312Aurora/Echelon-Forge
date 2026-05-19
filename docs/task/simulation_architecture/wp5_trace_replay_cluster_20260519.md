# WP5-C Dispatch Sheet: Trace And Replay Gates

Status: `2026-05-19` first-wave dispatch sheet.

Language:

- English canonical: `wp5_trace_replay_cluster_20260519.md`
- Chinese companion: [wp5_trace_replay_cluster_20260519.zh.md](wp5_trace_replay_cluster_20260519.zh.md)

Inputs:

- [WP5 validation harness](validation_harness_wp5_20260519.md)
- [WP4 facade alignment acceptance review](../review/wp4_facade_alignment_acceptance_review_20260519.md)
- [WP4-G facade evidence notes](wp4_facade_evidence_notes_20260519.md)
- [WP4-B/C engagement-step alignment notes](wp4_engagement_step_alignment_notes_20260519.md)
- Current `tests/runtime/engagement/` and `tests/runtime/facade/`

## 1. Purpose

WP5-C adds trace and replay-facing gates around the evidence that already
exists. It should test ancestry, ids, world-safe retagging, and current replay
metadata availability without inventing new runtime semantics.

This is a higher-reasoning stream because false assumptions about event
ordering, source time, or trace ancestry can create brittle tests.

## 2. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP5-C1 Trace Ancestry Gate` | Add or document focused tests for current launch/effects/damage/diagnostics ancestry carried by engagement export. | `tests/runtime/engagement/`, optional docs note. | High. |
| `WP5-C2 Replay Metadata Availability Review` | Distinguish metadata available today from metadata deferred by WP2.5/WP4, especially snapshot, barrier, source-time, and deterministic event-id fields. | `tests/runtime/facade/`, `tests/runtime/engagement/`, docs note. | High. |
| `WP5-C3 Piggyback Diagnostics Boundary` | Preserve the rule that `DiagnosticsTrace` is piggyback evidence in WP4/WP5 first wave, not a dedicated diagnostics facade surface. | `tests/runtime/engagement/`, docs. | Medium-high. |
| `WP5-C4 Smoke Candidate Note` | Recommend trace/replay tests for later WP5 smoke promotion. | Docs note or report to integration owner. | Medium. |

## 3. Non-Goals

- Do not add a dedicated diagnostics facade query in this cluster.
- Do not require snapshot/barrier/source-time metadata before DTO support
  exists.
- Do not replace `RecentEngagementEvents` or change event ordering semantics.
- Do not edit broad facade signatures unless a minimal field has already been
  accepted by the integration owner.

## 4. Acceptance Gates

This cluster is accepted when:

1. Current trace ancestry is tested or explicitly documented as missing.
2. Available replay metadata is separated from metadata-dependent future gates.
3. Diagnostics piggyback evidence remains distinct from a dedicated diagnostics
   surface.
4. Focused tests pass locally.
