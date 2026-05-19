# WP4 Facade 对齐验收审查

状态：`2026-05-19` WP4 最终验收已完成。

范围：WP4 facade surface inventory、engagement/step 对齐、policy/binding 对齐、
facade evidence gate、被动 agent shim、compatibility guard review 与 WP5 交接。

相关文档：

- [WP4 facade 对齐](../simulation_architecture/facade_alignment_wp4_20260519.zh.md)
- [WP4 第一波验收审查](wp4_first_wave_acceptance_review_20260519.zh.md)
- [WP4 第二波验收审查](wp4_second_wave_acceptance_review_20260519.zh.md)
- [WP4-F 集成交接](../simulation_architecture/wp4_integration_handoff_20260519.zh.md)
- [WP5 验证套件](../simulation_architecture/validation_harness_wp5_20260519.zh.md)

## 1. 验收决定

WP4 facade 对齐予以验收。

已验收范围有意保持轻实现。WP4 没有为 agent role、decision belief、action
intent 或 coordination intent 提前提升新的 public C++ DTO。它稳定了
maintained facade 词汇，在既有 facade 行为周围添加聚焦 evidence gate，并发布
被动 Python shim，使 policy/agent metadata 显式化，但不改变 runtime 行为。

## 2. 已验收证据

| 领域 | 已验收证据 | 决定 |
|------|------------|------|
| Facade surface 分类 | `wp4_surface_inventory_wp4a_20260519.md` | Maintained、compatibility-only、diagnostics-only 与 deferred surface 已足够支撑 WP5 validation。 |
| Engagement 与 step 对齐 | `wp4_engagement_step_alignment_notes_20260519.md` | 当前 producer 覆盖与 step-result 语义形状已记录，并标出 deferred slot。 |
| Policy 与 binding 对齐 | `wp4_policy_binding_alignment_notes_20260519.md` | 当前 adapter 已分类，且没有过早扩张 C++ binding。 |
| Facade evidence gates | `tests/runtime/engagement/test_facade_engagement_evidence_gates.py`、`tests/runtime/facade/test_facade_step_evidence_gates.py` | 聚焦测试覆盖当前 engagement export evidence 与 execution-step 形状。 |
| Agent metadata shim | `python/rl/runtime/agent_shim.py`、`tests/runtime/test_agent_shim.py` | 被动 Python compatibility scaffold 予以验收。 |
| Compatibility guard review | `wp4_compat_guard_notes_20260519.md` | 宽泛 raw-runtime ban 延后到 provenance label 与 allowlist 准备就绪之后。 |
| 集成交接 | `wp4_integration_handoff_20260519.md` | WP5 immediate gate 与 metadata-dependent gate 已分开。 |

## 3. 验证

WP4 记录的聚焦命令：

```bash
python -m py_compile python/rl/runtime/agent_shim.py tests/runtime/test_agent_shim.py
python -m pytest -q tests/runtime/test_agent_shim.py
python -m pytest -q tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/facade/test_facade_step_evidence_gates.py
```

此前报告的更宽聚焦命令：

```bash
python -m pytest -q tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/engagement/test_facade_engagement_export.py tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_diagnostics_trace_contract.py tests/runtime/facade/test_facade_step_evidence_gates.py tests/runtime/facade/test_runtime_facade.py
```

报告结果：`23 passed`。

## 4. 路由到 WP5 的剩余风险

以下项目不阻断 WP4 验收，因为它们需要 runtime metadata、新 maintained
producer 或更宽的验证策略：

1. `ObservationBatchPacket` 仍缺少类型化 runtime metadata 形式的 source-time、
   barrier 与 snapshot-version provenance。
2. `DecisionBelief` 仍是 policy/agent 侧概念，而不是 public C++ facade DTO。
3. Reward fact/shaping attribution 与 termination reason-source attribution
   尚未成为类型化契约。
4. `DiagnosticsTrace` 仍是 engagement export 内的 piggyback evidence，而不是专用
   diagnostics facade surface。
5. 宽泛 direct `sim.*` policy-path ban 需要 provenance label 与 allowlist 后才能安全强制。

## 5. 交接决定

WP5 可从已验收的 WP4 label 与 evidence gate 启动。WP5 第一波应盘点现有验证
覆盖、强化 design/boundary gate，并添加 trace/replay 检查，同时不重新打开
facade 语义。

WP4 状态应从 `active` 移为 `complete`；WP5 应成为 simulation-architecture 的活跃工作包。
