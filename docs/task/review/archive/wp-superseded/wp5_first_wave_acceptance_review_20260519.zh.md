# WP5 第一波验收审查

状态：`2026-05-19` 第一波验收已完成。

范围：WP5-A harness inventory、WP5-B design/boundary gates 与 WP5-C trace/replay gates。

相关文档：

- [WP5 验证套件](../simulation_architecture/validation_harness_wp5_20260519.zh.md)
- [WP5-A harness inventory 笔记](../simulation_architecture/wp5_harness_inventory_notes_20260519.zh.md)
- [WP5-B design/boundary 笔记](../simulation_architecture/wp5_design_boundary_notes_20260519.zh.md)
- [WP5-C trace/replay gates 笔记](../simulation_architecture/wp5_trace_replay_gates_notes_20260519.zh.md)
- [WP4 facade 对齐验收审查](wp4_facade_alignment_acceptance_review_20260519.zh.md)

## 1. 验收决定

WP5 第一波工作予以验收。

第一波成功把 WP4 facade baseline 转成维护中的 validation evidence，且没有重新打开
runtime 语义。它盘点了当前 harness，新增 design/boundary guard，并增加
trace/replay-facing engagement gate，同时保持 metadata-dependent checks deferred。

## 2. 已验收产物

| 领域 | 产物 | 验收备注 |
|------|------|----------|
| Harness inventory | `wp5_harness_inventory_notes_20260519.md` | 作为当前 tier map、smoke membership review 与 immediate-vs-metadata-dependent gap register 验收。 |
| Design/boundary guards | `tests/architecture/test_wp5_design_boundary_gates.py` | 作为 maintained facade header isolation、escape-hatch containment、facade README language 与避免过早 broad `sim.*` ban 的聚焦 guard 验收。 |
| Design/boundary notes | `wp5_design_boundary_notes_20260519.md` | 作为 smoke candidate 与 deferred-boundary handoff 验收。 |
| Trace/replay gates | `tests/runtime/engagement/test_trace_replay_gates.py` | 作为当前 launch/effects/damage/diagnostics ancestry 与 replay-sortable id 的聚焦覆盖验收。 |
| Trace/replay notes | `wp5_trace_replay_gates_notes_20260519.md` | 作为当前 metadata boundary 与 diagnostics-piggyback handoff 验收。 |

## 3. 验证

主线程验证：

```bash
python -m pytest -q tests/architecture/test_wp5_design_boundary_gates.py tests/architecture/runtime_facade/test_layering.py tests/runtime/facade
```

结果：`26 passed`。

```bash
python -m pytest -q tests/runtime/engagement/test_trace_replay_gates.py tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_diagnostics_trace_contract.py tests/runtime/facade/test_facade_step_evidence_gates.py
```

结果：`12 passed`。

```bash
python -m pytest -q tests/runtime/test_agent_shim.py
```

结果：`6 passed`。

主线程审阅的第一波文档与测试通过 `git diff --check`。

## 4. 剩余风险

以下项目作为 WP5-D/E 或后续工作验收，不阻断第一波：

1. Information/belief leakage 仍需要 maintained-path label 与谨慎的
   compatibility/diagnostics allowlist。
2. `ObservationBatchPacket` 与 `EngagementEventPacket` 仍缺 packet-level
   snapshot、barrier、source-time 与 unified event-sequence metadata。
3. `DecisionBelief`、typed `RewardReport` 与 typed termination reason-source
   attribution 仍依赖 metadata/DTO。
4. `DiagnosticsTrace` 仍是 piggyback evidence，而不是专用 diagnostics facade surface。
5. Smoke-suite promotion 有意留给 WP5-D 返回后的 WP5-E 串行集成。

## 5. 交接决定

WP5 应继续推进：

1. `WP5-D Information And Belief Gates` 作为下一条高推理 worker stream。
2. `WP5-E Smoke Promotion And Docs` 作为 WP5-D 回报候选测试与 allowlist 边界后的串行集成 stream。
