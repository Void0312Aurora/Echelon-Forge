# 操作层与物理层

> ARCHIVED NOTE (2026-03-23): 该文档属于旧的架构拆分说明，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/CMO/docs/standards/README.md)。

## 1. 职责

这一层负责：

- 将高层命令映射成可执行的控制输入
- 处理命令链路延迟与命令滞后
- 运行飞行动力学、气动、地面接触、制导、传感器、仪表系统

这一层不负责：

- 解释军事任务线程
- 决定 CAP / RTB / Landing 的战术语义

## 2. 当前代码落点

### 2.1 核心组件定义

- [`src/components/physics/action.h`](/home/void0312/CMO/src/components/physics/action.h)

关键结构体：

- `PilotAction`
- `MissionCommand`
- `TaskOrder`
- `LeaderIntent`
- `CommandLag`
- `CommandLink`
- `PendingMissionCommand`

### 2.2 系统调度

- [`src/core/engine/simulation_kernel.cpp`](/home/void0312/CMO/src/core/engine/simulation_kernel.cpp)

`SimulationKernel` 负责：

- 注册 ECS 组件
- 注册各系统
- 提供 Python 可调用的 set/get 接口

### 2.3 命令链路系统

- [`src/systems/systems/command_link_system.h`](/home/void0312/CMO/src/systems/systems/command_link_system.h)

负责：

- `MovementCommand`
- `ActionCommand`
- `MissionCommand`

的延迟投递。

### 2.4 操作映射系统

- [`src/systems/core/operation_system.h`](/home/void0312/CMO/src/systems/core/operation_system.h)

负责：

- `ActionCommand -> MovementCommand`
- `MovementCommand -> LaggedCommand`

### 2.5 仪表系统

- [`src/systems/physics/instrument_system.h`](/home/void0312/CMO/src/systems/physics/instrument_system.h)

负责把物理真值整理成：

- `InstrumentState`
- command bugs
- EGI / 环境 / EW 等飞行员可读量

### 2.6 控制模型

- [`src/models/air/default_control_model.cpp`](/home/void0312/CMO/src/models/air/default_control_model.cpp)

负责：

- 使用 `PilotAction` 或 `MissionCommand` 生成实际控制量
- 在没有 `PilotAction` 时，用 `MissionCommand` 驱动命令语义受限的 legacy 自动驾驶

当前已固化的解释规则：

- `command_code = 3` 时，把 `cmd_heading_deg` 视为航迹参考，优先按 ground track 做 lateral tracking。
- `command_code = 4` 时，把 `recovery_base_id / recovery_runway_id / recovery_approach_type` 视为回收程序元数据，terminal 自动驾驶只保留温和的程序参考，不再按通用大增益 heading hold 解释。
- `landing` 命令下自动保持起落架放下。

## 3. 当前最该关注的接口

如果要改操作层或物理层接口，优先看：

1. [`src/components/physics/action.h`](/home/void0312/CMO/src/components/physics/action.h)
2. [`src/core/engine/simulation_kernel.h`](/home/void0312/CMO/src/core/engine/simulation_kernel.h)
3. [`src/interfaces/python/python_module.cpp`](/home/void0312/CMO/src/interfaces/python/python_module.cpp)
4. [`src/models/air/default_control_model.cpp`](/home/void0312/CMO/src/models/air/default_control_model.cpp)
5. [`src/systems/systems/command_link_system.h`](/home/void0312/CMO/src/systems/systems/command_link_system.h)

## 4. 当前结构风险

- `default_control_model.cpp` 仍然是兼容性自动驾驶，不是完整 recovery-program 执行器；terminal 几何仍主要依赖执行层脚本 / 模型。
- 仪表层 `cmd bugs` 已按 `command_code` 分流：`route` 显示 LNAV/track 参考，`landing` 优先显示 runway/recovery 参考；但仪表结构体本身仍只有 legacy `heading / alt / speed` 三元 bug，尚未直接暴露 `route_ref_id / recovery_*`。
- `TaskOrder` 和 `LeaderIntent` 已进入内核并补入 route/recovery 字段，但更细的任务字段仍会继续扩展。

## 5. 后续修改建议

若要在底层固化新接口，建议顺序是：

1. 先改 `action.h` 中的数据结构
2. 再改 Python 绑定
3. 再改 `default_control_model.cpp` 对 `MissionCommand` 的解释
4. 最后再回归链路系统、仪表系统和执行层环境
