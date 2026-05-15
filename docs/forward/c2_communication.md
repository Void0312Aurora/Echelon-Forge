# C2 通信与指挥链前瞻

本文件记录指挥链路与通信约束的规划与当前实现。

## 当前实现（最小可用）
- CommandLink：指令延迟与丢包率（单位级别）。
- PendingCommand：指令排队并在指定时间投递。
- 同时支持 MovementCommand 与 ActionCommand。

相关代码入口：
- 数据结构：`src/components/action.h`
- 链路系统：`src/systems/command_link_system.h`
- 投递逻辑：`src/core/simulation_kernel.cpp`

## 设计目标
1) 引入真实的指挥链路限制（延迟/丢包/频宽）。
2) 支持分层指挥（上层目标 -> 中层任务 -> 底层动作）。
3) 能够在训练中模拟通信损伤与链路退化。

## 后续扩展
- 带宽/频率限制：高频命令被节流或降采样。
- 多跳链路：指挥节点之间的中继延迟与丢包。
- 任务式命令：下达目标点/巡逻区而非连续控制量。
- C2 节点摧毁：链路失效与自主模式切换。
