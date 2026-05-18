# 代码冗余与重复逻辑审计报告

状态：`2026-05-16` 全量静态分析完成；`2026-05-16` 已对非 `scenario_loader` 主线项完成代码复核与冻结范围内的第一轮实现收口
范围：C++ 核心引擎、ECS 组件体系、命令链数据结构、Python RL 运行时的冗余与重复逻辑

## 1. 背景

本项目经过多轮重构（flat struct → Core/Air/Naval 多继承拆分、`python/rl` 根目录 → 子包收敛、MovementCommand → PilotAction 迁移），不可避免地产生了过渡期残留。本报告聚焦于**仍在生效的重复代码、字段重叠、双轨并行和维护风险**。

## 2. 审计范围

- `src/components/` — ECS 组件定义（命令、任务、物理、系统）
- `src/systems/` — 各系统实现（气动、力、控制、传感器、数据链、地面接触）
- `src/core/engine/` — 内核系统注册与编排
- `python/rl/` — RL 运行时 Python 层（profile、tasking、runtime、control）
- `gym_envs/` — Gymnasium 环境封装

## 2.1 复核备注

- 本轮复核**排除了** `gym_envs/scenario_loader/*` 主线拆分项的再判断，尤其是 `5.3`、`5.11`、`5.15`；这些条目保留原始审计结论，但不作为本轮优先切入点。
- 复核结论采用三档：
  - `成立`：问题客观存在，且适合作为当前维护项推进。
  - `部分成立`：现象存在，但原文表述偏大，或其中一部分属于合理分层/兼容桥接。
  - `暂不作为当前切入点`：现象存在，但更像兼容层、验证层或预留接口，不宜按“冗余清理”优先处理。
- 复核后确认，最适合立即展开的切入点是：`3.1`、`3.3`、`5.7`、`5.12`、`5.13`。这些改动与 `scenario_loader` 主线拆分解耦，收益明确，回归面可控。
- `2026-05-16` 冻结计划执行完成后，`3.1`、`3.3`、`3.2`、`5.4`、`5.7`、`5.10`、`5.12`、`5.13` 的本轮授权收口已全部记录到位；本文档保留为审计与追踪基线，不再承担活动计划角色。

## 3. 高优先级发现

### 3.1 `MassProperties` 在系统注册中重复声明

**位置**：[src/core/engine/simulation_kernel_systems.cpp:78 和 :99](../../../../src/core/engine/simulation_kernel_systems.cpp)

```cpp
ecs.component<MassProperties>();  // Line 78
// ...
ecs.component<MassProperties>();  // Line 99 — 完全相同的重复
```

虽然 flecs 中重复注册是幂等的，但两次声明位于不同段落（Physics 段与 EW/Logistics 段），表明注册代码缺乏按组件语义的分组整理。

**2026-05-16 执行更新**：当前版本已移除重复注册，`src/core/engine/simulation_kernel_systems.cpp` 中仅保留一处 `ecs.component<MassProperties>()`。该条目的直接重复问题已收敛，后续若继续处理，将主要聚焦 `3.2` 所述的双轨质量组件边界，而不是注册样板本身。

---

### 3.2 `Mass` 与 `MassProperties` 双轨质量组件

**复核结论**：`已完成第一批边界补强`

**位置**：
- `Mass` 定义于 [src/components/physics/dynamics.h](../../../../src/components/physics/dynamics.h)
- `MassProperties` 定义于 [src/components/systems/logistics.h](../../../../src/components/systems/logistics.h)

| 字段 | `Mass` | `MassProperties` |
|---|---|---|
| `empty_mass_kg` | ✅ | ✅ **重复** |
| `fuel_mass_kg` | ✅ | — |
| `stores_mass_kg` | ✅ | — |
| 总质量获取方式 | `get_total_kg()` | `current_total_mass_kg` |
| 参考面积/翼展/弦长 | — | ✅ |
| 阻力指数 | — | ✅ |

**影响**：

1. `empty_mass_kg` 分布在两个组件中，可能发生数据不同步。
2. `aerodynamics_system.h` 使用 `MassProperties`（读面积/弦长），而 `force_system.h`、`leapfrog_system.h`、`ground_contact_system.h` 使用 `Mass`（读总质量）。
3. `logistics_system.h` 必须同时更新两个组件（`MassUpdate` 系统以 `MassProperties, Mass, FuelSystem` 为参数），维护成本翻倍。

**建议**：将 `empty_mass_kg` 和 `get_total_kg()` 统一到一个权威组件（`MassProperties`），`Mass` 仅保留燃油/挂载重量子字段，或直接废除 `Mass`。

**2026-05-16 WP-C 执行更新**：当前版本已完成第一批边界补强：
- [src/systems/systems/logistics_system.h](../../../../src/systems/systems/logistics_system.h) 的 `MassUpdate` 已显式以 `Mass` 为运行时分解质量权威，并同步 `MassProperties.empty_mass_kg/current_total_mass_kg`；
- `MassProperties.current_total_mass_kg` 现改为镜像 `Mass::get_total_kg()`，从而不再漏掉 `stores_mass_kg`；
- 新增最小 debug 读回口与直接回归测试，用于验证 `Mass` / `MassProperties` 同步关系，而未扩张为通用组件暴露面。

剩余保留项：
- `Mass` 与 `MassProperties` 的双轨结构仍然存在；
- `aerodynamics / force / leapfrog / ground_contact` 仍分别读取不同组件面，这一层级的“单权威组件迁移”不在本轮冻结范围内。

---

### 3.3 `command_link_system.h` 三系统复制粘贴

**位置**：[src/systems/systems/command_link_system.h:7-68](../../../../src/systems/systems/command_link_system.h)

