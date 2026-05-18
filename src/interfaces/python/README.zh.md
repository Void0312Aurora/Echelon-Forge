<!-- Machine-translated draft generated on 2026-05-18 from src/interfaces/python/README.md. Review before treating this file as authoritative. -->

# `src/interfaces/python` 边界

`interfaces/python` 是 nanobind 暴露层。它把 `runtime/facade`、必要的 `core` 兼容 API 和数据类型暴露给 Python；不应在这里实现领域行为。

## 允许

- `NB_MODULE` 聚合和 binding 函数。
- C++ enum、struct、class 的 Python 暴露。
- Python 参数到 C++ request/result 的轻量转换。
- DLPack 等绑定层视图适配。

## 禁止

- 任务 JSON 解释、episode transition、reward breakdown。
- 物理、传感器、武器、控制律实现。
- 新增绕过 `RuntimeFacade` 的长期主线 API。
- 训练配置治理或 scenario 目录治理。

## 当前结构

`python_module.cpp` 只保留 `NB_MODULE`、`set_log_level` 和分区 binding 注册调用。各绑定单元按职责维护：

- `bindings_core.cpp`
  低层兼容类型、`SimulationKernel` 和历史诊断入口。
- `bindings_command.cpp`
  command/tasking enum、`PilotAction`、`MissionCommand`、`TaskOrder`、`LeaderIntent`、`PilotReport`、`CommPacket`。
- `bindings_episode.cpp`
  mission/runtime/reward/termination/episode controller 相关数据结构和纯运行时函数。
- `bindings_runtime.cpp`
  `WorldBatchRuntime`、`RuntimeFacade` 和 facade request/result 类型。
- `bindings_gpu.cpp`
  GPU helper、batch observation/visual helper、DLPack / `GpuTensorView` 适配。
- `binding_utils.h`
  nanobind 公共 include、分区注册声明和 numpy owner helper。

新增绑定时优先放入对应分区；只有跨分区通用的 nanobind 小工具才放入 `binding_utils.h`。

## 迁移备注

保留低层 `SimulationKernel`、`WorldBatchRuntime` 绑定可以服务兼容期；新增主线能力应优先绑定 `RuntimeFacade`。
