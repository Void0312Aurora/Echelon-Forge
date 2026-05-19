# WP2.5-D + WP2.5-E Normative Dispatch Sheet: Clock-Domain Merge and Deterministic Replay

Status: `2026-05-19` normative dispatch sheet.

Language:

- English canonical: `wp25_clock_replay_cluster_20260519.md`
- Chinese companion: [wp25_clock_replay_cluster_20260519.zh.md](wp25_clock_replay_cluster_20260519.zh.md)

Inputs:

- [WP2.5 scheduler semantics freeze](scheduler_semantics_wp25_20260519.md)
- [WP2.5-F + WP2.5-A manifest/event cluster](wp25_manifest_event_cluster_20260519.md)
- [WP2.5-B + WP2.5-C state/barrier cluster](wp25_state_barrier_cluster_20260519.md)
- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [architecture plan review](../review/architecture_plan_review_20260519.md)

Normative language:

- `MUST` marks required WP2.5 behavior for maintained documentation and later implementation.
- `MUST NOT` marks behavior that cannot define maintained scheduler or replay truth.
- `SHOULD` marks the default rule; deviations need an explicit follow-up task or review note.
- `MAY` marks an allowed compatibility or diagnostics path.

## 1. Purpose

This sheet turns `WP2.5-D Clock-Domain Merge` and
`WP2.5-E Deterministic Replay Contract` into a normative dispatch package. It is
for subagents that later implement scheduler, facade, backend, diagnostics, or
replay work without inventing additional clock or replay semantics.

The dispatch goal is:

- `WP2.5-D` freezes how clock domains merge into deterministic scheduling windows.
- `WP2.5-E` freezes the replay input envelope, forbidden nondeterminism,
  parity-budget declaration, and diagnostics obligations.

This sheet is documentation/specification work. It MUST NOT implement a runtime
scheduler or replay harness.

## 2. Normative Scope and Non-Goals

In scope:

- nested triggering as the default outer-window rule;
- merge-policy matrix for `nested_slot`, `hold_last`, `interpolate`,
  `enqueue_event`, `defer_to_next_window`, and `reject_on_ambiguous_order`;
- independent clock-domain handling as maintained, rejected, or
  diagnostics-only fallback;
- replay input envelope using stable `StageNodeManifest`, event, shard,
  `SnapshotVersion`, and barrier vocabulary;
- forbidden nondeterminism table;
- parity-budget template for accelerated or approximate backends;
- diagnostics obligations tying requests, events, `SnapshotVersion`, barriers,
  reports, and exports.

Out of scope:

- runtime scheduler implementation;
- replay harness implementation;
- backend parity implementation;
- machine-readable registry generation;
- new merge-policy values;
- new public facade APIs;
- reopening WP3 or changing WP4 scope.

## 3. Dispatch Slices

| Slice | Focus | Required output | Dependencies | Reasoning budget |
|-------|-------|-----------------|--------------|------------------|
| `D1` | Merge-policy matrix. | Normative table for all six frozen merge-policy values. | Manifest/event cluster and state/barrier cluster. | High |
| `D2` | Independent clock-domain handling. | Maintained/rejected/diagnostics-only rules plus required metadata. | `D1`, backend profile vocabulary from the architecture baseline. | High |
| `E1` | Replay input envelope. | Ordered table of replay inputs and required provenance. | `D1/D2`, manifest/event cluster, state/barrier cluster. | High |
| `E2` | Forbidden nondeterminism and parity. | Nondeterminism table plus parity-budget template. | `E1` and frozen backend-reference rule. | High |
| `E3` | Diagnostics obligations and acceptance. | Trace obligations, acceptance gates, and open-question cleanup. | `D1-D2`, `E1-E2`. | Medium-high |

Parallelism rules:

1. `D1` MUST land before `D2` because independent-domain handling references
   merge-policy values.
2. `E1` MAY be outlined while `D2` is in review, but MUST NOT finalize
   normative wording until `D2` is stable.
3. `E2` and `E3` MAY run in parallel after `E1` is stable if one owner keeps
   final English/Chinese section alignment.
