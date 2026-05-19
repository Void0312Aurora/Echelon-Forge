# WP2.5 Scheduler Semantics Freeze

Status: `2026-05-19` scheduler semantics freeze complete.

Language:

- English canonical: `scheduler_semantics_wp25_20260519.md`
- Chinese companion: [scheduler_semantics_wp25_20260519.zh.md](scheduler_semantics_wp25_20260519.zh.md)

Inputs:

- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [WP2 contract freeze](contract_freeze_wp2_20260519.md)
- [architecture plan review](../review/architecture_plan_review_20260519.md)
- [temporary review source](../review/temp-01.md)
- [WP2.5 scheduler semantics acceptance review](../review/wp25_scheduler_semantics_acceptance_review_20260519.md)

WP2.5 is a documentation-only semantic freeze inserted between `WP2 Contract
Freeze` and `WP4 Facade Alignment`. It does not reopen the accepted `WP3
Engagement Pilot`, and it does not implement a scheduler. Its job is to turn
the architecture concepts `StateStore`, `EventQueue`, `ClockDomain`, `Barrier`,
and `StageNodeManifest` into rules that future implementation work can test
against.

## 1. Freeze Position

The architecture baseline already states that `P0-P10` is a semantic lifecycle
and that real execution is a multi-rate temporal DAG. The review finding is
that several scheduler concepts were correct but still too implicit:

1. event family priority was named but not tabulated,
2. deterministic `event_id` generation was not pinned down,
3. state shard versions had no increment rule,
4. barrier visibility did not say which reads observe pre-commit versus
   post-commit state,
5. independent clock domains lacked a merge rule,
6. stage-node declarations were not yet formalized as a manifest.

WP2.5 freezes the minimum semantic rules needed before facade hardening and the
validation harness depend on them.

Acceptance note: WP2.5 is accepted as a documentation/specification freeze in
the [WP2.5 scheduler semantics acceptance review](../review/wp25_scheduler_semantics_acceptance_review_20260519.md).

Non-goals:

- no runtime scheduler rewrite,
- no Flecs pipeline migration,
- no GPU or resident-state implementation,
- no change to the accepted WP3 engagement pilot,
- no new public facade API unless a later WP4 task explicitly needs one.

## 2. Deliverables

| Deliverable | Frozen in this document | Later implementation target |
|-------------|-------------------------|-----------------------------|
| `event_family_priority_table.md` | Event ordering table and deterministic `event_id` rule. | Machine-readable event family registry. |
| `state_shard_versioning_rules.md` | Shard vocabulary, increment policy, and snapshot naming. | State-store or backend sync implementation. |
| `barrier_visibility_rules.md` | Read/write visibility across injection, stage, commit, and export barriers. | Scheduler tests and observation/export guards. |
| `clock_domain_merge_rules.md` | Nested triggering default and explicit merge rules for independent domains. | Multi-rate scheduler implementation. |
| `deterministic_replay_contract.md` | Replay log inputs, sort keys, and forbidden nondeterministic dependencies. | Replay harness under WP5 or later. |
| `stage_node_manifest_schema.md` | Required manifest fields for stage-node governance. | Markdown-to-schema registry, lint, or generated manifests. |

These names may later become separate files if implementation volume justifies
it. For the current freeze, the normative content lives here to keep the
semantic surface compact.

## 3. Event Family Priority

Maintained event behavior must sort by:

```text
(timestamp, priority, event_id)
```

`timestamp` is simulated time, `priority` is fixed by event family, and
`event_id` is deterministic. Insert order is not a maintained tie-breaker.

Initial priority table:

| Priority | Event family | Typical producer | Visibility intent |
|----------|--------------|------------------|-------------------|
| `000` | setup and reset events | `P1 WorldSetup` | Establishes initial state before runtime events. |
| `100` | external intent injection | facade, policy, orchestration, human, diagnostic adapters | Makes arrived cross-layer requests visible before scheduled nodes run. |
| `200` | tasking and command delivery | `P2 TaskingIntent`, `P3 CommandDelivery` | Materializes tasking, link latency, command arrival, and drop events. |
| `300` | platform control handoff | `P4 PlatformControl` | Records resolved control intent and validity outcomes. |
| `400` | physics/contact candidates | `P5 PhysicsStep` | Publishes committed physical-state or contact candidate events. |
| `500` | sensing, track, and link updates | `P6 SenseTrackLink` | Publishes track snapshots, link reports, and detection/fusion events. |
| `600` | fire-control and launch | `P7 FireControlLaunch` | Records accepted/rejected launch decisions and munition spawn ancestry. |
| `700` | munition lifecycle | `P8 MunitionLifecycle` | Records seeker, guidance, fuze-arm, terminal, miss, or effects trigger candidates. |
| `800` | effects and damage | `P9 EffectsDamage` | Applies effects, damage reports, kill/loss transitions, and capability deltas. |
| `900` | observation, diagnostics, and export | `P10 ObservationExport` | Exports committed snapshots, diagnostics traces, and facade packets. |

