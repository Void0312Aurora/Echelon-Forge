# WP15 Counterfactual Experiment Generation Acceptance Review

Status: `2026-05-21` accepted / implementation mergeable.

Language:

- English canonical:
  `wp15_counterfactual_experiment_generation_acceptance_review_20260521.md`
- Chinese companion:
  [wp15_counterfactual_experiment_generation_acceptance_review_20260521.zh.md](wp15_counterfactual_experiment_generation_acceptance_review_20260521.zh.md)

Inputs:

- [WP15 Counterfactual Experiment Generation](../simulation_architecture/wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.md)
- [WP15-A Replay Envelope And Branch Point Contract](../simulation_architecture/wp15_counterfactual_experiment_generation/wp15_replay_envelope_branch_point_cluster_20260521.md)
- [WP15-B Worldline Branch Metadata Gate](../simulation_architecture/wp15_counterfactual_experiment_generation/wp15_worldline_branch_metadata_gate_cluster_20260521.md)
- [WP15-C Counterfactual Request Admission](../simulation_architecture/wp15_counterfactual_experiment_generation/wp15_counterfactual_admission_cluster_20260521.md)
- [WP15-D Scenario And Adversary Generation Request Surface](../simulation_architecture/wp15_counterfactual_experiment_generation/wp15_scenario_adversary_generation_surface_cluster_20260521.md)
- [WP15-E Experiment Evidence And Capability Profiling Bridge](../simulation_architecture/wp15_counterfactual_experiment_generation/wp15_experiment_evidence_bridge_cluster_20260521.md)
- [WP15-F Integration And Acceptance Handoff](../simulation_architecture/wp15_counterfactual_experiment_generation/wp15_integration_acceptance_cluster_20260521.md)
- [WP14 Capability Composition Acceptance Review](wp14_capability_composition_acceptance_review_20260521.md)

## 1. Verdict

WP15 is accepted as the Phase 6 counterfactual and experiment-generation increment. The first slices for replay envelopes, worldline branch metadata, counterfactual admission, generation request surfaces, and experiment evidence ancestry were already validated in the main thread; this closure lane records the final handoff and acceptance boundary.

The accepted boundary is intentionally narrow:

- no full snapshot/restore;
- no maintained counterfactual rollout execution;
- no broad generator runtime or public experiment orchestrator;
- no score-to-truth or score-to-support promotion;
- no second semantic lifecycle outside the causal/facade boundary.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP15-A Replay Envelope And Branch Point Contract` | pass | `tests/architecture/causal_runtime/test_replay_envelope_contracts.py` passed; the slice defines deterministic replay envelope, branch point, seed, snapshot, barrier, event-order, and facade provenance vocabulary. |
| `WP15-B Worldline Branch Metadata Gate` | pass | `tests/architecture/causal_runtime/test_worldline_branch_metadata.py` passed; the slice names parent/child worldlines, branch reason, mutation intent, provenance refs, and unsupported-restore boundaries. |
| `WP15-C Counterfactual Request Admission` | pass | `tests/architecture/causal_runtime/test_counterfactual_admission.py` passed; the slice admits or rejects metadata-only counterfactual requests with fail-closed ancestry, authority, backend/fidelity, and capability checks. |
| `WP15-D Scenario And Adversary Generation Request Surface` | pass | `tests/scenario/test_wp15_generation_request_surface.py` passed, and `tests/scenario/test_scenario_compiler.py -k "wp15 or branch or runtime"` passed; the request surface stays additive and non-mutating. |
| `WP15-E Experiment Evidence And Capability Profiling Bridge` | pass | `tests/architecture/causal_runtime/test_experiment_evidence_bridge.py` passed; experiment ancestry stays queryable without turning scores into support claims. |
| `WP15-F Integration And Acceptance Handoff` | pass | This review records A-E status, exact validation outcomes, residuals, README/route sync, and bilingual closure. |

## 3. Validation Commands

Passed in the main thread before this closure:

```bash
python -m pytest -q tests/architecture/causal_runtime/test_replay_envelope_contracts.py
python -m pytest -q tests/architecture/causal_runtime/test_worldline_branch_metadata.py
python -m pytest -q tests/architecture/causal_runtime/test_counterfactual_admission.py
python -m pytest -q tests/architecture/causal_runtime/test_experiment_evidence_bridge.py
python -m pytest -q tests/scenario/test_wp15_generation_request_surface.py
python -m pytest -q tests/scenario/test_scenario_compiler.py -k "wp15 or branch or runtime"
python -m pytest -q tests/architecture/platform_spawn/test_platform_capability_contracts.py
```

Observed outcome:

- all commands passed.

Closure-lane checks in this pass:

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP15
```

Observed outcome:

- both commands passed.

## 4. Runtime Surface Summary

- `ReplayEnvelope` and `BranchPoint` remain deterministic and fail closed when required ancestry is missing.
- `WorldlineBranchMetadata` names parent/child worldlines, mutation intent, provenance refs, and unsupported-restore boundaries.
- `CounterfactualExperimentRequest` admission stays metadata-only and rejects raw authoritative state mutation.
- Scenario and adversary generation remain request surfaces, not authoritative runtime writers.
- Experiment evidence ancestry stays queryable without promoting scores to support or truth claims.

## 5. Residuals And Next Plan

Residuals intentionally carried forward:

- full snapshot/restore;
- maintained counterfactual rollout execution;
- broad generator runtime and public experiment orchestration;
- score-to-support or score-to-truth promotion;
- any second semantic lifecycle outside the causal/facade boundary.

The main thread can now finalize WP15 acceptance using this closure packet and the already-passed A-E slices.
