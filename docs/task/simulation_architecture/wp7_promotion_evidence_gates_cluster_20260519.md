# WP7-C Dispatch Sheet: Promotion Evidence Gates

Status: `2026-05-19` planned WP7 promotion-gate dispatch sheet.

Language:

- English canonical: `wp7_promotion_evidence_gates_cluster_20260519.md`
- Chinese companion:
  [wp7_promotion_evidence_gates_cluster_20260519.zh.md](wp7_promotion_evidence_gates_cluster_20260519.zh.md)
- Implementation-ready notes:
  [wp7_promotion_evidence_gates_notes_20260519.md](wp7_promotion_evidence_gates_notes_20260519.md)

Inputs:

- [WP7 backend capability materialization](backend_capability_materialization_wp7_20260519.md)
- [WP7-A registry materialization](wp7_registry_materialization_cluster_20260519.md)
- [WP7-D multi-fidelity entry conditions](wp7_multifidelity_entry_conditions_cluster_20260519.md)
- [WP5 validation harness](validation_harness_wp5_20260519.md)
- [WP6 backend profile registry](wp6_backend_profile_registry_20260519.md)
- [WP6 parity budget registry](wp6_parity_budget_registry_20260519.md)
- [WP6 resident-state boundary rules](wp6_resident_state_boundary_rules_20260519.md)

## 1. Purpose

WP7-C defines the evidence gates that must pass before a backend candidate can
become a maintained capability. It is a gate-design task, not a promotion task.
It does not change `maintained_status`, parity budget acceptance, or capability
projection for any candidate.

The current candidate profiles remain unmaintained:

1. `gpu_exact.unmaintained_candidate`
2. `resident_state.unmaintained_candidate`
3. `shadow_compare.unmaintained_candidate`

## 2. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP7-C1 Exact GPU Promotion Gate` | Checklist for event-order identity, snapshot identity, ownership/sync, parity budget, and replay validation. | Docs and future test plan. | High. |
| `WP7-C2 Resident-State Promotion Gate` | Checklist for host/backend owner split, sync cadence, barrier ids, reconstruction/export, stale-state policy, and validation evidence. | Docs and future test plan. | High. |
| `WP7-C3 Shadow Compare Promotion Gate` | Checklist for non-interference, diagnostics separation, ancestry, mismatch policy, and whether shadow output can ever affect committed state. | Docs and future test plan. | High. |
| `WP7-C4 WP5 Harness Mapping` | Map each promotion gate to design, trace, boundary, information, and replay/evidence validation tiers. | Docs and test-index proposal. | Medium-high. |

## 3. Required Promotion Evidence

Any promotion proposal must provide:

1. a maintained backend profile registry revision,
2. a maintained parity budget revision,
3. host/backend ownership and sync policy,
4. event order and snapshot/version evidence,
5. diagnostics labels for non-maintained state,
6. mismatch and quarantine policy,
7. replay evidence,
8. facade/core layering evidence,
9. WP5 harness coverage,
10. an acceptance review that updates capability projection rules.

The detailed gate definitions live in the implementation notes. They define
three named gates:

1. `exact_gpu_promotion_gate` for `gpu_exact.unmaintained_candidate`,
2. `resident_state_promotion_gate` for
   `resident_state.unmaintained_candidate`,
3. `shadow_compare_promotion_gate` for
   `shadow_compare.unmaintained_candidate`.

Each gate must remain fail-closed. If any profile registry revision, parity
budget revision, ownership/sync contract, event order/snapshot evidence,
mismatch/quarantine policy, replay evidence, facade/core layering evidence,
WP5 harness mapping, or acceptance review is absent or incomplete, capability
projection for the promoted capability remains false.

WP7-D fidelity requests, including `fast_training`, `sensor_heavy`, and
`weapon_effects_heavy`, cannot bypass any promotion gate. Request labels may
select desired execution shape or validation emphasis, but they cannot convert
an unmaintained candidate into maintained support.

## 4. Non-Goals

- Do not promote any profile in this cluster.
- Do not implement exact GPU world-step.
- Do not implement resident-state runtime code.
- Do not make shadow output affect committed state.
- Do not relax WP6 candidate status without an acceptance review.

## 5. Acceptance Gates

This cluster is accepted when:

1. Each current candidate has a named promotion gate.
2. Each gate names required profile, parity, ownership, sync, and validation
   evidence.
3. Each gate maps to WP5 validation tiers.
4. The docs state that failed or incomplete gates keep capability projection
   false.
5. The docs state that WP7-D fidelity requests cannot bypass promotion gate
   evidence.
6. No wording implies current maintained support for exact GPU, resident-state,
   or shadow compare.

## 6. Validation Commands

```bash
git diff --check
rg -n "gpu_exact\\.unmaintained_candidate|resident_state\\.unmaintained_candidate|shadow_compare\\.unmaintained_candidate|promotion gate|WP5|replay|mismatch|quarantine|acceptance review|capability projection" docs/task/simulation_architecture/wp7_promotion_evidence_gates*20260519*.md
```
