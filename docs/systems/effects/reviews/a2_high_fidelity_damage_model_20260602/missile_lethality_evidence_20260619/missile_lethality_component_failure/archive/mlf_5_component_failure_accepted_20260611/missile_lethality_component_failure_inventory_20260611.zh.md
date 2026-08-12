# A2 MLF-5A-X1 部件失效边界与盘点

状态：`2026-06-11` pass / inventory packet。本文是 MLF-5 的中文主文；英文辅文：[missile_lethality_component_failure_inventory_20260611.md](missile_lethality_component_failure_inventory_20260611.md)。

本轮只读审计了指定源码、测试和 MLF-3/MLF-4 归档证据，只产出文档 packet，未修改 runtime、测试、README、current status、dispatch queue 或 task clusters。结论是：MLF-5 已有很强的候选实现面，但 accepted 事实面尚未闭合。`ComponentDamageEvent` 只是合同脚手架；丰富的概率、证据、失效模式、完整度和冗余组数据目前主要折叠在 `EffectsResult` / `EffectsEvent` / `ComponentMechanismLoadRow` 与 `ComponentDamageState` 中，诊断探针尚未输出标准的部件失效阶段。

## 审计范围

- `src/runtime/contracts/engagement_contracts.h`
- `src/core/interfaces/effects_model.h`
- `src/models/weapons/detail/default_effects_system_effect_detail.inc`
- `src/models/weapons/detail/default_effects_state_detail.inc`
- `src/models/weapons/detail/default_effects_spatial_projection_detail.inc`
- `src/systems/combat/damage_system_air.h`
- `src/components/domains/air/combat/damage_air.h`
- `tools/diagnostics/air_combat_stage0_process_probe.py`：当前工作区显示为 deleted；本轮只读审计 HEAD 版本，未恢复、未修改。
- `tests/runtime/air_combat/weapon_guidance_realism/component_damage.py`
- `tests/runtime/air_combat/weapon_guidance_realism/vulnerability_authority.py`
- `tests/runtime/air_combat/weapon_guidance_realism/vulnerability_scaffold.py`
- MLF-3/MLF-4 archived README/acceptance。

补充只读依赖：为准确描述 `ComponentDamageState` 和候选实现，本轮还读取了 `src/components/combat/common/damage_common.h`、`src/models/weapons/detail/default_effects_component_damage_detail.inc` 和 `src/models/weapons/detail/default_effects_result_detail.inc`。这些文件未被修改；它们是上面审计入口直接包含或调用的实现依赖。

## 边界结论

MLF-5A 可以登记为 pass，但不能把当前 runtime 直接声明为 MLF-5 accepted。原因如下：

- MLF-3 已验收的是起爆后的战斗部机制载荷、空间覆盖和部件受载事实；它明确不证明部件失效。
- MLF-4 已验收的是连续杆/切割曝光事实；它明确不证明部件失效概率。
- MLF-5 需要把这些上游事实转换为部件失效概率、样本、失效模式、完整度前后值、冗余组状态和 handoff 事实。
- 现有候选实现已经能计算并导出很多 MLF-5 所需字段，但标准 `ComponentDamageEvent` writer、诊断行和 focused acceptance tests 尚未闭合。
- 概率为正不等于抽样失效已发生；`failure_sample <= failure_probability` 才触发候选失效模式/impulse 路径。现有 `apply_component_damage_state` 会按概率和载荷积累部件完整度下降，因此 MLF-5 后续必须区分“损伤累积状态变化”和“抽样失效模式触发”。

## 字段盘点

