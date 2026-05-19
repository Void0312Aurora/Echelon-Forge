# WP2.5-B + WP2.5-C State Shard Versioning and Barrier Visibility Sheet

Status: `2026-05-19` normative dispatch sheet for WP2.5 execution.

Language:

- English canonical: `wp25_state_barrier_cluster_20260519.md`
- Chinese companion: [wp25_state_barrier_cluster_20260519.zh.md](wp25_state_barrier_cluster_20260519.zh.md)

Inputs:

- [WP2.5 Scheduler Semantics Freeze](scheduler_semantics_wp25_20260519.md)
- [WP2.5-F + WP2.5-A Manifest/Event Cluster](wp25_manifest_event_cluster_20260519.md)
- [Simulation System Architecture Design](../../plan/architecture/simulation_system_architecture_design.md)
- [architecture plan review](../review/architecture_plan_review_20260519.md)
- [temporary review source](../review/temp-01.md)

## 1. Purpose

This sheet converts the WP2.5 state/barrier draft into a normative task package.
It is intended for subagents that will review or implement scheduler semantics
later without inventing additional rules.

Normative terms:

- `MUST` and `MUST NOT` define required WP2.5 behavior.
- `SHOULD` defines the preferred rule unless a later review records a reasoned
  exception.
- `MAY` defines an allowed but non-required diagnostic or documentation choice.

## 2. Scope and Non-Goals

In scope:

- state shard vocabulary, owner stages, commit triggers, and increment rules;
- `SnapshotVersion` structure, example, and naming rules;
- barrier visibility before and after `input_injection`, `stage_publish`,
  `window_commit`, and `export`;
- same-window legality based on producer publish intent and consumer declared
  read set;
- diagnostics obligations consumed by replay, facade export, and
  `StageNodeManifest` declarations;
- manifest fields:
  `read_state_shards`, `write_state_shards`, `read_snapshot_policy`,
  `write_commit_policy`, `allowed_same_window_edges`, `required_barriers`,
  `diagnostic_trace_obligations`, and `facade_visibility`.

Out of scope:

- runtime scheduler implementation or refactor;
- event ordering redesign;
- clock-domain merge policy beyond referencing committed snapshot versions;
- replay harness implementation;
- facade API expansion;
- WP3 reopening;
- machine-readable manifest registry or generated schema.

## 3. Dispatch Slices

| Slice | Focus | Required output | Reasoning budget |
|-------|-------|-----------------|------------------|
| `B1` | Shard ownership and increment policy. | Complete shard/version table and exception notes. | Medium |
| `B2` | Snapshot naming and diagnostics obligations. | `SnapshotVersion` example, naming rules, and export diagnostics checklist. | Medium |
| `C1` | Barrier matrix and same-window legality. | Before/after visibility matrix and legality rules. | High |
| `C2` | Acceptance examples and manifest alignment. | Manifest field mapping, acceptance criteria, and resolved/open-question list. | Medium |

Parallelism rules:

1. `B1` and `B2` SHOULD stay in one owner if the shard names are still moving.
2. `C1` MAY run in parallel after shard names are stable.
3. No two workers should edit the same barrier matrix or snapshot example at
   the same time.
4. A worker that changes same-window legality MUST re-check diagnostics and
   manifest alignment in this sheet.

## 4. Shard and Version Rules

Maintained scheduler semantics MUST be shard-ready even when an early CPU-only
path exposes one global snapshot version.

