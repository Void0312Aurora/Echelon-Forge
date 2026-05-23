# WP6-B Normative Dispatch Sheet: Parity Budget And Comparison Rules

Status: `2026-05-19` completed dispatch sheet for parity budgets and comparison
rules, with implementation-ready registry output.

Language:

- English canonical: `wp6_parity_budget_cluster_20260519.md`
- Chinese companion: [wp6_parity_budget_cluster_20260519.zh.md](wp6_parity_budget_cluster_20260519.zh.md)
- Implementation registry: [wp6_parity_budget_registry_20260519.md](wp6_parity_budget_registry_20260519.md)

Inputs:

- [WP6 backend profile policy](backend_profile_policy_wp6_20260519.md)
- [WP6-A backend profile taxonomy cluster](wp6_backend_profile_taxonomy_cluster_20260519.md)
- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [architecture and performance research followup](../../plan/architecture/architecture_and_performance_research_followup.md)
- [architecture plan review](../review/architecture_plan_review_20260519.md)
- [Temp-02 SCAL architecture vision review](../review/temp-02_review_20260519.md)
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

This dispatch sheet turns `WP6-B Parity Budget And Comparison Rules` into a
bounded documentation task. It freezes how backend profiles publish
parity-budget metadata, which comparisons are exact vs toleranced, and which
differences are diagnostics-only.

The central rule is simple: a parity budget is profile-owned metadata, not a
single scalar tolerance knob. It belongs to the backend profile that claims it
and must travel with that profile's comparison contract.

## 2. Dispatch Deliverables

| Stream | Required output | Owner profile | Reasoning budget |
|--------|-----------------|---------------|------------------|
| `WP6-B1 Budget Template` | Canonical parity-budget schema, required fields, and one worked example per profile class. | Parity budget worker. | High. |
| `WP6-B2 Comparison Domain Rules` | Domain-by-domain exactness and tolerance rules for event order, snapshot versions, numeric state, observation export, and diagnostics trace. | Parity budget worker. | High. |
| `WP6-B3 Profile-Specific Guidance` | Executable budget guidance for `reference`, `accelerated_exact`, `resident_state`, and `approximate`. | Parity budget worker. | High. |
| `WP6-B4 Diagnostics And Acceptance Rules` | Required diagnostics metadata, mismatch classification, and acceptance conditions for maintained budgets. | Integration-minded parity worker. | Medium-high. |

## 3. Parity Budget Template

Every maintained backend profile that claims parity MUST carry a profile-owned
`parity_budget` block in its metadata or in an explicitly referenced
profile-owned record. The budget MUST not be a free-floating scalar stored
outside the profile contract.

### 3.1 Required fields

| Field | Status | Meaning |
|-------|--------|---------|
| `budget_id` | MUST | Stable id for the budget record. |
| `budget_version` | MUST | Revision number for the budget record. |
| `backend_profile_id` | MUST | The profile that owns the budget. |
| `profile_class` | MUST | One of `reference`, `accelerated_exact`, `resident_state`, or `approximate`. |
| `comparison_reference` | MUST | The semantic anchor used for comparison. |
| `budget_scope` | MUST | Clock domains, state shards, and export families covered by the budget. |
| `comparison_domains` | MUST | Domain-by-domain exactness and tolerance rules. |
| `sync_barriers` | MUST | Barriers used to anchor replay and comparison. |
| `diagnostics_requirements` | MUST | Structured fields needed to explain mismatches. |
| `mismatch_policy` | MUST | What happens when the comparison fails. |
| `acceptance_gate` | MUST | Review or test gate required before maintained use. |
| `change_reason` | MAY | Short reason for a budget revision. |

### 3.2 Canonical shape

