# `src/systems/combat` 边界

`systems/combat` 保存战斗系统 tick 逻辑，包括伤害处理和制导系统调度。

## 允许

- damage system。
- guidance system。
- 对 `components/combat` 和 `models/weapons` 的组合调用。

## 禁止

- combat component 定义。
- mission reward/termination 规则。
- Python binding 或 facade。

## 迁移备注

奖励和任务结果属于 `core/mission`；本目录只处理 world 内战斗状态推进。
