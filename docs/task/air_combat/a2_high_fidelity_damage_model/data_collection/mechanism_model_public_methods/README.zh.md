# 公开机制模型方法收集

状态：`2026-05-28` 数据收集包初版。本文档只记录公开爆轰、破片、穿透和连续杆机制模型来源，用于后续 `validated_physics_surrogate` 方法候选筛选；不收集、不推断、不补全任何机密型号数据，也不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

上级准入规则见 [A2 数据来源准入规则](../source_admission_rules_20260528.zh.md)。逐条来源、权利、scope、交叉验证和不确定性记录见 [source_ledger.zh.md](source_ledger.zh.md)。

本轮 `2026-05-28` source pin 补强已把 DDESB TP-20/BEC-O 与 TP-21 记录为公开 benchmark-design / validation-criteria 候选路线，但 artifact、rights 和 checksum 仍待固定；同时把 WBDG 官方声明为 FOUO / export controlled 的 UFC 3-340-01 降级为 rejected-for-use，不得从第三方镜像补其正文。

## 本包范围

本包只回答一个问题：哪些公开方法可以作为 A2 `mechanism_load` 的候选物理代理入口，支持后续把事件几何、战斗部族、距离、角度和候选组件暴露成可审计载荷向量。

纳入范围：

- Hopkinson-Cranz / Sachs scaled distance；
- Kingery-Bulmash 或同类公开 blast overpressure / impulse 工程方法；
- Mott / Gurney / 破片质量与速度分布的公开教材、论文或联合国/工程手册入口；
- 公开穿透近似和 ballistic-limit 方程入口；
- 连续杆战斗部的公开工程描述和可用于方向性/切割机制建模的非型号化描述。

排除范围：

- 具体现役或敏感型号的战斗部几何、装药、预制破片、引信逻辑、方向图和杀伤概率；
- 受限手册或不可再分发数据正文；
- 论坛、民间数据库和二手百科式材料作为 authority；
- 未验证 surrogate 产物或当前仓库 synthetic scaffold 作为真实校准数据。

## 初步结论

| 机制 | 可作为 `mechanism_load` 方法来源 | 只适合背景 / sanity check | 不能直接转成校准参数 |
|---|---|---|---|
| blast scaled distance | UN IATG 01.80 的 Hopkinson-Cranz / Sachs / Kingery-Bulmash 摘要；WBDG/UFC 3-340-02 作为 DoD blast 设计入口 | 公开 blast calculator 或教材复述可用于量级检查 | 不能把 TNT 半球爆地面 burst 曲线直接当任意空空导弹近炸、任意高度或任意装药等效的校准真值 |
| blast overpressure / impulse | Kingery-Bulmash 公开报告引用和 IATG 表述可作为 pressure/impulse proxy 的候选公式入口 | Kinney-Graham 等同类方法可作为交叉检查 | 缺少战斗部真实 TNT 等效、壳体遮挡、空爆姿态和目标局部反射验证时，不能写成 calibrated row |
| fragment velocity | Gurney 方程的公开工程入口和 IATG 初速章节适合作非型号化初速代理 | 历史 BRL/Gurney 原始报告若只定位到题录，可作来源指针 | 不能反推出特定 missile warhead 破片速度或能量分布 |
| fragment mass / count | Mott 1947 论文和 IATG fragment mass-distribution 摘要适合质量分布代理入口 | 安全距离/风险模型中的碎片密度可作 sanity check | 不能当作预制破片数量、材料、形状或方向图校准参数 |
| penetration / ballistic limit | NASA-HDBK-8719.14 的 ballistic-limit equation 章节适合作公开 BLE 形状和验证思路入口；Recht-Ipson DOI、MIL-STD-662F ASSIST/QuickSearch 路线和 DDESB TP-21 可支撑 threshold/debris criteria；UFC 3-340-01 rejected | 航天 Whipple/超高速 BLE、装甲 V50 与空战破片侵彻只做方法类比 | 不能把航天碎片超高速、铝靶、装甲试验或受限防护结构条件直接转成飞机组件穿透概率 |
| continuous rod | JHU/APL Talos continuous-rod warhead 历史公开文章、Science Museum 实物页、公开 naval training/历史资料适合机制背景 | 非官方网页只作 sanity check | 不能从历史 Talos/Mk 46 公开叙述外推到 AIM-120C-class 或任意现代连续杆参数 |

## 对 A2 事件字段的映射建议

当前 A2 `EffectsEvent` 已有 `fragment_energy_j`、`fragment_areal_density_per_m2`、`penetration_margin`、`blast_overpressure_kpa`、`blast_impulse_kpa_ms`、`blast_scaled_distance_m_kg13`、`rod_cut_margin` 和 `surface_incidence_cos` 等机制载荷证据字段。本包建议的公开方法入口只用于生成这些字段的非权威 proxy 或 validated surrogate 候选输入。

可先作为 `mechanism_load` 候选：

- `blast_scaled_distance_m_kg13`：Hopkinson-Cranz / Sachs 作为距离和装药质量的归一化轴；
- `blast_overpressure_kpa` / `blast_impulse_kpa_ms`：Kingery-Bulmash 或 IATG/UFC 公开 blast 方法作为初始工程曲线；
- `fragment_energy_j` / `fragment_areal_density_per_m2`：Gurney 初速 + Mott 质量分布 + 球面稀释/方向 pattern 代理；
- `penetration_margin`：公开 ballistic-limit equation 形状或穿透近似，作为条件过滤指标；
- `rod_cut_margin`：连续杆公开工程描述支持“连续线切割 + 方向性窗口”的代理结构，但参数必须后续由公开验证或 synthetic-only 标注。

必须保持 `background_only`：

- 任何具体武器介绍中的“战斗部类型”“lethal radius”“连续杆/破片描述”；
- 未给出公式、误差范围、适用域和公开权利的工程文章；
- 只描述历史研发过程、测试照片或样件尺寸的博物馆/历史页。

必须拒绝直接参数化：

- 受限、专有或不可再分发手册正文；
- 对现役型号的未授权参数推断；
- 把安全距离/QD 风险模型直接变成空战组件失效概率；
- 把单一公开公式曲线直接授予 `component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`。

## 后续准入门

若本包来源进入 `validated_physics_surrogate` 候选，至少需要补齐：

- surrogate model card：公式版本、单位、适用域、输入输出、数值稳定性和禁用范围；
- validation manifest：公开 benchmark / 文献样例 / 可复现求解批次、误差指标、acceptance criteria 和 sha256；
- residual register：空爆 vs 地面爆、TNT 等效、破片方向图、姿态/遮挡、材料/入射角、目标组件脆弱性等未关闭缺口；
- source ledger row：每条可消费 row 必须保留 `row_id`、`source_ref`、`provenance`，并明确该 row 是 `method_input`、`benchmark` 还是 `background`。