`CommandLinkMovement`、`CommandLinkAction`、`CommandLinkMission` 三个系统包含完全相同的逻辑——仅操作不同组件类型：

```cpp
// 三段代码完全一致，仅组件类型不同：
if (!pending[i].active) continue;
if (current_time < pending[i].deliver_time) continue;
cmd[i] = pending[i].command;
cmd[i].active = true;
pending[i].active = false;
```

**影响**：每次修改延迟/投递逻辑需要改三处，极易遗漏。

**建议**：用 C++ 模板函数 `deliver_pending<TCmd, TPending>(iter)` 替代三段重复代码，消除 ~45 行冗余。

**2026-05-16 执行更新**：当前版本已在 `src/systems/systems/command_link_system.h` 中引入模板 helper `deliver_pending_command()`，将 `Movement / Action / Mission` 三类待投递命令的公共投递逻辑收口到同一实现。该条目的复制粘贴问题已完成第一轮清理。

---

### 3.4 Python 侧手动维护 C++ 结构体字段镜像

**位置**：[gym_envs/leader_env.py:83-177](../../../../gym_envs/leader_env.py)

```python
_TASK_ORDER_FIELDS = (
    "task_id", "task_type", "service_profile", ...
)  # 50+ 字段

_LEADER_INTENT_FIELDS = (
    "phase_id", "element_phase_id", ...
)  # 33 字段

_PILOT_REPORT_FIELDS = (
    "report_type", "sender_id", ...
)  # 23 字段
```

这些列表在 `_clone_task_order()`、`_clone_leader_intent()`、`_clone_pilot_report()` 中通过 `setattr(getattr())` 逐字段复制。

**风险**：每次 C++ 结构体增删字段，Python 侧必须手动同步三处字段列表，否则克隆操作会静默丢失字段。

**建议**：利用 nanobind 的类型反射（`nb::enum_` / `nb::class_` 已注册所有字段）自动生成字段名列表，或至少添加单元测试验证 Python 字段列表与 C++ 结构体的一致性。

**2026-05-16 执行更新**：本轮已完成第一批修复：
- 为 `TaskOrder` / `LeaderIntent` 补齐缺失的 cooperative takeoff 字段镜像；
- 在 `gym_envs/leader_env.py` 中增加 `_clone_assign_field()`，对 Python `int -> ef_py enum` 赋值失败场景做兼容转换，避免强类型枚举字段被静默丢弃；
- 在 `tests/leader/test_two_ship_contract_fields.py` 中增加反射校验，要求 Python 字段列表与 `dir(ef_py.TaskOrder/LeaderIntent/PilotReport)` 一致。

**2026-05-16 继续推进**：已进一步将 `_TASK_ORDER_FIELDS` / `_LEADER_INTENT_FIELDS` / `_PILOT_REPORT_FIELDS` 改为直接基于 `dir(ef_py.*())` 的反射生成，并将 clone 主体收敛为统一实现。这样 Python 侧不再单独维护字段名元组，只保留 clone 兼容层本身。

后续仍可继续评估是否让 `leader_env` 直接按反射结果 clone，而不再保留显式字段常量导出。

---

## 4. 中优先级发现

### 4.1 `MovementCommand` 遗留体系仍在 9 个文件中生效

**复核结论**：`部分成立`

**引用文件**：
- `src/systems/physics/force_system.h`
- `src/systems/physics/ground_contact_system.h`
- `src/systems/physics/instrument_system.h`
- `src/systems/systems/logistics_system.h`
- `src/systems/systems/command_link_system.h`
- `src/systems/core/operation_system.h`
- `src/core/engine/simulation_kernel_systems.cpp`
- `src/core/engine/simulation_kernel_command_api.cpp`
- `src/core/engine/exact_stage_inventory.cpp`

每个系统中的重复模式：

```cpp
// Priority 1: PilotAction (新)
if (pilot && pilot->active) { throttle = pilot->throttle; }
// Priority 2: MovementCommand (遗留)
else if (cmd && cmd->active) { throttle = cmd->throttle_cmd; }
```

`MovementCommand` 的遗留链路确实横跨 9 个文件，但“同一段优先级逻辑在 9 个文件中重复”并不准确。经复核，真正重复的 throttle / brake / command fallback 逻辑主要集中在 `force_system.h`、`logistics_system.h`、`ground_contact_system.h`、`instrument_system.h` 等少数运行时系统中，其余文件更多是在注册、API 暴露或阶段清单中维持兼容路径。

**建议**：提取公共函数 `resolve_throttle(entity)` 消除重复，并在所有引用迁移完成后标记 `MovementCommand` 为 `[[deprecated]]`。

**2026-05-16 执行更新**：本轮已完成第一批收敛：
- 新增 `src/components/command/air/control_input_resolution.h`；
- 将 `force_system.h`、`logistics_system.h`、`ground_contact_system.h`、`instrument_system.h` 中重复的 `PilotAction -> MovementCommand` throttle / brake fallback 收口到共享 helper；
- 保留 `logistics_system.h` 中 `ActionCommand` 的第三优先级逻辑和 `ground_contact_system.h` 的 legacy idle/full-brake 特例在本地，避免过度抽象；
- 增加运行时回归，验证 `PilotAction` 仍优先覆盖 legacy `MovementCommand`。

**2026-05-16 继续推进**：已完成第二批收口：
- 在 `src/components/command/legacy_command.h` 中为 legacy autopilot / stick / lagged command 增加统一构造 helper；
- 在 `src/components/command/command_link.h` 中增加 `make_pending_movement_command()`；
- 将 `src/core/engine/simulation_kernel_command_api.cpp` 与 `src/models/core/default_unit_factory.h` 中重复的 `MovementCommand` / `PendingMovementCommand` / `LaggedCommand` 初始化样板收口到共享 helper。

