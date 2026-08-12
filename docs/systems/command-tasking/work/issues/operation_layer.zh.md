# 操作层与动作空间

Language:
- English canonical: [operation_layer.md](operation_layer.md)
- Chinese companion: `operation_layer.zh.md`

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/command-tasking/work/issues/operation_layer.md`
Owner: `systems/command-tasking`
Last verified: `not established`
Content status: not reverified during the 2026-08-07 ownership migration.

本文档提出桥接 AI 决策与控制模型的操作层；在 owner 完成核验前，它只是草拟的
动作空间参考。

## 在技术栈中的位置
- AI/策略生成动作。
- 操作层将动作映射为稳定、有界的指令。
- 控制模型消费指令并施加物理限制。

数据流：
AI动作 → 操作层 → MovementCommand → ControlModel → Velocity/Transform

## 动作级别
1. 高层目标（绝对量）
   - target_heading（度，导航模式）
   - target_speed（米/秒）
   - target_altitude（米）
   - fire（布尔值）
   优点：简单。缺点：策略必须显式管理约束。

2. 速率级指令（归一化）
   - turn_rate_cmd 取值 [-1, 1] → 度/秒
   - accel_cmd 取值 [-1, 1] → 米/秒²
   - climb_rate_cmd 取值 [-1, 1] → 米/秒
   - fire_cmd 取值 [0, 1]
   优点：训练信号稳定，易于钳制。

3. 离散战术动作（可选）
   - turn_left、turn_right、accelerate、decelerate、climb、dive、fire
   - 映射为固定幅度的速率级指令。

## 默认动作空间（飞行器）
使用速率级指令作为AI代理的默认控制接口。

参数（按单位类型或场景设定）：
- max_turn_rate_deg_s
- max_accel_mps2
- max_climb_rate_mps
- min_speed_mps、max_speed_mps
- min_alt_m、max_alt_m

映射（每时间步）：
1) turn_rate = turn_rate_cmd * max_turn_rate_deg_s
2) accel = accel_cmd * max_accel_mps2
3) climb_rate = climb_rate_cmd * max_climb_rate_mps
4) 积分得到目标：
   - target_heading += turn_rate * dt
   - target_speed += accel * dt
   - target_altitude += climb_rate * dt
5) 将目标钳制到边界，并填充 MovementCommand。

说明：
- 使用 FlightModel 的限制来收紧边界（失速 + 最大过载）。
- 将航向钳制到 [0, 360) 导航角度。
- 维护每个代理的指令状态（航向/速度/高度）以实现平滑积分。

## 动作空间接口（计划实现）
- ActionSpaceConfig：保存边界和速率限制。
- AgentAction：针对一个单位的归一化向量。
- ActionMapper：将 AgentAction 转换为 MovementCommand。

## 日志记录
在场景日志中记录动作和观测值：
- 原始动作向量
- 映射后的 MovementCommand
- 衍生限制（有效最低速度、过载限制的转弯速率）

## 后续步骤
- 将 ActionSpaceConfig 添加到 content/ 或场景文件中。
- 实现一个供 Python gym 环境使用的 ActionMapper。
- 添加从 Python 设置/获取动作空间的绑定。

## 当前实现说明
- 组件：`ActionCommand`、`ActionSpaceConfig`、`CommandLag`、`LaggedCommand`。
- 系统：`ActionMapping`（ActionCommand → MovementCommand）和 `CommandLag`。
- 控制模块消费 `LaggedCommand`，因此指令延迟适用于所有被指令的飞行器。
