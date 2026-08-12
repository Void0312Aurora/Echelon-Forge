# 杀伤链制导与近炸杀伤校准研究记录

日期：`2026-06-21`

状态：研究记录 / 待开显式 follow-on。本文只记录当前仓库的工程代理行为和
校准入口，不放行真实 AIM-120C、F-16C 或 Pk 权威。MLF-10 已把校准门基础设施
归档，但明确保持 runtime 参数重调、真实弹种/目标杀伤权威和 deterministic fuze
authority 为 held 项。

## 问题

用户指出两个不符合直觉的现象：

1. 制导：8 km、30 度偏置攻击匀速目标时，看起来无法命中。
2. 杀伤：近炸导致的杀伤偏低。

本次复核把两者拆开：先看导弹是否进入引信/近炸窗口，再看进入窗口后的
damage / component failure / platform consequence 是否足够。

## 当前测试与代码入口

- 8 km / 30 度数据库 AIM-120C 镜像测试位于
  `tests/runtime/air_combat/weapon_guidance_realism/missile_dynamics.py` 的
  `test_mirrored_launch_bearings_stay_symmetric_with_kinematic_target`。当前验收门只要求
  左右镜像最近距都小于 `15 m`，以及左右差小于 `0.5 m`。
- 另一个 P0 miss-distance baseline 在
  `tests/runtime/air_combat/weapon_guidance_realism/launch_guidance.py` 中，只把
  `red_x=13000, red_y=9000` 的高离轴工程代理场景压到 `5 m` 内，并不是数据库
  AIM-120C 的 8 km / 30 度场景。
- 制导链路使用 PN + terminal capture + APN/lead blend。`apn_target_accel_gain > 0`
  时才启用目标运动估计与 lead blend，8 km 正好落在
  `kLeadBlendTerminalRangeM = 8000` 的终端混合边界。
- 近炸链路中，引信先根据 reliable/soft radius 计算 sensor opportunity 和
  mechanism quality；旧 `effective.damage *= 0.6 + 0.4 * fuze_quality` 路径
  已从 runtime surface 删除。
- 默认 blast-fragmentation 空间投影半径不是直接等于 `lethal_radius`，而是
  `lethal_radius * projection_radius_fraction`。AIM-120C 数据库当前
  `lethal_radius=15 m`、`projection_radius_fraction=0.60`，因此空间投影半径约为
  `9 m`。
- 组件失效概率仍经过 `component_failure_probability(...)` 的非直击门。非直击
  threshold 为 `0.56`，概率上限为 `0.72`，在 8-12 m 附近会强烈受
  `spatial_effect_scale`、mechanism load、结构/部件阈值和 synthetic vulnerability
  缩放影响。

## 复现结果

命令：

```bash
python -m pytest tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py -q
```

结果：`47 passed, 6 subtests passed`。也就是说当前仓库测试没有把该场景判为失败；问题是现有验收门
过宽，未覆盖“近炸后应有足够杀伤”的要求。

用现有 runtime 做只读诊断，数据库 AIM-120C、station 1、目标匀速，强制 truth
track：

| 场景 | 最近距 | 引信 | effects | component failures | 主要观测 |
| --- | ---: | --- | --- | ---: | --- |
| 16 km / -20 deg | `7.113 m` | `fuze_armed` | `damage_applied` | 0 | `spatial_effect_scale ~= 0.389`, failure probability `~=0.214` |
| 16 km / +20 deg | `7.113 m` | `fuze_armed` | `damage_applied` | 0 | 左右镜像良好 |
| 8 km / -30 deg | `10.963 m` | `fuze_armed` | `damage_applied` | 0 | `spatial_effect_scale ~= 0.130`, failure probability `~=0.008` |
| 8 km / +30 deg | `10.963 m` | `fuze_armed` | `damage_applied` | 0 | 目标仍 active；肉眼上像“没打中/没杀伤” |

结论：8 km / 30 度并不是完全没有近炸，导弹已经进入 15 m 引信窗口；真正的问题是
最近距落在当前战斗部/部件失效模型的弱作用区，导致引信触发但杀伤近似无效。

近炸 debug sweep 使用 `blast_fragmentation, damage=180, radius=15, mass=18.144`：

| miss distance | component failures | failure probability | spatial effect | platform/system 观测 |
| ---: | ---: | ---: | ---: | --- |
| `0.5 m` | 4 | `0.949` | `0.828` | 系统健康明显下降 |
| `2 m` | 5 | `0.821` | `0.828` | 系统健康明显下降 |
| `4 m` | 3 | `0.935` | `0.867` | 系统健康明显下降 |
| `8 m` | 0 | `0.0216` | `0.130` | 只有轻微系统健康下降 |
| `10.96 m` | 0 | `0.0085` | `0.060` | 极弱影响 |
| `12 m+` | 0 | `0.0` | `0.0` | 基本无影响 |

