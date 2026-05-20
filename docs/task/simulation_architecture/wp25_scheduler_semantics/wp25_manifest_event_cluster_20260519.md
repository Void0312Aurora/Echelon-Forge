# WP2.5-F + WP2.5-A Normative Dispatch Sheet: StageNodeManifest Schema and Event Ordering

Status: `2026-05-19` normative dispatch sheet.

Language:

- English canonical: `wp25_manifest_event_cluster_20260519.md`
- Chinese companion: [wp25_manifest_event_cluster_20260519.zh.md](wp25_manifest_event_cluster_20260519.zh.md)

Inputs:

- [WP2.5 scheduler semantics freeze](scheduler_semantics_wp25_20260519.md)
- [WP2.5-B + WP2.5-C state/barrier cluster](wp25_state_barrier_cluster_20260519.md)
- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [WP2 contract freeze](contract_freeze_wp2_20260519.md)
- [architecture plan review response](../review/architecture_plan_review_20260519.md)

Normative language:

- `MUST` marks required WP2.5 behavior for maintained documentation and later implementation.
- `MUST NOT` marks behavior that cannot define maintained scheduler truth.
- `SHOULD` marks the default rule; deviations need an explicit follow-up task or review note.
- `MAY` marks an allowed compatibility or documentation path.

## 1. Purpose

This dispatch sheet turns `WP2.5-F StageNodeManifest Schema` and
`WP2.5-A Event Ordering and ID Rules` into normative work items. It is a
documentation/specification task, not a runtime implementation task.

Later scheduler, facade, and replay work MUST be able to reference this sheet
without inventing new manifest vocabulary, event priority bands, producer
labels, or deterministic identity rules.

## 2. Normative Scope

This sheet freezes:

- the `StageNodeManifest` field set and per-field presence classification,
- manifest enum vocabulary for snapshot reads, commit/write visibility, facade
  visibility, compatibility labels, and producer categories,
- event ordering by `(timestamp, priority, event_id)`,
- deterministic `event_id` generation,
- the producer allowlist by event priority band,
- the diagnostics minimum for maintained events and facade-visible packets,
- task boundaries for subagents that refine or verify these rules.

This sheet does not implement a scheduler, generate a machine-readable schema,
or reopen WP3/WP4 behavior.

## 3. Dispatch Deliverables

| Stream | Required output | Owner profile | Reasoning budget |
|--------|-----------------|---------------|------------------|
| `WP2.5-F1` | Manifest field classification table and canonical examples. | Schema worker. | High. |
| `WP2.5-F2` | Enum vocabulary tables and compatibility-label rules. | Same owner as `F1`. | High. |
| `WP2.5-A1` | Event priority table and deterministic ordering statement. | Event semantics worker. | Medium-high. |
| `WP2.5-A2` | Producer allowlist matrix by priority band. | Event semantics worker coordinated with `F1/F2`. | High if any producer crosses facade or compatibility boundaries. |
| `WP2.5-A3` | Diagnostics minimums and open-question cleanup. | Event semantics worker coordinated with state/barrier owners. | Medium-high. |
| Cluster integration | English/Chinese section alignment and `git diff --check`. | Integration owner. | Medium. |

## 4. StageNodeManifest Field Classification

Presence classification:

- `Required`: the field MUST be present for every maintained stage-node manifest.
  Empty lists are allowed only where the rule below says so.
- `Conditional`: the field MUST be present when the condition is true; otherwise
  the manifest SHOULD omit it or set an empty/false value as stated.
- `Optional`: the field MAY be present for documentation clarity, but later
  implementation MUST NOT depend on it unless a separate schema freeze promotes
  it.

