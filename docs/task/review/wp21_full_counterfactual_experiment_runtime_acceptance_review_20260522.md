# WP21 Full Counterfactual Experiment Runtime Acceptance Review

Status: `2026-05-22` accepted / implementation mergeable.

Language:

- English canonical:
  `wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.md`
- Chinese companion:
  [wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.zh.md](wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.zh.md)

Inputs:

- [WP21 Full Counterfactual Experiment Runtime](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/full_counterfactual_experiment_runtime_wp21_20260521.md)
- [WP21-A Fact Ledger And Residual Freeze](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_fact_ledger_residual_freeze_cluster_20260521.md)
- [WP21-B Snapshot Restore And Worldline Boundary](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_snapshot_restore_worldline_boundary_cluster_20260521.md)
- [WP21-C Counterfactual Rollout And Causal Difference](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_counterfactual_rollout_causal_difference_cluster_20260521.md)
- [WP21-D Scenario Intervention Generation Runtime](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_scenario_intervention_generation_cluster_20260521.md)
- [WP21-E Experiment Facade And Evidence Collection](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_experiment_facade_evidence_cluster_20260521.md)
- [WP21-F Final Cleanup And Acceptance Handoff](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_final_cleanup_acceptance_cluster_20260521.md)
- [WP21 dispatch queue](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_subagent_dispatch_queue_20260521.md)

## 1. Verdict

WP21 is accepted as the bounded final counterfactual / experiment runtime
increment. It turns the accepted WP15 vocabulary and WP17 selected branch slice
into a maintained facade-owned runtime path for bounded restore, parent/branch
rollout, deterministic generated-input artifacts, experiment evidence
collection, and non-promotional ancestry.

No blocking findings were identified. The remaining items are deliberate
compatibility residuals with retained ownership, not unowned refactor-route
residuals.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP21-A Fact Ledger And Residual Freeze` | pass | Source-backed facts and residual IDs `WP21-A-R1` through `WP21-A-R9` freeze the contract, selected runtime, generation, loader mirror, typed setup, and backend boundaries. |
| `WP21-B Snapshot Restore And Worldline Boundary` | pass | Runtime and binding surfaces support bounded `host_owned_facade_state_only` restore, worldline identity, deterministic seed metadata, and fail-closed rejection of raw mutation, full clone, resident-state, exact-GPU, barrier mismatch, and worldline mismatch. |
| `WP21-C Counterfactual Rollout And Causal Difference` | pass | `RuntimeFacade::run_counterfactual_branch()` consumes the restore boundary, executes parent/branch selected slices, and records replay envelope, branch point, restore barrier, worldline ids, deterministic seed, and comparison evidence. |
| `WP21-D Scenario Intervention Generation Runtime` | pass | `python/scenario/compiler/generation_runtime.py` creates deterministic, canonical, non-mutating generation artifacts with lineage while leaving `ScenarioLoader` and C++ rollout semantics untouched. |
| `WP21-E Experiment Facade And Evidence Collection` | pass | `RuntimeFacade::run_counterfactual_experiment()` exposes the maintained experiment facade, returns observations, rewards, terminations, traces, branch comparisons, generated-input refs, and ancestry through the WP15 evidence bridge without truth/support promotion. |
| `WP21-F Final Cleanup And Acceptance Handoff` | pass | This review records A-E evidence, validation, retained compatibility notes, README/review index sync, bilingual companions, and final route verdict after implementation evidence exists. |

## 3. Validation Rollup

Recorded closure-pass validation:

```powershell
git diff --check
cmake --build build-local-win --target ef_py --config Release
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\architecture\test_wp15_experiment_evidence_bridge.py tests\architecture\test_wp15_counterfactual_admission.py tests\architecture\test_wp15_worldline_branch_metadata.py tests\architecture\test_wp15_replay_envelope_contracts.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "counterfactual or worldline or experiment or setup"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\scenario -k "generation or counterfactual or scenario_loader"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_bindings_runtime_dto_surface.py -k "counterfactual or experiment"
.\tools\maintenance\cmo_env.ps1 python tools\maintenance\wp_doc_closure_audit.py --wp WP21 --summary
```

Observed outcomes:

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

## 4. Retained Compatibility Residuals

The accepted scope intentionally leaves these compatibility items retained and
owned:

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

WP21 closes the frozen post-WP17 refactor route for the counterfactual /
experiment runtime slice. No unowned refactor-route residual remains. Future
work that expands beyond bounded host-owned restore, selected-slice branch
execution, or non-promotional experiment evidence must start from a new scoped
task and a new evidence gate rather than reopening WP21.
