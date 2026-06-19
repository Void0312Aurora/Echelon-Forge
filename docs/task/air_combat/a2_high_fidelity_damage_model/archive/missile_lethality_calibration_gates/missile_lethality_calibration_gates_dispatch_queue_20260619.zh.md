# MLF-10 校准门派发队列

状态：`2026-06-19` P0-P6 complete，用于
[MLF-10 校准门](README.zh.md)。

## Completed Queue

| Date | Packet | Cluster | Output | Status |
| --- | --- | --- | --- | --- |
| `2026-06-19` | `MLF10-Q0` | `MLF10-P0` | 子项目面和父级 live entry | complete |
| `2026-06-19` | `MLF10-Q1` | `MLF10-P1` | [类校准证据盘点](missile_lethality_calibration_gates_inventory_20260619.zh.md) | complete |
| `2026-06-19` | `MLF10-Q2` | `MLF10-P2` | [Admission contract 和 report schema](missile_lethality_calibration_admission_contract_20260619.zh.md) | complete |
| `2026-06-19` | `MLF10-Q3` | `MLF10-P3` | [确定性 audit tooling](missile_lethality_calibration_gates_audit_tooling_20260619.zh.md) | complete |
| `2026-06-19` | `MLF10-Q4` | `MLF10-P4` | [Retained report integration](missile_lethality_calibration_gates_report_integration_20260619.zh.md) | complete |
| `2026-06-19` | `MLF10-Q5` | `MLF10-P5` | [聚焦验证](missile_lethality_calibration_gates_validation_20260619.zh.md) | complete |
| `2026-06-19` | `MLF10-Q6` | `MLF10-P6` | [验收记录](missile_lethality_calibration_gates_acceptance_20260619.zh.md) | complete |

## Active Queue

当前没有 active packet。只有在验收记录定义的条件下才重开。

## Planned Queue

当前 evidence set 没有 planned packet。

## Hold 条件

- 如果请求在 admission contract 存在前直接调参，停止。
- 如果 report 会在 admission 前暗示 real-world Pk、weapon-specific lethality、
  target-specific lethality 或 deterministic fuze truth，停止。
- 如果 source 需要接入但缺 source-rights 和 provenance review，停止。
- 如果实现必须重写已归档 MLF evidence，而不是消费 accepted outputs，停止。

## Q0-Q6 验证

- 对父级 A2 README 文件和 MLF-10 docs 做本地 Markdown 链接检查。
- `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model`。
- 聚焦 MLF-10、MLF-9 和 A2 source-admission tests。
- 确定性 retained-report regeneration。
