# Documentation Audit — Consolidated Issue Tracker

Audit date: `2026-05-18`, corrected `2026-05-18` after re-verification.
Commit `ce101c8` ("docs: correct verified documentation drift") resolved several issues.

Legend:
- **[FIXED]** = resolved by commit ce101c8
- **[INVALID]** = audit finding was incorrect on re-verification
- **[DRAFT]** = document is explicitly labeled as a draft/plan and never claimed implementation
- **[OPEN]** = confirmed valid, not yet fixed

---

## P0 — Critical

### stick_pitch sign inverted — [FIXED]
- **Source**: [standards_vs_code.md](standards_vs_code.md) — `air/act.md`
- **Was**: doc said negative=pitch-up, code said positive=pitch-up.
- **Fix**: Changed to "Pulling back is positive (pitch up), pushing forward is negative (pitch down)", matching `pilot_action.h`.
- **Also fixed**: `jettison_btn` → `jettison_emergency`.

### visualization_guide.md references nonexistent script — [FIXED]
- **Source**: [manual_vs_code.md](manual_vs_code.md) — `visualization_guide.md`
- **Was**: Referenced `python3 examples/viz/perception_viz.py` which didn't exist.
- **Fix**: Changed to `python3 examples/viz/run_viz.py --scenario <path>` with `viz_runner.py` as alternative.

### Architecture interfaces documented but never created — [DRAFT]
- **Source**: [plan_vs_code.md](plan_vs_code.md) — `architecture/system_layering_and_engine_encapsulation_plan.md`
- **Re-evaluation**: The document explicitly says "Status: Architecture draft on 2026-05-10" and "it is not a frozen single-run task sheet." The `IPhysicsBackend`, `ISimulationRuntime` etc. interfaces are aspirational design targets, not claims of implementation. **NOT a doc-code mismatch**.

### GPU exact-step backends documented as planned, zero implementation — [DRAFT]
- **Source**: [plan_vs_code.md](plan_vs_code.md) — 5 exact_runtime documents
- **Re-evaluation**: All 5 documents are explicitly labeled as drafts/plans:
  - `cpp_exact_runtime_refactor_plan.md`: "Status: Draft follow-on implementation plan... not yet a separately frozen execution plan. No implementation should expand under this document until its scope is explicitly re-frozen."
  - `gpu_resident_state_implementation_plan.md`: pre-implementation analysis with bottleneck data.
  - `gpu_exact_world_step_performance_and_parity_plan.md`: machine-translated draft, describes current-state analysis.
  - `gpu_execution_mainline_integration_checklist.md`: explicitly an unchecked checklist.
- **NOT doc-code mismatches**. These documents never claimed the items were implemented.

---

## P1 — Significant

### c2_communication.md — wrong file paths + missing feature — [OPEN]
- **Source**: [forward_vs_code.md](forward_vs_code.md)
- `src/components/action.h` → actual: `src/components/command/legacy_command.h` + `src/components/command/command_link.h`
- `src/systems/command_link_system.h` → actual: `src/systems/core/operation_system.h`
- `src/core/simulation_kernel.cpp` → actual: `src/core/engine/simulation_kernel.cpp`
- `PendingCommand` claimed as implemented → does not exist (only `CommandLag`/`LaggedCommand`)

### engagement_termination.md — claimed features don't exist — [FIXED]
- **Source**: [forward_vs_code.md](forward_vs_code.md)
- **Was**: `disengage_range_m`, `min_specific_energy_j_kg`, `ammo_depletion_ends` claimed as "Already Implemented".
- **Fix**: Rewrote section as "Recommended Engagement-Level Termination Extensions" — these are now correctly described as planning targets. Paths corrected to `src/core/mission/runtime/termination_runtime.*` and `gym_envs/scenario_loader/` package.

### rl_selfplay.md — claimed implementation doesn't exist — [OPEN]
- **Source**: [forward_vs_code.md](forward_vs_code.md)
- `examples/training/train_self_play.py` → directory and file don't exist
- `examples/training/selfplay_config.json` → not found anywhere
- No `train_self_play` or `selfplay_config` references in any source file
- The "Current Implementation Notes" section needs to either be rewritten to match actual code, or the implementation needs to be found (if it exists under a different path).

