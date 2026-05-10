# `src/systems` 边界

`systems/` 保存 ECS system registration 和每 tick mutation 逻辑。这里的代码消费 `components/` 与 `models/`，并由 `core/engine` 注册和调度。

## 允许

- Flecs system/query 注册函数。
- 每 tick 对 ECS component 的更新逻辑。
- 调用 `models/` 中的可替换模型实现。
- 使用 `core/interfaces` 中的模型接口。

## 禁止

- 定义新的 ECS component 或 command/tasking DTO。
- 拥有 world lifecycle、batch runtime、episode controller 或 facade。
- Python binding 或外部 API 适配。
- 读取训练配置、场景文件或直接管理多 world。

## 子目录约定

- `core/`：通用 operation / lifecycle system。
- `physics/`：空气动力、控制、力、积分、地面接触、仪表等物理系统。
- `combat/`：伤害、制导和战斗效果系统。
- `systems/`：平台系统 runtime，例如 command link、data link、EW、logistics、navigation、sensor、track manager。
- `visual/`：视觉观测 system。

## 迁移备注

`systems/systems` 命名过宽。新增平台系统可以暂放此目录，但应在下一轮重命名评估中收敛为更明确的业务名，例如 `systems/platform` 或 `systems/avionics`。
