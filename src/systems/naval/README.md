# `src/systems/naval` 边界

`systems/naval` 保存舰艇、潜艇和舰载航空 token-level runtime 的每 tick
推进逻辑。这里消费 `components/naval`、`components/command` 与基础运动组件，
但不拥有 mission/tasking 编排或 facade。

## 允许

- 舰艇/潜艇运动与朝向、速度、深度更新。
- 海况、耐波、站位保持等 naval platform per-frame mutation。
- 舰载航空发收舰与 OTH relay 的 token-level runtime 调度。

## 禁止

- 定义 naval platform component 或 command/tasking DTO。
- mission reward、termination、scenario 编译或 episode transition。
- Python binding、facade、训练脚本或多 world owner。
- 把舰载航空 MVP runtime 扩展成未冻结的大型 mission 编排层。

## 当前文件

- [ship_motion_system.h](ship_motion_system.h)
  - 舰艇速度、航向、海况阻力和站位保持更新。
- [submarine_motion_system.h](submarine_motion_system.h)
  - 潜艇速度、航向和深度包线更新。
- [embarked_air_ops_system.h](embarked_air_ops_system.h)
  - 舰载直升机发收舰与 OTH relay token-level runtime。

## 依赖方向

本目录可以消费 `components/naval`、`components/command`、`components/basic`
和必要的 `core/interfaces`。它不应依赖 `runtime/facade`、`interfaces/python`
或训练/场景 glue。
