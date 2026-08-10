# MLF-6 Structural Failure — Task Clusters

Status: `2026-06-18` v10 finite task-cluster plan. P1/P2, P3, P4, P5,
P6 focused validation, P7 broad regression, and the v10 near-field continuous
rod / cumulative wing-loss calibration are complete. Archive movement was
completed by explicit user instruction. Matches [README.md](README.md) phase plan
(P0-P7).

## Boundary Decision

This subproject advances MLF-6 only: structural failure fact writing. It reads
live ECS `ComponentDamageState` and writes `StructuralBreakupEvent` rows.
Per design decision D2, it does NOT read or write `structural_integrity`.
Per D1, it reads ECS components, not event-store rows. Per D4, the state
machine is per-airframe, cumulative, and irreversible.

Write surface: `src/systems/combat/structural_failure_system.*` (new),
`src/core/engine/simulation_kernel_engagement_event_store.*` (event append),
`tools/diagnostics/structural_breakup_export.py` (new), focused C++ tests.

It must not:
- Modify `aerodynamics_system.h`, `FlightModel`, `Propulsion`, or any
  flight-dynamics path (MLF-7).
- Modify `structural_integrity`, `flight_control_integrity`,
  `propulsion_integrity`, or any `AircraftDamageState` scalar (MLF-7).
