# 杀伤链场景期望矩阵

状态：`2026-06-23`，用于
[杀伤链期望标准化](README.zh.md) 的 P2 pass 场景矩阵。本文只是 docs-only 场景矩阵；
不运行仿真，不重调参数，不声明真实 AIM-120C / F-16C / Pk 权威。

英文规范页：
[kill_chain_scenario_expectation_matrix_20260622.md](kill_chain_scenario_expectation_matrix_20260622.md)

## 矩阵政策

P1 合同已将半径 policy 收口为：

```text
R_effect_policy = independent_review_variable
```

因此，本矩阵在分类制导 / 引信期望时，不会暗中把 `R_effect` 等同于 `R_fuze`。
后续可以在一个 row 上声明一个或多个 `R_effect_variant` 进行评价，但发射窗口 / 引信期望
必须和有效载荷期望分开。

## 共享种子画像

| 字段 | 值 |
| --- | --- |
| profile_id | `KCES-AIM120C-LIKE-FIGHTER-V0` |
| authority_level | `engineering_proxy_expectation` |
| weapon_proxy | AIM-120C-like active-radar、blast-fragmentation engineering proxy |
| target_proxy | fighter-size synthetic target；只使用仓库 F-16C-like vulnerability shape |
| R_fuze | 按 profile 声明；后续 metric row 可映射到仓库 trigger-radius 代理 |
| R_effect | independent review variable |
| forbidden claims | 真实 AIM-120C 战斗部 / 引信 / 破片真值、真实 F-16C 易损性、确定性引信、Pk、reward authority |

## 发射窗口类别

| 类别 | 定义 | 制导期望 |
| --- | --- | --- |
| `nominal_in_envelope` | 非机动或轻微目标运动，几何位于声明测试包线内，且没有传感器 / 数据简化刻意阻止末制导。 | 最近点应进入 `R_fuze`；若重复 miss 在 `R_fuze` 外，优先进入制导 / 运动学 / 模型分类工作。 |
| `marginal_in_envelope` | 几何对转弯率、闭合、seeker handoff 或 timing 有压力，但仍是 plausible shot。 | 进入引信范围是 plausible，但不保证；若 stage facts 能解释，miss 可以接受。 |
| `outside_envelope` | 几何或目标运动超出声明代理包线。 | 没有进入引信或杀伤期望。 |

## 热图矩阵政策

P2 的校准约束对象不是单个 8 km / 30 deg row，而是距离 x 偏置角的热图矩阵。
单点 row 只作为 heatmap cell 的锚点或诊断示例。P3/P4 不得只证明一个 cell 通过后
就声明 envelope 校准成立。

第一轮 heatmap 锚点使用以下轴：

| 轴 | 样本值 | 说明 |
| --- | --- | --- |
| 初始距离 `range_km` | `4`, `6`, `8`, `10`, `12`, `16` | engineering-proxy anchor grid；不是 AIM-120C 真实射程表，也不是最终采样密度。 |
| 偏置角 `offset_deg` | `0`, `15`, `30`, `45`, `60`, `75`, `90` | 表示 launch geometry offset / bearing-angle stress；P3 负责映射到具体 stage-report 字段；不是最终角度步长。 |
| 目标运动层 | `nonmaneuvering_constant_velocity` full grid；`mild_maneuver` sparse grid；`hard_maneuver` held | 先约束匀速目标 full heatmap，再用机动层检查一般性。 |

符号：

| 符号 | 含义 | P3 期望 |
| --- | --- | --- |
| `N` | `nominal_in_envelope` | 应进入 `R_fuze`；若重复不进入，需要制导 / 运动学解释。 |
| `M` | `marginal_in_envelope` | 进入 `R_fuze` plausible but not guaranteed；P3 必须记录 stage facts。 |
| `O` | `outside_envelope` | 不施加 fuze/load/response 校准压力。 |

第一轮匀速目标 heatmap：

| range_km \ offset_deg | `0` | `15` | `30` | `45` | `60` | `75` | `90` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `4` | N | N | N | N | M | M | O |
| `6` | N | N | N | N | M | O | O |
| `8` | N | N | N | M | M | O | O |
| `10` | N | N | M | M | O | O | O |
| `12` | N | M | M | O | O | O | O |
| `16` | M | M | O | O | O | O | O |

这个 heatmap 是工程代理期望，不是真实武器包线。它的作用是约束拓扑：

- 固定偏置角时，距离增加不应让期望等级反向变好，除非 P3 明确声明 seeker / handoff
  等机制理由。
