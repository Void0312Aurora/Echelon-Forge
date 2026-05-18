# `src/models/systems` 边界

`models/systems` 保存平台系统相关模型实现，例如 sensor model 默认实现。

## 允许

- sensor、track、data-link 等平台系统的可替换计算模型。
- 只依赖 `core/interfaces` 和 component 数据的纯 C++ 逻辑。

## 禁止

- Flecs system tick。
- component 定义。
- Python binding 或 facade。

## 迁移备注

目录名与 `systems/systems` 相近，新增文件必须用具体业务名表达模型类型，避免泛化扩张。
