# WP2.5 Scheduler Semantics Acceptance Review

Status: `2026-05-19` accepted.

Language:

- English canonical: `wp25_scheduler_semantics_acceptance_review_20260519.md`
- Chinese companion: [wp25_scheduler_semantics_acceptance_review_20260519.zh.md](wp25_scheduler_semantics_acceptance_review_20260519.zh.md)

Scope:

- [WP2.5 Scheduler Semantics Freeze](../simulation_architecture/scheduler_semantics_wp25_20260519.md)
- [WP2.5-F + WP2.5-A manifest/event cluster](../simulation_architecture/wp25_manifest_event_cluster_20260519.md)
- [WP2.5-B + WP2.5-C state/barrier cluster](../simulation_architecture/wp25_state_barrier_cluster_20260519.md)
- [WP2.5-D + WP2.5-E clock/replay cluster](../simulation_architecture/wp25_clock_replay_cluster_20260519.md)

## 1. Verdict

WP2.5 is accepted as a documentation/specification freeze.

It successfully closes the architecture review gap that identified
`StateStore`, `EventQueue`, `ClockDomain`, `Barrier`, and
`StageNodeManifest` as concepts that needed executable semantics before WP4
facade hardening and WP5 validation work.

The acceptance is intentionally documentation-only. It does not claim that a
runtime scheduler, replay harness, machine-readable manifest registry, or
backend parity implementation exists.

## 2. Evidence

| Area | Evidence | Result |
|------|----------|--------|
| Stage-node manifest | `WP2.5-F + WP2.5-A` defines required/conditional manifest fields, enum vocabulary, compatibility labels, producer categories, canonical examples, and diagnostics minimums. | Accepted. |
| Event ordering | Event order remains `(timestamp, priority, event_id)` and `event_id = stable_hash(run_seed, world_id, producing_node_id, event_family, local_sequence)`. Producer allowlist covers priority bands `000-900`. | Accepted. |
| State shard versioning | `WP2.5-B + WP2.5-C` defines shard ownership, commit triggers, increment rules, diagnostics obligations, and `SnapshotVersion` naming. | Accepted. |
| Barrier visibility | The same sheet defines before/after visibility for `input_injection`, `stage_publish`, `window_commit`, and `export`, with same-window legality tied to producer publish intent and consumer manifest read sets. | Accepted. |
| Clock-domain merge | `WP2.5-D + WP2.5-E` freezes all six merge policies and independent clock-domain handling as maintained, rejected, or diagnostics-only. No new merge-policy values were introduced. | Accepted. |
| Deterministic replay | Replay input envelope, forbidden nondeterminism, parity-budget template, and diagnostics chain are documented. | Accepted as a future implementation contract. |
| WP3 boundary | All WP2.5 documents keep WP3 accepted and avoid rescoping engagement behavior. | Accepted. |

## 3. Resolved Decisions

1. WP2.5 does not add runtime code.
2. `allowed_producers` is not a first-class manifest field in WP2.5; the
   normative source is the producer allowlist matrix.
3. Diagnostics-only and compatibility-only adapters must not write maintained
   event queues or define scheduler truth.
4. `observation` is a maintained shard for export packet versions, while
   diagnostics-only pre-commit views do not increment it.
5. `barrier_id` is limited to the four frozen barriers; detailed labels belong
   in `barrier_detail`.
6. Same-window legality requires both producer publish intent and consumer
   declared read set.
7. `interpolate` is maintained only as a derived consumer view in WP2.5 and
   does not commit producer shard versions.
8. `parity_budget` is a backend profile block, not a single scalar.
9. If ordering ambiguity affects scheduler truth, `reject_on_ambiguous_order`
   is the only maintained outcome.

## 4. Residual Risks

These are not blockers for WP2.5 acceptance, but they must be handled by later
work:

1. `stable_hash` still needs a concrete algorithm before implementation.
2. A future machine-readable registry may need to normalize `clock_domain_id`,
   backend profile ids, `barrier_detail`, and manifest enum values.
3. WP5 must decide whether every diagnostics-only fallback requires a full
   trace graph, or whether compact records are acceptable when no replay
   assertion consumes the fallback.
4. Implementation tests must decide whether facade exports must always record
   the full shard map or only the replay-sensitive subset.

## 5. Handoff

WP4 may proceed using WP2.5 as its scheduler-semantics input. WP4 should not
invent new scheduler rules inside facade alignment. If facade work needs a
field, producer, barrier, merge policy, or replay rule that is not covered by
WP2.5, it should open a targeted contract amendment rather than hiding the
rule inside runtime or facade code.

WP5 should turn the WP2.5 normative dispatch sheets into architecture tests,
manifest checks, replay-envelope tests, or smoke validation once the
implementation surface exists.

## 6. Acceptance Status

Accepted artifacts:

- [scheduler semantics freeze](../simulation_architecture/scheduler_semantics_wp25_20260519.md)
- [manifest/event normative sheet](../simulation_architecture/wp25_manifest_event_cluster_20260519.md)
- [state/barrier normative sheet](../simulation_architecture/wp25_state_barrier_cluster_20260519.md)
- [clock/replay normative sheet](../simulation_architecture/wp25_clock_replay_cluster_20260519.md)

Validation performed:

```bash
git diff --check -- docs/task/simulation_architecture/scheduler_semantics_wp25_20260519.md docs/task/simulation_architecture/scheduler_semantics_wp25_20260519.zh.md docs/task/simulation_architecture/wp25_manifest_event_cluster_20260519.md docs/task/simulation_architecture/wp25_manifest_event_cluster_20260519.zh.md docs/task/simulation_architecture/wp25_state_barrier_cluster_20260519.md docs/task/simulation_architecture/wp25_state_barrier_cluster_20260519.zh.md docs/task/simulation_architecture/wp25_clock_replay_cluster_20260519.md docs/task/simulation_architecture/wp25_clock_replay_cluster_20260519.zh.md docs/task/simulation_architecture/README.md docs/task/simulation_architecture/README.zh.md
```

No runtime tests were required because WP2.5 is documentation/specification
only.
