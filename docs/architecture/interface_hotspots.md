# 接口修改热点清单

> ARCHIVED NOTE (2026-03-23): 该清单基于旧的 air-first 标准化路线整理，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/CMO/docs/standards/README.md)。

本文档只回答一个问题：

“如果我们现在要把各层接口按新标准固化，应该优先改哪些组件？”

## 1. 一级热点：一定会改

### 1.1 `src/components/physics/action.h`

原因：

- `MissionCommand`
- `TaskOrder`
- `LeaderIntent`

都在这里定义。

如果要让参数按 `command_code` 绑定，这里必须先改。

### 1.2 `src/interfaces/python/python_module.cpp`

原因：

- 所有 Python 训练、测试、可视化都依赖这里暴露的字段。
- 只改 C++ 不改绑定，Python 层会立刻失配。

### 1.3 `python/rl/leader_tasking.py`

原因：

- 当前 `LeaderIntent -> MissionCommand` 的映射规则在这里。
- `TaskOrder`、`PilotReport` 的规则桥也在这里。

### 1.4 `gym_envs/leader_env.py`

原因：

- 当前长机动作解码、命令 guard、命令写回都在这里。
- 这是“通用三元组”历史设计最集中的地方。

## 2. 二级热点：大概率要改

### 2.1 `gym_envs/scenario_loader.py`

原因：

- 运行时 `mission_cmd`
- waypoint / ILS / runway 几何
- `post_waypoint_transition`

都集中在这里。

只要 `MissionCommand` 解释规则变了，这里就几乎一定要跟着改。

### 2.2 `src/models/air/default_control_model.cpp`

原因：

- 当前在没有 `PilotAction` 时，直接把 `MissionCommand` 当 autopilot 输入。
- 如果 `MissionCommand` 从“通用三元组”改成“命令绑定参数”，这里必须同步改解释逻辑。

### 2.3 `python/rl/wrappers.py`

原因：

- 若脚本基线切换仍假设旧 `command_code` 口径，这里会出现隐性错配。

## 3. 三级热点：回归时必须检查

### 3.1 `python/testing/scenario_contract_runner.py`

原因：

- 这里会把很多运行时对象重新解释成合同检查项。

### 3.2 `examples/viz/viz_runner.py`

原因：

- 可视化侧需要知道 leader/execution 两条链如何接入。

### 3.3 `src/systems/physics/instrument_system.h`

原因：

- 这里定义了 command bugs 如何呈现在 `InstrumentState` 中。
- 若 `MissionCommand` 字段语义变化，仪表层要检查是否仍然合理。

## 4. 最小改动顺序

若只想先把接口收紧，不立刻重训，建议严格按这个顺序：

1. `action.h`
2. `python_module.cpp`
3. `leader_tasking.py`
4. `leader_env.py`
5. `scenario_loader.py`
6. `default_control_model.cpp`
7. `wrappers.py`
8. `scenario_contract_runner.py`
9. `viz_runner.py`

## 5. 修改前检查清单

在开始改接口前，建议先确认：

- 新的 `TaskOrder` 字段是否已经在文档中冻结
- 新的 `LeaderIntent` 是否仍保留 legacy 兼容字段
- `MissionCommand` 是否允许短期双轨兼容
- 现有执行层模型是否需要过渡适配层
- 现有合同哪些是“结构合同”，哪些是“行为合同”

只有这些问题先定下来，后续代码修改才不会反复返工。
