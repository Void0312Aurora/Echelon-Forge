# WP4-F 集成与交接

状态：`2026-05-19` 集成交接已完成；WP4 最终验收已发布。

语言版本：

- 英文主文：[wp4_integration_handoff_20260519.md](wp4_integration_handoff_20260519.md)
- 中文辅文：`wp4_integration_handoff_20260519.zh.md`

输入：

- [WP4 facade 对齐](facade_alignment_wp4_20260519.zh.md)
- [WP4 第一波验收审查](../review/wp4_first_wave_acceptance_review_20260519.zh.md)
- [WP4 第二波验收审查](../review/wp4_second_wave_acceptance_review_20260519.zh.md)
- [WP4-A surface inventory 初稿](wp4_surface_inventory_wp4a_20260519.zh.md)
- [WP4-G facade evidence 笔记](wp4_facade_evidence_notes_20260519.md)
- [WP4-H agent shim 实现笔记](wp4_agent_shim_implementation_notes_20260519.md)
- [WP4-I compatibility guard 笔记](wp4_compat_guard_notes_20260519.zh.md)

## 1. 集成摘要

WP4 已经产出维护中的 facade 对齐基线、聚焦 evidence gate，以及被动
Python 侧 metadata shim，且没有重新打开仿真语义。

已验收的 WP4 产物：

| 产物 | 状态 | 备注 |
|------|------|------|
| Surface inventory | 作为 WP4-A 词汇输入验收。 | 分类 maintained、compatibility、diagnostics-only 与 deferred surface。 |
| Engagement/step 对齐笔记 | 作为有边界证据验收。 | 记录 producer 覆盖、deferred slot、diagnostics piggyback 与 step/lifecycle 缺口。 |
| Policy/binding 对齐笔记 | 作为 discovery 输入验收。 | 将当前 adapter 映射到 `AgentRole`、intent、observation 与 compatibility 分类。 |
| Facade evidence tests | 已验收并本地验证。 | 为 engagement export 与 step-result 语义形状添加聚焦 guard。 |
| 被动 agent shim | 已验收并本地验证。 | 新增 Python-only `AgentRole`、`ActionIntentCompat`、`CoordinationIntentCompat` 与 `ObservationProvenance` shell。 |
| Compatibility guard notes | 作为当前 guard review 验收。 | 在 provenance label 与 allowlist 成熟前，暂缓宽泛 direct `sim.*` ban。 |

## 2. 维护中的 WP4 验证命令

主线程已验证的聚焦命令：

```bash
python -m py_compile python/rl/runtime/agent_shim.py tests/runtime/test_agent_shim.py
python -m pytest -q tests/runtime/test_agent_shim.py
python -m pytest -q tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/facade/test_facade_step_evidence_gates.py
```

worker 已验证的更宽聚焦命令：

```bash
python -m pytest -q tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/engagement/test_facade_engagement_export.py tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_diagnostics_trace_contract.py tests/runtime/facade/test_facade_step_evidence_gates.py tests/runtime/facade/test_runtime_facade.py
```

worker 报告结果：`23 passed`。

## 3. WP5 交接

WP5 可以立即验证：

1. engagement producer 覆盖与 step-result 形状的 facade evidence gate。
2. Agent shim metadata 分类，以及非法 status / merge-policy 拒绝。
3. Raw runtime escape hatch 文档与既有 architecture-layering guard。
4. 作为 piggyback evidence 的 engagement diagnostics。
5. 作为 validation label 的 surface inventory 分类。

WP5 应等待 runtime/facade metadata 后再强制：

1. `ObservationViewSpec` schema compatibility 作为 runtime DTO。
2. `ObservationPacket` source `SnapshotVersion`、barrier 与 source-time provenance。
3. 类型化 `DecisionBelief` provenance。
4. C++ binding 中类型化 `AgentRole` authority / action-interface metadata。
5. 类型化 `RewardReport` fact/shaping attribution。
6. 类型化 termination reason-source attribution。
7. 专用 diagnostics facade surface 要求。

## 4. Deferred 或 Post-WP4 项

| 项目 | 路由 |
|------|------|
| `launch_requests` 与 `munition_lifecycle_packets` engagement producer | 当 maintained producer 存在后再添加 producer 与 retagging 测试。 |
| 专用 `DiagnosticsTrace` facade surface | 交由 WP5 trace conformance 决策，或后续 diagnostics 架构工作。 |
| Runtime `ObservationViewSpec` DTO | 交由 WP5 information-state metadata enforcement，或后续 facade DTO 工作。 |
| `AgentRole`、`DecisionBelief`、`ActionIntentPacket`、`CoordinationIntentPacket` 的 C++ binding | 等待 WP4-A 名称与 DTO 字段稳定到足以暴露 maintained API。 |
| 宽泛 direct `sim.*` ban | 在 agent/provenance shim 被 maintained adapter 采用后，再添加基于 allowlist 的 AST guard。 |
| `RuntimeFacade` 拆分 | 仅当 maintained public method 数量越过已记录阈值时触发规划。 |

## 5. 最终验收建议

在索引同步、最终验收发布与最终 `git diff --check` 之后，WP4 可进入 WP5 validation。

最终验收发布条件：

1. 所有已验收 WP4 产物均已进入索引。
2. 聚焦 WP4 测试在本地通过。
3. Compatibility-only 与 diagnostics-only 路径仍与 maintained policy/training truth 明确分离。
4. WP5 交接分别列出 immediate gate 与 metadata-dependent gate。