**2026-05-16 再推进**：已完成第三批低风险样板清理：
- 在 `src/components/command/legacy_command.h` 中增加 `make_action_command()`；
- 在 `src/components/command/command_link.h` 中增加 `make_pending_action_command()` 与 `make_pending_mission_command()`；
- 将 `src/core/engine/simulation_kernel_command_api.cpp`、`src/models/core/default_unit_factory.h` 中的 `ActionCommand` / `PendingActionCommand` / `PendingMissionCommand` 聚合初始化切换到共享 helper；
- 同时移除 `DefaultUnitFactory` 中对 `ActionCommand` 的重复 inactive 重置，减少兼容层样板噪声。

**2026-05-16 WP-A 第一批推进**：已继续收紧 `simulation_kernel_command_api.cpp` 内部样板：
- 新增文件内 helper，统一 `entity_id -> flecs::entity` 的 invalid guard / warn；
- 新增共享 helper 统一 `world_time_total` 读取、`CommandLink` 是否需要进入 pending delivery 路径的判定；
- 将 `PilotAction` / `MissionCommand` / `TaskOrder` / `LeaderIntent` / `PilotReport` 的 `active=true` copy-set 模式收口到共享 helper；
- 补充针对 invalid entity no-op 与 roundtrip `active` 置位的直接回归测试。

**2026-05-16 WP-A 第二批推进**：已对 `src/systems/core/operation_system.h` 做最后一批低风险样板收口：
- 抽出 `operation_seed_movement_command()` 与 `operation_seed_lagged_command()`；
- 将 `ActionMapping` / `CommandLag` 两处“从当前 `Transform + Velocity` 初始化 legacy target 状态”的重复块改为共享 seed helper；
- 经复核，`src/systems/physics/control_system.h` 当前仅承担调度/转发职责，没有同级别值得继续抽取的重复逻辑，因此本轮不再为了抽象而扩张范围。

`MovementCommand` 兼容链本身仍然存在，因此该条目仍保留为“部分成立”，但第一批重复逻辑已不再分散实现。

---

### 4.2 `common_core_defaults.py` ↔ `common_core_profile.py` 函数包裹

**复核结论**：`部分成立`

**位置**：
- [python/rl/profile/common_core_defaults.py](../../../../python/rl/profile/common_core_defaults.py) (132 行) — 底层原语
- [python/rl/tasking/common_core_profile.py](../../../../python/rl/tasking/common_core_profile.py) (630 行) — 包裹层

几乎每个底层函数在上层都有一个 `_` 前缀版本：

| 底层函数 | 上层包裹 |
|---|---|
| `service_profile_default()` | `_service_profile_default()` |
| `task_family_default()` | `_task_family_default()` |
| `coordination_mode_default()` | `_coordination_mode_default()` |
| `infer_tactical_unit_type()` | `_infer_tactical_unit_type()` |
| `infer_recovery_site_id()` | `_infer_recovery_site_id()` |

上层文件前段确实存在一批 `_service_profile_default()` / `_task_family_default()` 这类转发包装，但 `apply_task_order_common_core_defaults()`、`apply_leader_intent_common_core_defaults()`、`apply_pilot_report_common_core_defaults()` 等后半段函数承担了真实的 profile 选择、默认值编排和 air/naval 语义桥接。因此它不是一个“可以整体删除的空壳包裹层”，更适合做有限度收缩而不是简单合并。

**建议**：评估 `common_core_profile.py` 中的组合函数（`apply_task_order_common_core_defaults` 等）是否可以下沉到 `profile/` 目录，或直接让调用方使用底层 API。

---

### 4.3 `leader_env.py` 1752 行：环境逻辑与命令策略混合

**位置**：[gym_envs/leader_env.py](../../../../gym_envs/leader_env.py) — 全项目最长的 Python 文件

该文件混合了：
- 环境生命周期（`step/reset/close`）
- 动作解码（`_decode_action`，包含量化区间映射逻辑）
- 动作清洗（`_sanitize_action_mapping`，包含起飞保护、进场门控等规则）
- 命令应用（`_apply_leader_command`，110 行，包含 phase→cmd_code 的完整映射表）
- 观测构建（`_build_observation`，110 行）
- 执行策略管理（`_build_execution_policy`、`_predict_execution_action`）
- C2/教师基线管理（`_compute_teacher_baseline`、`_update_scripted_c2`）

**建议**：将 `_decode_action` + `_sanitize_action_mapping` + `_apply_leader_command` 提取到 `python/rl/tasking/` 下的独立模块 `leader_command_codec.py`，将 `_build_observation` 提取到 `leader_observation_builder.py`。

---

### 4.4 `air_profile.py` 与 `naval_profile.py` 平行接口

**复核结论**：`部分成立`

**位置**：
- [python/rl/profile/air_profile.py](../../../../python/rl/profile/air_profile.py) (31 个函数)
- [python/rl/profile/naval_profile.py](../../../../python/rl/profile/naval_profile.py) (18 个函数)

11 个函数在两模块中同名存在：

`build_kernel_mission_command`, `infer_coordination_mode`, `infer_recovery_approach_type`, `infer_recovery_base_id`, `infer_recovery_runway_id`, `infer_route_ref_id`, `is_patrol_task`, `is_recover_task`, `normalize_task_order_spec`, `resolved_task_family`, `task_observation_codes`

这是策略模式的正常拆解（air vs naval 行为不同），不应简单视为“无意义重复”。但其中 `is_patrol_task`、`is_recover_task`、`resolved_task_family`、部分 recovery 推断函数仍有可上移的共性，适合在不破坏领域边界的前提下抽取共享原语。

