# 指挥链与 C2 通信现实性分析

状态：`2026-05-17` 冻结分析版。

关联文件：

- [TaskOrder 组件](../../../../src/components/tasking/task_order.h)
- [TaskOrderCore (通用)](../../../../src/components/tasking/common/task_order_core.h)
- [TaskOrderAir (47 字段)](../../../../src/components/tasking/air/task_order_air.h)
- [TaskOrderNaval (3 字段)](../../../../src/components/tasking/naval/task_order_naval.h)
- [LeaderIntent 组件](../../../../src/components/tasking/leader_intent.h)
- [LeaderIntentAir (33 字段)](../../../../src/components/tasking/air/leader_intent_air.h)
- [LeaderIntentNaval (2 字段)](../../../../src/components/tasking/naval/leader_intent_naval.h)
- [PilotReport 组件](../../../../src/components/tasking/pilot_report.h)
- [MissionCommand 组件](../../../../src/components/command/mission_command.h)
- [MissionCommandAir (12 字段)](../../../../src/components/command/air/mission_command_air.h)
- [Command 组件 README（边界声明）](../../../../src/components/command/README.md)
- [PilotAction 组件](../../../../src/components/command/pilot_action.h)
- [MovementCommand / ActionCommand / CommandLag](../../../../src/components/command/legacy_command.h)
- [CommandLink / pending command 组件](../../../../src/components/command/command_link.h)
- [CommandLinkSystem（投递调度）](../../../../src/systems/systems/command_link_system.h)
- [CommMessage / CommQueue / CommPacket](../../../../src/components/command/common/comm_message.h)
- [DataLinkSystem（航迹共享 + 消息分发）](../../../../src/systems/systems/data_link_system.h)
- [MissionCommandCodec（JSON 编解码）](../../../../src/core/mission/episode/detail/mission_command_codec.h)
- [ExecutionEpisodeController](../../../../src/core/mission/episode/execution_episode_controller.h)
- [DefaultControlModel（命令消费端）](../../../../src/models/air/default_control_model.cpp)
- [SimulationKernel 命令 API](../../../../src/core/engine/simulation_kernel_command_api.cpp)
- [LeaderTasking（Python C2 任务管理器）](../../../../python/rl/tasking/leader_tasking.py)
- [LeaderCommandBridge](../../../../gym_envs/leader_env_parts/bridges.py)
- [LeaderEnv commands.py](../../../../gym_envs/leader_env_parts/decision_runtime/commands.py)
- [AirProfile（空中命令构建）](../../../../python/rl/profile/air_profile.py)
- [NavalProfile（海军命令构建）](../../../../python/rl/profile/naval_profile.py)
- [C2 通信与指挥链前瞻](../../../systems/command-tasking/work/issues/c2_communication.zh.md)
- [海军任务最小结构](../../../domains/naval/standards/minimal_task_structure.md)

文档定位：

- 本文档仅记录当前指挥链与 C2 通信管线的已知缺陷及其对应的真实军事指挥与控制情况。
- 不涵盖可接受的简化，不提供优先级排序，不给出工作计划。
- 空中与海军指挥链在本项目中确实具有不同的结构和成熟度，本文档分别论述并在最后进行跨域对比。
- 当前判断以本分析中的 `2026-05-18` 收口标记为准，不再引用 `program/` 或 `archive/` 作为当前状态来源。

当前状态指引：

- 本文档是冻结分析输入，不是当前执行状态看板。
- 当前与本分析直接相关的状态判断，请只参见本分析中的 `2026-05-18` 收口标记。

## 补记：`2026-05-18` 收口标记

标记口径：

- `未解决`：原论点基本仍成立。
- `部分解决`：已有局部实现或 shared contract 收口，但核心差距仍在。
- `已有最小收口`：最小运行时闭环已存在，不宜再按“完全缺失”表述。
- `已解决`：该条旧论述已不再适合作为当前状态描述。

本补记只用于判断这些 `C2` 论点今天是否仍可直接视为当前问题。

