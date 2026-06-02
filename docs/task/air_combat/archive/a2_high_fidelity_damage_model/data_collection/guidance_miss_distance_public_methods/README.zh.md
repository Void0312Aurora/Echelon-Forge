# A2 guidance / miss-distance / terminal evasion 公开方法候选

状态：`2026-05-28 data-collection / no-authority-granted`。

本文档只收集公开 guidance、miss-distance、terminal evasion、seeker/track/noise 方法和验证数据候选。它不新增运行时代码，不放行 deterministic fuze，不授予 Pk / vulnerability authority，也不把开源仿真或民间资料提升为校准来源。

本目录来源台账见 [source_ledger.zh.md](source_ledger.zh.md)。本轮公开入口、权利、scope 和 artifact/hash 缺口补丁见 [source_pin_update_20260528.zh.md](source_pin_update_20260528.zh.md)。

## 结论摘要

当前可公开来源中，能稳定支撑 A2 后续 benchmark 的主轴不是“现代空空导弹真实命中率数据”，而是以下几类可复核方法：

- PN / APN / optimal guidance 的教材和公开论文，可支撑 guidance-law implementation criteria、miss-distance sensitivity criteria 和 cross-check。
- 公开 NPS/AFIT 老论文，可作为 simplified engagement / terminal evasion benchmark_dataset 候选，但只能覆盖旧式、简化、非现代武器参数的 PN engagement。
- JHU/APL Technical Digest guidance/filter/6DOF 文章，可支撑 seeker/track/noise、autopilot/flight-control lag、6DOF 模块边界和 validation_criteria。
- Singer maneuvering-target tracking 模型可作为目标机动和 seeker filter 的公开入口，但它是 tracking/noise 模型，不是杀伤或 Pk 数据。
- 开源仿真、第三方 PDF 镜像、论坛和民间实现只能做 sanity check；不得进入 authoritative descriptor。

因此，本轮可推荐的最高用途是 `benchmark_dataset` / `validation_criteria` / `reproducibility` 候选；没有来源可直接作为 A2 的 calibrated `effect_scale_authority`、`component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`。

## 采用等级

| 等级 | 含义 | 可进入后续门 |
|---|---|---|
| `benchmark_dataset_candidate` | 来源含公开或可获得的简化场景、miss distance 输出、仿真描述或代码形状，可复刻成 toy benchmark。 | 可进入 benchmark harness 设计；不能授权 Pk。 |
| `validation_criteria_candidate` | 来源给出 guidance/filter/flight-control/6DOF 建模原则、评估量或 sensitivity 轴。 | 可进入验收标准、残差表、测试矩阵。 |
| `reproducibility_candidate` | 来源提供公开全文、方程、代码、handle、稳定 DOI 或可复现配置线索。 | 可进入复现实验包；受版权限制的 companion code 只记录引用。 |
| `background_only` | 来源只适合术语、教材解释或交叉检查。 | 不进入数据行、不进入 authority gate。 |
| `sanity_check_only` | 开源实现、民间资料或第三方镜像。 | 只能用于发现实现错误或数量级异常。 |

## 推荐候选组合

| 用途 | 推荐来源组合 | 可支持 | 不能支持 |
|---|---|---|---|
| PN / APN guidance law 入口 | Zarchan AIAA 教材、JHU/APL `Basic Principles`、JHU/APL `Modern Homing`、USNA/FAS Chapter 15 | PN/APN/optimal-guidance 术语、LOS/closing-speed/target-accel/autopilot-lag 建模轴、benchmark criteria | 现代 AIM/R 系具体参数、真实 Pk |
| miss distance benchmark 方法 | Zarchan miss-distance/adjoint 方法、Lukenbill NPS thesis、JHU/APL 6DOF simulation、Jackson flight-control article | planar/3D PN toy benchmark、adjoint/sensitivity 方法、commanded vs achieved accel、lag/saturation metrics | 现代高保真武器验证数据 |
| terminal evasion 对 miss distance 的公开建模 | Straight AFIT thesis、McNamara AFIT thesis abstract、Lukenbill NPS thesis | jink/switching/constant-turn/barrel-roll 等 evasion maneuver sweep 候选、terminal timing sensitivity | 可再分发现成数值数据；现代战术有效性结论 |
| seeker / track / noise 方法入口 | JHU/APL `Guidance Filter Fundamentals`、Singer 1970、USNA/FAS active/SARH/passive/TVM、JHU/APL 6DOF simulation | Kalman/EKF/filter lag、sensor noise/data-rate/track continuity、seeker FOV/terminal sensor 模块边界 | ECCM、notch、clutter、decoy 真实性能 |