| 面 | 已有字段 | 可复用性 | MLF-5 缺口 |
| --- | --- | --- | --- |
| `ComponentDamageEvent` | `component_name`、`component_system`、`component_redundancy_group_id`、`integrity_before`、`integrity_after`、`failure_mode`、`failure_severity`、`failure_probability`、`failure_sample` | 可作为 5B 标准事件骨架 | 无 probability source/evidence、无多失效模式列表、无 group availability/count、无机制载荷上下文、无 live writer/probe 验收 |
| `ComponentLoadEvent` | 部件名/系统/冗余组、direct hit、距离、effect scale、fragment/blast/rod/surface incidence、`load_source` | MLF-3/MLF-4 accepted 输入事实，可作为 MLF-5 的上游 gate | 不包含失效概率、样本、失效模式或完整度变化 |
| `ComponentMechanismLoadRow` | 部件身份、机制载荷、dependency、`component_failure_probability`、source、calibrated、dataset/row/source/provenance、sample、authority、component-specific、weapon/aspect/closure/miss buckets、failure mode list、primary mode/severity | 当前最丰富的候选实现面，5B/5C 可复用字段和 selector 逻辑 | 不是标准事件；mode authority 固定 false；before/after integrity 不完整；依赖 `EffectsEvent` 聚合导出 |
| `EffectsResult` / `EffectsEvent` | aggregate probability/source/evidence/sample/count、primary component、primary integrity、primary mechanism load、redundancy availability/member/failed count、vulnerability metadata | 可复用作 event writer 输入和历史测试 anchor | 聚合面偏向 primary/max probability，不能替代每个部件的标准 damage event |
| `ComponentDamageState` | `component_integrity`、`component_redundancy_group`、`component_system`、`component_redundancy_weight`、`component_failure_mode_severity`、`component_primary_failure_mode`、`redundancy_group_availability`、member/failed count、pending dependency effects | 5D handoff 的核心状态容器 | 当前没有标准事件 capture before/after；状态变化与抽样失效模式触发需要分层诊断 |
| `AircraftDamageState` handoff | flight/control/hydraulic/propulsion/fuel/avionics/crew/fire/smoke/overstress 等状态 | 可消费 `ComponentDamageState` 并让已有系统传播后果 | MLF-5 不应在此层声明高层结论；只登记 handoff 是否发生 |

## 概率、来源、证据和样本

现有候选概率路径是可复用但未验收的实现：

- 默认源是 `synthetic_sigmoid`，由 severity、mechanism scale、component scale、direct hit、机制载荷、系统脆弱性、依赖复杂度和既有完整度/冗余状态共同决定。
- 有有效 `AircraftVulnerabilityProfile` 且 selector 命中 `component_failure_probability_authority` 的 evidence row 时，概率源可切到 `vulnerability_evidence_row`。
- evidence row 可用 `weapon_family`、`aspect_bucket`、`closure_bucket`、`miss_distance_bucket`、`component_name`、`component_system`、`component_redundancy_group_id` 和机制载荷 bucket 选择。
- 机制载荷 gate 已覆盖 fragment energy、fragment areal density、penetration margin、blast overpressure、blast impulse、blast scaled distance、rod cut margin 和 surface incidence。
- `component_failure_sample` 来自组件 RNG；候选逻辑以 `failure_sample <= failure_probability` 作为失效模式/impulse 触发条件。
- `component_failure_probability_authority == true` 只应表示该行概率来自已授权 evidence row，不应扩展为 Pk、真实弹种校准或高层杀伤结论。

MLF-5C 可以复用 `synthetic_sigmoid` 作为通用、未校准、可替换的 baseline，但需要把 source category、scope、unit、uncertainty/replacement rule 写入文档和诊断面；否则它只能继续作为候选实现。

## 失效模式盘点

已有候选失效模式：

- `puncture`
- `cut`
- `blast_deformation`
- `fuel_leak`
- `hydraulic_pressure_loss`
- `electrical_loss`
- `data_loss`
- `fire_source`
- `structural_weakening`

模式来源有两类：部件显式 `failure_mode_weights` 或 `synthetic_inferred_part_failure_modes`。当前 `component_failure_mode_authority` 为 false，因此这些模式适合作为通用工程候选和测试 fixture，不应直接提升为 authoritative MLF-5 accepted 结论。若 5C/5D 继续使用这些模式，需要把“显式权重”和“合成推断”分别标注，并在诊断中保留 mode list、mode severity、primary mode 和 primary severity。

## 完整度和冗余组

可复用字段：

- 部件身份：`component_name`、`component_system`、`component_redundancy_group_id`。
- 当前导出：`component_primary_integrity`、`component_redundancy_group_availability`、`component_redundancy_group_member_count`、`component_redundancy_group_failed_count`。
- 状态容器：`ComponentDamageState.component_integrity`、`component_redundancy_group`、`component_redundancy_weight`、`redundancy_group_availability`。

缺口：

