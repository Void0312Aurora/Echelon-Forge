# P11 期望重基线独立审核接受记录

审核日期：2026-09-15  
审核方式：独立 agent 只读复核；按项目决策等效人工审核  
审核基线：`5ae8e06ae5a8a0cfcaac34f157800b42b90c2eda`  
Verdict：`accept-with-residuals`

## 接受范围

- 接受 93-cell 候选 N/M/O 重基线：`N=63, M=2, O=28`。
- 允许 expectation harness 精确采用候选矩阵。
- 两个 mild-maneuver、6 km、±60 deg cell 必须保留为 M：
  - `kces_anchor_grid_mild_6km_m60deg`
  - `kces_anchor_grid_mild_6km_p60deg`
- 两个 residual 的原因必须保留为 `seeker_fov_exit_then_memory_timeout`。
- 接受范围仅覆盖 synthetic engineering expectation contract，不构成真实 AIM-120、
  确定性引信、lethality 或 Pk 权威。

## 独立复核结果

- 集成证据为 279 个唯一 `(case_id, seed)` runs、93 个唯一 cells；每个 cell
  均包含 `20260621/20260622/20260623` 三个种子。
- 279 runs 均为 `structural_consistent=true`。
- 独立重算结果为 189 runs / 63 cells `complete_effect_chain`，6 runs / 2 cells
  `in_radius_fuze_blocked`，84 runs / 28 cells `outside_no_load`。
- 49 个标签变化与逐 cell 候选映射一致；角度拓扑无镜像不一致或 miss-to-hit
  离轴逆转。
- terminal-track 敏感性矩阵为完整的 2 cases × 8 timeouts × 3 seeds：
  `0.25–0.50 s` 为 outside，`0.75–2.00 s` 为 in-radius blocked，
  `3.00–5.00 s` 为 complete chain。
- 敏感性只解释残差依赖记忆窗口，不证明 `0.75 s` 错误，也不授权采用
  `3.0 s` 生产默认值。

## 审核发现与处置

- High：无。
- Medium：重基线和 timeout 敏感性门禁需要验证唯一 case/seed、完整笛卡尔积、
  每 cell 精确种子集合、残差原因非空，以及两个镜像 case 均观察到恢复；在采用
  新 harness 时补强。
- Low：集成报告的空 `outcome_state` 应规范为相应 chain state，以提高下游 JSON
  工具兼容性。

## 未接受事项

- P11 complete 仍为 `false`。
- 不允许修改 `track_break_time_s`、seeker FOV、terminal-fuze support gate 或
  AIM-120 数据库定义。
- 剩余实质阻塞是 terminal-track runtime contract：需要独立评估延长 memory
  对陈旧航迹风险、跟踪语义和引信安全边界的影响。
