# C2 通信与指挥链前瞻

Language:
- English canonical: [c2_communication.md](c2_communication.md)
- Chinese companion: `c2_communication.zh.md`

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/command-tasking/work/issues/c2_communication.md`
Owner: `systems/command-tasking`
Last verified: `not established`
Content status: not reverified during the 2026-08-07 ownership migration.

本文件记录指挥链路与通信约束的规划与当前实现。

## 当前实现（最小可用）
- CommandLink：指令延迟与丢包率（单位级别）。
- 延迟投递由 `command_link.h` 中的具体 pending command 组件表示：
  `PendingMovementCommand`、`PendingActionCommand` 和
  `PendingMissionCommand`。当前没有通用的 `PendingCommand` 类型。
- 支持 `MissionCommand` 投递，也保留面向 legacy `MovementCommand` 与
  `ActionCommand` 表面的维护中兼容桥接。

相关代码入口：
- 链路状态与 pending command 数据：
  `src/components/command/command_link.h`
- legacy movement/action 兼容 DTO：
  `src/components/command/legacy_command.h`
- 链路系统：
  `src/systems/systems/command_link_system.h`
- 命令 API 排队逻辑：
  `src/core/engine/simulation_kernel_command_api.cpp`

## 设计目标
1) 引入真实的指挥链路限制（延迟/丢包/频宽）。
2) 支持分层指挥（上层目标 -> 中层任务 -> 底层动作）。
3) 能够在训练中模拟通信损伤与链路退化。

## 后续扩展
- 带宽/频率限制：高频命令被节流或降采样。
- 多跳链路：指挥节点之间的中继延迟与丢包。
- 任务式命令：下达目标点/巡逻区而非连续控制量。
- C2 节点摧毁：链路失效与自主模式切换。
