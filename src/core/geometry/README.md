# `src/core/geometry` 边界

`core/geometry` 保存空间查询和几何辅助 runtime。它服务 simulation、sensor、visual 或 mission 查询，但不拥有 world lifecycle。

## 允许

- spatial query runtime。
- 几何查询、距离/视线/邻近关系等辅助计算。
- 可被 `core/engine` 或 `systems/` 调用的纯 C++ 查询服务。

## 禁止

- ECS system registration。
- mission episode 状态机。
- Python binding 或 facade。
- GPU kernel 实现。

## 迁移备注

若查询开始依赖具体 world owner 生命周期，应把 ownership 保持在 `core/engine`，本目录只保留查询服务实现。
