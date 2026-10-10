# 飞机结构包线损伤契约

Language:
- English canonical: `docs/architecture/standards/aircraft_structural_envelope_damage_contract.md`
- Chinese companion: `aircraft_structural_envelope_damage_contract.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/aircraft_structural_envelope_damage_contract.md`
Owner: `architecture/air-damage`
Last verified: `2026-10-10`

本文档定义飞机结构包线渐进损伤的维护中运行时契约。它描述状态转移语义，
不声称当前系数已经针对某一种具体机型完成标定。

## 起始与累积

- 维护中的辅助函数是
  `src/systems/combat/damage_system_air.h` 中的
  `accumulate_aircraft_structural_envelope_damage`。
- 非正时间步长不产生状态变化。
- 当动压和马赫数均不超过配置的颤振基线时，完整机体不会产生包线起始损伤。
- 当任一量超过对应基线时，系统会向颤振暴露度和结构超载增加有界的正向起始速率。
  该起始项不要求已有损伤，因此完整机体可以进入渐进失效路径。
- 已有结构损伤仍然会放大既有的高能量与失速相关速率，但不再是唯一触发条件。
- 辅助函数运行后，外层飞机损伤系统会对结构完整度、颤振暴露度和结构超载进行限制。

当前起始系数是用于保持转移有限且可测试的合成默认值，并不表示物理或机型标定结果。
机型标定应写入 baseline 数据，同时保持“包线内为零、包线外为正”的契约。

## 验证边界

原生 `structural_failure_state` 测试覆盖包线内零起始、包线外正向起始、时间步长缩放，
以及已有损伤放大。测试通过只证明状态转移契约，不证明飞行动力学保真度或 RL 可利用性。
