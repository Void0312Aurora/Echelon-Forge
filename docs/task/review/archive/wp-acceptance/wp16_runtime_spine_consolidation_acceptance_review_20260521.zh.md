# WP16 Runtime Spine Consolidation 验收审查

状态：`2026-05-21` accepted / implementation mergeable。

语言版本：

- 英文主文：[wp16_runtime_spine_consolidation_acceptance_review_20260521.md](wp16_runtime_spine_consolidation_acceptance_review_20260521.md)
- 中文辅文：`wp16_runtime_spine_consolidation_acceptance_review_20260521.zh.md`

输入：

- [WP16 Runtime Spine Consolidation](../simulation_architecture/wp16_runtime_spine_consolidation/runtime_spine_consolidation_wp16_20260521.zh.md)
- [WP16-A Runtime Spine Inventory And Bypass Map](../simulation_architecture/wp16_runtime_spine_consolidation/wp16_runtime_spine_inventory_cluster_20260521.zh.md)
- [WP16-B Clock-Domain Enforcement And Merge Trace](../simulation_architecture/wp16_runtime_spine_consolidation/wp16_clock_domain_enforcement_cluster_20260521.zh.md)
- [WP16-C Facade And Batch Path Spine Migration](../simulation_architecture/wp16_runtime_spine_consolidation/wp16_facade_batch_spine_migration_cluster_20260521.zh.md)
- [WP16-D Legacy Path Deprecation And Compatibility Gates](../simulation_architecture/wp16_runtime_spine_consolidation/wp16_legacy_deprecation_compatibility_cluster_20260521.zh.md)
- [WP16-E Generated Documentation And Closure Automation](../simulation_architecture/wp16_runtime_spine_consolidation/wp16_generated_documentation_automation_cluster_20260521.zh.md)
- [WP16-F Integration And Acceptance Handoff](../simulation_architecture/wp16_runtime_spine_consolidation/wp16_integration_acceptance_cluster_20260521.zh.md)
- [WP15 验收审查](wp15_counterfactual_experiment_generation_acceptance_review_20260521.zh.md)

## 1. 结论

WP16 已作为 selected-slice runtime-spine consolidation 增量验收。它把已验收的 WP10-WP15 runtime、facade、agency、backend/fidelity、capability 与 counterfactual 边界，收束为 narrowed spine slice 上的维护中默认运行路径。

这里明确不是 global rewrite：

- 没有 global scheduler rewrite；
- 没有 full multi-rate support；
- 没有 public legacy API 删除；
- 没有 maintained independent-domain merge success path；
- 没有把 counterfactual/scenario generation runtime consumer 推进到超出保留的 compatibility 与 diagnostics 边界之外。

