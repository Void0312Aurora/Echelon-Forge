# A2 MLF-5 当前状态

状态：`2026-06-11` accepted / archived。MLF-5 已作为独立“部件脆弱性与失效”子项目完成收口；`MLF-5A-X1 Boundary And Inventory`、`MLF-5B-W1 Component Damage Event Surface`、`MLF-5C-W1 Generic Vulnerability Probability`、`MLF-5D-W1 Component State Handoff`、`MLF-5E-W1 Diagnostics And Gates` 与 `MLF-5F-C1 Acceptance And Archive Prep` 均已验收。Helmholtz 返回 partial 后，主线程修正为“只有样本触发才导出 `ComponentDamageEvent`”；5D 又把 `integrity_before` / `integrity_after` 接到同一受载行的真实状态写入前后值；5E 将部件损伤事实接入诊断链路；5F 将本证据包移入 archive 并同步父索引。

英文辅文：[missile_lethality_component_failure_current_status_20260611.md](missile_lethality_component_failure_current_status_20260611.md)

## 本次变化

- 创建独立于已归档 MLF-3/MLF-4 的 MLF-5 工作面。
- 明确第五阶段只消费部件受载和切割曝光，输出部件失效概率、失效模式和状态变化。
- 明确飞行性能、控制、推进、传感器等后果通过已有损伤/飞行系统传播，不由 MLF-5 单独判死。
- 保持结构解体、残骸、Pk、训练胜负和真实弹种校准在本阶段之外。
- 验收 5A 只读盘点：[missile_lethality_component_failure_inventory_20260611.zh.md](missile_lethality_component_failure_inventory_20260611.zh.md)。盘点确认候选实现面丰富，但标准 `ComponentDamageEvent` writer / probe / focused tests 尚未闭合。
- 派发 5B，目标是闭合同链路部件损伤标准事件面，不进入概率模型、诊断、飞行动力学或高层杀伤结论。
- 验收 5B 标准事件面：新增 `EngagementComponentDamageEventRecord` / `record_component_damage_event`，事件存储可导出同链路 `ComponentDamageEvent`，聚焦测试覆盖触发样本、未起爆、无部件载荷和 Python 绑定。
- 主线程修正 5B gate：正概率本身不导出部件损伤事件，只有 `failure_sample <= failure_probability` 的样本触发路径才导出；避免把“有风险”写成“已经发生失效”。
- 主线程本地验收 5C：新增 `test_component_failure_probability_surface.py`，确认通用失效概率随载荷、连续杆切割裕度、冗余/关键性、已有损伤和授权证据行变化；未授权或不匹配的证据行会退回通用未校准估算。
- 主线程追加 5C 近炸量级修正：通用近炸破片/爆压通道把理想近炸主受影响部件提升到约三分之一概率；连续杆擦过关键部件时也进入可观察概率，同时保持远距/弱载荷显著更低，并继续标注为未校准估算。
- 主线程修复调试命中抽样种子：`debug_apply_*proximity_hit*` 不再使用固定 `123456789` 作为合成导弹随机种子；多种子场景统计现在能真实反映抽样变化。
- 主线程本地验收 5D：`ComponentMechanismLoadRow` 记录部件完整度和冗余组可用度的前后值，`ComponentDamageEvent` 复制同一行的 `integrity_before` / `integrity_after`；测试确认不再导出默认 `1.0 -> 1.0` 的空前后值。
- 主线程本地验收 5E：诊断链路 schema 升为 v2，新增 `component_damage` 阶段和部件失效概率、样本、失效模式、完整度前后值摘要；测试确认标准 `ComponentDamageEvent` 优先、旧 `EffectsEvent` 只在样本触发时做过渡投影，未触发样本不产生虚假部件损伤行。
- 主线程本地验收 5F：新增收口验收页，将详细证据包归档，并把 MLF-5 顶层 README、archive 索引、A2 指针和 MLF-4 后续指针同步为归档入口。

