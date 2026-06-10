# WP3 交战试点 — 验收审查

状态：`2026-05-19` 验收审查完成。
范围：WP3 交战试点实现 — 契约、适配器、facade 导出、Python 绑定、测试、烟雾套件提升。

关联文档：

- [WP3 任务族](../../task/simulation_architecture/engagement_pilot_wp3_20260519.md)
- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.md)
- [WP1 流水线清单](../../task/simulation_architecture/pipeline_inventory_wp1_20260519.md)
- [WP2 契约冻结](../../task/simulation_architecture/contract_freeze_wp2_20260519.md)

## 1. 审查范围

- `src/runtime/contracts/engagement_contracts.h` — 7 个稳定 DTO（TrackPacket、LaunchRequest、LaunchEvent、MunitionLifecyclePacket、EffectsEvent、DamageReport、DiagnosticsTrace）
- `src/core/engine/weapon_launch_adapter.h` — header-only 转换接缝（7 个 snapshot 类型，7 个 inline 转换器）
- `src/runtime/facade/runtime_facade.h` / `.cpp` / `types.h` — EngagementBatchRequest、EngagementEventPacket、export_engagement_event_packet()
- `src/interfaces/python/bindings_runtime.cpp` — 通过 nanobind 暴露全部 7 个 DTO + EngagementEventPacket + RecentEngagementEvents
- `tests/runtime/engagement/` — 8 个文件中 24 个测试，覆盖契约形状、空中/海军适配器、生命周期、效果、损伤、诊断追踪、实时捕获、facade 导出
- `tests/runtime/facade/test_runtime_facade.py` — 10 个测试，包括 engagement packet shell 和导出验证
- `tests/architecture/` — 15 个分层和构建目标合规测试
- `tests/smoke/ci_smoke_suite.json` — engagement 测试目录提升为烟雾套件

## 2. 测试执行证据

```
tests/runtime/engagement/                    24 passed in 0.25s
tests/runtime/facade/test_runtime_facade.py   10 passed in 0.30s
tests/architecture/                           15 passed in 0.15s
────────────────────────────────────────────────────────
合计                                          49 passed, 0 failed
```

全部测试在本地运行，无需 RL 训练依赖。无 `torch`、`gym`、`gymnasium` 或任何 RL 模块的导入。

## 3. 验收闸门

### 闸门 1 — 跨平台家族共享 LaunchEvent 形状

**通过。** 空中挂架发射（F-16 硬挂点通过 `fire_missile()`）和海军舰炮/VLS 发射（DDG Mk45 舰炮通过 `fire_naval_weapon()` 和 DDG VLS 防空导弹通过 `fire_missile()`）均映射到**相同**的 `LaunchRequest` / `LaunchEvent` 类型对。

证据：
- [test_air_launch_adapter.py](../../../tests/runtime/engagement/test_air_launch_adapter.py) — `station_id="air:pylon"`、`requested_munition_family="missile"`
- [test_naval_launch_adapter.py](../../../tests/runtime/engagement/test_naval_launch_adapter.py) — `mount_id="mk45_gun"` 和 `mount_id="forward_vls_sam"`
- 两者均使用 `ef_py.LaunchRequest` 和 `ef_py.LaunchEvent`——无类型分叉

### 闸门 2 — 显式接受/拒绝原因

**通过。** `LaunchEvent.accepted` 是显式布尔字段。`LaunchEvent.rejection_reason` 携带原因字符串（拒绝时为 `"no_active_track"`，接受时为空字符串 `""`）。遗留 `fire_missile()` 返回的 `flecs::entity`（可为 0）不再作为维护契约路径。

