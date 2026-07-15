# 杀伤链制导校准热图

这些图只渲染已经封存的第四、第五阶段证据；未重跑仿真、
未修改 tuning，也未增加默认发布权威。所有热图均按离散采样单元绘制，
不对未采样区域做插值或平滑。

- 第四阶段来源：`docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_guidance_envelope_rebuild_20260715/kill_chain_guidance_envelope_rebuild_20260715.json`
- 第五阶段来源：`docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_guidance_scalar_calibration_20260715/kill_chain_guidance_scalar_calibration_20260715.json`
- 选择的 nav gain：`4.0`
- 默认发布状态：`held`

| 图 | Matrix CSV | PNG | SVG |
| --- | --- | --- | --- |
| `stage4_launch_class` | [kill_chain_guidance_calibration_stage4_launch_class_heatmap_20260715.csv](kill_chain_guidance_calibration_stage4_launch_class_heatmap_20260715.csv) | [kill_chain_guidance_calibration_stage4_launch_class_heatmap_20260715.png](kill_chain_guidance_calibration_stage4_launch_class_heatmap_20260715.png) | [kill_chain_guidance_calibration_stage4_launch_class_heatmap_20260715.svg](kill_chain_guidance_calibration_stage4_launch_class_heatmap_20260715.svg) |
| `stage4_log10_rho_edge` | [kill_chain_guidance_calibration_stage4_log10_rho_edge_heatmap_20260715.csv](kill_chain_guidance_calibration_stage4_log10_rho_edge_heatmap_20260715.csv) | [kill_chain_guidance_calibration_stage4_log10_rho_edge_heatmap_20260715.png](kill_chain_guidance_calibration_stage4_log10_rho_edge_heatmap_20260715.png) | [kill_chain_guidance_calibration_stage4_log10_rho_edge_heatmap_20260715.svg](kill_chain_guidance_calibration_stage4_log10_rho_edge_heatmap_20260715.svg) |
| `stage5_state_changes_vs_N4` | [kill_chain_guidance_calibration_stage5_state_changes_vs_N4_heatmap_20260715.csv](kill_chain_guidance_calibration_stage5_state_changes_vs_N4_heatmap_20260715.csv) | [kill_chain_guidance_calibration_stage5_state_changes_vs_N4_heatmap_20260715.png](kill_chain_guidance_calibration_stage5_state_changes_vs_N4_heatmap_20260715.png) | [kill_chain_guidance_calibration_stage5_state_changes_vs_N4_heatmap_20260715.svg](kill_chain_guidance_calibration_stage5_state_changes_vs_N4_heatmap_20260715.svg) |

## 图示结论

- 第四阶段主网格为 `N/M/O = 146/32/69`；N 与 O 分别形成连续内部和连续外部，M 是经过八邻域内缩后保留的过渡带。
- `60 deg` 主网格 robust-hit 区间为 `8-14 km`；近端 miss -> hit -> 远端 miss 是单一命中区间，不应解释成射程方向单调。
- 保守 `rho_edge` 的 robust-hit 中位数为 `9.19e-05`，robust-miss 范围为 `6.25` 到 `1.07e+03`；说明分类面主要是终端几何边界，而不是围绕 `rho=1` 的宽缓过渡。
- 第五阶段的状态变化全部显示在基线命中边界附近；stage-4 N/O 硬门未被破坏。
- 非基线候选的最大角边界位移取值为 `5 deg`，预注册上限为 `2.5 deg`；低增益以丢失命中单元换取较低饱和，高增益扩张边界但提高饱和。
- holdout hit 只作为观察量，不计为材料性收益。因此热图支持保留 `nav_gain=4`，但不解除机动目标/APN 权威缺口。

## 第五阶段面板指标

| nav_gain | Main net hit | Holdout hit | Theta shift deg | Saturation P95 delta |
| ---: | ---: | ---: | ---: | ---: |
| 3.5 | -8 | -9 | 5 | -0.029 |
| 3.75 | -7 | -1 | 5 | -0.015 |
| 4.25 | +3 | 0 | 5 | +0.002 |
| 4.5 | +5 | +5 | 5 | +0.010 |

解释边界：这里只是工程校准诊断，不是真实武器性能、目标易损性或 Pk 权威。
