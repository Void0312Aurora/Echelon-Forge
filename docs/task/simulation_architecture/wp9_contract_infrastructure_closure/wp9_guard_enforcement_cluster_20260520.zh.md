# WP9-D Guard Enforcement

状态：`2026-05-20` complete / accepted WP9 并行流。

语言版本：

- 英文主文：[wp9_guard_enforcement_cluster_20260520.md](wp9_guard_enforcement_cluster_20260520.md)
- 中文辅文：`wp9_guard_enforcement_cluster_20260520.zh.md`

输入：

- [WP9 contract and infrastructure closure](contract_infrastructure_closure_wp9_20260520.zh.md)
- [WP5 验证套件验收](../../review/archive/wp-acceptance/wp5_validation_harness_acceptance_review_20260519.zh.md)
- [WP7.5 训练路径 facade 桥接](../wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md)
- [Subagent 使用规范](../../../standards/governance/subagent_usage_policy.zh.md)

## 1. 目的

WP9-D 把 deferred guard items 转成维护中的检查。目标不是禁止每条 compatibility path，而是让每个保留的 direct `sim.*`、runtime 或 binding surface exception 可见、带标签且可测试。

本流覆盖：

- GUA-1 global `sim.*` AST guard with allowlist
- GUA-2 binding surface smoke promotion

## 2. Guard 设计

Guard 必须区分：

| 类别 | 允许条件 | 必需标签 |
|------|----------|----------|
| Maintained facade path | 使用 typed request/result facade APIs。 | 不需要 exception label。 |
| Compatibility adapter | 把 legacy access 集中在命名 adapter 后面，且没有 hidden state ownership。 | `compatibility_only`。 |
| Diagnostics path | 读取 trace/debug/export data，但不影响 committed state。 | `diagnostics_only`。 |
| Test fixture | 只为 surface validation 构造 shell worlds 或 packet defaults。 | `test_only`。 |
| Violation | 在 facade contracts 外 mutate authoritative simulation state，或把 raw runtime access 隐藏在 mainline code。 | 不允许。 |

## 3. 实施路线

推荐路线：

1. 在 architecture guard test 附近添加 allowlist document 或 table。
2. 实现 AST checks，扫描 Python call site 中的 direct `sim.*` 与 raw runtime escape hatch。
3. 保留现有 scoped escape hatch tests，但让 provenance labels 更显式。
4. 提升 `test_bindings_engagement_surface.py`，覆盖 empty packet-shell world-index case，使其不再是 review-only residual。
5. 避免 broad string-grep bans 在没有解释 allowed path 的情况下破坏 diagnostics-only code。

推荐写入范围：

- `tests/architecture/*`
- `tests/runtime/bindings/test_bindings_engagement_surface.py`
- `docs/task/simulation_architecture/wp9_contract_infrastructure_closure/*`
- 可选：`docs/standards/governance/` 下的 focused allowlist 文件

## 4. 工作项

| 流 | 必需产出 | 预算 |
|----|----------|------|
| `WP9-D1 Allowlist Vocabulary` | Direct simulation/runtime access 的 labels 与 allowed path categories 文档。 | Medium. |
| `WP9-D2 AST Guard` | 执行 allowlist 的静态测试，避免误禁 diagnostics/compatibility。 | High. |
| `WP9-D3 Binding Smoke Promotion` | Empty engagement packet shell 与 world-index/default field behavior 的 binding test。 | Medium. |
| `WP9-D4 Evidence Sync` | 为 WP9-E acceptance 记录 test names 与 guard labels。 | Medium. |

## 5. 非目标

- 当 maintained callers 仍需要 compatibility adapters 时，不删除它们。
- 不在没有 allowlist 与 labels 的情况下添加 broad `sim.*` ban。
- 除非 test-only fixture 暴露真实 binding bug，否则不改变 C++ runtime behavior。
- 不从 import success 推断 facade correctness。

## 6. 验收 Gate

WP9-D 满足以下条件后可进入 WP9-E：

1. Allowlist labels 已文档化。
2. Static guard tests 执行 labels，并报告有用 file/line evidence。
3. Binding smoke 覆盖先前延后的 empty packet-shell world-index case。
4. Compatibility 与 diagnostics exceptions 保持显式。
5. 最终 WP9 review 记录 validation commands。

## 7. 验证命令

```bash
git diff --check
pytest tests/architecture/test_runtime_facade_layering.py tests/architecture/test_wp5_design_boundary_gates.py tests/runtime/bindings/test_bindings_engagement_surface.py
rg -n "sim\\.\\*|compatibility_only|diagnostics_only|test_only|Binding surface smoke|EngagementEventPacket" tests docs/task/simulation_architecture/wp9_contract_infrastructure_closure
```
