# WP19-D Resident-State Sync And Shard Contract

Status: `2026-05-21` preflight-only / pass.

Language:

- English canonical: `wp19_resident_state_sync_shard_contract_cluster_20260521.md`
- Chinese companion:
  [wp19_resident_state_sync_shard_contract_cluster_20260521.zh.md](wp19_resident_state_sync_shard_contract_cluster_20260521.zh.md)

Inputs:

- [WP19 main plan](cuda_resident_state_alignment_wp19_20260521.md)
- [WP19-B device-resident output contract](wp19_device_resident_output_contract_cluster_20260521.md)
- [WP19-C GPU helper diagnostics boundary](wp19_gpu_helper_diagnostics_boundary_cluster_20260521.md)
- [WP6 resident-state boundary rules](../wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.md)
- [Simulation system architecture design](../../../plan/architecture/simulation_system_architecture_design.md)
- [WP2.5 scheduler semantics](../wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.md)
- `src/core/engine/world_batch_runtime.h`
- `src/core/engine/world_batch_runtime.cpp`
- `src/runtime/facade/runtime_facade.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/contracts/backend_profile_contracts.h`

## Purpose

Map resident-state ownership and sync vocabulary onto current runtime evidence
so future device-resident paths have a contract before they can own maintained
state.

The preflight conclusion is intentionally conservative:

1. current maintained truth is still host-owned;
2. current resident-state profile remains a blocked candidate, not a live
   maintained surface;
3. current host-visible export barriers are `export` packet barriers and
   host-returned batch results, not backend-owned resident commits.

## Scope

In scope:

- state-shard vocabulary for physics, tasking, track, damage, observation
  export, episode/runtime metadata, helper diagnostics, and adjacent runtime
  setup/control seams when present;
- sync cadence, trigger, barrier, stale-read, conflict, quarantine, and
  reconstruction/export rules;
- architecture tests or preflight notes that prevent unsynced backend-local
  state from becoming maintained truth.

Out of scope:

- CUDA helper implementation;
- device output DTO field ownership, owned by WP19-B;
- capability support promotion.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `D1` | Shard vocabulary | Candidate state shards are named and linked to existing runtime/facade evidence where possible. |
| `D2` | Sync barrier contract | Host-visible sync/export barriers and stale-read behavior are explicit. |
| `D3` | Ownership labels | Host-owned, backend-owned, partial-sync, observation-only, and export-only labels are mapped to WP19 surfaces. |
| `D4` | Guard coverage | Tests or a concrete test plan prevent unsynced backend-local state from affecting committed host truth. |

## Runtime Evidence Baseline

| Evidence source | Current fact | WP19-D implication |
|-----------------|--------------|--------------------|
| `backend_profile_contracts.h` resident-state registry seed | `resident_state.unmaintained_candidate` is `profile_class: resident_state`, `sync_policy: undeclared_blocked`, `maintained_status: unmaintained_candidate`, `resident_state_supported: false`, and `diagnostics_allowed: true`. | There is no maintained backend-owned or partial-sync resident shard today. Unsynced backend-local state remains candidate-only. |
| `RuntimeFacade::capabilities()` | `supports_resident_state` is hard-coded `false` while the facade still exports candidate id, parity-budget ref, and rejection reason. | Resident-state is explicitly fail-closed at the public capability surface. |
| `WorldBatchRuntime` batch mutators and readers | Setup, tasking, mission-command, leader-intent, pilot-report, observation, and execution-episode controller mirrors are host-visible batch calls. | Current maintained truth is exposed through host-owned runtime/facade surfaces, not through device-owned resident commits. |
| `ObservationBatchPacket` and `EngagementEventPacket` | Host-visible export packets carry `snapshot_version`, `barrier_id`, `source_time_s`, and provenance labels. `EngagementEventPacket` additionally carries `barrier_sequence`, `barrier_detail`, maintained packet provenance, and diagnostics-only diagnostics provenance. | Current maintained export barrier is the host-visible facade export packet envelope, not a backend-owned resident barrier. |
| `ExecutionBatchStepResult` | Rewards, termination, status vectors, reward reports, step infos, controller-state-change flags, and nested `observation_packet` are returned as host-side step products. | Episode/runtime metadata is currently a host-owned derived product and cannot be silently delegated to unsynced backend-local state. |
| `WorldBatchRuntime::get_*_candidate_ids_batch(..., use_gpu)` | GPU helper paths return candidate ids for sensor/visual/comm broadphase queries, but they do not project capability support or maintained truth. | Current helper/GPU state is export-only or diagnostics-only evidence. |
| `RuntimeFacade.runtime()` plus architecture guards | The raw runtime escape hatch is documented as compatibility/diagnostics-only, and architecture tests already block facade coupling to GPU helper implementations or probe-based capability projection. | WP19-D can extend the same fail-closed boundary to resident-state sync semantics without widening public truth paths. |

