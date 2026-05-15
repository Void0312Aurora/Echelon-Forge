# `src/core` 边界

`core/` 是 C++ runtime 内核层，负责单 world simulation、batch runtime、mission/episode runtime、几何查询和模型接口。它可以编排下层 `systems/`、`models/`、`components/` 和 `content/`，但不承载 Python 绑定或应用层 facade contract。

## 允许

- `SimulationKernel` 和 `WorldBatchRuntime` 这类 runtime owner。
- mission、objective、reward、termination、episode controller。
- 几何查询与核心模型接口。
- 面向 facade 的稳定 C++ API 实现底座。

## 禁止

- nanobind/Python 暴露代码。
- 前端专用 API 命名和语言绑定兼容逻辑。
- GPU 实验主线替换 CPU truth path。
- 把 component 或 model 实现直接定义在 core。

## 子目录约定

- `engine/`：单 world kernel 与 batch runtime owner。
- `mission/`：mission/episode/objective/reward/termination runtime。
- `geometry/`：空间查询和几何辅助 runtime。
- `interfaces/`：模型接口和跨 core 的抽象 contract。

## 迁移备注

`mission/` 已按 `runtime/`、`episode/`、`episode/detail/` 拆出物理层级。后续新增 mission 代码应先归入这些子层级，并保持 `runtime/` 不反向依赖 `episode/`。

`engine/` 后续拆分仍应优先按职责拆实现文件，并保持 public API 稳定。
