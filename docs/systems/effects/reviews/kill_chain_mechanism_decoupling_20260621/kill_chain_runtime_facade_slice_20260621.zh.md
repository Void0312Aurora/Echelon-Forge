# P2/P5 runtime facade 清理切片

日期：`2026-06-21`

状态：runtime facade 现在直接由 `EffectsEvent.component_response_rows` 驱动。
旧的 load-row response 投影兜底已删除，load row 不再携带 response owner 字段。

## 当前实现

runtime contract 保留稳定 DTO：

- `KillChainApproachFact`
- `KillChainFuzeDecision`
- `KillChainWarheadLoadField`
- `KillChainTargetSusceptibility`
- `KillChainComponentResponseFact`
- `KillChainConsequenceProjection`
- `KillChainRuntimeFacade`

`make_kill_chain_runtime_facade(const EffectsEvent &effects)` 当前只读取真实 DTO/事件面：

- component load facts 来自 `ComponentMechanismLoadRow` 的载荷/机制字段。
- component response facts 来自 `ComponentResponseRow`。
- 不再从 load row 推导 response probability、sample、failure mode 或 integrity。

## 当前基线

刷新后的 review packet：

`docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_decoupling_probe_20260621.json`

关键状态：

- `facade_status = runtime_dto_backed`
- `component_response_rows_available = true`
- `runtime_response_rows_available = true`
- `rows_with_response_fields_on_load_row = 0`
- `legacy_fuze_quality_damage_multiplier_removed = true`

8 km / 30 度样本仍显示近炸杀伤偏低，这是后续工程代理校准问题，不再由旧兼容层掩盖。

## 验收含义

本切片完成的是 runtime surface 清理，不是杀伤参数校准：

1. P2 的 facade 入口仍存在。
2. P5 的 response owner 已从 load row 分离。
3. 旧投影兜底和旧字段已从 ABI/binding 中移除。
4. 后续校准只能在单层 evidence/admission guard 下调整工程代理数据。