| 条目 | 当前标记 | 说明 |
|------|----------|------|
| `2.1` 指挥链按域不对称——海军侧严重欠发育 | `部分解决` | 海军侧仍明显弱于空中侧，但已从“严重欠发育”推进到最小工程闭环接入主线 |
| `2.2` `MissionCommand` 是“共享壳 + 大量空中负载” | `部分解决` | 整体仍偏 `air-shaped`，但海军专属 `station/reference` 字段已接入 |
| `2.3` 海军命令映射绕过全部任务式指挥 | `已解决` | 海军命令映射现已承载 `MissionCommand` 语义与运行时 `station/reference` 处理；当前剩余差距在更丰富的海军任务阶段语义，而不是“完全绕过任务式指挥” |
| `2.4` 两条命令管道共存——`MovementCommand` 未被废弃 | `部分解决` | 双管道仍在，但 `Ship` 主 authority 已从 `MovementCommand` 收回到 `MissionCommand` |
| `2.5` `CommandLink` 模型过于简化 | `部分解决` | 已有 `FIFO backlog + 最小 priority reorder`，但仍无 `ACK/retry/jitter/multi-hop` |
| `2.6` 通信消息系统没有带宽/电磁对抗约束 | `部分解决` | 已不再是无限广播，`budget/drop/debug` 已接入，但仍无 `relay/jamming` |
| `2.7` `PilotAction` 和 `MissionCommand` 的控制权竞争 | `已有最小收口` | 已有最小 `deadband` 接管语义，但仍无完整 mode-state/hysteresis |
| `2.8` 无交战规则（ROE）状态机 | `部分解决` | 已有最小 `roe_state + authority gate`，但仍非完整 `ROE` 状态机 |
| `2.9` 无指挥关系中的交战权转移 | `未解决` | authority transfer / revoke / inheritance 仍未落地 |
| `2.10` `LeaderIntent ↔ MissionCommand` 之间的编解码冗余 | `部分解决` | 冗余仍在，但 roundtrip/codec 漂移已被显式守门测试部分压住 |
| `2.11` 编队控制仅在空中侧建模——海军无编队逻辑 | `部分解决` | 海军仍无完整编队控制回路，但已具最小 `station/reference/formation` 承载 |

---

## 一、当前指挥链架构

项目实现了五层指挥链，从战略任务分配延伸到物理舵面：

```
Layer 5: TaskOrder        → C2 任务分配（谁执行什么任务、在哪里、和谁协同）
Layer 4: LeaderIntent     → 领导者决策（当前阶段、目标航向/高度/速度、交战授权）
Layer 3: MissionCommand   → 编译后的执行命令（自动驾驶仪/舰船可消费的航向/高度/速度）
Layer 2: MovementCommand  → 遗产通用运动指令（或 PilotAction → 直接杆量/油门）
Layer 1: ControlModel     → 物理执行（FBW 自动驾驶仪 / 舰船航向-航速追踪）
```

命令流经 `CommandLink`（延迟 + 丢包），经由 `Pending*Command` 队列延迟投递。

---

## 二、已知失真点

### 2.1 指挥链按域不对称——海军侧严重欠发育

空中指挥链有 47 字段 TaskOrderAir + 33 字段 LeaderIntentAir + 12 字段 MissionCommandAir，覆盖编队、起降、进近、僚机、CAP 站位等。海军侧 `TaskOrderNaval` / `LeaderIntentNaval` / `PilotReportNaval` 实际上共享同一对字段：

```cpp
// naval_tasking_enums.h + task_order_naval.h / leader_intent_naval.h / pilot_report_naval.h
NavalWarfareRole warfare_role_code;    // ScreenCommander / SurfaceActionCommander / ...
NavalStationType naval_station_type;   // Screen / Support / PatrolStation / ...
// TaskOrderNaval 额外有: officer_in_tactical_command
```

真实海军指挥链的复杂度不低于空中——一个航母战斗群的 C2 涉及：