4. Workers MUST NOT split the same normative table across multiple concurrent
   authors.

## 4. Clock-Domain Baseline

The default maintained scheduling rule is:

```text
one outer scheduling window owns deterministic order;
lower-rate domains run as declared nested triggers inside that window.
```

Required baseline rules:

1. A maintained stage node MUST declare `clock_domain`, `latency_policy`,
   `sync_policy`, `required_barriers`, and emitted event families in its
   `StageNodeManifest`.
2. Lower-rate domains SHOULD be represented as nested triggers whenever their
   cadence can be expressed as deterministic slots inside the outer window.
3. A domain that cannot prove deterministic ordering MUST use
   `reject_on_ambiguous_order` or a diagnostics-only fallback.
4. Independent backend or resident-state clocks are not maintained replay
   sources until they declare sync barriers, event export order, parity budget,
   and diagnostics metadata.

## 5. Merge-Policy Matrix

No merge-policy values beyond the six frozen values are introduced by WP2.5.

| Merge policy | Maintained use | Required inputs | Visibility/barrier rule | Replay rule | Rejection or diagnostics rule |
|--------------|----------------|-----------------|-------------------------|-------------|-------------------------------|
| `nested_slot` | Producer runs in a deterministic slot inside the outer scheduling window. | `clock_domain`, slot number or cadence rule, `node_id`, `world_id`, source `SnapshotVersion`, and required barriers. | Output is visible according to `stage_publish`, `window_commit`, or `export` declared by the producer manifest. | Replay reruns the producer at the same slot and orders events by `(timestamp, priority, event_id)`. | Missing or duplicate slot declarations are replay errors unless the node is diagnostics-only. |
| `hold_last` | A lower-rate producer output is reused until `valid_until` or equivalent validity expiry. | Producer output id, `effective_time`, `valid_until`, source snapshot, held value version, and consumer domain. | Consumers may read the held output only after the declared injection or commit barrier and before expiry. | Replay must record the first-producing event/request and every consumer window that depends on the held value. | If no valid held output exists, the consumer must reject, defer, or use a declared diagnostics-only fallback. |
| `interpolate` | A consumer derives an intermediate value from two versioned producer outputs. | Previous and next producer output ids, source times, source shard versions, interpolation rule id, and consumer node id. | Interpolated values are derived consumer views; they do not commit producer shard versions. | Replay must reconstruct the same interpolation from the same two versioned outputs and rule id. | Interpolation is not maintained if either endpoint is missing, unversioned, diagnostics-only, or unordered. |
| `enqueue_event` | Producer output becomes a timestamped event for the current or a later window. | Event family, timestamp, deterministic `event_id`, source request/event id, source snapshot, and target barrier. | Event is consumed when its timestamp enters a maintained window and is ordered by `(timestamp, priority, event_id)`. | Replay consumes the sorted event stream; insertion order is never a tie-breaker. | Events without deterministic id or timestamp are rejected from maintained truth and may only be diagnostics-only. |
| `defer_to_next_window` | Producer output is accepted but not visible until the next scheduling window. | Source request id, `effective_time`, prior snapshot, target window id or timestamp, and deferred reason. | Output is invisible to current-window maintained logic and becomes eligible after the next `input_injection` or declared barrier. | Replay must preserve the deferral decision and target window. | Hidden current-window visibility is prohibited; ambiguous deferral becomes reject or diagnostics-only. |
| `reject_on_ambiguous_order` | Scheduler or adapter rejects an input when deterministic order cannot be proven. | Source id, attempted merge policy, ambiguity reason, input snapshot, and rejection barrier. | No maintained state shard or event queue mutation occurs. Diagnostics may export the rejection. | Replay must reproduce the same rejection from the same metadata. | This is the only maintained outcome when order ambiguity would otherwise affect scheduler truth. |

## 6. Independent Clock-Domain Handling

Independent clock domains include external backends, device-resident state,
resident physics substeps, asynchronous sensors, service callbacks, or any
producer whose ordering is not naturally a nested slot in the outer scheduling
window.

