# MLF-10 校准门

状态：`2026-06-19` accepted / retained calibration-gate infrastructure；
calibration authority held。MLF-10 的起点是：项目里已经有不少“校准味道”的工程代理值
和调试结果，但它们在显式 gate 放行前，仍不能被读成真实世界权威。

语言：

- 英文 canonical：[README.md](README.md)
- 中文 companion：`README.zh.md`

输入：

- 父级 A2 follow-on 索引：[../README.zh.md](../README.zh.md)
- MLF archive registry：[../archive_registry.zh.md](../archive_registry.zh.md)
- MLF-9 统计趋势：
  [../archive/missile_lethality_pk_statistical_trends/README.zh.md](../archive/missile_lethality_pk_statistical_trends/README.zh.md)
- MLF-6 结构失效：
  [../archive/missile_lethality_structural_failure/README.zh.md](../archive/missile_lethality_structural_failure/README.zh.md)
- MLF-8 残骸/碎片生命周期：
  [../archive/missile_lethality_debris_wreck_lifecycle/README.zh.md](../archive/missile_lethality_debris_wreck_lifecycle/README.zh.md)
- A2 retained calibration/residual register：
  [../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md](../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md)
- A2 task granularity and authority backlog：
  [../../archive/a2_high_fidelity_damage_model/task_granularity_and_coordination_20260601.zh.md](../../archive/a2_high_fidelity_damage_model/task_granularity_and_coordination_20260601.zh.md)
- Realism authority boundary：
  [../../../../standards/foundation/realism_authority_boundary.zh.md](../../../../standards/foundation/realism_authority_boundary.zh.md)

## 目的

MLF-10 判断已有导弹杀伤证据应如何被读取为 calibration evidence。它不从修改毁伤参数开始。
它首先建立 admission gate，把四类东西分开：

1. 用于仿真行为的 engineering proxy tuning；
2. 可审计但非权威的 research-retained evidence；
3. 具有 provenance、denominator 和 uncertainty 信息的 calibration candidate；
4. released authority claim。除非 gate 明确放行，否则继续拒绝。

这很重要，因为早期 A2/MLF 工作里有多个看起来像校准的值：近场结构阈值、累计翼损行为、
部件失效概率、source-admission packet、敏感性扫参和 MLF-9 trend reports。MLF-10
让这些事实可以被审计，但不偷偷把它们写成真实 AIM-120C、F-16C、MQ-9 或 Pk 真值。

