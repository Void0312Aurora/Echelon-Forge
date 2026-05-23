# WP10-A Manifest Registry Seed

Status: `2026-05-20` planned WP10 dispatch sheet.

Language:

- English canonical: `wp10_manifest_registry_cluster_20260520.md`
- Chinese companion:
  [wp10_manifest_registry_cluster_20260520.zh.md](wp10_manifest_registry_cluster_20260520.zh.md)

Inputs:

- [WP10 causal runtime foundation](causal_runtime_foundation_wp10_20260520.md)
- [WP2.5 manifest/event cluster](../wp25_scheduler_semantics/wp25_manifest_event_cluster_20260519.md)
- [WP2.5 state/barrier cluster](../wp25_scheduler_semantics/wp25_state_barrier_cluster_20260519.md)
- [Post-WP9 route plan](../post_wp9_architecture_route_plan_20260520.md)

## 1. Purpose

`WP10-A` creates the first code-owned `StageNodeManifest` registry for the
selected engagement/observation slice. Later WP10 streams consume this registry;
they must not redefine manifest fields locally.

## 2. Scope

In scope:

- choose the registry location and public query API;
- encode stable `node_id` values for selected `P7`, `P9`, and `P10` nodes;
- encode required WP2.5 manifest fields for those nodes;
- add fixtures or builders that architecture tests can enumerate;
- mark clock domains advisory in WP10 rather than strictly enforced.

Out of scope:

- inventorying every runtime system;
- generating a full schema compiler;
- changing facade export behavior beyond compile-facing type exposure;
- enforcing clock-domain cadence.

## 3. Required Manifest Fields

Every WP10 maintained node in the selected slice must declare:

| Field group | Required fields |
|-------------|-----------------|
| Identity | `node_id`, `semantic_stage`, `owner_module` |
| Contracts | `input_packets`, `output_packets`, `event_families_emitted` |
| State | `read_state_shards`, `write_state_shards`, `read_snapshot_policy`, `write_commit_policy` |
| Time and visibility | `clock_domain`, `latency_policy`, `sync_policy`, `required_barriers`, `facade_visibility` |
| Same-window | `allowed_same_window_edges` when `write_commit_policy = stage_publish` or same-window visibility is claimed |
| Diagnostics | `diagnostic_trace_obligations`, source snapshot or shard ancestry requirements |
| Compatibility | `compatibility_adapter_allowed` when legacy/raw access remains reachable |

## 4. Candidate Slice Nodes

| Node candidate | Semantic stage | Initial role | Expected visibility |
|----------------|----------------|--------------|---------------------|
| `p7.fire_control_launch.v1` | `P7 FireControlLaunch` | Launch request admission, fire-control gating, launch event publication. | Maintained stage node with facade request ancestry. |
| `p9.effects_damage.v1` | `P9 EffectsDamage` | Effects/damage event and damage-state commit evidence. | Maintained stage node or diagnostic bridge if current code cannot yet commit the shard. |
| `p10.observation_export.v1` | `P10 ObservationExport` | Recent engagement events, diagnostics trace, and observation/facade export. | Maintained facade export. |

The worker may rename node ids only if the names remain stable, deterministic,
and documented in the handoff.

## 5. Acceptance Tests

Minimum tests:

- an architecture test enumerates all WP10 maintained manifest records;
- missing required fields fail closed;
- same-window publish claims require non-empty `allowed_same_window_edges`;
- compatibility nodes cannot be reported as maintained scheduler truth;
- event-emitting nodes declare event family and diagnostics obligations.

## 6. Handoff Contract

Return:

- registry file paths and public query functions;
- node ids and any deliberate deviations from the candidate list;
- tests added or updated;
- commands run and outcomes;
- fields left advisory rather than enforced;
- integration notes for `WP10-B/C/D`.
