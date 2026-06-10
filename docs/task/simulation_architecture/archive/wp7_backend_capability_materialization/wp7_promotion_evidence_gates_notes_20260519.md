# WP7-C Implementation Notes: Promotion Evidence Gates

Status: `2026-05-19` implementation-ready notes for the WP7-C second design
refinement wave.

Language:

- English canonical: `wp7_promotion_evidence_gates_notes_20260519.md`
- Chinese companion:
  [wp7_promotion_evidence_gates_notes_20260519.zh.md](wp7_promotion_evidence_gates_notes_20260519.zh.md)
- Dispatch sheet:
  [wp7_promotion_evidence_gates_cluster_20260519.md](wp7_promotion_evidence_gates_cluster_20260519.md)

Inputs:

- [WP7 backend capability materialization](backend_capability_materialization_wp7_20260519.md)
- [WP7-A registry materialization](wp7_registry_materialization_cluster_20260519.md)
- [WP7-A implementation notes](wp7_registry_materialization_notes_20260519.md)
- [WP7-D multi-fidelity entry conditions](wp7_multifidelity_entry_conditions_cluster_20260519.md)
- [WP7-D implementation notes](wp7_multifidelity_entry_conditions_notes_20260519.md)
- [WP6 backend profile registry](wp6_backend_profile_registry_20260519.md)
- [WP6 parity budget registry](wp6_parity_budget_registry_20260519.md)
- [WP6 resident-state boundary rules](wp6_resident_state_boundary_rules_20260519.md)
- [WP5 validation harness](validation_harness_wp5_20260519.md)

## 1. Operating Rule

WP7-C defines promotion gate evidence only. It does not promote
`gpu_exact.unmaintained_candidate`, `resident_state.unmaintained_candidate`, or
`shadow_compare.unmaintained_candidate`.

A candidate may project maintained capability only after all evidence in its
promotion gate is accepted together:

1. maintained backend profile registry revision,
2. maintained parity budget revision,
3. ownership and sync contract,
4. event order and snapshot evidence,
5. mismatch and quarantine policy,
6. replay evidence,
7. facade/core layering evidence,
8. WP5 harness mapping,
9. acceptance review that updates capability projection rules.

Fail-closed rule: if any required item is absent, stale, candidate-only,
diagnostics-only, or incomplete, capability projection remains false. Runtime
code, GPU helper availability, deployment probes, faster execution, or a
fidelity request label cannot override this rule.

## 2. Gate Record Shape

Future implementation or review checklists should represent each promotion gate
as a record with these fields:

```yaml
promotion_gate_id: exact_gpu_promotion_gate
candidate_profile_id: gpu_exact.unmaintained_candidate
required_profile_registry_revision:
  backend_profile_id: future-maintained-profile-id
  maintained_status: maintained
required_parity_budget_revision:
  budget_id: future-maintained-budget-id
  budget_version: incremented
ownership_sync_contract:
  host_state_owner: declared
  backend_state_owner: declared
  sync_policy: declared
event_snapshot_evidence:
  event_order: exact_or_budgeted_by_domain
  snapshot_versions: exact_or_reconstructed_at_declared_barriers
mismatch_quarantine_policy:
  mismatch_policy: fail_or_quarantine_for_maintained_result
  quarantine_required: true
replay_evidence:
  seeds_events_snapshots_barriers: present
facade_core_layering_evidence:
  maintained_facade_path: no_raw_core_bypass
wp5_harness_mapping:
  mandatory_tiers: []
  scope_condition_tiers: []
acceptance_review:
  required: true
capability_projection:
  remains_false_until_acceptance_review: true
```

The shape is descriptive, not a runtime schema commitment. The exact field names
may adapt to WP7-A materialization, but the obligations must not be weakened.

## 3. Exact GPU Promotion Gate

`exact_gpu_promotion_gate` applies to `gpu_exact.unmaintained_candidate`.
Promotion means a future accelerated exact profile may be treated as maintained
truth for the declared scope. It is not enough to prove that a GPU kernel runs
or that helper probes are available.

