# Task Archive Registry

Status: established `2026-06-09`. This file is the registration index for all archived subprojects under `docs/task/archive/`.

Each entry records: subproject name, archive date, brief work description, and archive rationale.

---

## Archived Subprojects

### `common_air_naval/`

- **Archived**: 2026-06-09
- **Description**: Common / Air / Naval three-domain DTO modular split freeze plan. Decomposed mixed DTOs into `joint/common core` (`common/`), `air specialization` (`air/`), and `naval specialization` (`naval/`), establishing a Python profile dispatch seam while preserving compatibility umbrella headers. Contained 9 work packages (WP0–WP8), all completed and accepted.
- **Rationale**: WP0–WP8 all completed; foundational structure (common/air/naval DTO split, TaskOrder/LeaderIntent/PilotReport common-core extraction, MissionCommand compatibility split, Python profile dispatch seam) landed in main code. Subsequent naval runtime expansion and air-first helper migration continue via standalone task sheets.
- **Key artifacts**: `src/components/tasking/common/`, `src/components/tasking/air/`, `src/components/command/common/`, `src/components/command/ground/` directory structures; `MissionCommandCore/Air/Naval/Ground` projection system.

### `code_redundancy/`

- **Archived**: 2026-06-09
- **Description**: Code redundancy identification and deduplication workline. Records identified code duplication patterns (DRY violations, repeated logic blocks, templated boilerplate), redundancy analysis, and deduplication recommendations.
- **Rationale**: Converted to archive-type work records. Historical analysis snapshots in `archive/` subdirectory; current redundancy issues tracked by the architecture refactoring audit (`docs/task/review/architecture_refactoring_audit_20260522`).
- **Key artifacts**: Redundancy analysis documents, deduplication recommendation records.

### `diagnostics_eval/`

- **Archived**: 2026-06-09
- **Description**: Diagnostics tooling and evaluation entrypoint convergence workline. Covered diagnostics benchmark CLI convergence, diagnostics modularization, and eval entrypoint unification. Aimed to converge scattered diagnostic scripts and evaluation tools into a consistent toolchain entrypoint.
- **Rationale**: Converted to archive-type work records. Actual diagnostic tool code lives in `tools/diagnostics/`, evaluation entrypoints in `tools/eval/`, both in maintained state.
- **Key artifacts**: Three convergence records: `diagnostics_benchmark_cli_convergence`, `diagnostics_modularization`, `eval_entrypoint_convergence`.

### `game/`

- **Archived**: 2026-06-09
- **Description**: Game frontend integration exploratory workline. Explored connecting a playable external game frontend (Arma 3) while keeping Echelon Forge backend as the authoritative simulation truth source. Core principle: backend authority stays with Echelon; external game entities are proxy/representation shells only; AI behavior comes from repository-trained policies.
- **Rationale**: Exploratory workline, not an active execution project. The active tracked Arma proxy helper is the stub in `tools/diagnostics/`; the former raw env-backed backend has been archived under `tools/archive/`. Godot/WebSocket experiments remain archived locally.
- **Key artifacts**: Arma proxy backend stub, archived Arma proxy raw-env backend.

### `performance_runtime/`

- **Archived**: 2026-06-09
- **Description**: Runtime performance optimization task subproject. Took over runtime performance work after the realism/fidelity deepening line was temporarily frozen: optimization layering rules, compute chain analysis, and benchmark-oriented optimization entrypoint consolidation.
- **Rationale**: Optimization layering and benchmark-oriented analysis frozen; legacy planning chain treated as reference material. README already directed readers to archive index as the sole canonical entrypoint.
- **Key artifacts**: Runtime performance planning documents, optimization ordering and upgrade rules, hot-path analysis records.

### `python_rl/`

- **Archived**: 2026-06-09
- **Description**: Python RL framework subfolder convergence records. Covered modularization convergence for `python/rl/` subdirectories (control, runtime, tasking, policy_algo, planning_support) and deduplication/normalization of root shim callsites.
- **Rationale**: Converted to convergence record archive. Subfolder modularization convergence completed; historical snapshots in `archive/` subdirectory.
- **Key artifacts**: 8 subfolder convergence records (control, runtime phase2, tasking domain, planning support, policy_algo, root shim callsite, runtime subfolder, tasking subfolder).

---

## Archive Rules

A subproject may be archived when any of the following conditions are met:

1. All work packages completed and accepted; follow-up work transferred to standalone task sheets.
2. Subproject self-declares as "archive-type work record" with no active execution surface.
3. Exploratory workline frozen; actual code artifacts in maintained state (e.g., under `tools/`).
4. Planning documents frozen as reference material, no longer serving as active execution entrypoints.

Archived subprojects remain traceable through this registry. To reactivate a workline, first assess whether the current code state has rendered the original planning obsolete.

---

*Registry established 2026-06-09.*
