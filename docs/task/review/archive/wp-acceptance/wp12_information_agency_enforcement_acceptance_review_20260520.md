# WP12 Information And Agency Enforcement Acceptance Review

Status: `2026-05-20` accepted / implementation mergeable.

Language:

- English canonical: `wp12_information_agency_enforcement_acceptance_review_20260520.md`
- Chinese companion:
  [wp12_information_agency_enforcement_acceptance_review_20260520.zh.md](wp12_information_agency_enforcement_acceptance_review_20260520.zh.md)

Inputs:

- [WP12 Information And Agency Enforcement](../simulation_architecture/wp12_information_agency_enforcement/information_agency_enforcement_wp12_20260520.md)
- [WP12-A Law 14 Read-Side Enforcement](../simulation_architecture/wp12_information_agency_enforcement/wp12_law14_read_side_enforcement_cluster_20260520.md)
- [WP12-B Agency Role Authority Boundary](../simulation_architecture/wp12_information_agency_enforcement/wp12_agency_role_authority_cluster_20260520.md)
- [WP12-C Information Transformation Surface](../simulation_architecture/wp12_information_agency_enforcement/wp12_information_transformation_surface_cluster_20260520.md)
- [WP12-D Intent Injection Authority Guard](../simulation_architecture/wp12_information_agency_enforcement/wp12_intent_injection_authority_guard_cluster_20260520.md)
- [WP12-E Integration And Acceptance Handoff](../simulation_architecture/wp12_information_agency_enforcement/wp12_integration_acceptance_cluster_20260520.md)
- [WP11 acceptance review](wp11_facade_vertical_slice_provenance_acceptance_review_20260520.md)

## 1. Verdict

WP12 is accepted as the Phase 3 information and agency enforcement increment.
It turns the WP11 provenance/pre-gate vocabulary into focused, test-backed
read-side, authority, transformation, and intent-injection guards.

Scope caveats are intentional:

- Law 14 enforcement is focused on selected maintained consumer and
  belief/intent fixtures, not repository-wide static coverage.
- `AgentRole` authority validation is the first maintained authority slice, not
  full Agency Graph runtime dispatch.
- Information transformation evidence is a contract/helper surface for the
  selected slice; it does not migrate every sensor, track, or data-link
  producer.
- Intent injection enforcement is contract-level / architecture-level guard
  evidence. It is not yet wired into `run_wp10_window()` request admission.
- No backend/fidelity, capability composition, counterfactual/worldline, or
  policy/control/physics cadence claim is made.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP12-A Law 14 Read-Side Enforcement` | pass | `python/rl/runtime/agent_shim.py`, `tests/runtime/test_agent_shim.py`, and `tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py` enforce a focused maintained read-side allowlist for provenance-labeled `ObservationPacket` / `DecisionBelief` inputs while keeping diagnostics-only truth/raw paths explicit. |
| `WP12-B Agency Role Authority Boundary` | pass | `src/runtime/contracts/policy_contracts.h`, `src/interfaces/python/bindings_runtime.cpp`, `tests/runtime/mission/test_policy_contract_shape.py`, `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`, and `tests/architecture/policy_execution/test_agent_role_authority.py` add fail-closed `AgentRole` authority/source/interface validation and Python-visible authorization helpers. |
| `WP12-C Information Transformation Surface` | pass | `src/runtime/contracts/information_transform_contracts.h` and `tests/architecture/policy_execution/test_information_transformation_surface.py` add canonical transformation vocabulary, evidence structs, validators, diagnostics-only shortcut rules, and negative tests for invalid belief-to-intent provenance. |
| `WP12-D Intent Injection Authority Guard` | pass | `src/runtime/contracts/information_transform_contracts.h` and `tests/architecture/policy_execution/test_intent_injection_authority_guard.py` compose A/B/C into `authorize_maintained_decision_belief_action_intent_injection()` with authority, transformation, ancestry, timing, merge-policy, and no-raw-facade-bypass checks. |
| `WP12-E Integration And Acceptance Handoff` | pass | This review records A-D status, validation commands, residuals, route/index updates, and the closure-lane scope boundary. |

## 3. Validation Commands

Passed:

```bash
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/policy_execution/test_intent_injection_authority_guard.py tests/architecture/policy_execution/test_agent_role_authority.py tests/architecture/policy_execution/test_information_transformation_surface.py tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py tests/runtime/test_agent_shim.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/mission/test_policy_contract_shape.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_bindings_policy_surface.py
git diff --check
```

Observed outcomes before this review:

- WP12 architecture guard set: `25 passed`.
- Runtime facade/window plus agent shim set: `20 passed`.
- Mission/bindings contract set: `31 passed`.
- `git diff --check`: passed.

Final closure validation should additionally run:

```bash
cmake --build build-workshop -j4
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP12
```

## 4. Integration Notes

- WP12-A keeps diagnostics-only truth/raw runtime paths explicit and does not add
  a global raw ECS ban.
- WP12-B currently authorizes the first maintained authority vocabulary:
  `platform_control -> PilotActionAssignmentCompat / pilot_action`,
  `mission_command -> CommandChainAssignmentCompat / mission_command`, and
  `formation_coordination -> CommandChainAssignmentCompat /
  coordination_intent`.
- WP12-C's transformation surface is intentionally independent and does not
  require broad DTO/binding expansion.
- WP12-D composes the accepted A/B/C helpers rather than adding a second
  authority or injection path.
- `RuntimeFacade` did not gain a new maintained raw injection API.

## 5. Residuals And Next Plan

Residuals intentionally carried forward:

- Wire `authorize_maintained_decision_belief_action_intent_injection()` into the
  maintained facade-compatible request admission seam before claiming runtime
  admission enforcement.
- Extend the combination guard to `CoordinationIntentPacket` when a concrete
  maintained coordination-injection slice is opened.
- Broaden Law 14 coverage beyond selected Python/architecture fixtures only
  after a wider static or runtime guard plan exists.
- Keep full Agency Graph runtime dispatch, role-based access control over every
  producer, and decision-model dispatch as later work.
- Backend/fidelity expansion remains the next post-WP9 route phase only after
  this information/agency evidence boundary is accepted.

Recommended next WP: open Phase 4 backend/fidelity expansion, using the WP10
causal seam, WP11 provenance, and WP12 enforcement guards as the evidence
boundary. Do not promote exact GPU, resident-state, shadow, or multi-fidelity
capability without query/reject/evidence gates.