- **复合战区指挥官（CWC，Composite Warfare Commander）** 概念：将战术指挥分解为防空战指挥官（AAWC）、反潜战指挥官（ASWC）、反水面战指挥官（SUWC）等多个职能指挥官，每个有独立的职责和交战授权
- **交战权（Weapon Release Authority）** 的分层委派：从 OTC（Officer in Tactical Command）逐层下放到 Warfare Commander → 单元指挥官 → 武器控制官（WCO）。不同武器类型有不同的交战权阈值（自防御 CIWS 为自动、反舰导弹需要 AAWC 授权、对陆攻击需要 OTC 授权）
- **协同交战能力（CEC，Cooperative Engagement Capability）**：允许一艘舰使用另一艘舰的雷达数据进行火控解算并发射导弹。当前 CEC 完全不建模——没有"远程交战"（engage on remote）语义、没有传感器-射手（shooter-sensor）配对
- **Link 16 的指挥关系框架**：J12.x 系列消息承载任务分配（tasking order）、交战状态（engagement status）和武器协同（weapon coordination）。当前 `DataLinkSystem` 仅共享 `ContactList` 而不承载任何任务下达
- **海上编队的动态 OTC 转移**：当 OTC 舰被击伤或通信中断时，指挥权需按预设继承顺序转移。当前无指挥权转移逻辑

### 2.2 MissionCommand 是"共享壳 + 大量空中负载"

源码 README 对此有坦承声明：

> `CommandLink` 比 `MissionCommand` 更接近真正的共享核心；`MissionCommand` 目前仍更像"共享壳 + 大量 air 负载"。

```cpp
// MissionCommand 的 flat 结构
cmd_heading_deg, cmd_altitude_m, cmd_speed_mps  // 通用，源自 MissionCommandCore
command_code (0/1/2/3/4 = IDLE/TAKEOFF/VECTOR/ROUTE/LANDING)  // 通用
// 但 command_code 值域全部是飞行语义——IDLE/TAKEOFF/LANDING 对舰船无意义

// MissionCommandAir: 12 字段全部是航空专用
recovery_base_id, recovery_runway_id, recovery_approach_type  // 着陆/进近
takeoff_procedure_id, takeoff_clearance_id, takeoff_interval_s, runway_slot_id  // 起飞
formation_id, form_offset_x/y/z  // 编队
```

真实海军 MissionCommand（或称"运动指令/阵位指令"）应包含：

- **阵位指派**：相对于参考单元（通常是 HVU 或编队旗舰）的方位和距离（如"DDG-51 站位 HVU 前方 10 nmi，左舷 30°"），而非绝对航向/高度
- **巡逻区/搜索扇区**：屏护舰的巡逻责任区（a sector of responsibility）
- **威胁轴**：预期威胁方向，影响屏护舰的优先站位和传感器指向
- **交战规则状态**：WEAPONS FREE / WEAPONS TIGHT / WEAPONS HOLD 区分
- **辐射控制（EMCON）状态**：限制雷达/通信发射以降低被探测概率
- **舰船不应有"command_code = TAKEOFF/LANDING"**——当前海军档案硬编码 `command_code = 3 (ROUTE)`，将一切驱逐舰行为等同于"沿航路飞行"

### 2.3 海军命令映射绕过全部任务式指挥

`naval_profile.py:build_kernel_mission_command()` 仅从 `task_order` 简单提取航向/航速，硬编码命令码为 3。这意味着：

- **无任务阶段转换**：空中侧有 SCRAMBLE → CAP → RTB → RECOVER_LAND 的完整状态机（`ScriptedC2TaskManager`，701 行），海军侧无等效物——DDG-51 从开始到结束处于同一状态
- **无阵位到达/离开判断**：空中 CAP 有基于半径-高度-速度区间的阵位到达检测。海军侧无屏护站位到达标准
- **无任务驱动的传感器/武器状态切换**：空中任务状态影响雷达模式、武器选择、燃油管理。海军侧传感器和武器根本不在任务控制之下（部分原因是它们尚不存在运行时实现）

### 2.4 两条命令管道共存——MovementCommand 未被废弃

源码中存在两个活跃的命令注入通道，彼此独立：

```
通道 A: TaskOrder → LeaderIntent → MissionCommand → MissionCommand 自动驾驶仪
通道 B:                 └→ set_unit_command() → MovementCommand → 各种消费者
通道 C: set_pilot_action() → PilotAction → ControlModel（绕过后全部上层）
```

