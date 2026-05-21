# WP21 Full Counterfactual Experiment Runtime 验收审查

状态：`2026-05-22` accepted / implementation mergeable。

语言版本：

- 英文主文：[wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.md](wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.md)
- 中文辅文：`wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.zh.md`

输入：

- [WP21 Full Counterfactual Experiment Runtime](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/full_counterfactual_experiment_runtime_wp21_20260521.zh.md)
- [WP21-A Fact Ledger And Residual Freeze](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_fact_ledger_residual_freeze_cluster_20260521.zh.md)
- [WP21-B Snapshot Restore And Worldline Boundary](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_snapshot_restore_worldline_boundary_cluster_20260521.zh.md)
- [WP21-C Counterfactual Rollout And Causal Difference](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_counterfactual_rollout_causal_difference_cluster_20260521.zh.md)
- [WP21-D Scenario Intervention Generation Runtime](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_scenario_intervention_generation_cluster_20260521.zh.md)
- [WP21-E Experiment Facade And Evidence Collection](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_experiment_facade_evidence_cluster_20260521.zh.md)
- [WP21-F Final Cleanup And Acceptance Handoff](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_final_cleanup_acceptance_cluster_20260521.zh.md)
- [WP21 dispatch queue](../simulation_architecture/wp21_full_counterfactual_experiment_runtime/wp21_subagent_dispatch_queue_20260521.zh.md)

## 1. 结论

WP21 已作为有边界的最终 counterfactual / experiment runtime 增量验收。
它把 WP15 已验收 vocabulary 与 WP17 selected branch slice 转成维护中的
facade-owned runtime path，覆盖 bounded restore、parent/branch rollout、
deterministic generated-input artifacts、experiment evidence collection 与
non-promotional ancestry。

未发现阻塞性 findings。剩余项目都是有意保留且有 ownership 的 compatibility
residuals，不是未归属的 refactor-route residuals。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP21-A Fact Ledger And Residual Freeze` | pass | source-backed facts 与 residual IDs `WP21-A-R1` 至 `WP21-A-R9` 冻结 contract、selected runtime、generation、loader mirror、typed setup 与 backend boundaries。 |
| `WP21-B Snapshot Restore And Worldline Boundary` | pass | runtime 与 binding surface 支持 bounded `host_owned_facade_state_only` restore、worldline identity、deterministic seed metadata，并对 raw mutation、full clone、resident-state、exact-GPU、barrier mismatch 与 worldline mismatch fail closed。 |
| `WP21-C Counterfactual Rollout And Causal Difference` | pass | `RuntimeFacade::run_counterfactual_branch()` 消费 restore boundary，执行 parent/branch selected slices，并记录 replay envelope、branch point、restore barrier、worldline ids、deterministic seed 与 comparison evidence。 |
| `WP21-D Scenario Intervention Generation Runtime` | pass | `python/scenario/compiler/generation_runtime.py` 生成 deterministic、canonical、non-mutating generation artifacts，并保留 lineage，同时不触碰 `ScenarioLoader` 与 C++ rollout semantics。 |
| `WP21-E Experiment Facade And Evidence Collection` | pass | `RuntimeFacade::run_counterfactual_experiment()` 暴露 maintained experiment facade，返回 observations、rewards、terminations、traces、branch comparisons、generated-input refs，并通过 WP15 evidence bridge 保留 ancestry 且不做 truth/support promotion。 |
| `WP21-F Final Cleanup And Acceptance Handoff` | pass | 本 review 在 implementation evidence 存在后记录 A-E evidence、validation、retained compatibility notes、README/review index sync、双语 companion 与最终 route verdict。 |

## 3. 验证汇总

记录的 closure-pass validation：

```powershell
git diff --check
cmake --build build-local-win --target ef_py --config Release
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\architecture\test_wp15_experiment_evidence_bridge.py tests\architecture\test_wp15_counterfactual_admission.py tests\architecture\test_wp15_worldline_branch_metadata.py tests\architecture\test_wp15_replay_envelope_contracts.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "counterfactual or worldline or experiment or setup"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\scenario -k "generation or counterfactual or scenario_loader"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_bindings_runtime_dto_surface.py -k "counterfactual or experiment"
.\tools\maintenance\cmo_env.ps1 python tools\maintenance\wp_doc_closure_audit.py --wp WP21 --summary
```

观察结果：

- `git diff --check`：通过，仅有 LF/CRLF conversion warnings。
- `cmake --build build-local-win --target ef_py --config Release`：通过；最终实现构建后目标报告无待构建内容。
- WP15 architecture batch：`23 passed in 71.42s`。
- Runtime facade slice：`11 passed, 14 deselected in 1.55s`。
- Scenario generation / loader slice：`9 passed, 15 deselected in 0.94s`。
- Runtime binding DTO slice：`4 passed, 23 deselected in 0.30s`。
- `wp_doc_closure_audit.py --wp WP21 --summary` 在本 review 发布前运行过，
  正确报告 planned stage 下缺少 acceptance review；本次 publication sync 后应重新运行。

## 4. 保留的 Compatibility Residuals

WP21 验收范围有意保留以下 compatibility items，并明确其 ownership：

- `ScenarioLoader` 与 Python world-batch mirrors 继续是 compatibility/front-end
  mirrors；它们没有晋级为 maintained simulation truth。
- `RuntimeFacade.runtime()` 继续是 compatibility/diagnostics escape hatch，
  不是维护中的 experiment path。
- typed setup 保持 additive 且 compatibility-preserving；不强制 scenario-schema migration。
- exact GPU、resident-state restore、full clone、shadow compare 与 arbitrary
  unbounded worldline trees 继续 blocked。
- experiment outputs 只作为 evidence observations；不提升 backend/capability
  support，也不形成 truth claims。

## 5. 最终路线结论

WP21 关闭 frozen post-WP17 refactor route 中 counterfactual / experiment
runtime slice。没有未归属的 refactor-route residual。未来若要扩展 bounded
host-owned restore、selected-slice branch execution 或 non-promotional
experiment evidence 之外的能力，应从新的 scoped task 与新的 evidence gate
开始，而不是重开 WP21。
