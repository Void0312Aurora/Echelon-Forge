# `src/core/engine` 边界

`core/engine` 负责单世界仿真内核和批量世界所有者。它是 CPU 精确世界步进语义的主线位置，也是下层 ECS 系统的调度者。

## 允许

- `SimulationKernel` 的生命周期、reset、step、spawn 和 query API。
- `WorldBatchRuntime` 的多世界持有、批量 reset/step、批量 command/observation 操作。
- ECS component 和 system registration 的编排。
- 与 `content/` 和 `models/` 的组合逻辑。

## 禁止

- Python 绑定。
- mission-command JSON 编解码、episode 转移、reward breakdown。
- GPU kernel 实现。
- facade request/result 类型定义。

## 当前结构

`SimulationKernel` 的 public API 保持在 `simulation_kernel.h`。实现按职责拆分：

- `simulation_kernel_systems.cpp`
  ECS component registration 和系统注册顺序。
- `simulation_kernel_command_api.cpp`
  legacy movement/action command、command link、digital pilot/tasking setters/getters、message command。
- `simulation_kernel_command_surface.*`
  非 owning 的窄命令/读取 surface，供 batch/facade-facing 代码使用，避免新的调用点直接依赖完整 `SimulationKernel` public API。
- `simulation_kernel_observation_api.cpp`
  unit/agent observation、detections、health/fuel/messages 和 observation diagnostics。
- `simulation_kernel_visual_api.cpp`
  ARB visual scene collection 和 visual tensor rendering API。
- `simulation_kernel_weapon_api.cpp`
  missile launch API 和发射时 missile/sensor 调优。
- `exact_stage_inventory.cpp`
  exact-stage inventory、contract inventory 和 manual trace frame 辅助逻辑。
- `simulation_kernel.cpp`
  constructor/destructor、model injection、reset/step、unit spawn、database/environment configuration。

`SimulationKernel` 为了兼容 Python 绑定和现有测试仍保留较宽 public API。新的 C++ 调用点如果只需要 command/tasking 写入或读取，应优先使用窄命令 surface。

## 依赖方向

本层可以依赖 `systems/`、`models/`、`components/`、`content/` 和 `core/interfaces`。它不依赖 `runtime/facade` 或 `interfaces/python`。