## Candidate Shard Inventory

The table below maps candidate resident-state shards onto current runtime
evidence. "Current label" means the label that best matches today's maintained
implementation, not a promotion recommendation.

| Candidate shard | Current evidence / surface | Current label | Current cadence / trigger / barrier | Current stale-read / conflict rule |
|-----------------|----------------------------|---------------|-------------------------------------|------------------------------------|
| `setup/static world config` | `BatchWorldSetupRequest`, `BatchWorldSetupResult`, `reset_batch`, `apply_world_setup_batch`, terrain/wind/zone/spawn setup in `WorldBatchRuntime`. | `host-owned` | Triggered only by setup/reset calls. Semantically aligns to WP25 `setup/reset` and `input_injection`; no backend-owned resident barrier is exposed. | Setup state is authoritative only after host setup/reset completes. A future backend cache may mirror it, but cannot become maintained truth without declared reconstruction/export rules. |
| `tasking/command/control intent` | `set_pilot_actions_batch`, `set_mission_commands_batch`, `set_task_orders_batch`, `set_leader_intents_batch`, `set_pilot_reports_batch`; corresponding getters on `WorldBatchRuntime` and `RuntimeFacade`. | `host-owned` | Triggered by explicit batch setters before `step_batch()` or `run_wp10_window()`. Semantically visible at WP25 `input_injection`; no same-window backend publish surface exists. | Host batch mutators remain the only authoritative writers. Backend-local copies are stale or candidate mirrors unless a later profile declares per-field ownership and commit barriers. |
| `physics/world truth` | `SimulationKernel::step()` invoked through `step_batch()` / `step_worlds()`, plus indirect host exports through observations and counterfactual snapshots. | `host-owned` today; `backend-owned` unavailable | Triggered by runtime step completion. The only maintained read points are post-step host reads and later export packets. | Parallel worker completion order is not scheduler truth. A future resident physics shard must publish committed host-visible reconstruction at declared barriers before it can influence maintained state. |
| `track/sensed observation state` | `get_agent_observations_batch`, `ObservationBatchPacket.agent_observations`, `EngagementEventPacket.track_packets` derived from observation contacts. | `observation-only` payload inside a `host-owned` export envelope | Triggered by explicit facade export or nested export inside execution-step results. Public barrier is `export`. | Track/observation payloads may inform maintained consumers only through exported packets with snapshot/provenance. They must not mutate committed world/tasking/damage state directly. |
| `engagement lifecycle` | `LaunchRequest`, `LaunchEvent`, `MunitionLifecyclePacket`, and recent engagement events exported through `EngagementEventPacket`. | `host-owned` export | Triggered by explicit engagement export after recent events have been collected. Public barrier is `export`, with `barrier_sequence` and `barrier_detail` on the packet envelope. | Recent-event buffers may be exported or compared, but unsynced backend-local event order cannot define scheduler truth. |
| `damage/effects` | `EffectsEvent`, `DamageReport`, recent engagement-event export, diagnostics ancestry linking traces to effects/damage ids. | `host-owned` export with `export-only` diagnostics sidecars | Triggered by explicit engagement export after host-visible recent events are available. Public barrier is `export`. | Damage reports are maintained only as exported host-visible products. Backend-only effects accumulators must quarantine to diagnostics until reconstruction and parity rules exist. |
| `observation export envelope` | `ObservationBatchPacket.snapshot_version`, `barrier_id`, `source_time_s`, `provenance`; `EngagementEventPacket.snapshot_version`, `barrier_id`, `barrier_sequence`, `barrier_detail`, `packet_provenance`, `diagnostics_provenance`. | `host-owned` envelope carrying `observation-only` or `export-only` payloads | Triggered by facade export calls. Public barrier is explicitly serialized as `export`. | Any future backend-owned or partial-sync shard must reconstruct into this envelope or an additive WP19-B DTO seam before frontends may treat it as maintained. |
| `episode/runtime metadata` | `ExecutionEpisodeState`, rewards, `terminated`, `truncated`, status vectors, termination specs, reward reports, step infos, controller-state-change flags, and nested `ObservationBatchPacket` in `ExecutionBatchStepResult`. | `host-owned` | Triggered by `export_execution_episode_states()` or `step_execution_batch()`. The nested observation packet uses `export`; the rest is a host-returned step bundle with no resident barrier id yet. | Controller mirrors are valid only when primed and world/entity matched. Backend-local controller copies or reward caches cannot become maintained truth without explicit ownership, barrier, and replay rules. |
| `helper diagnostics / candidate broadphase exports` | `get_sensor_candidate_ids_batch`, `get_visual_candidate_ids_batch`, `get_comm_candidate_ids_batch`, GPU helper/probe outputs, diagnostics traces. | `export-only` | Triggered by explicit helper/query/export calls. No maintained resident barrier exists. | These outputs may be stale, approximate, or backend-local. They must not drive committed state, fallback, or capability projection. |
| `backend operational resident shards` | Only the blocked registry placeholder `resident_state.unmaintained_candidate`; no current facade DTO or host-visible resident commit packet. | `backend-owned` or `partial-sync` future candidate only | Trigger/barrier/cadence are currently undeclared and therefore blocked. | Promotion is forbidden until per-shard ownership, cadence, trigger, barrier, reconstruction, parity budget, and validation evidence are declared and accepted. |

