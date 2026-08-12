# MLF-10 类校准证据盘点

状态：`2026-06-19` P1 complete。本盘点对 A2 和 MLF-6 到 MLF-9 中已经存在的
证据进行分类。它不接入新来源、不修改 runtime 参数，也不释放任何 authority。

英文主文：
[missile_lethality_calibration_gates_inventory_20260619.md](missile_lethality_calibration_gates_inventory_20260619.md)。

## 分类规则

| 分类 | MLF-10 中的含义 |
| --- | --- |
| `engineering_proxy` | 已进入维护中的仿真数值或机制，有测试，但没有释放真实世界校准声明。 |
| `retained_non_authoritative` | 为审阅、回放或方法开发保留的可审计证据，不能驱动已释放的校准声明。 |
| `calibration_candidate` | 已具备足够 provenance、总体身份、uncertainty 和 authority metadata，可进入契约审阅，但不能自动通过。 |
| `admitted` | 已在明确 scope 和 authority 字段上通过 MLF-10 admission contract 的证据。 |
| `rejected` | provenance、权利、稳定性或 scope 不合格，不能被消费的证据或声明。 |
| `blocked` | 可能相关，但必需 gate 仍 fail-closed 或未完成的证据。 |

这些标签只描述 MLF-10 当前如何处理证据，不回写已归档来源包的状态。

## 证据盘点