**建议**：为 air/naval profile 创建共享基类 `BaseTaskingProfile`，将通用实现上移，仅在领域差异点使用多态。

---

## 5. 低优先级发现

### 5.1 兼容性过渡文件

**复核结论**：`暂不作为当前切入点`

| 文件 | 内容 | 可删除条件 |
|---|---|---|
| [src/components/physics/action.h](../../../../src/components/physics/action.h) | 仅含 13 个 `#include` | 所有外部引用迁移到直接导入 |
| [src/components/tasking/tasking_enums.h](../../../../src/components/tasking/tasking_enums.h) | 仅含 2 个 `#include` | `action.h` 不再引用它 |

---

### 5.2 C++ 侧 `PilotAction` 字段部分未使用

**复核结论**：`暂不作为当前切入点`

`PilotAction` 定义了 20+ 个字段（含 `radar_active`, `radar_scan_az`, `radar_scan_el`, `tms_up`, `master_arm`, `fire_weapon`, `fire_gun`, `weapon_select_id` 等），但当前仿真中：
- 传感器系统 (`default_sensor_model.cpp`) 不读取 `radar_active` / `radar_scan_az` / `radar_scan_el`——雷达始终全向扫描
- 武器系统 (`default_guidance_model.cpp`) 不读取 `master_arm` / `fire_weapon`——导弹通过 `fire_missile()` API 直接发射

这些字段是为未来扩充预留的正确占位，不构成冗余，但值得注意"接口已定义、行为未实现"的缺口。

---

### 5.3 `scenario_loader/core.py` 超大文件 3831 行

**位置**：[gym_envs/scenario_loader/core.py](../../../../gym_envs/scenario_loader/core.py) — 188KB，全项目最大单文件

`ScenarioLoader` 类包含 129 个方法，职责横跨：

- 场景 JSON 解析与编译
- 实体生成与随机化
- 航路点生成与旋转
- ILS 信标管理
- 任务命令构建
- C2 任务接口
- 执行情节状态构建
- 观测缓存管理
- 奖励/终止运行时字段
- GPU 后端模式切换
- 编译后场景加载

**问题**：该文件比 `python/scenario_compiler.py` (1321 行, 59 个函数) 和 `python/scenario_runtime.py` (1520 行, 38 个函数) 的总和还要大。`ScenarioCompiler` 和 `ScenarioLoader` 都处理场景编译逻辑，存在语义重叠但调用关系不清晰。

**建议**：将 `core.py` 按职责拆分为 `scenario_loading.py`、`entity_spawning.py`、`mission_building.py`、`runtime_state.py`（后者的部分已存在但规模远小于 `core.py` 中对应逻辑）。

---

### 5.4 三个脚本控制器共享模式但未提取基类

**复核结论**：`已完成第一批收口`

**位置**：
- [python/rl/control/scripted_takeoff.py](../../../../python/rl/control/scripted_takeoff.py)
- [python/rl/control/scripted_stable_flight.py](../../../../python/rl/control/scripted_stable_flight.py)
- [python/rl/control/scripted_landing.py](../../../../python/rl/control/scripted_landing.py)

三个类共享完全相同的接口和初始化模式：

```python
class ScriptedXxxController:
    def __init__(self, *, action_dim: int, dt: float = 0.05):
        self.action_dim = int(action_dim)
        self.dt = float(dt)
        # ...

    def reset(self, obs: dict) -> None:
        inst = np.asarray(obs.get("instruments", ...))
        mission = np.asarray(obs.get("mission", ...))
        # 相同的 inst/mission 提取模式 ...

    def step(self, obs: dict) -> np.ndarray:
        inst = np.asarray(obs.get("instruments", ...))
        mission = np.asarray(obs.get("mission", ...))
        # 相同的字段提取模式 ...
```

额外重复：
- `_wrap_deg()` 辅助函数在 `scripted_takeoff.py` 和 `scripted_landing.py` 中各定义一次
- 仪器数组索引解包（`ias = inst[0]`, `alt_radar = inst[3]` 等）在三处各自独立实现

**建议**：提取 `BaseScriptedController` 抽象基类，统一 `__init__`/`reset`/`step` 模板方法和共享的仪器解码逻辑。三个子类仅实现差异化的控制律。

**2026-05-16 WP-B 执行更新**：当前版本已完成最小共享骨架抽取：
- 新增 [python/rl/control/base_scripted_controller.py](../../../../python/rl/control/base_scripted_controller.py)，统一 `action_dim/dt`、`obs -> np.ndarray` 解包、零动作构造与 `wrap_deg()`；
- [scripted_takeoff.py](../../../../python/rl/control/scripted_takeoff.py)、[scripted_stable_flight.py](../../../../python/rl/control/scripted_stable_flight.py)、[scripted_landing.py](../../../../python/rl/control/scripted_landing.py) 已切换到共享 helper，但未改动控制律主体，也未改变公开类名或构造签名；
- 聚焦 contract 已回归通过：`scripted_takeoff_takeoff2_throttle`、`scripted_takeoff_clearance_hold`、`scripted_landing_controller`、`scripted_stable_flight_rudder_sign`；
- 同时修正 [tests/contracts/unit/controllers/scripted_takeoff_clearance_hold.json](../../../../tests/contracts/unit/controllers/scripted_takeoff_clearance_hold.json) 缺失的 `type: "unit_regression"` 测试夹具元数据，使其可被统一 contract runner 正常分发。

剩余保留项：
- 三个 controller 内部的仪器字段索引与控制律仍保持各自本地实现；
- 本轮未向 `wrappers.py`、`leader_env.py` 或更广的 scripted baseline runtime 扩张，这是刻意保持低风险边界的结果。

---

### 5.5 `world_batch_vec_env.py` ↔ `cooperative_world_batch_vec_env.py` 并行实现

