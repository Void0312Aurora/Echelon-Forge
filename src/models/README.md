# `src/models` 边界

`models/` 保存可替换的领域模型实现。它为 `systems/` 和 `core/engine` 提供 control、environment、sensor、effects、guidance、unit factory 等能力。

## 允许

- 默认模型实现。
- 可替换模型的纯 C++ 计算逻辑。
- 只依赖 component 数据和 `core/interfaces` contract 的 helper。

## 禁止

- ECS system registration。
- runtime owner、batch owner 或 facade。
- Python binding。
- 训练配置或 scenario 编排。

## 子目录约定

- `air/`：飞行控制等航空模型。
- `core/`：unit factory 等基础模型实现。
- `environment/`：环境模型和 snapshot。
- `systems/`：传感器等平台系统模型。
- `weapons/`：effects 和 guidance 模型。

## 当前阅读入口

- [air/README.md](air/README.md)
- [core/README.md](core/README.md)
- [environment/README.md](environment/README.md)
- [systems/README.md](systems/README.md)
- [weapons/README.md](weapons/README.md)

## 当前文件落点

- `air/`
  - `default_control_model.cpp`
- `core/`
  - `default_unit_factory.h`
- `environment/`
  - `default_environment_model.cpp`, `default_environment_snapshot.h`
- `systems/`
  - `default_sensor_model.cpp`
- `weapons/`
  - `default_effects_model.cpp`, `default_guidance_model.cpp`

## 迁移备注

新增模型应优先检查 `core/interfaces` 是否已有 contract。没有 contract 时，先补接口边界，再引入默认实现。