已验收 slice 是围绕 `RuntimeWindowRequest` admission、`input_injection`、维护中的 `p7.fire_control_launch.v1` / `p9.effects_damage.v1` / `p10.observation_export.v1` 节点、`window_commit`、`export`、facade export，以及当前 facade-shaped consumer adapters 的 runtime-spine handoff。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP16-A Runtime Spine Inventory And Bypass Map` | pass | `tests/architecture/fixtures/wp16_runtime_spine_inventory_20260521.json` 与 `docs/task/simulation_architecture/wp16_runtime_spine_consolidation/wp16_runtime_spine_inventory_evidence_20260521.md` 对 maintained、compatibility、diagnostics-only、deprecated、blocked 与 unknown paths 进行了显式分类，并标出 owner 与 next gate。 |
| `WP16-B Clock-Domain Enforcement And Merge Trace` | pass | `src/runtime/facade/runtime_window_coordinator.h`、`src/runtime/contracts/stage_node_manifest_registry.h` 与 `tests/runtime/facade/test_runtime_facade_window_loop_injection.py` 证明 selected slice 的 trigger/skip evidence，以及缺少 deterministic merge metadata 时的 fail-closed 处理。 |
| `WP16-C Facade And Batch Path Spine Migration` | pass | `src/runtime/facade/runtime_facade.h`、`src/runtime/facade/runtime_facade.cpp`、`python/rl/runtime/world_batch/adapter.py`、`python/rl/runtime/world_batch_vec_env.py` 与 `tests/runtime/bindings/test_bindings_engagement_surface.py` 在保留兼容性的同时，把选定的 maintained consumer 通过 runtime-window evidence spine 或显式 fallback wrapper 路由。 |
| `WP16-D Legacy Path Deprecation And Compatibility Gates` | pass | `docs/task/simulation_architecture/wp16_runtime_spine_consolidation/wp16_legacy_path_gate_evidence_20260521.md` 与 `tests/architecture/test_wp16_legacy_path_gates.py` 让 `WorldBatchRuntime`、`batch_runtime`、`RuntimeFacade.runtime()` 与 diagnostics-only paths 保持明确边界，而不是被静默当作 maintained。 |
| `WP16-E Generated Documentation And Closure Automation` | pass | `tools/maintenance/wp_doc_closure_audit.py` 现在可以报告 WP16 closure 状态，但不会替代 acceptance authority；generated summaries 仍然只是 advisory。 |
| `WP16-F Integration And Acceptance Handoff` | pass | 本审查记录 A-E 状态、精确验证结果、residuals、README/route/index sync 与窄的验收边界。 |

## 3. 验证命令

在本 review 之前，主线程已通过：

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp16_runtime_spine_inventory.py tests/architecture/test_wp16_clock_domain_enforcement.py tests/architecture/test_wp16_legacy_path_gates.py tests/architecture/test_wp_doc_closure_audit.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py -k "clock or window or barrier or evidence"
python -m pytest -q tests/world_batch/test_single_world_batch_runtime.py tests/world_batch/test_world_batch_vec_env.py -k "reset_uses_runtime_facade_compatibly or exposes_batch_runtime_as_compatibility_view or single"
python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py -k "runtime_window or observation_batch_packet or engagement_event_packet"
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP16 --summary --json
```

观察结果：

- `git diff --check`：通过。
- WP16 architecture batch：`18 passed`。
- Runtime facade window-loop batch：`5 passed`。
- World-batch compatibility batch：`5 passed, 34 deselected`。
- Runtime binding DTO batch：`3 passed, 14 deselected`。
- closure audit summary：通过，并且没有缺少 acceptance review，也没有缺少 optional evidence docs 的中文辅文。

在补充 review package 后，又运行了一次最终 closure validation：

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP16
```

观察结果：

- 两条命令均通过。

## 4. 运行时表面摘要

- `RuntimeWindowRequest` admission 现在会记录 selected spine slice，并带上 `input_injection`、`window_commit` 与 `export` barrier evidence。
- 维护中的 spine 仍然只覆盖 `p7.fire_control_launch.v1`、`p9.effects_damage.v1` 与 `p10.observation_export.v1`；reserved 或 diagnostics sibling nodes 仍不在 maintained slice 内。
- `RuntimeFacade.runtime()` 与 `batch_runtime` 仍是 compatibility surface，不是晋级后的 maintained frontend contract。
- `WorldBatchRuntime` 仍是 deprecated-candidate surface，并保留 explicit compatibility retention，不是已删除 API。
- `python/scenario/compiler/generation_request.py` 与 `src/runtime/contracts/counterfactual_replay_contracts.h` 仍因缺少 maintained runtime execution linkage 而 blocked，本次不晋级为 maintained runtime consumer。

## 5. Residuals 与下一步

有意保留的 residuals：

- global scheduler rewrite；
- full multi-rate support；
- maintained independent-domain merge success path；
- public legacy API 删除；
- counterfactual/scenario generation maintained runtime consumer 晋级；
- 在 retained fallback paths 还未有更窄 owner 之前，对 compatibility wrappers 做大范围替换。

WP16 的 accepted 增量作为 selected-slice runtime-spine consolidation closure packet 已可 merge，但必须继续保留 residual register 与上面这条窄实现边界。
