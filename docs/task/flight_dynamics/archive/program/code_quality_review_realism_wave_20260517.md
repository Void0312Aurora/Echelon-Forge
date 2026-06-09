<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/program/code_quality_review_realism_wave_20260517.zh.md. Review before treating this file as authoritative. -->

# Realism Advancement Code Quality Review

Status: `2026-05-17` Review Freeze Version.

Scope: All 170 files of the P0 + P1 realism advancement have uncommitted changes (+5,022 / -759 lines),
covering 56 modified files and 10 new C++ files under `src/`.

Associated documents:

- [Realism Task Master Table](realism_program_taskboard_20260516.zh.md)
- [Realism P1 Task Master Table](realism_program_p1_taskboard_20260517.zh.md)
- [Current Status of Realism Mainline](realism_program_current_status_20260517.zh.md)
- [Flight Dynamics Analysis](../flight/flight_dynamics_realism_analysis_20260516.zh.md)
- [Sensor Analysis](../sensor_situation/sensor_situation_realism_analysis_20260516.zh.md)
- [Weapon Analysis](../weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md)
- [Naval Analysis](../naval/naval_realism_analysis_20260516.zh.md)
- [C2 Analysis](../c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md)

Document positioning:

- This document does not repeat the physical realism analysis of each domain; it only reviews the structural quality of this code change.
- It focuses on evaluating cross-boundary coupling, God Object tendency, duplicate code, and architecture degradation risks.

---

## 1. Overall Assessment

The physical functionality gains from this round of realism advancement are substantial – all five domains have reached P0 usability.
However, several issues in code structure require attention: **God Factory swelling, cross-domain contamination in the content layer,
duplicate definitions, linear growth of the Kernel API, and boundary backflow and high-coupling hot spots in the Python orchestration layer.**

The good news is that these problems are still in an "early emerging" stage, with low correction cost. But if left unaddressed,
they will solidify into architectural debt after two or three more rounds of similar progress.

---

## 2. Issues Requiring Immediate Attention

### 2.1 default_unit_factory.h: God Factory Forming

**Current state:** 845 lines, 27 `#include`, include chain covering all domains:

```
command → combat → physics → sensors → naval → content → core
```

`make_factory_default_sensor()` (94-line inline function) creates sensors for aircraft, missiles, ships,
facilities, and C2 nodes – default values for all domains are concentrated in a single function.

Problems:

- **Domain knowledge leakage.** A factory should not simultaneously know "F-16 radar parameters", "DDG-51 sensor package",
  and "submarine quiet speed". These are objects from different problem domains, belonging to separate factories.
  The correct division should be `DefaultAirUnitFactory` / `DefaultSurfaceUnitFactory` /
  `DefaultSubsurfaceUnitFactory`, each holding only its own domain parameters.
- **Universal default anti-pattern.** All five built-in default types of the factory call the same
  `make_factory_default_sensor()` modifying only the last two parameters. Besides the sensor type enum,
  they use `max_range=30000m, fov_deg=120°` as the universal default for all platforms –
  this is physically wrong (the detection range of AN/SPS-67 should be the radar horizon constrained 46.3km,
  not the same universal 30km as airborne radar).
- **Header file is too heavy.** All 845 lines are in `.h`, so every `#include` change triggers
  large-scale recompilation.

**Specific code locations:**

- `make_factory_default_sensor()`: lines 49-94 (46-line inline default value initialization)
- `class DefaultUnitFactory`: lines 97-845 (745-line method body)
- Sensors for aircraft/missiles/ships/facilities/C2 five types use the same function with only `sensor_type` changed

### 2.2 unit_definition.h: Content Layer Domain Contamination

**Current state:** 164 lines. Originally pure data definitions (cross-domain DTOs), this round added runtime component dependencies:

```cpp
#include "components/systems/sonar.h"
#include "components/naval/embarked_air_ops.h"
#include "components/naval/ship_platform.h"
#include "components/naval/submarine_platform.h"
#include "components/physics/flight_dynamics_tuning.h"
```

