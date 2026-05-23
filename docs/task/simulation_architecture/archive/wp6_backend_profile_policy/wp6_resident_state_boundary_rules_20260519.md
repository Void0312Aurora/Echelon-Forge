# WP6-C1 Resident-State Boundary Rules

Status: `2026-05-19` implementation-ready boundary rules for
resident-state ownership, sync policy, diagnostics separation, and capability
projection.

Language:

- English canonical: `wp6_resident_state_boundary_rules_20260519.md`
- Chinese companion: [wp6_resident_state_boundary_rules_20260519.zh.md](wp6_resident_state_boundary_rules_20260519.zh.md)

Inputs:

- [WP6-A backend profile registry](wp6_backend_profile_registry_20260519.md)
- [WP6-B parity budget registry](wp6_parity_budget_registry_20260519.md)
- [WP6-C + WP6-D integration and index sync](wp6_integration_and_index_sync_20260519.md)
- [WP2.5 scheduler semantics freeze](scheduler_semantics_wp25_20260519.md)
- [WP5 validation harness](validation_harness_wp5_20260519.md)

Normative language:

- `MUST` marks required metadata or behavior for any maintained resident-state
  profile.
- `MUST NOT` marks claims that cannot be made from candidate, diagnostics-only,
  or unsynced backend-local state.
- `SHOULD` marks the default implementation-preparation rule.
- `MAY` marks an allowed diagnostics, compatibility, or future promotion path.

## 1. Purpose

This document defines the WP6-C1 boundary between host-maintained truth,
backend-resident operational state, diagnostics exports, and future
resident-state capability projection.

It is intentionally conservative. The current A/B registries contain
`resident_state.unmaintained_candidate`, but they do not accept a maintained
resident-state profile. Therefore `RuntimeCapabilities`, `BackendCapabilityFacade`,
or any later capability surface MUST keep `supports_resident_state` false until
a maintained profile revision satisfies the promotion gates in this document.

## 2. Source Registry Consumption

WP6-C1 consumes, but does not modify, the WP6-A and WP6-B registry records below:

| Source | Consumed record | WP6-C1 interpretation |
|--------|-----------------|-----------------------|
| WP6-A backend profile registry | `resident_state.unmaintained_candidate` | A placeholder `resident_state` row. It is still an unmaintained candidate, its `sync_policy` is `undeclared_blocked`, and it cannot project maintained resident-state support. |
| WP6-B parity budget registry | `parity_budget.resident_state.unmaintained_candidate.v1` | A candidate budget, not an acceptance budget. It names required future comparison domains and barriers, but it does not make backend-resident state maintained truth. |

Registry consumers MUST NOT infer support from the existence of either record.
The only valid projection from the current pair is:

```yaml
backend_profile_id: resident_state.unmaintained_candidate
parity_budget_ref: parity_budget.resident_state.unmaintained_candidate.v1
maintained_status: unmaintained_candidate
supports_resident_state: false
diagnostics_result: report_only
```

## 3. Boundary Vocabulary

The five sync-policy labels below are the only WP6-C1 resident-state boundary
labels that a future maintained profile may use. A profile may combine labels
only when each state shard has a single authoritative owner and an explicit
barrier contract.

| Boundary label | Definition | Allowed use | Forbidden declaration | Promotion gate |
|----------------|------------|-------------|-----------------------|----------------|
| `host-owned` | Host state is the authoritative maintained truth. Backend work may be derived from host inputs, but host committed snapshots, event order, and structured diagnostics remain canonical. | Maintained CPU exact baseline, compatibility fallbacks, backend helper inputs, and reconstructed exports whose truth is checked against host snapshots. | MUST NOT declare backend-local caches, device memory, queue completion order, or helper output as maintained truth. MUST NOT set `supports_resident_state` true from this label alone. | Identify host-owned shards, host barriers, exported snapshot identity, and the parity budget that verifies the host truth source. |
| `backend-owned` | A named backend shard is authoritative for a named maintained state scope after accepted sync and replay gates. Host-visible truth is reconstructed, exported, or committed from that backend-owned shard at declared barriers. | Future maintained resident-state profiles where the backend owns a specific operational shard and exposes a host-visible maintained result. | MUST NOT be declared for `resident_state.unmaintained_candidate`. MUST NOT hide owner changes behind generic acceleration or probe availability. MUST NOT let unsynced backend-local state affect committed host state. | Create a maintained registry revision that names `backend_state_owner`, `state_scope`, reconstruction or export rules, sync barriers, parity budget, replay evidence, and validation gate. |
| `partial-sync` | Host and backend each own named shards, and only declared fields cross the boundary at declared cadence, trigger, and barrier points. | Backend-resident working sets that periodically synchronize host-visible state, observation packets, or committed exports. | MUST NOT leave cadence, triggers, barriers, conflict resolution, or stale-read behavior implicit. MUST NOT treat non-synced fields as maintained parity evidence. | Declare per-shard ownership, sync cadence, sync trigger, barrier ids, stale-state policy, reconstruction rule, mismatch policy, and replay validation. |
| `observation-only` | Backend-resident state may produce host-visible observations, but it does not own committed world state outside the observation envelope and declared provenance. | Sensor, visibility, or perception outputs where the maintained surface is the observation envelope plus payload comparison domain. | MUST NOT mutate committed world state, scheduler state, engagement state, or fallback control flow. MUST NOT use observation success to claim full resident-state ownership. | Declare observation field set, source snapshot version, visibility label, provenance, numeric comparison rule, export barrier, and replay evidence against the reference profile. |
| `export-only` | Backend or helper output crosses to the host as report-only diagnostics or one-way export. It is never a maintained state owner. | Diagnostics traces, helper metrics, probe exports, mismatch reports, and candidate evidence. | MUST NOT set `supports_resident_state` true. MUST NOT drive committed state, scheduler ordering, fallback decisions, or maintained parity acceptance. | Keep outputs labeled diagnostics-only or candidate evidence; promotion requires reclassification to `backend-owned`, `partial-sync`, or `observation-only` with a maintained budget and validation gate. |

