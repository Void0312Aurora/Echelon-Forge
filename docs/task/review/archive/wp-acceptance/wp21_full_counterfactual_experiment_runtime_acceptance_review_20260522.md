# WP21 Full Counterfactual Experiment Runtime Acceptance Review

Status: `2026-05-22` owner-rejected / acceptance invalidated; historical
record only.

Language:

- English canonical:
  `wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.md`
- Chinese companion:
  [wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.zh.md](wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.zh.md)

Inputs:

- [WP21 Full Counterfactual Experiment Runtime](../../../simulation_architecture/wp21_full_counterfactual_experiment_runtime/full_counterfactual_experiment_runtime_wp21_20260521.md)
- [WP21-A Fact Ledger And Residual Freeze](../../../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_fact_ledger_residual_freeze_cluster_20260521.md)
- [WP21-B Snapshot Restore And Worldline Boundary](../../../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_snapshot_restore_worldline_boundary_cluster_20260521.md)
- [WP21-C Counterfactual Rollout And Causal Difference](../../../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_counterfactual_rollout_causal_difference_cluster_20260521.md)
- [WP21-D Scenario Intervention Generation Runtime](../../../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_scenario_intervention_generation_cluster_20260521.md)
- [WP21-E Experiment Facade And Evidence Collection](../../../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_experiment_facade_evidence_cluster_20260521.md)
- [WP21-F Final Cleanup And Acceptance Handoff](../../../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_final_cleanup_acceptance_cluster_20260521.md)
- [WP21 dispatch queue](../../../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_subagent_dispatch_queue_20260521.md)
- [WP22 forced-retirement remediation](../../../simulation_architecture/wp22_legacy_compatibility_retirement/legacy_compatibility_retirement_wp22_20260522.md)

## 1. Verdict

This review's original accepted verdict is invalidated by owner rejection on
`2026-05-22`. It is retained only as a historical record of the closure attempt.
It must not be cited as the current acceptance authority for WP21 or as final
route closure.

The rejection reason is substantive: subagent work was not closed into complete
return packets, timeout/partial work was treated as if it closed tasks, and
compatibility layers / old implementation surfaces remained first-class after
the claimed final cleanup. Those are blockers, not acceptable residuals.

Current authority moves to WP22, whose gate is forced retirement of default
legacy and compatibility paths.

## 2. Gate Verdicts

| Gate | Current status | Reason |
|------|----------------|--------|
| `WP21-A Fact Ledger And Residual Freeze` | claimed pass / not owner-accepted | The ledger did not prevent later closure from retaining first-class compatibility paths. |
| `WP21-B Snapshot Restore And Worldline Boundary` | claimed pass / not owner-accepted | Runtime progress may exist, but final closure did not prove old runtime surfaces were retired. |
| `WP21-C Counterfactual Rollout And Causal Difference` | claimed pass / not owner-accepted | Rollout evidence does not close default legacy access by itself. |
| `WP21-D Scenario Intervention Generation Runtime` | claimed pass / not owner-accepted | Generation evidence does not close raw loader, tasking, or mission-command bypasses. |
| `WP21-E Experiment Facade And Evidence Collection` | claimed pass / not owner-accepted | Experiment facade evidence does not retire compatibility layers still used elsewhere. |
| `WP21-F Final Cleanup And Acceptance Handoff` | failed closure / superseded by WP22 | The final cleanup left unretired compatibility and old implementation surfaces and over-accepted incomplete subagent closure. |

## 3. Validation Rollup

Previously recorded closure-pass validation:

```powershell
git diff --check
cmake --build build-local-win --target ef_py --config Release
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\architecture\test_wp15_experiment_evidence_bridge.py tests\architecture\test_wp15_counterfactual_admission.py tests\architecture\test_wp15_worldline_branch_metadata.py tests\architecture\test_wp15_replay_envelope_contracts.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "counterfactual or worldline or experiment or setup"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\scenario -k "generation or counterfactual or scenario_loader"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_bindings_runtime_dto_surface.py -k "counterfactual or experiment"
.\tools\maintenance\cmo_env.ps1 python tools\maintenance\wp_doc_closure_audit.py --wp WP21 --summary
```

Previously observed outcomes:

- `git diff --check`: passed with LF/CRLF conversion warnings only.
- `cmake --build build-local-win --target ef_py --config Release`: passed; the
  target reported no pending build work after the final implementation build.
- WP15 architecture batch: `23 passed in 71.42s`.
- Runtime facade slice:
  `11 passed, 14 deselected in 1.55s`.
- Scenario generation / loader slice:
  `9 passed, 15 deselected in 0.94s`.
- Runtime binding DTO slice:
  `4 passed, 23 deselected in 0.30s`.
- `wp_doc_closure_audit.py --wp WP21 --summary` was run before this review and
  correctly reported the missing acceptance review as expected for the planned
  stage; it should be re-run after this publication sync.

## 4. Residuals That Invalidated Closure

The original review described the following as retained compatibility items.
After owner rejection, these cannot be used as pass-state language when they
remain default maintained paths:

- `ScenarioLoader` and Python world-batch mirrors remain compatibility/front-end
  mirrors; they are not promoted to maintained simulation truth.
- `RuntimeFacade.runtime()` remains a compatibility/diagnostics escape hatch,
  not the maintained experiment path.
- Typed setup stays additive and compatibility-preserving; no scenario-schema
  migration is forced.
- Exact GPU, resident-state restore, full clone, shadow compare, and arbitrary
  unbounded worldline trees remain blocked.
- Experiment outputs remain evidence observations only; they do not promote
  backend/capability support or truth claims.

## 5. Final Route Verdict

WP21 does not currently close the frozen post-WP17 refactor route. This
acceptance review is superseded by WP22. A future closure may only be claimed
after WP22 proves that default legacy paths are migrated, deleted, or explicitly
quarantined with guards, and that every subagent task has a complete return
packet or is recorded as blocked.
