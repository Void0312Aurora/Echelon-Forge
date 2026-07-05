# 杀伤链理想化期望合同

状态：`2026-06-21`，用于
[杀伤链期望标准化](README.zh.md) 的合同草案。本文是仓库 engineering-proxy 期望合同，
不是真实 AIM-120C、F-16C、确定性引信或 Pk 权威。

Schema label：`a2.kill_chain_idealized_expectation_contract.v0`

## 合同边界

本合同为已声明的代理画像定义期望行为。它不能从当前 runtime 输出反推。当前 runtime 输出
是实现行为证据；本文是上游目标，用来判断实现行为后续应校准、保持 held，还是重新分类。

合同有三层 authority：

| 层级 | 含义 | runtime 用途 |
| --- | --- | --- |
| `engineering_proxy_expectation` | 项目自有的理想化期望，用于可信简化行为。 | 可驱动文档、诊断和受保护校准计划。 |
| `research_candidate_expectation` | 来自可审阅方法或候选数据，但尚未准入为 runtime 真值。 | 可驱动 benchmark 设计和 residual 跟踪。 |
| `admitted_authority_expectation` | 通过未来任务专属 authority gate。 | 仅能在已准入字段和 scope 内驱动 runtime authority。 |

当前本文只使用 `engineering_proxy_expectation`。

## 阶段合同

杀伤链按以下有序阶段合同评价：

| 阶段 | 回答的问题 | 主要期望输出 | 不得决定 |
| --- | --- | --- | --- |
| `launch_window` | 该发射属于 declared nominal、marginal 还是包线外？ | 场景类别、目标运动类别、launch-envelope label | 杀伤强度 |
| `guidance_approach` | 导弹是否接近到声明的引信 / 效果区域？ | 最近距、最近点时间、剩余能量或运动学余量 | 部件损伤 |
| `fuze_decision` | 引信是否应按最近点几何触发？ | 触发 yes/no、触发点、引信质量或置信度 | 声明范围外的战斗部强度 |
| `warhead_load_field` | 哪种载荷场抵达目标代理？ | 归一化空间 / 载荷分区和机制载荷事实 | 目标后果 |
| `component_response` | 目标代理如何响应该载荷？ | 部件响应分区、完整度变化分区、失效概率分区 | 任务结局本身 |
| `consequence_projection` | 可观测任务或平台后果是什么？ | 任务、机动、传感、结构、生命周期或 loss-state 后果分区 | 反向决定制导 / 引信成功 |

校准必须一次只针对一个阶段。若某指标跨阶段，它必须显式声明为 cross-stage，且不能作为
单层校准目标。

## 归一化距离词汇

类似“10 m”这样的固定距离，在没有声明画像前没有独立含义。本合同使用：

```text
rho_fuze = miss_distance / R_fuze
rho_effect = miss_distance / R_effect
```

其中：

- `R_fuze` 是代理画像声明的近炸引信触发半径。
- `R_effect` 是代理期望声明的有效战斗部载荷半径。默认情况下它是独立 review
  variable，不是 `R_fuze` 的别名，也不能从当前 runtime 响应反推。它未来可以被设置为
  等于、小于或大于 descriptor / runtime projection radius，但必须在解释案例前声明。

初始定性期望分区为：

| 分区 | 归一化距离 | 理想化期望 |
| --- | --- | --- |
| `core` | `rho_effect <= 0.25` | 应有强载荷场和强部件响应。 |
| `effective` | `0.25 < rho_effect <= 0.50` | 应有显著载荷和非平凡部件响应。 |
| `outer_effective` | `0.50 < rho_effect <= 0.80` | 应有中等或边缘显著响应；近零响应需要解释。 |
| `edge` | `0.80 < rho_effect <= 1.00` | 弱响应、偶发响应或强几何依赖响应可以接受。 |
| `outside_effect` | `rho_effect > 1.00` | 默认没有有效战斗部载荷响应，除非声明了其他机制。 |

这些是定性分区，不是概率数值。量化阈值属于未来 P3/P4 决策。

## AIM-120C-like 种子画像

Profile id：`KCES-AIM120C-LIKE-FIGHTER-V0`

Authority：`engineering_proxy_expectation`

目的：为中距主动雷达空空弹对 fighter-size synthetic 目标提供第一讨论对象。

声明的代理假设：