## Sync Cadence, Trigger, And Barrier Rules

WP19-D reuses the WP25 barrier vocabulary, but the current runtime only exposes
part of it as public data.

| Semantic barrier | Current runtime evidence | WP19-D rule |
|------------------|--------------------------|-------------|
| `input_injection` | Represented semantically by host batch setters and setup calls before stepping. | Future resident-state profiles may reuse this barrier, but today it is still host-owned and not materialized as a resident packet barrier id. |
| `stage_publish` | No maintained public resident-state surface exposes same-window backend publishes. | Same-window backend visibility is not a maintained claim today. Any future use must be explicitly declared per shard and kept out of accidental facade truth. |
| `window_commit` | Represented semantically by completed runtime steps and controller step results, but not yet serialized as a packet barrier id for all result bundles. | Future resident-state or partial-sync profiles must name which shards commit here and how snapshot identity is reconstructed. |
| `export` | Explicitly surfaced on `ObservationBatchPacket` and `EngagementEventPacket`. | This is the only current public host-visible sync barrier for maintained observation/engagement exports. |
| `counterfactual_selected_slice` | Explicitly surfaced on `RuntimeCounterfactualSnapshot` / `RuntimeWorldlineComparison`. | This is a bounded comparison/export barrier, not a resident-state ownership barrier. |

Default cadence and trigger rules:

1. setup and static-world shards sync only on setup/reset paths;
2. tasking/control shards sync only on explicit host batch mutation followed by
   a runtime window;
3. physics, engagement, and damage shards become host-visible only after a
   completed step and later export or result reconstruction;
4. observation and track shards become maintained consumer inputs only at the
   explicit `export` barrier;
5. helper diagnostics sync only when explicitly exported or queried and remain
   non-authoritative.

## Ownership Label Mapping To WP19 Surfaces

