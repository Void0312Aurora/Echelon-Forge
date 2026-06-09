<!-- Machine-translated draft generated on 2026-05-18 from docs/task/code_redundancy/code_redundancy_followup_freeze_20260516.zh.md. Review before treating this file as authoritative. -->

# Code Redundancy Optimization Subsequent Freeze Plan

Status: `2026-05-16` freeze execution version; `2026-05-16` WP-A / WP-B / WP-C all closed

Related documents:

- [Code Redundancy and Duplicate Logic Audit Report](code_redundancy_duplication_audit_20260516.zh.md)
- [Common / Air / Naval Module Split Freeze Plan](../../common_air_naval/common_air_naval_modular_split_plan_20260515.zh.md)

Document positioning:

- This document is used to converge optimization items **still pending** after the `2026-05-16` audit and suitable for continued advancement outside the main `scenario_loader` line.
- This document freezes only a narrow scope of "compatibility layer boilerplate compression + low-risk shared extraction + minimal test reinforcement".
- This document does not authorize expansion into the `gym_envs/scenario_loader/*` split mainline, nor does it authorize advancing new large-file splits under the guise of "tidying up".

Verification criteria: When involving Python / nanobind / runtime implementations, the default acceptance uses local build artifacts and the repository virtual environment, i.e.:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop \
  ./.venv/bin/python -m pytest
