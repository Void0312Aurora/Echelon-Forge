# 第四阶段：连续发射窗口重建结论

本阶段使用生产候选 tuning，未附加 diagnostics mechanism profile。
候选为世界系 LOS-history PN、世界系 CV tracker、capture guidance 关闭；
`N=4`、`35 g`、`APN=0.5` 保持冻结。

## 采样与分类

- 主网格：`247` 个 unsigned cell，`1443` 次 signed/seed run。
- refinement：`105` 个 cell，`630` 次 run；状态变化边 `16` 条。
- robust 状态：`{'robust_hit': 162, 'robust_miss': 85}`。
- 新 N/M/O：`{'M': 32, 'N': 146, 'O': 69}`。
- N/O 采用 8 邻域内缩定义，边界、mixed 和异状态邻接统一归入 M。

## theta_fuze(range)

| range km | 最大 robust-hit angle | 首个 robust-miss angle | 状态 |
|---:|---:|---:|---|
| 4 | 52.5 | 55 | bracketed_or_mixed |
| 5 | 55 | 57.5 | bracketed_or_mixed |
| 6 | 57.5 | 60 | bracketed_or_mixed |
| 7 | 57.5 | 60 | bracketed_or_mixed |
| 8 | 60 | 62.5 | bracketed_or_mixed |
| 9 | 60 | 62.5 | bracketed_or_mixed |
| 10 | 60 | 62.5 | bracketed_or_mixed |
| 11 | 60 | 62.5 | bracketed_or_mixed |
| 12 | 60 | 62.5 | bracketed_or_mixed |
| 13 | 60 | 62.5 | bracketed_or_mixed |
| 14 | 60 | 62.5 | bracketed_or_mixed |
| 15 | 57.5 | 60 | bracketed_or_mixed |
| 16 | 57.5 | 60 | bracketed_or_mixed |

## 固定 angle 的 minimum/maximum range 边界

| angle deg | min robust-hit km | max robust-hit km | hit interval count |
|---:|---:|---:|---:|
| 0 | 4 | 16 | 1 |
| 5 | 4 | 16 | 1 |
| 10 | 4 | 16 | 1 |
| 15 | 4 | 16 | 1 |
| 20 | 4 | 16 | 1 |
| 25 | 4 | 16 | 1 |
| 30 | 4 | 16 | 1 |
| 35 | 4 | 16 | 1 |
| 40 | 4 | 16 | 1 |
| 45 | 4 | 16 | 1 |
| 50 | 4 | 16 | 1 |
| 55 | 4.5 | 16 | 1 |
| 60 | 8 | 14 | 1 |
| 65 | n/a | n/a | 0 |
| 70 | n/a | n/a | 0 |
| 75 | n/a | n/a | 0 |
| 80 | n/a | n/a | 0 |
| 85 | n/a | n/a | 0 |
| 90 | n/a | n/a | 0 |

range 方向允许 minimum-range miss -> hit -> maximum-range miss；
只有 robust-hit 分裂成两个以上区间才登记为多岛。

## 拓扑与不变量审计

- 主网格固定 range 的 angle miss->hit 反转：`0`。
- 主网格固定 angle 的多 robust-hit 区间：`0`。
- 加入 refinement 后的 sampled angle 反转 / range 多区间：`0` / `0`。
- robust-hit 连通分量 / 内部 holes：`1` / `0`。
- robust-miss 连通分量 / 内部 holes：`1` / `0`。
- 全域 robust hit：`False`；全域 robust miss：`False`。

工具不会对非单调、多岛、hole 或全域命中做平滑或后处理掩盖。

## 旧标签差异与运行约束

- 旧->新标签计数：`{'M->M': 3, 'M->N': 9, 'M->O': 1, 'N->N': 12, 'O->M': 3, 'O->N': 3, 'O->O': 11}`。
- 最大左右镜像最近距差：`0.000114146749 m`。
- 左右镜像 hit/miss 分类一致：`True`。
- 最大 seed spread：`0 m`。
- 最大 capture component：`0 g`。
- 最大 preclamp command：`128.184665 g`。
- 最大 postclamp command：`35 g`。
- 单案最大饱和采样比例：`0.521621622`。
- 最大 achieved lateral acceleration：`35 g`。
- diagnostics profile attached run：`0`。
- runtime observation / acceleration diagnostics missing run：`0` / `0`。
- resolved runtime contract mismatch run：`0`。
- data integrity：`PASS`。
- stage-4 shape gate：`PASS`。

该结果只说明当前仿真机制下的工程窗口；不构成真实武器射程、Pk 或交战规则权威。
