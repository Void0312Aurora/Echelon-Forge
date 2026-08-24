<!-- Machine-translated draft generated on 2026-05-18 from examples/config/Archive/training/leader_legacy/README.md. Review before treating this file as authoritative. -->

# 领导者遗留训练配置

此目录归档了之前位于 `examples/config/training/` 顶层目录中的冻结前领导者层训练配置。

- 范围：历史的 `p6_*` 和 `p7_*` 领导者实验。
- 状态：已归档；仅保留用于溯源和结果查找。
- 维护的基线：[examples/config/training/frozen](../../../training/frozen/README.md)

这些文件仍可能引用历史命名和较旧的实验意图。内部执行配置引用保持相对于已归档的冻结前配置位置的仓库相对路径，以便归档文件仍可被检视。新的训练运行应从冻结配置开始，而不是从此归档开始。

## 已退役文件（2026-08-13）

一次全仓库引用扫描移除了没有任何维护文档、测试、合同或工具指向的归档配置。可用
`git show 3ac600a6:examples/config/Archive/training/leader_legacy/<名称>` 取回：

- `p6_leader_layer_frozen_exec_smoke_v1.json`
- `p7_leader_layer_c2_reporting_baseline_v1.json`
- `p7_leader_layer_c2_reporting_generalization_batched_gpu_v1.json`
- `p7_leader_layer_c2_reporting_generalization_highcpu_v1.json`
- `p7_leader_layer_c2_task_chain_baseline_v1.json`
- `p7_leader_layer_c2_task_chain_earlystop_v1.json`
- `p7_leader_layer_c2_task_chain_fasttrack_v1.json`

其余配置因归档之外仍有引用而保留：`p6_leader_layer_frozen_exec_generalization_v1.json`、
`p7_leader_layer_c2_reporting_generalization_v1.json` 和
`p7_leader_layer_c2_reporting_generalization_fast_v2.json` 是
`examples/config/training/frozen/README.md` 中的谱系链接；
`p6_leader_layer_smoke_v1.json`、`p7_leader_layer_c2_reporting_smoke_v1.json` 和
`p7_leader_layer_c2_reporting_generalization_fast_v1.json` 被已归档的重架构笔记与
`tools/README.md` 引用。
