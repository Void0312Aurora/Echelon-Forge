# P11 集成杀伤链准入结论

- 总状态：`integrated_structure_passed_residuals_open`。
- P11 结构准入：`True`；P11 complete：`False`。
- 独立审核接受的 N/M/O 包络：`True`；terminal-track contract：`False`。
- 三种子 anchor：`279` runs / `93` cells；结构违规 `0`。
- 完整触发链：`189` runs；未触发且无 load/response：`90` runs。
- O 类负控告警：`0` cells；N 类制导残差：`0` cells。
- 已进入 R_fuze 但 terminal-track 未闭合：`2` cells。
- terminal-track 残差原因：`seeker_fov_exit_then_memory_timeout`=2。目标越过诊断场景的 ±90 deg seeker FOV 后进入 Memory，超时后转为 Ballistic；未修改视场或放宽引信终端跟踪门。

本批证明 config-backed guidance→fuze→warhead load→component response→platform consequence 的运行时结构闭合，独立审核已接受重基线后的 N/M/O 包络。近距 terminal-track runtime contract 仍未裁定，因此不声明完整 P11 通过。

所有数据仍是 synthetic engineering evidence，不构成真实 AIM-120、F-16C、确定性引信或 Pk 权威。
