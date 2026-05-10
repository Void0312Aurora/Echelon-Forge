# `src/systems/physics` 边界

`systems/physics` 保存物理和飞行状态推进逻辑。

## 允许

- aerodynamic、control、force、instrument、movement、leapfrog、ground contact 等 system。
- 对 `components/physics` 和航空模型的 per-frame 更新。

## 禁止

- 定义物理 component。
- mission/tasking 状态机。
- Python binding、facade 或 batch runtime。

## 迁移备注

如果逻辑解释 tasking/command 并转为物理动作，应谨慎划分：DTO 在 `components/command`/`components/tasking`，任务解释在 `core/mission`，物理执行在本目录。