## PN / APN guidance 公开来源

可采用的最小公开模型口径：

- `PN`：LOS rate 与 closing speed / missile speed 共同决定横向加速度命令；benchmark 应记录 LOS angle/rate、closing speed、commanded acceleration、achieved acceleration、navigation ratio。
- `APN / optimal guidance`：目标加速度、time-to-go、autopilot/airframe lag 和 maneuver capability 被显式纳入；benchmark 应区分“有 target acceleration estimate”和“无 target acceleration estimate”。
- `guidance loop`：seeker / estimator / guidance law / autopilot / airframe / propulsion 是闭环，miss distance 不能只看 guidance formula。

推荐实现前置准则：

| 准则 | 候选来源 | A2 观测字段建议 |
|---|---|---|
| PN baseline 必须能区分 head-on、tail-chase、beam、high-off-boresight | Zarchan、JHU/APL Basic、USNA/FAS、现有 A2 P0 baseline | `proximity_min_dist_m`、`truth_min_dist_m`、LOS rate、closure |
| APN/optimal guidance 只能在 target acceleration estimate 或 equivalent model 存在时声明 | JHU/APL Modern、Zarchan、Singer | target accel estimate、filter state、time-to-go、guidance mode |
| autopilot lag / g saturation 必须进入 miss-distance residual | Jackson、JHU/APL 6DOF、Zarchan | commanded vs achieved accel、max lateral g、autopilot tau、turn energy loss |
| noise/filter benchmark 必须独立于 final kill probability | JHU/APL Guidance Filter、Singer | measurement noise、filter covariance、track memory、bearing/range update rate |

## Miss-distance benchmark 方法

建议把 benchmark 拆成三层，避免把简化公开数据误包装成高保真验证。

| 层 | benchmark_dataset 候选 | validation_criteria 候选 | reproducibility 候选 |
|---|---|---|---|
| `B0 analytic/toy` | Lukenbill NPS classical PN thesis；Zarchan 例题结构 | final miss distance、time-to-go、adjoint/sensitivity、LOS-rate convergence | NPS handle / public-domain thesis；Zarchan 需受版权约束引用 |
| `B1 maneuver/evasion` | Straight AFIT thesis；McNamara AFIT thesis abstract；Lukenbill evasion timing | constant turn、switch/jink、barrel roll、last-second reversal、orthogonal-to-LOS maneuver timing | NTIS / NASA STAR records；需要官方全文或稳定归档后再入包 |
| `B2 simulation architecture` | JHU/APL 6DOF article；Jackson flight-control article | airframe/propulsion/aero/actuator/sensor/filter/guidance/autopilot 模块边界；noise/latency/lag | 公开论文可复核模块清单；无公开高保真参数表 |
| `B3 A2 internal harness` | 现有 A2 P0 geometry matrix | head-on/tail-chase/beam/high-off-boresight regression；structured effects event fields | 仓库测试可复跑；不是外部公开验证数据 |

最低指标建议：

- `min_distance`: truth 最近距与 runtime proximity 最近距均记录。
- `time_of_closest_approach`: 用连续插值或 substep residual 标注当前最近点后一帧触发误差。
- `guidance_effort`: commanded/achieved lateral acceleration、g saturation、autopilot lag、turn-induced drag。
- `track_quality`: seeker mode、FOV/lock/range gate、measurement noise、filter covariance、track memory timeout。
- `terminal_outcome`: fuze trigger、miss distance、local detonation point、closure、warhead spatial scale、DamageReport，不使用黑盒 kill probability 作唯一指标。

## Terminal evasion 建模入口

公开资料支持把 evasion 建模为目标机动、timing、LOS geometry 和 track/filter 压力源，而不是直接乘到最终杀伤概率。

| evasion 轴 | 公开候选 | 可测量输出 | A2 推荐状态 |
|---|---|---|---|
| constant turn / maximum-g break | Straight、McNamara、Lukenbill | miss distance、maneuver start time sensitivity、missile accel saturation | benchmark sweep 候选 |
| switch/jink / last-second reversal | Straight、McNamara、Lukenbill | terminal miss distance、timing window、LOS-orthogonal maneuver effect | benchmark sweep 候选 |
| barrel roll / non-optimal maneuver | Straight | 与 straight / turn / jink 的相对 miss-distance 排名 | sanity / ranking candidate |
| target acceleration model | Singer、JHU/APL Modern、JHU/APL Guidance Filter | tracker covariance、target accel estimate、guidance command bias | validation criteria |
| damaged evader | A2 internal aircraft damage overlay + public flight-control criteria | target achieved g/turn-rate reduction、miss distance change | internal extension only |