| Field | Classification | Value shape | Normative rule | Example |
|-------|----------------|-------------|----------------|---------|
| `node_id` | Required | Stable string id. | MUST be globally stable within the manifest registry and MUST be used as `producing_node_id` for maintained stage-node events. | `p7.fire_control_launch.v1` |
| `semantic_stage` | Required | Non-empty list of `P0-P10` stage names. | MUST name the semantic lifecycle stage or stages governed by the node. | `[P7 FireControlLaunch]` |
| `owner_module` | Required | Source module, adapter, model family, or facade surface. | MUST identify the maintained owner responsible for event emission and diagnostics. | `src/core/engine/simulation_kernel_weapon_api.cpp` |
| `input_packets` | Required | List of packet/request names; empty list allowed for setup-only nodes. | MUST enumerate consumed contract packets or requests. | `[LaunchRequest, TrackPacket]` |
| `output_packets` | Required | List of packet/report/export names; empty list allowed only for internal state-only nodes. | MUST enumerate produced packets, reports, or facade exports. | `[LaunchEvent, DiagnosticsTrace]` |
| `read_state_shards` | Required | List of shard names or shard/policy pairs. | MUST list every state shard whose committed or same-window version is read. | `[track, engagement, command]` |
| `write_state_shards` | Required | List of shard names; empty list allowed for pure export/diagnostic nodes. | MUST list every shard mutated or committed by the node. | `[engagement]` |
| `read_snapshot_policy` | Required | One value from the enum in section 5.1. | MUST describe the newest snapshot class the node may observe. | `post_injection` |
| `write_commit_policy` | Required | One value from the enum in section 5.2. | MUST describe when writes become visible outside the node. | `window_commit` |
| `clock_domain` | Required | Cadence, slot, event condition, or facade export rule. | MUST name the trigger domain consumed by clock-domain merge and replay work. | `event_driven_or_fire_control_cadence` |
| `latency_policy` | Required | Textual policy or later frozen enum value. | MUST state whether output is same-window, next-window, delayed, link-latency controlled, or backend-sync controlled. | `same_window_after_request_barrier` |
| `sync_policy` | Required | Textual policy or later frozen enum value. | MUST state whether state is host-owned, backend-owned, partially synced, observation-only, or explicitly exported. | `host_owned` |
| `allowed_same_window_edges` | Conditional | List of downstream node ids or stage families. | MUST be present and non-empty when `write_commit_policy = stage_publish` or when same-window output visibility is claimed; otherwise SHOULD be empty. | `[p8.munition_lifecycle.*]` |
| `required_barriers` | Required | List drawn from `input_injection`, `stage_publish`, `window_commit`, `export`. | MUST list barriers that must precede, follow, or gate node visibility. | `[input_injection, window_commit]` |
| `event_families_emitted` | Required | List of priority-band family names; empty list allowed only for non-emitting internal nodes. | MUST list every maintained event family emitted by this node. | `[fire_control_and_launch]` |
| `diagnostic_trace_obligations` | Required | List of required trace fields or ancestry links. | MUST cover the common diagnostics minimum in section 8 plus any family-specific additions. | `[launch_request_id, launch_event_id, input_track_snapshot_version]` |
| `facade_visibility` | Required | One value from the enum in section 5.3. | MUST state whether outputs are internal, maintained facade-visible, compatibility-only, or diagnostics-only. | `maintained_facade_export` |
| `compatibility_adapter_allowed` | Conditional | Boolean or compatibility label object. | MUST be present when legacy/raw-runtime access is allowed or when `facade_visibility = compatibility_adapter`; otherwise SHOULD be `false`. | `legacy_fire_missile: compatibility_diagnostics_only` |

No new `allowed_producers` manifest field is introduced in WP2.5. The producer
allowlist is normative in section 7 and MAY later be generated into a registry.

## 5. Manifest Enum Vocabulary

### 5.1 `read_snapshot_policy`

| Value | Meaning | Allowed visibility source |
|-------|---------|---------------------------|
| `pre_window` | Reads the snapshot committed before the current scheduling window starts. | Previous `window_commit`. |
| `post_injection` | Reads the pre-window snapshot plus arrived injected inputs accepted at `input_injection`. | `input_injection`. |
| `same_window` | Reads same-window outputs that were explicitly published by an upstream manifest edge. | `stage_publish` plus declared `allowed_same_window_edges`. |
| `committed` | Reads only committed shard versions. | Current or previous `window_commit`, depending on node position. |
| `diagnostic_only` | Reads a view that is not scheduler truth. | Declared diagnostics/export slot only. |