Problems:

- `UnitDefinition` semantically is an "intermediate data container after JSON loading" and should only depend on basic types and
  its own domain content. Introducing `sonar.h` (runtime sensor logic), `ship_platform.h`
  (runtime physics component), `submarine_platform.h` (runtime physics component),
  `flight_dynamics_tuning.h` (model layer tuning parameters) pollutes the content layer with compile-time dependencies on the runtime component graph.
- The newly added `NavalStoresDefinition` / `NavalLogisticsDefinition` are placed under
  `content/unit_definition.h`. Their natural home should be
  `components/naval/ship_logistics.h` – they are ship domain data structures,
  not cross-domain content definitions.

### 2.3 Duplicate Definition of Vec3

`missile_guidance_math.h` (new file) defines:

```cpp
namespace missile_guidance { struct Vec3 { double x, y, z; }; }
// operator+, operator-, operator*, operator/, dot, cross, norm, normalize...
```

But the project already has an equivalent type in `components/basic/common.h`:

```cpp
namespace Math { struct Vector3 { double x, y, z; }; }
```

Same data structure, two sets of names, independent operator implementations. The guidance logic in `default_guidance_model.cpp`
needs to do field-level copying between `Vec3` and `Math::Vector3` every time.

Correct approach: `missile_guidance_math.h` should directly use `Math::Vector3`,
and only keep `Vec3` as a namespace alias `using Vec3 = Math::Vector3`.

### 2.4 Duplicate Sensor Factory Functions

The same Sensor default values are initialized twice:

- `default_unit_factory.h:60-94` — `make_factory_default_sensor()`
- `unit_definition_loader.cpp:13` — `make_default_sensor_definition()`

Their initialization is completely identical: `reference_snr_db=13.0`, `pfa=1e-6`,
`confirm_hits_m=2`, `alpha_beta_alpha=0.65`, `alpha_beta_beta=0.12`, etc.
Extracting a `sensor_factory_defaults.h` or a `kDefaultSensor` constant can eliminate this.

### 2.5 RuntimeFacade Escape Hatch Narrowed to Adapter / Compat View

The project documentation explicitly defines `RuntimeFacade::runtime()` as a compatibility/diagnostic escape hatch, requiring
"the maintained Python frontend must concentrate access in an explicit adapter". The current mainline
has completed one round of recovery: raw runtime access is no longer scattered across business logic in `WorldBatchVecEnv` /
`leader_world_batch_runtime.py`, but concentrated in
`python/rl/runtime/world_batch/adapter.py` and `RuntimeCompatibilityView`
as migration-period compatibility surfaces.

- `src/interfaces/python/bindings_runtime.cpp:301`
  still exposes `RuntimeFacade.runtime()` directly to Python as a compatibility /
  diagnostics escape hatch.
- `python/rl/runtime/world_batch/adapter.py`
  caches `self.facade.runtime()`'s raw `WorldBatchRuntime` in `RuntimeFacadeAdapter`.
- `python/rl/runtime/world_batch_vec_env.py`
  still exposes `batch_runtime` / `runtime_facade` attributes, but `batch_runtime` currently is
  `RuntimeCompatibilityView`, used for compatibility with tests and migration code that still expect the old `vec_env.batch_runtime`
  access surface.
- `python/rl/runtime/leader_world_batch_runtime.py`
  currently accesses `WorldBatchVecEnv`'s controlled methods through `WorldBatchVecEnvAccess`,
  no longer directly pierces `batch_runtime.world()` to drive business logic.

Problems:

- **The closure is not frozen.** The compatibility adapter has isolated the old API, but the public attributes are still easily
  mistaken by new callers as maintained interfaces.
- **Boundary semantics are diluted.** Callers no longer distinguish between "long-term facade contract" and
  "migration-period raw runtime"; truly cutting off `WorldBatchRuntime` in the future will affect
  `leader_world_batch_runtime.py`, tests, and collaborative execution runtimes.