## 成熟度矩阵

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 子项目文档 | accepted / archived | README、任务簇、当前状态、派发队列、archive index、收口验收 | 只验收 MLF-5 部件失效事实链 |
| MLF-3 部件受载 | accepted / archived | [../../../missile_lethality_warhead_effects/README.zh.md](../../../missile_lethality_warhead_effects/README.zh.md) | 不判断部件失效 |
| MLF-4 切割曝光 | accepted / archived | [../../../missile_lethality_continuous_rod/README.zh.md](../../../missile_lethality_continuous_rod/README.zh.md) | 不判断部件是否坏掉 |
| MLF-5A 盘点 | accepted | [missile_lethality_component_failure_inventory_20260611.zh.md](missile_lethality_component_failure_inventory_20260611.zh.md) | 只验收字段、候选实现、历史测试和缺口 |
| MLF-5B 事件面 | accepted | `src/core/interfaces/engagement_event_recorder.h`、`src/core/engine/simulation_kernel_engagement_event_store.*`、`tests/runtime/air_combat/test_component_damage_event_surface.py` | 不修改概率模型、诊断、飞行动力学、结构解体、残骸、Pk 或训练胜负 |
| MLF-5C 概率面 | accepted | `tests/runtime/air_combat/test_component_failure_probability_surface.py`、[default_effects_system_effect_detail.inc](../../../../../../../src/models/weapons/detail/default_effects_system_effect_detail.inc) | 通用、未校准、可替换；不提升为真实弹种 Pk |
| MLF-5D 状态前后值 | accepted | [engagement_contracts.h](../../../../../../../src/runtime/contracts/engagement_contracts.h)、`src/models/weapons/detail/default_effects_component_damage_detail.inc`、`tests/runtime/air_combat/test_component_damage_event_surface.py` | 只暴露已有状态变化，不单独判坠毁或解体 |
| MLF-5E 诊断和禁止声明 | accepted | `tools/diagnostics/air_combat_weapon_employment_process_probe.py`、`tests/runtime/air_combat/test_diagnostics_probe_contracts.py` | 解释部件损伤，不声明坠毁、解体、残骸、Pk 或训练胜负 |
| MLF-5F 收口归档 | accepted | [missile_lethality_component_failure_acceptance_20260611.zh.md](missile_lethality_component_failure_acceptance_20260611.zh.md)、archive index、A2/MLF-4 指针 | 只同步验收/归档边界，不新增运行时杀伤规则 |
| `ComponentDamageEvent` | accepted writer/diagnostics surface | [engagement_contracts.h](../../../../../../../src/runtime/contracts/engagement_contracts.h) 与 5B/5D writer/export/focused tests；5E diagnostics tests | 不作为坠毁或解体结论 |
| 候选失效概率字段 | accepted generic surface | [effects_model.h](../../../../../../../src/core/interfaces/effects_model.h)、[default_effects_system_effect_detail.inc](../../../../../../../src/models/weapons/detail/default_effects_system_effect_detail.inc) | 不能当成真实 AIM-120C/MQ-9 校准 |
| 损伤传播系统 | active maintained runtime | [damage_system_air.h](../../../../../../../src/systems/combat/damage_system_air.h) | MLF-5 只交接部件状态，不重写飞行动力学 |

## 残余登记

- 5B 已闭合 live writer / export / binding / focused tests，使样本触发后的部件损伤事实从候选 effects 行进入标准事件面。
- 5C 已验收通用概率面，并追加近炸量级修正；35 m 配置下的距离/方位探测显示爆破/破片约 15.75 m 后退出投影，连续杆约 11 m 后退出投影，良好侧向暴露明显高于边缘/越界情形。多种子 sweep 显示理想近炸的任意部件触发率达到 `0.527344` 到 `0.644531`，而边缘/越界仍保持低或零。扩大矩阵显示连续杆非直接轴向掠过明显弱于侧向/上下方暴露。它仍是工程估算和授权证据行覆盖机制，不是 Pk 或具体弹种校准。
- 5D 已可靠捕获完整度前后值；这些值来自部件状态实际写入前后，不是事后伪造。
- 5E 已把部件损伤纳入诊断 probe：标准事件优先，旧 effects 行只在样本触发时过渡投影。
- 历史 `weapon_guidance_realism` 部件损伤/脆弱性测试已有一部分被拆成 MLF-5 聚焦证据；未拆入本阶段聚焦测试的历史测试仍只作脚手架。
- 先前宽筛选测试退出时的 nanobind 泄漏提示已关闭：绑定/helper 默认值不再持有 nanobind 对象，收集阶段和实际运行阶段复测均不再打印泄漏提示。

## 建议行动顺序

1. MLF-5 已关闭，不再派发。
2. 结构解体、残骸和 Pk 仍交给后续阶段。
3. 若需要真实弹种/目标校准，另开后续子项目。

## 禁止过度声明

- 不因部件失效概率为正就声明部件已经坏掉，除非有样本/状态变化事实。
- 不因部件坏掉就直接声明目标坠毁。
- 不因完整度下降就直接声明目标已经失去飞行能力。
- MLF-6 之前不声明结构解体或机体断裂。
- MLF-8 之前不声明残骸/wreck。
- 后续校准门之前不声明 Pk 或真实 AIM-120C/MQ-9 杀伤结论。
