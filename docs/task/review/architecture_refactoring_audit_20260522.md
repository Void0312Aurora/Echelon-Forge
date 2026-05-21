# Architecture Refactoring Audit — God Files, Legacy Code, And Structural Inconsistencies

Status: `2026-05-22` compiled from cross-codebase architecture audit.
Scope: 364 files (197 .h + 49 .cpp + 118 .py) across three parallel analysis streams.

## 1. Executive Summary

This audit identifies **31 distinct findings** — 4 critical, 13 high, 9 medium, 5 low.

The most severe systemic issues:
1. **Three god files** >1600 lines each handling 5+ distinct responsibility domains
2. **`legacy_command.h`** still consumed by 11 C++ systems as the primary command surface
3. **`RuntimeFacade`** is not a true facade — `runtime()` escape hatch is the default access path
4. **Flat aggregate inheritance** — every entity carries all domain fields; `LeaderIntentCore` verbatim mirrors `MissionCommandCore`
5. **ECS ordering is implicit** (registration order), not machine-checkable

---

## 2. God Files (Critical)

### F-001: `counterfactual_replay_contracts.h` — 2342 Lines

**Severity:** CRITICAL | **File:** [src/runtime/contracts/counterfactual_replay_contracts.h](src/runtime/contracts/counterfactual_replay_contracts.h)

159 constants, 18 structs, 40 inline validation functions across 6 domains in 1 file:
replay envelopes, branch points, worldline metadata, experiment requests, scenario generation, evidence bridge.

**Recommendation:** Split into 5+ files: constants, replay_types, worldline_types, experiment_types, scenario_generation_types, plus validation .cpp.

### F-002: `runtime_facade.cpp` — 2809 Lines

**Severity:** CRITICAL | **File:** [src/runtime/facade/runtime_facade.cpp](src/runtime/facade/runtime_facade.cpp)

7+ responsibility areas: track helpers, fidelity/spawn translation, platform materialization, counterfactual replay, experiment evidence, event sorting/export, facade orchestration. Four scattered `using namespace runtime::counterfactual` blocks.

**Recommendation:** Split into: core orchestration, counterfactual_facade, event_export_packager, track_helpers.

### F-003: `runtime_window_coordinator.h` — 1646 Lines (Header-Only)

**Severity:** CRITICAL | **File:** [src/runtime/facade/runtime_window_coordinator.h](src/runtime/facade/runtime_window_coordinator.h)

125+ inline functions, zero .cpp counterpart. Any change recompiles `runtime_facade.cpp`.

**Recommendation:** Create .cpp, extract cadence logic into separate module.

### F-004: `default_unit_factory.h` — 1457 Lines, 35 #includes

**Severity:** CRITICAL | **File:** [src/models/core/default_unit_factory.h](src/models/core/default_unit_factory.h)

Highest include count in any .h file. Single point of change for all unit definitions.

**Recommendation:** Split by domain: default_aircraft_factory, default_naval_factory, default_ground_factory.

### F-005: Contract Files >300 Lines — Universal Mixing Pattern

**Severity:** HIGH | **Files:** 7 of 9 contracts in `src/runtime/contracts/`

Every contract >300 lines mixes constants + struct definitions + inline validation in one header.

**Recommendation:** Extract constants to `*_constants.h`, move validation to `*_validation.cpp`.

### F-006: Python Profile Structural Duplication

**Severity:** HIGH | **Files:** `air_profile.py` (652L), `naval_profile.py` (540L), `ground_profile.py` (297L)

All three implement an identical 12-function template. `normalize_task_order_spec()` alone is 100+ lines each with structurally identical sections.

**Recommendation:** Extract shared normalization into parameterized base in `common_core_base.py`.

### F-007: Python Adapter Triplication

**Severity:** LOW | **Files:** 3 adapter files (~50 lines each)

Structurally identical templates differing only in imported `*_profile` module.

**Recommendation:** Replace with parameterized factory in `bridge.py`.

---

## 3. Legacy Code

### L-001: `legacy_command.h` — 11 Active System Consumers

**Severity:** HIGH | **File:** [src/components/command/legacy_command.h](src/components/command/legacy_command.h)

11 C++ systems still actively use `MovementCommand` and `ActionCommand`. Each physics system independently implements dual-path resolution: "check PilotAction first, fall back to legacy MovementCommand." No centralized resolution.

**Recommendation:** Consolidate to `PilotAction` only, or create a single `CommandResolution` bridge system.

### L-002: `RuntimeFacade.runtime()` Escape Hatch = Default Path

**Severity:** HIGH | **File:** `python/rl/runtime/world_batch/adapter.py:49`

Doc says "legacy adapters only," but `adapter.py` uses it as the primary batch target. Three other escape hatches exist: `SingleWorldBatchRuntime.sim()`, `WorldBatchVecEnv.batch_runtime`, `LeaderWorldBatchRuntime.batch_runtime`.

**Recommendation:** Implement real facade operations; deprecate or rename escape hatch.

