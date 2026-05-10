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
