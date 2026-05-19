# WP6-B Parity Budget Registry

Status: `2026-05-19` implementation-ready registry for WP6-B parity budget
records.

Language:

- English canonical: `wp6_parity_budget_registry_20260519.md`
- Chinese companion: [wp6_parity_budget_registry_20260519.zh.md](wp6_parity_budget_registry_20260519.zh.md)

Inputs:

- [WP6 backend profile policy](backend_profile_policy_wp6_20260519.md)
- [WP6-A backend profile taxonomy cluster](wp6_backend_profile_taxonomy_cluster_20260519.md)
- [WP6-B parity budget dispatch sheet](wp6_parity_budget_cluster_20260519.md)
- [WP2.5 scheduler semantics freeze](scheduler_semantics_wp25_20260519.md)
- [WP5 validation harness](validation_harness_wp5_20260519.md)

Normative language:

- `MUST` marks required WP6 behavior for maintained documentation and later
  implementation.
- `MUST NOT` marks behavior that cannot define maintained parity truth.
- `SHOULD` marks the default rule; deviations need an explicit follow-up task or
  review note.
- `MAY` marks an allowed compatibility or diagnostics path.

## 1. Purpose

This registry is the implementation-preparation output for `WP6-B Parity Budget
And Comparison Rules`. It turns the dispatch template into named budget records
that later backend profile metadata can reference through `parity_budget_ref`.

The registry is intentionally conservative. `cpu_exact.reference` is the only
maintained exact baseline in this first registry revision. GPU helper,
GPU-exact, resident-state, and shadow-compare entries are placeholders or
diagnostics records until a maintained profile explicitly declares ownership,
sync, parity evidence, and validation gates.

## 2. Registry Field Contract

Every registry entry MUST carry the following fields:

| Field | Requirement |
|-------|-------------|
| `budget_id` | Stable id for the budget record. |
| `budget_version` | Integer revision of the budget record. |
| `backend_profile_id` | Profile id that owns or will own the budget. |
| `profile_class` | One of `reference`, `accelerated_exact`, `resident_state`, `approximate`, or `diagnostics_only`. |
| `comparison_reference` | Semantic anchor used for comparison. |
| `budget_scope` | Clock domains, state shards, output families, and maintained/diagnostics split covered by the budget. |
| `comparison_domains` | Domain-by-domain exactness and tolerance rules. |
| `sync_barriers` | Barriers that anchor replay and comparison. |
| `diagnostics_requirements` | Structured fields required to explain mismatches. |
| `mismatch_policy` | Action when comparison fails or when a placeholder is evaluated. |
| `acceptance_gate` | Review or test gate required before maintained use. |
| `change_reason` | Short reason for this budget revision. |

Registry consumers MUST NOT infer maintained status from the presence of a
record. Maintained status comes from `profile_class`, `acceptance_gate`, and the
profile metadata that references the record.

## 3. Comparison Domain Defaults

These defaults apply to every entry below unless an entry narrows a domain more
strictly:

| Domain | Registry rule |
|--------|---------------|
| `event_order` | Exact-only identity domain. `timestamp`, `priority`, `event_id`, and event-family membership MUST match. No maintained tolerance is allowed. |
| `snapshot_versions` | Exact-only identity domain. Exported snapshot identity, barrier id, barrier sequence, shard-version map, and lineage MUST match. Internal versions must normalize to exported `SnapshotVersion` before comparison. |
| `numeric_state` | Payload comparison domain. Any tolerance MUST name the field family, comparator, and threshold. Unlisted fields default to exact. |
| `observation_export` | Exact envelope domain plus payload inheritance. Schema, field set, visibility label, provenance, and source snapshot reference are exact; payload values inherit `numeric_state`. |
| `diagnostics_trace` | Structured ancestry and mismatch codes are exact. Human-readable diagnostics prose, summary text, and formatting are diagnostics-only and MUST NOT participate in maintained truth. |

## 4. Initial Budget Registry

### 4.1 `cpu_exact.reference`

