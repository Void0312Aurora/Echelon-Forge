# `src/models/environment` 边界

`models/environment` 保存环境模型默认实现和环境 snapshot。

这里的 terrain 与 maritime/environment snapshot 是供 engine 和 system 查询的模型，不构成
land-domain terrain control、movement、sensing、fires 或 damage runtime。

## 允许

- wind、terrain、environment snapshot 等模型实现。
- 环境查询所需的纯计算辅助。

## 禁止

- ECS system registration。
- runtime owner 或 batch runtime。
- Python binding。
- land-domain terrain ownership 或 ground movement/sensing/fires/damage 行为。

## 迁移备注

环境状态 component 属于 `components/basic` 或更明确目录；环境计算模型属于本目录。
