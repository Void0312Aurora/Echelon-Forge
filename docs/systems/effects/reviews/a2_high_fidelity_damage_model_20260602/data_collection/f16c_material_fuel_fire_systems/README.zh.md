# F-16C Block 50 材料/燃油/火灾/结构后果/系统依赖公开来源收集

状态：`data_collection / non-authoritative / public-source-only`  
日期：`2026-05-28`  
适用任务：A2 高保真空战毁伤模型数据收集子任务，目标平台 `F-16C_Block50`。  
写入边界：本目录只包含资料准入与候选结论，不创建 runtime descriptor，不写校准 row。

本文档继续遵守上级准入规则和 `a2.vulnerability_evidence.v1` schema：所有来源默认 `non-authoritative`，不授予 Pk、deterministic fuze、effect-scale、component-failure probability、真实组件失效概率、真实油箱分隔、真实管线布置、真实材料厚度或真实 F-16C Block 50 脆弱性 authority。

## 与已有几何包的关系

已读取并沿用：

- `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/data_collection/source_admission_rules_20260528.zh.md`
- `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/vulnerability_evidence_schema_v1.zh.md`
- `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/data_collection/f16c_block50_target_geometry/`

已有 F-16 几何包已把 `F-16C_Block50` 的公开外形、总燃油量、发动机族、粗组件区和大量材料/装甲/内部布局缺口分开。本目录不改写几何结论，只补充公开来源能支持的燃油火灾、材料防火、结构后果和系统依赖方法背景。

## 本轮可采纳的公开结论

| 主题 | 可采纳结论 | 主要来源 | 当前 authority |
|---|---|---|---|
| F-16 scope 锚点 | 公开来源可支持 `F-16C Block 50/52`、GE F110 系列、外形/燃油总量量级和单发后机身区域作为已有几何包的上下文。 | USAF / Shaw fact sheet、GE F110 data sheet、既有几何 ledger。 | `candidate / non-authoritative` |
| 燃油箱爆炸/着火机制 | FAA/NTSB 公开资料支持把 fuel tank ullage flammability、ignition-source prevention、flammability-reduction/inerting、lightning/bonding/venting 作为通用机制轴。 | FAA AC 25.981-1D、AC 25.981-2A、AC 20-53B、FTFAM、NTSB TWA 800。 | `method/consequence candidate / non-authoritative` |
| 航空材料防火测试 | FAA 材料防火测试手册可作为材料燃烧/烟/火焰传播测试方法和术语来源。 | DOT/FAA/AR-00/12 Aircraft Materials Fire Test Handbook。 | `materials_fire_test_method_candidate / non-authoritative` |
| 发动机舱/干舱火灾 | NIST engine nacelle / dry bay 公开研究可支持 fuel/hydraulic/lube lines、ventilation、drainage、suppression distribution、full-scale validation 这些通用依赖轴。 | NIST SP 890、SP 984、NIST nacelle suppression papers。 | `generic_fire_system_candidate / non-authoritative` |
| 电气/液压/火灾级联 | FAA fire-protection/system-safety AC 和 AMT handbooks 可支持通用依赖图：EWIS、电气火源、可燃液体、液压/燃油/润滑、氧气/通风/灭火、冗余和隔离。 | FAA AC 25.869-1A、AC 25.1309-1A、AC 25.795-7、FAA-H-8083 handbooks。 | `dependency_taxonomy_candidate / non-authoritative` |
| 损伤后飞行后果 | NASA damaged-aircraft 公开论文可支持把 wing/tail/control-surface loss、rolling/yawing asymmetry、control degradation、thrust loss 等作为后果验证类目。 | NASA NTRS 20080034656、20120014568、20100002211。 | `consequence_validation_candidate / non-authoritative` |
| F-16 结构重要性 | USAF/GAO SLEP 公开资料支持 F-16 C/D 结构寿命、结构强化、翼/机身/座舱等结构件是应保留的后果节点。 | GAO-13-51、USAF F-16 SLEP 新闻。 | `structural_criticality_candidate / non-authoritative` |
| 组件到系统传播 | 公开 survivability 文献可支持用 component/state/fault-tree/redundancy 表达系统依赖，但不能提供 F-16C 概率表。 | FOI component kill criteria、Li 2013 aircraft vulnerability modeling、既有 component fragility ledger。 | `method_candidate / non-authoritative` |

## 不应采纳的结论

本轮没有找到可公开、可引用、scope 匹配且权利清楚的来源，能够支持以下任一项：

