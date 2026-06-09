# A2 通用导弹杀伤模型基础

状态：`2026-06-09` MLF-1A-D 已验收；MLF-1E 模块边界验收待展开；几何、引信、破片、连续杆和结构解体模型尚未实现。

语言：

- 英文辅文：[README.md](README.md)
- 中文主文：`README.zh.md`

输入：

- A2 指针：[../README.zh.md](../README.zh.md)
- A2 封存包：[../../archive/a2_high_fidelity_damage_model/README.zh.md](../../archive/a2_high_fidelity_damage_model/README.zh.md)
- A8 损伤效果链：[../../a8_damage_effect_chain/README.zh.md](../../a8_damage_effect_chain/README.zh.md)
- A2 损伤后果奖励面：[../damage_consequence_reward_surface/README.zh.md](../damage_consequence_reward_surface/README.zh.md)
- 当前效果模型入口：[../../../../../src/models/weapons/default_effects_model.cpp](../../../../../src/models/weapons/default_effects_model.cpp)
- 损伤组件定义：[../../../../../src/components/combat/damage.h](../../../../../src/components/combat/damage.h)
- 武器和导弹组件：[../../../../../src/components/combat/weapon.h](../../../../../src/components/combat/weapon.h)
- MLF-1 合同：[missile_lethality_chain_contract_20260609.zh.md](missile_lethality_chain_contract_20260609.zh.md)
- MLF-1A 字段盘点：[missile_lethality_field_inventory_20260609.zh.md](missile_lethality_field_inventory_20260609.zh.md)
- 任务簇计划：[missile_lethality_model_foundation_task_clusters_20260609.zh.md](missile_lethality_model_foundation_task_clusters_20260609.zh.md)
- CMO-DB 代理资料源：<https://www.cmo-db.com/en/>

## 目的

把导弹杀伤从“近炸触发后给一个粗略损伤结果”推进到可分层、可替换、可验收的通用杀伤模型。

本子项目不是 AIM-120C / MQ-9 的专项调参。它先建设通用模型骨架：命中几何、引信、战斗部作用、空间覆盖、目标部件、部件脆弱性、结构失效、二次后果、飞行动力学对接、残骸对象和统计校验。只有这些层次站稳之后，才回头做具体弹种/目标组合。

## 为什么现在先做基础模型

当前已有工作能证明几件事：

- 导弹发射、起爆、效果事件和损伤报告可以连起来。
- 部件损伤可以传到一部分飞机内部状态。
- 损伤后果可以被训练奖励读取。
- 延迟坠地可以作为训练终局识别。

但这些还不等于高保真导弹杀伤。当前仍然缺少：

- 通用 Pk 或统计校验层。
- 更完整的引信模型。
- 通用破片和连续杆/切割类战斗部模型。
- 结构断裂、空中解体和碎片/残骸对象。
- 清晰的证据分级和校准流程。

因此继续讨论“一发 AIM-120C 打 MQ-9 应该是漏油慢坠还是直接碎裂”，会过早进入个案调参。正确顺序是先把通用杀伤链标准化。

## 边界

纳入：

- 定义导弹杀伤链每一层的模型职责、输入、输出和验收顺序。
- 指定当前 runtime 中可以逐步接入的代码位置。
- 规划通用预制模型，不依赖某个具体真实弹种的保密参数。
- 要求所有模型保留证据等级：官方/手册公开资料、公开资料、CMO-DB 代理资料、工程假设、训练用合成、未校准。
- 要求高保真链路优先产生具体损伤和后果，再由训练端消费，而不是直接给 kill。

不纳入：

- 不把 CMO-DB、公开网页、论坛或训练结果冒充为官方实测/保密级权威。
- 不声明真实 Pk、真实引信阈值、真实战斗部质量或真实破片分布。
- 不用“直接坠毁/直接删除”规则代替杀伤链。
- 不把 Pk 当成高保真损伤链的替代品。
- 不在基础模型完成前继续调具体 AIM-120C/MQ-9 碎裂效果。

## 代理资料源

CMO-DB 可以作为当前公开条件下的高价值代理资料源使用。它提供 Command:
Modern Operations DB3000 的可搜索装备数据，适合补齐公开世界很难取得的武器、平台、传感器和挂载关系等细节。

使用 CMO-DB 时采用以下规则：