```yaml
budget_id: parity_budget.cpu_exact.reference.v1
budget_version: 1
backend_profile_id: cpu_exact.reference
profile_class: reference
comparison_reference: self
budget_scope:
  maintained_status: maintained_exact_baseline
  clock_domains: [physics.fixed_tick, sensor.scan_slot]
  state_shards: [scheduler, physics, track, observation, engagement]
  output_families: [observation_packet, committed_snapshot, diagnostics_trace]
  diagnostics_only_surfaces: [human_readable_diagnostics_prose]
comparison_domains:
  event_order:
    mode: exact_identity
    key: [timestamp, priority, event_id]
    event_family_membership: exact
    allowed_drift: none
  snapshot_versions:
    mode: exact_identity
    identity: [world_id, global_version, barrier_id, barrier_sequence, shard_versions, lineage]
    normalization: exported_snapshot_version
    allowed_drift: none
  numeric_state:
    mode: exact
    tolerance_budget: []
    default_for_unlisted_fields: exact
  observation_export:
    envelope:
      mode: exact
      fields: [schema_version, field_set, visibility_label, provenance, source_snapshot_version]
    payload: inherit_numeric_state
  diagnostics_trace:
    structured:
      mode: exact
      fields: [source_request_id, event_id, source_snapshot_version, resulting_snapshot_version, mismatch_code]
    prose: diagnostics_only
sync_barriers: [input_injection, tick_commit, window_commit, export]
diagnostics_requirements:
  - backend_profile_id
  - budget_id
  - budget_version
  - comparison_reference
  - source_snapshot_version
  - resulting_snapshot_version
  - sync_barrier_id
  - mismatch_domain
  - mismatch_code
  - mismatch_summary
mismatch_policy:
  maintained_profile_result: fail
  diagnostics_result: report_only
  quarantine_required: true
acceptance_gate: maintained_cpu_reference_existing_wp6_baseline
change_reason: initial maintained exact reference budget
```

Implementation note: this is the only entry in this registry that may be used
as maintained exact truth without a later promotion review.

### 4.2 `gpu_helpers.diagnostics_only`

```yaml
budget_id: parity_budget.gpu_helpers.diagnostics_only.v1
budget_version: 1
backend_profile_id: gpu_helpers.diagnostics_only
profile_class: diagnostics_only
comparison_reference: cpu_exact.reference
budget_scope:
  maintained_status: diagnostics_only_not_truth
  clock_domains: [declared_by_helper_export]
  state_shards: []
  output_families: [helper_metrics, helper_trace, probe_export]
  diagnostics_only_surfaces: [all_exported_surfaces]
comparison_domains:
  event_order:
    mode: exact_identity_if_replayed_against_reference
    key: [timestamp, priority, event_id]
    event_family_membership: exact
    allowed_drift: none
  snapshot_versions:
    mode: exact_identity_if_snapshot_link_is_reported
    identity: [source_snapshot_version, barrier_id, barrier_sequence]
    normalization: exported_snapshot_version
    allowed_drift: none
  numeric_state:
    mode: diagnostics_only
    tolerance_budget: []
    required_if_promoted: field_family_comparator_threshold
    default_for_unlisted_fields: exact
  observation_export:
    envelope:
      mode: exact_if_present
      fields: [schema_version, field_set, visibility_label, provenance, source_snapshot_version]
    payload: inherit_numeric_state
  diagnostics_trace:
    structured:
      mode: exact_if_present
      fields: [source_request_id, event_id, source_snapshot_version, mismatch_code]
    prose: diagnostics_only
sync_barriers: [export]
diagnostics_requirements:
  - backend_profile_id
  - budget_id
  - budget_version
  - comparison_reference
  - source_snapshot_version
  - export_barrier_id
  - helper_name
  - helper_build_or_feature_flag
  - diagnostics_label
  - mismatch_summary
mismatch_policy:
  maintained_profile_result: not_applicable
  diagnostics_result: report_only
  quarantine_required: false
acceptance_gate: not_eligible_for_maintained_truth_without_reclassification
change_reason: initial diagnostics-only placeholder for GPU helper exports
```

Implementation note: this record may support diagnostics reporting. It MUST NOT
be used to claim exact GPU execution, resident state, or shadow comparison.

### 4.3 `gpu_exact.unmaintained_candidate`

```yaml
budget_id: parity_budget.gpu_exact.unmaintained_candidate.v1
budget_version: 1
backend_profile_id: gpu_exact.unmaintained_candidate
profile_class: accelerated_exact
comparison_reference: cpu_exact.reference
budget_scope:
  maintained_status: unmaintained_candidate
  clock_domains: [physics.fixed_tick, sensor.scan_slot]
  state_shards: [scheduler, physics, track, observation, engagement]
  output_families: [observation_packet, committed_snapshot, diagnostics_trace]
  diagnostics_only_surfaces: [accelerator_kernel_notes, human_readable_diagnostics_prose]
comparison_domains:
  event_order:
    mode: exact_identity_required_for_promotion
    key: [timestamp, priority, event_id]
    event_family_membership: exact
    allowed_drift: none
  snapshot_versions:
    mode: exact_identity_required_for_promotion
    identity: [world_id, global_version, barrier_id, barrier_sequence, shard_versions, lineage]
    normalization: exported_snapshot_version
    allowed_drift: none
  numeric_state:
    mode: exact_required_for_accelerated_exact
    tolerance_budget: []
    default_for_unlisted_fields: exact
  observation_export:
    envelope:
      mode: exact_required_for_promotion
      fields: [schema_version, field_set, visibility_label, provenance, source_snapshot_version]
    payload: inherit_numeric_state
  diagnostics_trace:
    structured:
      mode: exact_required_for_promotion
      fields: [source_request_id, event_id, source_snapshot_version, resulting_snapshot_version, mismatch_code]
    prose: diagnostics_only
sync_barriers: [input_injection, tick_commit, window_commit, export]
diagnostics_requirements:
  - backend_profile_id
  - budget_id
  - budget_version
  - comparison_reference
  - source_snapshot_version
  - resulting_snapshot_version
  - sync_barrier_id
  - accelerator_backend_id
  - accelerator_build_or_feature_flag
  - mismatch_domain
  - mismatch_code
  - mismatch_summary
mismatch_policy:
  maintained_profile_result: not_accepted
  candidate_result: fail_and_remain_unmaintained
  diagnostics_result: report_only
  quarantine_required: true
acceptance_gate: future_wp6_accelerated_exact_promotion_review_with_replay_evidence
change_reason: initial unmaintained candidate budget; no exact GPU acceptance claimed
```

