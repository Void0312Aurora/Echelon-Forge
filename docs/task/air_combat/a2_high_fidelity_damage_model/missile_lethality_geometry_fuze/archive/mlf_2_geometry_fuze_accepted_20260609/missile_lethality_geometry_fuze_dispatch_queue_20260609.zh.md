# A2 MLF-2 派发队列

状态：`2026-06-09` archived dispatch queue；`MLF-2B`、`MLF-2C`、`MLF-2D`、`MLF-2E`、`MLF-2F` 和 `MLF-2G` 已验收，当前没有运行中的派发包。

英文辅文：[missile_lethality_geometry_fuze_dispatch_queue_20260609.md](missile_lethality_geometry_fuze_dispatch_queue_20260609.md)

父任务簇：[missile_lethality_geometry_fuze_task_clusters_20260609.zh.md](missile_lethality_geometry_fuze_task_clusters_20260609.zh.md)

## 边界

本队列只用于 MLF-2 接近几何和引信评估。任何派发都不得创建新的会话线程，不得进入破片、连续杆、结构解体、残骸、Pk 或 AIM-120C/MQ-9 个案校准。

## 已派发包

| Packet | Cluster | Assignee | Write set | Required output | Status |
| --- | --- | --- | --- | --- | --- |
| `MLF-2B-X1` | `MLF-2B Controlled Geometry Fixtures` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | read-only inspection; no runtime/test/probe edits in this packet | 找出最短受控几何路径，说明现有代码是否已有可复用 fixture；本包只读，不实现引信物理。 | accepted |
| `MLF-2B-W1` | `MLF-2B Controlled Geometry Fixtures` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | `tests/runtime/air_combat/weapon_guidance_realism/geometry_fixtures.py`；`tests/runtime/air_combat/test_weapon_guidance_realism_guards.py` | 实现最小 live missile 受控几何测试夹具，至少改变距离/方位/闭合速度/高度差中的两项，并只验证几何观测。 | accepted |
| `MLF-2C-X1` | `MLF-2C NearestApproachEvent Writer` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | read-only writer-path audit; no runtime/contract/test edits | 找出 live missile lifecycle 中写入 `NearestApproachEvent` 的最小 producer 路径。 | accepted |
| `MLF-2C-W1` | `MLF-2C NearestApproachEvent Writer` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | `src/components/combat/weapon.h`；`src/core/interfaces/engagement_event_recorder.h`；`src/core/engine/simulation_kernel_engagement_event_store.h`；`src/core/engine/simulation_kernel_engagement_event_store.cpp`；`src/core/engine/simulation_kernel_weapon_release_service.cpp`；`src/interfaces/python/bindings_core.cpp`；`src/systems/combat/damage_system.h`；相关 geometry/fuze tests | 写入最近接近事件，未起爆也能记录最近点和原因；最近点时间取自最近点刷新时刻。 | accepted |
| `MLF-2D-X1` | `MLF-2D FuzeEvaluationEvent Writer` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | read-only writer-path audit; no runtime/contract/test edits | 找出 live missile lifecycle 中写入 `FuzeEvaluationEvent` 的最小 producer 路径。 | accepted |
| `MLF-2D-W1` | `MLF-2D FuzeEvaluationEvent Writer` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | `src/core/interfaces/engagement_event_recorder.h`；`src/core/engine/simulation_kernel_engagement_event_store.h`；`src/core/engine/simulation_kernel_engagement_event_store.cpp`；`src/systems/combat/damage_system.h`；相关 geometry/fuze tests | 写入解保、触发、未触发、延迟和失败原因。 | accepted |
| `MLF-2E-X1` | `MLF-2E Diagnostics Projection` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | read-only diagnostics/probe path audit; no runtime edits | 找出 process probe/诊断导出消费最近接近和引信评估事件的最小路径。 | accepted |
| `MLF-2E-W1` | `MLF-2E Diagnostics Projection` | main thread | `tools/diagnostics/air_combat_stage0_process_probe.py`；`tests/runtime/air_combat/test_diagnostics_probe_contracts.py` | 导出每枚弹的几何/引信阶段行，不依赖旧 `last_effect_*`。 | accepted |
| `MLF-2F-I1` | `MLF-2F Runtime Handoff Gate` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | read-only weapon lifecycle/effects invocation audit; no runtime edits | 审计起爆才进入效果模型、未触发路径有事件有原因无效果的最小 gate。 | accepted |
| `MLF-2F-W1` | `MLF-2F Runtime Handoff Gate` | main thread | `tests/runtime/air_combat/weapon_guidance_realism/fuze.py` | 用测试钉住 runtime handoff gate：触发路径一次效果/损伤记录，接触近失无效果/损伤记录，可靠性失败为零伤害过渡记录。 | accepted |
| `MLF-2G-C1` | `MLF-2G Acceptance And Archive Prep` | main thread | this subproject README/status/task cluster/dispatch queue/archive index; A2 README | 汇总证据，更新 accepted/held 状态和后续残余地图。 | accepted |

