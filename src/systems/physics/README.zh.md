# `src/systems/physics` 边界

`systems/physics` 保存物理、成熟 air/flight state 路径和共享 ground-contact primitive 的推进逻辑。

这里的 ground contact 支持 aircraft/terrain interaction 和通用物理约束，不是 land-domain movement model 或 full ground runtime。

## 允许

- aerodynamic、control、force、instrument、movement、leapfrog、ground contact 等 system。
- 对 `components/physics`、航空模型和 terrain/ground-contact state 的逐帧更新。

## 禁止

- 定义物理 component。
- mission/tasking 状态机。
- Python binding、facade 或 batch runtime。
- land movement、sensing、fires 或 damage runtime ownership。

## 迁移备注

如果逻辑解释 tasking/command 并转为物理动作，应谨慎划分：DTO 在 `components/command`/`components/tasking`，任务解释在 `core/mission`，物理执行在本目录。
