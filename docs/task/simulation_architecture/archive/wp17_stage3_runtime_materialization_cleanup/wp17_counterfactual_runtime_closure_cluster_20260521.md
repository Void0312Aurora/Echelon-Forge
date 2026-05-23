# WP17-F Counterfactual Runtime Slice And Closure

Status: `2026-05-21` narrowed selected-slice runtime implemented; focused
validation passed.

Inputs:

- [WP17 main plan](stage3_runtime_materialization_cleanup_wp17_20260521.md)
- [WP15 counterfactual experiment generation](../wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.md)
- [WP8 learning face](../wp8_learning_face/learning_face_wp8_20260520.md)

## Purpose

Add the first executable counterfactual slice and close the final legacy cleanup
lane. The accepted target is an explicit-setup selected-entity
snapshot/branch/compare path, not arbitrary live-world clone or full experiment
orchestration.

## Entry Conditions

- WP17-C has deterministic cadence/barrier evidence for the selected runtime
  slice.
- WP17-D names the accepted fidelity/profile scope as the reference CPU exact
  baseline selected through `RuntimeFacade::admit_fidelity_request()`.
- WP17-B has bounded maintained business access away from compatibility-only
  `batch_runtime` reads.

## Scope

In scope:

- snapshot of position, velocity, orientation, and minimal physics state for one
  selected entity;
- branch creation from an explicit `BatchWorldSetupRequest` baseline with
  deterministic seed and mutation metadata;
- two-world selected-entity comparison with causal deltas at barriers;
- final legacy cleanup guard review and closure-lane handoff.

Out of scope:

- arbitrary-depth worldline trees;
- arbitrary live-world reflection/clone as a branch baseline;
- full curriculum or adversarial experiment orchestration;
- generated scenario mutation of authoritative runtime state without admission;
- deleting compatibility APIs before replacement evidence is complete.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `F1` | Physics snapshot/restore | `RuntimeFacade::snapshot_counterfactual_entity()` captures selected-entity position, velocity, orientation, fidelity/provider, cadence, barrier, and evidence refs. |
| `F2` | Branch rollout | `RuntimeFacade::run_counterfactual_branch()` builds parent/branch worlds from explicit setup, applies a facade-owned selected-entity mutation, and rejects raw authoritative mutation. |
| `F3` | Causal comparison | `RuntimeWorldlineComparison` reports selected-slice deltas at the counterfactual barrier. |
| `F4` | Final cleanup handoff | Legacy paths retained, deprecated, or blocked are recorded with guards and closure-owner notes. |

## Implementation Evidence

Runtime surfaces:

- `RuntimeCounterfactualSnapshot`
- `RuntimeCounterfactualBranchRequest`
- `RuntimeCounterfactualBranchResult`
- `RuntimeWorldlineComparison`
- `RuntimeFacade::snapshot_counterfactual_entity()`
- `RuntimeFacade::run_counterfactual_branch()`

Accepted semantics:

- branch baselines must come from explicit `BatchWorldSetupRequest`;
- reference CPU exact-evaluation fidelity is admitted;
- resident/exact-GPU/shadow provider requests fail closed;
- `allow_raw_authoritative_state_mutation` is rejected;
- WP15 metadata-only replay/admission contracts remain fail-closed for full
  snapshot/restore support.

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp15_*.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py -k "barrier or evidence"
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or replay or fidelity or provider"
```

## Handoff

Return snapshot scope, determinism evidence, rollout/compare behavior, commands
run, final residuals, and closure-lane requirements.
