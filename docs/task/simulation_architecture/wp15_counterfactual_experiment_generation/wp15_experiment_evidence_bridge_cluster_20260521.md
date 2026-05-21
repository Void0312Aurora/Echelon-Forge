# WP15-E Experiment Evidence And Capability Profiling Bridge

Status: `2026-05-21` mergeable / first slice complete.

Language:

- English canonical: `wp15_experiment_evidence_bridge_cluster_20260521.md`
- Chinese companion:
  [wp15_experiment_evidence_bridge_cluster_20260521.zh.md](wp15_experiment_evidence_bridge_cluster_20260521.zh.md)

Inputs:

- [WP15 counterfactual experiment generation](counterfactual_experiment_generation_wp15_20260521.md)
- [WP15-C counterfactual admission](wp15_counterfactual_admission_cluster_20260521.md)
- [WP15-D scenario and adversary generation request surface](wp15_scenario_adversary_generation_surface_cluster_20260521.md)
- [WP8 learning face](../wp8_learning_face/learning_face_wp8_20260520.md)
- [WP13 backend fidelity expansion](../wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.md)
- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.md)

## 1. Purpose

`WP15-E` links experiment runs and comparison evidence to counterfactual
admission, generated inputs, backend/fidelity profiles, platform capabilities,
and WP8 capability profiling vocabulary. The bridge should make evidence
ancestry queryable without turning experimental scores into maintained support
or truth claims.

## 2. Scope

In scope:

- experiment run, comparison, generated-input, and profile-observation evidence
  vocabulary;
- references to replay envelope, branch point, worldline, counterfactual
  admission, generation request, backend profile, fidelity profile, parity
  budget, capability bundle, and resolved spawn plan evidence;
- non-truth-claim and non-promotion validation gates;
- focused tests proving missing ancestry and unsupported promotions fail closed.

Out of scope:

- training or evaluation loop rewrites;
- broad experiment scheduler/orchestrator;
- promoting backend, fidelity, capability, or policy support from scores;
- changing WP8 capability profile semantics.

## 3. Candidate Implementation Seams

Inspect before editing:

- output from `WP15-C` and `WP15-D`;
- `docs/task/simulation_architecture/wp8_learning_face/*capability*`;
- `src/runtime/contracts/backend_profile_contracts.h`;
- `src/runtime/contracts/parity_budget_contracts.h`;
- `src/runtime/contracts/fidelity_profile_contracts.h`;
- `src/runtime/contracts/platform_capability_contracts.h`;
- `tests/architecture/test_wp14_*.py`.

Preferred approach:

- keep the bridge as evidence contracts/helpers and focused tests first;
- require explicit ancestry refs instead of looking up ambient runtime state;
- include a validation flag or reason that prevents score-to-support promotion;
- keep learning/profile labels observational.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Experiment ancestry | Experiment run references replay, branch, admission, generation, backend/fidelity, and capability evidence where applicable. |
| Comparison evidence | Baseline and variant comparisons preserve branch/worldline ids and seed/version metadata. |
| Profile observation | Capability profile outputs remain observations with evidence refs, not support claims. |
| Promotion blocked | Scores cannot promote backend/fidelity/capability support without accepted gates. |

## 5. Acceptance Tests

Minimum tests:

- valid experiment evidence fixture links counterfactual admission and generated
  inputs;
- validation rejects missing run id, comparison id, branch ancestry, generation
  ref, backend/fidelity ref, or capability evidence when required;
- profile observation cannot mark support/truth as maintained;
- score-to-support promotion is rejected with a stable reason.

Suggested commands:

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp15_experiment_evidence_bridge.py
python -m pytest -q tests/architecture/test_wp14_platform_capability_contracts.py
```

## 6. Handoff Contract

Return:

- evidence bridge files touched;
- experiment/profile field names;
- validation helper names and rejection reasons;
- tests added or updated;
- exact commands run and outcomes;
- blockers for `WP15-F`.
