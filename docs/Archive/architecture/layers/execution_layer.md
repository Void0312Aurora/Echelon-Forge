# 执行层

> ARCHIVED NOTE (2026-03-23): 该文档属于旧的 air-specific 架构拆分说明，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/Workshop/CMO/docs/standards/README.md)。

## 1. 职责

执行层负责：

- 接收 `MissionCommand`
- 结合仪表/导航观测完成轨迹跟踪
- 输出 `PilotAction`
- 生成到达/无法到达/返航等报告信号

执行层不负责：

- 改写 `TaskOrder`
- 自行切换 C2 任务线程
- 取代长机层的任务展开决策

## 2. 当前代码落点

### 2.1 通用执行环境

- [`gym_envs/universal_env.py`](/home/void0312/Workshop/CMO/gym_envs/universal_env.py)

负责：

- 单机执行层训练/评估环境
- 与 `ScenarioLoader`、`SimulationKernel` 交互
- 提供执行层 observation / reward / termination

### 2.2 场景装载与任务观测

- [`gym_envs/scenario_loader/core.py`](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)

负责：

- 生成 `mission_observation`
- 维护 waypoint 状态
- 维护 ILS / runway 几何
- 将 runtime `mission_cmd` 同步进内核

### 2.3 动作包装层

- [`python/rl/control/wrappers.py`](/home/void0312/Workshop/CMO/python/rl/control/wrappers.py)

负责：

- 脚本基线与残差控制混合
- 多时间尺度动作包装
- 按 phase 切换脚本控制模式

### 2.4 脚本控制器

- [`python/rl/control/scripted_takeoff.py`](/home/void0312/Workshop/CMO/python/rl/control/scripted_takeoff.py)
- [`python/rl/control/scripted_stable_flight.py`](/home/void0312/Workshop/CMO/python/rl/control/scripted_stable_flight.py)
- [`python/rl/control/scripted_landing.py`](/home/void0312/Workshop/CMO/python/rl/control/scripted_landing.py)

## 3. 输入与输出

### 输入

- `MissionCommand`
- `InstrumentState`
- EGI/nav/ILS
- phase / waypoint progress

### 输出

- `PilotAction`
- 执行层 reward / termination
- 供长机层桥接的状态与报告

## 4. 当前最该关注的接口

如果要改执行层接口，优先看：

1. [`gym_envs/universal_env.py`](/home/void0312/Workshop/CMO/gym_envs/universal_env.py)
2. [`gym_envs/scenario_loader/core.py`](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)
3. [`python/rl/control/wrappers.py`](/home/void0312/Workshop/CMO/python/rl/control/wrappers.py)
4. [`src/models/air/default_control_model.cpp`](/home/void0312/Workshop/CMO/src/models/air/default_control_model.cpp)

## 5. 当前结构风险

- `ScenarioLoader` 同时承载场景解释、mission state、ILS 几何、waypoint 引导、phase 切换，职责较重。
- `ScenarioLoader` 虽已开始把 `recovery_base_id / recovery_runway_id / recovery_approach_type` 归一化进 runtime `mission_cmd`，但 legacy 场景字段重叠仍未完全清理。
- 执行层脚本与 `MissionCommand` 的解释已经开始按 `command_code` 分流，但 kernel 侧 recovery 程序仍不如 Python 脚本层完整。
- `wrappers.py` 已改成 `phase -> command_code -> 低层观测兜底` 的切换优先级，并保留低空 `takeoff` 安全门；后续若再扩展 `command_code`，需要同步更新该映射而不是再回到散落启发式。

## 6. 后续修改建议

若要改执行层接口，建议顺序是：

1. 先稳定 `MissionCommand` 解释规则
2. 再改 `ScenarioLoader` 中 waypoint / landing 切换逻辑
3. 再改脚本控制器输入契约
4. 最后再回归执行层模型与训练配置
