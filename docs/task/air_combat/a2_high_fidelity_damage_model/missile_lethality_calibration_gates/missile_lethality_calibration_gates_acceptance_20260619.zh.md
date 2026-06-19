# MLF-10 验收记录

状态：`2026-06-19` accepted / retained gate infrastructure；calibration
authority held。

英文主文：
[missile_lethality_calibration_gates_acceptance_20260619.md](missile_lethality_calibration_gates_acceptance_20260619.md)。

## 已验收

MLF-10 验收以下基础设施：

- 有引用的当前类校准证据盘点；
- versioned evidence-manifest、evidence-record 和 audit-report contract；
- 逐字段、fail-closed authority decisions；
- 确定性 audit tooling 和 focused tests；
- retained 当前仓库 manifest 和生成报告；
- engineering proxy、retained evidence、blocked candidate、rejected source
  和 admitted evidence 的显式分离；
- 报告可确定性重生成，并兼容 MLF-9 trend 和 A2 source-admission guardrails 的验证。

## 继续 Held

以下项目继续 held：

- 当前 Stage B evidence 的 `effect_scale_authority`；
- 当前 Stage C evidence 的 `component_failure_probability_authority`；
- TP-21 selected debris output admission；
- BEC-O recalculated blast output admission；
- real-world Pk；
- deterministic fuze reliability；
- stock weapon/target lethality；
- reward authority；
- entity-deletion authority；
- 基于当前 evidence 的 runtime 参数重调。

## 证据

- [盘点](missile_lethality_calibration_gates_inventory_20260619.zh.md)
- [准入契约](missile_lethality_calibration_admission_contract_20260619.zh.md)
- [审计工具](missile_lethality_calibration_gates_audit_tooling_20260619.zh.md)
- [报告集成](missile_lethality_calibration_gates_report_integration_20260619.zh.md)
- [验证](missile_lethality_calibration_gates_validation_20260619.zh.md)
- [当前 retained report](mlf10_calibration_admission_report_20260619.json)

## 收口决策

Gate infrastructure 以 accepted / retained 状态保留在 A2 follow-on 根目录。它不做
物理归档，因为未来 authority-promotion 工作应复用同一 contract、tool 和当前 evidence
manifest surface。

A2 archive registry 继续只登记物理归档的 evidence package。因此 MLF-10 不会被伪造为
一条 archived calibration result。

只有在出现新 evidence、replacement signoff packet 或明确 authority-promotion request
时才重开 MLF-10。任何 authority decision 改变前必须重新生成报告。