### L-003: Direct `loader.sim.*` Calls Bypass Facade

**Severity:** HIGH | **File:** `leader_tasking.py` (10+ sites), contract tests (50+ sites)

`leader_tasking.py:486-496` directly calls `loader.sim.set_task_order/intent/report()`. Production code bypassing the facade.

**Recommendation:** Route through `tasking_bridge` or `RuntimeFacade`.

### L-004: `loader.mission_cmd` Universally Raw Dict

**Severity:** MEDIUM | **Files:** 10+ files

Every consumer uses `getattr(loader, "mission_cmd", {}) or {}` then `.get("field", default)`. No typed DTO.

**Recommendation:** Create `MissionCommandDTO`, migrate consumers progressively.

### L-005: Legacy Runtime Mode Still First-Class

**Severity:** MEDIUM | **Files:** `env_config.py:9-11`, `scenario_loader/common.py`

"legacy" is a valid, documented first-class runtime mode. `terrain_type = "legacy"` is hardcoded default in both C++ and Python.

**Recommendation:** Gate legacy mode behind explicit opt-in flag.

### L-006: Legacy Benchmark Reimplementations

**Severity:** LOW | **Files:** `tools/diagnostics/benchmarks/`

Python reimplementations of C++ spatial queries in benchmark directory. Correctly scoped. No immediate action.

### L-007: Temporary Stability Hacks

**Severity:** LOW | **File:** `rotational_system.h:123`

`"Damping (temporary stability hack until Aerodynamics provides damping)"` — no expiration plan.

### L-008: `leader_tasking.py:210` Hardcodes Air Profile

