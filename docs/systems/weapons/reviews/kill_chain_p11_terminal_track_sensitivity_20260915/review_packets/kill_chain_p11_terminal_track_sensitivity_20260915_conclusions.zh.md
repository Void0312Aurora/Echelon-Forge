# P11 terminal-track 记忆窗口敏感性结论

- 状态：`p11_terminal_track_memory_sensitivity_explained`；残差解释可用：`True`。
- 矩阵：`48` runs / `16` 个跨三种子稳定 cells。
- run 状态：`{'complete_effect_chain': 12, 'in_radius_fuze_blocked': 24, 'outside_no_load': 12}`。
- 基准 `track_break_time_s=0.75 s` 重现两个 `in_radius_fuze_blocked`；扩大记忆窗口后，若进入 `complete_effect_chain`，只能说明该残差对记忆窗口敏感，不等于默认值应被修改。
- 所有 cells 的 timeout 响应单调：`True`。

结论：该批把 `seeker_fov_exit_then_memory_timeout` 量化为一个可复现的记忆窗口边界问题。它没有证明 0.75 s 是错误值，也没有授权放宽 seeker FOV、terminal fuze门或生产默认配置；P11 仍保持 incomplete，后续应由独立 runtime contract 决定是否调整。