**复核结论**：`部分成立`

**位置**：
- [python/rl/runtime/world_batch_vec_env.py](../../../../python/rl/runtime/world_batch_vec_env.py) (2018 行)
- [python/rl/runtime/cooperative_world_batch_vec_env.py](../../../../python/rl/runtime/cooperative_world_batch_vec_env.py) (1861 行)

两个文件仍共享大量函数名和导入模式，也确实保留了不少并行实现，但“完全独立双写”已不准确。`cooperative_world_batch_vec_env.py` 已显式复用 `world_batch_vec_env.py` 中的 `_RuntimeFacadeAdapter`、`_normalize_batch_observation_backend`、`_normalize_batch_visual_backend` 等基础设施。

仍然分散维护的共享基础设施包括：

- `_batch_observation_backend_mode()`
- `_normalize_flight_shaping_backend()`
- `_prepare_step_evaluations_batch()`
- `_sync_command_chain_batch()`
- `_refresh_visual_batch()`

**问题**：这两个类本质上是同一架构的单智能体 vs 多智能体变体。当前已经出现部分共享，但共享边界仍不集中，导致进一步修改基础设施时仍需双边对照。

**建议**：提取 `_BaseWorldBatchInfrastructure` mixin 容纳所有共享函数（约 25 个），两个具体类继承它并仅保留差异逻辑。

---

### 5.6 `EGI` 与 `InstrumentState` 字段重叠

**复核结论**：`部分成立`

**位置**：
- `EGI` 定义于 [src/components/systems/navigation.h](../../../../src/components/systems/navigation.h)
- `InstrumentState` 定义于 [src/components/physics/instruments.h](../../../../src/components/physics/instruments.h)

两个组件存在 12 个语义重叠的字段：

| 数据 | `EGI` | `InstrumentState` |
|---|---|---|
| 纬度 | `lat_deg` | `lat_deg` |
| 经度 | `lon_deg` | `lon_deg` |
| NED 速度 | `vn/ve/vd_mps` | `vn/ve/vd_mps` |
| 气压高度 | `alt_baro_m` | `alt_baro_m` |
| 雷达高度 | `alt_radar_m` | `alt_radar_m` |
| 航向/俯仰/滚转 | `heading/pitch/roll_deg` | `heading/pitch/roll_deg` |

`NavigationSystem` 写入 `EGI`，然后 `InstrumentSystem` 从 `EGI` 复制到 `InstrumentState`，字段重叠客观存在。但 `EGI` 同时还携带 `drift_lat_m`、`drift_lon_m`、`drift_alt_m`、`time_since_last_gps_fix`、`position_uncertainty_m`、`gps_available` 等导航状态；因此它并不只是“毫无意义的重复容器”，更像导航中间缓存与状态面。

**建议**：短期优先明确 `EGI` 的职责边界。如果它将承担 GPS 中断/漂移/导航置信度建模，则应保留并文档化；若长期不承载这些语义，再评估是否下沉到 `InstrumentState` 或抽出只读投影层。

**2026-05-16 执行更新**：本轮已完成第一批边界收口：
- 将 `EGI` 明确视为导航缓存/状态面；
- 在 `src/components/systems/navigation.h` 中新增 `InstrumentNavigationProjection` 与 `project_egi_to_instrument_navigation()`；
- `src/systems/physics/instrument_system.h` 不再直接手写 `EGI -> InstrumentState` 的字段搬运与地速/地航迹派生，而是统一消费导航投影结果；
- 增加运行时回归，验证仪表导航读数仍按 `EGI` 输出投影。

这一步没有删除重叠字段，但已经把“状态面”和“pilot-facing 投影面”的责任边界显式化，便于后续评估是否继续下沉或保留双层结构。

---

### 5.7 `instrument_system.h` 和 `default_control_model.cpp` 重复实现地面航迹计算

**位置**：
- [src/systems/physics/instrument_system.h:44-49](../../../../src/systems/physics/instrument_system.h) — `inst_ground_track_deg_from_velocity()`
- [src/models/air/default_control_model.cpp:57-65](../../../../src/models/air/default_control_model.cpp) — `ground_track_deg_from_velocity()`

两个函数做完全相同的事：从 `Velocity` 计算地速航迹，低速时回退到航向角。仅变量名不同（`horiz_speed` vs `v_h`）。

**建议**：将地面航迹计算提取到 `components/basic/common.h` 作为共享工具函数。

**2026-05-16 执行更新**：当前版本已在 `src/components/basic/common.h` 中统一提供 `Math::ground_track_deg_from_velocity()`。
- `src/systems/physics/instrument_system.h` 已通过 `inst_ground_track_deg_from_velocity()` 薄包装接入公共 helper；
- `src/models/air/default_control_model.cpp` 已直接调用 `Math::ground_track_deg_from_velocity()`；
- `src/components/systems/navigation.h` 中的导航投影也已复用同一原语。

因此该条目的核心重复逻辑已完成收口，后续若继续精简，重点将是删除局部薄包装命名，而不是再处理算法分叉问题。

---

### 5.8 `world_to_body` 姿态矩阵重复实现

**复核结论**：`部分成立`

同一姿态矩阵在世界坐标→机体坐标的转换至少在三个地方出现相关实现：

| 文件 | 实现 |
|---|---|
| [src/systems/physics/aero_state_system.h:39-78](../../../../src/systems/physics/aero_state_system.h) | `world_to_body()` — 完整 3 轴旋转 |
| [src/systems/physics/instrument_system.h:83-124](../../../../src/systems/physics/instrument_system.h) | `project_forces_to_body()` — 完整 3 轴旋转，但仅返回 ax/az |
| [src/systems/physics/aerodynamics_system.h:26-45](../../../../src/systems/physics/aerodynamics_system.h) | `get_body_right()` — 部分旋转（仅 body Y → world） |