Deterministic `event_id` rule:

```text
event_id = stable_hash(run_seed, world_id, producing_node_id, event_family, local_sequence)
```

Requirements:

1. `producing_node_id` comes from `StageNodeManifest.node_id`.
2. `local_sequence` is counted within one producing node, one event family, one
   scheduling window, and one world.
3. Parallel producers must not allocate event ids from a shared mutable counter
   unless the counter order is itself derived from deterministic node order.
4. Compatibility paths that cannot produce deterministic ids must tag exports
   as diagnostics-only until wrapped by a maintained event producer.

## 4. State Shard Versioning

Early CPU-only execution may expose one global snapshot version, but maintained
scheduler semantics must be shard-ready.

Initial shard vocabulary:

| Shard | Owned stages | Includes | Minimum version increment rule |
|-------|--------------|----------|--------------------------------|
| `setup` | `P0`, `P1` | content ids, world setup, initial entity refs, static environment refs | Increment on setup/reset commit. |
| `tasking` | `P2` | task orders, authority state, coordination intent accepted into the DAG | Increment when tasking state commits. |
| `command` | `P3` | delivered commands, pending queues, link state, command reports | Increment when delivery state or queues commit. |
| `control` | `P4` | resolved action/control state, actuator intent, validity reports | Increment when control inputs commit. |
| `physics` | `P5` | truth position/velocity/orientation, contacts, physical environment state | Increment when a physics integration window commits. |
| `track` | `P6` | detections, fused tracks, link reports, shared situation snapshots | Increment when a track/link snapshot commits. |
| `engagement` | `P7`, `P8` | launch events, munition refs, munition lifecycle state, fuze/effects trigger candidates | Increment when launch or munition lifecycle state commits. |
| `damage` | `P9` | damage reports, platform damage state, capability degradation, kill/loss state | Increment when damage or capability effects commit. |
| `observation` | `P10` | observation packet versions, diagnostics trace export, mirrored episode status | Increment when an exportable observation snapshot is produced. |

Snapshot naming:

```text
SnapshotVersion = {
  global_version,
  shard_versions: map<state_shard, version>,
  source_time,
  barrier_id
}
```

Rules:

1. A write increments the target shard only at a commit barrier, not at every
   internal temporary mutation.
2. `global_version` increments whenever any maintained shard commits.
3. A stage node that reads multiple shards must record all source shard
   versions in diagnostics when it emits an event or facade-visible packet.
4. Observation packets must state which committed snapshot they read.
5. Damage-to-capability feedback must write `damage` and, when capability
   state changes, the affected capability-bearing shard. Fire-control or sensor
   nodes observe that change only after the declared barrier.

## 5. Barrier Visibility

The maintained scheduling window has four semantic barriers:

| Barrier | Position | Writes becoming visible | Required readers |
|---------|----------|-------------------------|------------------|
| `input_injection` | Before scheduled stage nodes run. | Arrived facade, policy, orchestration, human, and diagnostic requests. | `P2`, `P3`, `P4`, or later nodes whose manifest read set includes injected inputs. |
| `stage_publish` | Between same-window DAG nodes. | Writes explicitly marked same-window visible by the producing node. | Downstream nodes with data-derived same-window edges. |
| `window_commit` | After the acyclic window DAG completes. | Committed state shard versions and future event-queue inserts. | Next-window nodes and replay log. |
| `export` | After commit or at declared diagnostic/export slots. | Facade packets, observation views, diagnostics traces, and mirrored status. | Frontends, tests, policy consumers, and replay validators. |

Default visibility policy:

1. Stage-local temporary writes are invisible outside the producing node.
2. Same-window reads are legal only when the producing manifest declares a
   same-window output and the consuming manifest declares the corresponding
   read.
3. Cross-window feedback reads committed `SnapshotVersion` values only.
4. `P10 ObservationExport` reads post-`window_commit` snapshots by default.
   Pre-commit diagnostic views are allowed only when explicitly labeled as
   diagnostics and excluded from policy/training truth.
5. If a facade action should not affect the current window, it must carry an
   `effective_time` for a later window rather than relying on hidden call order.

