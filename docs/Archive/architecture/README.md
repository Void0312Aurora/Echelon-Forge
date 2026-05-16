# 项目分层结构总览

> ARCHIVED NOTE (2026-03-23): 本目录保留为“联合层/军种 profile 标准化重构”之前的代码状态快照。
> 当前标准化建模基线请改看 [docs/standards/README.md](/home/void0312/Workshop/CMO/docs/standards/README.md)。

本文档用于回答三个问题：

1. 这个项目当前的分层结构是什么。
2. 各层分别由哪些目录和组件承载。
3. 当 `TaskOrder / LeaderIntent / MissionCommand / PilotAction` 口径调整时，应优先修改哪些文件。

本目录关注“代码现状与接口落点”，不重复定义军事语义标准。语义标准以：

- [Task Order & Leader Layer Standard](/home/void0312/Workshop/CMO/docs/Archive/air_first_standards/com/task_order_leader_standard.md)
- [CAP 任务与长机层落地计划](/home/void0312/Workshop/CMO/docs/Archive/air_first_standards/com/cap_task_bootstrap_plan.md)

为准。

## 1. 主链路

当前项目的核心控制链可概括为：

`Scenario / Scripted C2 -> TaskOrder -> LeaderIntent -> MissionCommand -> PilotAction / Autopilot -> MovementCommand / Control Law -> Physics -> Instrument / Nav / Reports`

对应的主要落点如下：

- 场景与任务编排：`gym_envs/scenario_loader/core.py`
- 长机层训练环境：`gym_envs/leader_env.py`
- 通用执行层训练环境：`gym_envs/universal_env.py`
- 长机规则与任务桥接：`python/rl/tasking/leader_tasking.py`
- RL 训练与包装：`python/rl/`, `train.py`
- 内核数据结构：`src/components/physics/action.h`
- 内核主入口：`src/core/engine/simulation_kernel.{h,cpp}`
- 链路与投递：`src/systems/systems/command_link_system.h`
- 操作映射：`src/systems/core/operation_system.h`
- 仪表产物：`src/systems/physics/instrument_system.h`
- 飞控/自动驾驶：`src/models/air/default_control_model.cpp`
- Python 绑定：`src/interfaces/python/python_module.cpp`

## 2. 目录分层

### 2.1 场景与任务语义层

- `scenarios/`
- `examples/config/`
- `gym_envs/scenario_loader/core.py`

负责场景 JSON、任务参数、航点链、进近切换、随机化和回放入口。

### 2.2 C2 / 长机任务层

- `python/rl/tasking/leader_tasking.py`
- `gym_envs/leader_env.py`
- `python/rl/runtime/leader_batched_vec_env.py`

负责 `TaskOrder`、`LeaderIntent`、`PilotReport`、phase 展开、长机层 RL 接口。

### 2.3 执行层 / 飞行员层

- `gym_envs/universal_env.py`
- `python/rl/control/wrappers.py`
- `src/models/air/default_control_model.cpp`

负责执行层观测、执行层 RL/脚本控制、自动驾驶与物理飞控衔接。

### 2.4 操作层 / 物理层 / 内核层

- `src/components/`
- `src/systems/`
- `src/core/engine/`
- `src/models/`

负责 ECS 组件、系统调度、命令链路、控制律、动力学与仪表更新。

### 2.5 绑定 / 测试 / 可视化层

- `src/interfaces/python/python_module.cpp`
- `python/testing/`
- `tests/`
- `examples/viz/`
- `tools/`

负责 Python 访问、合同测试、诊断脚本、可视化与调试工具。

## 3. 推荐阅读顺序

当你要理解“从任务到飞机动作”的真实落点时，建议按下面顺序阅读：

1. [C2 层](/home/void0312/Workshop/CMO/docs/Archive/architecture/layers/c2_layer.md)
2. [长机层](/home/void0312/Workshop/CMO/docs/Archive/architecture/layers/leader_layer.md)
3. [执行层](/home/void0312/Workshop/CMO/docs/Archive/architecture/layers/execution_layer.md)
4. [操作层与物理层](/home/void0312/Workshop/CMO/docs/Archive/architecture/layers/operation_physics_layer.md)
5. [内核绑定、测试与可视化](/home/void0312/Workshop/CMO/docs/Archive/architecture/layers/kernel_binding_test_layer.md)
6. [接口修改热点](/home/void0312/Workshop/CMO/docs/Archive/architecture/interface_hotspots.md)

## 4. 当前最重要的结构事实

### 4.1 已经具备的对象

当前内核已经原生注册并暴露了这些对象：

- `MissionCommand`
- `TaskOrder`
- `LeaderIntent`
- `PilotReport`
- `PendingMissionCommand`

主要定义在：

- [`src/components/physics/action.h`](/home/void0312/Workshop/CMO/src/components/physics/action.h)
- [`src/components/systems/comm.h`](/home/void0312/Workshop/CMO/src/components/systems/comm.h)

### 4.2 当前最关键的结构矛盾

虽然对象已经具备，但字段语义还没有完全按新的标准收紧：

- `MissionCommand` 仍以 `cmd_heading_deg / cmd_altitude_m / cmd_speed_mps` 为核心通用字段。
- `LeaderIntent` 也仍沿用同一组三元组。
- Python 侧 `leader_env.py` 仍带有把这些字段当成通用可调参数的历史实现痕迹。
- `default_control_model.cpp` 当前仍把 `MissionCommand` 解释为简化自动驾驶输入，而不是按 `command_code` 分槽位解释。

因此，后续改口径时不能只改文档或只改 Python，必须跨层同步。

## 5. 本目录产出用途

本目录的文档不是“宣传材料”，而是接口重构前的定位手册。目标是：

- 明确每一层的责任边界
- 明确每个对象在哪些文件被定义、读写和重解释
- 为后续接口收口提供改动清单