| Shard | Owner stages | Committed contents | Commit trigger | Increment rule | Diagnostics obligation |
|-------|--------------|--------------------|----------------|----------------|------------------------|
| `setup` | `P0`, `P1` | Scenario content ids, world setup, initial entity refs, static environment refs. | Setup/reset commit before runtime windows. | Increment once per accepted setup/reset commit; do not increment for read-only content lookup. | Record content id set, setup manifest id, `barrier_id`, and resulting `setup` version. |
| `tasking` | `P2` | Accepted task orders, authority state, coordination intent admitted into the DAG. | Tasking state commit at `window_commit` or a declared delayed task event commit. | Increment when accepted tasking state changes; reject or diagnostics-only inputs do not increment. | Record source request ids, input snapshot version, accepted/rejected status, and target `effective_time`. |
| `command` | `P3` | Delivered commands, pending command queues, link-delivery state, command reports. | Command delivery or queue mutation commit. | Increment when delivered command state or pending queues change; pure inspection does not increment. | Record command id, link/report ancestry, delivery timestamp, and source `tasking`/`track` versions when consumed. |
| `control` | `P4` | Resolved action/control state, actuator intent, validity reports. | Control handoff commit. | Increment when resolved control input or validity state changes. | Record controlling request/event id, validity window, consumed `command` version, and rejection reason if not maintained. |
| `physics` | `P5` | Truth pose, velocity, orientation, contacts, physical environment state. | Physics integration window commit. | Increment once per committed integration window that mutates physical state; same-window temporary integration state does not increment. | Record integration window, source `control` version, prior `physics` version, and deterministic backend profile. |
| `track` | `P6` | Detections, fused tracks, link reports, shared situation snapshots. | Track/link snapshot commit. | Increment when a maintained detection, fusion, or link snapshot is committed. | Record source time, source `physics` version, sensor/link producer id, and any held/interpolated source versions. |
| `engagement` | `P7`, `P8` | Launch decisions, munition refs, munition lifecycle state, seeker/fuze/effects trigger candidates. | Fire-control launch or munition lifecycle commit. | Increment when launch acceptance, munition state, seeker/fuze state, or trigger candidate state changes. | Record parent request/event id, munition/entity ref, consumed `track`/`physics`/`control` versions, and emitted event id. |
| `damage` | `P9` | Damage reports, platform damage state, capability degradation, kill/loss state. | Effects/damage commit. | Increment when damage, capability, or kill/loss state changes. If capability-bearing state in another shard changes, increment that shard at the same `window_commit`. | Record effects event id, affected entity refs, prior and resulting capability state, source `engagement`/`physics` versions, and any coupled shard increments. |
| `observation` | `P10` | Observation packet versions, diagnostics trace exports, mirrored episode/status views. | Exportable observation snapshot production at `export` after a committed source snapshot. | Increment when a maintained facade/observation packet version is produced. Diagnostics-only pre-commit views MUST NOT increment the maintained `observation` shard. | Record exported packet id, source `SnapshotVersion`, export barrier detail, facade visibility label, and diagnostics-only flag when applicable. |

Additional rules:

1. A write MUST increment the target shard only at its declared commit trigger.
2. `global_version` MUST increment whenever any maintained shard version
   increments.
3. Multiple shard increments in the same `window_commit` share one
   `global_version` value for the resulting committed snapshot.
4. Stage-local temporary writes MUST NOT change shard versions.
5. Same-window published outputs MUST NOT change shard versions until their
   owning write commits.
6. Rejected, diagnostics-only, or compatibility-only observations MUST NOT
   define maintained shard truth.

## 5. SnapshotVersion Contract

Canonical shape:

```yaml
SnapshotVersion:
  name: sv.world_alpha.g000042.window_commit.000017
  world_id: world_alpha
  global_version: 42
  shard_versions:
    setup: 1
    tasking: 8
    command: 11
    control: 21
    physics: 42
    track: 17
    engagement: 6
    damage: 3
    observation: 15
  source_time: 12.500s
  barrier_id: window_commit
  barrier_sequence: 17
  barrier_detail: physics_tick_250
```

Naming rules:

1. `name` SHOULD use
   `sv.<world_id>.g<global_version>.<barrier_id>.<barrier_sequence>`.
2. `world_id` MUST be stable within the replay scope and MUST NOT depend on
   memory addresses or allocation order.
3. `global_version` MUST be zero-padded in diagnostic names for readability,
   but numeric comparison MUST use the integer field, not lexical order.
4. `barrier_id` MUST be one of `input_injection`, `stage_publish`,
   `window_commit`, or `export`.
5. More specific labels MAY be recorded in `barrier_detail`; they MUST NOT
   replace the frozen `barrier_id`.
6. `source_time` is simulated time. Wall-clock time MUST NOT be used as a
   snapshot ordering key.