`MovementCommand` 和 `ActionCommand` 被标记为"遗产"（legacy），但仍被以下途经积极使用：

- `SimulationKernel::set_unit_command()` ——写入 `MovementCommand`，绕过 `MissionCommand`
- `CommandLinkSystem` 中有独立的 `CommandLinkMovement`、`CommandLinkAction`、`CommandLinkMission` 三个投递系统
- 海军命令在 `command_link_system.h:72-84` 中专设分支：MissionCommand 投递后额外生成一个派生的 MovementCommand

真实指挥链不区分"任务命令"和"运动命令"是两个独立管道——这不是两条路径的设计，而是一个层次化的命令分解：

```
任务式命令（"屏护 HVU 免遭来自 090 方向的威胁"）
  → 阵位指派（"站位 HVU 前方 10 nmi"）
    → 运动指令（"航向 090，航速 15kt"）
      → 自动驾驶仪/舵手/轮机控制（舵角 + 油门）
```

当前两条管道的共存意味着同一个实体可能同时持有内容不一致的 MissionCommand 和 MovementCommand，消费端（控制模型）没有明确的优先级和冲突解决语义。

### 2.5 CommandLink 模型过于简化

当前命令延迟模型对每一条命令独立施加：

- 固定延迟 `latency_s`（秒）
- 独立丢包概率 `drop_prob` [0, 1]
- 投递判定为确定性伪随机（SplitMix64，基于 `floor(current_time*1000) ^ entity_id`）

真实战术数据链的命令投递面临更复杂的约束：

- **时隙竞争**：Link 16 的 TDMA 时隙是稀缺资源。在密集作战期间，多条命令排队竞争同一时隙，产生**排队延迟**（queuing delay），其统计特性是长尾的——偶尔出现数秒级别的抖动
- **命令优先级**：不是所有命令平等——交战命令（engage）的优先级高于阵位调整命令。当带宽饱和时，低优先级命令被延迟到下一帧
- **命令序列完整性的保证**：真实系统需要保证命令序列的完整性和顺序——如果命令 #3 在命令 #2 之前投递，可能导致矛盾状态。当前每帧独立判定丢包，无序列号/排序/去重
- **无确认/重传**：Link 16 的点对点消息有 ACK/NACK 机制。重要的命令如果未被确认，将被重传。当前命令发出后无反馈——发送方不知接收方是否收到
- **延迟参数是单位级常量**：真实延迟取决于：网络拓扑（几跳）、时隙分配周期（通常 3-12 秒）、发送方和接收方的时隙偏移。从 AWACS 到 F-16 的一条命令经历 AWACS→Link 16 时隙→F-16 接收处理，总延迟 0.5-6 秒不等。当前单一 `latency_s` 无法表达多跳和时隙等待的结构
- **一次只投递一条命令**：`Pending*Command` 仅保留最新一条待投递命令。如果发送方在第一条命令投递前发出第二条，第一条将被静默覆盖。这在快速变化的战术态势中可能导致关键命令丢失

### 2.6 通信消息系统没有带宽/电磁对抗约束

`DataLinkSystem` 的 `CommPacket` 分发机制是无损的：

- 在同一网络 + 同阵营 + 视距内的任意两个实体之间，消息总是即时无差错送达
- 无带宽上限——可以在单帧内广播无限消息
- 消息的 0.5 秒 TTL 清除是一个工程近似（清理旧的收件箱条目），但不是真实的通信约束

真实战术通信面临：

- **电磁对抗（jamming）**：敌方干扰可降低或阻断特定频段的通信。Link 16 使用扩频（FHSS，跳频扩频）抗干扰，但在强干扰下仍会丢失数据
- **平台间通信可能有中继限制**：不是所有平台都能直接与所有平台通信。超视距通信需要中继（relay）节点，引入了额外的延迟和单点故障
- **语音和数据共享带宽**：实际可用带宽在数据（J-series 消息）和语音（加密数字语音）之间分配

### 2.7 PilotAction 和 MissionCommand 的控制权竞争