| Handling status | Normative rule | Required metadata | Allowed output | Acceptance gate |
|-----------------|----------------|-------------------|----------------|-----------------|
| Maintained | MAY be maintained only when deterministic merge order is declared and replayable. | `clock_domain_id`, owner node/backend, deterministic backend profile, sync barriers, event export order, merge policy, source time, source `SnapshotVersion` or shard versions, `effective_time`, `valid_until` when applicable, parity-budget reference, diagnostics obligations. | Maintained events, committed shard updates, or facade exports according to manifest and barrier rules. | A later replay can reconstruct the same request/event/report/export order without wall-clock or thread completion order. |
| Rejected | MUST be rejected when deterministic order, required metadata, valid source snapshot, or allowed merge policy is missing. | Source id, attempted domain id, ambiguity or missing-metadata reason, input snapshot if available, rejection barrier. | Rejection diagnostics only; no maintained event or shard mutation. | The rejection itself is replayable and does not alter maintained scheduler truth. |
| Diagnostics-only fallback | MAY export inspection data when the source is useful but not maintained. | Compatibility or diagnostics label, source id, best-effort timestamp, source snapshot if available, reason not maintained, export barrier. | Diagnostics/export channels only. | Output MUST NOT define scheduler truth, policy/training truth, replay parity truth, or event-queue truth. |

Additional independent-domain rules:

1. Independent domains MUST NOT use backend thread completion order as event
   order.
2. Independent domains MUST NOT use wall-clock arrival time as a maintained
   tie-breaker.
3. Missed slots are replay errors unless the manifest or backend profile
   explicitly declares skippable semantics and diagnostics records each skip.
4. Backend profiles MUST declare whether they are CPU exact, accelerated exact,
   approximate, or diagnostics-only before replay treats them as maintained
   sources.
5. Diagnostics for independent domains SHOULD record both the pre-merge source
   snapshot and the post-merge committed or exported snapshot when a maintained
   output is produced.

## 7. Replay Input Envelope

A maintained replay MUST be reconstructable from the ordered input envelope
below. The table uses the stable vocabulary from the manifest/event and
state/barrier dispatch sheets.

| Input block | Required contents | Source vocabulary | Replay use | Diagnostics link |
|-------------|-------------------|-------------------|------------|------------------|
| Static content and scenario setup | Content ids, scenario setup packets, world setup refs, setup/reset commit ids. | `setup` shard, `P0/P1`, `SnapshotVersion`, setup/reset events. | Recreates initial authoritative state. | Setup manifest id, content id set, setup barrier id. |
| Run identity | Run seed, world ids, deterministic backend profile ids, replay format/version id. | `world_id`, backend profile, `StageNodeManifest` registry. | Defines deterministic identity and backend assumptions. | Run trace id and profile hash or stable id. |
| Stage-node registry | `StageNodeManifest` entries with `node_id`, stages, packets, shards, clock domain, barriers, event families, diagnostics obligations, and facade visibility. | Manifest/event cluster fields and enum vocabulary. | Defines legal producers, consumers, barriers, and event families. | Manifest registry id or version. |
| External and facade requests | `source_id`, request id, input packet type, `input_snapshot_version`, `effective_time`, `valid_until`, `merge_policy`, authority/validity metadata. | Priority `100` injection events, facade/external producer categories. | Replays accepted, deferred, rejected, and diagnostics-only injections. | Request trace id, injection barrier, accepted/rejected reason. |
| Clock-domain merge records | Domain id, merge policy, slot or source times, held/interpolated endpoints, target window, rejection or diagnostics reason. | Section 5 merge-policy matrix and Section 6 independent-domain metadata. | Reconstructs cross-domain visibility and ordering decisions. | Merge trace id, source and resulting snapshots. |
| Event stream | Events sorted by `(timestamp, priority, event_id)` with event family, producer id, local sequence, source request/event id, and visibility barrier. | Manifest/event priority table and deterministic id rule. | Replays event consumption order. | Event trace id and ancestry links. |
| Snapshot sequence | Committed `SnapshotVersion` entries with global version, shard versions, source time, barrier id, barrier sequence, and barrier detail. | State/barrier cluster `SnapshotVersion` contract. | Reconstructs committed state visibility. | Snapshot trace id and source shard versions. |
| Reports and facade exports | Report ids, observation/export packet ids, source `SnapshotVersion`, facade visibility label, diagnostics-only flags. | `P10`, `observation` shard, `export` barrier, facade visibility enum. | Replays maintained export surfaces and excludes diagnostics-only truth. | Export trace id, report ancestry, observation packet version. |
| Diagnostics trace | Request, event, report, snapshot, barrier, merge, rejection, and export links. | `diagnostic_trace_obligations` from manifests and this sheet. | Audits replay reconstruction and parity comparison. | Trace graph root and per-edge ids. |

