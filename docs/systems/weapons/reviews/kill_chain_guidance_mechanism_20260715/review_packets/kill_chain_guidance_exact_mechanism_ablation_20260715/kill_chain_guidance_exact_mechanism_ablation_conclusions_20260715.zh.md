# 杀伤链严格制导机制消融结论 — 2026-07-15

## 结论摘要

本轮不是继续调 `N`、过载上限或 APN 增益，而是在冻结 `N=4`、`35 g`、
`APN gain=0.5` 后，对 capture、PN、速度 lead、加速度 lead、目标运动学来源和
APN 做严格离散开关。共运行 `20` 个左右镜像匀速案例、`16` 个机制 profile，
合计 `320` 次确定性仿真；另以第二 seed 对 `16` 个关键运行做复核，最近距逐项相同。

核心结论是：当前 `45 deg -> M` 并非纯参数校准结果。它同时吸收了旧 PN 坐标系
耦合、目标运动学估计误差以及 capture 对发射窗口的隐式整形。世界系 PN 是实质机制
修正候选，但不能在保留旧 N/M/O 标签不变的前提下直接落为生产默认，因为它在改善
`45 deg` 的同时击穿 `16 km / 30 deg` O 负控。旧负控本身又是在旧机制上得到的，
所以“击穿旧负控”不能单独证明世界系 PN 不合理；正确做法是先修正机制，再重新标定
窗口整形与分类，而不是继续用旧 PN 的方向衰减充当隐式窗口门控。

## 证据与边界

保留工件如下：

- [JSON 报告](kill_chain_guidance_exact_mechanism_ablation_20260715.json)
- [逐次结果](kill_chain_guidance_exact_mechanism_ablation_20260715_rows.csv)
- [左右镜像 pair 均值](kill_chain_guidance_exact_mechanism_ablation_20260715_pairs.csv)
- [匹配条件效应](kill_chain_guidance_exact_mechanism_ablation_20260715_effects.csv)
- [自动摘要](kill_chain_guidance_exact_mechanism_ablation_20260715_summary.md)

该 profile 只在发射后、首次制导更新前显式附着到单枚导弹。正常导弹没有该组件，
未修改武器数据库、发射服务或生产默认参数。lead 在这里仍保持现有机制语义：它只改变
capture aimpoint，不是一条独立加速度命令。

## 实现与测量验收

| 检查 | 结果 |
| --- | ---: |
| 未附着 baseline 与 all-enabled legacy profile 最大最近距差 | `0.0 m` |
| 全矩阵最大左右镜像差 | `0.00005075 m` |
| capture / PN / APN 禁用后对应最大分量 | `0.0 g` |
| `preclamp = capture + PN + APN` 最大向量闭合误差 | `4.55e-12 m/s^2` |
| 总指令限幅后最大值 | `35.00000000000001 g` |
| truth-CV 下 velocity/quadratic lead 差 | `0.0 m` |
| truth-CV 下 APN off/on 差 | `0.0 m` |
| capture 关闭后 lead off/on 差 | `0.0 m` |

上述不变量说明本轮测到的是离散机制差异，不再是上一轮 epsilon 增益的近似门控。

## 当前 baseline

| 单元 | `4 km` | `6 km` | `8 km` |
| --- | ---: | ---: | ---: |
| `30 deg` 最近距 | `9.461 m` | `10.267 m` | `10.963 m` |
| `45 deg` 最近距 | `22.438 m` | `22.101 m` | `24.448 m` |

`12 km / 45 deg` 为 `48.462 m`，`16 km / 30 deg` 为 `17.010 m`。因此当前
baseline 保持全部 N30 正样本进入 `R_fuze=15 m`，并保持两个 O 负控在外。

## 机制归因

### 1. lead 的真实 owner 是 capture-lead 复合链

从当前链中移除 lead，N30 最近距恶化 `39.955..47.998 m`，M45 恶化
`77.932..93.167 m`。lead 仍是主导必要机制，但严格不变量显示：capture 关闭后，
lead off/on 的逐案差为 `0.0 m`。因此 lead 不是独立控制力，它只通过 capture
aimpoint 生效。

capture 自身不是单调“越多越好”的机制：

- 移除 capture 会让 N30 反而改善 `9.058..10.959 m`；
- 却会让 M45 恶化 `5.786..83.495 m`；
- 在 `16 km / 30 deg`，移除 capture 会把最近距从 `17.010 m` 推到
  `0.024 m`。

这说明 capture 同时承担末段收敛和发射窗口整形。当前 O 类边界的一部分不是由纯
运动学不可达性产生，而是由 capture / PN 的非线性交互产生。

### 2. PN 是必要机制，但现有 PN frame 会随姿态-速度失配衰减

从当前链中移除 PN，N30 恶化 `5.718..9.753 m`，M45 恶化
`6.110..32.644 m`，因此 PN 不可删除。

