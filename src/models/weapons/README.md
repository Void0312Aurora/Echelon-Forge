# `src/models/weapons` 边界

`models/weapons` 保存武器效果、制导和命中相关默认模型实现。

## 允许

- effects model。
- guidance model。
- 纯计算的武器行为模型。

## 禁止

- ECS system registration。
- combat component 定义。
- Python binding 或 mission episode 编排。

## 迁移备注

系统调度放在 `systems/combat`，状态放在 `components/combat`，模型实现放在本目录。
