# `docs/plan` Documentation Index and Governance Guide

Status: `2026-06-01` plan authority and archive-boundary index.
This document describes the real `docs/plan/` structure currently in the repository and how these documents are used in the current mainline, avoiding mixing historical discussions, research drafts, frozen execution baselines, and retained result artifacts.

Language migration note:

- The current `docs/plan/` is being migrated to a bilingual system with English `.md` as primary and Chinese `.zh.md` as secondary.
- The migration plan can be found at [documentation_bilingual_migration_plan_20260518.md](documentation_bilingual_migration_plan_20260518.md).
- The strict bilingual maintenance surface is the stable plan authority layer, not every historical freeze or candidate draft under `docs/plan/**`.
- Until English peers are fully supplemented, existing `.zh.md` long texts will still be used as transitional inputs, but English main texts should be supplemented in subsequent batches.

## 1. Current Directory Structure

`docs/plan/` currently contains four active mainline subdirectories and two retained auxiliary directories:

- [architecture/README.md](architecture/README.md)
  - Architecture main plan, performance research, and archived `src/` layering records.
- [runtime_facade/README.md](runtime_facade/README.md)
  - Runtime facade contract and active cleanup follow-up; completed execution records now live in `archive/`.
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

1. [architecture/simulation_system_architecture_design.md](architecture/simulation_system_architecture_design.md)
   - Strict simulation-system baseline, answering "what is the canonical lifecycle and how should domain extensions attach to it".
2. [architecture/system_layering_and_engine_encapsulation_plan.md](architecture/system_layering_and_engine_encapsulation_plan.md)
   - Architecture main plan, answering "what is the target layering and how should the engine boundary be defined".
3. [architecture/architecture_and_performance_research_followup.md](architecture/architecture_and_performance_research_followup.md)
   - Route research and performance trade-off explanation, answering "why this layering and how to prioritize subsequent routes".
4. [runtime_facade/runtime_facade_contract_plan.md](runtime_facade/runtime_facade_contract_plan.md)
   - Facade contract basis, answering "what C++ application contract should the upper layer depend on long-term".
5. [archive/runtime_facade/README.md](archive/runtime_facade/README.md)
   - Archived runtime-facade cleanup and bootstrap record index; use as history only.
6. [cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.md](cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.md)
   - Cooperative training foundation and performance analysis main text.
7. [cooperative/p8_cooperative_execution_pipeline_findings_and_plan.md](cooperative/p8_cooperative_execution_pipeline_findings_and_plan.md)
   - P8 cooperative execution pipeline facility review and next steps.
8. Special documents under `exact_runtime/`
   - Only delve deeper when the task explicitly enters the GPU / exact runtime mainline, and start from `exact_runtime/README.md` rather than assuming every candidate draft still exists.

## 3. Historical Freeze Records

These documents have been moved out of the active subdirectories and are kept
for execution history only:

- [archive/runtime_facade/README.md](archive/runtime_facade/README.md)
- [archive/architecture/README.md](archive/architecture/README.md)
- [archive/exact_runtime/README.md](archive/exact_runtime/README.md)

## 4. Current Authority Relationships

### A. Direction and Contract Basis

| Document | Current Role | Usage Rules |
|----------|--------------|-------------|
| [architecture/simulation_system_architecture_design.md](architecture/simulation_system_architecture_design.md) | Strict simulation architecture baseline | Current authority for the canonical lifecycle, extension model, and architecture gates; not a direct task list |
| [architecture/system_layering_and_engine_encapsulation_plan.md](architecture/system_layering_and_engine_encapsulation_plan.md) | Architecture main plan | Authoritative background for layer direction; not a direct task list |
| [architecture/architecture_and_performance_research_followup.md](architecture/architecture_and_performance_research_followup.md) | Route research main text | Provides route prioritization and performance judgment; does not directly authorize implementation |
| [runtime_facade/runtime_facade_contract_plan.md](runtime_facade/runtime_facade_contract_plan.md) | Facade contract basis | Defines interface boundaries and DTOs; does not directly authorize extended implementation |
| [cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.md](cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.md) | Cooperative training direction basis | Provides facility foundation, risks, and route analysis |
| [cooperative/p8_cooperative_execution_pipeline_findings_and_plan.md](cooperative/p8_cooperative_execution_pipeline_findings_and_plan.md) | Cooperative execution direction basis | Provides current cooperative execution mainline facility review and next steps |

### B. Archived or Phase-Based Freeze Records

| Document | Current Status | Notes |
|----------|----------------|-------|
| [archive/runtime_facade/README.md](archive/runtime_facade/README.md) | Archived runtime-facade record index | Use the archive index to reach completed bootstrap and cleanup freezes |
| [archive/architecture/README.md](archive/architecture/README.md) | Archived architecture record index | Use the archive index to reach completed `src/` layering freezes |
| [exact_runtime/gpu_execution_phase4_rollout_hot_path_freeze.md](exact_runtime/gpu_execution_phase4_rollout_hot_path_freeze.md) | Frozen phase-based execution plan | Used as historical phase record for GPU mainline |

### C. Still Actionable Special Drafts / Checklists

| Document | Current Status | Notes |
|----------|----------------|-------|
| [exact_runtime/cpp_exact_runtime_refactor_plan.md](exact_runtime/cpp_exact_runtime_refactor_plan.md) | Draft follow-on implementation plan | Subsequent C++ exact runtime candidate plan |
| [exact_runtime/gpu_execution_mainline_integration_checklist.md](exact_runtime/gpu_execution_mainline_integration_checklist.md) | Open | GPU execution mainline consistency checklist |
| [exact_runtime/README.md](exact_runtime/README.md) | Candidate-plan index | Use the local README to see which exact-runtime drafts are still present |

### D. Archive Material Locations

- Earlier performance refactoring and route evolution notes can be found at [docs/Archive/rearchitecture/README.md](../Archive/rearchitecture/README.md).
- Earlier speed rearchitecture summary can be found at [docs/Archive/speed_rearchitecture/README.md](../Archive/speed_rearchitecture/README.md).
- These materials retain traceability value but should not be treated as current implementation authority.

## 5. Execution Rules

1. Only frozen execution documents that clearly specify scope, acceptance criteria, and non-goals can be used directly as implementation basis.
2. "Drafts", "research", "contracts", "checklists", and "evaluation records" by default only provide direction, arguments, contracts, or results, and do not directly authorize extended implementation.
3. Completed freeze documents automatically become execution records; new unfrozen scope should not be appended to the original document.
4. Historical retention or experimental archive materials are only used for traceability, explaining route evolution, or reviewing abandoned solutions.
5. If a new task depends on multiple research, contracts, or historical plans, it should first be consolidated into a new single frozen task list before entering implementation.