- Modify `PlatformDamageState::loss_state` or `Health::current_hp` (MLF-7).
- Create, destroy, or detach ECS entities (MLF-8).
- Implement wreck/debris lifecycle (MLF-8).
- Implement Pk/statistical trends (MLF-9).
- Reopen sealed MLF-1 through MLF-5 packages.
- Claim deterministic kill, Pk authority, or real-weapon lethality.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-6A Boundary And Index` | main thread | n/a | Create MLF-6 v2 subproject with frozen D1-D7 decisions, corrected phase plan, task clusters, status, dispatch queue, acceptance draft, and parent navigation. | `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_structural_failure/**`, `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README*.md`, `docs/domains/air/README*.md` | runtime edits, probe implementation, worker dispatch | `git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_structural_failure docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/README*.md docs/domains/air/README*.md` | future agents can resume MLF-6 independently; README v2 with D1-D7 frozen | first, serial | 2 | complete |
| `MLF-6B Component Inventory` | main thread | n/a | Inventory every `ComponentDamageState` field MLF-6 will read, every F-16C component name from `f16c_block50.json` and TG-P7 split receivers, and every `structural_integrity` write site MLF-6 must NOT touch. | `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_structural_failure/missile_lethality_structural_failure_component_inventory_20260617.md` | runtime edits | doc diff check; referenced paths exist; every F-16C component listed with system group and structural parent region | inventory doc complete; ready for P2 mapping design | after 6A; serial | 1 | complete |
| `MLF-6C Break-Mode Mapping` | main thread | n/a | Design the component→break-mode classification table: each F-16C component classified into `wing_left`, `wing_right`, `tail_left`, `tail_right`, `vertical_tail`, `engine_left`, `engine_right`, `fuselage`, or `none`. Each structural group has an explicit cumulative integrity-drop threshold. | `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_structural_failure/missile_lethality_structural_failure_break_mode_mapping_20260617.md` | runtime edits | doc review; every component classified; no component is in two structural groups except the documented default-DB `wing_spar_center` cross-region case; thresholds are justified by engineering rationale | mapping table approved; ready for P3 implementation | after 6B; serial | 2 | complete |
| `MLF-6D State Machine` | main thread | n/a | Implement `StructuralFailureUpdate` ECS system: reads `ComponentDamageState`, applies P2 mapping rules, tracks per-airframe `breakup_state` and active `break_mode` set internally. Does NOT write events yet. Registers after `AircraftDamageStateUpdate`. | `src/components/combat/structural_failure.h`, `src/systems/combat/structural_failure_system.h`, `src/core/engine/simulation_kernel_systems.cpp`, `src/tests/test_structural_failure_system.cpp`, CMakeLists.txt | event writing, aerodynamics changes, structural_integrity changes, entity creation/deletion | `ef_test --test-suite=structural_failure_state`; `ctest --test-dir build-workshop -R ef_test_all --output-on-failure` | controlled ComponentDamageState inputs produce correct breakup_state and break_mode set; state is irreversible and cumulative; no ECS mutation beyond new `StructuralBreakupState` | after 6C; serial | 3 | complete |
| `MLF-6E Event Writer` | implementation worker (same as 6D or serial handoff) | n/a | Extend `StructuralFailureUpdate` to write `StructuralBreakupEvent` rows into `RecentEngagementEvents` when state transitions or new break modes activate. Populate all contract fields. | `src/systems/combat/structural_failure_system.h`, `src/core/interfaces/engagement_event_recorder.h`, `src/core/engine/simulation_kernel_engagement_event_store.*`, `src/runtime/facade/runtime_facade.cpp`, `src/tests/test_structural_failure_system.cpp` | aerodynamics, structural_integrity, loss-state, entity creation | `ef_test --test-suite=structural_failure_events`; facade/contract Python guards | controlled inputs produce correct StructuralBreakupEvent rows with traceable cause_event_id; no-damage baseline produces zero events; airframe_breakup only true for full_breakup | after 6D; serial | 3 | complete |
| `MLF-6F Diagnostics Export` | diagnostics worker | n/a | Add thin Python diagnostic probe consuming existing `StructuralBreakupEvent` and `structural_breakup_events` bindings (`bindings_runtime.cpp:449-457`, `bindings_core.cpp:540-`). No new binding surface; no duplicate export pipeline. | `tools/diagnostics/structural_breakup_export.py`, `tests/tools/test_structural_breakup_export.py` | new bindings, rewrite of existing diagnostics, aerodynamics, structural_integrity | `pytest -q tests/tools/test_structural_breakup_export.py` | probe exports breakup_state, break_mode, detached_part_ref, detached_part_count, airframe_breakup, cause_event_id per chain_id via existing facade/binding surface | after 6E; can parallel with 6G test authoring | 2 | complete |
| `MLF-6G Focused Tests` | main thread or test worker | n/a | Write focused C++ tests: wing_loss, tail_loss, engine_detach, fuselage_rupture, multi_axis, and no-damage zero-event. | `src/tests/test_structural_failure_system.cpp`, `CMakeLists.txt` | scenario-level tests, training tests, Python tests | `ctest --test-dir build-workshop -R structural_failure --output-on-failure` | every P2 break mode has a passing C++ test; zero-event baseline passes | after 6E; can parallel with 6F | 2 | complete |
| `MLF-6H Zero-Regression Smoke` | main thread | n/a | Run full air_combat and world_batch test suites; confirm zero regressions vs main. | test execution and obsolete-oracle test updates only | new features, scope expansion | `ctest --test-dir build-workshop -R ef_test_all --output-on-failure`; `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/` → `447 passed` | focused MLF-6 lanes green; broad air_combat/world_batch lane green | after 6E+6F+6G; serial | 2 | complete |
| `MLF-6I Acceptance And Archive` | main thread | n/a | Summarize evidence, update status, sync parent READMEs, prepare archive boundary, write residual map. | docs/index and local A2 archive registry | overclaiming real-weapon structural kill, Pk, debris lifecycle, or aerodynamics authority | docs diff check + referenced focused tests pass | accepted evidence matches the recorded tests; MLF-7/MLF-8 residuals explicit; archive movement complete by user instruction | after 6H; serial | 1 | complete / archived |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit the same normative table, event contract field,
  public API, or status line concurrently.
- 6D and 6E are preferably the same worker: the event writer extends the state
  machine's internal tracking.
- 6F and 6G can run in parallel after 6E completes (different write surfaces).
- 6H is serial after all implementation clusters pass.
- 6I is last, serial.
- If a cluster exceeds its round cap, stop and re-scope before adding a follow-up
  wave.
- Follow [Subagent Usage Policy](../../../../../../engineering/automation/standards/subagent_usage_policy.md).
- This queue only covers MLF-6. Do not enter MLF-7 (aerodynamics bridging,
  loss-state integration), MLF-8 (debris/wreck), or MLF-9 (Pk).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

For MLF-6D/6E specifically, the worker packet must also:
- List every `ComponentDamageState` field read and why.
- List every `StructuralBreakupEvent` field written and its source.
- Confirm no `structural_integrity`, `FlightModel`, `Propulsion`, `Health`, or
  `PlatformDamageState` field was modified.
- Confirm the system registers after `AircraftDamageStateUpdate`.

## Validation Plan

Core validation commands:

```bash
# C++ build
cmake --build build-workshop --target ef_core ef_py ef_test -j4

# State machine focused tests (after 6D)
./build-workshop/ef_test --test-suite=structural_failure_state

# Event writer focused tests (after 6E)
./build-workshop/ef_test --test-suite=structural_failure_events

# Break-mode focused tests (after 6G)
ctest --test-dir build-workshop -R structural_failure --output-on-failure

# Full regression (after 6H)
ctest --test-dir build-workshop -R ef_test_all --output-on-failure

# Python diagnostics (after 6F)
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q \
  tests/tools/test_structural_breakup_export.py

# Python regression (after 6H)
cmo_python -m pytest -q \
  tests/runtime/air_combat/ \
  tests/world_batch/
```

## Acceptance Criteria

- [x] `MLF-6A`: README v2 with D1-D7 frozen; parent navigation complete.
- [x] `MLF-6B`: Component inventory lists every `ComponentDamageState` field,
  every F-16C component with structural group, and every forbidden write site.
- [x] `MLF-6C`: Break-mode mapping table classifies every F-16C component;
  integrity thresholds are explicit and justified.
- [x] `MLF-6D`: State machine produces correct `breakup_state` and `break_mode`
  from controlled `ComponentDamageState` inputs; state is irreversible.
- [x] `MLF-6E`: `StructuralBreakupEvent` rows are correct and traceable;
  no-damage baseline produces zero events; `airframe_breakup` only for
  `full_breakup`.
- [x] `MLF-6F`: Python probe exports breakup facts per `chain_id`.
- [x] `MLF-6G`: Every P2 break mode has a passing focused C++ test.
- [x] `MLF-6H`: Full air_combat/world_batch suites are green after
  obsolete-oracle updates.
- [x] `MLF-6I`: Residual map and archive boundary are explicit; package is
  accepted / archived.

## Residual Map

Immediate:

- `MLF-6H`: broader air_combat/world_batch regression smoke is green:
  `447 passed`.
- `MLF-6I`: archive movement completed by explicit user instruction.

Follow-on (explicitly deferred to named MLF phases):

- **MLF-7**: Aerodynamics bridging — read `StructuralBreakupEvent`, set
  `structural_integrity` or bridge directly to flight dynamics. Write surface:
  `damage/air/physics/tests`.
- **MLF-7**: Loss-state integration — decide whether `full_breakup` implies
  `PlatformLossState::Lost`. Write surface: `damage/air`.
- **MLF-8**: Debris/wreck lifecycle — create persistent world entities from
  `detached_part_ref` string labels. Write surface: `runtime/tests`.

Deferred:

- Pk/statistical calibration (MLF-9).
- AIM-120C/MQ-9 structural-kill calibration (MLF-10).
- Naval/ground platform structural failure.
