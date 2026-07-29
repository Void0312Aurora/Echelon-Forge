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
2. [cpp_exact_runtime_refactor_plan.md](cpp_exact_runtime_refactor_plan.md)
3. [gpu_execution_mainline_integration_checklist.md](gpu_execution_mainline_integration_checklist.md)
4. [gpu_execution_phase4_rollout_hot_path_freeze.md](gpu_execution_phase4_rollout_hot_path_freeze.md)
5. [../archive/exact_runtime/README.md](../archive/exact_runtime/README.md)

Usage rules:

- The CUDA-resident second-backend program is the single frozen execution plan
  for that new workline. RB0 is accepted; RB1 is the only currently authorized
  implementation iteration, and later rows remain dependency-gated.
- Except for frozen phase plans, the remaining documents are by default candidate special drafts or checklists.
- The current repository structure has evolved; some code paths in the text still carry historical semantics. When using, cross-reference with the current code tree.
- Earlier GPU mainline discussions and experimental routes have been moved to `../archive/exact_runtime/`.
