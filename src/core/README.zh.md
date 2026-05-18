# `src/core` 边界

`core/` 是 C++ 运行时内核层，负责单世界仿真、批量运行时、任务/回合运行时、几何查询和模型接口。它可以编排下层 `systems/`、`models/`、`components/` 和 `content/`，但不承载 Python 绑定或应用层外观契约。

## 允许

- `SimulationKernel` 和 `WorldBatchRuntime` 这类运行时所有者。
- mission、objective、reward、termination、episode controller 相关逻辑。
- 几何查询与核心模型接口。
- 面向 facade 的稳定 C++ API 实现底座。

## 禁止

- nanobind/Python 暴露代码。
- 前端专用 API 命名和语言绑定兼容逻辑。
- 用 GPU 实验主线替代 CPU 真实路径。
- 把 component 或 model 的实现直接定义在 `core` 中。

## 子目录约定

- `engine/`：单世界内核与批量运行时所有者。
- `mission/`：mission/episode/objective/reward/termination 运行时。
- `geometry/`：空间查询与几何辅助运行时。
- `interfaces/`：模型接口和跨 `core` 的抽象契约。

## 当前阅读入口

- [engine/README.md](engine/README.md)
- [mission/README.md](mission/README.md)
- [geometry/README.md](geometry/README.md)
- [interfaces/README.md](interfaces/README.md)

## 当前文件落点

- `engine/`
  - `simulation_kernel.h/.cpp`
  - `simulation_kernel_systems.cpp`
  - `simulation_kernel_command_api.cpp`
  - `simulation_kernel_observation_api.cpp`
  - `simulation_kernel_visual_api.cpp`
  - `simulation_kernel_weapon_api.cpp`
  - `world_batch_runtime.h/.cpp`
  - `exact_stage_inventory.cpp`
- `mission/`
  - `runtime/*`：mission、objective、reward、termination、execution 运行时
  - `episode/*`：episode 状态、批量准备、controller
  - `episode/detail/*`：transition、codec、reward breakdown 私有辅助逻辑
- `geometry/`
  - `spatial_query_runtime.h/.cpp`
- `interfaces/`
  - `control_model.h`, `effects_model.h`, `environment_model.h`
  - `guidance_model.h`, `sensor_model.h`, `observation.h`, `unit_data.h`, `unit_factory.h`

## 迁移备注

`mission/` 已按 `runtime/`、`episode/`、`episode/detail/` 拆出物理层级。后续新增 mission 代码应优先归入这些子层级，并保持 `runtime/` 不反向依赖 `episode/`。

`engine/` 后续拆分仍应优先按职责拆分实现文件，并保持 public API 稳定。