| Ownership label | Current eligible WP19 surface | Current status |
|-----------------|-------------------------------|----------------|
| `host-owned` | `BatchWorldSetupRequest/Result`, batch mutators, host-returned execution-step bundles, `ObservationBatchPacket`, `EngagementEventPacket`, execution-episode controller mirrors. | This is the only maintained state path today. |
| `backend-owned` | No current maintained public surface. Only the blocked registry placeholder and future additive DTO/export seams are candidates. | Not available; remains blocked by `resident_state.unmaintained_candidate`. |
| `partial-sync` | No current maintained public surface. A future profile could synchronize selected backend shards into host-visible packets or DTOs. | Not available; any introduction must declare per-shard ownership, cadence, trigger, barrier, stale-state policy, and mismatch policy. |
| `observation-only` | `ObservationBatchPacket.agent_observations`, `EngagementEventPacket.track_packets`, and any later device observation view that stays within declared observation envelopes. | Available only as exported observation payload, not as state ownership. |
| `export-only` | Diagnostics traces, helper candidate-id queries, helper/probe outputs, mismatch evidence, shadow-style reports. | Available today, but must not affect committed truth or support flags. |

## Stale-Read, Conflict, Quarantine, And Reconstruction Rules

1. Any backend-local or helper-local value that lacks a declared host-visible
   reconstruction/export barrier is stale by definition for maintained use.
2. `RuntimeFacade.runtime()` and direct `WorldBatchRuntime` escape hatches remain
   compatibility/diagnostics-only; they are not a resident-state commit path.
3. A shard may have only one authoritative owner per maintained profile. Mixed
   host/backend authority on the same committed field is forbidden unless a
   future profile declares a precise partial-sync split and conflict rule.
4. Parallel worker completion order and any future GPU queue completion order
   are not scheduler truth. Accepted order remains the WP25 barrier/order model
   plus exported snapshot identity.
5. Unsynced backend-local state must quarantine to `diagnostics-only`,
   `observation-only`, or `export-only` surfaces. It must not update committed
   host state, alter fallback control flow, or satisfy parity by itself.
6. Reconstruction from backend-owned or partial-sync shards must terminate in a
   host-visible packet or DTO that carries snapshot identity, barrier identity,
   source time, provenance, and mismatch handling.
7. Observation-only shards may export payloads, but they must not mutate
   committed world truth, scheduler order, tasking state, or damage state.
8. Episode/runtime metadata remains host-owned until a future resident-state
   profile declares how controller state, reward state, and termination state
   are synchronized, versioned, and replay-validated.

## Guard Coverage

Current guard stance:

- existing `tests/architecture/runtime_facade` coverage already
  blocks facade coupling to GPU helper implementations and probe-driven
  capability promotion;
- WP19-D should keep resident-state sync preflight in the same fail-closed lane:
  blocked resident-state candidate, `supports_resident_state == false`, and
  host-visible export barriers staying explicit.

Safe architecture guard addition for this stream:

- assert the resident-state registry entry remains
  `undeclared_blocked` + `unmaintained_candidate` + `resident_state_supported:
  false`;
- assert the public facade capability surface remains fail-closed and the
  observation/engagement export packet envelopes continue to use explicit
  host-visible `export` barriers with maintained/diagnostics provenance labels.

## Residuals For Future Maintained Resident-State Promotion

This stream does not justify capability promotion. The main residuals are:

1. no public per-shard resident `SnapshotVersion.shard_versions` contract exists
   yet on facade DTOs;
2. `input_injection` and `window_commit` are still semantic barriers for most
   runtime products, not fully serialized host-visible packet metadata;
3. no maintained DTO currently carries backend-owned or partial-sync
   reconstruction results;
4. conflict resolution, mismatch quarantine, and stale-state policy are not yet
   machine-readable per shard in the backend profile contract;
5. no replay/validation evidence proves that a backend-owned resident shard can
   reconstruct host-visible truth without violating WP6/WP25 rules;
6. helper/GPU exports remain useful evidence, but cannot be promoted beyond
   `observation-only` or `export-only` semantics from this preflight alone.

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/architecture/runtime_facade
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP19 --summary
```

## Handoff

Return:

- sync/shard inventory and ownership-label mapping;
- any added architecture guard coverage;
- blockers or residuals for WP19-B / WP19-E;
- explicit note that WP19-D currently closes as `preflight-only`, not as a
  maintained resident-state promotion.

## Closure Outcome

WP19-D is accepted for WP19 as a preflight-only sync/shard contract. Current
maintained truth remains host-owned, resident-state remains a blocked
candidate, and future promotion still requires per-shard ownership, cadence,
barrier, reconstruction, parity-budget, conflict, quarantine, and replay
evidence.
