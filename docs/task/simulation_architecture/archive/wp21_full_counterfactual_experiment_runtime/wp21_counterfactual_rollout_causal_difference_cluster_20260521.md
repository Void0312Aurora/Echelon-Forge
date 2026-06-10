# WP21-C Counterfactual Rollout And Causal Difference

Status: `2026-05-21` planned; waits for WP21-B.

Language:

- English canonical: `wp21_counterfactual_rollout_causal_difference_cluster_20260521.md`
- Chinese companion:
  [wp21_counterfactual_rollout_causal_difference_cluster_20260521.zh.md](wp21_counterfactual_rollout_causal_difference_cluster_20260521.zh.md)

Inputs:

- [WP21 main plan](full_counterfactual_experiment_runtime_wp21_20260521.md)
- [WP21-B snapshot/restore boundary](wp21_snapshot_restore_worldline_boundary_cluster_20260521.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md)
- [WP15 counterfactual admission](../wp15_counterfactual_experiment_generation/wp15_counterfactual_admission_cluster_20260521.md)

## Purpose

Execute parent and branch worldlines from admitted inputs and produce
causal-difference evidence at declared barriers. This turns the selected
branch/compare proof into maintained runtime behavior.

## Scope

In scope:

- parent and branch worldline rollout from explicit setup, restore boundary, or
  deterministic generated artifact;
- deterministic seed derivation and replay envelope checks;
- causal difference records for state, observation, termination, and trace refs
  in the selected slice;
- fail-closed rejection of raw authoritative mutation and unsupported restore
  scope.

Out of scope:

- broad curriculum orchestration;
- truth/support promotion from branch outcomes;
- unlimited worldline tree management.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `C1` | Branch execution | Parent and branch run independently from admitted setup/restore inputs. |
| `C2` | Determinism evidence | Replay envelope, seed, branch point, and barrier refs are recorded and validated. |
| `C3` | Causal difference | Runtime emits comparable deltas and evidence refs at each declared comparison barrier. |
| `C4` | Rejection behavior | Unsupported mutation, missing envelope/branch point, invalid restore scope, and unsupported fidelity fail closed. |

## Suggested Validation

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or causal or worldline"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/causal_runtime/test_counterfactual_admission.py
```

## Handoff

Return rollout semantics, comparison schema, determinism evidence, touched
files, commands run, and E-facing experiment collection notes.
