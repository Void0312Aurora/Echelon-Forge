# `src/models/systems` 边界

`models/systems` 保存平台系统相关模型实现，例如 sensor 和 acoustic model 默认实现。

本目录在 sensing/contact 侧是 multi-domain aware，包括 air/visual sensor
行为和 naval/acoustic helper。它不拥有 full ground sensing 或 land C2 runtime 行为。

## 允许

- sensor、acoustic/sonar、track、data-link 等平台系统的可替换计算模型。
- 只依赖 `core/interfaces` 和 component 数据的纯 C++ 逻辑。

## 禁止

- Flecs system tick。
- component 定义。
- Python binding 或 facade。
- full ground sensing、terrain-control 或 fires runtime。

## 迁移备注

目录名与 `systems/systems` 相近，新增文件必须用具体业务名表达模型类型，避免泛化扩张。