### weapons_engagement_impl.md — all code paths wrong — [FIXED]
- **Source**: [forward_vs_code.md](forward_vs_code.md)
- **Was**: 4 paths missing subdirectories (`engine/`, `weapons/`, `combat/`).
- **Fix**: All 4 paths corrected, content significantly expanded to accurately describe missile launch, seeker screening, guidance model, and flight dynamics.

### physics_engine_inventory.md — disabled system + wrong path — [FIXED]
- **Source**: [manual_vs_code.md](manual_vs_code.md)
- **Was**: `MovementSystem` described as active; pipeline had 11 stages; `src/systems/systems/logistics.h` didn't exist.
- **Fix**: `MovementSystem` now correctly labeled as legacy/disabled. `LeapfrogIntegrationSystem` documented as active. Pipeline expanded to full ~25 stages. Logistics entry path corrected.

### engine_capabilities.md — disabled system — [FIXED]
- **Source**: [manual_vs_code.md](manual_vs_code.md)
- **Was**: `MovementSystem` claimed as active position integration.
- **Fix**: `LeapfrogIntegrationSystem` added as active mainline; `MovementSystem` noted as "simpler legacy... currently disabled in the active kernel path."

### landing_task_notes.md / takeoff_to_cruise_mixedmode_notes.md — wrong repo root — [OPEN]
- **Source**: [manual_vs_code.md](manual_vs_code.md)
- All absolute paths use `/home/void0312/CMO/` → actual repo: `/home/void0312/Workshop/CMO/`
- `gym_envs/scenario_loader.py` → is a directory, not a `.py` file
- `experiments_tmp/` → doesn't exist at either path
- 4 regression test files claimed → none exist in `tests/`

### forward/README.md — references nonexistent file — [FIXED]
- **Source**: [forward_vs_code.md](forward_vs_code.md)
- **Was**: Listed `release_alpha_checklist.md` which didn't exist.
- **Fix**: Removed the reference; replaced with note about release checklists living alongside concrete task/plan docs.

### scenario_guide.md — JSON schema wrong — [INVALID]
- **Source**: [standards_vs_code.md](standards_vs_code.md)
- **Audit claimed**: top-level key is `meta` not `scenario_name`; `max_steps` inside `meta` not `environment`; no `terrain_type`.
- **Re-verification**: The audit only checked `examples/scenarios/test_scenario.json` (a minimal test file). Actual production scenarios (`scenarios/landing/landing_ils_final_train_v1.json`, `scenarios/cruise/cooperative_cruise_*.json`) all use `scenario_name`, `environment.max_steps`, and `environment.terrain_type` as documented. **The scenario_guide.md schema is correct**.

### air/obs.md — observation space over-described — [OPEN, reclassified as P2]
- **Source**: [standards_vs_code.md](standards_vs_code.md)
- The doc is a "Pilot Observation Space Standard" — it describes what a pilot SHOULD observe, not what `AgentObservation` currently exposes. The documented 20+ variables exist in `InstrumentState` (an internal component) but are not all surfaced to `AgentObservation`.
- **Reclassification**: This is a gap between standard and implementation, not a wrong document. The standard is aspirational. Downgraded to **P2**.

### modularization_plan.md — dependency claim violated — [OPEN]
- **Source**: [standards_vs_code.md](standards_vs_code.md)
- `content/` claimed "depends on: none (data only)" → actually includes from `components/` extensively and has inline logic.

### Plan doc line counts severely outdated — [OPEN, reclassified as P2]
- **Source**: [plan_vs_code.md](plan_vs_code.md) — `architecture/architecture_and_performance_research_followup.md`
- Line counts in the document are from 2026-05-10 and have since changed due to refactoring.
- This is a research follow-up document; stale line counts are expected post-refactor. Downgraded to **P2**.

### CMake target split documented but never executed — [DRAFT]
- **Source**: [plan_vs_code.md](plan_vs_code.md)
- The target split is described in architecture drafts and freeze cleanup plans as a future step. The plans explicitly say these would be "next steps" after freeze completion. **Not a mismatch** — the split was never claimed as complete.

### Runtime facade contract DTOs not matching — [DRAFT]
- **Source**: [plan_vs_code.md](plan_vs_code.md)
- Like the architecture plan, this contract plan proposes ideal DTOs and method signatures. The actual API evolved differently. The plan is a design document, not an implementation claim.