- **Tests still need to annotate compatibility semantics.** `tests/world_batch/test_world_batch_vec_env.py`
  still asserts that `vec_env.batch_runtime` / `vec_env.runtime_facade` is available, and reads
  controller state; these assertions should continue to be clearly identified as compatibility view, not
  recommended entry points for new business code.

These issues are not "mainline scattered penetration", but rather **the compatibility layer still has a risk of being misused as a mainline interface**.

Additional note:

- This round's main thread has already begun recovering this leak:
  some world/time-step accesses in `world_batch_vec_env.py` and `leader_world_batch_runtime.py`
  have been first moved back to explicit adapter, and `tests/architecture/runtime_facade/test_layering.py`
  has added guards.
- However, the risk has not disappeared. The current state is more accurately described as:
  **"The raw runtime escape hatch has been narrowed from scattered business calls to compatibility interface remnants, but the final freeze has not yet been completed."**

### 2.6 ScenarioLoader: Forming a Python-Side God Object

`gym_envs/scenario_loader/core.py` currently has 1163 lines, defining 122 instance methods.
Although the directory has split `loading/`, `reward_runtime/`, `behavior_runtime/`
and other subdomains, `ScenarioLoader` is still the sole owner and master router for all subdomains:

- Holds scenario data, entity roster, waypoint/mission state, reward cache,
  compiled metadata, scripted opponent state, leader/tasking bridge, and many more types of state.
- Re-hooks submodule logic back into the same class method space via a large number of `_foo_impl(self)` forms.
- Directly depends on `examples.agents.RedScriptedAgent`
  (`gym_envs/scenario_loader/core.py:6` and `:1099`), forming a
  `gym_envs -> examples` reverse layer dependency.

Problems:

- **Excessive responsibilities.** Scenario loading, behavior updates, reward calculation, navigation geometry, scripted opponents,
  runtime state synchronization all need to modify the same owner.
- **Cross-boundary dependency.** `examples/` should be a sample and experiment entry, but the mainline loader
  directly imports it, indicating "upper-level directory backfeeding lower-level runtime" has occurred.
- **Splitting packages does not truly split power.** Submodules have sunk files, but control and state ownership are still concentrated in
  `ScenarioLoader`; adding more features in the future will still flow back to `core.py`.

This is already a classic case of "files are split but object boundaries are not separated".

Additional note:

- This round's main thread has already first performed state shell extraction of `ScenarioLoader`, and centralized the mission/route/reward/runtime cache synchronization logic of execution episode state into `runtime_state.py`.
- Additionally, the first stage of owner extraction for `scripted-opponent` and `command-chain` has landed:
  `build/reset/step` lifecycle and `_leader_phase_manager`, `_naval_screen_*`
  runtime state caches have been sunk to `behavior_runtime/scripted_opponents.py` and
  `behavior_runtime/command_chain_owner.py`.
- Meanwhile, the `post_waypoint_transition / mission_phase_name / _approach_prev_*`
  set of behavior-phase states have also been sunk to `behavior_runtime/behavior_phase_owner.py`,
  and the execution episode state contract is kept unchanged via `runtime_state.py`'s unified mirror view.
- Therefore, the most prominent remaining issue has narrowed from "all states squeezed into one owner" to:
  **compat facade and deeper collaborator facets are still lingering in `core.py`; object boundaries have not been completely depowered.**

### 2.7 simulation_kernel_weapon_api.cpp: Forming a Weapon-Side Integration Hotspot

Currently, `simulation_kernel_weapon_api.cpp` is no longer just a thin API for "launch a missile",
but has started to concurrently bear:

1. mission/track selection
2. station-based launch definition parsing
3. definition tuning -> runtime tuning conversion
4. global tuning overlay
5. launch envelope evaluation
6. munition / ammo / cooldown / VLS consumption
7. missile runtime state assembly