证据：
- [test_air_launch_adapter.py:213](../../../tests/runtime/engagement/test_air_launch_adapter.py#L213)：拒绝发射断言 `rejection_reason == "no_active_track"`
- [test_naval_launch_adapter.py:325-326](../../../tests/runtime/engagement/test_naval_launch_adapter.py#L325-L326)：无航迹 VLS 场景断言 `rejection_reason == "no_active_track"`

### 闸门 3 — 弹药、冷却、发射器、弹药和血缘在事件字段中表示

**通过。** `LaunchEvent` 包含 `ammo_delta`、`cooldown_delta_s`、`selected_launcher`、`selected_munition`、`spawned_munition`（EngagementEntityRef）和 `has_spawned_munition`。`MunitionLifecyclePacket` 通过 `launch_event_id` 回链到发射事件。

证据：
- [test_naval_launch_adapter.py:225-226](../../../tests/runtime/engagement/test_naval_launch_adapter.py#L225-L226)：`ammo_delta == -1`、`cooldown_delta_s == 3.5`
- [test_air_launch_adapter.py:180-182](../../../tests/runtime/engagement/test_air_launch_adapter.py#L180-L182)：`ammo_delta == -1`、`cooldown_delta_s == 0.75`

### 闸门 4 — 弹药生命周期导出不暴露完整 ECS 内部细节

**通过。** `MunitionLifecyclePacket` 仅导出 17 个归一化语义字段（`seeker_mode`、`guidance_cadence_s`、`track_memory_state`、`fuel_remaining_fraction`、`burnout`、`max_flight_time_s`、`fuze_state` 等）。包含约 75 个字段的 `Missile` ECS 组件未泄露。

证据：
- [test_munition_damage_adapter.py:84-118](../../../tests/runtime/engagement/test_munition_damage_adapter.py#L84-L118)：从 `debug_get_missile_runtime_state()` 原始字典中选择性提取字段并归一化填入 `MunitionLifecyclePacket`

### 闸门 5 — 损伤可见性使用 DamageReport

**通过。** `DamageReport` 包含 `hp_delta`、`system_health_delta`、`platform_damage_state_delta`、`mission_kill`、`mobility_kill`、`sensor_kill`、`survivability_kill`、`loss_state_from`、`loss_state_to`、`destroyed`。不依赖原始 debug 健康读数作为公共契约。

证据：
- [test_munition_damage_adapter.py:209-226](../../../tests/runtime/engagement/test_munition_damage_adapter.py#L209-L226)：从健康/损伤状态构造 DamageReport，含语义 kill 状态映射
- [test_live_engagement_event_capture.py:163-188](../../../tests/runtime/engagement/test_live_engagement_event_capture.py#L163-L188)：`debug_apply_proximity_hit` 产生 EffectsEvent + DamageReport 对，`hp_delta < 0.0`，通过 `source_event_id` 链接

### 闸门 6 — DiagnosticsTrace 链连接

**通过。** `DiagnosticsTrace` 结构体包含 `trace_id`、`parent_trace_id`、`chain_id`、`track_id`、`launch_request_id`、`launch_event_id`、`munition`（EngagementEntityRef）、`effects_event_id`、`damage_report_id`、`observation_packet_version`。全部 7 个 link 字段经过端到端验证。

证据：
- [test_diagnostics_trace_contract.py:133-151](../../../tests/runtime/engagement/test_diagnostics_trace_contract.py#L133-L151)：验证每个 link 字段与单一链中对应 packet ID 匹配

### 闸门 7 — 显式 facade 和 Python 访问

**通过。** `RuntimeFacade::export_engagement_event_packet()` 是 facade 级 API。`RuntimeFacade::runtime()` 逃逸口带有文档注释："Compatibility escape hatch for diagnostics and legacy adapters only." Python 绑定将全部 7 个 DTO + `EngagementEventPacket` + `RecentEngagementEvents` 通过 `ef_py` 暴露。架构测试强制执行 facade 分层合规。

证据：
- `src/runtime/facade/runtime_facade.h:33-36`：显式逃逸口文档
- [test_runtime_facade_layering.py](../../../tests/architecture/runtime_facade)：9 个分层测试通过——逃逸口保持在适配器内、VecEnv 不缓存原始句柄、leader runtime 不触及原始 world 句柄、契约头文件不包含 engine 头文件

### 闸门 8 — 本地验证无需 RL 依赖

**通过。** 全部 49 个测试在 0.7 秒内完成。无 RL 导入。`ci_smoke_suite.json` 包含 `tests/runtime/engagement` 作为目录路径。

证据：
- `tests/smoke/ci_smoke_suite.json:7`：`"tests/runtime/engagement"` 条目
- 测试套件输出确认零 RL 导入

## 4. 分支交付物确认

| 分支 | 工件 | 状态 |
|------|------|------|
| WP3-A | `engagement_contracts.h`——7 个 DTO，无 `core/` 或 `engine/` include | 已验证：4 个 contract shape 测试通过 |
| WP3-B | `EngagementBatchRequest`、`EngagementEventPacket`、`export_engagement_event_packet()` | 已验证：2 个 facade export 测试通过，include flags 正确受控 |
| WP3-C | 全部 7 个 DTO + `RecentEngagementEvents` 的 Python 绑定 | 已验证：所有测试通过 `ef_py` 构造和读取 DTO 字段 |
| WP3-D | 空中挂架发射 → `LaunchRequest`/`LaunchEvent` | 已验证：2 个空中适配器测试（接受 + 拒绝） |
| WP3-E | 海军舰炮/VLS 发射 → 相同 `LaunchEvent` 形状 | 已验证：3 个海军适配器测试（舰炮接受 + VLS 接受 + VLS 拒绝） |
| WP3-F | 弹药生命周期和效果/损伤适配器 | 已验证：2 个测试（生命周期归一化 + 合成效果/损伤） |
| WP3-G | 诊断追踪全链连接 | 已验证：1 个测试验证 7 个 link 字段 |
| WP3-H | 烟雾套件提升 | 已验证：`ci_smoke_suite.json` 包含 `tests/runtime/engagement` |
| WP3-I | 集成和文档 | 已验证：49 个测试绿色，无共享文件冲突 |

## 5. WP3 验收范围外（文档标明的后续工作）

参照 [WP3 任务文档第 9 节](../../task/simulation_architecture/engagement_pilot_wp3_20260519.md#L236-L242)：

1. **真实导弹终端效果/损伤捕获。** 当前覆盖：legacy launch、naval direct-fire、debug proximity-hit 路径。来自 maintained guidance/effects 系统的终端效果留给 WP4/WP5。
2. **Recent-event 存储策略。** 目前为 bounded compatibility buffer（`kMaxRecentEngagementEvents = 64`）。是否迁移到 formal event queue owner 留给 WP4/WP5 决策。

## 6. 架构对齐评估

实现遵循架构基线中记录的架构设计规则：

- **法则 #3**（组件是数据契约）：`engagement_contracts.h` 是纯 DTO，无 per-tick 行为。
- **法则 #7**（facade 不复制每个 kernel 方法）：`export_engagement_event_packet()` 是用例级 API，非 1:1 kernel 方法镜像。
- **法则 #8**（接口和 Python 适配器只做格式转换）：`weapon_launch_adapter.h` 是 header-only 转换接缝，无仿真语义。
- **法则 #10**（领域扩展声明 pipeline 参与）：`LaunchRequest` 和 `LaunchEvent` 覆盖 `P7 FireControlLaunch`，`MunitionLifecyclePacket` 覆盖 `P8 MunitionLifecycle`，`EffectsEvent` 和 `DamageReport` 覆盖 `P9 EffectsDamage`，`DiagnosticsTrace` 覆盖 `P10 ObservationExport`。

架构的 temporal DAG 目标与当前线性 `ecs.progress()` 执行之间的差距已在架构文档本身中确认（法则 #11），并被跟踪在 WP4/WP5 下——这不在 WP3 范围内。

## 7. 结论

WP3 满足全部 8 项验收闸门，且已通过验收。跨领域交战生命周期——空中挂架发射和海军舰炮/VLS 发射——共享一个类型化契约词汇表，未产生 "air weapon" 或 "naval weapon" 私有运行时路径。契约层对 `core/engine/*` 零依赖。Facade 访问是显式的，逃逸口已文档化。诊断可以解释从 track 到 observation 的完整链条。本地验证无需 RL 依赖即可运行。WP4/WP5 项目属于 WP3 验收范围外。