## 8. Forbidden Nondeterminism

Maintained scheduler or replay truth MUST NOT depend on the following sources.

| Forbidden source | Why it is forbidden | Required replacement | Diagnostics handling |
|------------------|--------------------|----------------------|----------------------|
| Nondeterministic container iteration order | It changes event or producer order across runs, compilers, or processes. | Deterministic node order plus `(timestamp, priority, event_id)`. | Record ambiguity and reject or label diagnostics-only. |
| Wall-clock timing as a tie-breaker | It is not simulated time and cannot be replayed reliably. | Simulated `timestamp`, `effective_time`, `valid_until`, and deterministic event id. | Wall-clock may appear only as non-semantic diagnostic metadata. |
| Raw pointer addresses | Allocation layout changes across runs. | Stable ids such as `world_id`, `node_id`, request id, entity semantic id, or event id. | Pointer-like values must not appear in maintained event ids. |
| Entity allocation accidents | Allocation order may change when parallelism or backend layout changes. | Stable entity refs or setup-assigned ids recorded in `SnapshotVersion` ancestry. | Allocation-only ids are diagnostics-only until wrapped. |
| Hidden Python helper call order | Frontend call ordering is not scheduler truth unless expressed as facade metadata. | Facade/external requests with `source_id`, `input_snapshot_version`, `effective_time`, `valid_until`, and `merge_policy`. | Unwrapped helper order is compatibility diagnostics only. |
| Backend thread completion order | Thread scheduling is host/runtime dependent. | Backend profile with deterministic sync barriers and event export order. | Without a profile, backend output is rejected or diagnostics-only. |
| Floating approximate backend drift without budget | Approximate results may differ while appearing valid. | Declared parity budget and comparison domain before maintained replay use. | Outside-budget output fails parity or remains diagnostics-only. |

## 9. Parity-Budget Template

Accelerated or approximate backends MUST declare a parity budget before they are
treated as maintained replay sources.

```yaml
parity_budget:
  budget_id: backend_profile.cpu_exact.reference
  backend_profile_id: cpu_exact.reference
  status: maintained_reference
  applies_to_clock_domains: [physics.fixed_tick, sensor.scan_slot]
  comparison_reference: cpu_exact
  deterministic_ordering:
    sync_barriers: [input_injection, window_commit, export]
    event_export_order: [timestamp, priority, event_id]
    merge_policies_allowed: [nested_slot, enqueue_event, defer_to_next_window]
  numeric_tolerance:
    position_abs: 0.0
    velocity_abs: 0.0
    time_abs: 0.0
  event_tolerance:
    event_family_set: exact
    event_order: exact
    rejected_inputs: exact
  snapshot_tolerance:
    shard_versions: exact
    committed_barriers: exact
  diagnostics_required:
    - backend_profile_id
    - source_snapshot_version
    - resulting_snapshot_version
    - parity_budget_id
```

Template rules:

1. CPU exact path is the default reference and SHOULD use exact parity.
2. Accelerated exact paths MUST keep event order and committed shard versions
   exact unless a later backend-specific task records a stricter exception.
3. Approximate paths MUST declare numeric tolerance, event tolerance, snapshot
   tolerance, and affected clock domains.
4. A backend with no parity budget MUST remain diagnostics-only for replay
   truth, even if it can export useful inspection data.

