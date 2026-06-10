# WP21-E Experiment Facade And Evidence Collection

Status: `2026-05-21` planned; waits for WP21-C and WP21-D.

Language:

- English canonical: `wp21_experiment_facade_evidence_cluster_20260521.md`
- Chinese companion:
  [wp21_experiment_facade_evidence_cluster_20260521.zh.md](wp21_experiment_facade_evidence_cluster_20260521.zh.md)

Inputs:

- [WP21 main plan](full_counterfactual_experiment_runtime_wp21_20260521.md)
- [WP21-C rollout and causal difference](wp21_counterfactual_rollout_causal_difference_cluster_20260521.md)
- [WP21-D scenario generation runtime](wp21_scenario_intervention_generation_cluster_20260521.md)
- [WP15 experiment evidence bridge](../wp15_counterfactual_experiment_generation/wp15_experiment_evidence_bridge_cluster_20260521.md)

## Purpose

Expose the maintained experiment runtime surface and collect evidence across
setup, generation, branch rollout, comparison, observations, rewards,
terminations, and traces.

## Scope

In scope:

- experiment run DTOs / facade methods / Python bindings as needed;
- collection of parent and branch observations, rewards, terminations, traces,
  causal differences, generated-input artifacts, and evidence ancestry;
- non-truth-claim and support-promotion guards inherited from WP15;
- focused tests proving complete ancestry and public visibility.

Out of scope:

- broad curriculum learning runtime;
- capability or backend support promotion from experiment scores;
- exact GPU or resident-state promotion.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `E1` | Experiment run surface | A maintained facade surface creates or runs a bounded experiment from admitted inputs. |
| `E2` | Evidence collection | Results include observations, rewards, terminations, traces, causal differences, and generated-input refs. |
| `E3` | Ancestry validation | Replay envelope, branch point, setup/generation, backend/fidelity, and capability refs are present and consistent. |
| `E4` | Public/binding proof | Python binding or facade tests prove visibility and fail-closed non-truth-claim behavior. |

## Suggested Validation

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/causal_runtime/test_experiment_evidence_bridge.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "experiment or counterfactual or worldline"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py -k "experiment or counterfactual"
```

## Handoff

Return facade/binding surface, evidence schema, ancestry checks, non-truth-claim
guards, touched files, commands run, and final cleanup notes for F.