## 6. Clock Domain Merge

Default rule:

```text
one outer scheduling window owns deterministic order;
lower-rate domains run as declared nested triggers inside that window.
```

Typical merge behavior:

| Clock domain relation | Maintained rule |
|-----------------------|-----------------|
| Integer multiple of base tick | Run on declared slot numbers; missed slots are replay errors unless explicitly skippable. |
| Lower-rate policy or control | Use `ActionHoldPolicy` or equivalent validity windows to consume one producer output across multiple control/physics ticks. |
| Event-driven damage or fuze | Enqueue timestamped events; consume them when their timestamp enters the current window. |
| Sensor/track scans | Produce snapshots with source time and shard versions; consumers must not assume physics tick equality. |
| Independent backend or resident-state clock | Not maintained until a backend profile declares sync barriers, event export order, and parity budget. |

Merge policy values:

| Value | Meaning |
|-------|---------|
| `nested_slot` | The producer runs in a deterministic slot within the outer window. |
| `hold_last` | The most recent valid producer output is reused until expiry. |
| `interpolate` | Consumer derives an intermediate value from two versioned producer outputs. |
| `enqueue_event` | Producer output becomes a timestamped event. |
| `defer_to_next_window` | Producer output is not visible until the next window. |
| `reject_on_ambiguous_order` | Scheduler or adapter rejects the input if deterministic order cannot be proven. |

## 7. Deterministic Replay Contract

A maintained replay must be reconstructable from:

1. static content ids and scenario setup,
2. run seed and deterministic backend profile,
3. facade and external producer requests with `source_id`,
   `input_snapshot_version`, `effective_time`, `valid_until`, and
   `merge_policy`,
4. `StageNodeManifest` registry,
5. event stream sorted by `(timestamp, priority, event_id)`,
6. committed `SnapshotVersion` sequence,
7. diagnostics traces that connect source requests, events, reports, and
   observation exports.

Forbidden maintained dependencies:

- event insertion order from nondeterministic container iteration,
- wall-clock timing as a tie-breaker,
- raw pointer addresses or entity allocation accidents as semantic ids,
- Python helper call order that is not reflected in facade request metadata,
- backend-specific thread completion order without a deterministic merge rule.

Replay tolerance:

1. CPU exact path is the reference.
2. Accelerated or approximate backends must declare their parity budget before
   being treated as maintained replay sources.
3. Diagnostics-only compatibility exports may be compared structurally but do
   not define scheduler truth.

## 8. StageNodeManifest Schema

Every maintained stage node should be describable by this manifest schema:

| Field | Requirement |
|-------|-------------|
| `node_id` | Stable unique id used by docs, tests, event ids, and diagnostics. |
| `semantic_stage` | One or more `P0-P10` stages. |
| `owner_module` | Owning source module, adapter, model family, or facade surface. |
| `input_packets` | Contract packets or requests consumed. |
| `output_packets` | Contract packets, reports, or facade exports produced. |
| `read_state_shards` | State shards and snapshot policy read by the node. |
| `write_state_shards` | State shards mutated or committed by the node. |
| `read_snapshot_policy` | `pre_window`, `post_injection`, `same_window`, `committed`, or `diagnostic_only`. |
| `write_commit_policy` | `stage_publish`, `window_commit`, `delayed_event`, `export_only`, or `diagnostic_only`. |
| `clock_domain` | Trigger cadence, event condition, or facade-requested export rule. |
| `latency_policy` | Same-window, next-window, delayed, link-latency controlled, or backend-sync controlled. |
| `sync_policy` | Host-owned, backend-owned, partial sync, observation-only sync, or explicit export. |
| `allowed_same_window_edges` | Downstream node ids or stage families allowed to read same-window outputs. |
| `required_barriers` | Barrier names that must occur before or after the node runs. |
| `event_families_emitted` | Event families and priorities emitted by this node. |
| `diagnostic_trace_obligations` | Trace ids, ancestry ids, or source snapshot versions that must be recorded. |
| `facade_visibility` | Maintained facade surface, compatibility adapter, diagnostics-only, or internal. |
| `compatibility_adapter_allowed` | Whether legacy/raw-runtime access may wrap this node and under what label. |

Minimal markdown example:

```yaml
node_id: p7.fire_control_launch.v1
semantic_stage: [P7 FireControlLaunch]
owner_module: src/core/engine/simulation_kernel_weapon_api.cpp
input_packets: [LaunchRequest, TrackPacket]
output_packets: [LaunchEvent, DiagnosticsTrace]
read_state_shards: [track, engagement, command]
write_state_shards: [engagement]
read_snapshot_policy: post_injection
write_commit_policy: window_commit
clock_domain: event_driven_or_fire_control_cadence
latency_policy: same_window_after_request_barrier
sync_policy: host_owned
allowed_same_window_edges: [p8.munition_lifecycle.*]
required_barriers: [input_injection, window_commit]
event_families_emitted: [fire_control_and_launch]
diagnostic_trace_obligations:
  - launch_request_id
  - launch_event_id
  - input_track_snapshot_version
facade_visibility: maintained_facade_export
compatibility_adapter_allowed: true_for_legacy_fire_missile_only
```

## 9. Workstream Map

WP2.5 is a freeze document, but the follow-on work should be organized as
bounded streams with explicit dependencies and ownership boundaries.

| Workstream | Focus | Dependencies | Parallelism | Reasoning budget | Exit artifact |
|------------|-------|--------------|-------------|------------------|---------------|
| `WP2.5-F StageNodeManifest Schema` | Define manifest fields, examples, ownership tags, and compatibility labels. | Baseline architecture document, review findings. | Start first and run in parallel with A-C once node vocabulary is stable. | High. | Manifest schema draft that other streams reference. |
| `WP2.5-A Event Ordering and ID Rules` | Finalize event families, priorities, deterministic ids, and allowed producers. | `StageNodeManifest` node ids, review findings. | Can run with B/C/F after shared naming is stable. | Medium. | Event ordering table ready for implementation tests. |
| `WP2.5-B State Shard Versioning` | Define shard vocabulary, commit boundaries, version increments, and snapshot naming. | Baseline state model, manifest schema. | Parallel with A/C/F. | Medium. | Shard/version rule set ready for later scheduler tests. |
| `WP2.5-C Barrier Visibility` | Define injection, stage_publish, window_commit, and export visibility plus same-window legality. | Manifest read/write fields, event ordering. | Parallel with A/B/F. | Medium. | Barrier rule set with explicit pre/post commit visibility. |
| `WP2.5-D Clock-Domain Merge` | Define nested triggering defaults and independent domain merge policies. | A, C, and F. | Starts after A/C/F are stable enough. | High. | Merge-policy matrix and clock-domain contract. |
| `WP2.5-E Deterministic Replay Contract` | Define replay inputs, prohibited nondeterminism, parity budget, and diagnostics obligations. | A-D plus F. | Serial integration after A-D. | High. | Replay contract suitable for WP5 harnessing. |
| `WP2.5-G Integration and Index Sync` | Sync README, architecture baseline, WP2 handoff, and validation notes. | All of the above. | Serial integration owner. | Medium. | Doc index aligned and ready for WP4/WP5 handoff. |

Dispatch artifacts:

- [WP2.5-F + WP2.5-A manifest/event cluster](wp25_manifest_event_cluster_20260519.md)
- [WP2.5-B + WP2.5-C state/barrier cluster](wp25_state_barrier_cluster_20260519.md)
- [WP2.5-D + WP2.5-E clock/replay cluster](wp25_clock_replay_cluster_20260519.md)

Suggested execution order:

1. `WP2.5-F` first, so every other stream can name the same node vocabulary.
2. `WP2.5-A`, `WP2.5-B`, and `WP2.5-C` in parallel once manifest fields are stable.
3. `WP2.5-D` after event ordering, barrier semantics, and manifest fields are stable.
4. `WP2.5-E` after A-D, because replay depends on the frozen semantics.
5. `WP2.5-G` last, as the serial integration and publication pass.

Recommended reasoning budget:

- High: `WP2.5-D` and `WP2.5-E`.
- Medium: the other streams.

## 10. WP2.5 Acceptance Gates

WP2.5 exits when:

1. The task tree links to this freeze from `README.md`,
   `README.zh.md`, and the WP2 handoff.
2. The architecture baseline names WP2.5 as the freeze plan for scheduler
   semantics.
3. Event ordering, state shard versioning, barrier visibility, clock-domain
   merge, replay, and `StageNodeManifest` schema have explicit rules.
4. The accepted WP3 pilot remains marked complete and is not re-scoped.
5. WP4 and WP5 can reference this document instead of inventing scheduler
   semantics in facade or validation work.

Recommended follow-on validation under WP5:

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\architecture
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_pytest_suite.py --suite tests\smoke\ci_smoke_suite.json
```

Future implementation may add architecture tests that parse this document or a
machine-readable manifest registry, but that is outside the WP2.5 documentation
freeze.
