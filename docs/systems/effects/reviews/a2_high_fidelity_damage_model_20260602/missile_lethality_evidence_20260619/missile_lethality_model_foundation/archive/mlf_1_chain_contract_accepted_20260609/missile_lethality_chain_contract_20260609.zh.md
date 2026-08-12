# 导弹杀伤链事件和诊断字段合同

状态：`2026-06-09` MLF-1 设计记录 / 未改运行逻辑。

语言：

- 中文主文：`missile_lethality_chain_contract_20260609.zh.md`
- 英文辅文：[missile_lethality_chain_contract_20260609.md](missile_lethality_chain_contract_20260609.md)

输入：

- 子项目入口：[README.zh.md](README.zh.md)
- 字段盘点：[missile_lethality_field_inventory_20260609.zh.md](missile_lethality_field_inventory_20260609.zh.md)
- 合同结构：[../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../../../src/runtime/contracts/engagement_contracts.h)
- 最近交战事件包：[../../../../../src/core/engine/engagement_event_types.h](../../../../../../../../src/core/engine/engagement_event_types.h)
- 事件记录：[../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp](../../../../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp)
- 受控调试入口：[../../../../../src/core/engine/simulation_kernel_damage_debug_api.cpp](../../../../../../../../src/core/engine/simulation_kernel_damage_debug_api.cpp)
- 诊断导出：[../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py](../../../../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py)
- 训练消费：[../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py](../../../../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py)

## 结论

需要标准化。现在的记录已经能把“发射、效果、损伤报告、训练消费”连起来，但字段混在少数大结构里，诊断端只能看到最后一两个事件。继续往里加破片、连续杆、结构断裂和残骸对象之前，必须先把每一步的记录格式固定下来。

也需要抽出一个小的“杀伤链合同”子域，但第一步只抽合同和诊断投影，不抽新的物理仿真循环。引擎仍然负责记录事件，武器模型仍然负责算引信和战斗部作用，损伤系统仍然负责改变目标状态，飞行动力学仍然负责把损伤变成飞行后果。

## 现在已有的东西

| 现有记录 | 现在能说明什么 | 主要问题 |
| --- | --- | --- |
| `LaunchRequest` / `LaunchEvent` | 谁请求发射、是否接受、用了哪个挂点、生成了哪枚弹 | 和后续命中/损伤之间只靠事件查找补链路 |
| `MunitionLifecyclePacket` | 导弹是否活动、导引状态、燃料、引信粗状态 | 不是完整事件流，不能解释“为什么此刻触发或没触发” |
| `EffectsEvent` | 起爆位置、最近距离、引信、战斗部、空间覆盖、部件作用和证据标签 | 一个结构承担太多阶段，最近点、引信判断、战斗部作用、部件载荷不容易分开验收 |
| `ComponentMechanismLoadRow` | 单个部件承受的破片、爆压、切割等载荷 | 没有独立事件身份，难以追溯到具体引信和战斗部样本 |
| `DamageReport` | 目标生命值/能力变化、任务失效、机动失效、动力失效、最终状态 | 仍有 `hp_delta` 和字符串差分，不能完整表达部件前后状态和结构断裂 |
| `DiagnosticsTrace` | 链路 id，发射、效果、损伤报告之间的引用 | 只有引用关系，没有每个阶段的判定原因和证据等级 |
| 诊断 probe | 导出最近一次效果、损伤、奖励项 | 以“最后一次”为主，不能稳定重建一枚弹的全链路 |
| 训练奖励读取 | 读取损伤报告和触地状态 | 是消费端，不应该成为杀伤链事实来源 |

## 标准事件序列

每一枚弹至少应能重建下面这条流水账。某一步没有发生时，也要有“没有发生的原因”，而不是直接缺记录。