7. `shard_versions` MUST use the shard keys in Section 4 exactly.
8. A facade-visible packet MUST name the `SnapshotVersion` it read or exported.
9. A maintained event emitted from a stage that read state MUST record the
   relevant source `SnapshotVersion` or source shard versions.

## 6. Barrier Visibility Matrix

| Barrier | Before visibility | After visibility | Legal readers after barrier | Explicit exclusions |
|---------|-------------------|------------------|-----------------------------|---------------------|
| `input_injection` | External/facade/policy/human requests may exist in ingress buffers, but scheduled stage nodes cannot consume them as maintained inputs. State shards remain at the prior committed snapshot. | Accepted requests whose `effective_time` enters the current window and whose source metadata is valid become visible as injected inputs. | Nodes whose manifest declares matching `input_packets`, `read_snapshot_policy: post_injection`, and the required `input_injection` barrier. | Does not expose state writes. Late, invalid, or future-effective requests are rejected or deferred and remain invisible to current-window maintained logic. |
| `stage_publish` | Producer stage-local writes and draft outputs are invisible outside the producing node. | Outputs explicitly marked by the producer as same-window visible become visible to declared downstream consumers. | Consumers named in `allowed_same_window_edges` whose manifest declares `read_snapshot_policy: same_window` and a matching read set. | Does not commit shard versions, does not create a general read-after-write channel, and does not permit undeclared consumers. |
| `window_commit` | Same-window published outputs may have been consumed by legal downstream nodes, but shard versions still represent the previous committed snapshot until commit. | Maintained writes become committed shard versions; future event-queue inserts become replay-visible; the resulting `SnapshotVersion` is available to next-window nodes and default `P10` export. | Next-window nodes, replay log construction, post-commit diagnostics, and `P10 ObservationExport` by default. | Pre-commit diagnostic views cannot become policy/training truth. Failed or diagnostics-only writes do not commit. |
| `export` | Frontends, policy consumers, tests, and replay validators can only rely on previously exported maintained packets or committed snapshots. | Facade packets, observation views, diagnostics traces, and mirrored status become visible with source snapshot and barrier metadata. | Frontends, tests, policy consumers, replay validators, and diagnostics tools according to `facade_visibility`. | Diagnostics-only pre-commit exports must be labeled and excluded from maintained truth, policy training truth, and replay parity assertions. |

Visibility rules:

1. The default read snapshot for maintained stage logic is the latest committed
   `SnapshotVersion` available at the stage's declared barrier.
2. `input_injection` changes input availability, not committed state shard
   versions.
3. `stage_publish` is an intra-window visibility edge, not a commit.
4. `window_commit` is the only barrier in this cluster that commits maintained
   state shard versions.
5. `export` publishes views over committed snapshots unless the packet is
   explicitly labeled diagnostics-only.

## 7. Same-Window Legality

Same-window reads are legal only when producer intent and consumer declaration
both permit the edge.

Required producer conditions:

1. The producer manifest MUST declare the output packet or state-derived output.
2. `write_commit_policy` MUST be `stage_publish` for the output consumed in the
   same window.
3. `allowed_same_window_edges` MUST include the consumer node id or an allowed
   downstream stage family.
4. The producer MUST name the published shard or packet and preserve a
   diagnostic link to the eventual committed shard version or event id.
5. The publish must fit an acyclic deterministic window DAG.

Required consumer conditions:

1. The consumer manifest MUST declare `read_snapshot_policy: same_window`.
2. The consumer `read_state_shards` or `input_packets` MUST include the exact
   shard/packet published by the producer.
3. The consumer `required_barriers` MUST include `stage_publish`.
4. The consumer diagnostics MUST record producer node id, producer output id,
   source shard version before commit, and the current scheduling window.

Legality table:

| Producer publish intent | Consumer declared read set | Same-window result |
|-------------------------|----------------------------|--------------------|
| `stage_publish` and consumer is named in `allowed_same_window_edges`. | Matching `read_snapshot_policy: same_window` plus matching shard/packet. | Allowed after `stage_publish`; no shard version increment until `window_commit`. |
| `stage_publish`, but consumer is not named or DAG order is ambiguous. | Any read set. | Prohibited as maintained behavior; reject or diagnostics-only. |
| `window_commit` only. | `same_window` read requested. | Prohibited; consumer must wait for next committed `SnapshotVersion`. |
| `delayed_event` or future `effective_time`. | Any current-window read set. | Prohibited in the current window; consume when the event enters its declared window. |
| `export_only` or `diagnostic_only`. | Maintained stage read set. | Prohibited as scheduler truth; may be visible only through diagnostics/export paths. |
| `stage_publish`. | Consumer lacks the matching shard/packet in `read_state_shards` or `input_packets`. | Prohibited; manifest read set is the authority. |

## 8. Diagnostics Checklist

Every maintained event, committed state mutation, or facade-visible packet that
uses this sheet MUST record enough information to reconstruct its barrier and
snapshot context.

Minimum fields:

- `world_id`;
- scheduling window id or simulated time window;
- `barrier_id` and optional `barrier_detail`;
- producer `node_id` or external `source_id`;
- consumer `node_id` for same-window edges;
- source `SnapshotVersion` or exact source shard versions;
- resulting `SnapshotVersion` for committed or exported outputs;
- event id or packet id when an event/export is produced;
- diagnostics-only or compatibility label when the output is not maintained
  truth.

Export-specific rules:

1. Maintained facade/observation packets MUST record the committed
   `SnapshotVersion` they read.
2. Diagnostics-only pre-commit views MUST record the pre-commit barrier context
   and MUST NOT be consumed as policy/training truth.
3. A same-window diagnostic trace MUST record both the pre-commit source shard
   version and the later committed version if the write commits.

## 9. Manifest Alignment

| Manifest field | Required alignment for this cluster |
|----------------|-------------------------------------|
| `read_state_shards` | Must use shard names from Section 4. Same-window consumers must include the exact shard they read. |
| `write_state_shards` | Must name every maintained shard that can increment at commit. Coupled `damage` capability updates must name all affected shards. |
| `read_snapshot_policy` | Must be one of `pre_window`, `post_injection`, `same_window`, `committed`, or `diagnostic_only`; same-window reads require Section 7 compliance. |
| `write_commit_policy` | Must distinguish `stage_publish`, `window_commit`, `delayed_event`, `export_only`, and `diagnostic_only`. |
| `allowed_same_window_edges` | Must be empty or explicit; wildcard same-window visibility is not maintained. |
| `required_barriers` | Must name the barriers required before/after the node runs. |
| `diagnostic_trace_obligations` | Must include snapshot, shard, barrier, producer, and consumer fields needed by Sections 5, 7, and 8. |
| `facade_visibility` | Must distinguish maintained facade surfaces from compatibility or diagnostics-only outputs. |

## 10. Acceptance Criteria

This cluster is accepted when:

1. every shard has an owner-stage set, committed contents, commit trigger,
   increment rule, and diagnostics obligation;
2. `SnapshotVersion` has a concrete example and stable naming rules;
3. each barrier has explicit before/after visibility;
4. same-window legality depends on both producer publish intent and consumer
   declared read set;
5. diagnostics obligations are explicit for state commits, same-window edges,
   and exports;
6. runtime scheduler implementation remains out of scope;
7. English and Chinese task sheets are section-aligned.

## 11. Resolved Decisions and Remaining Questions

Resolved decisions:

1. `observation` remains a maintained shard for export packet versions, but
   diagnostics-only pre-commit views do not increment it.
2. `barrier_id` is limited to the four frozen barrier names; richer labels use
   `barrier_detail`.
3. Maintained exports record their source `SnapshotVersion`; same-window and
   replay-sensitive paths record exact source shard versions.
4. Same-window legality is determined by both producer publish intent and
   consumer declared read set.
5. Pre-commit diagnostic views are allowed only as diagnostics-only paths and
   are excluded from policy/training truth.

Remaining questions for later work:

1. Whether the future machine-readable manifest registry should normalize
   `barrier_detail` values.
2. Whether implementation tests should require all exports to record full shard
   maps or allow compact source-shard subsets when no replay assertion depends
   on omitted shards.
