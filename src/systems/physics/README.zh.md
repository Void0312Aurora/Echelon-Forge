# `src/systems/physics` 边界

`systems/physics` 保存共享物理推进逻辑，以及旧 air/flight system 路径的兼容头。
canonical air-domain runtime owner 现在是 `systems/air`。

这里的 ground contact 支持 aircraft/terrain interaction 和通用物理约束，不是 land-domain movement model 或 full ground runtime。

## 允许

- force、instrument、movement、leapfrog、ground contact 等共享 system。
- 对 `components/physics` 和 terrain/ground-contact state 的逐帧更新。
- 迁移期保留 air system 的 include-only compatibility wrapper。

## 禁止

- 定义物理 component。
- mission/tasking 状态机。
- Python binding、facade 或 batch runtime。
- land movement、sensing、fires 或 damage runtime ownership。

## 迁移备注

如果逻辑解释 tasking/command 并转为物理动作，应谨慎划分：DTO 在 `components/command`/`components/tasking`，任务解释在 `core/mission`，物理执行在本目录。

air-only system（aerodynamic state、aerodynamic effect、flight control、
propulsion）应由 `systems/air` 持有；旧 `systems/physics/*` 对应头文件仅作为
compatibility wrapper。
