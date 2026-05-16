# `src/` 分层边界

状态：`2026-05-10` 分层重构护栏。  
本文档定义 `src/` 的目录职责和依赖方向。它不描述一次性搬迁目标，而是给后续拆分、重命名和新增代码提供边界。

## 依赖方向

主线依赖方向应保持为：

```text
interfaces/python
  -> runtime/facade
    -> core/engine and core/mission
      -> systems
        -> models / components / content

gpu
  -> core/runtime data packets or systems-visible packets
  -> no ownership of canonical world-step truth
```

允许下层定义数据、模型和系统逻辑；上层负责组合、批量运行、facade 和语言绑定。反向依赖需要先写入冻结计划。

## 目录职责

- `components/`：ECS component 和稳定 DTO-like 数据结构。
- `systems/`：Flecs system registration 与每 tick mutation 逻辑。
- `models/`：可替换领域模型实现。
- `content/`：内容 schema、unit definition 和加载器。
- `core/`：C++ runtime 编排、单 world kernel、batch runtime、mission/episode runtime。
- `runtime/`：维护中的应用层 C++ runtime contract，尤其是 facade。
- `interfaces/`：语言绑定和外部接口适配。
- `gpu/`：GPU helper、packet runtime 和显式实验探针。
- `tools/`：开发期工具和实验工具，不进入主线 runtime contract。

## 推荐阅读

- [components/README.md](/home/void0312/Workshop/CMO/src/components/README.md)
- [components/command/README.md](/home/void0312/Workshop/CMO/src/components/command/README.md)
- [components/command/common/README.md](/home/void0312/Workshop/CMO/src/components/command/common/README.md)
- [components/command/air/README.md](/home/void0312/Workshop/CMO/src/components/command/air/README.md)
- [components/tasking/README.md](/home/void0312/Workshop/CMO/src/components/tasking/README.md)
- [components/tasking/common/README.md](/home/void0312/Workshop/CMO/src/components/tasking/common/README.md)
- [components/tasking/air/README.md](/home/void0312/Workshop/CMO/src/components/tasking/air/README.md)
- [components/tasking/naval/README.md](/home/void0312/Workshop/CMO/src/components/tasking/naval/README.md)
- [core/README.md](/home/void0312/Workshop/CMO/src/core/README.md)
- [core/engine/README.md](/home/void0312/Workshop/CMO/src/core/engine/README.md)
- [core/mission/README.md](/home/void0312/Workshop/CMO/src/core/mission/README.md)
- [core/mission/runtime/README.md](/home/void0312/Workshop/CMO/src/core/mission/runtime/README.md)
- [core/mission/episode/README.md](/home/void0312/Workshop/CMO/src/core/mission/episode/README.md)
- [core/mission/episode/detail/README.md](/home/void0312/Workshop/CMO/src/core/mission/episode/detail/README.md)
- [runtime/README.md](/home/void0312/Workshop/CMO/src/runtime/README.md)
- [runtime/contracts/README.md](/home/void0312/Workshop/CMO/src/runtime/contracts/README.md)
- [runtime/facade/README.md](/home/void0312/Workshop/CMO/src/runtime/facade/README.md)
- [interfaces/README.md](/home/void0312/Workshop/CMO/src/interfaces/README.md)
- [interfaces/python/README.md](/home/void0312/Workshop/CMO/src/interfaces/python/README.md)
- [gpu/README.md](/home/void0312/Workshop/CMO/src/gpu/README.md)

## CMake 分组

当前仍保留 `ef_core` 单 target，但 `CMakeLists.txt` 中的源码已经按未来 target 边界分组：

- `EF_CORE_ENGINE_SOURCES`
- `EF_CORE_GEOMETRY_SOURCES`
- `EF_CORE_MISSION_RUNTIME_SOURCES`
- `EF_CORE_MISSION_EPISODE_SOURCES`
- `EF_CORE_MISSION_EPISODE_DETAIL_SOURCES`
- `EF_CORE_MISSION_SOURCES`
- `EF_RUNTIME_FACADE_SOURCES`
- `EF_MODEL_DEFAULT_SOURCES`
- `EF_CONTENT_SOURCES`
- `EF_PYTHON_BINDING_SOURCES`
- `EF_GPU_MAINTAINED_HELPER_SOURCES`
- `EF_GPU_EXPERIMENT_SOURCES`

新增源码应先归入明确 source group；不要直接把 `src/...` 文件追加到 `add_library(ef_core)` 或 `nanobind_add_module(ef_py)`。

## 禁止事项

- 不要因为 include 方便，把 command、tasking、mission、runtime 或 binding 逻辑塞进已有宽目录。
- 不要在 `interfaces/` 中实现领域逻辑；先落到 `core/` 或 `runtime/facade`。
- 不要让 `gpu/` 成为 CPU truth path 的替代实现，除非另起 exact backend 冻结文档。
- 不要新增没有 README 的主目录或新的跨层聚合目录。

## 迁移原则

- 先补 README 和兼容 umbrella header，再移动 include。
- 先保持 public API 和 Python 暴露名稳定，再拆实现文件。
- 先缩小大文件职责，再考虑 CMake target 拆分。
- 旧路径进入兼容期时，应在 README 或头文件注释中写明目标路径。
