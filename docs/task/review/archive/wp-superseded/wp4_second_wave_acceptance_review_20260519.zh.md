# WP4 第二波验收审查

状态：`2026-05-19` 第二波验收完成。

范围：WP4-G facade evidence gates、WP4-H information/agent shim、WP4-I compatibility guard review。

相关文档：

- [WP4 第一波验收审查](wp4_first_wave_acceptance_review_20260519.zh.md)
- [WP4-G facade evidence 笔记](../simulation_architecture/wp4_facade_evidence_notes_20260519.md)
- [WP4-H agent shim 实现笔记](../simulation_architecture/wp4_agent_shim_implementation_notes_20260519.md)
- [WP4-I compatibility guard 笔记](../simulation_architecture/wp4_compat_guard_notes_20260519.zh.md)
- [WP4 facade 对齐](../simulation_architecture/facade_alignment_wp4_20260519.zh.md)

## 一、验收结论

WP4 第二波工作予以验收。

第二波把 WP4 从纯文档 discovery 推进到了聚焦证据与最小兼容脚手架：

1. Facade evidence gates 已覆盖 engagement producer coverage、deferred placeholder、diagnostics piggyback、multi-world retagging 与当前 execution-step semantic shape。
2. 已存在 passive Python-side `AgentRole` / intent / provenance shim，且不改变 policy inference，也不新增 public C++ binding。
3. Compatibility guard 覆盖已完成审查，并分阶段安排到 WP5 在 provenance metadata 可用后强化 leakage checks。

## 二、接受的产物

| 领域 | 产物 | 验收说明 |
|------|------|----------|
| Engagement evidence gates | `tests/runtime/engagement/test_facade_engagement_evidence_gates.py` | 作为 producer coverage、deferred placeholder、piggyback diagnostics 与 multi-world effects/damage/trace retagging 的 WP4 聚焦 guard 予以接受。 |
| Step semantic gate | `tests/runtime/facade/test_facade_step_evidence_gates.py` | 作为当前 `ExecutionBatchStepResult` shape 的 guard 予以接受，不强迫新增 DTO 字段。 |
| Agent shim | `python/rl/runtime/agent_shim.py` 与 `tests/runtime/test_agent_shim.py` | 作为 passive compatibility scaffolding 予以接受。它不提升新的 public C++ facade 或 binding surface。 |
| Guard review | `wp4_compat_guard_notes_20260519.md` | 作为当前 compatibility boundary assessment 与 WP5 handoff basis 予以接受。 |

## 三、验证

主线程重复运行了窄检查：

```bash
python -m py_compile python/rl/runtime/agent_shim.py tests/runtime/test_agent_shim.py
python -m pytest -q tests/runtime/test_agent_shim.py
python -m pytest -q tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/facade/test_facade_step_evidence_gates.py
```

结果：

- `tests/runtime/test_agent_shim.py`：`6 passed`。
- WP4-G facade evidence gates：`4 passed`。

## 四、剩余风险

这些不阻塞 WP4 第二波验收，但必须保留在 WP4-F/WP5 handoff 中：

1. `ObservationBatchPacket` 仍缺完整 WP2.5 snapshot/barrier/source-time provenance 字段。
2. Reward fact/shaping attribution 仍是 JSON/string shape，不是 typed `RewardReport`。
3. Termination reason source 尚未 typed。
4. `DiagnosticsTrace` 仍是 engagement-piggyback evidence，不是 dedicated diagnostics facade surface。
5. 对所有 policy path 的 direct `sim.*` ban 必须等待 provenance label 与 allowlist 成熟。

## 五、移交决定

WP4 现在应进入 `WP4-F Integration And Docs`：

1. 把第一波与第二波已验收发现整合进 WP4 任务文档；
2. 记录聚焦验证命令；
3. 将 deferred DTO/runtime metadata 项标为 WP5 或 post-WP4 follow-up；
4. 集成后准备最终 WP4 验收审查。