`DefaultControlModel::update()` 第 119-130 行：

```cpp
if (has_pilot) {
    // [A] Manual / RL Control ——直接使用杆量
} else if (has_mission) {
    // [B] Mission-command autopilot ——将 MissionCommand 转换为杆量
} else {
    // [C] No Command ——仅 SAS 阻尼
}
```

当 `PilotAction` 和 `MissionCommand` 同时存在且均为 active 时，`PilotAction` 无条件覆盖 `MissionCommand`。此优先级逻辑未在任何文档中记录，消费端更无"冲突告警"——如果 RL 策略在 MissionCommand 执行期间意外激活 PilotAction，自动驾驶仪被静默禁用。

真实现代飞机（F-16、F/A-18）有明确的**自动驾驶仪/手动控制模式切换**逻辑：

- 自动驾驶仪的脱开（disengage）需要明确的飞行员动作（按下操纵杆上的脱开按钮）或在杆力超过阈值时自动脱开
- 自动驾驶仪工作时，操纵杆的微动（如飞行员无意识触碰）不应导致脱开
- 恢复自动驾驶仪需要明确的"重新接通"动作

当前无任何滞后（hysteresis）、无脱开阈值、无重新接通逻辑——仅仅是 `if (pilot && pilot->active)` 就切换了。

### 2.8 无交战规则（ROE）状态机

`MissionCommandCore` 有 `authorization_to_fire`（bool），但这是一个瞬时快照状态，而非规则驱动的状态机。

真实交战规则：

- **WEAPONS HOLD**：仅在自卫时可开火（敌方已开火或明确表现出即将开火的意图）
- **WEAPONS TIGHT**：仅在确认目标身份为 hostile 且有交战授权时可开火
- **WEAPONS FREE**：可对任何未识别为 friend 的目标开火
- 状态之间的转换需要特定条件（敌我识别、威胁评估、指挥官批准），且通常有交战后审查（post-engagement review）
- ROE 状态和 IFF 状态联动——一个被分类为"suspect"的目标在 WEAPONS TIGHT 下不可交战，但在 WEAPONS FREE 下可以

当前 `authorization_to_fire` 的布尔开关将整个交战规则维度压缩为一个位。

### 2.9 无指挥关系中的交战权转移

空中侧和海军侧均不建模交战权（Engagement Authority）的委托和转移。

真实联合作战中：

- AWACS 可以委托交战权给战斗机编队的长机
- 长机可以进一步委托给僚机
- 数据链上存在正式的"交战状态"报告：ENGAGED（已交战）、ENGAGING（正在交战）、ENGAGE（交战许可）
- 当授权节点被击落或通信中断时，交战权有预设的继承链

当前 `leader_intent.authorization_to_fire` 和 `mission.assigned_target_id` 仅能表达"长机指定了一个目标并授权开火"，无法表达授权的沿袭、撤销、转移或继承。

### 2.10 LeaderIntent ↔ MissionCommand 之间的编解码冗余

C++ 侧有 `MissionCommandCodec`（JSON 序列化/反序列化），Python 侧有 `build_kernel_mission_command()`（从 Python dict 重组 MissionCommand）。两个编解码路径独立维护：

- C++ 编解码器在 `mission_command_codec.h` / `.cpp` 中，负责 `ExecutionEpisodeState::mission_command_json`
- Python 构建器在 `air_profile.py:529` 中，负责从 `leader_intent` + `loader.mission_cmd` 构建 MissionCommand C++ 对象
- 两条路径对 `command_code` 的解析逻辑不同：Python 侧使用 `parse_mission_command_from_dict()` 直接从 JSON 字段推断，C++ 侧使用 `build_state_mission_command_json()` 从结构体序列化。如果两者对某一字段的默认值或枚举映射不同，会产生静默分歧

### 2.11 编队控制仅在空中侧建模——海军无编队逻辑

`LeaderIntentAir` 包含完整的编队控制字段：`formation_id`、`form_offset_x/y/z`、`FormationMode`（LineAbreast / EchelonLeft / EchelonRight / Wedge / Trail 等）、`WingmanCommandMode`、`join_flag`、`split_flag` 等。