```yaml
parity_budget:
  budget_id: parity_budget.cpu_exact.reference.v1
  budget_version: 1
  backend_profile_id: cpu_exact.reference
  profile_class: reference
  comparison_reference: cpu_exact
  budget_scope:
    clock_domains: [physics.fixed_tick, sensor.scan_slot]
    state_shards: [physics, track, observation]
    output_families: [observation_packet, diagnostics_trace]
  acceptance_gate: wp6_b_acceptance_review
  change_reason: initial reference-profile parity budget
  comparison_domains:
    event_order:
      mode: exact
      key: [timestamp, priority, event_id]
      allowed_drift: none
    snapshot_versions:
      mode: exact
      identity: [world_id, global_version, barrier_id, barrier_sequence, shard_versions]
      allowed_drift: none
    numeric_state:
      mode: exact_or_toleranced
      comparator: exact
      tolerance_budget: {}
    observation_export:
      mode: exact_envelope_with_domain_payload
      envelope: [schema_version, field_set, visibility_label, provenance, source_snapshot_version]
      payload: inherit_numeric_state
    diagnostics_trace:
      mode: exact_graph_with_diagnostics_text
      ancestry: [source_request_id, event_id, source_snapshot_version, mismatch_summary]
      summary_text: diagnostics_only
  sync_barriers: [input_injection, window_commit, export]
  diagnostics_required:
    - backend_profile_id
    - budget_id
    - budget_version
    - source_snapshot_version
    - resulting_snapshot_version
    - comparison_reference
    - mismatch_summary
  mismatch_policy:
    maintained_profiles: fail
    diagnostics_only_profiles: report_only
```

Rules:

1. The budget MUST live inside backend profile metadata or in a profile-owned
   referenced block.
2. The budget MUST name its comparison reference.
3. The budget MUST name the clock domains or output families it covers.
4. The budget MUST name the sync barriers required for replayability.
5. The budget MUST name the diagnostics fields needed to explain mismatches.
6. The budget MUST version itself so later revisions can be reviewed without
   ambiguity.

## 4. Comparison Domain Rules

The comparison domains are layered, not interchangeable:

- Event order and snapshot versions are identity domains.
- Numeric state is the payload comparison domain.
- Observation export is the envelope-plus-payload bridge.
- Diagnostics trace is the ancestry-and-explanation domain.

If a value participates in more than one domain, the exact identity rule wins
for the identity layer, and the numeric tolerance rule applies only to the
payload layer.

| Comparison domain | Exact boundary | Toleranced boundary | Diagnostics-only boundary |
|-------------------|----------------|---------------------|---------------------------|
| Event order | The ordering key `(timestamp, priority, event_id)` and the event-family membership used to derive it MUST match exactly. | None for maintained parity. Any reorder is a mismatch. | A free-form explanation may differ, but it does not redefine order. |
| Snapshot versions | Snapshot identity, barrier id, barrier sequence, shard-version map, and lineage MUST match exactly. Any internal versioning must normalize to the exported `SnapshotVersion` before comparison. | None for maintained parity. Numeric payload inside a snapshot is compared under `numeric_state`, not here. | Pre-commit or compatibility snapshots MAY exist only when labeled diagnostics-only and excluded from maintained truth. |
| Numeric state | Values are exact when the budget says exact. | Only the field families listed in `tolerance_budget` may drift, and only under the declared comparator (`abs`, `rel`, `ulp`, or another explicit comparator). Unlisted fields default to exact. | Rounded or summary-only outputs may be emitted for diagnostics, but they do not count as maintained truth. |
| Observation export | Schema, field set, visibility label, provenance, and source snapshot reference MUST match exactly. | Numeric payload values inherit the `numeric_state` rule. The export envelope itself is never tolerant. | Pre-commit exports or compatibility views MAY exist only as diagnostics-only artifacts and MUST be labeled as such. |
| Diagnostics trace | Structured ancestry ids, source request/event ids, source snapshot links, and mismatch codes MUST match exactly. | Human-readable summary text and formatting MAY vary if the structured trace stays identical. | Summary-only or narrative-only traces are diagnostics-only and MUST NOT replace the structured trace. |