| Evidence area | Required evidence before promotion |
|---------------|------------------------------------|
| Profile registry revision | A maintained backend profile row replaces or supersedes `gpu_exact.unmaintained_candidate`; it names stable `backend_profile_id`, `profile_class: accelerated_exact`, maintained `comparison_reference`, `host_state_owner`, `backend_state_owner`, `sync_policy`, `state_scope`, `observability_scope`, `validation_gate`, `maintained_status`, and source provenance. |
| Parity budget revision | A maintained budget replaces `parity_budget.gpu_exact.unmaintained_candidate.v1`, increments `budget_version`, and keeps `event_order`, `snapshot_versions`, observation envelope, and structured diagnostics ancestry exact. Any numeric tolerance would disqualify `accelerated_exact` and require reclassification. |
| Ownership and sync | The proposal names whether host or backend owns each state shard, the sync barriers for input injection, tick commit, window commit, and export, and the rule that GPU completion order is never scheduler truth. |
| Event order and snapshot evidence | Evidence must prove identical event family membership, timestamp/priority/event id ordering, exported `SnapshotVersion`, barrier id, barrier sequence, shard-version map, and lineage against `cpu_exact.reference`. |
| Mismatch and quarantine policy | Maintained result mismatches fail the gate. Candidate mismatch output is quarantined from committed state and retained only as labeled diagnostics. A mismatch summary must include domain, code, source snapshot, resulting snapshot, and backend build/profile ids. |
| Replay evidence | Replay must reconstruct the same facade request stream, deterministic seed, event log, barrier sequence, committed snapshots, observation exports, and diagnostics ancestry on both CPU reference and GPU candidate paths. |
| Facade/core layering evidence | Maintained access must go through facade request/result contracts. The accelerated core must not expose raw runtime mutation paths, hidden fallback control flow, or helper-only capability projection. |
| WP5 harness mapping | Mandatory tiers: design, trace, boundary, replay/evidence. Scope-conditioned tier: information/belief is mandatory when the exact GPU scope includes observation, track, data-link, belief, or policy-input surfaces. |
| Acceptance review | Review must accept the profile registry revision, parity budget revision, replay report, mismatch/quarantine policy, facade/core layering evidence, and capability projection update in the same promotion packet. |

Projection guard: `projection.exact_gpu_supported` remains false until the
acceptance review explicitly points to the maintained profile and maintained
budget. `fast_training` and `large_scale_swarm` requests may ask for throughput
or scale, but they do not bypass this promotion gate.

## 4. Resident-State Promotion Gate

`resident_state_promotion_gate` applies to
`resident_state.unmaintained_candidate`. Promotion means a future profile may
declare backend-resident ownership or synchronization for a named maintained
state scope. Unsynced backend-local state remains diagnostics-only.

| Evidence area | Required evidence before promotion |
|---------------|------------------------------------|
| Profile registry revision | A maintained resident-state profile row replaces or supersedes `resident_state.unmaintained_candidate`; it names stable `backend_profile_id`, `profile_class: resident_state`, maintained `comparison_reference`, per-shard `host_state_owner`, per-shard `backend_state_owner`, accepted `sync_policy`, `state_scope`, `observability_scope`, `validation_gate`, `maintained_status`, and source provenance. |
| Parity budget revision | A maintained budget replaces `parity_budget.resident_state.unmaintained_candidate.v1`, increments `budget_version`, and names maintained host-visible state, backend-resident operational state, comparison domains, sync barriers, diagnostics requirements, mismatch policy, and acceptance gate. |
| Ownership and sync | The proposal must choose accepted WP6-C1 labels such as `backend-owned`, `partial-sync`, or `observation-only` per shard; define cadence, triggers, barriers, stale-read policy, conflict resolution, reconstruction/export rules, rollback or fallback non-interference, and quarantine behavior. |
| Event order and snapshot evidence | Evidence must prove scheduler event order at declared barriers, not backend thread completion order. Host-visible reconstruction or export must normalize to exported `SnapshotVersion` with barrier id, barrier sequence, shard versions, and lineage. |
| Mismatch and quarantine policy | Stale, conflicting, unsynced, or unreconstructable state fails the gate and is quarantined from maintained state. Diagnostics exports must label backend-local caches, device-resident working sets, queue-local scratch state, and speculative values as diagnostics-only. |
| Replay evidence | Replay must reconstruct pre-sync, sync, and post-sync state for every declared shard, including owner map, source snapshot, resulting snapshot, barrier id, stale-state outcome, conflict outcome, and diagnostics ancestry. |
| Facade/core layering evidence | Public maintained paths must consume facade exports, reconstructed snapshots, or declared observation packets. No policy, scheduler, or engagement path may read raw backend-resident truth outside the accepted facade contract. |
| WP5 harness mapping | Mandatory tiers: design, boundary, replay/evidence. Trace is mandatory when resident state touches command, launch, munition, effect, damage, reward, termination, or scheduler traces. Information/belief is mandatory when resident state touches observation, visibility, track, data-link, belief, or decision inputs. |
| Acceptance review | Review must accept the ownership/sync map, resident-state boundary label, maintained budget, stale-state policy, mismatch/quarantine policy, replay report, facade/core layering evidence, and capability projection update together. |