### 5.2 `write_commit_policy`

| Value | Meaning | Visibility rule |
|-------|---------|-----------------|
| `stage_publish` | Output becomes visible to declared same-window consumers. | Requires non-empty `allowed_same_window_edges` and a `stage_publish` barrier. |
| `window_commit` | Output becomes a committed state shard or future event insert after the window DAG completes. | Visible after `window_commit`. |
| `delayed_event` | Output becomes a timestamped event for a later window or declared event time. | Consumed when its timestamp enters a maintained window. |
| `export_only` | Output is only an observation/facade export over committed state. | Visible at `export`; does not mutate scheduler truth. |
| `diagnostic_only` | Output is debug/test/inspection material only. | MUST NOT define maintained scheduler truth or policy/training truth. |

### 5.3 `facade_visibility`

| Value | Meaning | Maintained status |
|-------|---------|-------------------|
| `internal` | Node output is not facade-visible. | Maintained if other manifest rules are satisfied. |
| `maintained_facade_surface` | Node consumes or exposes a maintained request surface. | Maintained; requires source metadata and diagnostics. |
| `maintained_facade_export` | Node emits maintained observation/export packets. | Maintained; requires committed `SnapshotVersion` ancestry. |
| `compatibility_adapter` | Node is reachable through a legacy/raw-runtime adapter. | Not maintained event truth unless wrapped by a maintained producer. |
| `diagnostics_only` | Node output is only for inspection, tests, or debug export. | Not maintained scheduler truth. |

### 5.4 Compatibility Labels

| Label | Meaning | Write permission |
|-------|---------|------------------|
| `maintained_stage_node` | Event is emitted by a manifest-declared stage node. | MAY write maintained event queues for declared families. |
| `maintained_facade_surface` | Event/request crosses a maintained facade surface with source metadata. | MAY produce priority `100` injection events; otherwise it is source ancestry for stage-node events. |
| `external_injection` | Policy, orchestration, human, or external source crosses `input_injection`. | MAY produce priority `100` injection events only. |
| `compatibility_diagnostics_only` | Legacy/raw-runtime path is not yet wrapped by maintained semantics. | MUST write diagnostics/export channels only. |
| `diagnostics_only` | Helper used for inspection, tests, or debug export. | MUST write diagnostics/export channels only. |

### 5.5 Producer Categories

| Producer category | Required label | Maintained event role | Required metadata |
|-------------------|----------------|-----------------------|-------------------|
| `stage_node` | `maintained_stage_node` | Primary maintained producer for bands `000`, `200-900` when the manifest declares the family. | `node_id`, `world_id`, `event_family`, `local_sequence`, source snapshots. |
| `runtime_facade` | `maintained_facade_surface` | Maintained producer for explicit injection/reset surfaces only; otherwise source ancestry. | `source_id`, `input_snapshot_version`, `effective_time`, `valid_until`, `merge_policy`. |
| `external_injection` | `external_injection` | Maintained producer for arrived external intent at priority `100`. | `source_id`, `effective_time`, `merge_policy`, authority/validity metadata. |
| `compatibility_adapter` | `compatibility_diagnostics_only` | Compatibility bridge only. | Legacy source ref, wrapper id when present, diagnostic reason. |
| `diagnostic_helper` | `diagnostics_only` | Inspection/test/debug only. | Test/debug id, source snapshot when available, diagnostic reason. |

## 6. Event Ordering and Deterministic IDs

Maintained event behavior MUST sort by:

```text
(timestamp, priority, event_id)
```

`timestamp` is simulated time. `priority` is fixed by the event family. `event_id`
is deterministic. Insert order, wall-clock time, pointer identity, entity
allocation accident, and nondeterministic container iteration MUST NOT be
semantic tie-breakers.

Priority bands:

| Priority | Event family | Typical maintained producer |
|----------|--------------|-----------------------------|
| `000` | setup and reset events | `P1 WorldSetup` or maintained reset surface. |
| `100` | external intent injection | facade, policy, orchestration, human, or declared injection adapter. |
| `200` | tasking and command delivery | `P2 TaskingIntent`, `P3 CommandDelivery`. |
| `300` | platform control handoff | `P4 PlatformControl`. |
| `400` | physics/contact candidates | `P5 PhysicsStep`. |
| `500` | sensing, track, and link updates | `P6 SenseTrackLink`. |
| `600` | fire-control and launch | `P7 FireControlLaunch`. |
| `700` | munition lifecycle | `P8 MunitionLifecycle`. |
| `800` | effects and damage | `P9 EffectsDamage`. |
| `900` | observation, diagnostics, and export | `P10 ObservationExport`. |

The deterministic `event_id` rule remains unchanged:

```text
event_id = stable_hash(run_seed, world_id, producing_node_id, event_family, local_sequence)
```

Requirements:

1. `producing_node_id` MUST come from `StageNodeManifest.node_id` for stage-node
   events, or from a maintained facade/external source id for priority `100`
   injection events.
2. `local_sequence` MUST be counted within one producing node or maintained
   source, one event family, one scheduling window, and one world.
3. Parallel producers MUST NOT allocate event ids from a shared mutable counter
   unless the counter order is itself derived from deterministic node order.
4. Compatibility paths that cannot produce deterministic ids MUST be labeled
   `compatibility_diagnostics_only` or `diagnostics_only`.

## 7. Producer Allowlist by Priority Band

This matrix is the WP2.5 producer allowlist. Later implementation may encode it
as a registry, but WP2.5 does not add a runtime registry or manifest field.

| Priority | Event family | Maintained producer categories | Conditional or compatibility producers | Explicitly disallowed as maintained truth |
|----------|--------------|--------------------------------|----------------------------------------|-------------------------------------------|
| `000` | setup and reset events | `stage_node`; `runtime_facade` only for declared maintained reset/setup surfaces. | `compatibility_adapter` may export diagnostics for legacy setup/reset. | `diagnostic_helper` and unwrapped compatibility paths. |
| `100` | external intent injection | `runtime_facade`; `external_injection`; declared injection `stage_node`. | `compatibility_adapter` only as `compatibility_diagnostics_only`. | Raw helper calls without `source_id`, `effective_time`, and `merge_policy`. |
| `200` | tasking and command delivery | `stage_node`. | `runtime_facade` and `external_injection` may be ancestry sources through priority `100`, not direct producers. | Direct facade writes to command/tasking maintained queues. |
| `300` | platform control handoff | `stage_node`. | Compatibility adapters may mirror diagnostics only. | Human/policy helpers bypassing tasking or command delivery. |
| `400` | physics/contact candidates | `stage_node`. | Backend compatibility exports are diagnostics-only until a backend profile declares deterministic merge/order. | Backend thread completion order or raw physics callback order. |
| `500` | sensing, track, and link updates | `stage_node`. | External sensor/link adapters must be wrapped by a maintained node or priority `100` injection path. | Direct diagnostic sensor writes to maintained track queues. |
| `600` | fire-control and launch | `stage_node`. | Facade launch requests are ancestry inputs; legacy fire-missile adapters are `compatibility_diagnostics_only` until wrapped. | Direct facade or compatibility writes to launch event queues. |
| `700` | munition lifecycle | `stage_node`. | Backend/legacy munition helpers may export diagnostics only. | Raw resident-state callbacks without deterministic ordering. |
| `800` | effects and damage | `stage_node`. | Compatibility damage calculators may emit diagnostics only until wrapped. | Direct mutation reports without shard versions and barrier ancestry. |
| `900` | observation, diagnostics, and export | `stage_node`; `runtime_facade` for maintained export surfaces. | `diagnostic_helper` and `compatibility_adapter` may write diagnostics/export channels, not scheduler truth. | Diagnostics-only material used as policy/training truth. |