- 固定距离时，偏置角增加不应让期望等级反向变好，除非 P3 明确声明几何或目标运动理由。
- `8 km / 30 deg` 匀速 cell 是 `N`，但它不是唯一校准目标；相邻 cell 也必须保留
  合理连续性。
- `O` cell 是 negative control。它们不应因为调杀伤参数而产生有效载荷 / 部件响应期望。

第一轮机动目标 sparse heatmap：

| range_km \ offset_deg | `0` | `30` | `60` |
| --- | --- | --- | --- |
| `6` | N | M | O |
| `8` | M | M | O |
| `10` | M | O | O |

`mild_maneuver` sparse heatmap 用来检查校准一般性，但不反向削弱匀速目标 full heatmap。
`hard_maneuver` 暂不进入 P2 pass，后续只有在机动强度、目标加速度和制导模型指标明确后才扩展。

## 热图验收约束

后续 P3/P4 至少应把每个 heatmap cell 映射到这些层：

| Heatmap layer | 字段 | 用途 |
| --- | --- | --- |
| `launch_class` | `N/M/O` | P2 给出的期望类别。 |
| `guidance_fuze` | `rho_fuze`、nearest approach、fuze trigger | 判断 cell 是否满足制导 / 引信期望。 |
| `runtime_projection_effect` | `REV-RUNTIME-PROJECTION` 下的 `rho_effect` 和 load band | 对照当前实现。 |
| `eq_fuze_effect` | `REV-EQ-FUZE` 下的 `rho_effect` 和 load band | sensitivity 上界。 |
| `smaller_load_effect` | `REV-SMALLER-LOAD` 下的 `rho_effect` 和 load band | “触发但有效载荷更小”的解释路径。 |
| `component_response` | failure probability band、integrity delta band、sampled failure | 只在 fuze/load 成功后评价。 |

P2 不要求每个 cell 立即有 runtime sample；它要求 P3/P4 的采样和报告以 heatmap 为对象。
若后续算力有限，优先级顺序是：`N` cells、与 `N/M` 边界相邻 cells、`O` negative controls。

## 采样密度估算

上面的 `4/6/8/10/12/16 km` 和 `0/15/30/45/60/75/90 deg` 是 P2
锚点网格，用于声明期望拓扑；它不应作为后续校准 harness 的唯一采样密度。
P3/P4 应显式区分 unsigned heatmap cell、signed bearing case 和 repeat/seed 数。

| 采样层级 | 距离轴 | 偏置角轴 | 目标运动层 | 单 seed case 估算 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `anchor-grid` | `4,6,8,10,12,16` km | unsigned `0,15,30,45,60,75,90` deg；signed 为 `0, +/-15, +/-30, +/-45, +/-60, +/-75, +/-90` | 匀速 full；机动 sparse | unsigned：`42 + 9 = 51`；signed：`78 + 15 = 93` | 文档锚点、smoke、快速拓扑检查。 |
| `recommended-main-grid` | `4..16 km`，`1 km` 步进，共 `13` 点 | unsigned `0..90 deg`，`5 deg` 步进，共 `19` 点；signed 共 `37` bearing | 匀速 full；机动 sparse 使用 `4/6/8/10/12/14/16 km` x signed `0/15/30/45/60/75/90 deg` | 匀速 signed `13 x 37 = 481`；机动 sparse signed `7 x 13 = 91`；合计 `572` | 推荐的第一轮校准热图，用于形成稳定的距离 x 方位角曲面。 |
| `boundary-refinement` | 在 `N/M`、`M/O` 边界附近增加 `+/-0.5 km` 局部点 | 在边界附近增加 `+/-2.5 deg` 局部点 | 先匀速；机动只加密已出现异常的区域 | 预计额外 `200-400` cases；以 P3 实测边界数量为准 | 检查边界连续性、避免粗网格误判。 |
| `expanded-maneuver-grid` | 同 `recommended-main-grid` | 同 `recommended-main-grid` | mild maneuver 也跑 full grid | 匀速 `481` + mild full `481` = `962` | 仅在机动模型指标稳定后使用；不是 P2/P3 的默认入口。 |

Repeat / seed 预算：

| Grid | 1 seed | 3 seeds | 5 seeds | 建议 |
| --- | --- | --- | --- | --- |
| `anchor-grid` signed | `93` | `279` | `465` | smoke 和回归入口。 |
| `recommended-main-grid` signed + maneuver sparse | `572` | `1716` | `2860` | P3/P4 首选；先 1 seed，再对边界和异常 cell 加 repeat。 |
| `expanded-maneuver-grid` | `962` | `2886` | `4810` | 机动层成熟后再跑。 |
| `boundary-refinement` add-on | `+200-400` | `+600-1200` | `+1000-2000` | 由 P3 首轮热图自动挑选边界后再追加。 |

