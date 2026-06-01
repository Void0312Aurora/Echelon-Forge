# `src/components/combat` 边界

`components/combat` 保存战斗相关 ECS 状态，例如伤害、生命值、武器挂载和评分状态。

component surface 包含通用 weapon/damage state 与 naval weapon-system 数据，但这里只是数据层。这
不等于 ground fires/damage component model 或完整 naval engagement owner 已落地。

## 允许

- health、damage、weapon、scoring 等战斗状态 component。
- 仍保持纯 ECS 数据的 naval weapon-system state。
- 武器系统和伤害系统需要读写的纯数据。

## 禁止

- 制导、伤害结算或发射流程实现。
- 物理运动状态、传感器扫描状态或任务状态。
- Python binding 和 runtime owner。
- ground fires/damage schema ownership。

## 迁移备注

战斗行为放在 `systems/combat` 或 `models/weapons`；这里保留可序列化、可绑定的状态数据。
