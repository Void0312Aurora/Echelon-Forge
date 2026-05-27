# 空战高保真杀伤模型要求评审

状态：`2026-05-28` 追踪复核。本文档从空战杀伤建模的领域要求出发，定义"高保真"的实质标准，并把当前 A2 实现重新对齐到最新代码事实。`2026-05-26` 初评把当前实现归为"参数化命中效果 + 子系统标记"；此后 A2 已推进组件几何、机制载荷证据、引信 profile、组件冗余/依赖和 vulnerability evidence gate，但这些仍主要是工程化脚手架，不等价于校准高保真杀伤链。

## 1. 问题陈述

A2 当前已经越过最初的 HP-only / 大区域 hitbox 阶段：

- structured aircraft 不再由 HP-first bypass 直接定义击杀；
- F-16、Su-35、MQ-9、MH-60R、E-3 已具备 20+ 代表组件样例；
- `WarheadProfile` / `FuzeProfile`、组件 `mechanism_thresholds`、armor/exposure、组件失效概率、冗余组、组件依赖和 `EffectsEvent` 证据面已进入代码与回归；
- vulnerability descriptor gate 已能阻止 synthetic profile 或未授权 rows 被误提升为 Pk / deterministic-fuze authority。

但从领域标准看，当前仍不能宣称"高保真已完成"。主要原因是：组件阈值、机制载荷、引信可靠性和 vulnerability rows 仍是参数化或测试 fixture；真实破片云、连续杆切割、雷达/激光/触发引信物理模型、校准组件失效概率和 Pk 验证尚未完成。

本文档的目的：

- 从领域第一性原理定义空战杀伤模型的"高保真"意味着什么；
- 跟踪当前实现相比初评的新增进展；
- 明确下一步应继续推进哪些能把模型从工程化脚手架推向可校准物理链的工作。

## 2. 高保真杀伤链模型

高保真空战杀伤模型必须独立建模杀伤链的每一环。任何一环被启发式或黑盒替代，整个模型就会退化为参数化工程模型。

### 2.1 末端制导与 Miss Distance

**高保真要求**：miss distance 必须由制导律、目标机动、导弹能量状态和导引头性能在闭环仿真中产生，并作为损伤输入被下游模型消费。

| 要素 | 当前状态 | 仍存缺口 |
|------|---------|---------|
| 制导律 | PN 闭环存在，并已有 head-on / tail-chase / beam / high-off-boresight miss-distance baseline | 还没有导引头性能、制导误差、目标末端机动策略的高保真校准 |
| Miss distance 追踪 | `proximity_min_dist_m` 被跟踪，`EffectsEvent.miss_distance_m` 可审计 | live proximity 仍以最近点后一帧触发判定，不能单独放行确定性引信 |
| Miss distance 消费 | 近炸投射、距离衰减、vulnerability miss-distance bucket 和事件审计已开始消费 | 仍未形成"末端规避 -> miss distance -> 机制载荷 -> 组件失效"的全因果闭环 |
| 规避影响 | 制导回路能产生不同 miss distance；兼容 hit probability 仍保留 evasion 乘数 | evasion 仍部分以黑盒乘数存在，应逐步迁移到 miss-distance / seeker / fuze 机制内 |

### 2.2 引信模型

**高保真要求**：引信模型必须区分引信类型，建模触发条件、延迟、偏差、可靠性和失效模式，并产生目标几何中的 3D 爆轰点。

| 要素 | 当前状态 | 仍存缺口 |
|------|---------|---------|
| 引信类型 | `FuzeProfile` 已携带 radar/laser proximity、contact/impact、timed 等类型 | 类型语义仍是最小分支，不是校准引信模型 |
| 引信延迟 | `delay_s` 能把 `detonation_time_s` 与 `nearest_approach_time_s` 分离 | 延迟来源、漂移、穿入后延迟和失效模式未校准 |
| 引信可靠性 | `reliability`、`fuze_effective_reliability`、signature proxy 可审计 | radar/laser RCS/反射触发条件仍是代理尺度，不是传感器物理模型 |
| 接触/触发引信 | contact/impact 不再把 near-miss radius 当接触触发，事件暴露表面距离、穿入深度、inside-hitbox | 接触力学、穿入深度、结构表面材料和延迟爆轰仍未物理化 |
| timed fuze | 可按发射后 delay 独立生成 event | timed fuze 战术设定、漂移和安全约束未建模 |

### 2.3 战斗部效应

**高保真要求**：战斗部效应必须建模 3D 空间分布。不同战斗部类型有根本不同的杀伤机制。

#### 2.3.1 破片 / 爆破破片战斗部