Projection guard: `projection.resident_state_supported` remains false until the
acceptance review explicitly points to the maintained resident-state profile
and maintained budget. `sensor_heavy`, `fast_training`, and
`large_scale_swarm` requests may stress resident-like workloads, but they do not
bypass this promotion gate.

## 5. Shadow Compare Promotion Gate

`shadow_compare_promotion_gate` applies to
`shadow_compare.unmaintained_candidate`. Promotion does not mean shadow output
may silently affect committed state. A maintained shadow profile, if ever
accepted, must first define whether it is non-mutating diagnostics, a maintained
comparison service, or a separate reviewed control path.

| Evidence area | Required evidence before promotion |
|---------------|------------------------------------|
| Profile registry revision | A maintained or explicitly diagnostics-only shadow profile row replaces or supersedes `shadow_compare.unmaintained_candidate`; it names stable `backend_profile_id`, profile class, comparison reference, non-interference contract, observability scope, validation gate, maintained status, and source provenance. |
| Parity budget revision | A maintained budget or accepted diagnostics budget replaces `parity_budget.shadow_compare.unmaintained_candidate.v1`, increments `budget_version`, and names compared profile ids, reference stream identity, shadow run id, comparison domains, diagnostics requirements, mismatch policy, and acceptance gate. |
| Ownership and sync | The proposal must prove the host reference path owns committed state. Shadow outputs are export-only unless a later maintained profile explicitly declares a separate non-mutating or mutating control path and passes its own review. |
| Event order and snapshot evidence | Evidence must link shadow reports to reference event ids, source snapshot versions, barrier ids, barrier sequence, compared profile id, and shadow run id. Report timing must not reorder or influence the maintained reference stream. |
| Mismatch and quarantine policy | Shadow mismatches are report-only unless a future maintained control path is accepted. Any mismatch that could affect fallback, scheduling, policy input, or committed state must trigger quarantine and fail promotion. |
| Replay evidence | Replay must reproduce the reference stream, shadow input capture, shadow output report, mismatch code, and diagnostics ancestry without requiring the shadow path to mutate committed state. |
| Facade/core layering evidence | Shadow results must be surfaced as diagnostics or reviewed comparison outputs through facade evidence. Core shadow helpers must not bypass facade labels, mutate raw runtime state, or toggle capability projection by availability. |
| WP5 harness mapping | Mandatory tiers: design, boundary, replay/evidence. Trace is mandatory when shadow reports compare command, launch, effect, damage, reward, termination, or event ancestry. Information/belief is mandatory when shadow reports compare observation, visibility, track, belief, or policy-input surfaces. |
| Acceptance review | Review must accept the non-interference proof, diagnostics separation, maintained or diagnostics budget classification, mismatch/quarantine policy, replay report, facade/core layering evidence, and capability projection update together. |

Projection guard: `projection.shadow_supported` remains false unless acceptance
review explicitly accepts a maintained shadow capability. `weapon_effects_heavy`
or `sensor_heavy` requests may request additional comparison diagnostics, but
they do not bypass this promotion gate or allow shadow output to affect
committed state.

## 6. WP5 Harness Mapping

The WP5 mapping below is the required minimum. Mandatory means every promotion
proposal for that gate must pass the tier. Scope-conditioned means the tier is
mandatory when the candidate touches the listed domain.

