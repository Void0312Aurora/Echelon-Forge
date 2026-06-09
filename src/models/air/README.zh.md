# `src/models/air` 边界

`models/air` 保存航空、飞行控制以及 air-owned effects consequence helper 相关默认模型实现。

## 允许

- control model 默认实现。
- 与飞行控制、气动响应有关的纯计算逻辑。
- 通过 common effects routing 消费的 air-owned default effects consequence helper。

## 禁止

- ECS system registration。
- `SimulationKernel` lifecycle。
- Python binding 或训练配置解析。

## 迁移备注

若模型需要成为可替换 contract，先补 `core/interfaces`，再在本目录提供默认实现。

`default_effects_air_domain.h` 是共享 default effects model 的 owner helper，不是独立 effects model 入口。