## 8. Diagnostics Minimums

Every maintained event or facade-visible packet emitted by this cluster's
families MUST record:

- event identity: `event_id`, `event_family`, `timestamp`, `priority`;
- producer identity: `producing_node_id` or external `source_id`;
- ordering scope: `world_id`, scheduling window, and `local_sequence`;
- source versions: relevant `SnapshotVersion` or input snapshot fields;
- barrier ancestry: at least the barrier after which the event or packet became
  visible;
- ancestry links when available: request id, parent event id, entity ref, report
  id, or observation packet version;
- compatibility label when the source is not a maintained stage node.

Family-specific diagnostics MAY add required fields, but they MUST NOT remove
the common minimum above.

## 9. Canonical Manifest Examples

The example registry below is normative starter coverage for `P0-P10`. Each
entry is intentionally compact, but it must still use the frozen
`StageNodeManifest` vocabulary so later scheduler, facade, replay, and
validation work can cite one shared registry shape.

Maintained `P0 ContentCompile` example:

```yaml
node_id: p0.content_compile.v1
semantic_stage: [P0 ContentCompile]
owner_module: content/ and scenario compiler adapters
input_packets: [ScenarioDefinition, BackendProfileRequest]
output_packets: [WorldSetupPacket, ContentIdSet]
read_state_shards: [setup]
write_state_shards: [setup]
read_snapshot_policy: pre_window
write_commit_policy: window_commit
clock_domain: setup_only
latency_policy: same_window_setup
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [window_commit]
event_families_emitted: [setup_and_reset]
diagnostic_trace_obligations: [content_id_set, setup_commit_id]
facade_visibility: maintained_facade_surface
compatibility_adapter_allowed: false
```

Maintained `P1 WorldSetup` example:

```yaml
node_id: p1.world_setup.v1
semantic_stage: [P1 WorldSetup]
owner_module: src/runtime/facade/runtime_facade.cpp
input_packets: [WorldSetupPacket, BatchResetRequest]
output_packets: [WorldBatchPacket, EntityRefPacket]
read_state_shards: [setup]
write_state_shards: [setup]
read_snapshot_policy: post_injection
write_commit_policy: window_commit
clock_domain: reset_or_setup_request
latency_policy: same_window_after_request_barrier
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [input_injection, window_commit]
event_families_emitted: [setup_and_reset]
diagnostic_trace_obligations: [setup_commit_id, world_id]
facade_visibility: maintained_facade_surface
compatibility_adapter_allowed: false
```

Maintained `P2 TaskingIntent` example:

```yaml
node_id: p2.tasking_intent.v1
semantic_stage: [P2 TaskingIntent]
owner_module: components/tasking and core/mission
input_packets: [TaskOrder, LeaderIntent]
output_packets: [TaskingStatePacket, AuthorityStatePacket]
read_state_shards: [tasking, command]
write_state_shards: [tasking]
read_snapshot_policy: post_injection
write_commit_policy: window_commit
clock_domain: tasking_update_slot
latency_policy: same_window_after_request_barrier
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [input_injection, window_commit]
event_families_emitted: [tasking_and_command_delivery]
diagnostic_trace_obligations: [source_id, input_snapshot_version]
facade_visibility: maintained_facade_surface
compatibility_adapter_allowed: false
```

Maintained `P3 CommandDelivery` example:

```yaml
node_id: p3.command_delivery.v1
semantic_stage: [P3 CommandDelivery]
owner_module: command-link systems
input_packets: [MissionCommand, CoordinationIntentPacket]
output_packets: [DeliveredCommandPacket, CommandDeliveryReport]
read_state_shards: [tasking, command]
write_state_shards: [command]
read_snapshot_policy: post_injection
write_commit_policy: window_commit
clock_domain: command_link_tick
latency_policy: link_latency_controlled
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [input_injection, window_commit]
event_families_emitted: [tasking_and_command_delivery]
diagnostic_trace_obligations: [source_id, command_report_id]
facade_visibility: internal
compatibility_adapter_allowed: false
```