## 当前派发建议

当前没有运行中的派发包。`MLF-2G-C1` 已验收；本队列随 MLF-2 归档关闭。

后续不得在本队列中新增 runtime 功能、战斗部效果，或把 MLF-2 结论扩展成击毁、碎裂或 Pk 结论。

## 已返回派发包记录

### MLF-2B-X1

Worker 返回 `pass`，未修改文件。

- 可用最短路径：复用 live `sim.fire_missile`、`_spawn_geometry_pair`、truth-track 驱动和现有 `EffectsEvent` 几何字段。
- 可控项：初始距离、方位/侧向位置、闭合速度、高度差；目标 pitch/roll 在 live helper 中仍是限制项。
- 标准 `NearestApproachEvent` / `FuzeEvaluationEvent` 已声明/绑定，但当前搜索未发现 live writer。
- 结论：可以进入 `MLF-2B-W1` 最小测试夹具；`MLF-2C` 仍需等待 W1 几何 fixture 验收。

### MLF-2B-W1

Worker 返回 `pass`，主线程复验通过。

- 触碰文件：`tests/runtime/air_combat/weapon_guidance_realism/geometry_fixtures.py`、`tests/runtime/air_combat/test_weapon_guidance_realism_guards.py`。
- 可控项：距离、闭合速度、方位/侧向位置、高度差。
- 观测项：初始 truth detection 的 range/closing_speed/bearing/elevation，missile runtime 的 `proximity_min_dist_m`，以及 `EffectsEvent.nearest_approach_time_s`、`closure_mps`、`detonation_local_up_m`、`miss_distance_m`。
- 主线程复验：`py_compile` 通过；2 个聚焦 pytest 通过；相关 diff check 通过。
- 限制：目标 pitch/roll 尚未进入 live `_spawn_geometry_pair`；标准 `NearestApproachEvent` / `FuzeEvaluationEvent` writer 仍未 live。

### MLF-2C-X1

Worker 返回 `pass`，未修改文件。

- 标准 `NearestApproachEvent` / `FuzeEvaluationEvent` 结构、容器和 Python 绑定已存在。
- 当前没有 live `nearest_approach_events.push` / writer 路径；event store 只写 launch、effects 和 damage。
- 推荐实现：在 `engagement_event_recorder` 增加最近接近 record 接口，由 event store 分配 event id、解析 launch/chain/parent，再 push/cap/sort `nearest_approach_events`。
- 推荐调用点：`damage_system.h` 的 `ProximityFuze` pass-by / fuze 决策点，已经有 nearest local point、miss distance、closure 和目标信息。
- 限制：guidance max-flight-time 过期目前没有 recorder access，不能在 W1 中声称覆盖。

### MLF-2C-W1

Worker 返回 `pass`；主线程复验通过，并补充最近点时间字段后重新复验。