其中 `aero_state_system.h` 的 `world_to_body` 和 `instrument_system.h` 的 `project_forces_to_body` 两者都实现了相同的 ψ→θ→φ 欧拉旋转序列，属于实质性重复。`aerodynamics_system.h` 的 `get_body_right()` 只覆盖局部方向投影，不是完全同一层级；另外武器效果模型中还存在一份更简化的 `world_to_body`。

**建议**：将 `world_to_body()` 和 `body_to_world()` 提取为 `Math::` 命名空间中的公共函数。

**2026-05-16 执行更新**：本轮已完成第一批公共化：
- 在 `src/components/basic/common.h` 中新增 `Math::world_to_body()`、`Math::body_to_world()` 以及共享的欧拉角旋转系数辅助；
- 将 `src/systems/physics/aero_state_system.h`、`src/systems/physics/instrument_system.h`、`src/systems/physics/aerodynamics_system.h` 接入公共原语，消除主运行时中的重复 3 轴旋转实现；
- `src/models/weapons/default_effects_model.cpp` 中的简化 `world_to_body` 仍保留，暂不与主飞行动力学旋转原语强行合并，以避免在武器效果判定上引入语义变化。

---

### 5.9 GPU 与 CPU 双轨 FlightShaping 计算

**复核结论**：`暂不作为当前切入点`

**位置**：
- [src/gpu/gpu_flight_shaping_runtime.h](../../../../src/gpu/gpu_flight_shaping_runtime.h) — GPU 路径（36 行声明）
- [src/core/mission/runtime/reward_runtime.h](../../../../src/core/mission/runtime/reward_runtime.h) — CPU 路径（286 行声明 + 实现）

GPU 路径显式声明了 `compute_flight_shaping_reference_cpu_batch()` 和 `compute_flight_shaping_experiment_batch()` 两个函数。复核实现后确认，当前 GPU 路径在 CUDA 不可用或实验路径未返回结果时，会回退到 CPU reference；这属于标准验证双轨，而不是应立即删除的冗余。

---

### 5.10 Nanobind 绑定是第三个手动字段镜像

**复核结论**：`已完成第一批测试补强`

**位置**：[src/interfaces/python/bindings_command.cpp](../../../../src/interfaces/python/bindings_command.cpp) (417 行)

每个 C++ 结构体的每个字段都有一个对应的 `.def_rw("name", &Struct::field)` 行。Nanobind 绑定本身是合理的绑定样板；问题在于它再叠加 Python 侧的 `_TASK_ORDER_FIELDS` / `_LEADER_INTENT_FIELDS` / `_PILOT_REPORT_FIELDS` 元组后，形成了第三个手工维护面：

| 层 | 位置 | 行数 |
|---|---|---|
| C++ 定义 | `src/components/tasking/*.h` | 权威 |
| Nanobind 绑定 | `src/interfaces/python/bindings_command.cpp` | ~180 行字段映射 |
| Python clone 元组 | `gym_envs/leader_env.py` | ~100 行字段名 |

三个位置中任何一个遗漏都会导致字段丢失。

**建议**：最低成本方案——Python 侧用 `dir(ef_py.TaskOrder())` 反射替代硬编码元组（nanobind 对象支持 `dir()`）。或编写单元测试，在 C++ 结构体每次修改后自动检测 Python 镜像是否完整。

**2026-05-16 WP-C 执行更新**：当前版本已补齐第一批绑定维护面回归：
- 保留 nanobind 现有 `.def_rw(...)` 绑定模式，不引入新的自动绑定系统；
- 在 [tests/leader/test_two_ship_contract_fields.py](../../../../tests/leader/test_two_ship_contract_fields.py) 继续覆盖 `TaskOrder / LeaderIntent / PilotReport` 的反射一致性；
- 新增 [tests/runtime/bindings/test_bindings_command_surface.py](../../../../tests/runtime/bindings/test_bindings_command_surface.py)，直接固定 `MissionCommand / PilotAction / CommPacket` 的公开字段 surface，降低 `bindings_command.cpp` 漏绑后的静默漂移风险。

剩余保留项：
- `bindings_command.cpp` 仍是手工维护面；
- 本轮没有把 `MissionCommand / PilotAction / CommPacket` 的字段 surface 自动生成化，只是补了直接回归。

---

### 5.11 `shaping.py` deadband/norm/power 模式 24 次重复

**位置**：[gym_envs/scenario_loader/execution_runtime/shaping.py](../../../../gym_envs/scenario_loader/execution_runtime/shaping.py) (316 行)

同一个奖励项计算模式——取参数 deadband → 计算误差 → 除以 norm → 取 power → clip → 调用 `add_reward_term`——在以下场景中出现 24 次：

- 高度误差惩罚 + 高度保持奖励（2 次）
- 速度误差惩罚 + 速度保持奖励（2 次）
- 滚转/俯仰/偏航率/侧滑角 姿态惩罚（4 次，通过 tuple 循环减少到 ~30 行但仍重复 norm/power/clip 逻辑）
- G 载荷偏差惩罚（1 次）
- 跑道中心线惩罚（含 `_m` 变体、`_barrier` 变体、`_penalty` 变体共 6 次）
- 离场中心线惩罚 + 离场中心线奖励 + 离场航迹惩罚 + 离场航迹奖励（4 次）

总计 316 行中约 180 行是同一模式的变体。

**建议**：提取 `_compute_error_penalty(cfg, prefix, state_value, add_reward_term)` 辅助函数，将 `name/deadband/norm/power/clip` 五个键名的约定统一起来。

---

