# PF-R5 近炸引信 Surrogate 验证结果

状态：`2026-06-16`，PF-R5 聚焦矩阵验证完成。

验证决策：`pass_with_residuals`。

## 验证范围

- live missile / fuze runtime path；
- 机制族：`blast_fragmentation` 与 `continuous_rod`；
- 触发半径：`7, 8, 10, 12, 16, 24, 35, 50 m`；
- 初始横向偏置：`-120..120 m`；初始高度偏置：`-80..80 m`；
- 输出为最终 CSV、JSON 和一张热图，不保留额外中间结果。

## 主要结论

- 触发半径/实际最近距离比值能清楚打开或关闭探测门；小半径下出现 `target_not_detected` 和 no-load。
- 中心样本的 no-load-aware 期望起爆概率随触发半径单调不下降。
- 横向/高度初始偏置的影响较弱，因为导弹制导会补偿一部分初始几何差异；实际最近距离集中在 `6.58` 到 `8.33` m。
- 横向左右不完全对称不是本验证的失败条件：这里扫的是发射初始条件，制导、目标运动和机体朝向仍在链路中；若要验纯引信几何对称性，需要另建固定局部命中点 harness。
- `continuous_rod` 与 `blast_fragmentation` 共用探测门，但可通过 mechanism coverage 产生机制差异。
- 本验证仍不声明真实引信阈值、真实 Pk、具体弹种杀伤或 deterministic fuze authority。

## 输出

- CSV: `pf_r5_proximity_fuze_validation_20260616.csv`
- JSON: `pf_r5_proximity_fuze_validation_20260616.json`
- Heatmap: `pf_r5_proximity_fuze_validation_heatmaps_20260616.png`
