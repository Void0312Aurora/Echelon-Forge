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
8. [cpp_exact_runtime_refactor_plan.md](cpp_exact_runtime_refactor_plan.md)
9. [gpu_execution_mainline_integration_checklist.md](gpu_execution_mainline_integration_checklist.md)
10. [gpu_execution_phase4_rollout_hot_path_freeze.md](gpu_execution_phase4_rollout_hot_path_freeze.md)
11. [../archive/exact_runtime/README.md](../archive/exact_runtime/README.md)

Usage rules:

- The CUDA-resident second-backend program is the single frozen execution plan
  for that new workline. The companion iteration log records accepted branch
  evidence and the RB10 hold decision/RB11 closure record the no-promotion
  boundary. The plan is complete; future work requires a new explicit program.
- The CR2 program is that new explicit continuation program. It owns the
  full-window, size-governance, consumer, parity, resource, and small-batch
  gates; it does not authorize promotion until its final decision row.
- Except for frozen phase plans, the remaining documents are by default candidate special drafts or checklists.
- The current repository structure has evolved; some code paths in the text still carry historical semantics. When using, cross-reference with the current code tree.
- Earlier GPU mainline discussions and experimental routes have been moved to `../archive/exact_runtime/`.
