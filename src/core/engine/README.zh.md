<!-- Machine-translated draft generated on 2026-05-18 from src/core/engine/README.md. Review before treating this file as authoritative. -->

# `src/core/engine` 边界

`core/engine` 负责单 world simulation kernel 和 batch world owner。它是 CPU exact world-step 语义的主线位置，也是下层 ECS systems 的调度者。

## 允许

- `SimulationKernel` lifecycle、reset、step、spawn 和 query API。
- `WorldBatchRuntime` 多 world ownership、批量 reset/step、批量 command/observation 操作。
- ECS component 和 system registration 的编排。
- 与 `content/` 和 `models/` 的组合逻辑。

## 禁止

- Python binding。
- mission-command JSON codec、episode transition、reward breakdown。
- GPU kernel 实现。
- facade request/result 类型定义。

## 当前结构

`SimulationKernel` public API 保持在 `simulation_kernel.h`。实现按职责拆分：

- `simulation_kernel_systems.cpp`
  ECS component registration 和系统注册顺序。
- `simulation_kernel_command_api.cpp`
  legacy movement/action command、command link、digital pilot/tasking setters/getters、message command。
- `simulation_kernel_observation_api.cpp`
  unit/agent observation、detections、health/fuel/messages 和 observation diagnostics。
- `simulation_kernel_visual_api.cpp`
  ARB visual scene collection 和 visual tensor rendering API。
- `simulation_kernel_weapon_api.cpp`
  missile launch API 和 launch-time missile/sensor tuning。
- `exact_stage_inventory.cpp`
  exact-stage inventory、contract inventory 和 manual trace frame helpers。
- `simulation_kernel.cpp`
  constructor/destructor、model injection、reset/step、unit spawn、database/environment configuration。

`SimulationKernel` public API 可以保持不变；拆分重点是降低实现文件的职责密度。

## 依赖方向

本层可以依赖 `systems/`、`models/`、`components/`、`content/` 和 `core/interfaces`。它不依赖 `runtime/facade` 或 `interfaces/python`。