| 顺序 | 事件 | 必须回答的问题 | 现状 | MLF-1 处理 |
| --- | --- | --- | --- | --- |
| 1 | 发射事件 | 发射是否成立，弹从哪里来，目标是谁 | 已有 `LaunchEvent` | 保留，补公共字段要求 |
| 2 | 飞行/导引快照 | 导弹是否仍在飞，导引是否有效 | 有 `MunitionLifecyclePacket` | 作为低频状态，不替代后续事件 |
| 3 | 最近接近事件 | 导弹从什么方位接近，最近点在哪里，错过多远 | 部分塞在 `EffectsEvent` | 需要独立字段组，未起爆也要可报告 |
| 4 | 引信评估事件 | 是否解保，是否触发，为什么触发或失败 | 字段较粗 | 需要显式 `triggered/failure_reason/delay/reliability/sample` |
| 5 | 战斗部作用事件 | 起爆后产生爆压、破片、切割还是混合作用 | 部分已有 | 需要机制列表和证据等级 |
| 6 | 空间覆盖事件 | 这些作用扫过了哪些空间，方向和密度如何变化 | 部分已有 | 需要和目标部件暴露分开 |
| 7 | 部件载荷事件 | 哪些部件被打到，承受多强载荷 | 已有 row 雏形 | row 需要链路、机制和部件身份稳定化 |
| 8 | 部件损伤事件 | 部件从什么状态变成什么状态，失效模式是什么 | 部分散落 | 需要结构化前后状态，不只写总量变化 |
| 9 | 平台后果事件 | 控制、动力、传感、燃油、火灾、乘员状态如何变化 | 有部分状态 | 要作为损伤系统输出，而不是训练端临时推断 |
| 10 | 结构失效事件 | 是否断翼、断尾、机身断裂、发动机脱落或空中解体 | 基本缺失 | MLF-6 前先预留字段 |
| 11 | 生命周期事件 | 目标是否仍是可飞整机、迫降体、坠毁残骸、碎片 | 触地状态已有一部分 | 需要统一残骸/碎片/训练终局表达 |
| 12 | 训练投影事件 | 奖励和终局如何读取上述事实 | 已有消费逻辑 | 只能消费，不拥有事实 |

## 公共字段

所有杀伤链事件都应有同一套公共头，便于诊断工具按一枚弹重放。

| 字段 | 含义 | 说明 |
| --- | --- | --- |
| `schema_version` | 字段版本 | 诊断 CSV 和 Python binding 变动时必须递增，并说明迁移方式 |
| `chain_id` | 一枚弹的一条链路 | 优先来自发射事件；无发射事件时由效果事件生成 |
| `event_id` | 当前事件 id | 只在本事件类型内也必须唯一 |
| `parent_event_id` | 上游事件 | 例如部件载荷指向战斗部作用或空间覆盖 |
| `stage` | 所属阶段 | `launch`、`nearest_approach`、`fuze`、`warhead`、`component_load` 等 |
| `status` | 阶段结果 | `pass`、`no_trigger`、`miss`、`failed`、`not_evaluated` 等 |
| `reason` | 人可读原因 | 例如 `outside_trigger_radius`、`direct_contact`、`target_in_pattern` |
| `source_time_s` | 仿真时间 | 必须能排序 |
| `source_frame` | 帧号 | 用来排查同一时刻多个事件 |
| `munition` | 弹体实体 | 允许弹体销毁后仍能追溯 |
| `shooter` | 发射方实体 | 没有时填空引用 |
| `target` | 目标实体 | 目标失活后仍保留原 id |
| `producer_node_id` | 产生该事件的节点 | 便于定位是哪个系统写入 |
| `fidelity_mode` | 低/中/高细节模式 | 不能让低细节统计层覆盖高细节损伤事实 |
| `evidence_level` | 证据等级 | `official_public`、`public`、`cmo_db_proxy`、`engineering_assumption`、`training_synthetic`、`uncalibrated` |
| `confidence` | 诊断置信度 | 表示本阶段记录是否完整，不代表真实命中概率 |

## 资料源标注

杀伤链允许使用 CMO-DB 作为代理数据源。CMO-DB 当前页面说明它是 Command:
Modern Operations DB3000 的非官方数据查看器；因此它可以提供工程参数，但不能被写成官方实测权威。

凡是来自 CMO-DB 的字段，后续数据表或事件投影必须能追溯：