| Gate | Design | Trace | Boundary | Information/belief | Replay/evidence |
|------|--------|-------|----------|--------------------|-----------------|
| `exact_gpu_promotion_gate` | Mandatory: profile, budget, lifecycle, and capability projection artifacts match WP6/WP7-A fields. | Mandatory: event ids, event family membership, and diagnostics ancestry match the CPU reference for declared domains. | Mandatory: maintained paths use facade contracts and no raw core bypass. | Scope-conditioned: mandatory for observation, track, visibility, belief, data-link, or policy-input scope. | Mandatory: deterministic seeds, event order, snapshot versions, barriers, facade exports, and diagnostics reproduce against `cpu_exact.reference`. |
| `resident_state_promotion_gate` | Mandatory: ownership map, sync policy, resident boundary label, and state scope are documented and machine-checkable. | Scope-conditioned: mandatory for scheduler, command, launch, munition, effect, damage, reward, or termination scope. | Mandatory: host/backend boundary, reconstruction/export, and facade-only maintained access are enforced. | Scope-conditioned: mandatory for observation, visibility, track, data-link, belief, or decision-input scope. | Mandatory: pre-sync, sync, post-sync, stale-state, conflict, barrier, snapshot, and quarantine evidence replay. |
| `shadow_compare_promotion_gate` | Mandatory: non-interference, diagnostics separation, budget classification, and projection rules are documented. | Scope-conditioned: mandatory for event, engagement, reward, termination, or trace ancestry comparisons. | Mandatory: shadow output cannot mutate committed state or bypass facade diagnostics labels. | Scope-conditioned: mandatory for observation, visibility, track, belief, or policy-input comparisons. | Mandatory: reference stream, shadow capture, report export, mismatch code, and diagnostics ancestry replay. |

Promotion packets should include a WP5 evidence index that lists exact test
names, doc checks, fixtures, replay artifacts, or review exhibits for each
mandatory and scope-conditioned tier. Missing scope analysis is itself an
incomplete gate, so capability projection remains false.

## 7. Fidelity Request Non-Bypass Rule

WP7-D request labels are intent, not support claims. The following bindings are
required:

| Fidelity request | Gate interaction |
|------------------|------------------|
| `fast_training` | May use diagnostics or candidate paths only when labeled training-only/report-only. It cannot claim exact GPU, resident-state, or shadow support without the relevant promotion gate and acceptance review. |
| `sensor_heavy` | Must obey observation envelope, visibility, track, belief, and information-state evidence. It cannot use resident-state or shadow diagnostics as maintained observation truth without the relevant promotion gate. |
| `weapon_effects_heavy` | Must preserve launch, munition, effect, damage, reward, termination, event ancestry, mismatch, quarantine, and replay evidence. It cannot weaken exact event order or shadow non-interference. |
| `large_scale_swarm` | May request scale-oriented scheduling, but scale does not relax snapshot identity, shard-version evidence, quarantine, or capability projection gates. |
| `exact_evaluation` | Uses `cpu_exact.reference` unless a future exact profile has passed its promotion gate and acceptance review. |

If a request cannot bind to a maintained profile and maintained budget, the
request must be rejected, routed to `cpu_exact.reference`, or reported as
diagnostics-only according to its mismatch policy. It must not set maintained
capability projection to true.

## 8. Future Test Plan

No runtime code or pytest is required in this WP7-C design wave. If a later
change adds tests, they should start as architecture-doc or registry-seed checks
that assert:

1. each candidate has a named promotion gate,
2. each promotion gate cites profile revision, budget revision, ownership/sync,
   event/snapshot evidence, mismatch/quarantine, replay, facade/core layering,
   WP5 mapping, and acceptance review,
3. all current candidate capability projection values remain false,
4. WP7-D request labels cannot promote candidates,
5. English and Chinese WP7-C documents keep reciprocal links and aligned
   section order.

Suggested future target:

```text
legacy proposed target name: wp7_promotion_evidence_gates_docs
```

The test should inspect documentation or future registry seed artifacts only.
It must not depend on runtime GPU helper behavior, resident-state runtime code,
or shadow execution.

## 9. Acceptance Checklist

WP7-C is ready for integration only when:

1. `exact_gpu_promotion_gate`, `resident_state_promotion_gate`, and
   `shadow_compare_promotion_gate` are documented.
2. Every gate lists profile registry revision, parity budget revision,
   ownership/sync, event order/snapshot evidence, mismatch/quarantine policy,
   replay evidence, facade/core layering evidence, WP5 harness mapping, and
   acceptance review requirements.
3. The WP5 mapping names mandatory and scope-conditioned tiers for design,
   trace, boundary, information/belief, and replay/evidence.
4. WP7-D request labels are explicitly blocked from bypassing promotion gates.
5. Incomplete gates keep capability projection false.
6. No language claims maintained exact GPU, resident-state, or shadow compare
   support today.

## 10. Validation Commands

```bash
git diff --check
rg -n "gpu_exact\\.unmaintained_candidate|resident_state\\.unmaintained_candidate|shadow_compare\\.unmaintained_candidate|promotion gate|WP5|replay|mismatch|quarantine|acceptance review|capability projection" docs/task/simulation_architecture/wp7_promotion_evidence_gates*20260519*.md
```
