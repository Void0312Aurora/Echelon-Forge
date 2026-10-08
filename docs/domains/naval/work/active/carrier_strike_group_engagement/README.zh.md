# 航母打击群对抗

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/README.md`
Owner: `domains/naval`
Last verified: `2026-10-08`

状态：`2026-10-08` active。`P0 Boundary`、`S0-A`..`S0-D` 与 `S0-X` 已接受；`S0-B` 大地坐标放置已在
`087c1928` 验证。S0-X 已补齐两套原生确定性回放产物与无 agent 的 spectator profile。
S1-A/B 实现已验证，待集成审阅；S1-C/D/X 仍受共享依赖阻塞。本包保持开放。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

输入：

- [海军 owner README](../../../README.zh.md)
- [海军最小任务结构](../../../standards/minimal_task_structure.zh.md)
- [海军观测契约](../../../standards/observation_contract.zh.md)
- [海军领域执行面拆分](../naval_domain_surface_split/README.zh.md)：已接受的有界 N4 工作包，
  其维护面是本包的起点
- [Navy 军种画像](../../../../joint/service_profiles/standards/navy_profile.zh.md)
- [Joint 指挥与建模基线](../../../../joint/standards/command_and_modeling_baseline.zh.md)
- [Joint 指挥链路与报告基线](../../../../joint/standards/command_link_and_reporting_baseline.zh.md)
- [空域 owner README](../../../../air/README.zh.md)
- [梯度逼真度原则](../../../../../systems/standards/gradient_realism_principles.zh.md)
- [子项目创建标准](../../../../../engineering/automation/rules/subproject_creation_standard.zh.md)
- 已位于 `main` 的装备调研目录 `database/research/equipment/catalog/**`，
  仅作为参数及来源参考，不代表对应装备已获仿真能力准入

## 目的

本工作包构建一场实名、按条令完整编制的两支航母打击群对抗：美国海军 `杰拉尔德·R·福特`
级 CSG 对中国人民解放军海军 `福建` 级航母编队。以该场景作为组织目标，补齐仓库仍缺失的
海军基础设施。

本工作包是需求方与集成方。其他域也需要的机制由 `docs/systems/` 下的跨域系统 owner
建设，本包通过下方的依赖登记使用它们；本包拥有场景阶梯、海军专属机制与各阶段验收。

工作以场景驱动。一条可运行的场景阶梯从静态兵力存在逐级长到完整的双方对抗；每一级只补该级
所需的基础设施，可单独运行，并按其宣称的逼真度门验收。每一级同时提供一个对称镜像变体
（双方使用同一平台集合），以便在解读实名不对称效果之前先隔离机制缺陷。

首个交付是脚本驱动的双方推演。学习策略不在范围内，但每一级都必须留出后续强化学习工作包
所需的观测、动作与终止事件边界。

本工作包取代历史的 `N0`-`N8` 海军阶梯，作为海军作战能力的前向计划。原阶梯记录于
[海军进展快照](../../../reviews/naval_progress_snapshot_20260527.zh.md)，作为带日期的
出处保留，不再扩展。

## 当前状态

初始清单于 `2026-09-28` 在 `work/naval-mechanisms` 的 `5fa7fc9e` 上测得；S0-X 于
`2026-09-30` 在 `087c1928` 闭合。当前 S1-A/B 检查点为 `2026-10-08`，基于
`origin/main` 的 `cedfa01c3` 集成。完整清单与 S0-X、S1-A/B 运行时证据见
[当前状态](carrier_strike_group_engagement_current_status_20260928.md)。

| 领域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 海军平台 | S0 实名内容 | `examples/config/database/**/csg/{us,cn}/` 与 S0-C 内容测试 | S0 挂载已完成内容和生成证据；反舰与鱼雷机制仍延期 |
| 舰艇 / 潜艇机动 | S1-B 有界舰艇机动；潜艇仍为运动学 | `ship_motion_system.h`、`ship_maneuvering.h` 与原生机动测试 | 二次阻力、Nomoto 艏摇、回转与实时毁伤响应；无完整水动力；U1 潜艇工作仍开放 |
| 指令投影 | S1-A 有界编队与航路跟随 | `NavalCommandIntent`、`station_keeping.h`、`python/scenario/runtime/csg_transit.py` | 真方位站位与场景拥有的领舰航路；无 Joint 编队指挥层级 |
| 水面探测 | 有界 | 雷达含海杂波、大气波导与地平线代理 | 探测地平线仍是平面世界；S0 放置已使用共享大地坐标系 |
| 水下探测 | 仅被动 | `sonar_system.h`、`default_acoustic_model.cpp` | 直接读取所有舰艇/潜艇真实位置；无主动声呐、传播剖面、拖曳阵或浮标 |
| 海军武器 | 有界 | `weapon_naval.h`、`naval_mission_weapon_release_system.h` | 舰炮与 CIWS 为单次命中掷骰；VLS 仅经飞行员动作路径；无反舰导弹、舰空导弹族或鱼雷 |
| 海军毁伤 | 合成，已接通实时机动耦合 | `DM-N1`、`damage_system_naval.h` 与原生进水/机动测试 | 舱室效果仍属合成模型；舰艇机动直接消费 mobility capability |
| 航母航空 | S0 仅库存 | `meta.csg.groups[*].embarked_inventory` 与实名机型记录 | 无飞行甲板接触面或甲板周转；S2 前库存飞机不是活动实体 |
| 空战底座 | Air 脚本运行时和契约已合入 `main` | 空战场景；`python/simulation/air/` 和 `python/tasking_contracts/air/` | 复用而不重新接管；不代表航母甲板周期或 CSG S2 已验收 |
| 海军学习策略 | 缺失 | `examples/config/training/active/naval/` 下三个冒烟入口 | 无检查点或训练结果 |

## 范围

范围内：

- 双方编队的实名平台单位（航母、巡洋舰与驱逐舰、攻击型核潜艇、补给舰、舰载机、舰载直升机，
  以及其武器与传感器），每项带参数出处；
- 各阶段在阶段计划中列出的海军自有机制：编队与护航几何、舰艇与潜艇机动、飞行甲板与机库
  资源、舰上火控通道、海军平台舱室，以及海军传感器与武器平台适配器；
- 集成依赖登记中列出的跨域系统交付物，并提出各 owner 据以建设的需求说明；
- 一条场景阶梯 `CSG-S0`..`CSG-S6`，每级提供实名与对称镜像两个变体，附场景契约与测试；
- 每级的吞吐量实测记录（实体数 × 固定步长 × 墙钟时间）；本机无法完成时在 HEI 上运行；
- 每级预留的观测、动作与终止事件边界；
- 每级场景的回放与可视化。

范围外：

- 学习策略训练，或任何关于学习策略质量的声明；
- 两支编队之外的陆基打击/支援航空、天基资产与战区级联合兵力；首条阶梯不含陆基轰炸机、
  远程反舰弹道导弹与岸基导弹；
- 现实作战评估。实名平台与有出处的参数不会使任何场景结局成为对真实兵力的预测；
- 涉密或非公开性能数据；只用公开来源，并记录不确定度；
- 修改 Joint 通用核心语义或空域所有权；航母航空经空域 owner 的维护面使用空域机制；
- 在海军目录内建设跨域机制。大地坐标、环境、通用探测、数据链、电子战、武器族、通用毁伤与
  共享后勤归 `docs/systems/` 下各自的 owner。

## 阶段计划

主阶梯承载空中、水面与打击路径；水下轨道因写集基本不重叠而并行推进，须在 `CSG-S6` 之前汇合。
各级宣称上限使用项目共享的 `G0`-`G7` 标签。

| 阶段 | 场景 | 海军自有工作（系统依赖见下方登记） | 宣称上限 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 无 | 包范围、阶段阶梯、宣称上限、参数出处策略 | 仅文档 | accepted |
| `CSG-S0` | 双方完整编制静态生成 | 实名单位、编组 schema 与共享大地坐标放置 | `G0` | `2026-09-30` accepted；S0-X 回放/可视化已闭合 |
| `CSG-S1` | 双方编队航渡 | 编队与护航几何；航路跟随；回转与航速响应；毁伤-机动耦合；编队补给调度 | `G1`-`G2` | partial：A/B 已验证；C/D/X 受依赖阻塞 |
| `CSG-S2` | 甲板周转：出动波次、CAP、回收 | 弹射与拦阻循环；甲板、升降机与机库容量；出动架次；回收航线；舰载直升机作业 | `G3` | planned |
| `CSG-S3` | 相互搜索与战术态势 | 海军传感器平台适配器与编队航迹上报；海军辐射管制条令 | `G4` | planned |
| `CSG-S4` | 对防御编队的单向打击 | 舰上火控通道、VLS 与分层防空条令；舰载诱饵发射装置；舰艇舱室与飞行甲板能力丧失 | `G5` | planned |
| `CSG-S5` | 双方空海对抗 | 编队打击规划与目标分配；舰载直升机回收落水机组 | `G6` | planned |
| `CSG-S6` | 完整对抗（实名与镜像） | 水下轨道汇合；CSG 结局条件；冻结预留的 RL 边界 | `G6`，部分 `G7` 项 | planned |
| `CSG-U1` | 潜艇航渡与定深 | 深度、航速与自噪声耦合；安静航行 | `G1`-`G2` | planned |
| `CSG-U2` | 水下搜索 | 声呐平台：舰壳、拖曳、吊放、浮标阵 | `G4` | planned |
| `CSG-U3` | 鱼雷交战 | 鱼雷发射管与发射；潜射反舰导弹经 `CSG-S4` 路径；水线以下舱室 | `G5` | planned |
| `P5 Closure` | 无 | 验收、索引、归档 | 仅文档 | planned |

依赖：`CSG-S(n)` 需要 `CSG-S(n-1)` 已接受。`CSG-U1` 需要 `CSG-S0`；`CSG-U2` 需要 `CSG-U1`
与 `CSG-S3`；`CSG-U3` 需要 `CSG-U2` 与 `CSG-S4`。`CSG-S6` 需要 `CSG-S5` 与 `CSG-U3`。

### 系统依赖登记

其他域也使用的机制归跨域系统 owner。本包提出需求并集成交付物，不自行建设这些机制。
每个 owner 工作包在第一个需要它的阶段准备开工时开启。

| 机制 | 系统 owner | owner 工作包 | 需要它的阶段 | 海军自有部分 |
| --- | --- | --- | --- | --- |
| 大地坐标系与地球曲率 | `systems/physics` | [大地坐标系](../../../../../systems/physics/work/active/geodetic_frame/README.zh.md)（`P3-A`/`P3-B` 已接受） | `CSG-S0` 及此后所有阶段 | 无 |
| 分层环境：陆地、淡水、海洋、水深、海岸线、海况、风、昼夜、海洋声学数据 | `systems/environment` | [环境运行时](../../../../../systems/environment/work/active/environment_runtime/README.zh.md)（已开）；海洋数据线在其 `P2 Contract` 之后开启 | `CSG-S1`；`S2` 甲板限制；`S3` 探测；`U1` 深度限制；`U2` 水声 | 舰艇耐波性响应 |
| 传感器探测、地平线使用、去除真值读取 | `systems/sensing` | 于 `CSG-S3` 开启 | `S3`、`U2` | 海军雷达与声呐平台适配器 |
| 数据链、编队指挥层级、识别 | `systems/command-tasking`（关系沿用 Joint 基线） | 于 `CSG-S3` 开启 | `S1` 层级、`S3`、`S5` | 海军编队角色 |
| 电子战：干扰、ESM、辐射管制、软杀伤 | `systems/sensing` 与 `systems/weapons` | 于 `CSG-S3` 开启 | `S3`、`S4`、`S5` | 舰载诱饵发射装置（平台内容） |
| 反舰导弹、舰空导弹、鱼雷的制导、引信与弹库消耗 | `systems/weapons` | 于 `CSG-S4` 开启 | `S4`、`S5`、`U3` | 舰上火控通道与 VLS |
| 舱室毁伤、损管、能力退化 | `systems/effects` | 于 `CSG-S4` 开启 | `S4`、`S5`、`U3` | 舰艇舱室与 `DM-N1` profile |
| 燃油、续航、补给、空中加油 | `systems/physics`（共享后勤组件） | 于 `CSG-S1` 开启 | `S1` 舰艇、`S2` 舰载机 | 海上补给航行几何 |
| 舰载机弹射起飞与着舰 | 空域 owner | 于 `CSG-S2` 开启 | `S2` | 甲板资源与回收航线 |
| 结局裁定、终止、回放 | `systems/weapons` 与 architecture | 于 `CSG-S6` 开启 | `S6`；吞吐量与回放自 `S0` 起 | CSG 结局条件 |

## 任务簇

- 任务簇计划：
  [carrier_strike_group_engagement_task_clusters_20260928.md](carrier_strike_group_engagement_task_clusters_20260928.md)
- 当前状态：
  [carrier_strike_group_engagement_current_status_20260928.md](carrier_strike_group_engagement_current_status_20260928.md)
- 派发队列：
  [carrier_strike_group_engagement_dispatch_queue_20260928.md](carrier_strike_group_engagement_dispatch_queue_20260928.md)
- 验收门：
  [carrier_strike_group_engagement_acceptance_20260928.md](carrier_strike_group_engagement_acceptance_20260928.md)

## 产出与证据

每个已接受的阶段须留下：

- `scenarios/naval/csg/` 下的实名与镜像场景文件；
- `tests/contracts/unit/naval/csg/` 下的场景契约；
- 该阶段新增的每项机制的原生与 Python 聚焦测试；
- 吞吐量记录：实体数、固定步长、仿真时长、墙钟时间、主机；
- 回放产物与可视化 profile；
- 本目录中的阶段验收记录，写明宣称上限与遗留项。

平台内容须为每个参数留下出处记录：来源 ID、来源等级与不确定度。装备调研目录是第一来源；
缺口由公开网络调研补齐，并以同样方式记录。

## 验收门

本工作包只有满足以下全部条件才能标记为 accepted：

- `CSG-S0`..`CSG-S6` 与 `CSG-U1`..`CSG-U3` 各有阶段验收记录；
- 实名与镜像的 `CSG-S6` 场景在维护运行时上运行至裁定终止，并可回放；
- 每级的宣称上限都由维护运行时证据满足，而非仅诊断路径（梯度逼真度原则第 3 条）；
- 场景使用的任何海军探测路径在宣称 `G4` 及以上时都不读取其他实体的真实状态；
- 预留的 RL 观测、动作与终止事件边界已成文，并由脚本控制器实际走通；
- 每个实名平台参数都有出处记录；
- 任何文档或结果都不宣称学习策略质量或现实作战预测。

## 遗留与下一步

- `S0-X` 已接受。两套回放产物位于
  `docs/domains/naval/work/active/carrier_strike_group_engagement/artifacts/`，由
  `naval_csg_replay` 合同重新生成并逐帧校验；两个
  `examples/viz/profiles/naval_csg_s0_*_replay.json` profile 通过既有地图/状态可视化合同播放这些帧，
  不需要 agent；配套的 `*_spectator.json` profile 直接步进原生 kernel。`CSG-S1` 与 `CSG-U1` 的 S0 前置依赖已结清。
- [S1-A/B 检查点](carrier_strike_group_engagement_acceptance_20260928.md#csg-s1-ab-runtime-checkpoint-2026-10-08)
  验证了一小时实名/镜像航渡、终点驻站收敛、有来源的加速/停车检查，以及合成毁伤到机动的耦合。
  S1-C 等待共享舰船燃油/续航合同；S1-D 等待 Environment Runtime `P3-A`，之后完成环境与 Joint 层级集成。
  S1-X 需要两者闭合；不派发本地替代实现。
- [大地坐标系](../../../../../systems/physics/work/active/geodetic_frame/README.zh.md) 工作包的锚点与换算已被两套 S0 场景消费。
- `CSG-S1`/`CSG-S2` 的吞吐量记录将决定统一高保真步进能否承载完整编制。混合步长需另行决策；
  本包不预设采用。

## 归档

阶段验收记录在接受后移至 `docs/domains/naval/reviews/`。长期事实（如平台出处规则或编队契约）
提升为海军标准或参考。被取代的规划记录按仓库生命周期策略移入 `archive/`。