海军侧没有等效物——没有多舰编队站位（扇形屏护 / 环形屏护 / 纵队）、没有舰间间距维护、没有编队转弯协调（simultaneous turn vs sequential turn）。

真实海军编队——哪怕是最简单的两舰屏护——也要求：

- 屏护舰相对于 HVU 的站位定义（bearing + range from HVU）
- 站位误差的持续监控和修正（station-keeping）
- 编队航向/航速变更时的协调机动
- 威胁方向变化时屏护舰的重新站位

当前 DDG-51 被放在 HVU 前方 8 nmi 处并以相同航向航速运行——这是一个初始几何条件，不是编队控制回路的产物。

---

## 三、空中与海军指挥链差异总结

| 维度 | 空中 | 海军 |
|------|------|------|
| TaskOrder 专属字段 | 47 字段（跑道/编队/CAP/进近） | 3 字段（warfare_role / station_type / OTC） |
| LeaderIntent 专属字段 | 33 字段（编队/僚机/支援锚点） | 2 字段（warfare_role / OTC） |
| MissionCommand 专属字段 | 12 字段（起降/跑道/进近/编队） | 无。海军使用通用 MissionCommandCore |
| command_code 语义 | 全值域（IDLE/TAKEOFF/VECTOR/ROUTE/LANDING） | 硬编码 3 (ROUTE) |
| 控制模型 | 完整 FBW + 自动驾驶仪（起飞/巡航/进近模式） | 无。通过 MissionCommand→MovementCommand 桥接回退为航向-航速追踪 |
| 任务阶段状态机 | 有（SCRAMBLE→CAP→RTB→RECOVER_LAND） | 无 |
| 协调模式 | Independent / Attached / Recover | Screen / Support / Detached |
| 编队控制 | 完整（5 种编队模式 + 站位偏移 + 加入/脱离） | 无。初始几何仅由场景 JSON 设定 |
| 任务族 | Transit / Patrol / Recover | Escort / Patrol / Recover |
| 命令投递后处理 | FBW 自动驾驶仪消费 MissionCommand | `command_link_system.h` 中专设 Ship→MovementCommand 分支 |

**核心不对称**：空中侧从 TaskOrder 穿透到 ControlModel 是全链路贯通的（五层全部有代码）。海军侧的 Layer 2-1（MovementCommand → ControlModel）是借用的航空遗产代码层，Layer 5-3 仅有三字段占位。海军的指挥链目前是"上部挂载了海军枚举的航空管道"。

---

## 四、当前不应采用的表述

为避免后续语义漂移，当前以下表述应明确避免：

1. 不应将当前指挥链称为"联合作战 C2 仿真"——它是
   **"航空任务式指挥 + 海军枚举占位符 + 遗产运动指令管道"**。
2. 不应将当前 `TaskOrderNaval` / `LeaderIntentNaval` 称为"海军任务式指挥"——它们是
   **"共享航空命令框架 + 2-3 个海军枚举字段的占位扩展"**，
   无阵位指派语义、无交战权委托、无巡逻区/威胁轴建模。
3. 不应将当前 `CommandLink` 称为"战术数据链命令投递仿真"——它是
   **"每命令独立固定延迟 + 独立丢包概率"**，
   无时隙竞争、无命令优先级、无确认/重传、无序列号保证。
4. 不应将当前数据链消息系统称为"战术通信仿真"——它是
   **"同网同阵营无损耗即时消息广播"**，
   无带宽约束、无干扰对抗、无中继需求。
5. 不应将当前 `authorization_to_fire` 称为"交战规则（ROE）建模"——它是
   **"一个布尔开关"**，
   无 WEAPONS HOLD/TIGHT/FREE 状态机、无 IFF 联动、无交战权委托。
6. 不应将当前海军侧命令映射称为"舰艇 C2"——它是
   **"硬编码 command_code=3 (ROUTE) 的航向-航速追踪器"**，
   无阵位控制、无巡逻区、无威胁响应、无编队协调。

本结论冻结到下一次明确重开指挥链/C2 推进前为止。
