# WP10-C Same-Window Edge Validation

Status: `2026-05-20` planned WP10 dispatch sheet.

Language:

- English canonical: `wp10_same_window_validation_cluster_20260520.md`
- Chinese companion:
  [wp10_same_window_validation_cluster_20260520.zh.md](wp10_same_window_validation_cluster_20260520.zh.md)

Inputs:

- [WP10 causal runtime foundation](causal_runtime_foundation_wp10_20260520.md)
- [WP10-A manifest registry](wp10_manifest_registry_cluster_20260520.md)
- [WP2.5 state/barrier cluster](../wp25_scheduler_semantics/wp25_state_barrier_cluster_20260519.md)
- [Post-WP9 route plan](../post_wp9_architecture_route_plan_20260520.md)

## 1. Purpose

`WP10-C` makes same-window dataflow legal or illegal at schedule-construction
time. This prevents the first window loop from becoming either a hidden linear
pipeline or a wildcard read-after-write channel.

## 2. Scope

In scope:

- consume the `WP10-A` manifest registry;
- validate producer publish intent;
- validate consumer read declarations;
- validate read/write or packet intersections;
- reject wildcard or undeclared same-window edges;
- reject cycles in the selected manifest-derived window;
- add passing and failing fixtures.

Out of scope:

- per-tick dynamic edge discovery;
- global graph compiler;
- strict clock-domain enforcement;
- runtime mutation of manifest definitions.

## 3. Validation Rules

A same-window edge is legal only when all conditions are true:

1. The producer declares the output packet or state-derived output.
2. The producer declares `write_commit_policy: stage_publish` for that output.
3. The producer's `allowed_same_window_edges` names the consumer node id or an
   allowed downstream stage family.
4. The consumer declares `read_snapshot_policy: same_window`.
5. The consumer read set or input packets intersect the producer write set or
   output packets.
6. The consumer declares `stage_publish` in `required_barriers`.
7. The resulting window graph is acyclic.

Failure must be explicit: invalid edges should produce a stable validation
error, not silent fallback to hidden order.

## 4. Fixtures

Required fixture classes:

| Fixture | Expected result |
|---------|-----------------|
| Declared producer and consumer with matching read/write sets. | Pass. |
| Producer does not name the consumer. | Fail. |
| Producer names the consumer but read/write sets do not intersect. | Fail. |
| Consumer requests `same_window` but omits `stage_publish`. | Fail. |
| Edge introduces a cycle. | Fail. |
| `window_commit`-only producer is consumed as same-window. | Fail. |

## 5. Acceptance Tests

Minimum tests:

- passing fixture validates the selected WP10 slice;
- each invalid fixture fails with a named reason;
- validator uses the registry API rather than re-parsing duplicated doc tables;
- validation runs before the loop executes the selected schedule.

## 6. Handoff Contract

Return:

- validation helper file paths;
- fixture file paths;
- exact failure messages or error codes;
- tests added or updated;
- commands run and outcomes;
- integration notes for `WP10-B/D/E`.