当前开发机可见 `88` logical CPUs。P4 harness 计划可以先用 `32` workers 运行
pilot batch，确认每 case 时间、内存和输出争用后再上调到 `48-64` workers。`R_effect_variant`
默认应作为 recorded miss/load facts 的离线评价维度；除非实现确实需要重跑 runtime，
否则不应把 `REV-RUNTIME-PROJECTION`、`REV-EQ-FUZE` 和 `REV-SMALLER-LOAD`
直接乘进 simulation case 数。

## 初始场景行

以下 rows 是 heatmap 的锚点，不是完整校准集合。

| Row id | Heatmap cell | 几何类别 | 目标运动 | 发射窗口类别 | 制导期望 | 引信期望 | 战斗部载荷期望 | 部件响应期望 | 后果期望 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `KCES-S1-8KM-30DEG-CV` | CV heatmap `8 km x 30 deg = N` | 8 km 初始距离，30 deg 偏置，fighter-size 目标 | `nonmaneuvering_constant_velocity` | `nominal_in_envelope` | 最近点应进入 `R_fuze` | 若最近点在 `R_fuze` 内，则期望触发 | 取决于声明的 `R_effect_variant`；不能只凭米数解释 | 只有在 `core/effective/outer_effective` 变体下才期望非近零响应 | 在声明 component-response metric 前不声称后果 | 当前关切的主 cell。它首先是制导 / 引信期望 row，不是 kill-probability row。 |
| `KCES-S2-HEADON-CV` | CV heatmap low-offset `N` cells | 迎头，中等距离，低偏置 | `nonmaneuvering_constant_velocity` | `nominal_in_envelope` | 相比 S1 横向需求更低，最近点应进入 `R_fuze` | 若在 `R_fuze` 内则期望触发 | 通过 `rho_effect` 评价 | 响应分区跟随声明的 `rho_effect` | held | 简单拦截 baseline row。 |
| `KCES-S3-TAILCHASE-CV` | CV heatmap distance-stress `M` cells | 尾追，中等距离，需要正闭合余量 | `nonmaneuvering_constant_velocity` | `marginal_in_envelope` | 是否进入引信范围取决于闭合 / 能量余量 | 只有最近点进入 `R_fuze` 才期望触发 | 通过 `rho_effect` 评价；若制导失败，不给杀伤额外压力 | held unless fuze/load succeeds | held | 拆分能量 / 闭合限制和战斗部校准。 |
| `KCES-S4-BEAM-CV` | CV heatmap offset-stress `M` cells | 横向穿越目标，中等距离 | `nonmaneuvering_constant_velocity` | `marginal_in_envelope` | 最近点可能考验 lead / PN / autopilot response | 只对成功接近期望触发 | 通过 `rho_effect` 评价 | 不允许部件响应补偿 `R_fuze` 外的制导 miss | held | 用于检查末制导提前量和横向加速度。 |
| `KCES-S5-HIGH-OFFBORESIGHT-CV` | CV heatmap high-offset `M/O` cells | 高偏置 / 高 bearing angle | `nonmaneuvering_constant_velocity` | `marginal_in_envelope` 或 `outside_envelope` | 在约束声明前不保证 nominal fuze entry | 不保证触发 | 若不在 `R_fuze` 内，则无载荷期望 | 无 fuze/load 时无响应期望 | held | 防止把每次发射都当成 calibration oracle。 |
| `KCES-S6-8KM-30DEG-MANEUVER` | mild-maneuver sparse heatmap `8 km x 30 deg = M` | 8 km 初始距离，30 deg 偏置 | `mild_maneuver` | `marginal_in_envelope` | 是否进入引信范围取决于机动强度和制导模型 | 不保证触发 | 仅在 fuze 成功后评价 | 响应跟随声明的 `rho_effect` | held | 加入目标机动，但不改变非机动 S1 期望。 |
| `KCES-S7-OUTSIDE-RANGE-CV` | CV heatmap `O` cells | 距离或几何超出声明代理包线 | `nonmaneuvering_constant_velocity` | `outside_envelope` | 没有进入引信范围期望 | 不期望触发 | 无载荷期望 | 无响应期望 | 无后果期望 | negative-control row。 |

## R_effect 评价变体

这些变体不是 runtime 参数，只是后续 sensitivity 或 metric-mapping rows 的标签。P2
只选择第一轮评价标签，不声明米制半径或概率阈值。

