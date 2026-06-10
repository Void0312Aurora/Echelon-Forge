# `src/systems/combat` 边界

`systems/combat` 保存战斗系统 tick 逻辑，包括伤害处理和制导系统调度。

当前维护实现覆盖通用 combat-state 推进、missile guidance 调度、pilot weapon
release，以及接入共享 weapon release service 的桥接。naval mission-command weapon
release 在 `systems/domains/naval` 注册；engagement evidence 通过 runtime contracts 和 facade
packet 导出。本目录不表示 ground fires 或 ground damage runtime 已维护。

## 允许

- damage system。
- guidance system。
- pilot weapon-release system。
- 对 `components/combat`、`models/weapons` 和 weapon-release interface 的组合调用。

## 禁止

- combat component 定义。
- mission reward/termination 规则。
- Python binding 或 facade。
- ground fires、ground damage 或 land-domain combat runtime ownership。

## 迁移备注

奖励和任务结果属于 `core/mission`；本目录只处理 world 内战斗状态推进。
