# CUDA Resident Program 2 测试夹具

语言版本：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

该目录保存 CUDA 驻留 runtime-profile 测试消费的字节稳定证据、裁决和阶段冻结
记录。它是测试夹具，不是当前计划或文档权威。

建议阅读顺序：

1. [cuda_resident_backend_program_20260729.zh.md](cuda_resident_backend_program_20260729.zh.md)
2. [cuda_resident_backend_iteration_log_20260729.zh.md](cuda_resident_backend_iteration_log_20260729.zh.md)
3. [cuda_resident_rb10_hold_decision_20260731.zh.md](cuda_resident_rb10_hold_decision_20260731.zh.md)
4. [cuda_resident_rb11_closure_20260731.zh.md](cuda_resident_rb11_closure_20260731.zh.md)
5. [cuda_resident_runtime_program_2_20260731.zh.md](cuda_resident_runtime_program_2_20260731.zh.md)
6. [cuda_resident_runtime_program_2_iteration_log_20260731.zh.md](cuda_resident_runtime_program_2_iteration_log_20260731.zh.md)
7. [cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)
8. [cuda_resident_cr2_resource_evidence_20260804.zh.md](cuda_resident_cr2_resource_evidence_20260804.zh.md)
9. [cuda_resident_cr2_resource_evidence_20260804.json](cuda_resident_cr2_resource_evidence_20260804.json)
10. [cuda_resident_cr2_counter_evidence_20260804.zh.md](cuda_resident_cr2_counter_evidence_20260804.zh.md)
11. [cuda_resident_cr2_counter_evidence_20260804.json](cuda_resident_cr2_counter_evidence_20260804.json)
12. [cuda_resident_cr2_matrix_evidence_20260804.zh.md](cuda_resident_cr2_matrix_evidence_20260804.zh.md)
13. [cuda_resident_cr2_matrix_evidence_20260804.json](cuda_resident_cr2_matrix_evidence_20260804.json)
14. [cuda_resident_cr2_closure_20260805.zh.md](cuda_resident_cr2_closure_20260805.zh.md)
15. [cuda_resident_cr2_closure_20260805.json](cuda_resident_cr2_closure_20260805.json)
16. [cuda_resident_promotion_program_20260808.zh.md](cuda_resident_promotion_program_20260808.zh.md)
17. [cuda_resident_cp_resource_evidence_20260810.json](cuda_resident_cp_resource_evidence_20260810.json)
18. [cuda_resident_cp_counter_evidence_20260810.json](cuda_resident_cp_counter_evidence_20260810.json)
19. [cuda_resident_cp6_learner_consumption_design_20260812.zh.md](cuda_resident_cp6_learner_consumption_design_20260812.zh.md)
20. [cuda_resident_cp7_small_batch_disposition_prep_20260812.zh.md](cuda_resident_cp7_small_batch_disposition_prep_20260812.zh.md)
21. [cuda_resident_cp8_rematrix_kickoff_20260812.zh.md](cuda_resident_cp8_rematrix_kickoff_20260812.zh.md)
22. [cuda_resident_cp8_matrix_evidence_20260812.json](cuda_resident_cp8_matrix_evidence_20260812.json)
23. [cuda_resident_cp9_promotion_decision_20260813.zh.md](cuda_resident_cp9_promotion_decision_20260813.zh.md)
24. [cuda_resident_cp9_promotion_decision_20260813.json](cuda_resident_cp9_promotion_decision_20260813.json)
25. [gpu_execution_phase4_rollout_hot_path_freeze.md](gpu_execution_phase4_rollout_hot_path_freeze.md)

使用规则：

- CUDA 驻留第二后端计划是该新工作线唯一的冻结执行计划。companion 迭代账本
  记录已接受的分支证据与 RB10 hold decision/RB11 closure record，当前计划已完成
  且不晋级。之后若要继续必须建立新的显式计划。
- CR2 continuation program 已完成 full-window、规模治理、consumer、parity、resource
  与 small-batch gates，并在 CR2-7 无晋级关闭。保留的 advisory 不是 runtime selector；
  未来 CUDA-resident 工作需要另一套显式计划和用户授权。
- CP 晋升程序（CP-0..CP-9）于 2026-08-13 以范围化晋升裁定关闭：fixture 面上
  的 opt-in 维护地位、CPU 保持维护默认、性能主张保持主机特定实验性。运行时
  行为未变；公开暴露实现是单独授权的后续范围。
- 验证器要求字节稳定 provenance 时，本夹具保留历史路径和哈希。当前架构权威
  仍位于 `docs/architecture/`。
- 冻结证据内部的相对链接可能描述历史布局，不是当前仓库路由。
- 不得在此新增计划材料。新的 runtime 工作必须进入当前 owner-local work 结构。
