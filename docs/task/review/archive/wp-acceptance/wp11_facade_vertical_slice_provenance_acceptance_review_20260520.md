# WP11 Facade Vertical Slice And Provenance Acceptance Review

Status: `2026-05-20` accepted / implementation mergeable.

Language:

- English canonical: `wp11_facade_vertical_slice_provenance_acceptance_review_20260520.md`
- Chinese companion:
  [wp11_facade_vertical_slice_provenance_acceptance_review_20260520.zh.md](wp11_facade_vertical_slice_provenance_acceptance_review_20260520.zh.md)

Inputs:

- [WP11 Facade Vertical Slice And Provenance](../simulation_architecture/wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.md)
- [WP11-A ActionHoldPolicy Contract](../simulation_architecture/wp11_facade_vertical_slice_provenance/wp11_action_hold_policy_cluster_20260520.md)
- [WP11-B Information Provenance Labels](../simulation_architecture/wp11_facade_vertical_slice_provenance/wp11_information_provenance_labels_cluster_20260520.md)
- [WP11-C Facade Vertical Slice Proof](../simulation_architecture/wp11_facade_vertical_slice_provenance/wp11_facade_vertical_slice_proof_cluster_20260520.md)
- [WP11-D Consumer Boundary Pre-Gates](../simulation_architecture/wp11_facade_vertical_slice_provenance/wp11_consumer_boundary_pregates_cluster_20260520.md)
- [WP11-E Integration And Acceptance Handoff](../simulation_architecture/wp11_facade_vertical_slice_provenance/wp11_integration_acceptance_cluster_20260520.md)
- [WP10 acceptance review](wp10_causal_runtime_foundation_acceptance_review_20260520.md)

## 1. Verdict

WP11 is accepted as the Phase 2 facade vertical slice and provenance increment.
It adds the `ActionHoldPolicy` contract, stable information-state provenance
labels, a WP10-seam facade/binding proof, and focused consumer boundary
pre-gates.

Scope caveats are intentional:

- `ActionHoldPolicy` is contract-visible and binding-visible, but does not
  implement runtime policy/control/physics cadence.
- The consumer boundary work is a `GAP-5` precursor, not complete Law 14
  read-side enforcement.
- The vertical proof does not replace the scheduler, broaden the facade, or add
  a new raw runtime escape hatch.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP11-A ActionHoldPolicy Contract` | pass | `src/runtime/contracts/policy_contracts.h` defines `ActionHoldPolicy`; `src/interfaces/python/bindings_runtime.cpp` exposes `ef_py.ActionHoldPolicy`; `tests/runtime/mission/test_policy_contract_shape.py`, `tests/runtime/bindings/test_bindings_policy_surface.py`, and `tests/architecture/policy_execution/test_action_hold_policy_contract.py` verify field shape, conservative defaults, and fail-closed normalization. |
| `WP11-B Information Provenance Labels` | pass | `InformationStateSource`, canonical information-state/status vocabulary, packet provenance fields, and `DecisionBelief` validators are visible in contracts, facade packet types, runtime exports, bindings, and focused tests. |
| `WP11-C Facade Vertical Slice Proof` | pass | Engagement/facade/binding tests prove `p7.fire_control_launch.v1`, `p9.effects_damage.v1`, and `p10.observation_export.v1` node evidence with export barrier, snapshot/source-time metadata, diagnostics ancestry, and maintained/diagnostics provenance labels. |
| `WP11-D Consumer Boundary Pre-Gates` | pass | `python/rl/runtime/agent_shim.py`, `tests/runtime/test_agent_shim.py`, and `tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py` reject unlabeled maintained consumer fixtures while preserving explicit diagnostics-only truth/raw-ECS fixtures. |
| `WP11-E Integration And Acceptance Handoff` | pass | This review records A-D status, validation commands, residuals, and closure-lane handoff. |

## 3. Validation Commands

Passed:

```bash
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/mission/test_policy_contract_shape.py tests/runtime/bindings/test_bindings_policy_surface.py tests/architecture/policy_execution/test_action_hold_policy_contract.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_bindings_policy_surface.py tests/runtime/facade/test_runtime_dto_promotion_batch1.py tests/runtime/facade/test_runtime_facade.py tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py tests/runtime/mission/test_policy_contract_shape.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/engagement/test_facade_engagement_export.py tests/runtime/bindings/test_bindings_engagement_surface.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/facade/test_runtime_facade_window_loop_injection.py
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py tests/runtime/test_agent_shim.py
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/runtime_facade/test_layering.py tests/architecture/policy_execution/test_action_hold_policy_contract.py
git diff --check
```

Observed outcomes:

- Build: passed.
- WP11-A focused tests: `17 passed`.
- WP11-A/B combined focused tests: `45 passed`.
- WP11-C vertical slice proof tests: `36 passed`.
- WP11-D consumer pre-gate tests: `20 passed`.
- Architecture guard / ActionHoldPolicy batch: `16 passed`.
- `git diff --check`: passed.

## 4. Integration Notes

- `ActionHoldPolicy` defaults remain conservative and explicitly declarative.
  They must not be described as cadence execution.
- Provenance labels are now visible through `ObservationBatchPacket.provenance`,
  `EngagementEventPacket.packet_provenance`, and
  `EngagementEventPacket.diagnostics_provenance`.
- `DecisionBelief` truth/raw-ECS use is made diagnostics-visible through
  validator helpers, but full Law 14 enforcement is deferred.
- `run_wp10_window` is still not Python-bound; the vertical proof is split
  between facade/window tests and live facade/binding tests.
- No new raw runtime escape hatch was added by WP11-C.

## 5. Residuals And Next Plan

Residuals intentionally carried forward:

- Full policy/control/physics multi-rate cadence should consume
  `ActionHoldPolicy` in a later cadence slice.
- Complete Law 14 enforcement still requires wider read-side/static or runtime
  guards.
- Agency Graph authority scope, role-based access control, and decision-model
  dispatch remain later information/agency enforcement work.
- `SensedState` and `SharedTacticalPicture` are vocabulary entries but are not
  new runtime producers in WP11.
- Backend/fidelity expansion, capability composition, and counterfactual
  worldline work remain downstream phases.

Recommended next WP: open the information and agency enforcement phase, using
WP11 provenance labels and consumer pre-gates as the starting boundary.