**Severity:** MEDIUM | **File:** [leader_tasking.py:210](python/rl/tasking/leader_tasking.py#L210)

`return _air_profile.build_kernel_mission_command(loader)` — always air, even for naval/ground.

**Recommendation:** Replace with `tasking_bridge.build_kernel_mission_command(loader)`.

---

## 4. Architecture Documentation vs Reality

### A-001: `spawn_unit(type_name)` Is The Only Path

**Severity:** HIGH | **File:** `runtime_facade.cpp:261-279`

Architecture Law 15 targets `spawn_platform({capabilities...})` but `TypedPlatformSpawnRequest` explicitly converts back to legacy `WorldSpawnRequest`. WP20 acceptance review states this is accepted transitional state.

### A-002: Implicit ECS Ordering

**Severity:** HIGH | **File:** [simulation_kernel_systems.cpp:164-166](src/core/engine/simulation_kernel_systems.cpp#L164-L166)

Code admits design smell. No `depends_on` or custom pipeline phases used. Post-ECS manual query loop for naval weapon fire runs outside ECS frame.

### A-003: Information State Model Bypassed

**Severity:** MEDIUM | **Files:** `leader_tasking.py`, `agent_shim.py`

`leader_tasking.py:355` reads raw truth via `get_agent_observation()`. Known transitional; gated by WP21.

### A-004: `common_core_profile.py` Contains Air-Specific Logic

**Severity:** MEDIUM | **File:** [common_core_profile.py](python/rl/tasking/common_core_profile.py)

Line 76 defaults to `"air"`. Lines 182-208 define air-specific inference functions. Lines 446-488 repeat `if profile_name == "ground"` special-casing 3 times.

**Recommendation:** Move air functions to air_profile. Replace repeated ground special-cases with profile-provided function.

### A-005: Monkey-Patching `ef_py`

**Severity:** LOW | **File:** `common_core_profile.py:18-22`

Runtime injection of `ef_py` into profile modules to work around circular imports.

### A-006: Flat Aggregates — Domain Bleed

**Severity:** HIGH | See S-001 through S-004 below.

---

## 5. ECS & DTO Structural Issues

### S-001: Flat Multiple-Inheritance Aggregates

**Severity:** HIGH | **Files:** `mission_command.h`, `task_order.h`, `leader_intent.h`, `pilot_report.h`

All four aggregates use `struct X : XCore, XAir, XNaval {};`. Domain bleed: aircraft carries Naval fields, ships carry Air fields. `LeaderIntentCore` lines 17-25 are a verbatim mirror of `MissionCommandCore` lines 7-21 (10 identical fields).

### S-002: Recovery/Takeoff Fields Triplicated

**Severity:** HIGH | **Files:** `*_air.h` variants

Same 7 air-domain fields in `MissionCommandAir`, `TaskOrderAir`, `LeaderIntentAir`. Formation fields use different representations across aggregates.

### S-003: Naval Domain Inconsistently Decomposed

**Severity:** MEDIUM

MissionCommandNaval: 7 fields. TaskOrderNaval: 3. LeaderIntentNaval: 2. PilotReportNaval: 2.

### S-004: `WorldBatchRuntime` — 36 Methods, 7 Areas

**Severity:** HIGH | **File:** [world_batch_runtime.h](src/core/engine/world_batch_runtime.h)

Three spatial query methods share ~90% identical code. `apply_world_setup_batch` processes 6 operations in one closure.

**Recommendation:** Decompose into WorldPoolManager, ExecutionEpisodeOrchestrator, SpatialQueryService, EnvironmentConfigurator.

### S-005: SimulationKernel Exposes 55+ Methods To Python

**Severity:** MEDIUM | **File:** [bindings_core.cpp:431-956](src/interfaces/python/bindings_core.cpp#L431-L956)

Python can read/write any ECS component directly through bindings.

### S-006: PilotWeaponRelease Inline Definition

**Severity:** LOW | **File:** `simulation_kernel_systems.cpp:191-198`

Only system defined inline; all others use `register_*_system(ecs)` pattern.

---

## 6. Cross-Cutting Patterns

### The Dual-Path Anti-Pattern

| Domain | New Path | Legacy Path | Resolution |
|--------|----------|-------------|------------|
| Command | `PilotAction` | `MovementCommand` | Per-system fallback |
| Spawning | `TypedPlatformSpawnRequest` | `spawn_unit(type_name)` | Typed→legacy conversion |
| Runtime | `compiled` | `legacy` | Config flag |
| Flight shaping | `compiled`, `gpu_host` | `legacy`, `python` | Config flag |
| Observation | `ObservationBatchPacket` | `get_agent_observation()` | Adapter dispatch |
| Mission cmd | `RuntimeFacade` | `loader.sim.*` | Bridge dispatch |

### The Escape-Hatch Pattern

Four places expose internal runtime objects directly to Python callers.

---

## 7. Complete Index

| ID | Category | Severity | Title |
|----|----------|----------|-------|
| F-001 | God File | CRITICAL | counterfactual_replay_contracts.h — 2342 lines, 6 domains |
| F-002 | God File | CRITICAL | runtime_facade.cpp — 2809 lines, 7+ areas |
| F-003 | God File | CRITICAL | runtime_window_coordinator.h — 1646 lines header-only |
| F-004 | God File | CRITICAL | default_unit_factory.h — 1457 lines, 35 includes |
| F-005 | God File | HIGH | 7 contract files >300 lines mix constants+types+validation |
| F-006 | Duplication | HIGH | Profile 12-function structural duplication |
| F-007 | Duplication | LOW | Adapter file triplication |
| L-001 | Legacy | HIGH | legacy_command.h — 11 active consumers |
| L-002 | Legacy | HIGH | Facade.runtime() escape hatch is default path |
| L-003 | Legacy | HIGH | loader.sim.* direct calls bypass facade |
| L-004 | Legacy | MEDIUM | loader.mission_cmd universally raw dict |
| L-005 | Legacy | MEDIUM | Legacy runtime mode first-class |
| L-006 | Legacy | LOW | Legacy benchmark reimplementations |
| L-007 | Legacy | LOW | Stability hacks in physics |
| L-008 | Legacy | MEDIUM | leader_tasking.py:210 hardcodes air |
| A-001 | Doc vs Reality | HIGH | spawn_unit is only spawning path |
| A-002 | Doc vs Reality | HIGH | ECS ordering is implicit registration order |
| A-003 | Doc vs Reality | MEDIUM | Information state model bypassed |
| A-004 | Doc vs Reality | MEDIUM | common_core contains air-specific logic |
| A-005 | Doc vs Reality | LOW | Monkey-patching ef_py |
| A-006 | Doc vs Reality | HIGH | Flat aggregates carry all domain fields |
| S-001 | ECS/DTO | HIGH | Flat inheritance — domain bleed |
| S-002 | ECS/DTO | HIGH | Recovery fields triplicated |
| S-003 | ECS/DTO | MEDIUM | Naval domain inconsistent |
| S-004 | ECS/DTO | HIGH | WorldBatchRuntime 36 methods, 7 areas |
| S-005 | ECS/DTO | MEDIUM | Kernel exposes 55+ methods to Python |
| S-006 | ECS/DTO | LOW | PilotWeaponRelease inline definition |

## 8. Recommended Remediation Order

**Wave 1 — Docs only:** Acknowledge A-001, A-003 as accepted transitional. Document L-007 expiration criteria.

**Wave 2 — Low-risk cleanup:** L-008 (fix air hardcode), S-006 (extract system), A-005 (remove monkey-patch), F-007 (unify adapters).

**Wave 3 — Medium restructuring:** A-004 (purge air from common_core), F-003 (split coordinator .h/.cpp), F-006 (extract shared profile base), L-004 (typed MissionCommandDTO), L-005 (gate legacy mode).

**Wave 4 — Major refactoring:** F-001 (split counterfactual contracts), F-002 (split facade.cpp), F-004 (split unit factory), F-005 (extract contract validation), S-004 (decompose WorldBatchRuntime).

**Wave 5 — Architecture-level:** S-001/S-002/A-006 (replace flat aggregates), L-001 (resolve dual command path), L-002/L-003 (close facade escape hatches), A-002 (explicit ECS pipeline phases), S-005 (restrict kernel binding).