| Variant id | P2 decision | 含义 | 用途 |
| --- | --- | --- | --- |
| `REV-RUNTIME-PROJECTION` | selected | `R_effect` 映射到当前 runtime projection radius。 | 第一轮实现对比 row；用于解释当前实现落在哪个 `rho_effect` band，不作为理想化标准。 |
| `REV-EQ-FUZE` | selected | 为简化期望包线 sensitivity row 设 `R_effect = R_fuze`。 | 检查最强简单耦合假设；若该 row 下仍近零响应，P3/P4 应优先检查载荷 / 响应映射。 |
| `REV-SMALLER-LOAD` | selected | `R_effect < R_fuze`，表示引信范围大于有效载荷范围。 | 表达“近炸触发但有效载荷边缘或不足”的解释路径；只能在显式声明该变体时使用。 |
| `REV-DECLARED-EFFECT` | held | `R_effect` 来自未来 engineering-proxy review row。 | 仍是长期首选路径，但 P2 不伪造 review row；待 P3/P4 或外部 evidence 工作提供。 |

## P2 行级收口

| Row id | P2 状态 | 第一轮 `R_effect_variant` | P3 优先级 | P3 handoff |
| --- | --- | --- | --- | --- |
| `KCES-S1-8KM-30DEG-CV` | pass | `REV-RUNTIME-PROJECTION`, `REV-EQ-FUZE`, `REV-SMALLER-LOAD` | high | 主 calibration-planning anchor。P3 必须同时报告 `rho_fuze`、三个 `rho_effect` 变体、fuze trigger、load band、component-response band。 |
| `KCES-S2-HEADON-CV` | pass | `REV-RUNTIME-PROJECTION`, `REV-EQ-FUZE` | medium | 简单拦截 baseline。P3 用它分离低横向需求场景和 S1 的 30 deg 偏置需求。 |
| `KCES-S3-TAILCHASE-CV` | pass | `REV-RUNTIME-PROJECTION`, `REV-SMALLER-LOAD` | medium | 能量 / 闭合压力 row。P3 先确认是否进入 `R_fuze`，只有 fuze 成功才评价载荷和响应。 |
| `KCES-S4-BEAM-CV` | pass | `REV-RUNTIME-PROJECTION`, `REV-EQ-FUZE` | medium | lead / PN / lateral-acceleration row。P3 应把制导 miss 和 warhead response 分开。 |
| `KCES-S5-HIGH-OFFBORESIGHT-CV` | pass | conditional `REV-RUNTIME-PROJECTION` only after `R_fuze` entry | low | 先作为 envelope-classification row；若未进入 `R_fuze`，不进入载荷 / 响应校准。 |
| `KCES-S6-8KM-30DEG-MANEUVER` | pass | conditional `REV-RUNTIME-PROJECTION`, `REV-SMALLER-LOAD` only after `R_fuze` entry | medium | 机动目标 row；不得反向削弱 S1 非机动 nominal 期望。 |
| `KCES-S7-OUTSIDE-RANGE-CV` | pass | none | low | negative-control row；P3 应确认无 fuze/load/response 期望，而不是校准失败。 |

## P3 输入要求

P3 不需要重开 P2 分类。它应在上述 rows 上补齐可测字段：

- `launch_window`：range、offset/aspect、target-motion class、launch-window class。
- `guidance_approach`：nearest approach、`rho_fuze`、time-to-nearest、是否进入 `R_fuze`。
- `fuze_decision`：trigger yes/no、trigger point、fuze quality/confidence。
- `warhead_load_field`：所选 `R_effect_variant`、`rho_effect`、load band、机制载荷 facts。
- `component_response`：component response band、failure probability band、integrity delta band、sampled failure。
- `consequence_projection`：只在 component-response metric 明确后评价，不从 kill flag 倒推。

## P2 收口状态

P2 当前为 pass。本矩阵提供第一版距离 x 偏置角 heatmap、采样密度估算，并在 AIM-120C-like
engineering-proxy 期望下，将 8 km / 30 deg 非机动 cell 分类为
`nominal_in_envelope`。P2 已选择第一轮 `R_effect_variant` 评价集：
`REV-RUNTIME-PROJECTION`、`REV-EQ-FUZE` 和 `REV-SMALLER-LOAD`；`REV-DECLARED-EFFECT`
保持 held，直到未来 review row 或 admitted evidence 出现。

P2 本身不解决：

- 米制 `R_effect` 数值；
- 部件响应概率阈值；
- 后果 / Pk / reward authority。

具体 stage-report metrics 已进入独立 P3 映射页：
[kill_chain_metric_mapping_20260623.zh.md](kill_chain_metric_mapping_20260623.zh.md)。
剩余参数值、阈值和 harness 执行设计进入 P4 或后续 evidence work，且仍保持
docs-only / guarded planning 边界。
