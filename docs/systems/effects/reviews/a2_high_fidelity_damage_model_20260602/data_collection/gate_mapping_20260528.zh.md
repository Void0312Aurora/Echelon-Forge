# A2 数据候选到 Evidence Gate 映射 - 2026-05-28

状态：`data_collection_recovered / gate_mapping / non-authoritative`。本文档回收九个并行数据收集包，并把公开来源候选映射到 A2 evidence gate。它不创建 runtime descriptor，不授予 Pk、deterministic fuze、effect-scale 或 component-failure probability authority。

上级准入规则见 [公开数据来源准入标准](../../../../../research/standards/public_data_source_admission.zh.md) 与 [A2 数据来源准入规则](source_admission_rules_20260528.zh.md)。本文件只做 A2 gate 映射。

准入口径补充：A2 不要求每个候选都来自官方权威来源。可追溯第三方、社区和开源资料可以进入候选池，用于 sanity check、方法设计、非权威参数假设或 benchmark design；但引用时必须标记来源性质、合理性评估、交叉验证状态和 residual，且不得单独升格为 runtime authority。

## 回收包

| 包 | 回收状态 | 主要结论 | Authority 状态 |
|---|---|---|---|
| [F-16C Block 50 目标几何](f16c_block50_target_geometry/README.zh.md) | recovered | USAF/Shaw/NAVAIR/GE/GDMS/GAO/SLEP 等公开来源可支持低精度外形、总质量/总燃油量级、F110 后机身区域、鼻锥雷达、座舱、翼面/尾部/结构候选区。 | `target_geometry/component_layout candidate only` |
| [AIM-120C-class 战斗部/引信](aim120c_warhead_fuze/README.zh.md) | recovered | NAVAIR/USAF/ACC/Navy 等公开来源可支持 AIM-120 系列尺寸/全弹质量、blast-fragmentation family、active radar / TDD 术语；C 型具体战斗部和引信参数仍缺。 | `warhead_model/fuze_evidence candidate only` |
| [公开机制模型方法](mechanism_model_public_methods/README.zh.md) | recovered | UN IATG、UFC、Mott/Gurney、NASA BLE、JHU/APL 连续杆等可作为公开 mechanism-load 方法入口。 | `validated_physics_surrogate method candidate only` |
| [组件脆弱性 / 杀伤评估](component_fragility_vulnerability/README.zh.md) | recovered | FOI/NAP/GAO/FAA/NASA/open-access papers 可支持 kill criteria、validation criteria、component-fragility 方法；JMEM/J-ACE/AJEM/COVART 等必须拒绝。 | `method/validation candidate only` |
| [Guidance / miss-distance](guidance_miss_distance_public_methods/README.zh.md) | recovered | JHU/APL、NPS/AFIT、Singer、Zarchan/Siouris 等可支持 PN/APN、miss-distance、evasion、seeker/filter benchmark 和 validation criteria。 | `benchmark/criteria/reproducibility candidate only` |
| [F-16C 材料/燃油/火灾/系统依赖](f16c_material_fuel_fire_systems/README.zh.md) | recovered | FAA/NIST/NASA/GAO/USAF/FOI 等公开来源可支持燃油火灾机制轴、材料防火测试、engine nacelle / dry bay fire、损伤后飞行后果和系统依赖 taxonomy；Block 50 内部材料/油箱/管线/拓扑仍缺。 | `method/consequence/dependency candidate only` |
| [VPS blast-fragmentation 方法](vps_blast_fragmentation_methods/README.zh.md) | recovered | Hopkinson-Cranz/Sachs、UFC/Kingery-Bulmash、Mott/Gurney、BLE/penetration、areal-density/spatial sampling 等可支持 mechanism-load surrogate 方法和 toy benchmark 设计。 | `validated_physics_surrogate method/benchmark candidate only` |
| [组件脆弱性 benchmark 方法](component_fragility_benchmark_methods/README.zh.md) | recovered | FOI/NAP/GAO/Title 10/NASA-STD/HDBK/FAA/NASA/open papers 可支持 component kill criteria、failure probability surrogate benchmark、redundancy/dependency validation 和 residual register。 | `method/benchmark/validation/residual candidate only` |
| [Guidance / evasion benchmark 方法](guidance_evasion_benchmark_methods/README.zh.md) | recovered | PN/APN、terminal evasion、seeker/filter/noise、6DOF/fly-out 公开来源可支持 miss-distance benchmark 组合和复现 manifest。 | `benchmark/criteria/reproducibility candidate only` |

## Gate 映射