Maintained `P4 PlatformControl` example:

```yaml
node_id: p4.platform_control.v1
semantic_stage: [P4 PlatformControl]
owner_module: control models and platform systems
input_packets: [DeliveredCommandPacket, ActionIntentPacket]
output_packets: [ControlInputPacket, ActionValidityReport]
read_state_shards: [command, control, physics]
write_state_shards: [control]
read_snapshot_policy: committed
write_commit_policy: stage_publish
clock_domain: control_rate_slot
latency_policy: same_window_after_request_barrier
sync_policy: host_owned
allowed_same_window_edges: [p5.physics_step.v1]
required_barriers: [input_injection, stage_publish, window_commit]
event_families_emitted: [platform_control_handoff]
diagnostic_trace_obligations: [source_id, control_validity_report_id]
facade_visibility: internal
compatibility_adapter_allowed: false
```

Maintained `P5 PhysicsStep` example:

```yaml
node_id: p5.physics_step.v1
semantic_stage: [P5 PhysicsStep]
owner_module: physics systems and backends
input_packets: [ControlInputPacket, EnvironmentPacket]
output_packets: [TruthStatePacket, PhysicsTracePacket]
read_state_shards: [control, physics]
write_state_shards: [physics]
read_snapshot_policy: same_window
write_commit_policy: window_commit
clock_domain: physics.fixed_tick
latency_policy: same_window_after_control_publish
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [stage_publish, window_commit]
event_families_emitted: [physics_contact_candidates]
diagnostic_trace_obligations: [source_shard_versions, resulting_snapshot_version]
facade_visibility: internal
compatibility_adapter_allowed: false
```

Maintained `P6 SenseTrackLink` example:

```yaml
node_id: p6.sense_track_link.v1
semantic_stage: [P6 SenseTrackLink]
owner_module: sensor, EW, track, and data-link systems
input_packets: [TruthStatePacket, LinkStatePacket]
output_packets: [TrackPacket, DetectionPacket, SharedTrackReport]
read_state_shards: [physics, track, command]
write_state_shards: [track]
read_snapshot_policy: committed
write_commit_policy: window_commit
clock_domain: sensor.scan_slot
latency_policy: next_window_after_scan
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [window_commit]
event_families_emitted: [sensing_track_and_link_updates]
diagnostic_trace_obligations: [source_time, source_shard_versions, track_snapshot_version]
facade_visibility: maintained_facade_export
compatibility_adapter_allowed: false
```

Maintained `P7 FireControlLaunch` example:

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
allowed_same_window_edges: []
required_barriers: [input_injection, window_commit]
event_families_emitted: [fire_control_and_launch]
diagnostic_trace_obligations:
  - launch_request_id
  - launch_event_id
  - input_track_snapshot_version
facade_visibility: maintained_facade_export
compatibility_adapter_allowed:
  legacy_fire_missile: compatibility_diagnostics_only