`undeclared_blocked` is not a maintained boundary label. It means the profile
has not declared enough ownership or sync semantics to be used as maintained
resident-state support.

## 4. Maintained Profile Contract

A future maintained resident-state profile MUST declare all fields below before
any capability surface may set `supports_resident_state` true:

1. `backend_profile_id`, `profile_class: resident_state`, and maintained
   `comparison_reference`.
2. `host_state_owner` and `backend_state_owner` for every state shard in scope.
3. `sync_policy` selected from `host-owned`, `backend-owned`, `partial-sync`,
   `observation-only`, or `export-only`, with per-shard assignment when mixed.
4. `state_scope`, including host-visible maintained state and
   backend-resident operational state.
5. Sync cadence, triggers, barriers, stale-read behavior, conflict resolution,
   and failure quarantine behavior.
6. Host-visible reconstruction, commit, or export rule, including
   `SnapshotVersion` normalization when snapshots are compared.
7. `parity_budget_ref` that is maintained, not a candidate placeholder.
8. Structured diagnostics requirements and diagnostics-only labels for every
   unsynced backend-local field.
9. Validation gate that includes replay evidence, mismatch policy, and WP5
   harness coverage for the declared state scope.

If any field is missing, the profile remains unavailable for maintained
resident-state support even if backend code, device memory, worker threads, or
probeable deployment facts exist.

## 5. Completion Order And Unsynced State

Backend thread completion order MUST NOT become maintained truth. Maintained
event order remains the declared scheduler order at accepted barriers, not the
physical order in which backend workers, GPU kernels, async queues, or helper
threads finish.

Unsynced backend-local state is diagnostics-only. This includes backend-local
caches, device-resident working sets, queue-local scratch state, speculative
intermediate values, helper metrics, and any state that lacks an accepted
host-visible reconstruction or export barrier. Such state MAY be exported as
candidate evidence or diagnostics, but it MUST NOT:

1. Define committed host state.
2. Define maintained event order or snapshot identity.
3. Satisfy a parity budget by itself.
4. Set or imply `supports_resident_state`.
5. Drive fallback, promotion, or acceptance decisions unless a maintained
   profile later declares that control path.

## 6. Capability Projection Rules

Capability projection MUST be explainable from maintained registry metadata
plus probeable deployment facts. Probeable facts can explain availability of a
declared profile, but they cannot create resident-state semantics.

Projection rules:

1. `resident_state.unmaintained_candidate` MUST project
   `supports_resident_state: false`.
2. `parity_budget.resident_state.unmaintained_candidate.v1` MUST remain a
   candidate budget until replaced by a maintained budget revision.
3. `export-only` and diagnostics-only outputs MUST project report-only or
   observability affordances, not maintained state support.
4. `host-owned` profiles MAY be maintained baselines, but they do not imply
   resident-state support unless backend-resident ownership is also declared
   and accepted.
5. `backend-owned`, `partial-sync`, or `observation-only` profiles MAY set
   `supports_resident_state` true only after the maintained profile contract
   and promotion checklist are both satisfied.

Current required projection:

```yaml
RuntimeCapabilities:
  supports_resident_state: false
  resident_state_profile_id: null
  resident_state_reason: resident_state.unmaintained_candidate_is_not_maintained
  resident_state_diagnostics_allowed: true
```

## 7. Promotion Checklist

Promotion from `resident_state.unmaintained_candidate` to a maintained
resident-state profile requires a registry revision that completes every item
below:

1. Replace the candidate id or revise it into a stable maintained
   `backend_profile_id`.
2. Replace `undeclared_blocked` with an accepted boundary label and per-shard
   ownership map.
3. Replace `parity_budget.resident_state.unmaintained_candidate.v1` with a
   maintained parity budget revision.
4. Prove event order at declared barriers, not backend thread completion order.
5. Prove snapshot identity or host-visible reconstruction at declared barriers.
6. Label unsynced backend-local state as diagnostics-only and keep it outside
   maintained parity.
7. Define mismatch policy, quarantine behavior, and rollback or fallback
   non-interference.
8. Provide WP5 replay or validation harness evidence for the declared scope.
9. Update capability projection policy so `supports_resident_state` becomes
   true only for the maintained profile and only when deployment probes also
   satisfy the declared availability conditions.

Until every item passes review, the candidate remains unmaintained and
`supports_resident_state` remains false.

## 8. Non-Goals

- Editing WP6-A or WP6-B registries.
- Editing runtime code, bindings, tests, README files, or publication indexes.
- Promoting `resident_state.unmaintained_candidate`.
- Claiming exact GPU, shadow-style, or resident-state support.
- Treating backend thread completion order as scheduler truth.
- Treating unsynced backend-local state as maintained parity evidence.

## 9. Validation Commands

```bash
git diff --check
rg -n "host-owned|backend-owned|partial-sync|observation-only|export-only|resident_state\\.unmaintained_candidate|parity_budget\\.resident_state\\.unmaintained_candidate\\.v1|supports_resident_state|backend thread completion order|unsynced backend-local state" docs/task/simulation_architecture/wp6_resident_state_boundary_rules_20260519*.md
rg -n "wp6_resident_state_boundary_rules_20260519\\.zh\\.md" docs/task/simulation_architecture/wp6_resident_state_boundary_rules_20260519.md
rg -n "wp6_resident_state_boundary_rules_20260519\\.md" docs/task/simulation_architecture/wp6_resident_state_boundary_rules_20260519.zh.md
```