- `ComponentDamageEvent` 有 `integrity_before` / `integrity_after` 字段，但当前候选路径没有 accepted writer 在更新前后捕获它们。
- `EffectsEvent` 主要导出 primary component 的 after-like integrity 和 group availability，不能代表每个受载部件的 before/after。
- 冗余组会降低候选概率并通过 group availability 影响 aircraft state；5D 需要明确每个事件记录的是单部件完整度、组可用性，还是两者都记录。

## 状态 handoff

现有 handoff 路径可复用：

- `apply_component_damage_state` 将部件完整度和 redundancy group availability 写入 `ComponentDamageState`，并同步 `SystemHealth`。
- `apply_part_failure_mode_state` 在抽样触发后写入 `component_failure_mode_severity` 和 `component_primary_failure_mode`，并可对 aircraft/platform damage 施加候选 impulse。
- `derive_aircraft_damage_from_component_state` 将部件/冗余组可用性压低 flight control、roll/pitch/yaw、hydraulic、propulsion、fuel、avionics、command/navigation、fire suppression、crew 等 aircraft 状态。
- `register_aircraft_damage_system` 继续让既有飞行动力学、推进、传感器、燃油泄漏、火/烟热级联消费 `AircraftDamageState`。

5D 的边界应是“部件状态变化已交给已有损伤/飞行系统”，不是“MLF-5 自己判断飞行结果”。任何高层后果都必须留给后续阶段或已有维护系统，不作为本 packet 的验收声明。

## 诊断缺口

HEAD 版 `tools/diagnostics/air_combat_stage0_process_probe.py` 的 `LETHALITY_CHAIN_STAGES` 包含 `nearest_approach`、`fuze`、`warhead_mechanism`、`spatial_coverage`、`component_load`、`platform_consequence`、`lifecycle`，但没有 `component_damage` / `component_failure` 阶段。行字段也没有 failure probability/source/evidence/sample、failure mode、integrity before/after 或 redundancy group availability。快照只保留 component-load 层的 component name/system/load source/rod cut margin 等字段。

因此 5E 需要新增或等价投影：

- `stage = component_damage` 或 `stage = component_failure`。
- 字段至少包括 component identity、load source/event id、failure probability、probability source、calibrated、evidence dataset/row/source/provenance、failure sample、sampled failure bool、failure mode list、primary mode/severity、integrity before/after、redundancy group availability/member/failed count。
- no-detonation 与 no-load 必须不生成虚假部件失效行。
- no-positive-rod-cut 必须不生成 continuous-rod cut-sourced failure；但若存在 blast/fragmentation 正载荷，不能把“无正切割”误用成所有机制的全局 block。
- 诊断输出不得把 component failure row 提升为结构解体、坠毁、残骸、Pk、训练胜负或实体删除结论。

## 历史测试可复用性

可复用：

- `component_damage.py` 的 primary component、component threshold、failure probability trend、sample range、failure mode list、redundancy availability、ComponentDamageState -> AircraftDamageState handoff 等断言。
- `vulnerability_authority.py` 的 row authority、provenance metadata、component-specific override、mechanism-load bucket、rod cut / fragment density / surface incidence gate 断言。
- `vulnerability_scaffold.py` 的 non-authoritative scaffold 保持 `synthetic_sigmoid`、runtime-aligned descriptor 可驱动 component probability 且不授予 Pk/fuze authority 的断言。
- MLF-4 diagnostic tests 对 non-rod zero cut 和 no-detonation no rod rows 的 gate 语义可作为 5E 的上游约束。

不能直接提升为 MLF-5 accepted：

- 多数测试仍在 `weapon_guidance_realism` 历史套件，命名为 Phase 3 / Phase 5 / A8，不是当前 MLF-5 子项目的 focused acceptance。
- 多数 evidence row 是 `unit-test` / `fixture://`，证明 selector 和 gate mechanics，不证明真实数据权威。
- 测试主要读取 `EffectsEvent` aggregate 或 `component_mechanism_load_rows`，不是标准 `ComponentDamageEvent` live writer/probe。
- 现有测试没有完整覆盖 no-detonation、no-load、no-positive-rod-cut 与 component failure 诊断行之间的组合 gate。

## 后续建议和风险

### MLF-5B Component Damage Event Surface

建议：

