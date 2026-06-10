# WP6-C + WP6-D Dispatch Sheet: Resident-State Boundary Rules And Integration Handoff

Status: `2026-05-19` implementation-aligned dispatch sheet and completed
publication handoff for resident-state boundary rules, backend capability
projection policy, and WP6 index sync.

Language:

- English canonical: `wp6_integration_and_index_sync_20260519.md`
- Chinese companion: [wp6_integration_and_index_sync_20260519.zh.md](wp6_integration_and_index_sync_20260519.zh.md)

Inputs:

- [WP6 backend profile policy](backend_profile_policy_wp6_20260519.md)
- [WP6-A backend profile taxonomy cluster](wp6_backend_profile_taxonomy_cluster_20260519.md)
- [WP6-A backend profile registry](wp6_backend_profile_registry_20260519.md)
- [WP6-B parity budget cluster](wp6_parity_budget_cluster_20260519.md)
- [WP6-B parity budget registry](wp6_parity_budget_registry_20260519.md)
- [WP6-C1 resident-state boundary rules](wp6_resident_state_boundary_rules_20260519.md)
- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [architecture and performance research followup](../../plan/architecture/architecture_and_performance_research_followup.md)
- [architecture plan review](../review/architecture_plan_review_20260519.md)
- [Temp-02 SCAL architecture vision review](../review/temp-02_review_20260519.md)
- [WP4 facade alignment](facade_alignment_wp4_20260519.md)
- [WP5 validation harness](validation_harness_wp5_20260519.md)

Normative language:

- `MUST` marks required WP6 behavior for maintained documentation and later
  publication.
- `MUST NOT` marks behavior that cannot define maintained backend truth.
- `SHOULD` marks the default rule; deviations need an explicit follow-up task or
  review note.
- `MAY` marks an allowed compatibility or documentation path.

## 1. Purpose

This dispatch sheet turns the remaining WP6 concerns into a serial integration
package. It does not redefine taxonomy or parity. It resolves how resident-state
profiles, backend capability projection, and publication handoff fit together.

The prose here is intentionally implementation-facing and release-note-ready:
it should guide the first capability projection wave without claiming support
for exact GPU execution, resident-state truth, or shadow execution before a
maintained profile declares those capabilities.

This sheet is also the place where the WP6 naming normalization is recorded:
older notes that call backend profiles `WP7` are treated as historical naming,
while `WP6` is the active task identifier in this workline.

## 2. Dispatch Deliverables

| Stream | Required output | Owner profile | Reasoning budget |
|--------|-----------------|---------------|------------------|
| `WP6-C1 Resident-State Boundary Rules` | Host-owned, backend-owned, partial-sync, observation-only, and export-only rules. | Integration worker. | High. |
| `WP6-C2 Backend Capability Projection Policy` | Policy for `RuntimeCapabilities`, `BackendCapabilityFacade`, and any backend capability query. | Integration worker. | High. |
| `WP6-D1 Naming And Cross-Reference Sync` | Cross-document alignment for WP6 references and the older WP7 wording. | Integration worker. | Medium. |
| `WP6-D2 Publication Handoff` | Handoff text for future README/review index updates once the WP6 sheets stabilize. | Integration worker. | Medium. |

## 2.1 Completed WP6-C/WP6-D Outputs

The completed publication line cites these implementation-ready outputs:

1. [WP6-A backend profile registry](wp6_backend_profile_registry_20260519.md)
   as the profile metadata source.
2. [WP6-B parity budget registry](wp6_parity_budget_registry_20260519.md) as
   the profile-owned comparison budget source.
3. [WP6-C1 resident-state boundary rules](wp6_resident_state_boundary_rules_20260519.md)
   as the resident-state ownership and sync gate.
4. Capability-projection guards in
   [runtime facade layering tests](../../../tests/architecture/runtime_facade),
   [runtime facade tests](../../../tests/runtime/facade/test_runtime_facade.py),
   and [GPU runtime binding tests](../../../tests/test_gpu_runtime_bindings.py).
5. [WP6 acceptance review](../review/wp6_backend_profile_policy_acceptance_review_20260519.md)
   as the final WP6 publication record.

## 3. Resident-State Boundary Rules

WP6-C MUST state:

1. Device-resident state MAY be maintained only behind declared host/backend
   ownership and sync policy.