The newly added `launch envelope` pre-launch rejection is correct in itself,
and the behavior regression is currently green; the problem is that it is layered onto an already continuously expanding integration point.

This means:

- In the short term, it is a high-yield incision because it can most quickly turn weapon realism parameters into realistic behavior.
- In the medium term, if seeker activation, midcourse datalink, damage layering,
  launch authorization, etc., are all continuously stuffed into here, `simulation_kernel_weapon_api.cpp`
  will evolve into a God API for the Weapon line.

Therefore, the suggestion here is not to revert this round's behavior changes, but to quickly split subsequent work into:

1. launch definition resolution
2. tuning resolution / overlay
3. launch authorization / envelope policy
4. runtime state assembly

Four relatively clear collaborators or helper layers.

---

## 3. Structural Issues (Controllable Now but Will Worsen Over Time)

### 3.1 Kernel API Continuous Expansion

`simulation_kernel.h` carries 32+ public API method names in 249 lines. This round added:

| New API | Essence | Problem |
|----------|------|------|
| `get_unit_velocity()` | Directly reads `Velocity` component | Generic ECS queries are not suitable for kernel public interface |
| `set_unit_ammo()` | Directly writes `Ammo` component | Same as above |
| `set_weapon_cooldown()` | Directly writes `WeaponCooldown` component | Same as above |
| `acoustic_model_` | Acoustic model reference | Kernel knows a new domain's model interface |

The pattern increasingly looks like "SimulationKernel = CRUD facade for all ECS components".
The kernel's public API grows linearly with the number of components in the system – each new component
requires new getters/setters for Python bindings.

The comment in `RuntimeFacade` mentions "escape hatch closure" – but if the Kernel itself
becomes an escape hatch, closure is futile. The correct direction is for the facade to provide type-safe
request/response pipelines, and the kernel should no longer do "generic CRUD".

### 3.2 Manual Phase Chain for System Registration

`simulation_kernel_systems.cpp` has about 50 lines of sequential function call chain at the end:

```cpp
register_ship_motion_system(ecs);        // Phase 5.2: simple surface-ship kinematics
register_submarine_motion_system(ecs);   // Phase 5.25: simple submarine kinematics
register_sensor_system(ecs);             // Phase 6: Sensor
register_sonar_system(ecs);              // Phase 6.1: Sonar / acoustic contacts
register_embarked_air_ops_system(ecs);   // Phase 6.57: Embarked helo ...
```

The kernel should not know about "submarines" or "carrier helicopters". These system registrations should
be done autonomously by domain modules through a registration interface, with the kernel providing only the registration entry.

The current design means every time a new system is added (even just concept-proof level),
a core kernel file must be modified. With parallel development across 5-10 domains,
`simulation_kernel_systems.cpp` will become a merge conflict hotspot.

### 3.3 default_guidance_model.cpp Lacks Function-Level Modularity

Grew from 291 lines to 587 lines (+102%). The `update()` method now mixes:

- seeker track filter (first-order low-pass)
- 3DoF thrust/drag integration
- PN acceleration command
- autopilot surrogate (first-order lag)
- mass consumption/burnout detection
- track memory / reacquisition

These are all independently testable guidance sub-functions. The correct extraction direction is:

```
update() →
  seeker_track(contacts, dt) → {bearing, range, closing_speed}
  propulsion_step(mass, dt)  → {thrust, mass_consumed}
  drag_force(speed, alpha)   → {drag_vector}
  pn_accel_cmd(los, closing) → {accel_cmd}
  autopilot_response(accel_cmd, dt) → {achieved_accel}
```

Currently all inlined in one giant lambda/branch block in `update()`.

### 3.4 Facade Contract Still Hasn't Truly Departed from Mission/Episode Internal Types

The documents for `runtime/contracts` and `runtime/facade` emphasize they are upper-layer contracts,
but current public types still directly depend on mission episode controller internal data:

- `src/runtime/contracts/world_batch_contracts.h:12`
  includes `core/mission/episode/execution_episode_batch_prepare.h`
