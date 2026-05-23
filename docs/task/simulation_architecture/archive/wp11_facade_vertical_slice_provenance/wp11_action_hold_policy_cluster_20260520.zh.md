# WP11-A ActionHoldPolicy Contract

状态：`2026-05-20` planned WP11 dispatch sheet。

语言：

- 英文主文：[wp11_action_hold_policy_cluster_20260520.md](wp11_action_hold_policy_cluster_20260520.md)
- 中文辅文：`wp11_action_hold_policy_cluster_20260520.zh.md`

输入：

- [WP11 facade vertical slice and provenance](facade_vertical_slice_provenance_wp11_20260520.zh.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.zh.md)
- [WP9 policy contracts](../wp9_contract_infrastructure_closure/wp9_dto_promotion_batch2_cluster_20260520.zh.md)

## 1. 目的

`WP11-A` 添加架构中缺失的 `ActionHoldPolicy` contract。任何 policy/control/physics
cadence claim 之前都必须先有这个 typed contract。

本 stream 只创建 contract 与 tests。Runtime cadence execution 明确不在范围内。

## 2. 范围

范围内：

- 定义 typed `ActionHoldPolicy` DTO/contract；
- 编码 hold-last、interpolate、expire、drop behavior；
- 包含 validity duration、refresh cadence、expiry behavior 与 credit-assignment latency assumptions；
- 若相邻 policy DTO 已 binding-visible，则通过 Python bindings 暴露该 DTO；
- 添加 contract-shape 与 binding smoke tests。

范围外：

- enforcing multi-rate policy/control/physics cadence；
- 修改 scheduler；
- 把 interpolation 应用到真实 control commands；
- 宣称 maintained runtime cadence support。

## 3. Contract Shape

最小字段族：

| Field family | Required meaning |
|--------------|------------------|
| Identity | 可用时包含 stable policy id 或 action family label。 |
| Hold mode | `hold_last`、`interpolate`、`expire` 或 `drop` 之一。 |
| Validity | validity duration、可选 valid-until time 与 expiry action。 |
| Cadence | policy refresh cadence 与 target control cadence declarations。 |
| Interpolation | interpolation mode 或显式 `none`。 |
| Credit | credit-assignment latency / attribution note。 |
| Diagnostics | policy diagnostics-only 或 unsupported 时的 reason。 |

## 4. 验收测试

最小测试：

- C++/header contract 包含 required field families；
- default policy 确定且保守；
- 若添加 validator，invalid hold mode 被 helper 或 validation test 拒绝；
- 触碰 bindings 时，Python binding smoke 暴露 DTO fields；
- tests 断言 WP11-A 不宣称 runtime cadence execution。

## 5. Handoff Contract

返回：

- contract file paths 与 public fields；
- binding paths，如果有触碰；
- tests added or updated；
- commands run and outcomes；
- 哪些字段有意保持 declarative 而非 enforced；
- 给 `WP11-B/C/E` 的 integration notes。