| 字段 | 种子值 | 权威说明 |
| --- | --- | --- |
| 武器族标签 | `AIM-120C-like active-radar missile` | 只作为族标签，不是型号级性能声明。 |
| 战斗部机制 | `blast_fragmentation` | 仓库工程代理。 |
| 目标类别 | `fighter_size_synthetic_target` | 使用仓库 F-16C-like synthetic vulnerability shape 作为代理，不是真实 F-16C 真值。 |
| 目标运动类别 | 第一矩阵使用 `nonmaneuvering_constant_velocity` | 后续矩阵必须加入机动目标。 |
| 发射窗口类别 | `nominal_in_envelope` 必须逐案例声明 | 合同不会自动把每次发射都归类为 nominal。 |
| `R_fuze` | 按画像声明；需要映射时可先引用仓库 trigger-radius 代理 | 不是真实确定性引信权威。 |
| `R_effect` | `independent_review_variable` | 不从 `R_fuze` 派生，不从当前弱响应反推，也不是真实战斗部效果真值。 |

Policy decision：

```text
R_effect_policy = independent_review_variable
```

因此，种子画像把引信触发半径和有效载荷半径视为两个独立概念。场景 row 可以携带
`R_effect_variant` 标签，例如 `effect_radius_equals_fuze_radius`、
`effect_radius_smaller_than_fuze_radius` 或
`effect_radius_larger_than_runtime_projection`，但这些是审阅变体，不是隐藏默认值。

解释规则：

- 若某案例被声明为 `nominal_in_envelope`、非机动，且理想化测试中传感器 / truth gate
  不构成限制，则制导期望应把最近点压入 `R_fuze`。
- 若同一案例进入 `R_fuze`，且 `rho_effect` 属于 `core`、`effective` 或
  `outer_effective`，则下游载荷 / 响应阶段不应在没有声明目标抗性或战斗部效果理由的情况下
  坍缩为近零响应。
- 若 profile 审阅选择的 `R_effect` 小于 miss distance，则弱响应可以与期望合同一致；
  这时该案例属于 `outside_effect`，而不是 unexplained failed near-fuze lethality expectation。

这就是“10 m”歧义的答案：合同不说 10 m 必杀，也不说 10 m 不杀。它说，在声明
`R_fuze`、`R_effect`、目标代理和后果指标之前，10 m 不能被解释。

## 发射窗口期望

某代理案例若要称为 `nominal_in_envelope`，应显式声明：

- 初始距离、高度、己方和目标速度；
- 目标方位、偏置角和闭合几何；
- 目标机动类别；
- 测试使用的 seeker / data / track 简化；
- 画像使用的导弹运动学约束；
- 测试属于 idealized truth-guided、sensor-limited 还是 full runtime。

期望阶段结果：

| 发射窗口类别 | 制导期望 | 失败解释 |
| --- | --- | --- |
| `nominal_in_envelope` | 对非机动目标，最近点通常应进入 `R_fuze` | 若 miss 在 `R_fuze` 外，先视为制导 / 运动学 / 建模问题，除非重新分类。 |
| `marginal_in_envelope` | 进入引信范围是 plausible，但不保证 | 重复 miss 可以接受，但必须记录。 |
| `outside_envelope` | 没有进入引信范围的期望 | 不对杀伤施加校准压力。 |

8 km / 30 deg 案例在被显式归入上表前，不应作为校准 oracle。

## 通用空空模板

后续每条期望 row 应声明：

| 字段 | 必填内容 |
| --- | --- |
| `profile_id` | 代理期望的稳定 id。 |
| `authority_level` | 使用上文 authority level 之一。 |
| `weapon_proxy` | 武器族、制导类别、战斗部机制和已声明代理参数。 |
| `target_proxy` | 尺寸类别、易损性 profile、部件 map 和 synthetic / authority 状态。 |
| `geometry_class` | 距离、方位、偏置、闭合、高度带和目标机动类别。 |
| `R_fuze` 和 `R_effect` | 已声明半径及其来源 / authority。 |
| `expected_stage_bands` | 期望的 launch、guidance、fuze、load、response 和 consequence 分区。 |
| `measurement_fields` | 评价该 row 使用的 stage-report 字段。 |
| `forbidden_claims` | 仍保持拒绝的真实武器、真实目标、确定性引信、Pk 或 reward 声明。 |

## 开放决策

- 部件响应的定性分区应由完整度变化、部件失效概率、抽样失效还是任务后果定义。
- 发射窗口类别应先作为 task-local 文档维护，还是审阅后提升到更广 air/weapon 标准。

在这些决策关闭前，本文是标准化目标，不是 runtime 校准指令。

已关闭的 P1 决策：

- AIM-120C-like 种子的 `R_effect` 保持独立 review variable。这关闭了 P1 半径 policy
  歧义，同时保留后续 scenario matrix 中的 sensitivity rows。
