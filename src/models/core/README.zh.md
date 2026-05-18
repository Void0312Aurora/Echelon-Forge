# `src/models/core` 边界

`models/core` 保存基础模型实现，例如 unit factory 默认实现。

## 允许

- 默认 unit factory。
- 对 `content/` unit definition 的转换和实例化辅助。

## 禁止

- world lifecycle ownership。
- ECS system registration。
- Python binding 或 facade。

## 迁移备注

实例化流程的 owner 仍应在 `core/engine`；本目录只提供模型实现和工厂策略。