2. A resident-state profile MUST say which shards are host-owned and which are
   backend-owned.
3. A resident-state profile MUST say whether the maintained output is
   observation-only, export-only, or committed state.
4. A resident-state profile MUST say which parts of the backend-local state are
   outside maintained parity and therefore diagnostics-only.
5. Backend thread completion order MUST NOT become maintained truth.

## 4. Backend Capability Exposure Policy

WP6-C MUST also state:

1. `RuntimeCapabilities` is a capability projection, not a backend profile
   class, planner, or authority source.
2. `RuntimeCapabilities` MAY mirror declared profile metadata and probeable
   deployment facts, but it MUST NOT invent capability semantics that the
   profile does not declare.
3. `BackendCapabilityFacade` is a policy surface, not hidden implementation
   truth.
4. Any capability query that cannot be explained from the backend profile
   metadata belongs in a later implementation package.
5. Exact GPU world-step remains false until parity, ownership, sync rules, and
   validation gates are declared by a maintained profile.
6. Resident-state capability remains false until a maintained profile declares
   backend-owned state scope, host-visible reconstruction or export rules, sync
   barriers, and parity budget.
7. Shadow-style capability remains false unless a maintained profile explicitly
   declares what is shadowed, whether it affects committed state, and how its
   diagnostics are separated from maintained truth.
8. Probeable deployment facts MAY include compiled backend presence, runtime
   availability, device enumeration, or configured feature gates; these facts
   can explain why a declared profile is unavailable, but they cannot promote a
   helper into maintained exact/resident/shadow support.

## 5. Integration And Publication Rules

WP6-D MUST treat the following as publication constraints:

1. WP6-A taxonomy output and WP6-B parity output are the only sources for the
   backend profile vocabulary used in WP6-C and WP6-D.
2. The main WP6 sheet remains the top-level entry for backend profile policy.
3. README and review index updates cite the registry, boundary,
   capability-guard, and acceptance-review outputs rather than draft fragments.
4. Older references to WP7 in backend profile context MUST be normalized in the
   active WP6 line before publication, and they MUST remain historical naming
   only after normalization.
5. Any future runtime code change that depends on these docs must cite the final
   published WP6 line rather than draft note fragments.

## 6. Non-Goals

- Editing `docs/task/simulation_architecture/README.md` or review indexes before
  the WP6-A/B/C outputs stabilize.
- Implementing resident-state runtime code.
- Implementing backend capability queries.
- Claiming exact GPU, resident-state, or shadow support before maintained
  profile metadata declares it.
- Reopening scheduler semantics or facade semantics.
- Treating the integration sheet as a substitute for runtime parity work.

## 7. Exit Criteria

This sheet exits when:

1. Resident-state boundary rules are explicit and do not conflict with the
   taxonomy sheet.
2. Capability exposure is described as a policy surface, not a hidden runtime
   assumption.
3. `RuntimeCapabilities` is aligned as a projection of declared/profile
   metadata plus probeable deployment facts, with exact GPU, resident-state, and
   shadow-style support false unless a maintained profile explicitly declares
   otherwise.
4. The WP6/WP7 naming normalization is spelled out clearly.
5. The publication handoff updates README and review indices without rewriting
   the WP6 substance or reintroducing `WP7` as a live line.
6. The Chinese companion is aligned enough for later publication.

## 8. Publication Handoff Result

WP6-D publishes the following stable line:

1. `cpu_exact.reference` is the only maintained exact baseline in the initial
   profile registry.
2. GPU helpers, exact GPU candidates, resident-state candidates, and
   shadow-compare candidates remain diagnostics-only or unmaintained until a
   maintained profile revision declares ownership, sync, parity budget, and
   validation gates.
3. `RuntimeCapabilities` projects only maintained facade/core capabilities
   today: batch runtime, compiled episode controller, and compiled execution
   step. Exact GPU, device observation, resident-state, and shadow support
   remain false.
4. Backend helper/probe availability may explain diagnostics or deployment
   facts, but it cannot promote a profile into maintained truth.
5. Active docs use `WP6` as the normative backend profile line; historical
   `WP7` wording remains historical only.

## 9. Validation Commands

```bash
git diff --check
rg -n "WP6|WP7|resident-state|BackendCapability|RuntimeCapabilities|shadow|index sync" docs/task/simulation_architecture docs/plan/architecture docs/task/review
```
