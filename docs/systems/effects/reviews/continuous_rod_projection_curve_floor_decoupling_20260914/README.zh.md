# 连续杆 P7.1：解耦投影曲线 floor 与最终下界（2026-09-14）

## 结论

P7.1 已通过结构性准入。新增的 `projection_curve_floor_effect_scale` 使“投影曲线截距”和“最终 `min_effect_scale` 下界”可以分别控制。完整 192 对连续杆显式环带案例采用：

- 基线：曲线 floor `0.05`、最终下界 `0.05`；
- 解耦消融：曲线 floor 保持 `0.05`、最终下界降至 `0.00`。

这次对照只释放最终下界，不再改变非钳制距离曲线。

## 硬门结果

| 门 | 结果 | 数值 |
| --- | --- | --- |
| 完整矩阵 | 通过 | `192 / 192` |
| 几何/命中拓扑不变 | 通过 | `0` residual |
| 非钳制 effect 稳定 | 通过 | `0` 个变化 |
| 代表 trace 稳定 | 通过 | `0` 个变化（primary/component/system/group） |
| 机制载荷不变 | 通过 | `0` 个 `rod_cut_margin` residual |
| 下游传播 | 通过 | 36 个 component load effect、12 个 response 概率/完整性变化 |
| P7.1 曲线/下界解耦 | **passed** | 结构测试通过 |

命中案例仍为 `120` 个。基线被钳制的 `24` 个案例在解耦消融后全部释放；命中案例的 effect 差均值为 `0.0034775`，最大 `0.0314088`。非钳制命中案例保持逐格一致。

![连续杆曲线 floor 与最终下界解耦热力图](continuous-rod-projection-curve-floor-decoupling.png)

## 实现语义

profile 未设置新字段时，内部曲线 floor 自动跟随原 `projection_min_effect_scale`，保持旧行为和旧基线兼容。只有同时设置 `projection_curve_floor_effect_scale = 0.05` 与 `projection_min_effect_scale = 0.00` 时，才形成真正的 final-bound-only 消融。

此外，事件级代表 trace 的并列选择现在以 `preclamp_effect_scale` 作为稳定 tie-breaker。这样最终下界的变化不会把诊断代表从一个几何相交部件切换到另一个部件。

## 边界

这仍然是合成结构证据，不是实际武器标定。`0.05` 曲线 floor 和 `0.00` 消融下界都不是现实武器参数；component-load topology、vulnerability/consequence 和集成制导/引信/Pk 仍未准入。

下一批进入 P8 Component Load Admission：固定已解耦的空间投影语义，逐部件检查 `rod_cut_margin`、component load、冗余组和响应拓扑是否连续、可解释，并继续保留默认 profile promotion 的独立边界。

## 复现

```powershell
$env:CMO_BUILD_DIR = 'D:\workshop\Research\Echelon-Forge\build-warhead-spatial-admission-vs'
python tools/geometry/continuous_rod_projection_curve_floor_decoupling.py
python tools/geometry/render_continuous_rod_projection_floor_ablation.py `
--report artifacts/kill_chain/20260915/raw_review_packets/continuous_rod_projection_curve_floor_decoupling_20260914/continuous_rod_projection_curve_floor_decoupling_20260914.json `
  --output docs/systems/effects/reviews/continuous_rod_projection_curve_floor_decoupling_20260914/continuous-rod-projection-curve-floor-decoupling.png
```

原始机器可读 packet 留存在仓库外部的 artifact retention surface；仓库内只保留
结论和 manifest 作为审查入口。
