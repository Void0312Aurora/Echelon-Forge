# 杀伤链制导机制消融结论 — 2026-07-15

## 范围

本证据包只诊断当前 engineering runtime，不校准真实武器，也不授予 AIM-120C、
F-16C、引信、毁伤或 Pk 权威。baseline 固定为仓库当前 AIM-120-like 代理，包括
`N=4`、`35 g` 和 `APN=0.5`。

实验共运行 `200` 次确定性仿真：`20` 个左右镜像匀速案例乘 `10` 个制导机制变体。
极小正增益只用于打开或关闭现有机制门，不是待优化参数。保留证据包括
[JSON 报告](kill_chain_guidance_mechanism_ablation_20260715.json)、
[逐次结果](kill_chain_guidance_mechanism_ablation_20260715_rows.csv)、
[条件效应](kill_chain_guidance_mechanism_ablation_20260715_effects.csv)和
[自动摘要](kill_chain_guidance_mechanism_ablation_20260715_summary.md)。
本轮使用 `/home/void0312/Workshop/CMO/build/ef_py.cpython-313-x86_64-linux-gnu.so`。
当前工作树还包含此前未提交的 guidance cadence / held-command 重构；本批案例固定
`guidance_update_period_s=0`，因此 cadence 分支不是本次被测机制，但复现数据时必须
保留这一构建上下文。

## 主要结果

| 当前完整链 | 4 km | 6 km | 8 km |
|---|---:|---:|---:|
| `30 deg` 最近距 | `9.461 m` | `10.267 m` | `10.963 m` |
| `45 deg` 最近距 | `22.438 m` | `22.101 m` | `24.448 m` |

所有左右镜像 `30 deg` 单元都进入 `R_fuze=15 m`，所有 `45 deg` 单元都未进入。
左右对称性稳定：全部 `100` 对结果的最大最近距差小于 `0.000051 m`。

对 `4/6/8 km` 核心单元进行嵌套消融后，可以得到：

- lead 是主导且必要的机制。在 `capture + PN` 上加入 lead，`30 deg` 最近距减少
  `40.8..49.0 m`，`45 deg` 减少 `78.4..96.4 m`。
- PN 同样必要。在已有 lead 时加入 PN，`30 deg` 最近距减少 `5.8..10.3 m`，
  `45 deg` 减少 `6.0..45.2 m`。
- direct APN 加速度项不是近距残差 owner。在 `capture + PN + lead` 上加入 APN，
  `30 deg` 只改变 `0.19..0.29 m`，`45 deg` 只改变 `0.01..1.53 m`。

`45 deg` 失配是稳定的末段尾后超越，不是随机噪声。`4/6/8 km` 最近点在目标局部
forward 约为 `-19.2..-21.6 m`，横向约为 `11.0..11.4 m`，aspect 均为 `tail`；
末段平均指令约 `29 g`。指令饱和比例从 `4 km` 的 `0.477` 降到 `8 km` 的
`0.111`，但最近距仍保持在 `22..24 m`，因此不能把残差只归因于 `35 g` 限幅。

## 结构控制

| 变体 | 4 km / 45 deg | 6 km / 45 deg | 8 km / 45 deg | 16 km / 30 deg O 负控 |
|---|---:|---:|---:|---:|
| 完整 baseline | `22.438` | `22.101` | `24.448` | `17.010` |
| 移除 track filter | `19.120` | `18.206` | `19.400` | `12.703` |
| 近瞬时标量 autopilot | `20.078` | `21.520` | `23.735` | `16.148` |
| 二阶 autopilot | `25.279` | `22.843` | `25.024` | `17.331` |
| 三阶 autopilot | `35.878` | `24.537` | `25.767` | `18.690` |

移除 track filter 能让 `45 deg` 改善 `3.3..5.0 m`，但同时会把敏感的
`16 km / 30 deg` O 类负控推进 `15 m` 引信半径。这相当于扩大窗口，不能作为安全
收口方案。

近瞬时标量 autopilot 对核心 `45 deg` 只改善 `0.6..2.4 m`，没有任何单元进入
`R_fuze`；二阶、三阶标量 autopilot 反而退化。因此标量幅值滞后只是次要贡献，
改变 autopilot 阶次没有处理剩余的制导几何问题。

## 尚未闭合的机制问题

trace 暴露出两个高优先级结构不一致，但第一阶段门控消融还不能严格分离：

1. 导弹 Transform 航向基本停留在发射姿态，而速度航向在 `30 deg` 案例中已转动
   约 `47..52 deg`，在 `45 deg` 案例中已转动约 `75..80 deg`。capture 使用速度方向，
   PN/APN rate 项却通过导弹 `Transform` 转到世界系。相对方位角微分与坐标变换相互
   耦合，下一步必须直接实现世界系 LOS-rate 向量 PN，不能用外部强制姿态对齐替代。
2. 匀速目标产生了约 `22..29 g` 的目标加速度估计峰值。direct APN 被限制在约
   `5.4..6.1 g`，但同一个估计加速度还会进入未受该 APN 限制的二次 lead 预测。
   在把剩余尾后超越归因于这一项之前，必须比较 velocity-only lead 与
   velocity-plus-acceleration lead。

## 决策

当前 `45 deg -> M` 发射窗口分类仍然忠实描述当前 runtime，但这不等于机制闭合。
期望审计中的“无 nominal guidance residual”只表示分类已经贴合观测行为，不表示制导
机制已经校准。

本证据不支持增加 `N`、增加 `g` 或扩大 N 类窗口。下一批 exact mechanism 工作应冻结
全部标量并增加：

1. capture、PN、lead-velocity、lead-acceleration、APN 独立开关；
2. capture/PN/APN 向量、clamp 前总指令、clamp 后指令和实际加速度向量诊断；
3. 当前 frame PN 与世界系 LOS-rate 向量 PN 对照；
4. velocity-only lead、二次 lead 和匀速 truth-kinematics oracle；
5. 强制保持 `4/6/8 km / 30 deg` 正样本以及 `12 km / 45 deg`、
   `16 km / 30 deg` 负控。