```

Maintained `P8 MunitionLifecycle` example:

```yaml
node_id: p8.munition_lifecycle.v1
semantic_stage: [P8 MunitionLifecycle]
owner_module: guidance, seeker, and fuze systems
input_packets: [LaunchEvent, TrackPacket]
output_packets: [MunitionLifecyclePacket, DiagnosticsTrace]
read_state_shards: [engagement, track, physics]
write_state_shards: [engagement]
read_snapshot_policy: committed
write_commit_policy: window_commit
clock_domain: munition_guidance_slot
latency_policy: same_window_after_launch
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [window_commit]
event_families_emitted: [munition_lifecycle]
diagnostic_trace_obligations: [launch_event_id, munition_id, source_shard_versions]
facade_visibility: maintained_facade_export
compatibility_adapter_allowed: false
```

Maintained `P9 EffectsDamage` example:

```yaml
node_id: p9.effects_damage.v1
semantic_stage: [P9 EffectsDamage]
owner_module: effects models and damage systems
input_packets: [MunitionLifecyclePacket, EffectsTriggerCandidate]
output_packets: [EffectsEvent, DamageReport, DiagnosticsTrace]
read_state_shards: [engagement, damage, physics]
write_state_shards: [damage]
read_snapshot_policy: committed
write_commit_policy: window_commit
clock_domain: event_driven_effects_resolution
latency_policy: delayed_event
sync_policy: host_owned
allowed_same_window_edges: []
required_barriers: [window_commit]
event_families_emitted: [effects_and_damage]
diagnostic_trace_obligations: [launch_event_id, effects_event_id, damage_report_id]
facade_visibility: maintained_facade_export
compatibility_adapter_allowed: false
```

Maintained `P10 ObservationExport` example:

```yaml
node_id: p10.observation_export.v1
semantic_stage: [P10 ObservationExport]
owner_module: src/core/engine/simulation_kernel_observation_api.cpp
input_packets: [CommittedSnapshot, DiagnosticsTrace]
output_packets: [ObservationPacket, DiagnosticsTraceBatchPacket]
read_state_shards: [setup, tasking, command, control, physics, track, engagement, damage, observation]
write_state_shards: [observation]
read_snapshot_policy: committed
write_commit_policy: export_only
clock_domain: export_slot_after_window_commit
latency_policy: post_commit_export
sync_policy: explicit_export
allowed_same_window_edges: []
required_barriers: [window_commit, export]
event_families_emitted: [observation_diagnostics_and_export]
diagnostic_trace_obligations:
  - observation_packet_version
  - committed_snapshot_version
  - source_shard_versions
facade_visibility: maintained_facade_export
compatibility_adapter_allowed: false
```

## 10. Dispatch Plan

1. `WP2.5-F1/F2` MUST land first because manifest vocabulary constrains event
   producers, diagnostics, state/barrier references, and replay inputs.
2. `WP2.5-A1` MAY run in parallel once the field names and priority-band names
   are stable.
3. `WP2.5-A2/A3` MUST coordinate with the state/barrier cluster before closing
   same-window visibility or diagnostics wording.
4. Cluster integration MUST keep this English file and the Chinese companion
   section-aligned.
5. Cluster integration SHOULD run:

```bash
git diff --check -- docs/task/simulation_architecture/wp25_manifest_event_cluster_20260519.md docs/task/simulation_architecture/wp25_manifest_event_cluster_20260519.zh.md
```

## 11. Acceptance Criteria

1. Every `StageNodeManifest` field from the WP2.5 freeze has a
   required/conditional/optional classification.
2. Enum tables exist for `read_snapshot_policy`, `write_commit_policy`,
   `facade_visibility`, compatibility labels, and producer categories.
3. Event ordering remains `(timestamp, priority, event_id)`.
4. The deterministic `event_id` formula remains
   `stable_hash(run_seed, world_id, producing_node_id, event_family, local_sequence)`.
5. The producer allowlist matrix covers every priority band from `000` through
   `900`.
6. Diagnostics minimums are explicit and compatibility-only producers cannot
   define maintained scheduler truth.
7. Runtime implementation, generated registries, and edits outside the two
   owned task sheets remain out of scope.
8. English and Chinese documents stay section-aligned.

## 12. Non-Goals

- No runtime scheduler implementation.
- No WP3 or WP4 reopening.
- No backend parity or replay harness implementation.
- No machine-readable registry generation.
- No new public facade API.
- No edits to files outside these two task-sheet documents.

## 13. Open Questions

1. Should `stable_hash` name a concrete algorithm during WP2.5, or should that
   choice remain deferred to implementation while the input tuple stays frozen?
2. Should later schema work split `maintained_facade_surface` and
   `maintained_facade_export` into separate producer registries, or keep them
   as one facade-governance family?

Closed from the draft:

- `allowed_producers` is not a first-class manifest field in WP2.5; the
  normative source is the producer matrix in section 7.
- Diagnostics have one common minimum; family-specific fields may only add to
  it.
- Diagnostics-only and compatibility-only adapters MUST NOT write maintained
  event queues.