只把旧 `body angle-rate + Transform` PN 换成世界系 LOS-history PN，并继续使用
同一个 filtered LOS 与 filtered closing speed，可得到：

| 单元 | 当前 legacy PN | 世界系 LOS-history PN | 改善 |
| --- | ---: | ---: | ---: |
| `4 km / 45 deg` | `22.438 m` | `16.736 m` | `5.702 m` |
| `6 km / 45 deg` | `22.101 m` | `16.472 m` | `5.629 m` |
| `8 km / 45 deg` | `24.448 m` | `17.034 m` | `7.414 m` |
| `12 km / 45 deg` | `48.462 m` | `21.752 m` | `26.710 m` |
| `16 km / 30 deg` | `17.010 m` | `12.030 m` | `4.980 m` |

这直接验证了上一轮观察到的 Transform heading 与速度航向分离不是旁支现象，而是
有效 PN 指令被方向投影削弱的机制问题。世界系 PN 显著改善 M45，但也把 O_far 推入
`R_fuze`，因此不能把它当作只修 45°、不影响窗口的局部补丁。

### 3. track 运动学误差贡献了剩余残差，但 truth-CV 是 oracle，不是生产方案

在世界系解析 PN 下，将 track 运动学替换为 truth-CV：

| 单元 | track analytic | truth-CV analytic | 改善 |
| --- | ---: | ---: | ---: |
| `4 km / 45 deg` | `18.760 m` | `15.639 m` | `3.121 m` |
| `6 km / 45 deg` | `18.678 m` | `14.708 m` | `3.970 m` |
| `8 km / 45 deg` | `19.257 m` | `14.843 m` | `4.414 m` |
| `12 km / 45 deg` | `27.819 m` | `16.528 m` | `11.291 m` |
| `16 km / 30 deg` | `13.883 m` | `9.503 m` | `4.380 m` |

因此 track 速度链约解释核心 M45 的 `3.1..4.4 m` 残差。truth-CV 能让
`6/8 km / 45 deg` 进入 `15 m`，但同时进一步扩大旧窗口，不能直接进入生产链。

另一个重要结果是：用当前 track 速度做 analytic PN 并不优于 LOS-history PN；在
M45 上平均还恶化约 `1.040 m`。这说明下一步不能只把 PN 公式改成解析式，还必须先
处理 track 速度质量和坐标契约。

### 4. 加速度 lead 与 direct APN 都不是 45°主 owner

- quadratic 相对 velocity-only lead 在 legacy M45 只改善
  `1.395..1.699 m`；在世界系版本约改善 `1.0..1.2 m`。
- direct APN 在核心 M45 只改善 `0.012..1.531 m`，N30 只改善
  `0.192..0.294 m`。
- truth-CV 加速度严格为零时，quadratic/velocity 和 APN off/on 的最近距都逐案
  完全相同。

因此不能继续把 45°残差解释为“APN 增益不足”或“二次 lead 不够强”。

## 对当前校准结果的判断

1. **作为现有 runtime 的描述，当前 `45 deg -> M` 是可复现的。** all-enabled
   exact profile 与未附着 baseline 完全一致，N30/O 控制也复现。
2. **作为机制合理性结论，它不闭合。** 当前窗口吸收了旧 PN frame 衰减、track
   估计误差和 capture 窗口整形，不能被解释成单纯的 `N=4`、`35 g` 参数结果。
3. **世界系 PN 更接近应有的坐标机制，但不能直接以旧标签验收。** 旧 O 负控是基于
   legacy PN 形成的；如果机制修正改变可达域，必须重新推导 N/M/O envelope。
4. **当前不修改生产默认。** 在 capture 窗口整形和新 envelope 重标定完成前，保留
   legacy runtime 仅是兼容性决策，不是对旧机制的物理背书。

## 下一步

1. 把世界系 LOS-history PN 作为生产候选单独实现，并增加“改变 Transform heading、
   保持世界位置和速度不变时 PN 输出不变”的坐标不变量测试。
2. 对 capture law 做下一轮严格消融，重点分解 terminal weight、range scaling 和
   lead blend；它现在是 N/M/O 窗口整形的主要 owner。
3. 增加 track-vs-truth 位置、速度和 LOS-rate 误差时间序列，定位当前估计器为何使
   analytic PN 比 LOS-history PN 更差。
4. 在修正后的 PN + capture 组合上重新生成 `4..16 km x 0..90 deg` envelope，
   然后再决定 `45 deg` 和 `16 km / 30 deg` 的分类；禁止用旧标签反向约束新机制。

## 权威边界

本结论只诊断当前工程 runtime。它不授予真实 AIM-120 制导律、真实发射包线、Pk、
确定性引信或 stock weapon/target lethality authority。