注意：Straight / McNamara 是 1983 年公开记录的 AFIT thesis 线索，适合作为“老式 PN 规避 benchmark 候选”。在官方全文、表格、仿真配置、权利和 checksum 明确前，不应把其中结论转写为 A2 数据行。

## Seeker / track / noise 入口

推荐从以下公开方法抽象 A2 的 seeker/track/noise benchmark：

| 入口 | 来源 | 适用 benchmark |
|---|---|---|
| LOS angle/range pseudo-measurement、relative velocity estimate、time-to-go estimate | JHU/APL Guidance Filter | filter lag / noise miss-distance sweep |
| linear / EKF / Bayesian filtering assumptions | JHU/APL Guidance Filter、Singer | range/bearing/elevation noise、data rate、process noise |
| active / semiactive / passive / TVM homing taxonomy | USNA/FAS Chapter 15、JHU/APL Basic | seeker mode / datalink / terminal-local-contact tests |
| terminal sensor model fidelity | JHU/APL 6DOF | no-noise conceptual sensor vs noisy high-fidelity terminal sensor residual |
| flight-control loop interaction | Jackson、JHU/APL 6DOF | terminal sensor noise causing actuator activity、autopilot lag、command bandwidth |

## 不能提升为 authority 的内容

- 任何单条教材公式都不能授权 `deterministic_fuze_authority`。
- 任何 old thesis 的 miss-distance ranking 都不能授权现代 AIM-120 / R-77 / AIM-9X Pk。
- 任何 third-party PDF mirror 都不能作为可再分发数据源；只能用官方 handle、DOI、publisher page、NTIS/NASA/NPS 记录定位。
- 开源仿真代码、论坛、游戏/民间 missile model 只能做 sanity check，不能进入 vulnerability descriptor 的 `source_kind=external_calibration_dataset` 或 `validated_physics_surrogate`。
- JHU/APL / AIAA / Springer 等公开页面可引用，但正文、图表、代码和 companion material 仍受各自版权约束；仓库内只记录 source_ref 和摘要，不复制受限内容。

## 后续数据包建议

1. `pn_classical_toy_v1`：以 Lukenbill NPS thesis + Zarchan/APL 术语交叉检查建立 planar/3D PN toy suite，输出 final miss distance、LOS rate、time-to-go、commanded/achieved accel。
2. `terminal_evasion_sweep_v1`：以 Straight/McNamara/Lukenbill 的 maneuver taxonomy 建立 constant-turn、switch/jink、barrel-roll、last-second reversal sweep；初始只验证相对趋势，不声明现代战术。
3. `seeker_filter_noise_v1`：以 Singer + APL Guidance Filter 建立 bearing/range/elevation noise、sample-rate、filter tau、track dropout sweep；输出 track covariance 和 miss-distance sensitivity。
4. `a2_geometry_regression_v1`：保留现有 A2 head-on/tail-chase/beam/high-off-boresight geometry matrix，作为 internal reproducibility，不伪装成外部数据。

每个数据包必须附带：source_ref、方程/配置版本、权利说明、参数范围、seed 或 deterministic replay、metric 定义、cross-validation note、残余风险。

## 当前 residuals

| residual | 影响 | 关闭条件 |
|---|---|---|
| `RES-GMD-001 no-modern-public-aam-validation` | 无法授权现代空空导弹 Pk / deterministic fuze。 | 获取可公开、scope 匹配、权利明确的外部校准数据或经验证 surrogate。 |
| `RES-GMD-002 old-thesis-scope` | AFIT/NPS 老论文只覆盖简化 PN engagement。 | 逐项记录 missile/target dynamics、initial geometry、guidance variant、maneuver timing，与 A2 scope 分离。 |
| `RES-GMD-003 full-text-rights` | NTIS/IEEE/AIAA/Springer 来源可能只有 bibliographic 或付费访问。 | 记录官方 acquisition path，不复制受限正文/数据；只使用可公开摘要和自生成复现实验。 |
| `RES-GMD-004 seeker-ecm-gap` | clutter/notch/ECCM/decoy 缺公开可校准数据。 | 先做 track-quality proxy benchmark；真实 ECM 另开 evidence gate。 |
| `RES-GMD-005 reproducibility-gap` | 教材公式和论文摘要不足以形成数据集。 | 每个 benchmark 包补 manifest、参数表、dt、seed、checksum、生成脚本和审计报告。 |
