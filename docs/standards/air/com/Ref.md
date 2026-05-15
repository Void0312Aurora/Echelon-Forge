# 现有代码组件与新标准映射参考 (Component Mapping & Gap Analysis)

> ARCHIVED NOTE (2026-03-23): 该文档属于旧的 air-specific 标准化路线，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/CMO/docs/standards/README.md)。

本文档旨在梳理 `src/components` 下现有的 C++ 数据结构与新定义的 [飞行员标准](../) 之间的映射关系，并识别满足“拟真化”要求的改进点。

## 1. 观测空间映射 (`obs.md` vs Code)
目前的物理真值广泛分布在 `basic` 和 `physics` 组件中，但缺乏面向 AI 的仪表级封装。

| 标准观测项 (`obs.md`) | 现存 C++ 组件及字段 | 状态 | 改进建议 |
| :--- | :--- | :--- | :--- |
| `alt_baro / radar` | `Transform::z` ([common.h:31]) | ⚠️ 混合 | 需区分海平面高度与离地间隙（Radar Alt）。 |
| `ias / mach` | `Velocity` ([common.h:38]) + `AeroState` | ✅ 已包含 | `AeroState` 中已有 Mach，IAS 需增加计算逻辑。 |
| `pitch / roll / heading` | `Transform::pitch / roll / heading` ([common.h:33]) | ✅ 对应 | 字段完全匹配。 |
| `aoa / beta` | `AeroState::aoa / sideslip_angle` | ✅ 对应 | 来源于 `AeroStateSystem` 计算。 |
| `g_load` | 无直接组件 | ❌ 缺失 | 需在每一帧根据加速度计算法向 G 值并存储。 |
| `engine_rpm / temp` | 无 | ❌ 缺失 | `Propulsion` 目前仅有推力数值，无动态状态。 |
| `fuel` | `FuelSystem` ([logistics.h:47]) | ✅ 对应 | `internal_fuel_kg` 与 `external_fuel_kg` 匹配。 |

## 2. 操作空间映射 (`act.md` vs Code)
目前的操作指令高度混合，急需解耦。

| 标准操作项 (`act.md`) | 现存 C++ 组件及字段 | 状态 | 改进建议 |
| :--- | :--- | :--- | :--- |
| `stick_pitch / roll` | `MovementCommand::stick_pitch / roll` ([action.h:12]) | ✅ 对应 | 结构匹配，但需从 `MovementCommand` 剥离。 |
| `throttle_lever` | `MovementCommand::throttle_cmd` ([action.h:14]) | ✅ 对应 | 需确保其驱动 `PropulsionSystem` 产生非线性推力。 |
| `rudder_pedals` | 无 | ❌ 缺失 | 目前尚无航向舵控制逻辑。 |
| `gear_handle` | `MovementCommand::gear_handle` ([action.h:15]) | ✅ 对应 | 已有布尔开关。 |

## 3. 长机指令映射 (`aim.md` vs Code)
长机指令目前被错误地放置在了 `MovementCommand` 的核心字段中。

| 标准指令项 (`aim.md`) | 现存 C++ 组件及字段 | 状态 | 改进建议 |
| :--- | :--- | :--- | :--- |
| `cmd_heading / alt / speed` | `MovementCommand::target_heading / alt / speed` ([action.h:6]) | ⚠️ 混乱 | 应将其移入专门的 `MissionCommand` 组件，不应与 `stick` 共存；且这些字段必须被解释为命令绑定参数，而不是所有任务共享的通用自由变量。 |
| `CODE_TAKEOFF / CRUISE` | 无 | ❌ 缺失 | 现有的 `MovementCommand` 缺乏任务语义（Task Semantic）。 |

## 4. 汇报机制映射 (`rep.md` vs Code)
通讯系统已有模板，但战术语义尚为空白。

| 标准汇报项 (`rep.md`) | 现存 C++ 组件及字段 | 状态 | 改进建议 |
| :--- | :--- | :--- | :--- |
| `CommMsgType` | `CommMsgType` ([comm.h:6]) | ⚠️ 半成品 | 仅有 `ReportContact` 等基础项，需补全 `REP_WILCO`, `REP_BINGO` 等。 |
| `CommPacket` | `CommPacket` ([comm.h:14]) | ✅ 结构可用 | 数据包结构（Sender, Receiver, Type）非常稳健。 |

## 5. 综合判定与下一步逻辑重构建议

与本目录中的新增标准文档配合使用：
- [Task Order & Leader Layer Standard](./task_order_leader_standard.md)
- [CAP 任务与长机层落地计划](./cap_task_bootstrap_plan.md)
- [双机阶段标准总览](./two_ship/README.md)

该文档定义了 `C2 -> 长机层 -> 执行层 -> 操作层` 的标准职责划分，以及
`TaskOrder / LeaderIntent / PilotReport` 的目标接口。

新增的落地计划文档则进一步限定了第一阶段的最小参数子集、代码落点和里程碑，
适合直接作为后续实现与测试的工程参考。

通过以上对照，`src/components` 的重构重点应集中在：

1.  **解耦 `action.h`**: 
    *   将 `MovementCommand` 拆分为 `MissionInput` (长机给的) 和 `PilotControl` (飞行员做的)。
    *   这将彻底终结“脚本飞行员”在同一个结构体里自问自答的混乱状态。
2.  **强化 `comm.h`**: 
    *   根据 `rep.md` 扩展 `CommMsgType` 枚举，使 AI 能够输出结构化的“战术语言”。
3.  **新增 `instrumentation.h`**:
    *   作为物理真值到 AI 观测的过滤层。即使物理引擎内部使用平铺坐标，提供给 AI 的必须是模拟座舱仪表的相对数据。

**结论**: 现有代码提供了强大的 ECS 骨架，但由于早期为了快速实现 MVP (最小可行性产品)，在**“指挥层目标”**和**“执行层操作”**之间缺乏防火墙。修复这个数据结构的断裂是实现高性能 Transformer 训练的前提。
