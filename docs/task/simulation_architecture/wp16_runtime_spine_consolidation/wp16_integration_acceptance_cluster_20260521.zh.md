# WP16-F Integration And Acceptance Handoff

状态：`2026-05-21` complete / accepted integration and acceptance handoff。

语言版本：

- 英文主文：[wp16_integration_acceptance_cluster_20260521.md](wp16_integration_acceptance_cluster_20260521.md)
- 中文辅文：`wp16_integration_acceptance_cluster_20260521.zh.md`

输入：

- [WP16 runtime spine consolidation](runtime_spine_consolidation_wp16_20260521.zh.md)
- WP16-A through WP16-E worker handoffs
- [Subagent 使用规范](../../../standards/governance/subagent_usage_policy.zh.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.md)
- `tools/maintenance/wp_doc_closure_audit.py`

## 1. 目标

`WP16-F` 是串行 publication 与 acceptance lane。它应在 implementation streams
mergeable 后运行。职责是验证 runtime spine consolidation，如实记录 residuals，
同步 README/route/review index，并只在 gates 通过后创建 acceptance review。

## 2. 范围

范围内：

- 收集 A-E touched files、tests、blockers、residuals 与 integration notes；
- 运行 focused WP16 validation commands；
- 确认 `GAP-9` clock-domain enforcement status 与 residual boundary；
- implementation status 明确后更新 README 与 route；
- gates 通过时创建 final acceptance review 与中文辅文；
- 保持 generated documentation hints 与 acceptance authority 分离。

范围外：

- 在 workers handoff 后实现 A-E 代码，除非是小型 integration fixes；
- 隐藏 failed 或 blocked validation；
- 在缺少 evidence 时声明 global scheduler rewrite、full multi-rate support 或 broad legacy deletion。

## 3. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Implementation first | A-E 必须 mergeable，closure 才能标记 WP16 accepted。 |
| Exact commands | Acceptance 记录精确命令与结果。 |
| GAP-9 honesty | clock-domain enforcement 声明必须命名 selected slice 与 residuals。 |
| Generated-doc boundary | generated summaries 可辅助 closure，但不能验收 WP。 |
| Bilingual/index sync | 英文与中文 task/review/index docs 保持对齐。 |

## 4. 验证命令

预期 closure validation：

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp16_*.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py -k "clock or window or barrier or evidence"
python -m pytest -q tests/world_batch/test_world_batch_runtime.py tests/runtime/execution/test_execution_episode_batch_prepare.py -k "facade or window or evidence or batch"
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP16
```

如果添加了 public facade 或 binding surfaces，需要包含 worker handoffs 中相关 focused
runtime/binding commands。

## 5. 交接契约

返回：

- final A-E status table；
- 精确验证命令结果；
- `GAP-9` enforcement status 与 residuals；
- legacy path classification summary；
- generated documentation automation status；
- acceptance review paths if created；
- README/route/index files touched；
- 如果尚不应验收，必须保持开放的 blockers。