| 要素 | 当前状态 | 仍存缺口 |
|------|---------|---------|
| 破片样本数和命中估计 | `warhead_spatial_sample_count`、hit estimate/fraction 和 energy scale 已进入事件面 | 仍是参数化采样证据，不是 Mott 分布或真实破片质量/速度分布 |
| 破片穿透 / 装甲耦合 | `mechanism_fragment_energy_j`、`mechanism_penetration_margin`、armor/exposure scale 已进入 effects | 没有 THOR / FATEPEN 等穿透方程校准，也没有逐破片轨迹 |
| 空间分布 | 近炸投射按弹头族 footprint、距离、速度轴和姿态轴调制 | 仍不是 3D 破片云，也没有组件表面入射角和遮挡模型 |

#### 2.3.2 连续杆战斗部

| 要素 | 当前状态 | 仍存缺口 |
|------|---------|---------|
| 杆方向性 | continuous rod 已消费导弹速度轴和引爆姿态轴，并记录 orientation-pattern scale | 仍是参数化方向证据，不是杆环展开几何求交 |
| 杆切割载荷 | `mechanism_rod_cut_margin` 进入事件与组件失效概率 | 没有杆直径、展开速度、截面密度和目标结构厚度的物理求解 |

#### 2.3.3 爆轰战斗部

| 要素 | 当前状态 | 仍存缺口 |
|------|---------|---------|
| 超压 / 冲量证据 | `mechanism_blast_overpressure_kpa` 与 `mechanism_blast_impulse_kpa_ms` 已进入事件 | 仍是工程化载荷证据，不是 Sachs 缩放或校准爆轰传播模型 |
| 目标表面反射 | exposure scale 开始作为代理进入 mechanism scale | 未建模表面反射、遮挡、姿态相关增强和结构阈值 |

### 2.4 目标脆弱性与组件级几何

**高保真要求**：目标脆弱性应建模为组件级条件杀伤概率，对每个损伤机制类型具有特定阈值，并可追溯到校准数据。

| 要素 | 当前状态 | 仍存缺口 |
|------|---------|---------|
| 组件级 hitbox | 当前代表飞机库均有 20+ 组件，组件中心位于父 hitbox 内，并能在 runtime 报告 primary component | 仍只是代表组件样例，不是全机完整工程结构模型 |
| 机制特定阈值 | 组件可声明 `mechanism_thresholds`，并影响 failure probability | 阈值为工程化参数，不来自实测/公开校准数据 |
| 组件失效概率 | synthetic sigmoid 已消费机制载荷、阈值、direct/projection 和 RNG；授权 fixture rows 可覆盖概率 | 真实 calibrated rows 未接入，fixture 只能证明门控和数据通路 |
| 冗余建模 | `ComponentDamageState` 记录组件完整性、冗余组可用性、成员数和失败数 | 冗余仍是组可用性脚手架，不是完整液压/电气/飞控依赖网络 |
| 方位角相关暴露 | aspect bucket、velocity axis、orientation axis、projected exposure scale 已开始调制 | 仍不是基于全 3D 几何的暴露面积、遮挡和入射角计算 |
| 特定组件装甲 | hitbox/component `armor_mm` 已被机制采样读取 | armor 数值和材料模型未校准 |

### 2.5 损伤传播与级联效应

**高保真要求**：损伤不仅限于直接命中的组件。级联效应应沿功能依赖、物理邻接和时间线传播。

| 要素 | 当前状态 | 仍存缺口 |
|------|---------|---------|
| 火灾 / 燃油泄漏 | fuel leak 消耗 `FuelSystem` / `Mass`，火灾可继续影响结构、航电、机组、液压和燃油 | 没有起燃概率、邻接传播、抑制系统、烧穿时间线 |
| 液压级联 | 液压损伤会拖累飞控，组件依赖可传播到 flight_control/hydraulic overlay | 没有具体液压回路、管线破裂、作动器卡滞/漂移/自由模式 |
| 结构级联 | `structural_overstress` / `flutter_exposure` 在高能包线下累积并收紧包线 | 没有离散翼梁屈服、疲劳裂纹或灾难性结构失效事件 |
| 电气 / 航电级联 | power/data-link/mission radar 等组件可通过 dependencies 影响相关 overlay | 仍是最小依赖脚手架，不是总线切换和负载 shedding 模型 |
| 飞行员 / 机组 | crew/pilot/mission crew 字段影响传感器和控制能力 | 仍是能力乘数，不是伤害类型、任务分工和时间线模型 |

### 2.6 杀伤评估

**高保真要求**：给定损伤状态，每个杀伤类别的概率应基于导致该杀伤类别的具体组件失效、时间关键性和平台任务语境。

