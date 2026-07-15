# 第二阶段：世界系 CV 目标运动估计验收

结论：问题属于坐标与测量时间语义，不是只调球坐标滤波 tau。
候选采用新鲜时间戳校正、世界系 CV 外推、速度成熟门控和零加速度 CV 层。

- 选定参数：`alpha=0.20`, `beta=0.02`, 速度基线 `0.5 s`。
- clean position/velocity RMSE：`4.166 m` / `0.168 m/s`。
- 20 Hz 默认噪声 position/velocity RMSE：`7.073 m` / `12.980 m/s`。
- 默认噪声 LOS-rate RMSE：`3.056 mrad/s`。
- CV 假加速度 P95：`0.000000 m/s²`。
- clean M45 track-vs-truth oracle 最大最近距差：`0.763 m`。
- N30 最大最近距：`7.484 m`。

验收门：

- `clean_position_rmse_below_10m`: PASS
- `clean_velocity_rmse_below_2mps`: PASS
- `clean_false_accel_p95_below_0p5mps2`: PASS
- `noisy_position_rmse_below_40m`: PASS
- `noisy_velocity_rmse_below_20mps`: PASS
- `noisy_los_rate_rmse_below_5mradps`: PASS
- `noisy_false_accel_p95_below_3g`: PASS
- `duplicate_measurements_never_corrected`: PASS
- `clean_track_truth_oracle_gap_below_1p5m`: PASS
- `nominal_cells_inside_fuze`: PASS
- `nominal_mirror_delta_below_1mm`: PASS

候选仍保持可选择状态；最终是否写入 AIM-120 默认配置留到第五阶段。
