# WP10-B Window Loop And Injection

Status: `2026-05-20` planned WP10 dispatch sheet.

Language:

- English canonical: `wp10_window_loop_injection_cluster_20260520.md`
- Chinese companion:
  [wp10_window_loop_injection_cluster_20260520.zh.md](wp10_window_loop_injection_cluster_20260520.zh.md)

Inputs:

- [WP10 causal runtime foundation](causal_runtime_foundation_wp10_20260520.md)
- [WP10-A manifest registry](wp10_manifest_registry_cluster_20260520.md)
- [WP2.5 state/barrier cluster](../wp25_scheduler_semantics/wp25_state_barrier_cluster_20260519.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.md)

## 1. Purpose

`WP10-B` adds the minimal scheduling-window loop skeleton and the first
cross-layer request injection semantics for the selected slice.

The loop proves the architecture's `collect -> inject -> DAG -> commit ->
export` shape without replacing the global scheduler.

## 2. Scope

In scope:

- define a small scheduling-window context for the selected slice;
- collect facade-compatible graph inputs into an ingress queue;
- classify arrived requests as accepted, future-window, rejected, or expired;
- make accepted requests visible only after `input_injection`;
- run the selected manifest-derived node sequence;
- cross `window_commit` and `export` barriers with stable ids;
- add focused tests for barrier sequence and request visibility.

Out of scope:

- full multi-rate scheduler;
- strict clock-domain skip/merge enforcement;
- `ActionHoldPolicy` runtime cadence;
- global ECS scheduler replacement;
- broad policy/control/physics cadence proof.

## 3. Minimal Window Contract

The first loop skeleton should expose or internally record:

| Field | Meaning |
|-------|---------|
| `window_id` | Stable id or sequence for the scheduling window under test. |
| `world_id` | World identity used by event/snapshot evidence. |
| `source_time_s` | Simulated source time for the current window. |
| `barrier_sequence` | Monotonic sequence used to distinguish repeated barriers. |
| `current_barrier_id` | One of `input_injection`, `stage_publish`, `window_commit`, `export`. |
| `accepted_inputs` | Requests admitted to current-window maintained logic. |
| `deferred_inputs` | Requests whose `effective_time` is beyond the current window. |
| `rejected_inputs` | Invalid requests, including bad metadata or incompatible merge policy. |
| `expired_inputs` | Requests whose `valid_until` is older than the current window. |

## 4. Request Injection Rules

Every injected request must carry:

- `source_layer`;
- `source_id`;
- `input_snapshot_version`;
- `effective_time`;
- `valid_until`;
- `merge_policy`;
- request family or packet type.

Visibility rules:

1. Before `input_injection`, arrived requests may sit in ingress buffers but
   maintained stage nodes cannot consume them.
2. After `input_injection`, only accepted current-window requests become visible
   to nodes whose manifest declares matching input packets and
   `read_snapshot_policy: post_injection`.
3. Future-window requests remain deferred and invisible to the current window.
4. Expired or invalid requests are rejected or recorded as diagnostics-only; they
   do not mutate maintained state.

## 5. Acceptance Tests

Minimum tests:

- barrier sequence is recorded as `input_injection -> execution/stage_publish
  where applicable -> window_commit -> export`;
- accepted requests are visible only after `input_injection`;
- future-window requests are deferred;
- expired requests are not consumed in the current window;
- invalid metadata fails closed;
- the loop consumes manifest registry node ids from `WP10-A`.

## 6. Handoff Contract

Return:

- loop and injection file paths;
- accepted/deferred/rejected/expired semantics implemented;
- tests added or updated;
- commands run and outcomes;
- any shared facade or binding files touched;
- integration notes for `WP10-C/D/E`.
