# `exact_runtime/`

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This directory holds candidate special plans, checklists, and phase freeze
records for the exact runtime / GPU mainline.

Not every historical exact-runtime draft still lives in this active directory.
Use this README plus `../archive/exact_runtime/README.md` to determine which
documents remain active versus historical.

Recommended reading order:

1. [cuda_resident_backend_program_20260729.md](cuda_resident_backend_program_20260729.md)
2. [cuda_resident_backend_iteration_log_20260729.md](cuda_resident_backend_iteration_log_20260729.md)
3. [cuda_resident_rb10_hold_decision_20260731.md](cuda_resident_rb10_hold_decision_20260731.md)
4. [cuda_resident_rb11_closure_20260731.md](cuda_resident_rb11_closure_20260731.md)
5. [cuda_resident_runtime_program_2_20260731.md](cuda_resident_runtime_program_2_20260731.md)
6. [cuda_resident_runtime_program_2_iteration_log_20260731.md](cuda_resident_runtime_program_2_iteration_log_20260731.md)
7. [cuda_resident_runtime_program_2_size_policy_20260731.json](cuda_resident_runtime_program_2_size_policy_20260731.json)
8. [cuda_resident_cr2_resource_evidence_20260804.md](cuda_resident_cr2_resource_evidence_20260804.md)
9. [cuda_resident_cr2_resource_evidence_20260804.json](cuda_resident_cr2_resource_evidence_20260804.json)
10. [cuda_resident_cr2_counter_evidence_20260804.md](cuda_resident_cr2_counter_evidence_20260804.md)
11. [cuda_resident_cr2_counter_evidence_20260804.json](cuda_resident_cr2_counter_evidence_20260804.json)
12. [cuda_resident_cr2_matrix_evidence_20260804.md](cuda_resident_cr2_matrix_evidence_20260804.md)
13. [cuda_resident_cr2_matrix_evidence_20260804.json](cuda_resident_cr2_matrix_evidence_20260804.json)
14. [cuda_resident_cr2_closure_20260805.md](cuda_resident_cr2_closure_20260805.md)
15. [cuda_resident_cr2_closure_20260805.json](cuda_resident_cr2_closure_20260805.json)
16. [cuda_resident_promotion_program_20260808.md](cuda_resident_promotion_program_20260808.md)
17. [cuda_resident_cp_resource_evidence_20260810.json](cuda_resident_cp_resource_evidence_20260810.json)
18. [cuda_resident_cp_counter_evidence_20260810.json](cuda_resident_cp_counter_evidence_20260810.json)
19. [cpp_exact_runtime_refactor_plan.md](cpp_exact_runtime_refactor_plan.md)
20. [gpu_execution_mainline_integration_checklist.md](gpu_execution_mainline_integration_checklist.md)
21. [gpu_execution_phase4_rollout_hot_path_freeze.md](gpu_execution_phase4_rollout_hot_path_freeze.md)
22. [../archive/exact_runtime/README.md](../archive/exact_runtime/README.md)

Usage rules:

- The CUDA-resident second-backend program is the single frozen execution plan
  for that new workline. The companion iteration log records accepted branch
  evidence and the RB10 hold decision/RB11 closure record the no-promotion
  boundary. The plan is complete; future work requires a new explicit program.
- The CR2 continuation program completed those full-window, size-governance,
  consumer, parity, resource, and small-batch gates and then closed without
  promotion in CR2-7. Its retained advisory is not a runtime selector; future
  CUDA-resident work requires another explicit program and user authorization.
- Except for frozen phase plans, the remaining documents are by default candidate special drafts or checklists.
- The current repository structure has evolved; some code paths in the text still carry historical semantics. When using, cross-reference with the current code tree.
- Earlier GPU mainline discussions and experimental routes have been moved to `../archive/exact_runtime/`.