## 当前状态

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| MLF-1..MLF-9 链路证据 | accepted / archived | [archive registry](../archive_registry.zh.md) | 提供可回放仿真事实，不释放校准权威 |
| MLF-9 统计趋势 | accepted / archived | [MLF-9 README](../archive/missile_lethality_pk_statistical_trends/README.zh.md) | 趋势仍是 synthetic；没有真实 Pk 或具体武器/目标杀伤率 |
| A2 calibration residual register | retained / non-authoritative | [residual register](../../archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | 一些 research blocker 已关闭，但 authority blocker 和 fail-closed source gate 仍存在 |
| Source admission and rights packets | retained / mixed pass/fail-closed | A2 calibration package 下 retained artifacts | gate 证据存在；不自动授权 selected outputs |
| Runtime model parameters | active engineering proxies | MLF-6/MLF-7/MLF-8 runtime and diagnostics evidence | MLF-10 在 admission contract 前不得改参数 |

## 范围

纳入：

- 盘点 A2、MLF-6 到 MLF-9、近炸引信现实性和 retained A2 calibration artifacts
  中已有的 calibration-like evidence。
- 定义 calibration-admission contract，包含 provenance、source rights、denominator
  identity、uncertainty、independence 和 authority flags。
- 建立 audit/report surface，把证据分类为 rejected、retained-non-authoritative、
  calibration-candidate 或 admitted。
- 保持 real-world Pk、deterministic fuze reliability 和 stock weapon/target truth
  fail-closed，除非 gate 明确放行。
- 记录当前模型值中哪些只是 engineering proxy，哪些可以成为 calibration candidate。

不纳入：

- admission contract 之前不直接调 runtime 参数。
- 不声明真实 AIM-120C Pk、F-16C/MQ-9 杀伤率、deterministic fuze 或 stock weapon
  effectiveness。
- 不释放 reward authority、entity deletion authority 或 direct crash rule。
- 不回写已归档 MLF-1 到 MLF-9 证据包；除非只是修断链。
- 没有 source-rights 和 provenance review 前，不抓取或接纳新的公开数据。

## 阶段计划

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 打开 MLF-10 并冻结禁止声明。 | MLF-9 accepted / archived。 | README、current status、dispatch queue 和 task clusters 存在。 | complete |
| `P1 Calibration Inventory` | 映射已有 calibration-like values 和 retained source gates。 | P0 docs 存在。 | Inventory 区分 engineering proxy、retained evidence、candidate 和 authority blocker。 | complete |
| `P2 Admission Contract` | 定义 source/provenance/uncertainty/denominator gate schema。 | P1 inventory 完成。 | Contract 可拒绝或接纳证据，且不需要先改 runtime 参数。 | complete |
| `P3 Audit Tooling` | 对 retained evidence 和 MLF-9 trend artifacts 产出确定性 audit reports。 | P2 contract 可用。 | 聚焦测试覆盖 pass、fail-closed 和 retained-non-authoritative cases。 | complete |
| `P4 Report Integration` | 将 gate reports 暴露为 retained diagnostics artifacts。 | P3 tool 存在。 | Reports 可消费但不暗示 stock authority。 | complete |
| `P5 Validation` | 执行聚焦验证和本地链接检查。 | P4 reports 可用。 | Validation 记录 accepted/held boundaries 和 residuals。 | complete |
| `P6 Closure` | 接受 gate infrastructure 或 hold/re-scope calibration authority。 | P5 证据存在。 | 父级索引和 archive registry 与结论一致。 | complete |

## 任务簇

- Task cluster plan：
  [missile_lethality_calibration_gates_task_clusters_20260619.md](missile_lethality_calibration_gates_task_clusters_20260619.md)
- Current status：
  [missile_lethality_calibration_gates_current_status_20260619.md](missile_lethality_calibration_gates_current_status_20260619.md)
- Dispatch queue：
  [missile_lethality_calibration_gates_dispatch_queue_20260619.md](missile_lethality_calibration_gates_dispatch_queue_20260619.md)
- 类校准证据盘点：
  [missile_lethality_calibration_gates_inventory_20260619.zh.md](missile_lethality_calibration_gates_inventory_20260619.zh.md)
- 校准准入契约：
  [missile_lethality_calibration_admission_contract_20260619.zh.md](missile_lethality_calibration_admission_contract_20260619.zh.md)
- 准入审计工具：
  [missile_lethality_calibration_gates_audit_tooling_20260619.zh.md](missile_lethality_calibration_gates_audit_tooling_20260619.zh.md)
- Retained report 集成：
  [missile_lethality_calibration_gates_report_integration_20260619.zh.md](missile_lethality_calibration_gates_report_integration_20260619.zh.md)
- 聚焦验证：
  [missile_lethality_calibration_gates_validation_20260619.zh.md](missile_lethality_calibration_gates_validation_20260619.zh.md)
- 验收记录：
  [missile_lethality_calibration_gates_acceptance_20260619.zh.md](missile_lethality_calibration_gates_acceptance_20260619.zh.md)

## 输出和证据

- MLF-10 planning surface 和父级 A2 live-entry link。
- 有限任务簇计划，覆盖 calibration inventory、admission contract、audit tooling、
  report integration、validation 和 closure。
- current-status 记录：已有模型调参是 audit input，不是已释放 authority。
- P1 证据盘点：在不改变 runtime 行为或接纳 authority 的前提下完成现有证据分类。

## 验收门

本子项目只有在以下条件满足时才能标记 accepted：

- 每个 admitted calibration claim 都引用 source、provenance path、denominator、
  uncertainty treatment 和 authority flag；
- fail-closed source gates 保持 fail-closed，除非提供并通过有效 replacement packet；
- MLF-9 trend reports 继续标注为 synthetic simulation trends，除非后续 gate 明确提升；
- real-world Pk、weapon-specific lethality、target-specific lethality、
  deterministic fuze reliability、reward authority 和 entity deletion 继续拒绝，
  除非被单独接纳。

## 残余和下一步

- 当前 evidence set 下的立即工作已完成。
- Held：实际 runtime 参数重调、selected public-output admission 或 stock weapon/target
  calibration。

## 归档

MLF-10 以 accepted / retained 状态保留，不物理归档，以便未来 authority-promotion
复用 gate surface。只有在存在替代记录后，过期材料才移动到
[archive/README.zh.md](archive/README.zh.md)。