- `src/runtime/facade/runtime_facade_types.h:11`
  includes `core/mission/episode/execution_episode_controller.h`
- `src/runtime/facade/runtime_facade.h:58-73`
  public methods directly send/receive `ExecutionEpisodeState`,
  `ExecutionEpisodeRuntimeProducts`, `ExecutionBatchStepResult`

This indicates the facade is more like a "thin wrapper around the lower-level runtime", rather than
a well-abstracted application-layer contract.

Risk:

- Once the mission/episode internal types are adjusted, the facade header, Python bindings,
  and contract tests will all have to change.
- The facade will be difficult to split into independent targets in the future, because the contract header still drags along
  `core/mission/episode` compile-time dependencies.

### 3.5 Env Entry Files Assume Bootstrap and Public Toolkit Responsibilities

`gym_envs/universal_env.py` and `gym_envs/leader_env.py` both self-scan
`build-workshop/build-gpu/build` during import and modify `sys.path`, aiming to preferentially load the in-repository
`ef_py` extension. This highly duplicates the existing path bootstrapping logic in `python/testing/runtime.py`.

Meanwhile, `universal_env.py` has become a public helper collection reverse-imported by multiple modules:

- `build_pilot_action`
- `build_universal_observation`
- `build_step_info`
- `normalize_action`
- `half_to_unit`

These helpers are co-depended upon by `python/rl/runtime/*`, `gym_envs/leader_env_parts/*`,
`examples/viz/*`, `tests/runtime/*`.

Problems:

- **Entry files are difficult to sink.** Once `UniversalEnv` wants to continue sliming down, it will affect many
  helper dependencies unrelated to the env class itself.
- **Import side effects are too strong.** The env module not only defines the env, but also undertakes repository build directory selection and
  Python import governance, causing coupling between runtime logic and developer machine directory layout.

---

## 4. Acceptable Trade-offs Currently

### 4.1 Ship/Submarine Motion Systems are Symmetric Design

`ship_motion_system.h` and `submarine_motion_system.h` are parallel implementations of the same pattern
(command-driven, response-limited kinematics) in the same directory. Symmetric design is reasonable –
`target_depth_m` + 3D for submarines vs `z=0` for ships is a natural domain difference,
and they should not be forced merged into one system.

### 4.2 Data Link TrackReport Deduplication Semantics Are Correct

The newly added track deduplication logic (position delta > 500m, velocity delta > 2m/s,
last data link update > 5s) semantically belongs to the correct responsibility of `DataLinkFusionSystem` –
"who should send, what to send, how often to send" should be inside the data link system, not leaked to TrackManager.
The current implementation is correct.

### 4.3 Hierarchical Damage Enumeration Is in the Right Place

`PlatformDamageState` is in `components/combat/damage.h`,
`Health.mission_kill/mobility_kill/sensor_kill` is in
`components/combat/health.h` – both belong to the combat component bundle,
correctly placed, no cross-domain contamination.

### 4.4 missile_guidance_types.h Is Well Isolated

`MissileGuidanceDefaults` is extracted as an independent `constexpr` constant collection,
separated from the implementation logic of `default_guidance_model.cpp`. This allows tuning parameters
to be determined at compile time without polluting the guidance logic.

---

## 5. Key Metrics

| Metric | Before Realization Push | At Review | Risk |
|--------|------------------------|-----------|------|
| Lines in `default_unit_factory.h` | ~563 | 845 | **High** |
| Cross-domain includes in `default_unit_factory.h` | ~18 | 27 | **High** |
| Runtime component dependencies in `unit_definition.h` | 0 | 5 | **Medium** |
| Lines in `default_guidance_model.cpp` | 291 | 587 | **Medium** |
| Public API in `simulation_kernel.h` | ~25 | ~32 | **Medium** |
| Lines in `simulation_kernel_weapon_api.cpp` | ~225 | ~689 | **Medium** |
| Duplicate definitions (Vec3 / sensor factory) | 0 | 2 | **Low** |
| Domains known by Kernel (ship/sub/sonar/helo) | 1 (ship) | 4 | **Medium** |
| Lines / methods in `gym_envs/scenario_loader/core.py` | - | 1163 / 122 | **High** |
| Lines in `python/rl/runtime/world_batch_vec_env.py` | - | 2018 | **High** |
| Public escape hatch paths from facade | 0 | `RuntimeFacade.runtime()` + `vec_env.batch_runtime` | **High** |
| `sys.path` bootstrap entries in env | 0 | 2 (`universal_env.py`, `leader_env.py`) | **Medium** |

