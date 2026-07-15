# 第五阶段：制导标量约束校准结论

## 可识别性边界

本阶段只对 `nav_gain` 做 OFAT。capture 已关闭，APN 在 CV 目标下不可识别，
tracker alpha/beta 已在第二阶段冻结，35g 是约束而不是优化变量。

## 约束与判据

- 阶段4的 N 必须保持 robust hit，O 必须保持 robust miss。
- M 只观察，不施加二值优化压力。
- 半步长网格独立于阶段4主网格，仅用于观察边界外推；更多 hit 不计为收益。
- 镜像差、seed spread、capture=0、35g、runtime contract 与单命中带均为硬门。
- 相对 N=4，theta 最大位移不得超过 2.5deg，minimum/maximum range 边界最大位移不得超过 0.5km。
- 非基线候选还必须在无实质回归的前提下达到预注册的材料性改善阈值。
- release gate 独立于标量选择：world_cv tracker 的 `acceleration_world_mps2` 当前固定为 0，阶段4/5只有 CV authority。

## 候选结果

| nav gain | hard gate | clear net benefit | N violations | O violations | holdout hits(obs) | saturation P95 | theta shift | range shift min/max |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 3.5 | True | False | 0 | 0 | 134 | 0.235897436 | 5 | n/a/n/a |
| 3.75 | True | False | 0 | 0 | 142 | 0.249122807 | 5 | n/a/n/a |
| 4 | True | False | 0 | 0 | 143 | 0.26446281 | 0 | 0/0 |
| 4.25 | True | False | 0 | 0 | 143 | 0.266173752 | 5 | 1/2 |
| 4.5 | True | False | 0 | 0 | 148 | 0.274261603 | 5 | n/a/n/a |

## 选择

- selected nav gain：`4`。
- decision：`retain_nav_gain_4_no_clear_net_benefit`。
- selected hard gate：`True`。
- scalar selection passed：`True`。
- default promotion ready：`False`；当前 held，原因是 maneuver/APN authority 尚未建立。

该选择仅对当前确定性 CV 工程校准域有效，不构成真实武器性能或交战权威。