## 5. Profile-Specific Budget Guidance

The profile guidance below is executable, not aspirational. Diagnostics-only
artifacts may reuse the same field names for reporting, but they do not count
as maintained parity budgets.

| Profile | Comparison reference | Budget rule | Default mismatch policy |
|---------|----------------------|-------------|-------------------------|
| `reference` | `cpu_exact` or the maintained CPU exact path. | Exact across all maintained domains; no tolerance budget. | Fail. |
| `accelerated_exact` | The maintained reference profile. | Must stay semantically exact; acceleration internals do not relax parity. | Fail. |
| `resident_state` | The maintained host-visible reference path. | Must split host-visible maintained state from backend-resident operational state and anchor comparisons at declared sync barriers. | Fail unless a domain is explicitly marked diagnostics-only. |
| `approximate` | The named baseline profile. | Must spell out every tolerated field family and comparator; unlisted fields remain exact. | Report and quarantine until reviewed. |

### 5.1 `reference`

- `comparison_reference` SHOULD point to `cpu_exact` or the active maintained
  CPU baseline.
- `comparison_domains` MUST all be exact.
- `tolerance_budget` MUST be empty.
- `diagnostics_only` behavior is not accepted as maintained truth.
- `mismatch_policy` SHOULD be fail-fast because any drift is a real parity
  break.

### 5.2 `accelerated_exact`

- This profile reuses the reference parity budget.
- Event order, snapshot versions, numeric state, observation export, and
  diagnostics ancestry MUST remain exact on the maintained surfaces.
- Any accelerator-specific kernel differences live below the comparison layer
  and MUST NOT leak into exported maintained state.
- If a tolerance is required, the profile is no longer `accelerated_exact` and
  MUST be reclassified.
- `mismatch_policy` MUST be fail.

### 5.3 `resident_state`

- The budget MUST separate `host_visible_maintained_state` from
  `backend_resident_operational_state`.
- Comparisons SHOULD be anchored at the declared sync barriers; unsynced
  backend-local state is diagnostics-only unless explicitly promoted.
- Exported maintained snapshots MUST still obey exact rules for event order,
  snapshot versions, provenance, and observation envelope.
- Any tolerated numeric drift must be confined to an explicitly named field
  family and only if the review accepts that budget.
- If the host/backend split is not written down, the budget is incomplete.

### 5.4 `approximate`

- The budget MUST list every tolerated field family, comparator, and threshold.
- Unlisted fields default to exact.
- The profile MUST name its comparison reference and state why approximation is
  allowed.
- The profile SHOULD remain diagnostics-only until a review explicitly promotes
  it to maintained use.
- The profile MUST NOT describe itself as `reference` or `accelerated_exact`
  while tolerances remain in force.

## 6. Non-Goals

- Implementing parity checks or runtime comparators.
- Building a replay harness.
- Changing WP2.5 scheduler semantics.
- Letting wall-clock speed define parity.
- Hiding tolerances inside unversioned helper code.
- Treating approximate output as exact.
- Reopening the profile taxonomy inside this sheet.

## 7. Exit Criteria

This cluster exits when:

1. Every maintained profile carries a profile-owned parity budget record or a
   profile-owned reference to one.
2. Event order and snapshot versions are documented as exact-only identity
   domains.
3. Numeric state tolerance is explicit, field-family-specific, and named by
   comparator.
4. Observation export separates exact envelope rules from payload comparison
   rules.
5. Diagnostics trace distinguishes exact ancestry from diagnostics-only prose.
6. The guidance for `reference`, `accelerated_exact`, `resident_state`, and
   `approximate` is executable without guesswork.
7. The Chinese companion is structurally aligned enough for later publication.

## 8. Validation Commands

```bash
git diff --check
rg -n "budget_scope|mismatch_policy|diagnostics_requirements|comparison_domains|host_visible_maintained_state|tolerance_budget" docs/task/simulation_architecture/wp6_*.md
```
