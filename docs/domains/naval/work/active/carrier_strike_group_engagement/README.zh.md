# 航母打击群对抗

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/README.md`
Owner: `domains/naval`
Last verified: `2026-09-28`

状态：`2026-09-28` active。`P0 Boundary` 已于 `2026-09-28` 获 owner 接受；`CSG-S0` 已开始，
首先进行 `S0-A` 兵力编制调研。

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
- 未合并的装备调研目录 `origin/codex/database-scaffold`
  （`database/research/equipment/catalog/**`），仅作参数来源

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

于 `2026-09-28` 在 `work/naval-mechanisms` 的 `5fa7fc9e` 上测得；完整清单见
[当前状态](carrier_strike_group_engagement_current_status_20260928.md)。

| 领域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 海军平台 | 有界内容 | `examples/config/database/ships/units/*.json`（DDG-51 Flight I、ASW 直升机型 DDG、Kilo MVP、红方水面占位、T-AKE） | 无航母、巡洋舰、055/052D、攻击型核潜艇或中方补给舰 |
| 舰艇 / 潜艇机动 | 运动学 | `ship_motion_system.h`、`submarine_motion_system.h` | 仅速度/航向/深度限速；无水动力、回转圈、航路跟随或毁伤耦合 |
| 指令投影 | 已接受 | `NavalCommandIntent` | 每舰一个护航站位；无多舰编队或编队指挥层级 |
| 水面探测 | 有界 | 雷达含海杂波、大气波导与地平线代理 | 平面世界；无大地坐标系 |
| 水下探测 | 仅被动 | `sonar_system.h`、`default_acoustic_model.cpp` | 直接读取所有舰艇/潜艇真实位置；无主动声呐、传播剖面、拖曳阵或浮标 |
| 海军武器 | 有界 | `weapon_naval.h`、`naval_mission_weapon_release_system.h` | 舰炮与 CIWS 为单次命中掷骰；VLS 仅经飞行员动作路径；无反舰导弹、舰空导弹族或鱼雷 |
| 海军毁伤 | 合成 | `DM-N1` profile | 仅命中 hitbox 舱室时写入；舰艇机动不读毁伤状态 |
| 航母航空 | 缺失 | 无 | 无弹射、拦阻、甲板/机库容量、出动架次或舰上着舰 |
| 空战底座 | main 上已维护；脚本栈未合并 | 空战场景；`origin/codex/scripted-stack-*` | 复用而不重新接管；无舰载机单位 |
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
| `CSG-S0` | 双方完整编制静态生成 | 实名单位与挂载及参数出处；编队组成的场景 schema | `G0` | active |
| `CSG-S1` | 双方编队航渡 | 编队与护航几何；航路跟随；回转与航速响应；毁伤-机动耦合；编队补给调度 | `G1`-`G2` | planned |
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
| 大地坐标系与地球曲率 | `systems/physics` | [大地坐标系](../../../../../systems/physics/work/active/geodetic_frame/README.zh.md)（已开） | `CSG-S0` 及此后所有阶段 | 无 |
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

- `P0 Boundary` 需要 owner 审阅本 README、任务簇与验收门。
- `CSG-S0` 是首个实现阶段，需要[大地坐标系](../../../../../systems/physics/work/active/geodetic_frame/README.zh.md)
  工作包提供的锚点与换算；兵力编制调研可以先于它们开始。
- `CSG-S1`/`CSG-S2` 的吞吐量记录将决定统一高保真步进能否承载完整编制。混合步长需另行决策；
  本包不预设采用。

## 归档

阶段验收记录在接受后移至 `docs/domains/naval/reviews/`。长期事实（如平台出处规则或编队契约）
提升为海军标准或参考。被取代的规划记录按仓库生命周期策略移入 `archive/`。