| 标注项 | 含义 |
| --- | --- |
| `evidence_level=cmo_db_proxy` | 表示该数值来自 CMO-DB 代理资料 |
| `source_kind` | `cmo_db` |
| `source_version` | 例如 CMO Database v517 |
| `source_url` | CMO-DB 条目或搜索结果 URL |
| `source_entry_name` | CMO-DB 条目名 |
| `source_field_name` | 原始字段名 |
| `source_unit` | 原始单位 |
| `accessed_on` | 读取日期 |
| `mapping_rule` | 如何从 CMO-DB 字段转成本项目字段 |
| `manual_adjustment_note` | 如有人工修正，说明理由 |

这类字段可以直接用于默认参数和代理校准起点。禁止的是无标注使用，或把它描述成真实 Pk、真实引信阈值、真实战斗部破片分布等无需校准的真值。

## 诊断字段分组

诊断表不要只输出“最后是否击落”。最小字段应能回答七个普通问题。

| 问题 | 字段组 | 例子 |
| --- | --- | --- |
| 这是哪一发？ | 链路身份 | `chain_id`、`launch_event_id`、`munition_id`、`target_id` |
| 它从哪来，离多近？ | 接近几何 | `miss_distance_m`、`nearest_approach_time_s`、`local_forward/right/up_m`、`closure_mps`、`aspect_bucket` |
| 引信为什么动了或没动？ | 引信判定 | `fuze_type`、`fuze_armed`、`fuze_triggered`、`fuze_failure_reason`、`fuze_delay_s`、`fuze_reliability` |
| 起爆后产生了什么？ | 战斗部作用 | `mechanism_family`、`fragment_energy_j`、`fragment_density_per_m2`、`blast_overpressure_kpa`、`rod_cut_margin` |
| 打到了哪里？ | 部件载荷 | `component_name`、`component_system`、`direct_hit`、`distance_m`、`penetration_margin`、`incidence_cos` |
| 目标发生了什么变化？ | 部件/平台后果 | `integrity_before/after`、`failure_mode`、`control_delta`、`engine_delta`、`fuel_leak_delta`、`fire_state` |
| 后面世界里留下什么？ | 生命周期 | `loss_state`、`ground_lifecycle`、`breakup_state`、`wreck_entity_id`、`debris_count` |

## 应补的合同对象

MLF-1 不要求一次把所有对象都实现，但字段合同要先决定命名和归属。

| 合同对象 | 用途 | 推荐落点 |
| --- | --- | --- |
| `LethalityChainHeader` | 上述公共头 | 新合同头文件，供所有事件复用 |
| `NearestApproachEvent` | 记录最近点和方位，即使没有起爆 | MLF-2 前置 |
| `FuzeEvaluationEvent` | 记录解保、触发、失败和延迟 | MLF-2 前置 |
| `WarheadMechanismEvent` | 记录爆压、破片、切割等机制样本 | MLF-3/4 前置 |
| `SpatialCoverageEvent` | 记录方向图、采样数、覆盖强度 | MLF-3 前置 |
| `ComponentLoadEvent` | 稳定化现有 `ComponentMechanismLoadRow` | MLF-3/5 共用 |
| `ComponentDamageEvent` | 记录部件前后状态和失效模式 | MLF-5 前置 |
| `PlatformConsequenceEvent` | 记录损伤系统输出到控制/动力/传感/燃油/火灾 | MLF-7 前置 |
| `StructuralBreakupEvent` | 记录断裂、脱落、空中解体 | MLF-6 前置 |
| `LifecycleTransitionEvent` | 记录整机、迫降体、坠毁残骸、碎片之间的转换 | MLF-8 前置 |
| `TrainingProjectionEvent` | 记录训练如何消费事实 | 只做投影，不做事实来源 |

## 模块边界

建议抽出子域，但要克制地抽。

