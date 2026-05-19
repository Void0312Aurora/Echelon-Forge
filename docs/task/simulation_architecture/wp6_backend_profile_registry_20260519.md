# WP6-A Backend Profile Registry

Status: `2026-05-19` implementation-ready registry seed for backend profile
metadata. This file is a documentation registry, not generated runtime code.

Language:

- English canonical: `wp6_backend_profile_registry_20260519.md`
- Chinese companion: [wp6_backend_profile_registry_20260519.zh.md](wp6_backend_profile_registry_20260519.zh.md)

Inputs:

- [WP6 backend profile policy](backend_profile_policy_wp6_20260519.md)
- [WP6-A backend profile taxonomy cluster](wp6_backend_profile_taxonomy_cluster_20260519.md)
- [WP6-B parity budget cluster](wp6_parity_budget_cluster_20260519.md)
- [WP6-C + WP6-D integration and index sync](wp6_integration_and_index_sync_20260519.md)
- [WP2.5 scheduler semantics freeze](scheduler_semantics_wp25_20260519.md)
- [WP5 validation harness](validation_harness_wp5_20260519.md)

Normative language:

- `MUST` marks required metadata for maintained backend profiles.
- `MUST NOT` marks claims that cannot be made from this registry seed.
- `SHOULD` marks the default implementation-preparation rule.
- `MAY` marks an allowed diagnostics, compatibility, or future promotion path.

## 1. Purpose

This registry turns the WP6-A taxonomy into concrete profile records that later
implementation work can project into capability surfaces. It is intentionally
conservative: only `cpu_exact.reference` is a maintained reference record in
this seed.

`RuntimeCapabilities` is a projection, not the source of truth. It MAY mirror
declared backend profile registry metadata plus probeable deployment facts, but
it MUST NOT invent exact GPU, resident-state, or shadow-style support. The
backend profile registry is one metadata source for future capability
projection; runtime probes can explain availability, but they cannot promote an
undeclared profile into maintained truth.

## 2. Field Contract

Every maintained backend profile entry MUST declare the fields below. Candidate
and diagnostics-only rows use the same fields so their missing gates are visible
instead of being inferred by `RuntimeCapabilities` or helper code.

| Field | Registry rule |
|-------|---------------|
| `backend_profile_id` | Stable id used by docs, review, replay, diagnostics, and later capability projection. |
| `profile_class` | One of `reference`, `accelerated_exact`, `resident_state`, `approximate`, `diagnostics_only`. |
| `comparison_reference` | Semantic comparison anchor; use `not_maintained` only when no maintained comparison is claimed. |
| `host_state_owner` | Host-owned state shards or outputs for the profile's declared scope. |
| `backend_state_owner` | Backend-owned state shards or outputs for the profile's declared scope. |
| `sync_policy` | Host-owned, backend-owned, partial-sync, observation-only, export-only, or `undeclared_blocked`. |
| `state_scope` | State families covered by the profile; candidates must say what is not yet maintained. |
| `parity_budget_ref` | Profile-owned parity budget reference, or the missing budget that blocks promotion. |
| `observability_scope` | Outputs that may be exported as maintained or diagnostics-only evidence. |
| `compatibility_rule` | Legacy/helper behavior and capability-projection rule. |
| `deprecation_rule` | When the row must be removed, narrowed, renamed, or promoted by review. |
| `validation_gate` | Review or test gate required before maintained use. |

## 3. Initial Registry