## 10. Diagnostics Obligations

Diagnostics MUST connect the full scheduler/replay chain:

```text
request -> input_injection -> merge decision -> event/report
  -> window_commit SnapshotVersion -> export -> replay/parity check
```

Minimum trace fields:

- `world_id`;
- scheduling window id or simulated time window;
- producer `node_id` or external `source_id`;
- request id and input packet type when present;
- `input_snapshot_version` or exact source shard versions;
- merge policy and clock-domain id;
- barrier id and optional barrier detail;
- event id, event family, timestamp, priority, and local sequence when an event is produced;
- report id or packet id when a report/export is produced;
- resulting `SnapshotVersion` for committed or exported outputs;
- facade visibility, compatibility label, or diagnostics-only label;
- rejection reason, deferral target, hold expiry, or interpolation endpoints when applicable;
- parity-budget id for any accelerated or approximate maintained source.

Obligation table:

| Chain link | Required diagnostics | Must not omit |
|------------|----------------------|---------------|
| Request/injection | `source_id`, request id, `input_snapshot_version`, `effective_time`, `valid_until`, `merge_policy`, injection barrier. | Source metadata needed to replay accepted, rejected, or deferred input. |
| Merge decision | Clock-domain id, merge policy, source times, source snapshots, target window or barrier, ambiguity/rejection reason if any. | The reason an output became visible, deferred, rejected, or diagnostics-only. |
| Event/report | Deterministic event id or report id, producer id, priority band, source request/event links. | `(timestamp, priority, event_id)` ordering fields. |
| Snapshot/commit | Prior source shard versions, resulting `SnapshotVersion`, barrier id, barrier sequence. | The committed state ancestry consumed by later stages or exports. |
| Export | Export packet id, source `SnapshotVersion`, facade visibility label, diagnostics-only flag if applicable. | Whether the export is maintained truth or diagnostics-only. |
| Replay/parity | Replay input block ids, backend profile id, parity-budget id, comparison outcome. | Backend and budget metadata used to evaluate parity. |

## 11. Acceptance Criteria

This cluster is accepted when:

1. the default nested-triggering rule is explicit;
2. every frozen merge-policy value has a normative row and no new value is added;
3. independent clock domains have maintained, rejected, and diagnostics-only
   handling rules;
4. required metadata for independent domains is explicit;
5. replay input envelope covers setup, run identity, manifests, requests,
   merge records, events, snapshots, reports/exports, and diagnostics;
6. forbidden nondeterminism is tabulated with deterministic replacements;
7. parity-budget template distinguishes CPU exact, accelerated exact,
   approximate, and diagnostics-only backend status;
8. diagnostics obligations connect requests, events, `SnapshotVersion`,
   barriers, reports, exports, and parity;
9. runtime scheduler and replay harness implementation remain out of scope;
10. English and Chinese documents stay section-aligned.

## 12. Resolved Decisions and Remaining Questions

Resolved decisions:

1. `interpolate` is maintained only as a derived consumer view in WP2.5; it does
   not commit producer shard versions.
2. `parity_budget` is treated as a backend profile block that may name affected
   clock domains, not as a single scalar.
3. Maintained independent-domain diagnostics SHOULD record both pre-merge
   source snapshots and post-merge committed or exported snapshots when output
   is produced.
4. `reject_on_ambiguous_order` is the only maintained outcome when order
   ambiguity would affect scheduler truth.
5. Missed slots are replay errors unless explicit skippable semantics are
   declared in the manifest or backend profile and each skip is diagnosed.

Remaining questions for later work:

1. Whether future machine-readable registry work should normalize
   `clock_domain_id` and backend profile ids.
2. Whether implementation tests should require full trace graphs for every
   diagnostics-only fallback, or allow compact records when no replay assertion
   consumes the fallback.

## 13. Validation

Cluster integration SHOULD run:

```bash
git diff --check -- docs/task/simulation_architecture/wp25_clock_replay_cluster_20260519.md docs/task/simulation_architecture/wp25_clock_replay_cluster_20260519.zh.md
```
