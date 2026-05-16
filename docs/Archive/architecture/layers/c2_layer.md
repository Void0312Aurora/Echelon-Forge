# C2 层

> ARCHIVED NOTE (2026-03-23): 该文档属于旧的 air-specific 架构拆分说明，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/Workshop/CMO/docs/standards/README.md)。

## 1. 职责

C2 层负责：

- 定义任务线程
- 发布 `TaskOrder`
- 维护任务优先级与退出条件
- 根据长机回报切换 `TASK_SCRAMBLE / TASK_CAP / TASK_RTB / TASK_RECOVER_LAND`

C2 层不负责：

- 直接生成舵面
- 直接驱动终端进近
- 在每个仿真步手工改飞机姿态目标

## 2. 当前代码落点

### 2.1 场景配置入口

- [`scenarios/combined/`](/home/void0312/Workshop/CMO/scenarios/combined)
- [`examples/config/training/`](/home/void0312/Workshop/CMO/examples/config/training)

场景 JSON 中的这些区域直接影响 C2 任务语义：

- `meta.initial_c2_task`
- `c2_logic`
- `task_order`
- `mission_command`

### 2.2 Python 任务管理器

- [`python/rl/tasking/leader_tasking.py`](/home/void0312/Workshop/CMO/python/rl/tasking/leader_tasking.py)

关键类：

- `ScriptedC2TaskManager`

它负责：

- 读取 `TaskOrder`
- 接收 `PilotReport`
- 按规则推进 `TASK_SCRAMBLE -> TASK_CAP -> TASK_RTB -> TASK_RECOVER_LAND`
- 把当前任务状态写回 `ScenarioLoader`

### 2.3 场景装载桥

- [`gym_envs/scenario_loader/core.py`](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)

`ScenarioLoader` 负责把场景里的 `task_order`、`mission_command`、`post_waypoint_transition` 等配置装配进运行时状态。

## 3. 输入与输出

### 输入

- 场景 JSON
- 长机回报 `PilotReport`
- 自机当前状态、站位时间、回收窗口等派生量

### 输出

- `TaskOrder`
- 当前 `c2_task_name / c2_task_id`
- 任务转换原因与报告合法性状态

## 4. 目前最该关注的接口

如果要改 C2 层接口，优先看：

1. [`python/rl/tasking/leader_tasking.py`](/home/void0312/Workshop/CMO/python/rl/tasking/leader_tasking.py)
2. [`gym_envs/scenario_loader/core.py`](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)
3. [`src/components/physics/action.h`](/home/void0312/Workshop/CMO/src/components/physics/action.h)
4. [`src/interfaces/python/python_module.cpp`](/home/void0312/Workshop/CMO/src/interfaces/python/python_module.cpp)

## 5. 当前结构风险

- `TaskOrder` 已进入内核，但其字段集合仍偏最小实现。
- `recovery_approach_type` 等新增字段已经进入 C++ / Python 接口，但运行时解释逻辑仍在继续固化。
- 场景里的 `mission_command` 与 `task_order` 仍部分重叠，容易让 C2 任务语义和执行层程序语义混在一起。

## 6. 后续修改建议

若要固化 C2 接口，应优先做：

1. 先扩 `TaskOrder` 字段
2. 再扩 Python 绑定
3. 再改 `ScriptedC2TaskManager`
4. 最后再清理场景 JSON 中与 `TaskOrder` 冲突的 legacy 字段