- 允许直接用于默认参数、量级约束、类别映射和相对差异：例如平台尺寸/速度/高度、武器射程量级、导引/引信类别、战斗部类别、传感器类别、挂载关系。
- 允许用于具体弹种/目标组合的代理校准起点，但必须标注 `evidence_level=cmo_db_proxy` 或等价证据等级。
- 每条映射必须记录 CMO-DB 版本、条目名或 URL、字段名、单位、读取日期、映射规则和人工修正说明。
- 如果公开手册、厂商资料或官方游戏数据库说明与 CMO-DB 冲突，保留冲突记录并提高人工复核优先级。
- 不把 CMO-DB 数值说成真实实测值、保密参数或官方杀伤概率。它可以是工程上可用的代理参数，不是无需标注的真值。

因此，“不能直接补”的正确表述应改为：可以补，而且在很多情况下应该补；限制只在于必须带来源、版本、证据等级和映射说明，不能无标注地进入高保真链路。

## 模型清单

| 顺序 | 模型 | 要解决的问题 | 主要输出 | 当前判断 |
| --- | --- | --- | --- | --- |
| 0 | 证据和权限模型 | 哪些数值是公开支持，哪些只是工程假设 | evidence/authority 标记 | 必须先固定 |
| 1 | 杀伤链标准合同 | 发射、最近点、起爆、作用、损伤、后果如何串起来 | 统一事件和诊断字段 | 必须先固定 |
| 2 | 命中几何模型 | 导弹从哪里来、最近点在哪里、相对速度和方位如何 | miss distance、方位、局部坐标、闭合速度 | 当前已有雏形，需标准化 |
| 3 | 引信模型 | 何时起爆、是否过早/过晚、是否触发失败 | 起爆状态、延迟、可靠性、触发原因 | 当前过粗 |
| 4 | 战斗部作用模型 | 起爆后产生什么杀伤机制 | blast、fragment、continuous-rod/cutting 等机制载荷 | 缺通用预制模型 |
| 5 | 空间覆盖模型 | 破片/杆件扫过哪些部位，密度和能量如何随方向衰减 | 部件暴露度、命中样本、作用强度 | 当前不够表达方向性 |
| 6 | 目标几何和部件模型 | 机翼、尾翼、机身、发动机、油箱、传感器在哪里 | hitbox/component map | 已有部分，需要统一质量门 |
| 7 | 部件脆弱性模型 | 部件被击中后发生什么 | 失效模式、失效概率/严重度 | 有雏形，需证据分级 |
| 8 | 结构失效模型 | 断翼、断尾、机身断裂、发动机脱落、空中解体如何出现 | structural break、breakup、detached parts | 当前主要缺口 |
| 9 | 二次后果模型 | 火灾、漏油、液压/电力/控制下降如何延迟发展 | fire/leak/control/engine 后果 | 有雏形，需统一链路 |
| 10 | 飞行动力学对接 | 损伤如何改变升力、阻力、推力、控制效率、质量和重心 | aero/propulsion/control modifiers | 不能另写“能否飞”规则 |
| 11 | 残骸和碎片对象模型 | 目标解体后世界里留下什么 | wreck/debris entities、生命周期 | 当前只到坠毁残骸识别 |
| 12 | Pk/统计层 | 低细节仿真和总体趋势如何校验 | statistical kill probability、confidence | 只能作为低保真或校验层 |
| 13 | 诊断和回放模型 | 如何证明链路按预期运行 | replay/probe/report 表 | 每阶段都需要 |

## 展开顺序

