# WP12-D Intent Injection Authority Guard

状态：`2026-05-20` accepted / implementation mergeable。

语言版本：

- 英文主文：[wp12_intent_injection_authority_guard_cluster_20260520.md](wp12_intent_injection_authority_guard_cluster_20260520.md)
- 中文辅文：`wp12_intent_injection_authority_guard_cluster_20260520.zh.md`

输入：

- [WP12 information and agency enforcement](information_agency_enforcement_wp12_20260520.zh.md)
- [WP12-A Law 14 read-side enforcement](wp12_law14_read_side_enforcement_cluster_20260520.zh.md)
- [WP12-B agency role authority boundary](wp12_agency_role_authority_cluster_20260520.zh.md)
- [WP12-C information transformation surface](wp12_information_transformation_surface_cluster_20260520.zh.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.zh.md)
- [WP11 facade vertical slice and provenance](../wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.zh.md)

## 1. 目的

`WP12-D` 把 read-side、role-authority 与 transformation surfaces 集成为第一个
maintained decision-to-intent guard。maintained `DecisionBelief` 只有在路径携带
provenance、source ids、role authority、有效 timing metadata，并使用
facade-compatible injection seam 时，才可以产出 `ActionIntentPacket` 或
`CoordinationIntentPacket`。

## 2. 范围

范围内：

- guard focused `DecisionBelief -> ActionIntentPacket` path；
- 若同一 validator surface 低风险，也可覆盖 `DecisionBelief ->
  CoordinationIntentPacket`；
- 要求 packet family 已拥有字段中的 provenance labels、transformation step、
  source id、role authority、action interface、`effective_time`、`valid_until`
  与 `merge_policy`；
- 拒绝 unlabeled、unauthorized、expired 或 raw-runtime-injected maintained
  intents；
- 在 WP10/WP11 facade seam 上增加 integration tests。

范围外：

- 大范围 command/tasking runtime rewrite；
- 完整 policy/control/physics cadence；
- 全局 Agency Graph dispatcher；
- 新的 raw command/control injection path；
- backend/fidelity、capability composition 或 counterfactual work。

## 3. 候选实现接缝

编辑前检查：

- `src/runtime/contracts/policy_contracts.h`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_runtime.cpp`
- `python/rl/runtime/agent_shim.py`
- `tests/runtime/facade/test_runtime_facade_window_loop_injection.py`
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`
- `tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py`

优先方式：

- 组合 `WP12-A`、`WP12-B` 与 `WP12-C` 的 validators，而不是复制逻辑；
- accepted intents 通过既有 WP10 cross-layer request/injection seam；
- 在测试中保留 invalid intent evidence，不要静默丢掉原因。

## 4. Gate 规则

| Boundary | 必需行为 |
|----------|----------|
| Authorized maintained intent | 携带有效 belief provenance、合法 transformation step、source id、role authority、action interface、timing metadata 与 merge policy。 |
| Missing provenance | 拒绝。 |
| Invalid or missing role authority | 拒绝。 |
| Illegal transformation shortcut | 除非 diagnostics-only 且不作为 maintained action 注入，否则拒绝。 |
| Raw runtime injection | 对 maintained action/coordination paths 拒绝。 |
| Expired or future-invalid timing | 按既有 cross-layer request rules 拒绝或排队，并有测试证据。 |

## 5. 验收测试

最低测试：

- valid maintained belief-to-intent path 通过 facade-compatible injection 接受；
- missing provenance 失败；
- invalid role authority 失败；
- illegal transformation shortcut 失败；
- raw runtime injection bypass 失败；
- timing/validity metadata 行为被测试，或用命名 residual 明确阻塞；
- 不声明完整 policy/control/physics cadence。

## 6. 交付契约

返回：

- touched validators 与 facade/injection glue；
- accepted 与 rejected packet fixtures；
- 新增或更新的 tests；
- 精确 commands run 与 outcomes；
- 更广 intent families 的 blockers 和 residuals；
- 给 `WP12-E` 的 integration notes。
