<!-- Machine-translated draft generated on 2026-05-18 from docs/plan/exact_runtime/README.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/plan/exact_runtime/README.md. Review before treating this file as authoritative. -->

# `exact_runtime/`

This directory holds candidate special plans, checklists, and phase freeze records for the exact runtime / GPU mainline.

Recommended reading order:

1. [cpp_exact_runtime_refactor_plan.md](cpp_exact_runtime_refactor_plan.md)
2. [gpu_execution_mainline_integration_checklist.md](gpu_execution_mainline_integration_checklist.md)
3. [gpu_execution_phase4_rollout_hot_path_freeze.md](gpu_execution_phase4_rollout_hot_path_freeze.md)
4. [gpu_exact_world_step_performance_and_parity_plan.md](gpu_exact_world_step_performance_and_parity_plan.md)
5. [gpu_resident_state_implementation_plan.md](gpu_resident_state_implementation_plan.md)

Usage rules:

- Except for frozen phase plans, the remaining documents are by default candidate special drafts or checklists.
- The current repository structure has evolved; some code paths in the text still carry historical semantics. When using, cross-reference with the current code tree.
- Earlier GPU mainline discussions and experimental routes have been moved to `../archive/`.
