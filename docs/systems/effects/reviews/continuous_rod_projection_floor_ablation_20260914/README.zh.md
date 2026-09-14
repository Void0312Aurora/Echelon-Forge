# 连续杆 P7：projection 最小值钳制成对消融（2026-09-14）

## 结论

P7 的成对消融完成，但**未通过准入**。相同的 192 个连续杆显式环带案例、相同 seed、相同姿态和相同 `720 × 5` 射线采样，分别运行：

- 当前基线：`projection_min_effect_scale = 0.05`；
- 消融：`projection_min_effect_scale = 0.00`。

结果证明：当前字段同时承担两种语义：

1. `projected_spatial_effect_scale()` 的曲线截距；
2. 最终 `std::clamp()` 的 effect 下界。

因此把它降到 0 并不是“只取消尾部钳制”，而是会让完整空间效应曲线整体下移。

## 硬门结果

| 门 | 结果 | 数值 |
| --- | --- | --- |
| 完整成对矩阵 | 通过 | `192 / 192` |
| 几何相交拓扑不变 | 通过 | `0` 个相交/部件行集合变化 |
| 代表 trace 稳定 | 通过 | 当前 tie-break 后 `0` residual；历史耦合运行曾有 `8` 个切换 |
| 仅尾部应用 floor | 未通过 | `96` 个非钳制命中仍改变 effect |
| 机制载荷不变 | 通过 | `220 / 220` 个 `rod_cut_margin` 无变化 |
| component load effect 传播 | 通过 | `220 / 220` 行发生变化 |
| response 概率传播 | 通过 | `180 / 220` 行变化；failure mode `0` 翻转 |
| P7 projection floor/clamp 准入 | **held** | 需要 P7.1 |

效应差异统计：所有几何命中案例的基线减消融 effect 均值为 `0.01839`，最大 `0.04782`；其中 24 个基线 clamp 案例均值 `0.04172`，但另外 96 个非钳制命中仍有均值 `0.01256` 的变化。10 m 的 24 个命中案例从统一的 `0.05` 释放到 `0.00218–0.01080` 的范围。

![连续杆 projection floor 消融热力图](continuous-rod-projection-floor-ablation.png)

## 传播解释

`rod_cut_margin` 由环带覆盖率、杆件能量和部件几何机制载荷计算，与投影 effect 下界分离，所以这次消融不会改变它。另一方面，component load row 的 `effect_scale` 直接跟随投影 effect，随后影响非直击 vulnerability response：220 个 response row 中 180 个 failure probability 改变，192 个 integrity-after 改变，但当前样本没有 failure mode 翻转。

因此不能用“消融后没有 failure mode 翻转”证明 floor 无害；它已经改变了概率和完整性，只是尚未跨过离散 failure-mode 阈值。

历史运行中的 8 个代表 trace 切换属于并列候选的诊断选择问题，而不是底层几何变化。当前实现已用 `preclamp_effect_scale` 作为确定性 tie-breaker；复跑后的代表 trace residual 为 `0`，但耦合消融仍然改变了 96 个非钳制命中的 effect，因此 P7 的 floor-only 准入仍保持 held。

## 后续 P7.1

新增一个独立的可选字段，例如 `projection_curve_floor_effect_scale`，使曲线截距和最终最小下界可以分别控制：

- 曲线 floor 保持当前标定值 `0.05`；
- final minimum bound 单独消融到 `0.00`；
- 以上解耦实验已在独立报告中完成：非钳制 effect 与代表 trace 均保持稳定；
- 下一步把 10 m 载荷变化推进到 P8 Component Load Admission。

P7.1 报告：`../continuous_rod_projection_curve_floor_decoupling_20260914/README.zh.md`。即使 P7.1 通过，也不应将连续杆默认 profile 的最小值改为 0，或提升整体 Warhead Spatial Field/真实武器 Pk 准入。

## 复现

```powershell
$env:CMO_BUILD_DIR = 'D:\workshop\Research\Echelon-Forge\build-warhead-spatial-admission-vs'
python tools/geometry/continuous_rod_projection_floor_ablation.py
python tools/geometry/render_continuous_rod_projection_floor_ablation.py
```

机器可读证据位于 `review_packets/continuous_rod_projection_floor_ablation_20260914.json`。