这说明近炸杀伤曲线在 `4 m -> 8 m -> 11 m` 之间跌得过陡。

## 参数敏感性

只改制导参数的 what-if：

| 改动 | 8 km / 30 deg 最近距 | component failure probability | 结论 |
| --- | ---: | ---: | --- |
| 当前数据库 | `10.96 m` | `0.008` | 引信触发但弱杀伤 |
| `nav_gain=5` | `9.71 m` | `0.010` | 最近距改善有限 |
| `nav_gain=6` | `8.67 m` | `0.016` | 仍没有组件失效 |
| `max_lateral_g=45` | `9.16 m` | `0.012` | g 限提高不是主解 |
| 关闭 APN/lead | `~60 m` | 无 effects | APN/lead 是当前命中窗口的关键 |

只改 AIM-120C warhead 投影的 what-if：

| 改动 | 最近距 | spatial effect | component failure probability | 结论 |
| --- | ---: | ---: | ---: | --- |
| 当前 `projection_radius_fraction=0.60` | `10.96 m` | `0.130` | `0.008` | 太弱 |
| `projection_radius_fraction=1.00` | `10.96 m` | `0.261` | `0.012` | 有改善但远不够 |
| `projection_radius_fraction=1.00`, `nav_gain=6` | `8.67 m` | `0.351` | `0.029` | 仍低 |

结论：单独扩大空间投影半径不足以解决杀伤偏低。近炸杀伤需要同时审查
blast-frag mechanism load、非直击 component failure 概率曲线、AIM-120C 代理
projection/effect scale，以及 F-16C synthetic vulnerability 的 near-miss scale。

## 归因

### 制导

当前 8 km / 30 度数据库 AIM-120C 的制导表现是“进入近炸窗口，但不是高质量近炸”。
APN/lead 已经是必要条件；关闭后最近距退化到约 60 m。现有测试只验收 `<15 m`，
因此它会通过，但这个门不足以支撑“有效杀伤”。

制导侧建议不要先追求直接命中，而是新增一个更贴近杀伤链的门：

- 8 km / 30 deg AIM-120C 匀速目标，左右镜像；
- 最近距目标从当前 `<15 m` 收紧到一个工程阈值，例如 `<9 m` 或 `<8 m`；
- 同时记录 peak achieved g、peak lead blend、APN contribution，避免把后续杀伤
  参数问题误当成制导问题。

### 近炸杀伤

当前近炸模型的主问题是“引信窗口”和“有效战斗部作用窗口”分离过大：

- 引信可靠半径是 `15 m`，soft radius 可由 projection/lethal radius 扩展；
- 但 blast-frag 空间投影对 AIM-120C 被 `projection_radius_fraction=0.60` 压到约
  `9 m`；
- 8 km / 30 deg 的 `10.96 m` 最近距超过或接近有效投影边缘，组件 failure
  probability 只剩约 `0.8%`；
- 12 m 以后 debug 近炸基本无结构效果，这与“15 m 近炸半径”作为工程直觉不一致。

## 建议的后续校准路线

1. 新增一个显式 follow-on：`kill_chain_guidance_lethality_calibration`。入口不应写入
   已归档 MLF-1 到 MLF-10；应作为 A2 当前根面的新 active/retained follow-on。
2. 第一阶段只加诊断和验收门，不立即改实参：保留 8 km / 30 deg 数据库 AIM-120C
   诊断表，要求报告最近距、引信原因、spatial effect、component failure probability、
   component failure count 和目标 active/loss-state。
3. 制导候选：以 `nav_gain`、terminal capture/lead blend、短距高偏置 APN 响应为
   候选，但验收以最近距和左右镜像为主。制导修正单独验收，不把杀伤增强混入。
4. 杀伤候选：把 AIM-120C `projection_radius_fraction=0.60`、blast-frag
   `projection_min_effect_scale/falloff_exponent`、非直击 component failure 概率尾部、
   synthetic vulnerability `near_miss_scale` 分开做小矩阵；每次只改一个机制并记录
   8 m、10.96 m、12 m 的结果。
5. 权威边界：这些调整只能标为 `engineering proxy calibration`。除非 MLF-10 admission
   gate 后续显式放行，不能写成真实 AIM-120C Pk、真实 F-16C 易损性或确定性杀伤结论。

## 当前判断

最短路径不是“只修制导”或“只增大威力”，而是把该场景作为新的杀伤链联合校准门：

- 制导门负责把 8 km / 30 deg 从当前约 `10.96 m` 收紧到更稳定的近炸质量；
- 杀伤门负责让 `8-12 m` 区间的 blast-frag 近炸不再从明显杀伤突然掉到近零；
- 两个门分开报告，最后再组合验收。
