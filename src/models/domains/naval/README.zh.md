# `src/models/domains/naval` 边界

`models/domains/naval` 保存由共享 default model 消费的 naval-owned model adapter 与
placeholder route。

## 允许

- 为共享 model 读取 naval component 的 naval-specific model adapter。
- 在维护中的 naval damage-fidelity owner 存在前，保留 legacy 行为的显式
  placeholder effects routing。

## 禁止

- ECS system registration。
- 定义 naval component 或 mission/tasking DTO。
- 因 placeholder effects route 宣称完整 naval damage fidelity。

## 当前文件

- [naval_sensor_maritime_adapter.h](naval_sensor_maritime_adapter.h)
  - generic sensor model 使用的 ship-specific maritime state 与 radar helper 访问。
- [default_effects_naval_domain.h](default_effects_naval_domain.h)
  - 保持 finalize-only 行为的 placeholder naval effects routing。
