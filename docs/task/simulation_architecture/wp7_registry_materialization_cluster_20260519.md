# WP7-A Registry Materialization

Status: `2026-05-19` implementation-ready WP7 first-wave preparation.

Language:

- English canonical: `wp7_registry_materialization_cluster_20260519.md`
- Chinese companion:
  [wp7_registry_materialization_cluster_20260519.zh.md](wp7_registry_materialization_cluster_20260519.zh.md)
- Implementation notes:
  [wp7_registry_materialization_notes_20260519.md](wp7_registry_materialization_notes_20260519.md)

Inputs:

- [WP7 backend capability materialization](backend_capability_materialization_wp7_20260519.md)
- [WP6-A backend profile registry](wp6_backend_profile_registry_20260519.md)
- [WP6-B parity budget registry](wp6_parity_budget_registry_20260519.md)
- [WP6-C1 resident-state boundary rules](wp6_resident_state_boundary_rules_20260519.md)
- [WP6 backend profile policy acceptance review](../review/wp6_backend_profile_policy_acceptance_review_20260519.md)

Naming note:

- This is the new post-WP6 `WP7-A` registry materialization line.
- Do not revive the older historical alias where `WP7` meant backend profile
  policy; that policy was accepted and closed as `WP6`.

## 1. Purpose

WP7-A turns the accepted WP6 documentation registries into an
implementation-ready materialization plan. The plan must be machine-checkable
enough for later `RuntimeCapabilities` projection and promotion evidence work,
but it must not make generated data more authoritative than the accepted WP6
policy documents.

The output should let later runtime code and tests ask this narrow question:

```text
Which backend profiles and parity budgets are declared, maintained, candidate,
or diagnostics-only, and which capability claims may they project?
```

## 2. First-Wave Materialization Decision

The first materialized registry should be a hand-maintained seed with schema
validation, generated from WP6 markdown only after the field shape stabilizes.

Decision:

| Option | WP7-A decision | Reason |
|--------|----------------|--------|
| Hand-maintained seed | Choose for first implementation wave. | WP6 has five profile rows and five budget rows, so a reviewed seed is low cost and avoids brittle markdown-table parsing. |
| Generated-from-markdown | Defer to second wave. | The WP6 markdown is normative prose plus tables/YAML examples; immediate generation would make parser quirks look authoritative. |
| Docs-only with parser tests deferred | Reject as the primary plan. | WP7-B/C need stable field names, `maintained_status`, and projection eligibility; docs-only would leave too much implicit. |

The seed path is a proposal until implemented by a later code change:

```text
docs/task/simulation_architecture/generated/wp7_backend_registry_seed_20260519.yaml
```

The seed, once created, is a materialized mirror of WP6 policy. The source of
truth remains the WP6-A profile registry, WP6-B parity budget registry, WP6-C1
resident-state boundary rules, and the WP6 acceptance review.

## 3. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP7-A1 Registry Schema Shape` | Define profile rows, parity budget rows, `maintained_status`, projection eligibility, drift fields, and source-doc provenance. | This cluster and implementation notes; seed file proposal only. | High. |
| `WP7-A2 Seed Strategy` | Use a hand-maintained YAML seed first, with future markdown extraction only after schema and review checks stabilize. | Docs, seed path proposal, future test plan. | High. |
| `WP7-A3 Conservative Projection Matrix` | Map each current WP6 row to maintained baseline, diagnostics-only fact, candidate evidence, or false support. | Docs and future fixture plan. | High. |
| `WP7-A4 Drift Detection Gate` | Define checks for missing fields, stale `parity_budget_ref`, stale `budget_id`, status drift, and accidental promotion. | Doc-check proposal now; architecture test after seed lands. | Medium-high. |

## 4. Profile Schema

Every profile row in the materialized seed must preserve the WP6-A field
contract and add provenance, lifecycle, and projection fields.