---

## VI. Suggested Minimal Interventions

Ordered by urgency:

| # | Intervention | Target File(s) | Effort |
|---|--------------|----------------|--------|
| 1 | Extract `SharedDefaultSensor` | New `sensor_factory_defaults.h`, eliminate duplication between `default_unit_factory.h:60-94` and `unit_definition_loader.cpp:13` | Small (~30 lines moved) |
| 2 | Split `default_unit_factory.h` | Sensor creation logic → `models/systems/sensor_factory.h`; ship creation logic → `models/naval/ship_factory.h` (new) | Medium (~200 lines moved) |
| 3 | Eliminate `Vec3` duplication | `missile_guidance_math.h` uniformly uses `Math::Vector3`, provide namespace alias via `using Vec3 = Math::Vector3` | Small (pure replacement) |
| 4 | Split `default_guidance_model.cpp` | Extract 6 independent sub‑functions into namespace functions | Medium (~150 lines reorganized, no functional change) |
| 5 | Decouple system registration | New `SystemRegistry` or `RegistrationToken` interface; new systems self‑register instead of being hard‑coded in `simulation_kernel_systems.cpp` | Large (architectural change, suggest handling after P1) |
| 6 | Close `RuntimeFacade` escape hatches | No longer expose `batch_runtime` as a maintenance interface; supplement missing low‑level capabilities with facade/adaptor methods; gradually remove tests that directly assert on raw `runtime` | Medium (Python API convergence) |
| 7 | Split `ScenarioLoader`'s owner responsibilities | Separate scripted opponent, behavior update, mission state, compiled metadata into explicit service/state objects; remove direct dependency on `examples.agents` | Medium (structural refactoring, no need to change physics logic first) |
| 8 | Extract env bootstrap and shared helpers | Converge `ef_py` build directory selection into a unified bootstrap module; promote common helpers from `universal_env.py` to a standalone support module | Medium (import path adjustments) |

---

## VII. Review Conclusion

The code produced in this round of realization push **succeeded in physical correctness** — with 142 new lines (peak per file) enough to cover the missile guidance rewrite, thrust transient introduction, and construction of the sonar domain from scratch.

However, **three clear warning signals appear on structural maintainability**:

1. **God Factory is forming** — if not split, the next round of surface/ sonar/ submarine enhancements will push a single file over 1000 lines.
2. **Kernel API linear growth** — each new component requires a new getter/setter pattern that cannot continue. A facade request pipeline should be introduced before the next wave.
3. **Header pollution** — `unit_definition.h` has degraded from pure data definition to a runtime component dependency graph. Immediate backtracking is needed.
4. **Python orchestration layer enters a local high‑entropy zone** — `ScenarioLoader` becomes a manager of everything, `WorldBatchVecEnv` re‑exposes raw `runtime`, and `universal_env.py` turns into a common toolbox plus bootstrap entry point. If this is not closed now, the next issue will escalate from "local hot spot" to "de‑facto loss of control over mainline interfaces".

Interventions #1‑#4 are recommended to complete before P1 closure (total estimated effort < half a day); interventions #6‑#8 suggest at least freezing the design or completing the first round of closure; otherwise the coupling among facade / env / loader will continue to amplify; intervention #5 should be included in the next architecture cleanup (post‑P1).

This review is frozen until the next large‑scale code change.