- F-16C Block 50 真实机体材料分区、蒙皮/框梁/翼梁材料厚度、座舱透明件抗毁参数或装甲厚度。
- F-16C Block 50 真实内油箱分隔、油箱壁材料、油箱防火/惰化/自封细节、通气管路和 fuel transfer routing。
- F-16C Block 50 真实液压/电气/燃油/飞控线束或管线布置。
- F-16C Block 50 真实 engine bay / dry bay suppression layout、灭火剂容量、喷嘴位置或传感器逻辑。
- 任何 component failure probability、effect scale、Pk、deterministic fuze 或 missile-to-component calibrated vulnerability row。

## 可映射到后续数据结构的弱候选

| 后续字段/概念 | 本轮可支持的最低形状 | 必须保留的 residual |
|---|---|---|
| `fuel_fire_mechanism_axes` | `fuel_vapor_ignition`, `flammability_exposure`, `ullage_oxygen`, `venting`, `bonding/lightning`, `flammable_fluid_leak`, `drainage`, `suppression_distribution`。 | 民用 transport 和通用 nacelle 资料，不匹配 F-16C Block 50；不能推导概率或阈值。 |
| `material_fire_test_axes` | `flame_propagation`, `burnthrough`, `smoke/toxicity`, `wire/arc`, `compartment_material_test` 等测试类别。 | 不包含 F-16 真实材料清单；只能作为测试方法和术语。 |
| `system_dependency_nodes` | `fuel`, `hydraulic`, `lubrication`, `electrical/EWIS`, `engine`, `flight_control`, `fire_detection`, `fire_suppression`, `ventilation/drainage`, `structure`。 | 节点存在性通用，F-16 内部拓扑和冗余未知。 |
| `damaged_aircraft_consequence` | `control_loss`, `aero_surface_loss`, `rolling_asymmetry`, `yaw/pitch degradation`, `thrust_loss`, `structural_breakup`, `safe-flight-and-landing residual`。 | NASA/NTSB 案例主要是民用运输机或通用模型，不给空战毁伤概率。 |
| `F-16 structural residual` | SLEP/GAO 支持结构寿命和结构强化是公开议题。 | 不支持翼梁位置、主框强度、材料分布、毁伤阈值或 Block 50 专属结构图。 |

## 拒绝来源摘要

| 类别 | 判定 | 原因 |
|---|---|---|
| F-16 technical order、维修手册、飞行手册、IPB、结构维修手册、航电/武器接口手册镜像 | `rejected` | 可能受限、出口管制、权利不明或不可再分发；不得摘录或派生内部布局。 |
| 论坛附件、网盘 PDF、泄露课件、承包商报告、FOUO/CUI/ITAR 标注材料 | `rejected` | 不满足公开和权利准入，且高风险污染模型。 |
| 未授权 CAD、付费/来历不明 3D 模型、DCS/War Thunder/游戏 damage boxes | `rejected` | 权利和真实性不满足，不能进入 high-fidelity evidence chain。 |
| Wikipedia、F-16.net、论坛帖子、社媒战损照片 | `sanity_check_only` 或 `rejected` | 可提示检索关键词或核对明显外形，但不能授予 authority。 |
| 单一营销宣传值或无报告编号的图表 | `sanity_check_only` | 缺 provenance、scope 和交叉验证，不可直接采纳。 |

## 当前 residual

- F-16C Block 50 的真实材料、油箱、防火、液压、电气、飞控和火灾探测/灭火拓扑仍为空白。
- 公开 FAA/NIST/NASA 资料主要来自民用运输机或通用试验，不直接匹配单发战斗机和空空导弹毁伤。
- NIST engine nacelle / dry bay 研究能支持通用 fire-cascade 结构，但不能给 F-16 engine bay 或 dry bay 几何。
- NASA damaged-aircraft 资料能支持后果类目和验证思路，不能给武器命中、破片、火灾增长或组件失效概率。
- GAO/USAF SLEP 只能证明 F-16 结构寿命/结构强化重要，不能派生翼梁、框、舱段材料或强度。
- 若后续创建 descriptor，必须另建 validated surrogate manifest 或 external calibration dataset；本目录不能让任何 row 通过 runtime authority gate。

## 文件

- [source_ledger.zh.md](source_ledger.zh.md)：逐条候选来源、sanity check 和拒绝记录。
- [source_pin_update_20260528.zh.md](source_pin_update_20260528.zh.md)：本轮 source pin、字段级支持边界和 material/fuel/fire dependency authority gap 更新。
