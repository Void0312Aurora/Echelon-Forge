# WP5-C Trace 与 Replay Gate 笔记

状态：`2026-05-19` 聚焦 gate 已完成。

语言版本：

- 英文主文：[wp5_trace_replay_gates_notes_20260519.md](wp5_trace_replay_gates_notes_20260519.md)
- 中文辅文：`wp5_trace_replay_gates_notes_20260519.zh.md`

输入：

- [WP5-C trace/replay 分发单](wp5_trace_replay_cluster_20260519.zh.md)
- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)
- [WP4 facade 对齐验收审查](../review/wp4_facade_alignment_acceptance_review_20260519.zh.md)
- [WP4-G facade evidence 笔记](wp4_facade_evidence_notes_20260519.md)
- [WP4-B/C engagement-step 对齐笔记](wp4_engagement_step_alignment_notes_20260519.md)

## 1. 决定

WP5-C 应验证今天已经存在的 replay evidence，而不能把 WP2.5/WP4 推迟的
metadata 变成误报失败。第一条 gate 是
`tests/runtime/engagement/test_trace_replay_gates.py`。

该 gate 将 `DiagnosticsTrace` 视为 `EngagementEventPacket` 携带的 piggyback
evidence。它不新增也不要求专用 diagnostics facade query。

## 2. 当前 Trace 覆盖

| Evidence path | 当前 gate | 状态 |
|---------------|-----------|------|
| Launch event ids | 验证导出的 launch event 携带正数 `event_id` / `request_id`、accepted status、spawned munition ref 与非负 event time。 | Maintained compatibility-buffer evidence。 |
| Launch diagnostics ancestry | 验证 diagnostics trace 连接 `launch_event_id`、`launch_request_id`、`chain_id` 与 spawned munition。 | Piggyback evidence。 |
| Effects event ids | 验证 effects event 携带正数 `event_id`、target ref、munition ref、hit outcome 与非负 detonation time。 | Maintained compatibility-buffer evidence。 |
| Damage ancestry | 验证 damage report 的 `source_event_id` 指向 effects event，并携带 target/time/damage data。 | Maintained compatibility-buffer evidence。 |
| Effects/damage diagnostics ancestry | 验证 diagnostics trace 连接 `effects_event_id`、`damage_report_id`、`chain_id` 与 munition。 | Piggyback evidence。 |
| Per-slot replay sorting | 验证 launch/effects/damage/diagnostics vector 按当前暴露 id 排序。 | 当前 replay-sortable metadata。 |
| Track snapshot evidence | 验证 live track packet 暴露正数 `track_id`、`snapshot_version` 与非负 `source_time_s`。 | 仅限当前 track-level metadata。 |

该 gate 有意不要求完整 live `LaunchEvent -> EffectsEvent -> DamageReport` 链。
当前 producer 可以在同一 export 中记录 launch trace 与 effects/damage trace，但
effects/damage trace 不保证保留前序 launch id，除非 runtime producer 设置
`pending_effects_launch_event_id_`。完整 launch-to-damage ancestry gate 推迟到该
producer contract 成为 maintained 之后。

## 3. Replay Metadata 边界

| Metadata | 当前可用性 | WP5-C 处理 |
|----------|------------|------------|
| Per-slot ids | `LaunchEvent.event_id`、`EffectsEvent.event_id`、`DamageReport.report_id` 与 `DiagnosticsTrace.trace_id`。 | 当前要求。 |
| Per-slot sorted export | `SimulationKernel::export_recent_engagement_events()` 按相关 id 对各 slot 排序。 | 当前要求。 |
| Track snapshot id | live facade track export 中存在 `TrackPacket.snapshot_version`。 | 仅要求 track packets。 |
| Track source time | live facade track export 中存在 `TrackPacket.source_time_s`。 | 仅要求 track packets。 |
| Diagnostics observation version | `DiagnosticsTrace.observation_packet_version` 存在，但只为 live track diagnostics 填充，不覆盖所有 recent traces。 | 要求字段存在，不要求所有 trace 非零。 |
| Packet-level snapshot version | `EngagementEventPacket` 或 `ObservationBatchPacket` 上不存在。 | 推迟。 |
| Packet-level barrier/window id | 当前 packet DTO 不存在。 | 推迟。 |
| Packet-level source time | 当前 packet DTO 不存在。 | 推迟。 |
| Cross-slot total ordering | 没有统一 event sequence 字段。 | 推迟。 |

第二条 gate 断言当前不要假设这些 deferred packet-level 字段。这可以防止 DTO 支持
出现前，过早提升 metadata-dependent replay 测试。

## 4. Diagnostics 边界

`DiagnosticsTrace` 仍是 engagement export 内的 piggyback 字段：

- Maintained：调用者可通过 `RuntimeFacade::export_engagement_event_packet`
  请求 `EngagementEventPacket.diagnostics_traces`。
- Compatibility adapter：`RuntimeFacade::runtime()` 与
  `SimulationKernel::export_recent_engagement_events()` 仍可用于 legacy tests
  与低层 evidence production。
- Diagnostics-only：debug damage helper 与 raw recent buffer 可以为测试创建
  oracle-like evidence，但它们不是 policy input surface。
- Deferred：WP5-C 不要求 `export_diagnostics_packet`、
  `export_diagnostics_trace_packet`、`export_diagnostics_traces` 或
  `get_diagnostics_traces` facade method。

## 5. Smoke 候选

推荐 WP5-C 聚焦命令：

```bash
python -m pytest -q tests/runtime/engagement/test_trace_replay_gates.py
```

WP5-A/B 确定 suite shape 后，推荐 integration smoke 候选：

```bash
python -m pytest -q \
  tests/runtime/engagement/test_trace_replay_gates.py \
  tests/runtime/engagement/test_facade_engagement_evidence_gates.py \
  tests/runtime/engagement/test_live_engagement_event_capture.py \
  tests/runtime/engagement/test_diagnostics_trace_contract.py \
  tests/runtime/facade/test_facade_step_evidence_gates.py
```

在 maintained facade DTO 携带 packet-level snapshot/barrier/source-time 字段前，
不要把这些检查提升进 smoke。

## 6. Deferred Gates

以下项目需要 runtime semantic 或 DTO 支持，不应在 WP5-C 内解决：

- 当 damage producer 尚未通过 maintained launch-aware path 调用时，完整
  live launch-to-effects-to-damage ancestry。
- `ObservationBatchPacket` 与 `EngagementEventPacket` 的 packet-level snapshot provenance。
- injection、stage publish、window commit 与 export visibility 之间的
  barrier/window/source-time provenance。
- replay comparison 所需的 unified cross-slot event ordering。
- 与 engagement piggyback evidence 分离的专用 diagnostics facade query。
