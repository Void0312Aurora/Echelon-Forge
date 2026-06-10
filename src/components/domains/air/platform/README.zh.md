# `src/components/domains/air/platform` 边界

`components/domains/air/platform` 保存 air-domain ECS value type 与 tuning state。它是 fixed-wing
flight-dynamics tuning 的 component 侧 owner；这些类型不应再被视作共享 physics state。

## 允许

- air-domain data component、tuning struct 与轻量 value helper。
- 被 `systems/domains/air` 和 air model 消费的 flight dynamics tuning。

## 禁止

- system registration、逐 tick 更新逻辑、积分器或 control-model 执行。
- naval 或 ground component ownership。
- Python binding、facade、scenario loading 或 runtime orchestration。

## 当前文件

- [flight_dynamics_tuning.h](flight_dynamics_tuning.h)
  - `AeroTuning`、`EngineTuning`、`StallState` 与 air flight-dynamics helper。

## 已移除旧入口

旧的 `components/physics/flight_dynamics_tuning.h` include 路径已移除。需要
air flight-dynamics tuning 的代码必须直接 include
`components/domains/air/platform/flight_dynamics_tuning.h`。