### 5.12 `mission_obs_taxonomy.py` 字段列表完全展开

**复核结论**：`成立`

**位置**：[python/mission_obs_taxonomy.py](../../../../python/mission_obs_taxonomy.py) (189 行)

21 个字段名在多个观测模式列表中重复出现：

| 字段出现次数 | 示例 |
|---|---|
| 6 个模式 | `command_code`, `target_heading_deg`, `target_altitude_m`, `target_speed_mps` |
| 4 个模式 | `dist_m`, `bearing_rel_deg`, `cdi_norm`, ... (10 个 nav_v2 字段) |
| 3 个模式 | `form_offset_x/_y/_z_m` |
| 2 个模式 | `self_role_code`, `relative_slot_code`, ... (4 个角色字段) |

字段列表是"复制上一级 + 添加新字段"的完全展开模式，而非"基础列表 + 增量"的组合模式。若 `nav_v2` 中修改字段名，需要改 4 处。

**建议**：用增量定义替代完全展开：
```python
_NAV_V2_FIELDS = ["selected_steerpoint", "steerpoint_mode_code", ...]
_FORM_EXTRA = ["form_offset_x_m", "form_offset_y_m", "form_offset_z_m"]
_ROLE_EXTRA = ["self_role_code", ...]
MISSION_OBS_FIELD_NAMES_BY_NAME = {
    "nav_v2_formation_role_v1": _BASE_FIELDS + _NAV_V2_FIELDS + _FORM_EXTRA + _ROLE_EXTRA,
}
```

**2026-05-16 执行更新**：当前版本已按该建议完成重构。
- `python/mission_obs_taxonomy.py` 已拆分为 `_MISSION_OBS_BASIC_FIELDS`、`_MISSION_OBS_NAV_V2_EXTRA_FIELDS`、`_MISSION_OBS_FORMATION_EXTRA_FIELDS`、`_MISSION_OBS_ROLE_EXTRA_FIELDS`、`_MISSION_OBS_COOPERATIVE_TAKEOFF_EXTRA_FIELDS` 等增量列表；
- `MISSION_OBS_FIELD_NAMES_BY_NAME` 已通过“基础字段 + 增量字段”组合构造各模式字段集，而非继续完全展开；
- `tests/runtime/mission/test_mission_obs_taxonomy.py` 已对模式编码、字段布局、关键索引和维度做直接回归校验。

该条目在当前代码中可视为已实质解决，后续更多是随新 mission obs 模式扩展时维持组合式定义。

---

### 5.13 `env_config.py` args/env_cfg 合并模式 8 次重复

**复核结论**：`部分成立`

**位置**：[python/env_config.py:26-90](../../../../python/env_config.py)

`resolve_env_settings()` 中同类 merge 模式确实反复出现，但“8 次完全相同”略有简化。当前更准确地说，是 `include_proprio`、`action_mode`、`mission_obs_mode`、`visual_downsample`、`visual_update_interval`、`execution_step_runtime_mode`、`step_info_mode`、`flight_shaping_backend` 这 8 项采用同类 merge 模式，外加一个稍有特化的 `include_visual` 分支。

典型模式如下：

```python
X = getattr(args, "X", None)
if X is None:
    X = type(env_cfg.get("X", default))
else:
    X = type(X)
```

**建议**：提取 `_merge_config_value(args, attr_name, env_cfg, cfg_key, default, coerce_fn)` 消除重复。

**2026-05-16 执行更新**：当前版本已完成第一批收口。
- `python/env_config.py` 已新增 `_merge_config_value()` 与 `_merge_optional_config_value()`，并将 `include_proprio`、`action_mode`、`mission_obs_mode`、`visual_downsample`、`visual_update_interval`、`execution_step_runtime_mode`、`step_info_mode`、`flight_shaping_backend` 的合并逻辑切换到共享 helper；
- `include_visual` 仍保留独立分支，因为它额外承担“从 train_config 推断视觉 extractor”的特化语义，不宜为了统一形式强行合并；
- 本轮新增 `tests/runtime/core/test_env_config.py`，直接覆盖 optional merge 的 lower/trim、空串清空和非法值报错分支，补齐此前主要依赖 contract runner 的间接验证缺口。

因此该条目的重复模式已大幅收敛；当前剩余的是一个合理的特化分支，而不是大面积复制逻辑。

---

### 5.14 `simulation_kernel_command_api.cpp` entity 验证样板 20 次

**复核结论**：`部分成立`

**位置**：[src/core/engine/simulation_kernel_command_api.cpp](../../../../src/core/engine/simulation_kernel_command_api.cpp) (365 行)

文件中确实存在大量重复的 ECS entity 查找+验证模式，但“20 处”偏大。按当前实现复核，`auto e = ecs.entity(entity_id);` 在该文件中大约出现 14 次，其中显式 invalid guard / warn 约 11 处。
```cpp
auto e = world.entity(entity_id);
if (!e.is_valid()) return;
```

`observation_api.cpp` 中也存在同类样板，但它们应作为后续统一抽象的扩展范围，而不应与 `command_api.cpp` 的局部计数混为一谈。

**建议**：提取 `resolve_entity(world, entity_id)` 或更轻量的 `with_valid_entity(...)` helper，先消除 `command_api.cpp` 这一处高频样板，再决定是否推广到 observation / visual API。

**2026-05-16 执行更新**：当前版本已在 `src/core/engine/simulation_kernel_command_api.cpp` 内部落地第一批 helper 化：
- 统一 invalid entity guard / warn；
- 统一 world time 读取与 command-link queue 判定；
- 保持 helper 作用域局限在 `command_api.cpp` 文件内，未扩散到 observation / visual API。

本条目可视为已完成第一阶段收口；后续是否推广到其他 kernel API 文件，需另行评估，而不是在本轮内继续扩张。

