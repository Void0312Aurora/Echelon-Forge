# WP6-A Normative Dispatch Sheet: Backend Profile Taxonomy

Status: `2026-05-19` completed dispatch sheet for backend profile taxonomy,
with implementation-ready registry output.

Language:

- English canonical: `wp6_backend_profile_taxonomy_cluster_20260519.md`
- Chinese companion: [wp6_backend_profile_taxonomy_cluster_20260519.zh.md](wp6_backend_profile_taxonomy_cluster_20260519.zh.md)

Inputs:

- [WP6 backend profile policy](backend_profile_policy_wp6_20260519.md)
- [WP6-A backend profile registry](wp6_backend_profile_registry_20260519.md)
- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [architecture and performance research followup](../../plan/architecture/architecture_and_performance_research_followup.md)
- [architecture plan review](../review/architecture_plan_review_20260519.md)
- [Temp-02 SCAL architecture vision review](../review/temp-02_review_20260519.md)
- [WP2.5 scheduler semantics freeze](scheduler_semantics_wp25_20260519.md)
- [WP4 facade alignment](facade_alignment_wp4_20260519.md)

Normative language:

- `MUST` marks required WP6 behavior for maintained documentation and later
  implementation.
- `MUST NOT` marks behavior that cannot define maintained backend truth.
- `SHOULD` marks the default rule; deviations need an explicit follow-up task or
  review note.
- `MAY` marks an allowed compatibility or documentation path.

## 1. Purpose

This dispatch sheet turns `WP6-A Backend Profile Taxonomy` into a bounded
documentation task. It freezes the backend profile vocabulary before parity
budgets or resident-state publication are described in detail.

The taxonomy must distinguish the maintained reference path from accelerated,
resident-state, approximate, and diagnostics-only paths. It must also make the
host-owned versus backend-owned boundary explicit so later backend capability
work does not smuggle in a second semantic path.

If older planning notes still call this area `WP7`, treat that as a historical
alias only. The normative line in this cluster is `WP6`.

## 2. Dispatch Deliverables

| Stream | Required output | Owner profile | Reasoning budget |
|--------|-----------------|---------------|------------------|
| `WP6-A1 Profile Catalog` | Canonical table of backend profile classes, ids, maintained status, comparison anchor, and disallowed claims. | Backend taxonomy worker. | High. |
| `WP6-A2 Ownership And Sync Classification` | Host-owned, backend-owned, partial-sync, observation-only, and export-only rules with one-way / two-way constraints. | Backend taxonomy worker. | High. |
| `WP6-A3 Capability Surface Boundary` | Rule set for `RuntimeCapabilities`, `BackendCapabilityFacade`, and every backend capability query entry point. | Integration-minded taxonomy worker. | Medium-high. |
| `WP6-A4 Naming And Cross-Reference Sync` | English/Chinese alignment plus compatibility note for historical WP7 references. | Integration owner. | Medium. |

## 3. Backend Profile Classes

| Profile class | Default WP6 decision | Maintained status | State ownership | Sync rule | Parity rule | Notes |
|---------------|----------------------|-------------------|-----------------|-----------|-------------|------|
| `reference` | Canonical baseline. | Maintained. | Host-owned state. | Host-owned only. | Exact. | CPU exact path. |
| `accelerated_exact` | Same semantics, faster implementation. | Maintained only when exactness is preserved. | Host-owned or hybrid, but host truth must remain explicit. | Explicit host sync and committed-state visibility. | Exact event order and exact committed state. | CUDA or other accelerated helper attached through contracts. |
| `resident_state` | Backend keeps some operational state resident. | Gated; not maintained until sync and parity are explicit. | Backend-owned partial state with explicit host visibility rules. | Explicit partial sync or observation-only export. | Declared parity budget required. | Device-resident observation or physics helper. |
| `approximate` | Intentional approximation. | Experimental by default. | Backend-owned or hybrid. | Explicit and bounded. | Tolerance-based only. | Surrogate or fidelity-reduced backend. |
| `diagnostics_only` | Inspection or debug path. | Never maintained truth. | As declared by helper. | Export-only. | No maintained parity claim. | Trace export or probe helper. |

### 3.1 Profile Class Invariants

The five profile classes are not performance tiers. They are semantic
contracts:

1. `reference` is the only baseline used as the maintained comparison anchor.
   It defines the host-owned truth line and is the default fallback when a
   later doc needs a stable semantic reference.
2. `accelerated_exact` may change execution strategy, scheduling, or hardware
   placement, but it MUST preserve the declared event order and committed-state
   meaning of the reference path.
3. `resident_state` may keep backend-local state only when the host-visible
   reconstruction rule is explicit. If the host cannot recover or inspect the
   declared state scope, the path is not maintained.
4. `approximate` may deviate only inside an explicit tolerance envelope. It
   MUST state that envelope in its parity budget and MUST NOT be described as
   exact through wording, alias, or compatibility shortcut.
5. `diagnostics_only` may export traces, metrics, or snapshots, but it MUST NOT
   become a maintained comparison target, a hidden runtime truth, or a fallback
   control path.

### 3.2 Ownership And Sync Boundary Rules

The ownership label and the sync policy are separate decisions:

| Boundary type | Meaning | Allowed truth holder | Required sync shape | Forbidden claim |
|---------------|---------|-----------------------|---------------------|-----------------|
| `host-owned` | The host remains the authoritative source of maintained truth. | Host. | Explicit host sync only when declared. | Backend-local state is authoritative by default. |
| `backend-owned` | The backend holds the authoritative shard for the declared scope. | Backend. | Declared export, partial sync, or observation path. | Host silently owns the same shard. |
| `partial-sync` | Only a bounded subset of the backend state is synchronized back to the host. | Mixed, with a named authoritative side. | One declared subset and one declared cadence / trigger. | Full-state equivalence without an explicit contract. |
| `observation-only` | The backend exposes measurements or traces without participating in maintained control flow. | Helper or backend, as declared. | Read-only visibility only. | The observed data is maintained state. |
| `export-only` | The backend emits an artifact for inspection, replay, or offline analysis only. | Helper or backend, as declared. | One-way export only. | The export can be consumed as runtime truth. |

For this cluster, a backend path is only maintained when the ownership label,
sync shape, and parity budget can all be named together. If one of those parts
is missing, the path belongs in later implementation work, not in the taxonomy.

## 4. Required Taxonomy Metadata

Every maintained backend profile entry MUST declare:

| Field | Rule |
|-------|------|
| `backend_profile_id` | Stable id used by docs, review, replay, and diagnostics. |
| `profile_class` | One of `reference`, `accelerated_exact`, `resident_state`, `approximate`, `diagnostics_only`. |
| `comparison_reference` | The backend or path used as the semantic comparison anchor. |
| `host_state_owner` | Which state shards or outputs remain host-owned. |
| `backend_state_owner` | Which state shards or outputs may live on the backend. |
| `sync_policy` | Host-owned, backend-owned, partial sync, observation-only sync, or explicit export. |
| `state_scope` | The state family covered by the profile. |
| `parity_budget_ref` | The attached parity budget or comparison budget. |
| `observability_scope` | What may be exported as maintained output. |
| `compatibility_rule` | How legacy callers or diagnostics-only helpers behave. |
| `deprecation_rule` | When the profile stops being maintained or must be narrowed. |
| `validation_gate` | The review or test gate that proves the profile is safe. |

The implementation-ready registry seed for these fields is
[WP6-A backend profile registry](wp6_backend_profile_registry_20260519.md).
That registry is the WP6-A metadata source for later capability projection;
`RuntimeCapabilities` remains a projection of declared registry/profile
metadata plus probeable deployment facts, not the source of truth.

## 5. Capability Surface Boundary

WP6-A MUST state:

1. `RuntimeCapabilities` is a capability projection, not a profile class and
   not a planner.
2. `RuntimeCapabilities` MAY mirror declared backend profile metadata and
   immutable deployment facts, but it MUST NOT invent capability semantics that
   the profile does not declare.
3. `BackendCapabilityFacade` is the supported policy surface for asking
   capability questions. It MAY aggregate declared profile data, but it MUST
   not bypass taxonomy rules or consult hidden implementation truth.
4. Any capability flag that changes maintained meaning MUST be declared on the
   profile first. If the meaning cannot be expressed in the profile metadata,
   the rule belongs in later implementation work, not in the facade.
5. A diagnostics-only helper MAY contribute observability data, but it MUST NOT
   become the maintained capability truth or alter host/backend ownership.
6. If a capability query needs hidden resident state, private caches, or
   implementation-only branch logic to answer, then the query is not a
   capability query yet.

## 6. Non-Goals

- Implementing backend selection logic.
- Rewriting GPU or resident-state code.
- Changing scheduler semantics.
- Promoting `RuntimeCapabilities` into a new semantic path.
- Treating performance tier names as profile classes.
- Collapsing compatibility helpers into maintained truth.

## 7. Exit Criteria

This cluster exits when:

1. The profile catalog distinguishes the five backend profile classes and gives
   each one a non-overlapping definition.
2. Each maintained class names its comparison anchor, ownership, sync policy,
   and disallowed claim.
3. The ownership and sync matrix explicitly covers `host-owned`,
   `backend-owned`, `partial-sync`, `observation-only`, and `export-only`.
4. `RuntimeCapabilities` and `BackendCapabilityFacade` are positioned as
   policy surfaces, not hidden runtime truth.
5. The English and Chinese companions contain the same section order, the same
   profile class list, and reciprocal links.
6. The historical WP7 naming note is explicit enough that later docs do not
   drift, but it does not reopen the normative naming decision.

## 8. Validation Commands

```bash
git diff --check
rg -n "reference|accelerated_exact|resident_state|approximate|diagnostics_only|host-owned|backend-owned|partial-sync|observation-only|export-only|RuntimeCapabilities|BackendCapabilityFacade" docs/task/simulation_architecture/wp6_backend_profile_taxonomy_cluster_20260519*.md
rg -n "wp6_backend_profile_taxonomy_cluster_20260519\\.zh\\.md" docs/task/simulation_architecture/wp6_backend_profile_taxonomy_cluster_20260519.md
rg -n "wp6_backend_profile_taxonomy_cluster_20260519\\.md" docs/task/simulation_architecture/wp6_backend_profile_taxonomy_cluster_20260519.zh.md
```
