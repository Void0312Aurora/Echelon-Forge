# `src/` 分层边界

状态：`2026-06-01` 多域分层护栏。
本文档定义 `src/` 下各目录的职责与依赖方向。它不描述一次性迁移目标，而是为后续拆分、重命名和新增代码提供边界。

## 当前领域状态

`src/` 当前维护面已经是多域口径。air/execution 仍是最成熟路径；
common DTO/contract 用于承载 air、naval 和早期 ground-aware setup flow 的共享数据。

- Air：command、tasking、mission/episode、physics、observation 和 RL-facing execution 路径最成熟。
- Naval：已有维护中的平台组件、command/tasking owner slice、舰艇/潜艇/舰载航空 token runtime，以及 tasking/engagement evidence surface；这不等价于完整 naval mission runtime 已存在。
- Ground：仍是早期 bootstrap。`UnitType::Ground` 与 typed-platform capability evidence 已存在，shared terrain assignment 与 aircraft/terrain ground-contact primitive 也可用。但这些不是陆域 terrain 或 movement runtime；ground movement、sensing、terrain ownership、fires、damage 和 full ground runtime 仍 held。

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

下层可以定义数据、模型和系统逻辑；上层负责组合、批量运行、facade 和语言绑定。任何反向依赖都需要先写入冻结计划。

## 目录职责

- `components/`：ECS 组件和稳定的类似 DTO 的数据结构，包括 common command/tasking foundation、air/naval slices，以及 ground-bootstrap-aware setup 边界。
- `systems/`：Flecs system 注册与每轮更新的状态变更逻辑，包括 air/physics system、naval token runtime 和 ground-contact primitive。
- `models/`：可替换的领域模型实现和 unit-factory capability evidence。
- `content/`：面向 air、naval 与早期 ground-aware setup 数据的内容 schema、单位定义和加载器。
- `core/`：C++ 运行时编排、单 world kernel、batch runtime，以及 mission/episode runtime。
- `runtime/`：维护中的应用层 C++ 运行时契约，尤其是 facade 与共享 DTO contracts。
- `interfaces/`：语言绑定和外部接口适配。
- `gpu/`：GPU 辅助工具、packet runtime 和显式实验探针。
- `tools/`：开发期工具和实验工具，不进入主线运行时契约。

## 推荐阅读

- [components/README.md](components/README.md)
- [components/command/README.md](components/command/README.md)
- [components/command/common/README.md](components/command/common/README.md)
- [components/command/air/README.md](components/command/air/README.md)
- [components/command/naval/README.md](components/command/naval/README.md)
- [components/naval/README.md](components/naval/README.md)
- [components/tasking/README.md](components/tasking/README.md)
- [components/tasking/common/README.md](components/tasking/common/README.md)
- [components/tasking/air/README.md](components/tasking/air/README.md)
- [components/tasking/naval/README.md](components/tasking/naval/README.md)
- [content/README.md](content/README.md)
- [core/README.md](core/README.md)
- [core/engine/README.md](core/engine/README.md)
- [core/mission/README.md](core/mission/README.md)
- [core/mission/runtime/README.md](core/mission/runtime/README.md)
- [core/mission/episode/README.md](core/mission/episode/README.md)
- [core/mission/episode/detail/README.md](core/mission/episode/detail/README.md)
- [runtime/README.md](runtime/README.md)
- [runtime/contracts/README.md](runtime/contracts/README.md)
- [runtime/facade/README.md](runtime/facade/README.md)
- [models/README.md](models/README.md)
- [models/core/README.md](models/core/README.md)
- [models/systems/README.md](models/systems/README.md)
- [systems/README.md](systems/README.md)
- [systems/naval/README.md](systems/naval/README.md)
- [interfaces/README.md](interfaces/README.md)
- [interfaces/python/README.md](interfaces/python/README.md)
- [gpu/README.md](gpu/README.md)

## CMake 分组

当前仍保留 `ef_core` 这一个构建目标，但 `CMakeLists.txt` 中的源码已经按未来构建目标边界完成分组：

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

新增源码应先归入明确的源码分组；不要直接把 `src/...` 文件追加到 `add_library(ef_core)` 或 `nanobind_add_module(ef_py)`。

## 禁止事项

- 不要因为 include 路径方便，就把 command、tasking、mission、runtime 或 binding 逻辑塞进已有的宽口径目录。
- 不要在 `interfaces/` 中实现领域逻辑；应先落到 `core/` 或 `runtime/facade`。
- 不要让 `gpu/` 成为 CPU truth path 的替代实现，除非另行编写精确后端的冻结文档。
- 不要新增没有 README 的主目录，也不要新增跨层聚合目录。

## 迁移原则

- 先补 README 和兼容 umbrella header，再移动 include。
- 先保持 public API 和 Python 暴露名稳定，再拆分实现文件。
- 先缩小大文件职责，再考虑拆分 CMake 构建目标。
- 旧路径进入兼容期时，应在 README 或头文件注释中写明目标路径。
