<!-- Machine-translated draft generated on 2026-05-18 from docs/plan/README.zh.md. Review before treating this file as authoritative. -->

# `docs/plan` Documentation Index and Governance Guide

Status: `2026-05-18` Entry correction version.  
This document only describes the real `docs/plan/` structure currently in the repository, and how these documents are used in the current mainline, avoiding mixing historical discussions, research drafts, and frozen execution baselines.

Language migration note:

- The current `docs/plan/` is being migrated to a bilingual system with English `.md` as primary and Chinese `.zh.md` as secondary.
- The migration plan can be found at [documentation_bilingual_migration_plan_20260518.md](documentation_bilingual_migration_plan_20260518.md).
- Until English peers are fully supplemented, existing `.zh.md` long texts will still be used as transitional inputs, but English main texts should be supplemented in subsequent batches.

## 1. Current Directory Structure

`docs/plan/` currently contains four active mainline subdirectories and two retained auxiliary directories:

- [architecture/README.md](architecture/README.md)
  - Architecture main plan, performance research, `src/` layering refactoring boundaries.
- [runtime_facade/README.md](runtime_facade/README.md)
  - Runtime facade contract, completed execution records, subsequent cleanup freeze plan.
- [cooperative/README.md](cooperative/README.md)
  - Cooperative training and cooperative execution pipeline mainline documents.
- [exact_runtime/README.md](exact_runtime/README.md)
  - Candidate special plans, checklists, and phase freeze records for exact runtime / GPU mainline.
- `archive/README.md`
  - Closed routes, experimental archives, and historical traceability materials. This directory is often a local retention surface and should not be assumed to be uploaded to shared remotes.
- `results/README.md`
  - Benchmark, evaluation documentation, and acceptance result materials. This directory is often a local retention surface and should not be assumed to be uploaded to shared remotes.

Notes:

- `archive/` and `results/` may exist in the local workspace, but they are neither part of the "mainline plan authorization surface" nor should be treated as default shared sync entry points.
- Earlier archived design materials are mainly located in [docs/Archive/](../Archive).
- `results/` only holds results and acceptance materials; it should not be confused as a new entry point for main plan documents.

## 2. Recommended Reading Order

1. [architecture/system_layering_and_engine_encapsulation_plan.zh.md](architecture/system_layering_and_engine_encapsulation_plan.zh.md)
   - Architecture main plan, answering "what is the target layering and how should the engine boundary be defined".
2. [architecture/architecture_and_performance_research_followup.zh.md](architecture/architecture_and_performance_research_followup.zh.md)
   - Route research and performance trade-off explanation, answering "why this layering and how to prioritize subsequent routes".
3. [runtime_facade/runtime_facade_contract_plan.zh.md](runtime_facade/runtime_facade_contract_plan.zh.md)
   - Facade contract basis, answering "what C++ application contract should the upper layer depend on long-term".
4. [runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md](runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md)
   - Candidate freeze execution plan that can still be used, focusing on facade layering cleanup and decoupling.
5. [architecture/src_layered_refactor_freeze.zh.md](architecture/src_layered_refactor_freeze.zh.md)
   - `src/` layering refactoring boundaries and completed work records.
6. [cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md](cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md)
   - Cooperative training foundation and performance analysis main text.
7. [cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md](cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md)
   - P8 cooperative execution pipeline facility review and next steps.
8. Special documents under `exact_runtime/`
   - Only delve deeper when the task explicitly enters the GPU / exact runtime mainline.

## 3. Current Authority Relationships

### A. Direction and Contract Basis

| Document | Current Role | Usage Rules |
|----------|--------------|-------------|
| [architecture/system_layering_and_engine_encapsulation_plan.zh.md](architecture/system_layering_and_engine_encapsulation_plan.zh.md) | Architecture main plan | Authoritative description of architecture direction; not a direct task list |
| [architecture/architecture_and_performance_research_followup.zh.md](architecture/architecture_and_performance_research_followup.zh.md) | Route research main text | Provides route prioritization and performance judgment; does not directly authorize implementation |
| [runtime_facade/runtime_facade_contract_plan.zh.md](runtime_facade/runtime_facade_contract_plan.zh.md) | Facade contract basis | Defines interface boundaries and DTOs; does not directly authorize extended implementation |
| [cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md](cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md) | Cooperative training direction basis | Provides facility foundation, risks, and route analysis |
| [cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md](cooperative/p8_cooperative_execution_pipeline_findings_and_plan.zh.md) | Cooperative execution direction basis | Provides current cooperative execution mainline facility review and next steps |

### B. Completed or Phase-Based Freeze Records

| Document | Current Status | Notes |
|----------|----------------|-------|
| [runtime_facade/runtime_facade_task_bootstrap_plan.zh.md](runtime_facade/runtime_facade_task_bootstrap_plan.zh.md) | First batch `WP1-WP6` completed | Now an execution record; should not be extended with new scope |
| [architecture/src_layered_refactor_freeze.zh.md](architecture/src_layered_refactor_freeze.zh.md) | `WP1-WP7` completed | Completed work treated as record; new splits require a new freeze |
| [exact_runtime/gpu_execution_phase4_rollout_hot_path_freeze.md](exact_runtime/gpu_execution_phase4_rollout_hot_path_freeze.md) | Frozen phase-based execution plan | Used as historical phase record for GPU mainline |

### C. Still Actionable Special Drafts / Checklists

| Document | Current Status | Notes |
|----------|----------------|-------|
| [exact_runtime/cpp_exact_runtime_refactor_plan.md](exact_runtime/cpp_exact_runtime_refactor_plan.md) | Draft follow-on implementation plan | Subsequent C++ exact runtime candidate plan |
| [exact_runtime/gpu_execution_mainline_integration_checklist.md](exact_runtime/gpu_execution_mainline_integration_checklist.md) | Open | GPU execution mainline consistency checklist |
| [exact_runtime/gpu_resident_state_implementation_plan.md](exact_runtime/gpu_resident_state_implementation_plan.md) | Implementation draft | Device resident state direction draft |
| [exact_runtime/gpu_exact_world_step_performance_and_parity_plan.md](exact_runtime/gpu_exact_world_step_performance_and_parity_plan.md) | Implementation plan draft | GPU exact step performance/semantic parity special draft |

### D. Archive Material Locations

- Earlier performance refactoring and route evolution notes can be found at [docs/Archive/rearchitecture/README.md](../Archive/rearchitecture/README.md).
- Earlier speed rearchitecture summary can be found at [docs/Archive/speed_rearchitecture/README.md](../Archive/speed_rearchitecture/README.md).
- These materials retain traceability value but should not be treated as current implementation authority.

## 4. Execution Rules

1. Only frozen execution documents that clearly specify scope, acceptance criteria, and non-goals can be used directly as implementation basis.
2. "Drafts", "research", "contracts", "checklists", and "evaluation records" by default only provide direction, arguments, contracts, or results, and do not directly authorize extended implementation.
3. Completed freeze documents automatically become execution records; new unfrozen scope should not be appended to the original document.
4. Historical retention or experimental archive materials are only used for traceability, explaining route evolution, or reviewing abandoned solutions.
5. If a new task depends on multiple research, contracts, or historical plans, it should first be consolidated into a new single frozen task list before entering implementation.