- 触碰文件：`src/components/combat/weapon.h`、`src/core/interfaces/engagement_event_recorder.h`、`src/core/engine/simulation_kernel_engagement_event_store.h`、`src/core/engine/simulation_kernel_engagement_event_store.cpp`、`src/core/engine/simulation_kernel_weapon_release_service.cpp`、`src/interfaces/python/bindings_core.cpp`、`src/systems/combat/damage_system.h`、`tests/runtime/air_combat/weapon_guidance_realism/geometry_fixtures.py`、`tests/runtime/air_combat/weapon_guidance_realism/fuze.py`、`tests/runtime/air_combat/test_weapon_guidance_realism_guards.py`。
- 实现内容：新增最近接近 recorder 接口和 event-store writer；导出排序包含 `nearest_approach_events`；`damage_system.h` 在错过触发半径、无终端跟踪、引信未起爆和引信解保路径写入最近接近事件。
- 主线程补充：`Missile` 增加 `proximity_min_time_s`，最近点刷新时同步写入；最近接近事件和旧效果事件使用该时间，而不是统一使用终端判定帧时间。
- 主线程复验：`py_compile` 通过；`cmake --build build-workshop --target ef_py -j2` 通过；3 个导弹几何/引信聚焦 pytest 通过；`tests/runtime/engagement/test_live_engagement_event_capture.py -q` 7 个测试通过；相关 diff check 通过。
- 限制：未实现 `FuzeEvaluationEvent` writer；max-flight-time 过期仍缺 recorder access；旧 `EffectsEvent` 字段仍是过渡观察面。

### MLF-2D-X1

Worker 返回 `pass`，未修改文件；主线程复核事件结构和绑定存在。

- 已存在：`src/runtime/contracts/engagement_contracts.h` 的 `FuzeEvaluationEvent`；`engagement_event_types.h`、`runtime_facade_types.h` 的 `fuze_evaluation_events` 容器；`bindings_runtime.cpp` 和 `bindings_core.cpp` 的 Python 绑定。
- 缺口：没有 `record_fuze_evaluation_event(...)` recorder 接口；event store 没有 writer/push/cap；`export_recent_events_sorted()` 没有排序 `fuze_evaluation_events`。
- 推荐实现：新增 `EngagementFuzeEvaluationEventRecord`，由 event store 分配 id、解析 launch chain，并优先把 parent 指向同枚弹最近的 `NearestApproachEvent`。
- 推荐调用点：`damage_system.h` 的 `miss_outside_trigger_radius`、`fuze_no_terminal_track`、`fuze_no_detonation` 和 `fuze_armed` 分支。
- 限制：max-flight-time 过期仍没有 recorder access；timed fuze 需要作为 W1 可选/held 决定，不能混同为最近接近路径。

### MLF-2D-W1

Worker 返回 `pass`；主线程复验通过。

- 触碰文件：`src/core/interfaces/engagement_event_recorder.h`、`src/core/engine/simulation_kernel_engagement_event_store.h`、`src/core/engine/simulation_kernel_engagement_event_store.cpp`、`src/systems/combat/damage_system.h`、`tests/runtime/air_combat/weapon_guidance_realism/geometry_fixtures.py`、`tests/runtime/air_combat/weapon_guidance_realism/fuze.py`、`tests/runtime/air_combat/test_weapon_guidance_realism_guards.py`。
- 实现内容：新增 `EngagementFuzeEvaluationEventRecord` 和 `record_fuze_evaluation_event(...)`；event store 写入、裁剪并排序 `fuze_evaluation_events`；优先把 parent 指向同枚弹最近的 `NearestApproachEvent`。
- 分支覆盖：`miss_outside_trigger_radius`、`fuze_no_terminal_track`、`fuze_no_detonation`、`fuze_armed` 各写一条引信评估事件；延迟起爆后续 damage application 不重复写第二条。
- 主线程复验：`py_compile` 通过；`cmake --build build-workshop --target ef_py -j2` 通过；4 个导弹几何/引信聚焦 pytest 通过；`tests/runtime/engagement/test_live_engagement_event_capture.py -q` 7 个测试通过；相关 diff check 通过。
- 限制：timed fuze evaluation 仍 held；max-flight-time 过期仍缺 recorder access；诊断 probe 尚未消费 `FuzeEvaluationEvent`。

### MLF-2E-X1

Worker 返回 `pass`，未修改文件。