Implementation note: if any numeric tolerance becomes necessary, this candidate
MUST be reclassified away from `accelerated_exact`.

### 4.4 `resident_state.unmaintained_candidate`

```yaml
budget_id: parity_budget.resident_state.unmaintained_candidate.v1
budget_version: 1
backend_profile_id: resident_state.unmaintained_candidate
profile_class: resident_state
comparison_reference: cpu_exact.reference
budget_scope:
  maintained_status: unmaintained_candidate
  clock_domains: [physics.fixed_tick, sensor.scan_slot]
  host_visible_maintained_state: [committed_snapshot, observation_packet, diagnostics_trace_structured]
  backend_resident_operational_state: [backend_local_cache, device_resident_working_set]
  state_shards: [observation, physics_or_track_if_declared_by_future_profile]
  output_families: [observation_packet, committed_snapshot, diagnostics_trace]
  diagnostics_only_surfaces: [unsynced_backend_local_state, human_readable_diagnostics_prose]
comparison_domains:
  event_order:
    mode: exact_identity_required_at_declared_barriers
    key: [timestamp, priority, event_id]
    event_family_membership: exact
    allowed_drift: none
  snapshot_versions:
    mode: exact_identity_required_for_host_visible_exports
    identity: [world_id, global_version, barrier_id, barrier_sequence, shard_versions, lineage]
    normalization: exported_snapshot_version
    allowed_drift: none
  numeric_state:
    mode: exact_by_default_with_explicit_future_tolerance_only
    tolerance_budget: []
    required_if_toleranced: [field_family, comparator, threshold]
    default_for_unlisted_fields: exact
  observation_export:
    envelope:
      mode: exact_for_host_visible_exports
      fields: [schema_version, field_set, visibility_label, provenance, source_snapshot_version]
    payload: inherit_numeric_state
  diagnostics_trace:
    structured:
      mode: exact_for_host_visible_exports
      fields: [source_request_id, event_id, source_snapshot_version, resulting_snapshot_version, mismatch_code]
    prose: diagnostics_only
sync_barriers: [input_injection, partial_sync_commit, window_commit, export]
diagnostics_requirements:
  - backend_profile_id
  - budget_id
  - budget_version
  - comparison_reference
  - source_snapshot_version
  - resulting_snapshot_version
  - sync_barrier_id
  - host_state_owner
  - backend_state_owner
  - sync_policy
  - resident_state_scope
  - mismatch_domain
  - mismatch_code
  - mismatch_summary
mismatch_policy:
  maintained_profile_result: not_accepted
  candidate_result: fail_and_remain_unmaintained
  diagnostics_result: report_only
  quarantine_required: true
acceptance_gate: future_wp6_resident_state_promotion_review_with_ownership_sync_and_replay_evidence
change_reason: initial unmaintained resident-state candidate budget; host/backend split not yet accepted as maintained
```

Implementation note: unsynced backend-local state is diagnostics-only unless a
future profile declares ownership, sync cadence, and parity evidence.

### 4.5 `shadow_compare.unmaintained_candidate`

