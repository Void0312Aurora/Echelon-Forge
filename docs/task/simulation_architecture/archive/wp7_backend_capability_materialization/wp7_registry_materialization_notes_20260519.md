# WP7-A Registry Materialization Implementation Notes

Status: `2026-05-19` implementation-ready notes for the first WP7-A wave.

Language:

- English canonical: `wp7_registry_materialization_notes_20260519.md`
- Chinese companion:
  [wp7_registry_materialization_notes_20260519.zh.md](wp7_registry_materialization_notes_20260519.zh.md)
- Parent cluster:
  [wp7_registry_materialization_cluster_20260519.md](wp7_registry_materialization_cluster_20260519.md)

Inputs:

- [WP7 backend capability materialization](backend_capability_materialization_wp7_20260519.md)
- [WP6-A backend profile registry](wp6_backend_profile_registry_20260519.md)
- [WP6-B parity budget registry](wp6_parity_budget_registry_20260519.md)
- [WP6-C1 resident-state boundary rules](wp6_resident_state_boundary_rules_20260519.md)
- [WP6 backend profile policy acceptance review](../review/wp6_backend_profile_policy_acceptance_review_20260519.md)

## 1. First-Wave Choice

WP7-A should materialize the WP6 registries as a hand-maintained YAML seed
validated by schema checks. Markdown generation should wait until the seed and
schema have passed one review cycle.

Rationale:

1. WP6 has a small accepted surface: five `backend_profile_id` rows and five
   `budget_id` rows.
2. The WP6 documents combine normative tables, prose, and YAML examples. A
   markdown parser would be fragile and could accidentally make formatting
   choices authoritative.
3. WP7-B and WP7-C need a concrete field vocabulary now, especially
   `maintained_status`, `projection_eligibility`, `validation_gate`, and
   `acceptance_gate`.
4. A seed can remain subordinate to WP6 policy through explicit
   `source_doc_provenance` fields and drift checks.

Rejected alternatives:

| Alternative | Why not first wave |
|-------------|--------------------|
| Generated-from-markdown registry | Too brittle before the table/YAML extraction contract is reviewed. |
| Docs-only with parser tests deferred | Leaves WP7-B projection and WP7-C promotion evidence without a stable machine-facing shape. |

## 2. Proposed Seed Shape

The future seed should use two top-level arrays:

```yaml
registry_version: 1
accepted_policy_date: 2026-05-19
source_authority:
  - docs/task/simulation_architecture/wp6_backend_profile_registry_20260519.md
  - docs/task/simulation_architecture/wp6_parity_budget_registry_20260519.md
  - docs/task/simulation_architecture/wp6_resident_state_boundary_rules_20260519.md
  - docs/task/review/wp6_backend_profile_policy_acceptance_review_20260519.md
profiles: []
parity_budgets: []
```

The first seed file should be proposed at:

```text
docs/task/simulation_architecture/generated/wp7_backend_registry_seed_20260519.yaml
```

This notes file does not create that seed. It defines the shape so a later
implementation can add the seed and a narrow architecture-doc test without
changing the WP6 authority documents.

## 3. Profile Row Contract

Each profile row must include these WP6-A fields:

1. `backend_profile_id`
2. `profile_class`
3. `comparison_reference`
4. `host_state_owner`
5. `backend_state_owner`
6. `sync_policy`
7. `state_scope`
8. `parity_budget_ref`
9. `observability_scope`
10. `compatibility_rule`
11. `deprecation_rule`
12. `validation_gate`

Each profile row must also include these WP7-A materialization fields:

| Field | Allowed first-wave values |
|-------|---------------------------|
| `maintained_status` | `maintained_exact_baseline`, `diagnostics_only`, `unmaintained_candidate` |
| `projection_eligibility.maintained_cpu_exact_baseline` | `true` only for `cpu_exact.reference` |
| `projection_eligibility.exact_gpu_supported` | `false` for all current WP6 rows |
| `projection_eligibility.resident_state_supported` | `false` for all current WP6 rows |
| `projection_eligibility.shadow_supported` | `false` for all current WP6 rows |
| `projection_eligibility.diagnostics_allowed` | `true` for diagnostics-only/candidate evidence when labels remain report-only |
| `source_doc_provenance.path` | WP6 source doc path |
| `source_doc_provenance.section` | Source heading or table section |
| `source_doc_provenance.row_label` | The profile id or row label |
| `source_doc_provenance.accepted_by` | `wp6_backend_profile_policy_acceptance_review_20260519.md` |

Maintained support must be computed from explicit materialized fields, not from
helper availability or from `profile_class` alone.

## 4. Parity Budget Row Contract

Each parity budget row must include these WP6-B fields:

1. `budget_id`
2. `budget_version`
3. `backend_profile_id`
4. `profile_class`
5. `comparison_reference`
6. `budget_scope`
7. `comparison_domains`
8. `sync_barriers`
9. `diagnostics_requirements`
10. `mismatch_policy`
11. `acceptance_gate`
12. `change_reason`