---

## P2 — Minor

### Python-layer README omissions (7 items) — [OPEN]
- `gym_envs/universal_env_parts/common.py` not listed
- `gym_envs/leader_env_parts/runtime_facade.py` not listed
- `tests/architecture/` not in "Current Structure"
- `tests/contracts/env/` not documented (29 JSON contracts)
- `tests/contracts/unit/env/` not documented
- `tools/diagnostics/analyze_cooperative_observation_scales.py` + `trace_training_nonfinite_source.py` not listed
- `examples/agents/` not documented

### Standards doc minor inaccuracies (5 items, 2 fixed) — [OPEN + 2 FIXED]
- `conventions.md`: heading claimed "derived from velocity" → actually from Transform component
- `air/aim.md`: `cmd_vvi` and `tac_jettison` fields don't exist
- `air/rep.md`: structured report fields described but only generic fields exist
- `modularization_plan.md`: `core/interfaces/` omitted from module map; build doesn't enforce boundaries; components contain algorithm logic
- ~~`air/act.md`: `jettison_btn` vs `jettison_emergency` naming diff~~ **[FIXED]**

### Plan doc stale descriptions (5 items, 1 draft) — [OPEN]
- `simulation_kernel_damage_debug_api.cpp` exists but not in WP4 list
- `core/mission/runtime/` files not reflected in task bootstrap plans
- Test name mismatch in `p8_cooperative_execution_pipeline`
- Directory renames unresolved (`interfaces/python` → `bindings/python`, etc.) — **[DRAFT]**: explicitly open questions, not mismatches
- Phase4 GPU freeze: 2 remaining unchecked items

### Forward doc minor issues (2 items, 2 fixed) — [2 FIXED]
- ~~`physics_engine_roadmap.md`: `forces.h` labeled `[NEW]` but already implemented~~ **[FIXED]** — `forces.h` now exists
- ~~`engagement_termination.md`: path missing `runtime/` subdirectory~~ **[FIXED]**
- Pipeline ordering simplified in `engine_capabilities.md` — **[FIXED]** — now has full pipeline

### src/ README mismatches (~13 items) — [OPEN]
- 12 files on disk missing from README listings
- `src/components/tasking/naval/README.md` describes types as "future" when already implemented

### Python-layer editorial (6 items) — [OPEN]
- `tests/README.md`: missing directories in naming conventions; `bridges/*.json` listed twice
- `tests/diagnostics/` described as scripts but only has READMEs
- `tools/archive/check_binding.py` not listed; `examples/config/training/curriculum/` not documented

---

## Summary After Correction

| Category | Count | Change from original |
|----------|-------|---------------------|
| P0 [FIXED] | 2 | `stick_pitch`, `visualization_guide.py` |
| P0 [DRAFT] | 2 | Architecture interfaces, GPU backends — never claimed as implemented |
| P1 [FIXED] | 6 | `engagement_termination`, `weapons_engagement_impl`, `physics_engine_inventory`, `engine_capabilities`, `forward/README` |
| P1 [INVALID] | 1 | `scenario_guide.md` — schema is actually correct |
| P1 [OPEN] | 3 | `c2_communication.md`, `rl_selfplay.md`, landing/takeoff task notes |
| P1→P2 reclassified | 2 | `air/obs.md` (standard vs impl gap), line counts (expected post-refactor) |
| P1→DRAFT reclassified | 2 | CMake target split, facade contract DTOs |
| P2 [FIXED] | 3 | `air/act.md` naming, `forces.h` label, engagement_termination paths |
| P2 [OPEN] | ~33 | Various omissions, stale labels, editorial items |

### Remaining Actionable OPEN Items by Priority

**P1 (3 items to fix):**
1. `c2_communication.md` — correct 3 file paths; remove/rewrite `PendingCommand` claim
2. `rl_selfplay.md` — remove or rewrite "Current Implementation Notes" section referencing nonexistent files
3. `landing_task_notes.md` + `takeoff_to_cruise_mixedmode_notes.md` — fix repo root paths

**P2 (~33 items)** — Minor omissions, stale labels, editorial improvements across all domains.