| A2 evidence 角色 | 当前可采纳候选 | 可推进动作 | 当前不得声明 |
|---|---|---|---|
| `target_geometry` | F-16 公开外形尺寸、总质量/燃油量级、粗组件布局；三视图和仓库 JSON 只作 sanity check。 | 建立低精度 `target_geometry_candidate`；把当前 hitbox scaffold 的公开支持/engineering gap 分开标注。 | 真实内部结构、材料、装甲、油箱分隔、线缆/液压/电源冗余、组件失效概率。 |
| `material_fuel_fire_dependency` | FAA/NIST/NASA/GAO/USAF/FOI 公开方法可支持燃油箱可燃性、点火源、材料防火测试、engine/dry-bay fire、EWIS/fire/system-safety 和 damaged-aircraft consequence 轴。 | 设计 fire/fuel/material/dependency residual 和非权威 consequence validation；给 aircraft damage cascade 增加公开方法 provenance。 | F-16C Block 50 真实材料厚度、油箱分隔、管线/线束 routing、engine bay/dry bay layout、防火系统参数或组件概率。 |
| `warhead_model` | AIM-120 family 尺寸/全弹质量量级、`blast_fragmentation` family、早期 AIM-120 40 lb 级公开 sanity。 | 保留 `AIM-120C-class` family-level candidate；建立 C 型 warhead/fuze residual。 | AIM-120C 真实装药、TNT 等效、破片数/质量/速度/方向图、lethal radius。 |
| `fuze_evidence` | active radar / TDD / warhead burst-point determination 等公开术语。 | 用于 fuze evidence surface 和 P4 residual，不进入 deterministic admission。 | 触发半径、SNR 门限、safe-arm 逻辑、delay、可靠性、抗干扰细节、deterministic fuze authority。 |
| `mechanism_load` | Hopkinson-Cranz/Sachs、Kingery-Bulmash、Mott/Gurney、ballistic-limit、连续杆、areal-density/spatial sampling 公开机制描述。 | 作为 `validated_physics_surrogate` 方法候选，补 model card、version、unit、range、benchmark、manifest；优先从 `BFM-BM-001..006` 生成非权威 toy benchmark。 | 直接把公开公式写成 calibrated component-failure row、真实 AIM-120C warhead 参数或 Pk。 |
| `component_fragility` | FOI component kill criteria、NAP/GAO/LFT&E、NASA-STD/HDBK、FAA system safety、open-access shotline/vulnerability papers、NASA damaged-aircraft consequence studies。 | 设计 component kill criteria schema、fault-tree / redundancy validation、failure probability surrogate benchmark 和 residual register。 | 真实 F-16C Block 50 组件 Pcd|h、Pk、JMEM/J-ACE/AJEM/COVART 数据。 |
| `benchmark_dataset` | NPS/AFIT PN/evasion 老论文、JHU/APL guidance/filter/6DOF、NASA/NACA miss-distance、A2 internal geometry matrix、BFM toy benchmarks，以及经标记和合理性评估的第三方/社区候选数据。 | 生成公开可复现 toy benchmark，或生成标记为 third-party/community 的 sanity benchmark；记录 seed、dt、metric、checksum、source_refs、rights、scope、合理性评估和 residual。 | 现代 AIM-120/R-77/AIM-9X Pk、真实制导性能验证或真实杀伤校准。 |
| `validation_criteria` | NAP/GAO LFT&E、FOI、FAA/NASA consequence、JHU/APL guidance/filter、A2 CI matrix。 | 补 residual closeout 和 acceptance criteria；区分 evidence、benchmark、runtime gate。 | 用 criteria 替代数据或模型验证。 |
| `reproducibility` | source_ref、官方 handle/DOI、checksum 待补、A2 self-generated harness。 | 后续数据包必须附 manifest、version、sha256、生成配置。 | 把临时目录、下载副本或未核权利 PDF 当长期事实。 |

## 推荐下一步

1. 建立首个 `validated_physics_surrogate` 方法包，而不是直接创建 authoritative descriptor。建议 scope 仍保持窄域：`F-16C_Block50` × `AIM-120C-class/blast_fragmentation` × `beam` × `high` × `near_miss_0_35m`。
2. 先选 mechanism-load surrogate：`blast_scaled_distance` + `fragment_areal_density` + `surface_incidence`，只生成非权威 benchmark output 和 validation report。
3. 为该 surrogate 生成 model card、source ledger、validation manifest、residual register；只有验证报告闭合后，才考虑 runtime descriptor 的 `validated_physics_surrogate`。
4. `component_failure_probability` 的第一步应是 schema/method validation，不应直接写真实概率。可用 FOI/open-access 方法构造 synthetic-labeled benchmark，保持 `component_failure_probability_authority=false`。
5. P4 deterministic fuze 继续 deferred。AIM-120 TDD 公开术语只用于 residual 和 fuze evidence surface，不构成 trigger model。

## 拒绝清单摘要

以下来源类型已被收集包共同拒绝或降级。注意：第三方/社区来源并不因“非官方”自动拒绝；只有无 provenance、无权利边界、无法合理解释或疑似敏感/游戏平衡的数据才拒绝，其他可保留为已标记候选或 sanity check。

- JMEM/JWS/J-ACE/AJEM/COVART/FASTGEN/SLATE/Endgame Manager 等受控工具和数据；
- 无 provenance 或明显游戏平衡性质的 CMANO / DCS / War Thunder / 游戏配置 / 民间 missile DB 的 warhead、fuse radius、damage、Pk 单点值；
- 未授权飞行/维修/结构/IPB/技术令镜像；
- 无稳定 source_ref、无作者/版本、无合理性解释的论坛、网盘、截图、社媒部件号/战斗部质量/杀伤半径；
- 受限、FOUO/CUI、ITAR/EAR、不可再分发或来源不明材料；
- 单篇论文示例表格或单个宣传值直接转成 calibrated row。

## 当前验收结论

本轮完成的是“公开来源候选池与准入边界”。它让 A2 后续可以按仓库准则推进数据化工作，但当前仍没有任何新来源满足 runtime authoritative descriptor 的完整条件。现有代码中的 synthetic / engineering scaffold 和 schema fixture 仍必须保持非权威语义。