| 要素 | 当前状态 | 仍存缺口 |
|------|---------|---------|
| kill state 推导 | `AircraftDamageState` 与 `PlatformDamageState` 推导 mission/mobility/sensor/lost，1v1 consumer 可消费 `DamageReport` | 阈值仍是工程规则，不是校准 kill probability |
| 非终局损伤消费 | reward surface 可一次性消费非终局 `DamageReport` shaping，不写回物理权威 | 课程统计和任务级 kill assessment 仍未完整迁移 |
| 时间关键杀伤 | 燃油泄漏、火灾和高能结构暴露已有最小时间演化 | 没有燃油耗尽时间、火灾烧穿时间、返场约束的 kill-chain 评估 |

## 3. 当前实现分类

对照上述标准，当前 A2 实现更适合按以下层次描述：

```
层级 0: 基于 HP 的杀伤
层级 1: 参数化命中效果 + 子系统 overlay
层级 2A: 组件级几何、机制载荷和证据面脚手架
层级 2B: 校准组件脆弱性与条件失效概率
层级 3: 全物理杀伤链（制导 -> 引信 -> 战斗部 -> 脆弱性 -> 级联）
层级 4: 校准/验证过的杀伤链
```

当前实现应归为：**层级 1 已基本闭合，层级 2A 已启动并覆盖代表飞机库，层级 2B/3/4 尚未达成**。

这比初评的"纯层级 1"有实质进展：现在组件身份、机制阈值、装甲/暴露、机制载荷、组件概率、冗余组、依赖传播和 vulnerability evidence gate 都能进入运行时和事件审计。但这些数据仍以 synthetic / fixture / engineering scaffold 为主，因此不能把当前状态描述为"高保真已实现"。

## 4. 已完成进展对照

- Phase 1：HP-first bypass 反转、structured aircraft path、`EffectsEvent` / `DamageReport` 记录、physical effects 不直接写 RL `Score`。
- Phase 2：`AircraftDamageState` overlay、飞行动力学/推进/传感器/fuel leak 派生、火灾/液压/燃油级联、控制轴和 control-asymmetry overlay。
- Phase 3：`WarheadProfile` / `FuzeProfile`、弹头族 footprint、近炸空间投射、orientation-pattern 证据、机制载荷字段、候选组件机制载荷行及 row 级 failure provenance / authority / evidence-axis 审计、contact/impact/timed 初步语义、组件几何/阈值/冗余/依赖。
- Phase 5：synthetic vulnerability scaffold、descriptor gate、authority 分离、rows 受控接入、Pk / deterministic-fuze authority 防误提升。

## 5. 下一步建议

1. 固化层级 2A 验收门：继续保持"组件几何 + 机制证据 + 事件审计"为当前阶段目标，但文档和测试中避免使用"已高保真"的措辞。

2. 将候选组件级机制载荷行接入校准证据形状：当前同一事件已经能记录每个命中/投射候选组件的 fragment / blast / rod / penetration 载荷行，且 row 级 failure probability/source/calibrated/dataset/sample、authority 和 weapon/aspect/closure/miss-distance 匹配轴已可审计，下一步应让这些 row 能对接更细的 component-specific evidence ref，而不是停留在工程化 mechanism-load scaffold。

3. 继续把 evasion 迁移出黑盒 hit probability：下一步应让末端规避主要通过 miss distance、目标签名、引信触发和机制载荷传递，而不是独立乘数。

4. 建立非权威校准数据形状：可以先加入一份明确 non-authoritative 的 schema/fixture 文档，约束 future calibrated rows 的 weapon family、target、aspect、closure、miss-distance、mechanism-load 和 component-failure 字段。

5. Phase 4 deterministic fuze 仍不应放行：只有当 fuze trigger、miss-distance、target signature、warhead footprint 和 vulnerability evidence 都有可审计且非 synthetic 的授权路径时，才允许替换 RNG hit gate。

6. Phase 5 的真实工作不是更多 synthetic profile，而是选择一个窄目标/武器对，接入可追溯的校准来源或明确验证过的物理 surrogate，并让 authority gate 只对该窄域放行。

## 6. 结论

A2 的新进展是实质性的：项目已经从"大区域参数化命中效果"推进到"组件级几何和机制证据脚手架"。但高保真不是字段数量或测试 fixture 的同义词；它要求 kill chain 中的关键参数来自物理模型、实测数据或明确校准的 surrogate。当前最重要的工作，是把已建立的证据面继续向组件级机制载荷、真实脆弱性数据和可授权引信模型推进，同时保持 synthetic / calibrated / authoritative 三者的边界清晰。
