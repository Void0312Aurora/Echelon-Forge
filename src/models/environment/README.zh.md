# `src/models/environment` 边界

`models/environment` 保存环境模型默认实现和环境 snapshot。

## 允许

- wind、terrain、environment snapshot 等模型实现。
- 环境查询所需的纯计算辅助。

## 禁止

- ECS system registration。
- runtime owner 或 batch runtime。
- Python binding。

## 迁移备注

环境状态 component 属于 `components/basic` 或更明确目录；环境计算模型属于本目录。