```yaml
budget_id: parity_budget.shadow_compare.unmaintained_candidate.v1
budget_version: 1
backend_profile_id: shadow_compare.unmaintained_candidate
profile_class: diagnostics_only
comparison_reference: cpu_exact.reference
budget_scope:
  maintained_status: unmaintained_candidate
  clock_domains: [reference_clock_only]
  state_shards: []
  output_families: [shadow_report, mismatch_report, diagnostics_trace]
  diagnostics_only_surfaces: [shadow_report, mismatch_report, human_readable_diagnostics_prose]
comparison_domains:
  event_order:
    mode: exact_identity_for_reference_stream
    key: [timestamp, priority, event_id]
    event_family_membership: exact
    allowed_drift: none
  snapshot_versions:
    mode: exact_identity_for_reference_links
    identity: [source_snapshot_version, barrier_id, barrier_sequence]
    normalization: exported_snapshot_version
    allowed_drift: none
  numeric_state:
    mode: diagnostics_only_until_promoted
    tolerance_budget: []
    required_if_promoted: [field_family, comparator, threshold]
    default_for_unlisted_fields: exact
  observation_export:
    envelope:
      mode: exact_if_exported
      fields: [schema_version, field_set, visibility_label, provenance, source_snapshot_version]
    payload: inherit_numeric_state
  diagnostics_trace:
    structured:
      mode: exact_for_shadow_report_ancestry
      fields: [source_request_id, event_id, source_snapshot_version, mismatch_code]
    prose: diagnostics_only
sync_barriers: [reference_export, shadow_report_export]
diagnostics_requirements:
  - backend_profile_id
  - budget_id
  - budget_version
  - comparison_reference
  - source_snapshot_version
  - shadow_run_id
  - compared_profile_id
  - sync_barrier_id
  - mismatch_domain
  - mismatch_code
  - mismatch_summary
mismatch_policy:
  maintained_profile_result: not_applicable
  candidate_result: report_only_and_remain_unmaintained
  diagnostics_result: report_only
  quarantine_required: false
acceptance_gate: future_wp6_shadow_compare_review_before_any_maintained_claim
change_reason: initial unmaintained shadow-compare placeholder; no shadow capability acceptance claimed
```

Implementation note: shadow comparison can explain differences, but this
placeholder does not make shadow output a maintained truth source.

## 5. Promotion And Revision Rules

1. A new or revised entry MUST increment `budget_version` when comparison
   domains, sync barriers, diagnostics requirements, mismatch policy, or
   acceptance gate change.
2. Promotion from `unmaintained_candidate` to maintained use MUST cite replay
   evidence, ownership metadata, sync policy, and validation results.
3. Promotion to `accelerated_exact` MUST keep `event_order`,
   `snapshot_versions`, maintained `numeric_state`, observation envelope, and
   structured diagnostics ancestry exact.
4. Promotion to `resident_state` MUST identify `host_visible_maintained_state`,
   `backend_resident_operational_state`, authoritative owner, and sync cadence
   before any capability flag may become true.
5. Any tolerated numeric field MUST be listed by field family, comparator, and
   threshold. A prose statement such as "close enough" is not a budget.
6. Diagnostics prose MAY change without failing maintained parity only when the
   structured diagnostics fields remain exact and the prose is labeled
   diagnostics-only.

## 6. Non-Goals

- Implementing runtime comparators or replay code.
- Creating the backend profile registry owned by WP6-A.
- Promoting GPU exact, resident-state, or shadow-compare behavior to maintained
  status.
- Editing `RuntimeCapabilities`, tests, or runtime backend code.
- Updating README or index publication pages.

## 7. Exit Criteria

This registry is ready for WP6-B handoff when:

1. Every entry includes `budget_id`, `budget_version`, `backend_profile_id`,
   `profile_class`, `comparison_reference`, `budget_scope`,
   `comparison_domains`, `sync_barriers`, `diagnostics_requirements`,
   `mismatch_policy`, `acceptance_gate`, and `change_reason`.
2. `cpu_exact.reference` is the only maintained exact baseline.
3. GPU helper, GPU exact, resident-state, and shadow-compare entries are marked
   diagnostics-only or unmaintained candidates until future promotion.
4. `event_order` and `snapshot_versions` are exact-only identity domains.
5. Numeric tolerance requires explicit field family, comparator, and threshold.
6. Observation envelope is exact and observation payload inherits
   `numeric_state`.
7. Diagnostics prose is excluded from maintained truth.
8. The Chinese companion has the same section order and reciprocal links.

## 8. Validation Commands

```bash
git diff --check
rg -n "budget_id|budget_version|backend_profile_id|profile_class|comparison_reference|budget_scope|comparison_domains|sync_barriers|diagnostics_requirements|mismatch_policy|acceptance_gate|change_reason" docs/task/simulation_architecture/wp6_parity_budget_registry_20260519*.md
rg -n "event_order|snapshot_versions|numeric_state|observation_export|diagnostics_trace|cpu_exact\\.reference|gpu_helpers\\.diagnostics_only|gpu_exact\\.unmaintained_candidate|resident_state\\.unmaintained_candidate|shadow_compare\\.unmaintained_candidate" docs/task/simulation_architecture/wp6_parity_budget_registry_20260519*.md
```
