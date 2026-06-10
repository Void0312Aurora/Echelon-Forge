# `src/models` 边界

`models/` 保存可替换的领域模型实现。它为 `systems/` 和 `core/engine` 提供 control、environment、sensor、effects、guidance、unit factory 等能力。

model 层是 multi-domain aware，但成熟度不均。air control、air effects 与
execution-adjacent model 仍最深入，位于 `domains/air`；`domains/naval` 支持包括
平台、sensor/acoustic、weapon-mount helper 和显式 effects placeholder routing；
`domains/ground` 支持仅限 unit-factory capability evidence 和显式 effects
placeholder routing，不宣称完整 ground runtime 成熟度。

## 允许

- 默认模型实现。
- 可替换模型的纯 C++ 计算逻辑。
- 只依赖 component 数据和 `core/interfaces` contract 的 helper。
- typed setup 使用的 unit-factory capability evidence，包括 naval 与早期 ground-aware metadata。

## 禁止

- ECS system registration。
- runtime owner、batch owner 或 facade。
- Python binding。
- 训练配置或 scenario 编排。
- 对应 interface 与 runtime owner 存在前的 full ground movement、sensing、terrain、fires 或 damage model 实现。

## 子目录约定

- `core/`：unit factory 等基础模型实现。
- `domains/`：域自有 model implementation 与 adapter。当前已有 `air/`、`naval/`、`ground/` owner；新增域 model owner 应放到这里，而不是继续摊到 `models/` 根目录。
- `environment/`：环境模型和 snapshot。
- `systems/`：传感器和 acoustic helper 等平台系统模型。
- `weapons/`：effects、guidance 和 naval weapon-mount helper。

## 当前阅读入口

- [core/README.md](core/README.md)
- [domains/README.md](domains/README.md)
- [environment/README.md](environment/README.md)
- [systems/README.md](systems/README.md)
- [weapons/README.md](weapons/README.md)

## 当前文件落点

- `core/`
  - `default_unit_factory.h`
- `domains/`
  - `air/default_control_model.cpp`, `air/default_effects_air_domain.h`
  - `naval/default_effects_naval_domain.h`, `naval/naval_sensor_maritime_adapter.h`
  - `ground/default_effects_ground_domain.h`
- `environment/`
  - `default_environment_model.cpp`, `default_environment_snapshot.h`
- `systems/`
  - `default_sensor_model.cpp`, `default_acoustic_model.cpp`
- `weapons/`
  - `default_effects_model.cpp`, `default_guidance_model.cpp`,
    `naval_weapon_mounts.h`, `detail/default_effects_domain_routing_detail.inc`

## 迁移备注

新增模型应优先检查 `core/interfaces` 是否已有 contract。没有 contract 时，先补接口边界，再引入默认实现。