| `backend_profile_id` | `profile_class` | `comparison_reference` | `host_state_owner` | `backend_state_owner` | `sync_policy` | `state_scope` | `parity_budget_ref` | `observability_scope` | `compatibility_rule` | `deprecation_rule` | `validation_gate` |
|----------------------|-----------------|------------------------|--------------------|-----------------------|---------------|---------------|---------------------|-----------------------|----------------------|--------------------|-------------------|
| `cpu_exact.reference` | `reference` | `self` / maintained CPU exact path | Host owns committed scheduler state, world state, observation envelopes, and diagnostics ancestry. | None for maintained truth. Backend helpers may not own state under this profile. | `host-owned` only; no backend-owned truth. | Maintained CPU exact execution, event order, snapshots, observations, and diagnostics ancestry exposed through facade contracts. | `parity_budget.cpu_exact.reference.v1`. | Maintained facade outputs and structured diagnostics ancestry; diagnostics prose remains diagnostics-only. | Default fallback and comparison anchor for other profiles. `RuntimeCapabilities` may project this as the maintained baseline, not as accelerated support. | Deprecate only through a replacement reference profile that preserves WP2.5 event order, snapshot identity, and WP5 validation obligations. | WP6-A registry review plus WP6-B reference budget acceptance; no GPU/resident/shadow promotion implied. |
| `gpu_helpers.diagnostics_only` | `diagnostics_only` | `cpu_exact.reference` for explanation only; no maintained parity claim. | Host remains owner of all maintained truth. | GPU/helper-local diagnostics buffers or probes only when labeled diagnostics-only. | `export-only`; one-way diagnostics export. | GPU availability checks, helper traces, probe outputs, or debug artifacts that do not affect committed state. | `parity_budget.gpu_helpers.diagnostics_only.v1`; diagnostics-only, not maintained parity. | Diagnostics traces, probe summaries, build/runtime availability facts; never maintained state. | `RuntimeCapabilities` may project probeable deployment facts from declared probes, but MUST keep exact GPU, resident-state, and shadow support false unless another maintained profile declares them. | Remove or narrow if a helper starts influencing committed state; promote only by creating a separate maintained profile with ownership, sync, parity, and validation gates. | Diagnostics labeling review; tests may assert report-only behavior but cannot accept it as maintained parity. |
| `gpu_exact.unmaintained_candidate` | `accelerated_exact` | `cpu_exact.reference` if promoted later. | Host ownership of committed state is assumed until a maintained profile states otherwise. | No backend-owned maintained state declared; GPU execution internals are not authoritative. | `undeclared_blocked`; exact sync and committed-state visibility are not yet declared. | Placeholder for a possible exact GPU world-step or accelerated exact path; no maintained exact GPU support is claimed. | `parity_budget.gpu_exact.unmaintained_candidate.v1`; candidate budget, not acceptance. | Candidate diagnostics only, such as mismatch evidence or performance notes, if explicitly labeled. | `RuntimeCapabilities` MUST NOT project maintained exact GPU support from this row. It may only expose separate probeable deployment facts through diagnostics or availability fields. | Delete if no exact promotion plan remains; replace with a maintained `accelerated_exact` profile only after WP6-B/C gates pass. | Blocked until exact event order, snapshot identity, host/backend ownership, sync barriers, parity budget, and WP5 replay/validation gates are accepted. |
| `resident_state.unmaintained_candidate` | `resident_state` | `cpu_exact.reference` or another maintained host-visible reference if promoted later. | Host remains owner of maintained committed state until a profile declares host-visible reconstruction or export rules. | Candidate backend-resident operational shards are not maintained truth. | `undeclared_blocked`; partial-sync, observation-only, or export-only policy must be declared before use. | Placeholder for backend-resident observation, physics, or operational state; no maintained resident-state support is claimed. | `parity_budget.resident_state.unmaintained_candidate.v1`; candidate budget, not acceptance. | Candidate diagnostics only; unsynced backend-local state must stay outside maintained parity. | `RuntimeCapabilities` MUST keep resident-state capability false from this row. Probeable backend presence does not imply resident-state ownership. | Remove or split if the resident scope cannot be reconstructed, exported, or synchronized under WP6-C rules; promote only through a maintained registry revision. | Blocked until ownership split, sync cadence/trigger, sync barriers, host-visible reconstruction/export, parity budget, and validation gates are accepted. |
| `shadow_compare.unmaintained_candidate` | `diagnostics_only` | `cpu_exact.reference` for comparison reports only; no shadow execution support is maintained. | Host reference path owns committed state. | Shadow helper outputs are diagnostics-only and cannot own committed state. | `export-only` unless a later maintained profile explicitly declares a non-mutating shadow contract. | Placeholder for shadow comparison reports or offline A/B evidence; no maintained shadow support is claimed. | `parity_budget.shadow_compare.unmaintained_candidate.v1`; diagnostics/candidate budget, not maintained truth. | Comparison reports, mismatch summaries, and replay evidence labeled diagnostics-only. | `RuntimeCapabilities` MUST NOT project shadow-style capability from this row. Shadow output cannot affect committed state or fallback control flow. | Remove if reports are not used; promote only by defining what is shadowed, whether it can affect committed state, and how diagnostics are separated from maintained truth. | Blocked until shadow scope, non-interference rule, diagnostics separation, parity budget if maintained, and validation review are accepted. |

## 4. Projection Rules

1. `RuntimeCapabilities` MUST consume this registry as declared metadata, not as
   an inference target. A row can be projected only according to its
   `compatibility_rule`, `sync_policy`, and `validation_gate`.
2. Probeable deployment facts MAY be combined with registry metadata to explain
   availability, but they MUST NOT override `profile_class`,
   `parity_budget_ref`, or `validation_gate`.
3. Unmaintained candidate rows MUST project as unavailable or false for
   maintained exact GPU, resident-state, and shadow-style capabilities.
4. Diagnostics-only rows MAY project observability or report-only affordances
   when the output stays outside maintained state.
5. Any future maintained accelerated, resident, approximate, or shadow-like
   profile MUST be added here before a capability surface claims it.

## 5. Promotion Gates

Promotion from placeholder to maintained profile requires a registry revision
that names all of the following:

1. The stable `backend_profile_id` and `profile_class`.
2. The maintained `comparison_reference`.
3. The exact `host_state_owner` and `backend_state_owner` split.
4. The `sync_policy`, including cadence, trigger, barriers, or export direction.
5. The `state_scope` and `observability_scope`.
6. The profile-owned `parity_budget_ref`.
7. The `compatibility_rule`, `deprecation_rule`, and `validation_gate`.

Without those fields, capability projection remains false for maintained
support even if code, probes, or helpers exist.

## 6. Non-Goals

- Generating runtime registry files.
- Editing runtime code, bindings, tests, README files, or index files.
- Claiming maintained exact GPU execution.
- Claiming maintained resident-state ownership.
- Claiming maintained shadow execution or shadow fallback.
- Reopening WP6-B parity rules, WP6-C resident-state rules, or WP6-D
  publication handoff.

## 7. Validation Commands

```bash
git diff --check
rg -n "backend_profile_id|profile_class|comparison_reference|host_state_owner|backend_state_owner|sync_policy|state_scope|parity_budget_ref|observability_scope|compatibility_rule|deprecation_rule|validation_gate" docs/task/simulation_architecture/wp6_backend_profile_registry_20260519*.md
rg -n "cpu_exact\\.reference|gpu_helpers\\.diagnostics_only|gpu_exact\\.unmaintained_candidate|resident_state\\.unmaintained_candidate|shadow_compare\\.unmaintained_candidate|RuntimeCapabilities" docs/task/simulation_architecture/wp6_backend_profile_registry_20260519*.md
rg -n "wp6_backend_profile_registry_20260519\\.zh\\.md" docs/task/simulation_architecture/wp6_backend_profile_registry_20260519.md
rg -n "wp6_backend_profile_registry_20260519\\.md" docs/task/simulation_architecture/wp6_backend_profile_registry_20260519.zh.md
```