| 阶段 | 目标 | 入口条件 | 退出条件 | 允许动代码 |
| --- | --- | --- | --- | --- |
| `MLF-0 Boundary` | 固定证据等级、禁止声明、模型顺序 | 本文存在 | 父级 A2 README 指向本文 | 文档 |
| `MLF-1 Chain Contract` | 标准化杀伤链事件和诊断字段 | MLF-0 | 有 launch/nearest-approach/fuze/effect/damage/consequence/breakup 字段表 | contracts/tests |
| `MLF-2 Geometry And Fuze` | 把命中几何和引信从粗规则拆开 | MLF-1 | 受控接近方位、距离、速度能产生可解释起爆状态 | weapon runtime/tests |
| `MLF-3 Generic Fragmentation` | 建一个通用、未校准破片模型 | MLF-2 | 距离和方位改变会改变命中部件和强度 | effects model/tests |
| `MLF-4 Continuous-Rod / Cutting` | 建一个通用切割类机制 | MLF-3 | 可以表达扫过翼面/尾梁/机身时的线性切割结果 | effects model/tests |
| `MLF-5 Target Vulnerability` | 统一目标部件和脆弱性表 | MLF-3 | 部件失效模式、证据等级和默认值可机读 | content/tests |
| `MLF-6 Structural Failure` | 支持结构断裂、空中解体和主要部件脱落 | MLF-5 | 高烈度命中可产生完整机体以外的结果 | damage/physics/tests |
| `MLF-7 Secondary Consequence Coupling` | 统一火灾、漏油、动力、控制和飞行动力学传递 | MLF-6 | 损伤通过现有动力学自然影响飞行 | damage/air/physics/tests |
| `MLF-8 Debris And Wreck Lifecycle` | 把解体/坠毁后的对象留在世界中 | MLF-6 | 残骸、碎片、失效目标在观测和训练中语义清晰 | runtime/tests |
| `MLF-9 Statistical Layer` | 增加 Pk/统计校验层 | MLF-3 起码完成 | Pk 只作为低细节模式或趋势校验，不覆盖高保真链路 | optional runtime/tests |
| `MLF-10 Calibration Gates` | 回到具体弹种/目标组合 | MLF-1 至 MLF-8 至少有 accepted slice | 可以讨论 AIM-120C/MQ-9，但所有数值带证据等级 | docs/tests/probes |

## 推荐第一批任务

第一批不要直接写破片公式。先做三个小任务：

1. `MLF-1A Event Field Map`：列出现有事件字段和缺失字段，形成杀伤链字段表。
2. `MLF-1B Fidelity Mode Boundary`：定义 low/medium/high 三档仿真模式，以及每档允许用哪些模型。
3. `MLF-2A Controlled Geometry Probe`：构造固定距离、方位、速度、目标姿态的受控 probe，证明当前几何输入能稳定复现。

完成这三项后，才进入通用破片模型。

## 接入点

| 区域 | 当前文件 | 用途 |
| --- | --- | --- |
| 武器生命周期 | `src/core/engine/simulation_kernel_weapon_release_service.cpp` | 发射、导弹运行、近炸触发 |
| 导弹/战斗部组件 | `src/components/combat/weapon.h` | 导弹、引信、战斗部参数 |
| 效果模型 | `src/models/weapons/default_effects_model.cpp` 和 `src/models/weapons/detail/*` | 起爆后作用、空间投影、部件命中 |
| 损伤状态 | `src/components/combat/damage.h` | 平台、飞机、部件损伤状态 |
| 损伤系统 | `src/systems/combat/damage_system.h` | 损伤后果随时间发展 |
| 飞行动力学后果 | `src/systems/physics/*`、`src/models/air/*` | 损伤影响飞行 |
| 触地/残骸 | `src/systems/physics/ground_contact_system.h` | 坠地、残骸生命周期 |
| 事件和训练消费 | `src/core/engine/simulation_kernel_engagement_event_store.cpp`、`gym_envs/scenario_loader/reward_runtime/air_combat.py` | 报告、训练奖励、终局 |

## 验收原则

- 每个模型阶段必须有受控 probe，而不是只看训练结果。
- 每个新增数值必须标记证据等级。
- 每个高保真结果必须能解释“命中哪里、起爆在哪里、作用机制是什么、哪些部件受损、后果如何传递”。
- 低细节 Pk 可以存在，但不得覆盖高保真事件链。
- 结构解体和残骸对象必须与训练终局分开表达：训练可以判胜，但仿真世界仍应保留可观测后果。

## 何时可以回到 AIM-120C / MQ-9

只有在以下条件满足后，才适合重新研究具体案例：

- 命中几何和引信阶段已有受控 probe。
- 至少一个通用破片模型可运行。
- 目标部件几何和脆弱性表具备证据等级。
- 结构失效模型能产生“完整机体受损”“延迟坠毁”“空中解体/碎片”三个分支。
- 诊断表能把这些分支和训练奖励分开报告。

否则，对 AIM-120C / MQ-9 的具体结论只应写成疑问或待校准假设。

## 下一步

下一步应先执行 `MLF-1E` 模块边界验收，确认公共合同、诊断投影、训练消费和旧字段删除条件是否已经收束；通过后再进入 `MLF-2A`，构建受控接近几何和引信 probe。旧字段不作为长期兼容面保留；不要直接调整具体弹药、目标或杀伤阈值。