```

If only local C++ helper / document adjustments are made, phase acceptance with a focused test set is allowed; whenever the `ef_py` binding visible surface is touched, a `cmake --build build-workshop --target ef_py -j4` must be performed.

## 1. Current Baseline

According to the audit document and completed implementations, the following items have completed the first round or substantial closure in the current mainline:

1. `3.1` Duplicate registration of `MassProperties` has been deleted.
2. `3.3` The three types of pending delivery logic in `command_link_system.h` have been templated.
3. `3.4` The clone of `TaskOrder / LeaderIntent / PilotReport` on the Python side has been changed to reflection-driven, with field consistency checks.
4. `4.1` The `MovementCommand` compatibility chain has completed three batches of low-risk boilerplate closure:
   - throttle / brake fallback helper
   - legacy movement / lagged / pending movement helper
   - action / pending action / pending mission helper
5. `5.6` `EGI -> InstrumentState` has completed the "navigation state surface -> instrument projection surface" boundary closure.
6. `5.7` Ground track calculation has been unified to `Math::ground_track_deg_from_velocity()`.
7. `5.8` The main runtime attitude rotation generalization is complete; simplified approximations in weapon effect models are retained temporarily.
8. `5.12` The mission obs taxonomy has been changed to a combination of base fields + incremental fields, with direct test coverage.
9. `5.13` The `env_config.py` merge helper has been extracted, with optional merge direct unit test added.
10. `5.4` Scripted controllers have completed the minimum shared skeleton closure:
    - New `python/rl/control/base_scripted_controller.py`
    - Three controllers share `action_dim/dt`, `obs -> np.ndarray` unpacking, zero-action construction, and angle wrap helper
    - Public class names and construction signatures remain unchanged, focus controller contracts have passed regression
11. `3.2` / `5.10` Completed the first batch of boundary reinforcement:
    - `MassUpdate` now explicitly uses `Mass` as the authoritative runtime decomposed mass, and synchronizes `MassProperties.empty_mass_kg/current_total_mass_kg`
    - Added minimum debug readback surface and focused regression, fixed mass component synchronization relationships
    - Added direct tests for `MissionCommand / PilotAction / CommPacket` binding surfaces, tightening nanobind third maintenance surface risk

Therefore, no further expansion around the above completed items is continued; they are retained only as the current baseline record.

## 2. Remaining Items Buckets

### 2.1 Items Allowed to Proceed Under This Freeze Version

Current status: All authorized items under this freeze version have completed their current round of closure, and **no active implementation items are retained**.

Authorized closed items:

1. `4.1` Remaining low-risk boilerplate and consumer closure in the `MovementCommand` compatibility chain.
2. `5.14` Entity validate / warn boilerplate closure in `simulation_kernel_command_api.cpp`.
3. `3.2` `Mass` / `MassProperties` dual-track mass component boundary analysis and first-stage minimal implementation.
4. `5.10` Nanobind third maintenance surface status clarification and test reinforcement.

### 2.2 Explicitly Deferred Under This Freeze Version

The following items are not suitable for further development at the current stage:

1. `4.2` `common_core_profile.py` bridge and profile commonality re-abstraction.
2. `4.3` `leader_env.py` large-file responsibility split.
3. `4.4` `air_profile.py` / `naval_profile.py` common base class abstraction.
4. `5.5` `world_batch_vec_env.py` / `cooperative_world_batch_vec_env.py` deep infrastructure merge.
5. `5.16` `training_callbacks.py` and `world_model/dreamer.py` large-file splits.

These items either have risks significantly outweighing current benefits or are deeply coupled with the parallel development boundary of air/sea, requiring a separate freeze document.

### 2.3 Items Prohibited Under This Freeze Version

The following items are **not authorized for implementation** in this round:

1. `5.3` `gym_envs/scenario_loader/core.py` split.
2. `5.11` `gym_envs/scenario_loader/execution_runtime/shaping.py` abstraction closure.
3. `5.15` `execution_runtime/mainline.py` / `shadow.py` dual-write reorganization.
4. Any structural rearrangements that would affect the ongoing parallel integration work in `gym_envs/scenario_loader/*`.

Reasons:

- The user has explicitly indicated that `gym_env` is being split;
- Another parallel integration branch exists in the current repository;
- Continuing to extend audit optimization into that mainline would easily cause duplicate work and merge conflicts.

## 3. Overall Strategy

This freeze version adopts a "three-phase closure" strategy:

1. First continue compressing **compatibility layer boilerplate**, trying to converge high-frequency initialization, entity validation, and helper dispatch into shared primitives.
2. Then handle **light shared skeleton extraction**, extracting only script controllers that already have focused contracts, without touching heavier runtime/env large files.
3. Finally, only do **boundary clarification + minimal test reinforcement**, not starting new large refactorings within this plan.

Core principles:

1. Code implementation takes priority over further analysis, but every step must have clear stop conditions.
2. Each phase must be independently verifiable; any cross-phase new scope must be documented separately.
3. Content listed as "deferred" or "prohibited" in the document must not be brought into implementation because "it can be done while we're at it".

## 4. Freeze Work Packages

### WP-A: Compatibility Chain and Command API Boilerplate Continued Closure

Objectives:

- Complete the convergence judgment for `4.1` remaining low-risk consumers.
- Prioritize `5.14`, reducing repetitive entity parsing and invalid guard boilerplate in `simulation_kernel_command_api.cpp`.
- Extract only if the helper does not change the public API.

Freeze scope:

- [src/core/engine/simulation_kernel_command_api.cpp](../../../../src/core/engine/simulation_kernel_command_api.cpp)
- [src/components/command/legacy_command.h](../../../../src/components/command/legacy_command.h)
- [src/components/command/command_link.h](../../../../src/components/command/command_link.h)
- When necessary, allowed to touch:
  - [src/systems/core/operation_system.h](../../../../src/systems/core/operation_system.h)
  - [src/systems/physics/control_system.h](../../../../src/systems/physics/control_system.h)

Explicitly not doing:

1. Not marking `MovementCommand` as `[[deprecated]]` in this phase.
2. Not deleting `MovementCommand` / `LaggedCommand` / `PendingMovementCommand` compatibility chains in this phase.
3. Not extending this helper to observation / visual API comprehensively.

Acceptance criteria:

1. `cmake --build build-workshop --target ef_py -j4` passes.
2. The following focused regressions remain passing:
   - `tests/runtime/mission/test_mission_command_split_semantics.py`
   - `tests/runtime/mission/test_mission_runtime.py`
   - `tests/world_batch/test_world_batch_runtime.py`
3. The status of audit items `4.1` and `5.14` is updated synchronously.

Current execution record:

1. First batch completed: Invalid guard / world time / active-copy helperization in `simulation_kernel_command_api.cpp`.
2. Second batch completed: Seed initialization boilerplate closure for `MovementCommand` / `LaggedCommand` in `operation_system.h`.
3. Confirmed that `control_system.h` will not be further abstracted at this stage; it retains only scheduling/forwarding responsibility and is not a new closure surface for this phase.

Stop condition:

- Once helper extraction would require changing API behavior, entity lifecycle semantics, or large-scale cross-file linkage, stop immediately and move to subsequent candidates, not continuing in this phase.

### WP-B: Scripted Controller Minimal Shared Skeleton Extraction

Objectives:

- Address `5.4` shared interface/input unpacking duplication among three scripted controllers.
- Extract a minimal `BaseScriptedController` or equivalent shared helper, but keep existing controller names and entry points unchanged.

Freeze scope:

- [python/rl/control/scripted_takeoff.py](../../../../python/rl/control/scripted_takeoff.py)
- [python/rl/control/scripted_stable_flight.py](../../../../python/rl/control/scripted_stable_flight.py)
- [python/rl/control/scripted_landing.py](../../../../python/rl/control/scripted_landing.py)
- Allowed to add:
  - `python/rl/control/base_scripted_controller.py`
  - Or a lightweight shared helper module in the same directory

Explicitly not doing:

1. Not rewriting the control laws themselves.
2. Not changing the dependency pattern of the contract runner on the three public controller class names.
3. Not extending this phase into a script baseline refactoring of `wrappers.py` / `leader_env.py`.

Acceptance criteria:

1. The following contracts/tests remain passing:
   - `tests/contracts/unit/controllers/scripted_takeoff_takeoff2_throttle.json`
   - `tests/contracts/unit/controllers/scripted_takeoff_clearance_hold.json`
   - `tests/contracts/unit/controllers/scripted_landing_controller.json`
   - `tests/contracts/unit/controllers/scripted_stable_flight_rudder_sign.json`
2. If a new shared helper is added, the three controllers' public construction signatures remain compatible.
3. Audit item `5.4` status updated to "completed" or "first batch closure".

Current execution record:

1. Added [python/rl/control/base_scripted_controller.py](../../../../python/rl/control/base_scripted_controller.py), unifying `action_dim/dt` storage, `obs` array unpacking, zero-action construction, and `wrap_deg()`.
2. Changed [scripted_takeoff.py](../../../../python/rl/control/scripted_takeoff.py), [scripted_stable_flight.py](../../../../python/rl/control/scripted_stable_flight.py), and [scripted_landing.py](../../../../python/rl/control/scripted_landing.py) to use the shared helper, without modifying control law bodies or public class names/construction signatures.
3. Added missing `type: "unit_regression"` metadata to [tests/contracts/unit/controllers/scripted_takeoff_clearance_hold.json](../../../../tests/contracts/unit/controllers/scripted_takeoff_clearance_hold.json) so it can be dispatched and executed by the unified contract runner.
4. Completed the following focused verifications:
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/controllers/scripted_takeoff_takeoff2_throttle.json`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/controllers/scripted_takeoff_clearance_hold.json`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/controllers/scripted_landing_controller.json`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/controllers/scripted_stable_flight_rudder_sign.json`

Stop condition:

- As soon as extraction starts requiring changes to large env/wrapper call chains, stop immediately, retain as a helper closure within a single directory, and do not extend outward.

### WP-C: Mass Component and Binding Maintenance Surface Boundary Freeze

Objectives:

- For `3.2` and `5.10`, only do "boundary clarification + minimal reinforcement", not full-scope refactoring.
- Clarify the first-stage closure strategy for `Mass` / `MassProperties`.
- Clarify the reasonable boundary of nanobind bindings as a maintenance surface and the minimal test guarantees needed.

Freeze scope:

- [src/components/physics/dynamics.h](../../../../src/components/physics/dynamics.h)
- [src/components/systems/logistics.h](../../../../src/components/systems/logistics.h)
- [src/systems/systems/logistics_system.h](../../../../src/systems/systems/logistics_system.h)
- [src/interfaces/python/bindings_command.cpp](../../../../src/interfaces/python/bindings_command.cpp)
- [tests/leader/test_two_ship_contract_fields.py](../../../../tests/leader/test_two_ship_contract_fields.py)
- Allowed to add minimal regression tests targeting mass component boundaries

Explicitly not doing:

1. Not deprecating the `Mass` component in this phase.
2. Not converting all consumers to read-only `MassProperties` at once.
3. Not generating a new automatic binding system; not replacing the existing nanobind `.def_rw(...)` pattern.

Acceptance criteria:

1. Any code changes must come with focused tests proving no behavioral regression in `Mass` / `MassProperties`.
2. `bindings_command.cpp` is only allowed minimal reinforcement related to maintenance surface consistency; not allowed to expand into full automation refactoring.
3. Audit items `3.2` and `5.10` statuses and subsequent recommendations updated synchronously.

Current execution record:

1. In [src/systems/systems/logistics_system.h](../../../../src/systems/systems/logistics_system.h), tightened `MassUpdate` to the first-stage boundary: "`Mass` is the authoritative runtime decomposed mass; `MassProperties` only mirrors `empty/total` readings":
   - `rigid_mass.fuel_mass_kg` continues to be driven by `FuelSystem`;
   - `MassProperties.empty_mass_kg` and `current_total_mass_kg` are now explicitly mirrors of `Mass`'s `empty` and `get_total_kg()`;
   - Therefore `MassProperties.current_total_mass_kg` no longer misses `stores_mass_kg`.
2. Added minimal debug readback surfaces:
   - [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
   - [simulation_kernel_observation_api.cpp](../../../../src/core/engine/simulation_kernel_observation_api.cpp)
   - [bindings_core.cpp](../../../../src/interfaces/python/bindings_core.cpp)
   For test-time reading of `[mass_empty, mass_fuel, mass_stores, mass_total, props_empty, props_total]`, not extended to a general component exposure surface.
3. Added focused tests:
   - [tests/runtime/core/test_mass_component_boundary.py](../../../../tests/runtime/core/test_mass_component_boundary.py)
   - [tests/runtime/bindings/test_bindings_command_surface.py](../../../../tests/runtime/bindings/test_bindings_command_surface.py)
4. Completed the following acceptance:
   - `cmake --build build-workshop --target ef_py -j4`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest tests/runtime/core/test_mass_component_boundary.py -q`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest tests/runtime/bindings/test_bindings_command_surface.py -q`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest tests/leader/test_two_ship_contract_fields.py -q`
   - `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest tests/runtime/bindings/test_command_api_entity_guards.py tests/runtime/mission/test_mission_command_split_semantics.py -q`

Stop condition:

- Once a cross-system migration across `aerodynamics / force / leapfrog / logistics` is needed, stop immediately at the "analysis + freeze boundary" layer, and do not continue code implementation within this plan.

## 5. Phase Order

Fixed order as follows:

1. `WP-A`: First continue compressing command compatibility chain boilerplate.
2. `WP-B`: Then handle scripted controller minimal shared skeleton.
3. `WP-C`: Finally only do mass component and binding maintenance surface boundary freeze or minimal reinforcement.

Reasons for no order skipping:

1. `WP-A` directly connects to the helperization mainline already underway; regression surface is most controllable.
2. `WP-B` has existing contracts, enabling stable small-step extraction.
3. `WP-C` has the highest risk; must decide after the first two rounds are fully closed whether to implement or only update boundary documentation.

## 6. Freeze Rules

1. New items outside this document must not directly enter implementation.
2. Any optimization requests involving `gym_envs/scenario_loader/*` are all deferred to the parallel mainline; not advanced under the guise of this document.
3. If a phase encounters a situation where "splitting a large file is necessary to continue", it is considered beyond the scope of this freeze version; should stop and be independently chartered.
4. Document updates must be synchronized with code state; must not retain a "done but document still says pending" state.
5. Upon completing each work package, record an "execution update" in the audit document to avoid redundant judgments later.

## 7. Definition of Done

This freeze version is considered complete when all of the following are met:

1. `WP-A`, `WP-B` are completed and pass their respective focused acceptances.
2. `WP-C` has at least completed boundary conclusion freeze; if code is implemented, corresponding tests must pass.
3. The "remaining items" lists in the audit document and this plan document are synchronously converged, with no completed items still appearing in the "cut-in immediately" list.

**2026-05-16 Completion Confirmation**:

1. `WP-A`, `WP-B`, `WP-C` are all completed, with respective execution updates and focused acceptance results recorded.
2. This document's `2.1` no longer retains active implementation items.
3. If the topic is to be continued later, it should transition to a "next freeze document" instead of further expansion on this document.

## 8. Subsequent Candidates (Requires Separate Freeze)

The following directions are not part of this plan but may become candidates for the next freeze document:

1. `leader_env.py` command encoding/decoding / observation builder split.
2. `world_batch_vec_env.py` / `cooperative_world_batch_vec_env.py` infrastructure mixinization.
3. Commonality sinking of `common_core_profile.py` and `air/naval_profile.py`.
4. True single-authority component migration of `Mass` / `MassProperties`.
5. Audit backfill after the `scenario_loader` mainline split is complete.

These items must be separately formed into a new convergence document after the current freeze version is closed.