Each parity budget row must also include:

| Field | Allowed first-wave values |
|-------|---------------------------|
| `maintained_status` | Mirrors `budget_scope.maintained_status` after normalization. |
| `source_doc_provenance.path` | `docs/task/simulation_architecture/wp6_parity_budget_registry_20260519.md` |
| `source_doc_provenance.section` | Budget subsection such as `4.1 cpu_exact.reference`. |
| `source_doc_provenance.row_label` | The `budget_id`. |
| `source_doc_provenance.accepted_by` | `wp6_backend_profile_policy_acceptance_review_20260519.md` |

The normalized `maintained_status` values are:

| WP6 budget scope value | WP7-A normalized value |
|------------------------|------------------------|
| `maintained_exact_baseline` | `maintained_exact_baseline` |
| `diagnostics_only_not_truth` | `diagnostics_only` |
| `unmaintained_candidate` | `unmaintained_candidate` |

## 5. Initial Row Mapping

The seed must contain exactly the accepted WP6 rows until a later promotion
review adds or revises records.

| `backend_profile_id` | `budget_id` | `maintained_status` | `projection` |
|----------------------|-------------|---------------------|--------------|
| `cpu_exact.reference` | `parity_budget.cpu_exact.reference.v1` | `maintained_exact_baseline` | CPU exact reference baseline only. |
| `gpu_helpers.diagnostics_only` | `parity_budget.gpu_helpers.diagnostics_only.v1` | `diagnostics_only` | Diagnostics/probe facts only; no maintained support. |
| `gpu_exact.unmaintained_candidate` | `parity_budget.gpu_exact.unmaintained_candidate.v1` | `unmaintained_candidate` | Candidate evidence only; exact GPU support false. |
| `resident_state.unmaintained_candidate` | `parity_budget.resident_state.unmaintained_candidate.v1` | `unmaintained_candidate` | Candidate evidence only; resident-state support false. |
| `shadow_compare.unmaintained_candidate` | `parity_budget.shadow_compare.unmaintained_candidate.v1` | `unmaintained_candidate` | Diagnostics reports only; shadow support false. |

The projection adapter planned by WP7-B may expose deployment facts, but it must
not convert them into maintained capability support. The current conservative
truth is:

```yaml
projection:
  maintained_cpu_exact_baseline: true
  exact_gpu_supported: false
  resident_state_supported: false
  shadow_supported: false
  gpu_helper_diagnostics_allowed: true
```

## 6. Drift Detection Plan

When a seed and tests are added, the doc/schema test should fail on these
conditions:

1. Missing profile fields:
   `backend_profile_id`, `profile_class`, `comparison_reference`,
   `host_state_owner`, `backend_state_owner`, `sync_policy`, `state_scope`,
   `parity_budget_ref`, `observability_scope`, `compatibility_rule`,
   `deprecation_rule`, `validation_gate`, `maintained_status`,
   `projection_eligibility`, or `source_doc_provenance`.
2. Missing parity budget fields:
   `budget_id`, `budget_version`, `backend_profile_id`, `profile_class`,
   `comparison_reference`, `budget_scope`, `comparison_domains`,
   `sync_barriers`, `diagnostics_requirements`, `mismatch_policy`,
   `acceptance_gate`, `change_reason`, `maintained_status`, or
   `source_doc_provenance`.
3. A `parity_budget_ref` that does not match any `budget_id`.
4. A `budget_id` whose `backend_profile_id` does not match a profile row.
5. A budget/profile `profile_class` mismatch.
6. Any current WP6 row except `cpu_exact.reference` setting maintained
   projection support to true.
7. A promotion claim without updated `validation_gate`, `acceptance_gate`,
   maintained budget status, and source provenance.

The first test target, if added, should be:

```text
tests/architecture/test_wp7_registry_materialization_docs.py
```

It should inspect documentation or the seed only. It must not depend on runtime
GPU helper behavior, runtime backend selection, or capability promotion.

## 7. Handoff Notes For WP7-B/C

WP7-B may consume the materialized seed shape to define a conservative
`RuntimeCapabilities` projection contract. It must treat `maintained_status`
and `projection_eligibility` as the gate, then combine probeable deployment
facts only as diagnostics or availability explanation.

WP7-C may consume the same seed shape to require promotion evidence. Promotion
must update both sides of the registry pair: profile `validation_gate` and
budget `acceptance_gate`. A capability claim is not accepted if either side
remains candidate, diagnostics-only, or lacks source provenance.

## 8. Validation Commands

```bash
git diff --check
rg -n "backend_profile_id|parity_budget_ref|validation_gate|budget_id|acceptance_gate|projection|maintained_status" docs/task/simulation_architecture/wp7_registry_materialization*20260519*.md
```
