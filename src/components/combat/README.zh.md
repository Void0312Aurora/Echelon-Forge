# `src/components/combat` 边界

`components/combat` 保存战斗相关 ECS 状态，例如伤害、生命值、武器挂载和评分状态。

根 combat surface 现在只承载共享 combat state 与 common weapon/damage primitive。
Air、naval、ground combat owner slice 位于 `components/domains/<domain>/combat/`。

## 允许

- health、damage、weapon、scoring 等战斗状态 component。
- 仍保持纯 ECS 数据的域自有 combat slice，通过 `components/domains/<domain>/combat/` 承载。
- 武器系统和伤害系统需要读写的纯数据。

## 禁止

- 制导、伤害结算或发射流程实现。
- 物理运动状态、传感器扫描状态或任务状态。
- Python binding 和 runtime owner。
- 新的域专属 fires/damage schema ownership 放在 `components/combat` 根目录。

## 迁移备注

战斗行为放在 `systems/combat` 或 `models/weapons`；这里保留可序列化、可绑定的状态数据。