| Field | Required value shape | Purpose |
|-------|----------------------|---------|
| `backend_profile_id` | Stable string id from WP6-A. | Primary key for profile rows, diagnostics, reviews, and projection. |
| `profile_class` | `reference`, `accelerated_exact`, `resident_state`, `approximate`, or `diagnostics_only`. | Declared class, not inferred from code availability. |
| `comparison_reference` | Profile id or `self`/`not_maintained`. | Semantic comparison anchor. |
| `host_state_owner` | Text or structured owner list. | Host-owned maintained truth. |
| `backend_state_owner` | Text or structured owner list. | Backend-owned maintained or candidate state. |
| `sync_policy` | `host-owned`, `backend-owned`, `partial-sync`, `observation-only`, `export-only`, or `undeclared_blocked`. | Ownership and synchronization boundary. |
| `state_scope` | List or text preserving WP6-A scope. | State families covered or explicitly excluded. |
| `parity_budget_ref` | Existing WP6-B `budget_id`. | Cross-reference to the parity budget row. |
| `observability_scope` | Maintained or diagnostics-only output surfaces. | Defines what may be exported. |
| `compatibility_rule` | Text preserving WP6-A rule. | Projection and fallback guard. |
| `deprecation_rule` | Text preserving WP6-A rule. | Removal, split, or promotion guard. |
| `validation_gate` | Text preserving WP6-A gate. | Review/test gate before maintained use. |
| `maintained_status` | `maintained_exact_baseline`, `diagnostics_only`, or `unmaintained_candidate`. | Explicit lifecycle state used by projection. |
| `projection_eligibility` | Structured booleans for maintained and diagnostics claims. | Prevents accidental support from helper/probe presence. |
| `source_doc_provenance` | Source doc path, section/heading, row label, accepted date. | Allows drift detection and review traceability. |

Profile rows must not derive `maintained_status` from `profile_class` alone.
For example, `profile_class: accelerated_exact` on
`gpu_exact.unmaintained_candidate` still maps to
`maintained_status: unmaintained_candidate`.

## 5. Parity Budget Schema

Every parity budget row in the materialized seed must preserve the WP6-B field
contract and add provenance, lifecycle, and reverse-link fields.

| Field | Required value shape | Purpose |
|-------|----------------------|---------|
| `budget_id` | Stable string id from WP6-B. | Primary key for parity budget rows. |
| `budget_version` | Integer. | Revision tracking for drift detection. |
| `backend_profile_id` | Existing profile id. | Owner profile; must match one profile row. |
| `profile_class` | Same enum as the owning profile row. | Redundant check against profile drift. |
| `comparison_reference` | Profile id or `self`. | Semantic comparison anchor. |
| `budget_scope` | Structured scope including `maintained_status` and diagnostics-only surfaces. | Declares maintained versus diagnostics coverage. |
| `comparison_domains` | Event order, snapshot versions, numeric state, observation export, diagnostics trace. | Domain-by-domain exactness and tolerance policy. |
| `sync_barriers` | List of barrier ids. | Replay and comparison anchors. |
| `diagnostics_requirements` | List of required structured diagnostics fields. | Explains mismatch evidence. |
| `mismatch_policy` | Structured result actions. | Failure, quarantine, candidate, or report-only behavior. |
| `acceptance_gate` | Text preserving WP6-B gate. | Review/test gate before maintained use. |
| `change_reason` | Short text. | Explains the budget revision. |
| `maintained_status` | Mirrors the budget scope lifecycle value. | Explicit lifecycle value for checks. |
| `source_doc_provenance` | Source doc path, section/heading, code-block label, accepted date. | Allows drift detection and review traceability. |

Budget rows must not be treated as maintained merely because they exist. A
budget is maintained only when its `maintained_status`, `acceptance_gate`, and
owning profile row all allow maintained projection.

## 6. Conservative Projection Matrix

The first materialized registry must project the current WP6 rows exactly as
follows:

