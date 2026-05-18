# `src/tools/experimental` 边界

`tools/experimental` 保存实验性 C++ probes 和一次性工具。这里的代码不属于维护中的 runtime/tooling surface。

## 允许

- phase probe。
- parity 或性能探索工具。
- 临时诊断入口。

## 禁止

- 默认训练或 runtime 路径。
- 被核心库代码依赖。
- 无冻结计划地迁移为维护 API。

## 迁移备注

实验工具若需要长期保留，应先确定目标层级：GPU helper 进入 `gpu/`，runtime API 进入 `runtime/facade`，Python 暴露进入 `interfaces/python`。