---

### 5.15 `execution_runtime/mainline.py` ↔ `shadow.py` 并行验证双写

**位置**：
- [gym_envs/scenario_loader/execution_runtime/mainline.py](../../../../gym_envs/scenario_loader/execution_runtime/mainline.py) (741 行, 37KB)
- [gym_envs/scenario_loader/execution_runtime/shadow.py](../../../../gym_envs/scenario_loader/execution_runtime/shadow.py) (225 行)

`shadow.py` 实现了与 `mainline.py` 相同语义的 C++ `ExecutionEpisodeController` 路径，用于验证 C++ 编译路径与 Python 解释路径产生相同结果。这是深度学习编译器领域标准的 "shadow testing" 模式，但意味着每个步骤在计算上被运行两次。

**建议**：一旦 C++ `ExecutionEpisodeController` 路径被所有场景合约充分验证（当前 `scenario_contract_runner.py` 已在做），shadow 路径即可标记为废弃并移除。

---

### 5.16 `training_callbacks.py` 1120 行与 `world_model/dreamer.py` 1282 行

**复核结论**：`暂不作为当前切入点`

**位置**：
- [python/training_callbacks.py](../../../../python/training_callbacks.py) (1120 行, 28 个函数)
- [python/world_model/dreamer.py](../../../../python/world_model/dreamer.py) (1282 行, 13 个函数)

这是合理的大型文件（训练逻辑和 Dreamer 模型），不是冗余问题。但 `training_callbacks.py` 包含多种回调类型（日志记录、检查点保存、课程调度、评估调度、早停），可根据回调类型拆分为 `callbacks/logging.py`、`callbacks/checkpoint.py`、`callbacks/curriculum.py` 等子模块。

---

## 6. 复核后影响汇总

| 复核结论 | 条目 | 说明 |
|---|---|---|
| `成立` | `3.1` | 重复注册，低风险可立即清理 |
| `已完成第一批边界补强` | `3.2` | `Mass` 仍为运行时分解质量权威，`MassProperties` 同步边界已收紧 |
| `成立` | `3.3` | 三套数据链投递逻辑可直接模板化 |
| `成立` | `3.4` | Python 手工字段镜像存在静默漂移风险，但已完成字段补齐、枚举 clone 兼容与反射校验第一批修复 |
| `成立` | `4.3` | `leader_env.py` 职责混合明显 |
| `已完成第一批收口` | `5.4` | scripted 控制器已抽出最小共享骨架，控制律仍保留本地实现 |
| `成立` | `5.7` | 地面航迹计算存在真实重复 |
| `成立` | `5.12` | mission obs taxonomy 维护方式易漂移 |
| `部分成立` | `4.1` | 遗留链路范围属实，但 throttle/brake fallback 第一批重复逻辑已完成共享收口 |
| `部分成立` | `4.2` | 前段有 wrapper 冗余，后段仍承担真实 bridge 逻辑 |
| `部分成立` | `4.4` | air/naval 平行接口合理，适合抽共性但不应强行并表 |
| `部分成立` | `5.5` | 两个 vec env 仍并行维护，但已经开始共享 helper |
| `部分成立` | `5.6` | EGI 与 InstrumentState 仍重叠，但已完成第一批“状态面 -> 仪表投影面”边界收口 |
| `部分成立` | `5.8` | 主运行时 consumer 已完成第一批公共化，武器效果模型中的简化变体仍保留 |
| `已完成第一批测试补强` | `5.10` | 绑定样板仍手工维护，但关键公开 surface 已有直接回归覆盖 |
| `部分成立` | `5.13` | merge 模式重复真实存在，但不是“8 次完全相同” |
| `部分成立` | `5.14` | entity guard 样板真实存在，但计数被放大 |
| `暂不作为当前切入点` | `5.1` | 兼容 umbrella header，先留 |
| `暂不作为当前切入点` | `5.2` | 更像预留接口未完全落地 |
| `暂不作为当前切入点` | `5.9` | GPU/CPU 双轨属于验证路径 |
| `暂不作为当前切入点` | `5.16` | 属于模块体量问题，不是重复问题 |

## 7. 后续建议

### 7.1 立即切入

1. 删除 `MassProperties` 重复注册（`3.1`）。
2. 将 `command_link_system` 三段重复逻辑模板化（`3.3`）。
3. 将 `ground_track_deg_from_velocity()` 提取到公共头文件（`5.7`）。
4. 用增量组合重写 `mission_obs_taxonomy.py` 中的字段列表定义（`5.12`）。
5. 在 `env_config.py` 中提取 `_merge_config_value()` / `_merge_optional_config_value()`（`5.13`）。

### 7.2 第二批推进

1. 继续压缩 `MovementCommand` 兼容链的剩余 consumer，并评估何时进入 `[[deprecated]]` 状态（`4.1`）。
2. 继续评估 `EGI` 与 `InstrumentState` 的长期结构：是保持“导航状态面 + 仪表投影面”，还是进一步下沉只保留只读投影辅助（`5.6`）。
3. 评估 `src/models/weapons/default_effects_model.cpp` 中的简化 `world_to_body` 是否需要向公共旋转原语靠拢，或保留为独立近似模型（`5.8`）。

### 7.3 暂缓项

1. `scenario_loader` 主线拆分相关条目（`5.3`、`5.11`、`5.15`）继续按既有主线推进，不在本轮重复裁剪。
2. `common_core_profile.py` 与 `air/naval_profile.py` 先保持 bridge + strategy 结构，避免在海空并行开发阶段过早重塑抽象边界。
3. GPU/CPU FlightShaping 参考路径保留到 GPU 路径和验证工具链稳定后再评估移除。