| `backend_profile_id` | `parity_budget_ref` / `budget_id` | `maintained_status` | Maintained projection | Diagnostics projection | Blocked claims |
|----------------------|-----------------------------------|---------------------|-----------------------|------------------------|----------------|
| `cpu_exact.reference` | `parity_budget.cpu_exact.reference.v1` | `maintained_exact_baseline` | `projection.cpu_exact_baseline: true`; exact CPU reference may be the maintained comparison anchor. | Structured diagnostics ancestry may be maintained when covered by the reference budget; diagnostics prose remains diagnostics-only. | No accelerated, resident-state, device-observation, or shadow support is implied. |
| `gpu_helpers.diagnostics_only` | `parity_budget.gpu_helpers.diagnostics_only.v1` | `diagnostics_only` | No maintained runtime support. | Helper availability, helper traces, probe exports, and build/runtime facts may be reported as diagnostics-only. | `projection.exact_gpu_supported`, `projection.resident_state_supported`, and `projection.shadow_supported` must remain false. |
| `gpu_exact.unmaintained_candidate` | `parity_budget.gpu_exact.unmaintained_candidate.v1` | `unmaintained_candidate` | No maintained exact GPU support. | Candidate mismatch/performance evidence may be retained as diagnostics-only when labeled. | Exact GPU support, maintained acceleration, and exact parity acceptance remain false. |
| `resident_state.unmaintained_candidate` | `parity_budget.resident_state.unmaintained_candidate.v1` | `unmaintained_candidate` | No maintained resident-state support. | Candidate ownership/sync evidence and unsynced backend-local state may be report-only diagnostics. | `projection.resident_state_supported` and backend-owned truth remain false. |
| `shadow_compare.unmaintained_candidate` | `parity_budget.shadow_compare.unmaintained_candidate.v1` | `unmaintained_candidate` | No maintained shadow execution or shadow fallback support. | Shadow reports, mismatch summaries, and replay evidence may be diagnostics-only. | Shadow output cannot affect committed state, fallback control flow, or maintained support. |

Projection rule: a later adapter may combine materialized registry metadata with
probeable deployment facts, but probes can only explain availability of a
declared maintained profile. Probe availability cannot change
`maintained_status`, satisfy `validation_gate`, satisfy `acceptance_gate`, or
promote a candidate.

## 7. Drift Detection Strategy

WP7-A should introduce drift checks in two phases.

Phase 1, before the seed exists:

1. Keep this cluster and the implementation notes aligned with WP6 field names:
   `backend_profile_id`, `parity_budget_ref`, `validation_gate`, `budget_id`,
   `acceptance_gate`, `projection`, and `maintained_status`.
2. Verify English and Chinese WP7-A docs link to each other and retain the same
   major section order.
3. Do not add runtime capability promotion tests in this phase.

Phase 2, when the hand-maintained seed lands:

1. Schema validation must fail if any profile row is missing a WP6-A field,
   `maintained_status`, `projection_eligibility`, or `source_doc_provenance`.
2. Schema validation must fail if any budget row is missing a WP6-B field,
   `maintained_status`, or `source_doc_provenance`.
3. Cross-reference validation must fail if a `parity_budget_ref` has no
   matching `budget_id`, if a budget `backend_profile_id` has no profile row,
   or if profile/budget `profile_class` values disagree.
4. Conservative projection validation must fail if any row except
   `cpu_exact.reference` projects maintained exact baseline support.
5. Promotion validation must fail if GPU exact, resident-state, or shadow
   support becomes true without a maintained profile row, maintained budget,
   accepted `validation_gate`, accepted `acceptance_gate`, and updated source
   provenance.

If a test is added later, keep it in a narrow architecture-doc target such as
`tests/architecture/test_wp7_registry_materialization_docs.py`. It should check
schema and document constraints only; it must not depend on runtime capability
promotion.

## 8. Non-Goals

- Do not promote any candidate profile.
- Do not implement runtime backend selection.
- Do not make generated registry files override WP6 policy.
- Do not parse every historical draft; only the accepted WP6 line is in scope.
- Do not add a new public capability flag in this cluster.
- Do not edit WP7-B/C/D/E files, runtime C++, GPU helpers, README/index files,
  or accepted WP6 documents.

## 9. Acceptance Gates

This cluster is ready for WP7-B/C when:

1. Every WP6 profile row has a materialization strategy.
2. Every WP6 parity budget row has a materialization strategy.
3. The first-wave decision is explicit: hand-maintained seed first, markdown
   generation deferred.
4. `cpu_exact.reference` is the only maintained exact baseline in the first
   materialized shape.
5. GPU helper, exact GPU candidate, resident-state candidate, and shadow
   candidate rows project diagnostics-only or false maintained support.
6. Drift detection is specific enough to catch missing fields, stale
   `parity_budget_ref`, stale `budget_id`, or accidental capability promotion.
7. English and Chinese WP7-A documents are reciprocally linked and structurally
   aligned.

## 10. Validation Commands

```bash
git diff --check
rg -n "backend_profile_id|parity_budget_ref|validation_gate|budget_id|acceptance_gate|projection|maintained_status" docs/task/simulation_architecture/wp7_registry_materialization*20260519*.md
```