- 以现有 `ComponentDamageEvent` 为骨架，明确同链路 parent：最好从 `ComponentLoadEvent` 或其同链路 effects/trace 派生。
- 决定是扩展 `ComponentDamageEvent`，还是保留瘦事件并用 diagnostics row 补齐 source/evidence/load context。若要 accepted，推荐标准事件直接携带 probability source/evidence 与 redundancy group availability。
- 一次部件受载如果命中多个 component，应能输出多行或多事件；不要只记录 primary component。

风险：

- 扩展标准事件会触及 contracts、event store、bindings 和 tests；需要串行推进。
- 只复用 `EffectsEvent` aggregate 会丢失 per-component before/after 和多部件证据。
- 若 writer 在状态更新后才采样，`integrity_before` 会丢失。

### MLF-5C Generic Vulnerability Probability

建议：

- 复用现有 `synthetic_sigmoid` 作为通用未校准 baseline，并显式标注 synthetic / uncalibrated / replaceable。
- 保持 evidence row authority gate：只有 calibrated descriptor、authoritative source kind、row metadata 和 `component_failure_probability_authority` 同时满足时，才使用 `vulnerability_evidence_row`。
- 聚焦测试应覆盖 rod cut margin、fragment areal density、blast scaled distance、surface incidence、component-specific row、redundancy、pre-damage state。

风险：

- 当前默认公式包含工程常量，但缺少完整 runtime metadata；不能写成真实型号参数。
- component failure probability 与 effect-scale authority 需要继续分离，避免误把 vulnerability scale 当作概率权威。

### MLF-5D Component State Handoff

建议：

- 在状态更新前后捕获 `integrity_before` / `integrity_after`，并记录 group availability before/after。
- 明确两个层次：概率驱动的完整度累积，以及样本触发的失效模式/impulse。
- 用 focused tests 验证 `ComponentDamageState`、`AircraftDamageState`、`SystemHealth` 的 handoff；断言应停在状态变化，不引入高层结论。

风险：

- 当前路径对 component integrity 的积累不完全等同于 sampled failure；若文档和诊断不分层，后续会把概率、损伤和失效混为一谈。
- AircraftDamageState 的既有系统会继续传播后果；MLF-5 文档不能把下游传播写成 MLF-5 自己的结论。

### MLF-5E Diagnostics And Gates

建议：

- 在当前有效诊断入口新增 component damage/failure 行；若 `air_combat_stage0_process_probe.py` 已被替换，应在 successor probe 中实现，而不是恢复已删除文件。
- bump 或明确诊断 schema，加入 probability/evidence/sample/mode/integrity/redundancy 字段。
- 增加 focused gate tests：no detonation、no load、no positive rod cut、non-authoritative scaffold、authorized evidence row、component-specific row。

风险：

- 如果只在 snapshot 汇总 primary component，会再次丢失 per-component 解释。
- 如果 no-positive-rod-cut gate 写成全局 no-failure gate，会错误屏蔽 blast/fragmentation 正载荷路径。
- 如果把 platform/lifecycle 字段混入 component failure 行，容易产生越界解释。

## Worker Packet

status: pass

touched files:

- `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/missile_lethality_component_failure_inventory_20260611.zh.md`
- `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/missile_lethality_component_failure_inventory_20260611.md`

commands/outcomes:

- `git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure`：worker 返回与主线程验收均通过，无输出。
- `rg -n "[[:blank:]]$" docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure`：主线程验收无匹配。

remaining paths:

- 5B：标准 `ComponentDamageEvent` writer / bindings / export / focused tests。
- 5C：通用概率 baseline 与 evidence authority gate 的 focused tests。
- 5D：before/after integrity、redundancy group before/after、state handoff tests。
- 5E：component damage/failure 诊断阶段与 no-detonation/no-load/no-positive-rod-cut gates。

behavior risks:

- 现有候选实现已经改变 component integrity，但 accepted event/probe 没有捕获 before/after。
- 现有 `EffectsEvent` 是聚合面，不能替代 per-component damage fact。
- 历史 tests 证明机制存在，不证明当前 MLF-5 子项目 accepted。

integration notes:

- 未改变标准事件字段。
- 未新增默认常量。
- 未起爆和无载荷路径应保持无虚假部件失效；无正切割路径应只阻止 cut-sourced continuous-rod failure，不应误伤其他正载荷机制。
- 已避免声明结构解体、坠毁、残骸、Pk、训练胜负、实体删除或真实 AIM-120C/MQ-9 杀伤结论。