| 层 | 建议 | 不应做的事 |
| --- | --- | --- |
| 合同层 | 新增 `src/runtime/contracts/lethality_chain_contracts.h`，或先在 `engagement_contracts.h` 中分块后迁移 | 不把物理计算写进合同结构 |
| 事件记录层 | 保留在 `src/core/engine/*event_store*`，只负责收集、排序、关联和导出 | 不在 event store 里判断飞机能不能继续飞 |
| 武器模型层 | 后续放在 `src/models/weapons/lethality/` 一类位置，负责几何、引信、战斗部、空间覆盖 | 不让训练奖励反推命中效果 |
| 损伤层 | `src/systems/combat/*damage*` 继续负责把部件损伤变成平台状态变化 | 不用单个 kill 或 HP 代替部件后果 |
| 飞行/物理层 | 现有空气动力学、推进、控制、触地系统继续消费损伤后果 | 不新增独立的“是否还能飞”判死规则 |
| 诊断投影层 | 可加一个小的导出/扁平化 helper，让 probe、reward、测试用同一套字段名 | 不让每个 Python 脚本各自猜字段含义 |

短期推荐路径：

1. 先定义合同和字段名，不改模型行为。
2. 再把 `EffectsEvent` 中混杂的字段迁移为阶段字段，旧字段只作为来源清单，不作为长期导出别名。
3. 等受控 probe 能重建完整链路后，再拆 C++ 结构或移动文件。

## 不建议的路径

- 不建议继续把所有新增内容塞进 `EffectsEvent`。它已经同时承载接近几何、引信、战斗部、空间覆盖、部件和证据，后面会更难定位问题。
- 不建议把 Pk 放到链路中间当裁判。Pk 可以做低细节模式或总体趋势检查，但不能替代“哪里起爆、打到哪里、什么部件坏了”。
- 不建议由训练奖励决定目标是否被击毁。训练奖励只能读取事件和状态，不能制造事实。
- 不建议用“目标触地后删除”解决残骸问题。应先有生命周期事件，再决定观测和训练怎么处理。

## 第一批验收门槛

MLF-1 可以验收的最低条件：

- 单枚弹能从发射事件追到最近接近、引信、效果、部件载荷、损伤报告和后续状态。
- 未起爆、起爆未造成伤害、造成非终局损伤、造成迫降/坠毁、造成空中解体这几类分支都有可记录的位置。
- 诊断输出中不再只依赖 `last_effect_*` 和 `last_damage_*` 表示全链路。
- 所有新增数值都有证据等级；CMO-DB 数值使用 `cmo_db_proxy` 等标注，不能暗示官方实测/保密级 AIM-120C/MQ-9 权威。
- 旧字段必须列入删除或迁移清单，训练和诊断消费端要切到标准字段；不保留双轨长期兼容面。

## 下一轮可分发任务

| 任务 | 目标 | 写入范围 | 验收 |
| --- | --- | --- | --- |
| `MLF-1A Field Inventory` | 逐字段盘点现有合同、binding、probe、reward 消费 | 文档 | 已通过：[missile_lethality_field_inventory_20260609.zh.md](missile_lethality_field_inventory_20260609.zh.md) |
| `MLF-1B Header And Event Shape` | 设计公共头和新增事件 DTO | 合同文档或 C++ 合同草案 | 每个事件能说明上游、状态、原因和证据等级 |
| `MLF-1C Diagnostic Projection` | 统一 Python 扁平化字段名 | diagnostics helper/probe | 同一枚弹可导出多阶段行，不只看最后一条 |
| `MLF-1D Consumer Migration` | 迁移训练和诊断消费端，移除旧字段依赖 | reward/probe/tests | 消费端只依赖标准字段，旧字段有删除清单 |
| `MLF-1E Module Boundary Review` | 决定是否正式拆 `lethality_chain_contracts.h` | docs + 轻量代码移动计划 | event store、模型、损伤、飞行、训练职责不混在一起 |

## 当前判断

应该先建“杀伤链合同”这个小子域。它不是新仿真器，也不是新杀伤规则，而是一套稳定账本。没有这套账本，后续即使加了破片或连续杆，也很难说清楚目标是被什么打坏、坏在哪里、为什么后来还能飞或者为什么解体。