- 现状：`tools/diagnostics/air_combat_stage0_process_probe.py` 已有 `nearest_approach` 和 `fuze` 诊断行，但此前主要从 `EffectsEvent` 投影；无 `EffectsEvent` 的未触发/近失路径不能完整读出。
- 缺口：probe 尚未消费 `nearest_approach_events` 和 `fuze_evaluation_events`。
- 推荐实现：标准事件优先，旧 `EffectsEvent` 投影只在同一 chain/munition 缺少标准 nearest/fuze 行时作为回退。
- 限制：不改 runtime 物理、不改效果模型、不改 reward、不推断击毁/坠毁/Pk。

### MLF-2E-W1

主线程实现并验收。

- 触碰文件：`tools/diagnostics/air_combat_stage0_process_probe.py`、`tests/runtime/air_combat/test_diagnostics_probe_contracts.py`。
- 实现内容：`_lethality_chain_rows()` 优先投影 `NearestApproachEvent` / `FuzeEvaluationEvent`；旧 `EffectsEvent` nearest/fuze 投影只作为同一 chain/munition 缺省回退；新增诊断字段包括 `closure_mps`、`aspect_bucket`、`fuze_armed`、`fuze_triggered`、`fuze_failure_reason`、`fuze_reliability`、`fuze_sample` 和接触证据。
- 测试覆盖：标准事件-only 未起爆路径；标准事件存在时抑制旧效果事件 nearest/fuze 重复投影；既有 fallback 和 CSV 输出保持。
- 主线程复验：`py_compile` 通过；`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q` 17 个测试通过。
- 限制：platform/lifecycle 仍来自 `DamageReport` 投影；未实现 runtime handoff gate；不改变 reward 或效果模型。

### MLF-2F-I1

Worker 返回 `pass`，未修改文件。

- 效果模型调用点：`damage_system.h` 中 `fuze_delay_armed` 且到达 `fuze_detonation_time_s` 后调用 `effects_ref->model->on_proximity_hit(...)`。
- 触发路径：`fuze_armed` 写入最近接近和引信评估事件，随后只在延迟解析块进入现有效果模型，并记录一次 `EffectsEvent` / `DamageReport`。
- 未触发路径：`miss_outside_trigger_radius` 写事件后销毁导弹，不调用效果模型，不写效果/损伤报告；`fuze_no_terminal_track` 和 `fuze_no_detonation` 不调用效果模型，但仍保留零伤害过渡 `EffectsEvent` / `DamageReport`。
- 限制：timed fuze 标准事件覆盖仍 held；max-flight-time / guidance expiry 仍缺 recorder access。

### MLF-2F-W1

主线程测试硬化并验收。

- 触碰文件：`tests/runtime/air_combat/weapon_guidance_realism/fuze.py`。
- 实现内容：收紧现有引信测试，确认延迟触发路径只有一条最近接近、一条引信评估、一条效果事件和一条损伤报告；可靠性失败为一条零伤害过渡记录；接触近失无效果事件和无损伤报告。
- 主线程复验：`py_compile` 通过；3 个引信 gate 聚焦 pytest 通过。
- 限制：未改变 runtime 物理、效果模型或 reward；零伤害过渡事件仍保留，后续如要删除需等待下游消费面完全迁移。

### MLF-2G-C1

主线程执行并验收。

- 触碰文件：本子项目 README、current status、task clusters、dispatch queue、archive index，以及 A2/MLF-1 导航 README。
- 实现内容：把完整 MLF-2 证据包移入 `archive/mlf_2_geometry_fuze_accepted_20260609/`；当前 MLF-2 目录改为轻量指针；同步 accepted/held 状态和 MLF-3+ 残余地图。
- 验收结论：MLF-2 已能解释导弹最近点、引信解保/触发/失败原因和起爆 handoff；它仍不实现战斗部效果、碎裂、残骸、Pk 或具体弹种杀伤结论。
- 限制：timed fuze、guidance expiry recorder、零伤害过渡记录删除和更细目标姿态仍留给后续阶段。

## Worker Packet 合同

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 集成说明

- 主线程负责验收返回包和更新本队列。
- status line、任务簇状态和父级 README 只能在验收后串行更新。
- 当前队列没有运行中的 worker，且已随 MLF-2 归档关闭。
- 如果 worker 发现现有 runtime 无法受控复现几何输入，应返回 blocked/partial 并说明缺口，不要绕到直接击毁规则。
