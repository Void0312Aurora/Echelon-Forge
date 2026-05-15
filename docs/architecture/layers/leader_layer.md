# 长机层

> ARCHIVED NOTE (2026-03-23): 该文档属于旧的 air-specific 架构拆分说明，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/CMO/docs/standards/README.md)。

## 1. 职责

长机层负责：

- 将 `TaskOrder` 展开为 phase
- 决定当前 `command_code`
- 选择 route / CAP 站位 / RTB / recovery
- 触发 `approach_armed / commit_to_land / abort`
- 向 C2 汇报 `PilotReport`

长机层不负责：

- 直接输出舵面
- 直接实现控制律
- 把所有命令统一成一组三自由度 `heading / altitude / speed`

## 2. 当前代码落点

### 2.1 规则桥与任务对象

- [`python/rl/leader_tasking.py`](/home/void0312/CMO/python/rl/leader_tasking.py)

关键对象：

- `build_kernel_mission_command()`
- `RuleBasedLeaderPhaseManager`
- `ScriptedC2TaskManager`

这部分负责：

- 构造 `TaskOrder`
- 构造 `LeaderIntent`
- 构造 `PilotReport`
- 将 `LeaderIntent` 映射为当前内核 `MissionCommand`

### 2.2 长机层训练环境

- [`gym_envs/leader_env.py`](/home/void0312/CMO/gym_envs/leader_env.py)

这部分负责：

- 构造长机层观测
- 定义长机层动作空间
- 将长机策略动作解释成 `LeaderIntent / MissionCommand / PilotReport`
- 驱动冻结执行层环境

### 2.3 batched vec env

- [`python/rl/leader_batched_vec_env.py`](/home/void0312/CMO/python/rl/leader_batched_vec_env.py)

负责长机层训练时的批量环境包装。

## 3. 输入与输出

### 输入

- `TaskOrder`
- 仪表与导航状态
- 航路/站位/terminal 几何状态
- `PilotReport`
- 执行层步进结果

### 输出

- `LeaderIntent`
- `MissionCommand`
- `PilotReport`

## 4. 当前最该关注的接口

如果要改长机层接口，优先看：

1. [`gym_envs/leader_env.py`](/home/void0312/CMO/gym_envs/leader_env.py)
2. [`python/rl/leader_tasking.py`](/home/void0312/CMO/python/rl/leader_tasking.py)
3. [`src/components/physics/action.h`](/home/void0312/CMO/src/components/physics/action.h)
4. [`src/interfaces/python/python_module.cpp`](/home/void0312/CMO/src/interfaces/python/python_module.cpp)

## 5. 当前结构风险

### 5.1 通用三元组风险

当前 `LeaderIntent` 和 `MissionCommand` 仍都以：

- `cmd_heading_deg`
- `cmd_altitude_m`
- `cmd_speed_mps`

作为核心字段。

这会诱导实现把长机层动作误做成“通用飞行参考偏置”，而不是“命令选择 + 命令绑定参数”。

### 5.2 映射责任混叠

当前这些职责还没有彻底分开：

- phase 决策
- route 选择
- terminal 进入时机
- `MissionCommand` 字段解释

尤其在 [`gym_envs/leader_env.py`](/home/void0312/CMO/gym_envs/leader_env.py) 里，动作解码、guard、命令写回都集中在一个类中，后续改口径时风险很高。

## 6. 后续修改建议

若要固化长机层接口，建议顺序是：

1. 先重定义 `LeaderIntent` 的字段语义
2. 再重构 `leader_env.py` 的动作解码
3. 再收缩 `build_kernel_mission_command()` 的映射规则
4. 最后再改训练配置与合同测试
