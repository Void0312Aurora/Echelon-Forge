# P10 APN 8 km 低响应带复核结论

- Discussion：[#32](https://github.com/Void0312Aurora/Echelon-Forge/discussions/32)。
- 状态：`p10_apn_null_band_explained`；机制闭合：`True`。
- 矩阵：`120` runs / `20` cells，三种子、两组镜像困难角点。
- 8 km 的 APN=0 平均最近距为 `0.001402 m`；所有非零增益相对基线的最大绝对变化为 `5.407637e-05 m`。
- 8 km 非零增益的最小峰值 APN 分量为 `0.234971 m/s²`；估计器最迟在 `3.117 s` 收敛，距最近点仍有至少 `13.571 s`。
- 全部非零增益均落入 null threshold 的范围：`[7.0, 7.5, 8.0, 8.5]` km。
- 扫描中的首个高于 8 km 的非 null 距离为 `9.0` km。

结论：8 km 不是孤立异常，而是 7.0-8.5 km 低响应带的一部分；纯 PN 基线已经落在厘米以下的数值/几何观测底部，9 km 基线离开该底部后 APN 响应恢复。CVA 与 APN 均在最近点前生效，因此不是 APN 接线失效或估计器瞬态造成。这一解释只覆盖当前 synthetic 固定机动角点，不改变 P10 准入，也不构成真实 AIM-120 性能或 Pk 权威。
