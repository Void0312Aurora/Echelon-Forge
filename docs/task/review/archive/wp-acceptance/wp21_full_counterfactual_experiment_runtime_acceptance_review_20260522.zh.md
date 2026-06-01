# WP21 Full Counterfactual Experiment Runtime 验收审查

状态：`2026-05-22` owner-rejected / acceptance invalidated；仅保留为历史记录。

语言版本：

- 英文主文：[wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.md](wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.md)
- 中文辅文：`wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.zh.md`

输入：

- [WP21 Full Counterfactual Experiment Runtime](../../../simulation_architecture/archive/wp21_full_counterfactual_experiment_runtime/full_counterfactual_experiment_runtime_wp21_20260521.zh.md)
- [WP21-A Fact Ledger And Residual Freeze](../../../simulation_architecture/archive/wp21_full_counterfactual_experiment_runtime/wp21_fact_ledger_residual_freeze_cluster_20260521.zh.md)
- [WP21-B Snapshot Restore And Worldline Boundary](../../../simulation_architecture/archive/wp21_full_counterfactual_experiment_runtime/wp21_snapshot_restore_worldline_boundary_cluster_20260521.zh.md)
- [WP21-C Counterfactual Rollout And Causal Difference](../../../simulation_architecture/archive/wp21_full_counterfactual_experiment_runtime/wp21_counterfactual_rollout_causal_difference_cluster_20260521.zh.md)
- [WP21-D Scenario Intervention Generation Runtime](../../../simulation_architecture/archive/wp21_full_counterfactual_experiment_runtime/wp21_scenario_intervention_generation_cluster_20260521.zh.md)
- [WP21-E Experiment Facade And Evidence Collection](../../../simulation_architecture/archive/wp21_full_counterfactual_experiment_runtime/wp21_experiment_facade_evidence_cluster_20260521.zh.md)
- [WP21-F Final Cleanup And Acceptance Handoff](../../../simulation_architecture/archive/wp21_full_counterfactual_experiment_runtime/wp21_final_cleanup_acceptance_cluster_20260521.zh.md)
- [WP21 dispatch queue](../../../simulation_architecture/archive/wp21_full_counterfactual_experiment_runtime/wp21_subagent_dispatch_queue_20260521.zh.md)
- [WP22 强制退场补救](../../../simulation_architecture/archive/wp22_legacy_compatibility_retirement/legacy_compatibility_retirement_wp22_20260522.zh.md)

## 1. 结论

本 review 原先的 accepted verdict 已在 `2026-05-22` 被 owner 否决而失效。
它现在只作为 closure attempt 的历史记录保留，不得作为 WP21 当前验收权威或
最终路线闭合证据引用。

否决原因是实质性的：subagent 工作没有闭合成完整 return packet，timeout/partial
work 被当作任务关闭处理，而 compatibility layers / old implementation surfaces
在所谓 final cleanup 之后仍作为 first-class path 存在。这些是 blocker，不是可接受残留。

当前权威转移到 WP22；WP22 的 gate 是强制退场默认 legacy / compatibility paths。

## 2. Gate 结论

| Gate | 当前状态 | 原因 |
|------|----------|------|
| `WP21-A Fact Ledger And Residual Freeze` | claimed pass / not owner-accepted | ledger 未能阻止后续 closure 保留 first-class compatibility paths。 |
| `WP21-B Snapshot Restore And Worldline Boundary` | claimed pass / not owner-accepted | runtime 进展可能存在，但最终 closure 没有证明旧 runtime surfaces 已退场。 |
| `WP21-C Counterfactual Rollout And Causal Difference` | claimed pass / not owner-accepted | rollout evidence 本身不能关闭 default legacy access。 |
| `WP21-D Scenario Intervention Generation Runtime` | claimed pass / not owner-accepted | generation evidence 本身不能关闭 raw loader、tasking 或 mission-command bypass。 |
| `WP21-E Experiment Facade And Evidence Collection` | claimed pass / not owner-accepted | experiment facade evidence 不能证明其它仍被使用的 compatibility layers 已退场。 |
| `WP21-F Final Cleanup And Acceptance Handoff` | failed closure / superseded by WP22 | final cleanup 留下未退场 compatibility 与旧实现面，并过度接受未闭合 subagent 工作。 |

## 3. 验证汇总

此前记录的 closure-pass validation：

```powershell
git diff --check
cmake --build build-local-win --target ef_py --config Release
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\architecture\test_wp15_experiment_evidence_bridge.py tests\architecture\test_wp15_counterfactual_admission.py tests\architecture\test_wp15_worldline_branch_metadata.py tests\architecture\test_wp15_replay_envelope_contracts.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "counterfactual or worldline or experiment or setup"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\scenario -k "generation or counterfactual or scenario_loader"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_bindings_runtime_dto_surface.py -k "counterfactual or experiment"
.\tools\maintenance\cmo_env.ps1 python tools\maintenance\wp_doc_closure_audit.py --wp WP21 --summary
```

此前观察结果：

- `git diff --check`：通过，仅有 LF/CRLF conversion warnings。
- `cmake --build build-local-win --target ef_py --config Release`：通过；最终实现构建后目标报告无待构建内容。
- WP15 architecture batch：`23 passed in 71.42s`。
- Runtime facade slice：`11 passed, 14 deselected in 1.55s`。
- Scenario generation / loader slice：`9 passed, 15 deselected in 0.94s`。
- Runtime binding DTO slice：`4 passed, 23 deselected in 0.30s`。
- `wp_doc_closure_audit.py --wp WP21 --summary` 在本 review 发布前运行过，
  正确报告 planned stage 下缺少 acceptance review；本次 publication sync 后应重新运行。

## 4. 导致 Closure 失效的 Residuals

原 review 曾把以下项描述为 retained compatibility items。owner 否决后，只要它们仍作为
default maintained paths，就不得再作为 pass-state language 使用：

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

WP21 当前没有关闭 frozen post-WP17 refactor route。本验收审查由 WP22 取代。
只有在 WP22 证明默认 legacy paths 已迁移、删除或带 guard 显式隔离，并且每个
subagent 任务都有完整 return packet 或被记录为 blocked 后，才能再次声明 closure。
