# WP11-D Consumer Boundary Pre-Gates

Status: `2026-05-20` planned WP11 dispatch sheet.

Language:

- English canonical: `wp11_consumer_boundary_pregates_cluster_20260520.md`
- Chinese companion:
  [wp11_consumer_boundary_pregates_cluster_20260520.zh.md](wp11_consumer_boundary_pregates_cluster_20260520.zh.md)

Inputs:

- [WP11 facade vertical slice and provenance](facade_vertical_slice_provenance_wp11_20260520.md)
- [WP11-B information provenance labels](wp11_information_provenance_labels_cluster_20260520.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.md)

## 1. Purpose

`WP11-D` adds pre-enforcement gates for maintained consumers. It does not claim
full Architecture Law 14 enforcement; it makes the boundary testable enough for
the later information/agency enforcement phase.

## 2. Scope

In scope:

- add static or runtime guard tests that distinguish maintained consumer paths
  from diagnostics-only truth/raw-ECS paths;
- require maintained fixtures to consume provenance-labeled
  `ObservationPacket`/`DecisionBelief`-style inputs;
- keep diagnostics-only raw runtime paths explicit and allowlisted;
- document residuals for full Law 14 and Agency Graph enforcement.

Out of scope:

- blocking every raw ECS read in the repository;
- enforcing role authority scopes;
- dispatching decision models through Agency Graph;
- rewriting training or experiment code beyond focused fixtures.

## 3. Gate Rules

| Boundary | WP11-D behavior |
|----------|-----------------|
| Maintained consumer | Must use provenance-labeled packet or belief inputs in the focused slice. |
| Diagnostics fixture | May use truth/raw runtime setup only with explicit diagnostics-only label or allowlist. |
| Compatibility adapter | May remain if labeled compatibility-only and not presented as maintained decision evidence. |
| Unknown source | Fails closed in focused guard tests. |

## 4. Acceptance Tests

Minimum tests:

- architecture guard rejects unlabeled maintained consumer fixtures;
- diagnostics-only truth/raw-ECS setup remains explicit;
- maintained consumer smoke reads provenance-labeled packet or belief input;
- tests do not claim complete Law 14 enforcement;
- residuals identify the next enforcement WP.

## 5. Handoff Contract

Return:

- guard files and allowlists touched;
- maintained and diagnostics-only fixture paths;
- tests added or updated;
- commands run and outcomes;
- residuals for full Law 14 / Agency Graph enforcement;
- integration notes for `WP11-E`.