| ID | 证据族 | 稳定证据 | 分类 | 总体 / 分母解释 | Authority 与残余解释 |
| --- | --- | --- | --- | --- | --- |
| `INV-001` | MLF-6 近场结构阈值和累计翼损行为 | [MLF-6 README](../missile_lethality_structural_failure/README.zh.md) | `engineering_proxy` | 受控 runtime probe 和回归案例，不是真实武器/目标试验总体 | 可支持相对仿真行为；不支持 AIM-120C/F-16C 结构杀伤或 Pk authority。 |
| `INV-002` | MLF-7 平台后果投影 | [MLF-7 README](../missile_lethality_secondary_consequence_coupling/README.zh.md) | `retained_non_authoritative` | 以 accepted simulation breakup facts 为条件的后果行 | 只支持 chain outcome labels；不支持 target-specific mission kill 或 direct crash authority。 |
| `INV-003` | MLF-8 脱落部件和终端残骸生命周期事实 | [MLF-8 README](../missile_lethality_debris_wreck_lifecycle/README.zh.md) | `retained_non_authoritative` | 仿真链路上的 diagnostics-only lifecycle rows | 不支持校准碎片抛散、碎片损伤概率、reward 或 entity-deletion authority。 |
| `INV-004` | 近炸引信探测、触发、可靠性和机制覆盖 surrogate | [近炸引信现实性 README](../missile_lethality_proximity_fuze_realism/README.zh.md) | `engineering_proxy` | 聚焦 surrogate 矩阵和 live-guidance probes，不是 live-fuze trials | 机制形状可审阅；真实阈值、可靠性、deterministic fuze truth 和 Pk 继续拒绝。 |
| `INV-005` | MLF-9 趋势报告和 Wilson-style intervals | [MLF-9 指标契约](../missile_lethality_pk_statistical_trends/missile_lethality_pk_statistical_trends_metric_contract_20260619.zh.md)与[验证](../missile_lethality_pk_statistical_trends/missile_lethality_pk_statistical_trends_validation_20260619.zh.md) | `retained_non_authoritative` | 显式 `(episode, chain_id)` 仿真总体，分母和区间方法均命名 | 可作为 audit-tool input；synthetic source population 阻止真实世界 calibration 或 Pk 提升。 |
| `INV-006` | A2 窄域 blast-fragmentation surrogate 候选包 | [候选包 README](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/README.zh.md) | `calibration_candidate` | 固定 scope：F-16C Block 50、AIM-120C-class blast-fragmentation、beam/high、near-miss 0-0.35 m；author-side benchmark populations | 只属于可审阅研究候选；所有 stock authority flags 仍为 false。 |
| `INV-007` | Stage B effect-scale snapshot、retained pack、criteria、scope、uncertainty 和 review-readiness evidence | [Stage B review-readiness record](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_review_readiness_record_stage_b_effect_scale_20260530.zh.md)与[uncertainty gate](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_uncertainty_review_gate_20260531.zh.md) | `calibration_candidate` | Fixed-seed author-side benchmark cases 和 seed-window summaries，不是 operational trials | 其形状足以支持 P2 contract 设计；independent review、release-grade source/identity 和机制残余仍阻止 admission。 |
| `INV-008` | Stage C component-specific failure-probability surface | [Stage C review-readiness gate](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/validation_review_readiness_gate_stage_c_component_probability_20260530.zh.md) | `blocked` | Test-local、component-specific candidate rows 和 fixed-seed repeatability | 被 independent fragility truth、uncertainty coverage、geometry/mechanism provenance、independence 和 upstream Stage B release state 阻塞。 |
| `INV-009` | 窄域内部 source-signoff 和 scoped surrogate-identity records（`RES-001/002`） | [residual register](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | `retained_non_authoritative` | Package identity 和 retained payload accounting，不是 lethality population | 支持 traceability；不建立 external release rights、global release identity 或 calibration authority。 |
| `INV-010` | TP-21 selected debris comparison outputs（`RES-005`） | [residual register](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | `blocked` | 必需 reviewer-selected cases 和 selected-output preimages 不完整 | 在 locator、hashes、independent review、allowed-output signoff 和 authority-boundary signoff 通过前保持 fail-closed。 |
| `INV-011` | BEC-O recalculated selected blast outputs（`RES-006`） | [residual register](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | `blocked` | 已有 9 个 recalculated candidate outputs，但 9/9 hashes 与 cached anchors 不一致 | 在 lineage review、allowed-output signoff、tolerance policy 和 replacement-anchor signoff 完成前保持 fail-closed。 |
| `INV-012` | 真实世界 Pk 声明（`RES-013`） | [residual register](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | `blocked` | 没有独立 real-world kill-chain denominator 或 evidence chain | MLF-9 simulation denominators 不能关闭此边界。 |
| `INV-013` | Deterministic fuze reliability 声明（`RES-014`） | [residual register](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | `blocked` | 没有 admitted live fuze、target-signature、reliability 和 miss-distance joint population | 近炸引信 surrogate 行为不能关闭此边界。 |
| `INV-014` | Restricted、leaked、unstable、untraceable、rights-unclear 或 scope-mismatched source material | [公开数据来源准入标准](../../../../../../research/standards/public_data_source_admission.zh.md) | `rejected` | 来源不能进入证据链，因此不存在合格 denominator | 不得进入 descriptor row、generated benchmark、参数调节或 runtime authority path。 |
| `INV-015` | 已释放的 MLF-10 校准证据 | 本盘点 | `admitted` | 无 | P1 没有任何证据被接纳。Admission 需要 P2 contract 和后续明确 gate decision。 |

## Gate 字段覆盖

| 证据族 | Source / provenance | Rights | Scope | Denominator | Uncertainty | Independence | 显式 authority 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MLF-6 / MLF-7 / MLF-8 runtime evidence | 仓库代码、测试和归档记录 | 仓库内 | 显式 simulation scope | 受控案例或 chain rows | 限于 test/probe variation | 回归证据，不是 external validation | 按任务边界保持 non-authoritative |
| Proximity-fuze surrogate | 公开机制参考和仓库实现证据 | 只支持方法参考 | 有边界 surrogate scope | 聚焦矩阵 / live probe cases | 已记录 residuals | 无 live-fuze independent validation | deterministic-fuze 和 Pk authority false |
| MLF-9 trends | 显式 replay rows 和 report schema | 仓库内输入 | 命名 synthetic scenario / fixture population | 命名 counts 和 filters | 显式 interval method 和 sample count | 声明 fixture/seed provenance | real-world Pk authority false |
| A2 Stage B candidate | Source ledger、pinned artifacts、manifests、hashes 和 review records | Mixed retained / fail-closed | 窄 target/weapon/aspect/closure/miss-distance scope | Fixed-seed benchmark cases | Author-side seed-window review | 部分完成；release-grade independent review 不完整 | Candidate，所有 stock flags false |
| A2 Stage C candidate | Retained component row chain | 继承未关闭 source gates | 窄候选 scope 内单组件 | Test-local component rows | 只有 repeatability；coverage 不完整 | 缺 independent fragility truth | Blocked |
| TP-21 / BEC-O selected outputs | Retained gate records | Allowed-output signoff 不完整 | 窄 mechanism evidence | Selected cases 不完整或 replacement disputed | Tolerance/signoff 不完整 | Independent review 不完整 | Fail-closed |

## P2 Contract 输入

Admission contract 至少必须要求：

1. 稳定 evidence 和 source identifiers；
2. provenance 与 rights/redistribution state；
3. 精确 weapon、target、mechanism、geometry、aspect、closure 和 miss-distance scope；
4. population identity、denominator name、count、filters 和 independence assumptions；
5. uncertainty method、coverage 和 residuals；
6. independent-review status；
7. field-specific authority requests 和 decisions；
8. 对 Pk、deterministic fuze、reward、entity deletion 以及越界 weapon/target truth 的
   explicit non-claims。

任何必填字段缺失时，contract 必须默认输出 `blocked` 或
`retained_non_authoritative`。它不得从 passing test、benchmark snapshot、
retained artifact pack 或 author-side review 自动推导 admission。

## P1 决策

`MLF10-P1` 已完成：

- 当前证据族均已分类；
- 当前没有任何证据被 admitted；
- Stage B 是唯一已经可以演练 candidate contract 的证据族；
- Stage C、TP-21、BEC-O、Pk 和 deterministic fuze 继续 blocked；
- runtime 参数没有变化。

下一串行 packet 是 `MLF10-P2`：基于本盘点定义 admission contract 和 report schema。
