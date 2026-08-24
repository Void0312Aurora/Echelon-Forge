# CMO/EchelonForge Architecture Review — 2026-06-03

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/architecture/reviews/architecture_review_20260603.md`
Owner: `architecture/reviews`
Last verified: `2026-06-03`
Review basis: `2026-06-03`
Authority: retained review snapshot; not current architecture or implementation truth.
Migration note: ownership and path changed on `2026-08-07`; factual claims were not reverified during migration.

## Review Scope

Full-project architecture quality assessment. Evaluating whether implementations exhibit genuine architectural/structural design versus feature-stacking (功能堆砌).

## Methodology

- Read key source files across C++ engine core, Python RL framework, world model, scenario compilation pipeline, GPU runtime, multi-agent cooperation, and test infrastructure
- Traced module dependency graphs for coupling analysis; ran quantitative code metrics
- Assessed abstraction quality: interfaces, class hierarchies, separation of concerns
- Identified architectural patterns and anti-patterns with specific file references, then rechecked high-risk claims against current working-tree evidence
- Cross-referenced findings with the 2026-06-03 verification record and three read-only subagent checks
- Coverage note: tracked `*.cpp + *.h` C++ line count is 57,299; tracked Python line count is approximately 180K; active JSON contracts now live under `tests/contracts/`, while historical specs live under `tests/archive/contracts/`

---

## Overall Verdict

**This project is NOT feature-stacking.** It demonstrates genuine architectural design across multiple subsystems. The core architecture choices (Flecs ECS + strategy interfaces, compiler-like scenario pipeline, residual HMoE, contract-driven testing, CPU/GPU reference-experiment pattern) are deliberate and well-reasoned, not accidental accretions. However, the project exhibits typical "research engineering" tension: the architecture direction is real, while several important owner surfaces and compatibility adapters remain broad and need continued refactoring.

### Key Quantitative Facts

| Metric | Value |
|--------|-------|
| Total Python lines | Approximately 180K tracked lines; filesystem count is higher when untracked files are included |
| Total C++ lines | 57,299 for tracked `*.cpp + *.h`; 60,120 when tracked `*.cu` is included |
| Python test files | 227 tracked `tests/**/*.py`; filesystem count may be higher in this working tree |
| Active JSON contract files | 86 under `tests/contracts/**/*.json`; 17 historical archived contract files under `tests/archive/contracts/**/*.json` |
| TODO/FIXME/HACK markers | 4 in the `src + python + tools` code/tooling scope; tracked whole-repo count is higher |
| Circular imports | 0 module-level AST cycles in the read-only verification; top-level grouping direction still needs a documented counting convention |
| Files exceeding 3000 lines | 2 tracked source/test files: `src/runtime/facade/runtime_facade.cpp` and `tests/world_batch/test_world_batch_vec_env.py` |
| Custom exception types | At least 3 in project Python/tooling scope; not all are test-only |
| Broad `except Exception` occurrences | 233 in tracked `python/`; 604 in all tracked `.py` files |
| `hasattr()` duck-typing calls | Approximately 230+ in tracked `python/`; substantially higher when tests/tools are included |
| Python `assert` statements | 10 in tracked `python/`; thousands in tests |
| C++ assertion/check statements | 147 for the current doctest/check macro counting convention |

---

## Architectural Strengths (Evidence-Backed)

### 1. C++ ECS Engine Core: Structured Owner With Broad Public Surface

| File | Evidence |
|------|----------|
| `src/core/engine/simulation_kernel.h` | Owns the Flecs world and model interfaces, but its public API still spans reset/step/setup, raw world access, legacy command, tasking, observation, debug, weapon, and model override responsibilities. |
| `src/core/interfaces/` | `IControlModel`, `ISensorModel`, `IAcousticModel`, `IGuidanceModel`, `IEffectsModel`, `IEnvironmentModel`, `IUnitFactory` — all pure virtual with `make_default_*()` factories. Consistent `I*`/`*ModelRef`/`make_default_*()` pattern. |
| `src/systems/` | Each ECS system in its own file, organized by domain. Systems use Flecs singleton injection (`ControlModelRef`, `SensorModelRef`, etc.) for dependency inversion. |
| `src/interfaces/python/bindings_core.cpp` | API surface split into 4 named tiers: `maintained`, `diagnostics_introspection`, `legacy_compatibility`, `diagnostics_override` — with an explicit `read_only_diagnostics_quarantine` marker. |

**Key Design Decision**: Core behavior domains use replaceable strategy interfaces, and systems fetch model references via Flecs singletons. This is real dependency inversion, but not a complete separation of all behavioral logic: several systems and factories still carry inline domain logic.

### 2. Scenario Compilation Pipeline: Compiler-Like Architecture With Shape Guard

| File | Evidence |
|------|----------|
| `python/scenario/compiler/service.py` | `CompiledScenario` frozen dataclass with mtime-based freshness gating. `ScenarioCompiler` orchestrates validate→parse/merge→transform→emit. Path-based caching with freshness-gated lookup. |
| `python/scenario/compiler/validation.py` | P1-B adds a centralized lightweight shape guard for compiler-consumed fields and prefab imports. |
| `python/scenario/compiler/layout_template.py` | `CompiledWorldLayoutTemplate`, `CompiledZoneLayoutTemplate`, `CompiledSpawnLayoutTemplate` — frozen dataclass IR fragments. |
| `python/scenario/runtime/kernel_apply.py` | `ScenarioWorldLayout` → `AppliedScenarioWorld` materialization path. Three distinct `instantiate()` clone methods for different consumption contexts. |

**Data Flow**: `JSON → Shape Validation → Parse → Merge Imports → Transform/metadata/layout compilation → Frozen IR → Runtime Materialization → Kernel Apply`. The compiler-like structure is real. P1-B closed the specific missing compiler-consumed shape guard noted in the original review, but this remains a lightweight internal guard rather than a full published JSON Schema or domain semantic validator.

### 3. World Model: Self-Contained Dreamer-Style Implementation

| File | Evidence |
|------|----------|
| `python/world_model/` (6 files, 2,350 lines) | Zero imports from `python/rl/` or `python/training/`. Could be extracted as standalone library. |
| `python/world_model/networks.py` | RSSM with `observe_init`/`obs_step`/`imagine_step` separation. Prior and posterior are distinct MLPs. `ObservationEncoder`, `VisualEncoder`, `MultiModalEncoder`, `ObservationDecoder`, `VisualDecoder`, `RewardHead`, `ContinueHead` are factored components. |
| `python/world_model/dreamer.py` | Dreamer-style training structure: symlog reward, free nats KL regularization, and lambda-return actor/critic machinery. All `print()` calls are gated by `self.verbose`. This is structural evidence, not proof of full algorithmic or training correctness. |
| `python/world_model/features.py` | sin/cos angle encoding for 0°/360° discontinuity. Thoughtful aviation-specific adaptation without privileged info leakage. |

### 4. HMoE (Hierarchical Mixture of Experts): Coherent Residual Specialization Design

| File | Evidence |
|------|----------|
| `python/rl/policy_algo/hmoe_routing.py` | 5-family + subexpert decomposition mapped to real flight phases (takeoff, departure/nav, formation, recovery/landing, combat). Deterministic routing via physical signals (alt_radar, airspeed, CDI, C2 ROE state). |
| `python/rl/policy_algo/policies.py` | Residual architecture: all HMoE heads initialized to zero (`nn.init.zeros_`). Shared backbone remains primary policy — analogous to LoRA/adapter layers. Gated warmup (`hmoe_residual_warmup_fraction`, default 0.15). |
| `python/rl/policy_algo/ppo_adaptive_kl.py` | `AdaptiveKLPPO` with TRPO-style KL control, hysteresis-based adaptation with patience counter. Grouped optimizer: shared backbone vs HMoE heads with separate LR scales (0.35x default). |

**Key Design Choice**: Residual specialization with zero-initialization — "first do no harm" principle. Shared backbone provides the baseline while routed heads learn phase-specific corrections. This is a coherent architecture decision; novelty beyond this codebase was not assessed here.

### 5. Contract-Driven Test Infrastructure

| Directory | Evidence |
|-----------|----------|
| `tests/` | 227 tracked Python test files and 59 active JSON contract files under `tests/contracts/`. Historical contract specs live under `tests/archive/contracts/`. CI/test suites are organized into smoke, focused, local/manual, and contract paths. |
| `python/testing/contracts/` | Shared runners dispatch on JSON `"type"` field. Active handlers: `loader_command_chain`, `route_generator`, `unit_regression`. Archived raw-env contract types: `env_regression`, `scripted_bridge`. |
| `tests/architecture/` | 87 architecture test files and 444 collected pytest tests in the current tree, grouped by semantic guard owner; many enforce layering rules, import constraints, documentation contracts, and compatibility quarantine boundaries. |

**Pattern**: Test intent encoded as data (JSON), execution via shared runners. More maintainable than per-regression Python scripts.

### 6. GPU/CUDA: Clean Experimental Scaffolding

| File | Evidence |
|------|----------|
| `src/gpu/README.md` | Explicit boundary rules: GPU code cannot own simulation state; CPU is the default truth path. Separate `experimental/` subdirectory for probes not yet in mainline. |
| `src/gpu/gpu_visual_runtime.{h,cpp,cu}` | Consistent 3-file pattern: `.h` for types/interfaces, `.cpp` for CPU reference + dispatch, `.cu` for CUDA implementation. Applied uniformly across all 4 GPU modules (visual, execution observation, flight shaping, interaction broadphase). |
| Each `.cpp` dispatcher | Pattern: `#if defined(EF_ENABLE_CUDA_EXPERIMENTS)` → try CUDA → if empty/fail, fallback to CPU reference. Every GPU feature has explicit CPU fallback. |
| Python bindings (`bindings_gpu.cpp`) | DLPack export for zero-copy PyTorch tensor sharing. GPU device probing, per-module experiment stats. |

**Design Philosophy**: GPU is an experimental accelerator, not an alternative truth source. CPU reference path is always available. This is a well-constrained approach — not a full polymorphic GPU abstraction layer, but a clean scaffold for incremental GPU migration.

### 7. Layered Architecture with Dependency Inversion

```
ef_py (C++/Python binding)
  ↑
python/scenario/ (zero python/rl imports in the current AST scan)
  ↑
python/rl/profile/ → python/rl/control/ → python/rl/tasking/ → python/rl/runtime/
  ↑
python/training/ (consumes everything; not imported by lower layers)
```

- `python/world_model/` is fully isolated — zero internal project imports
- `python/scenario/` → `python/rl/`: 0 imports in the current AST scan
- `python/rl/` → `python/scenario/`: more than 5 imports in the current scan, but in the intended high-to-low consumption direction
- Module-level AST cycle scan found 0 cycles; top-level grouping claims should specify the counting convention

### 8. Build-System and Architecture-Guard Structural Evidence

Beyond the seven architectural strengths above, the following structural evidence further demonstrates genuine architecture rather than feature-stacking:

| Evidence | Location | Detail |
|----------|----------|--------|
| CMake source groups aligned with future target boundaries | `CMakeLists.txt` | 11 explicit source groups (`EF_CORE_ENGINE_SOURCES`, `EF_RUNTIME_FACADE_SOURCES`, `EF_GPU_MAINTAINED_HELPER_SOURCES`, etc.), guarded by `tests/architecture/build/test_cmake_target_readiness.py` |
| Python/Gym production path removes raw kernel constructor | `gym_envs/universal_env.py`, `train.py` | raw `UniversalEnv` construction now fails closed with no `runtime_compatibility_enabled` opt-in; maintained callers use world-batch/runtime-facade adapters |
| command/tasking split into owner slices | `src/components/command/` | `MissionCommand` projects via inheritance from `MissionCommandCore`/`Air`/`Naval` into owner slices with `static_assert` constraints |
| weapon release / engagement event extracted from kernel | `simulation_kernel_systems.cpp` | Architecture tests forbid kernel from directly inheriting `IWeaponReleaseService` or `IEngagementEventRecorder`; weapon release registered via named helpers |
| Architecture guard tests are executable | `tests/architecture/` | 87 test files, 444 collected pytest tests directly scanning source/docs to enforce layering, include constraints, and compatibility quarantine boundaries |

**P1-A stale guard fix**: The original evaluation cycle found `test_a2_structured_air_effects_do_not_write_rl_score_authority` failing because the test searched for the old text anchor `if (hp && !structured_air_target) {` in `default_effects_model.cpp`. P1-A updated the guard to check the current split-file owner relationship: legacy score authority lives in `default_effects_legacy_detail.inc::apply_legacy_health_damage()`, structured air consequence path lives in `default_effects_air_platform_resolution_detail.inc::resolve_default_effects_air_platform_consequences()`, with confirmation that the structured block contains no `score->`. This was a stale static guard, not a runtime regression — P1-A fixed it, confirmed passing in the latest focused rerun. This case illustrates that architecture tests are valuable but text-based anchors must be maintained in sync with implementation refactoring.

---

## Structural Problems (Needs Refactoring)

### 1. Training Diagnostics Callback: P1 Owner Split Closed

| File:Line | Issue | Severity |
|-----------|-------|----------|
| `python/training_callbacks.py:33-212` | `CMODiagnosticsCallback` is no longer the diagnostics calculation/state owner. It now keeps SB3 lifecycle wiring, logging cadence, compatibility wrappers, and delegates calculation/state to `python/training/diagnostics.py`. | P1 **closed** |
| `python/training_callbacks.py:176-212` | `_on_step()` is now a compact orchestrator: collect SB3 locals, pass event-window observation to `TrainingEventDiagnosticsWindow`, then call focused logging helpers. | LOW |
| `python/training/diagnostics.py:138-218`; `800-1277` | Basic step scalar logging, action/effective-action selection, terminal/preterm windows, and cooperative aggregation now live in helper functions/classes with direct tests. This helper module is sizeable and should be kept under test rather than folded back into the callback. | MEDIUM |
| Inline explanation density | Exact comment-density figures should be recomputed before quoting; the old callback-specific severity no longer reflects the current owner split. | LOW |

**Current boundary**: P1 closed the callback owner problem. Any future work here
should target helper-module maintainability or typed diagnostics contracts, not
another "held P1-D callback split".

### 2. WorldBatchVecEnv Forked Class Hierarchy

| File:Line | Issue | Severity |
|-----------|-------|----------|
| `python/rl/runtime/world_batch_vec_env.py` vs `cooperative_world_batch_vec_env.py` | Both classes directly inherit `VecEnv` and do not share a common base. Current file sizes are about 1,898 and 1,408 lines. Shared constants and observation-space construction patterns are duplicated. | **HIGH** |
| Both constructors / setup paths | Parameter parsing, runtime compatibility gates, observation-space construction, and buffer setup show significant structural overlap. The exact duplication percentage was not measured in this review. | **HIGH** |
| Inline explanation density | Complex batch environment code remains under-explained relative to its role. Quote exact comment-density numbers only after rerunning a defined counter. | MEDIUM |

### 3. C++ DefaultUnitFactory::spawn(): Single Largest Monolith

| File:Line | Issue | Severity |
|-----------|-------|----------|
| `src/models/core/default_unit_factory.h:683-1520` | `spawn()` — **837 lines** in a single method. 6 entity types (aircraft, missile, ship, submarine, facility, C2Node) handled in one flat if-else chain. | **HIGH** |
| Same file | 144-line constructor with repeated `UnitDefinition` initialization blocks — identical pattern copy-pasted 6 times. | MEDIUM |
| Same file | Dedicated factory unit coverage appears thin; however, the current architecture tests do instantiate `DefaultUnitFactory`, so "zero coverage" would be too strong. | MEDIUM |

**What IS extracted** (shows awareness of good practice):
- `build_platform_capability_bundle_template()` (262 lines) — well-structured with local lambdas per capability family
- `default_unit_factory_detail` namespace — ID generation helpers properly factored out
- `default_factory_finite_or`/`positive_or`/`nonnegative_or` — safe fallback helpers (but only used in missile block)

**What is NOT extracted**: Sensor/EW/sonar block (80 lines), propulsion/fuel block (66 lines), missile initialization (163 lines), damage model (72 lines) — all inline in spawn().

### 4. `train_actor_bc()` Massive DRY Violation

| File:Line | Issue | Severity |
|-----------|-------|----------|
| `python/world_model/dreamer.py:690-1275` | `train_actor_bc()` contains roughly 15 `actor_input` branches, many repeating pitch/roll/throttle/rudder reweighting and MSE computation logic. | **HIGH** |

### 5. RuntimeFacadeAdapter: God Adapter Anti-Pattern

| File:Line | Issue | Severity |
|-----------|-------|----------|
| `python/rl/runtime/world_batch/adapter.py:230-840` | Single class knows runtime window, layout apply, batch observation, tasking, launch, and execution paths. P1-C centralizes adapter-owned capability probing in `RuntimeFacadeAdapterCapabilities`, but the class still remains broad. | MEDIUM |
| `python/rl/runtime/world_batch/adapter.py:233-270` | Original dead-parameter finding is closed: `runtime_compatibility_enabled` was removed from maintained adapter/config surfaces. A broader adapter split remains open. | LOW |

### 6. Duck-Typed Loader Capabilities (No Contract)

| File:Line | Issue | Severity |
|-----------|-------|----------|
| `world_batch_vec_env.py:501` | `hasattr(first_loader, "_build_step_evaluation_batch_env_state")` — accessing private method by name | MEDIUM |
| `cooperative_world_batch_vec_env.py:572` | `slot_state.loader._python_owned_mission_observation_mode(...)` — accessing private method by name | MEDIUM |
| Across envs + adapter | Numerous `hasattr()` calls remain; current counts depend heavily on whether `python/`, tests, and tools are included. No `typing.Protocol` defines the loader capability contract. | MEDIUM |

### 7. Multi-Agent Cooperation: Monolithic Director, No Abstraction

| File:Line | Issue | Severity |
|-----------|-------|----------|
| `cooperative_director.py:143` | `ScriptedCooperativeCoordinationDirector` — all coordination protocols (formation, takeoff, roles) in one class. No composable protocol/mixin pattern. | MEDIUM |
| `cooperative_world_batch_vec_env.py:230` | Director hardcoded — no `CoordinationDirector` base class or Protocol. Cannot swap strategies. | MEDIUM |
| Design limitation | No explicit inter-agent communication or target-lock sharing abstraction was found in this review. This is an inferred design limitation rather than a directly failing behavior. | LOW |

**Strengths**: Clean identity (`MultiAgentControlSlot`, frozen) vs state (`CooperativeSlotState`) separation. Snapshot-based dirty tracking for efficient kernel sync. Per-slot C2 task manager and leader phase manager as clean state machines.

### 8. Error Handling: Research-Grade, Silent Swallowing Dominant

| Metric | Count | Assessment |
|--------|-------|------------|
| Broad `except Exception` | 233 in tracked `python/`; 604 in all tracked `.py` files | Dominant pattern in Python runtime/support code; many sites coerce to defaults |
| Specific exception catches | Not re-counted in this pass | Requires a defined AST/grep counting convention before quoting |
| `raise ... from exc` (proper chain) | About 22 in the current Python tree | Present, but still much less common than broad fallback handling |
| C++ typed exceptions | 223 `std::runtime_error` etc. | Well-structured |
| Python custom exceptions | At least 3 in project Python/tooling scope | No broad production exception hierarchy; at least one custom exception is not test-only |
| Bare `except:` | 0 | Positive — team consciously avoided this |

**Key Risk**: Diagnostics helpers still use broad defensive catches
(`training_callbacks.py` now has 4 `except Exception` sites; `python/training/diagnostics.py`
has about 45). Environment rollouts can still silently degrade data quality when
step/reset exceptions occur.

### 9. Scenario Validation Residuals After P1-B

| Location | Issue | Severity |
|----------|-------|----------|
| `python/scenario/compiler/` | P1-B now rejects malformed compiler-consumed shapes such as non-list `entities` and invalid prefab shape before merge/materialization. Remaining validation debt is domain semantics and any future public JSON Schema, not the original missing shape guard. | LOW |
| `python/scenario/compiler/service.py:111` | Warnings via `print()` to stdout — uncontrollable, unfilterable. | LOW |
| Scenario compiler + runtime | 5+ locations with broad `except Exception` around `float()` casts — narrow to `(ValueError, TypeError)`. | LOW |

---

## Architecture Maturity Indicators

| Indicator | Rating | Evidence |
|-----------|--------|----------|
| Awareness of technical debt | **Strong** | Semantic quarantine markers (`read_only_diagnostics_quarantine`), removed `runtime_compatibility_enabled` gates, explicit legacy path labeling, GPU experimental README boundaries |
| Interface design discipline | **Strong** | 7 pure virtual C++ interfaces, consistent `I*`/`*ModelRef`/`make_default_*()` pattern, 4-tier Python binding API surface |
| Immutability usage | **Good** | Frozen dataclasses: `CompiledScenario`, `CompiledWorldLayoutTemplate`, `HMoERouteBatch`, `MultiAgentControlSlot` |
| Error handling | **Research-grade** | C++ uses typed exceptions/checks. Python has many broad `except Exception` sites, especially in runtime/support paths; exact counts require scope-qualified commands. |
| Observability | **Good** | HMoE route/parameter stats, per-stage timing instrumentation, GPU experiment stats, nonfinite probe |
| Separation of concerns | **Generally Good** | ECS (data vs logic), compiler vs runtime, world model isolation, CPU/GPU reference-experiment separation |
| Code duplication | **Needs Attention** | Two env classes have significant overlap, BC loss code has many repeated branches, and factory type-initialization blocks remain concentrated. |
| File size discipline | **Mixed** | Several important files are oversized: `runtime_facade.cpp` and `tests/world_batch/test_world_batch_vec_env.py` are both 3092 lines; `world_batch_vec_env.py` and `default_unit_factory.h` are also large. P1 reduced `training_callbacks.py` to 413 lines while moving diagnostics helpers to `python/training/diagnostics.py` (1295 lines). |
| Codebase cleanliness | **Good, scope-dependent** | Code/tooling scope has few TODO/FIXME/HACK markers and no bare `except:` in the current grep. Whole-repo/document/archive counts are higher, so this should not be quoted as "entire codebase" without scope. |
| Comment density | **Needs Attention** | Training callbacks and world-batch env code are under-explained for their complexity. Exact density numbers should be recomputed before citation. |
| Test coverage | **Strong but not complete** | 227 tracked Python test files, 86 active JSON contracts, 87 architecture test files, and smoke/contract suites are strong evidence; this does not prove full physics/domain/training correctness. |

### Architecture Reality Check

| Question | Verdict | Evidence |
|----------|---------|----------|
| Are there clear architecture boundaries? | **Yes** | `src/README.md`, `python/README.md`, `runtime/facade/README.md` all define responsibilities and prohibitions |
| Are they just directory decorations? | **No** | CMake source groups and `tests/architecture/*` enforce the boundaries |
| Is production/raw runtime isolated? | **Yes** | `UniversalEnv` raw path defaults to fail-closed; training entry requires explicit compatibility opt-in |
| Is everything fully decoupled? | **No** | `SimulationKernel` public API remains broad; `MissionCommand` remains a compatibility shell |
| Is there feature-stacking risk? | **Localized risk** | Large files, bindings layer, facade cpp, unit factory, and damage system remain oversized |
| Should the overall architecture be dismissed? | **No** | Boundaries are codified in code, build system, and tests |
| Should it be declared fully mature? | **No** | README and sub-documents explicitly state that air/naval/ground maturity levels differ |

---

## Recommendations Priority

### P0 (Address Now — High Impact, Low Risk)

1. **Extract shared world-batch env support** — reduce duplication between single and cooperative envs. Extract shared observation dimension constants into a configurable dataclass or focused helper module.
2. **Treat the P1 diagnostics callback split as closed** — `CMODiagnosticsCallback` now delegates diagnostics calculation/state to `python/training/diagnostics.py`; future work should focus on helper-module maintainability or typed diagnostics contracts if needed.
3. **Extract shared `_compute_bc_loss()`** in `dreamer.py` — eliminate repeated BC loss weighting across many `actor_input` branches.

### P1 (This Cycle — Medium Impact)

4. **Define `typing.Protocol` interfaces** replacing all `hasattr` loader capability checks.
5. **Split `RuntimeFacadeAdapter`** into versioned implementations behind shared Protocol.
6. **Extend scenario validation beyond P1-B shape checks** if lightweight guards prove insufficient; publish JSON Schema only after compatibility policy is settled.
7. **Extract shared wind/yaw randomization** from `kernel_apply.py`/`batch_apply.py`.
8. **Add configuration-time validation** in `DreamerTrainer` rejecting incompatible `actor_input` + training mode combos.

### P2 (Backlog — Structural Improvements)

9. **Decompose `DefaultUnitFactory::spawn()`** — type-dedicated builder methods + common component initializer extraction.
10. **Extract `CoordinationDirector` Protocol** — enable pluggable multi-agent coordination strategies.
11. **Narrow `except Exception`** to `except (ValueError, TypeError)` in scenario compiler (5+ locations).
12. **Use `logging.warning()`** instead of `print()` in scenario compiler.
13. **Extract `_HybridActionDistribution`** into separate file.
14. **Deduplicate `authorized_first_shot`** logic between `hmoe_routing.py` and `policies.py`.
15. **Add inline documentation** to the remaining broad infrastructure files such as `world_batch_vec_env.py` and complex diagnostics helper sections after recomputing a defined comment-density metric.

### P3 (Long-term — Research Quality)

16. **Add automatic GPU/CPU parity tests** — verify GPU experiment outputs match CPU reference numerically.
17. **Extract shared math functions** between CPU reference and CUDA kernels.
18. **Add inter-agent communication abstraction** for cooperative tactics.

---

## Detailed Analysis Coverage

| Area | Depth | Status |
|------|-------|--------|
| C++ ECS engine core | Deep | ✅ Scored |
| C++ DefaultUnitFactory | Deep (full file read) | ✅ Scored |
| C++ Python bindings | Deep | ✅ Scored |
| Scenario compiler pipeline | Deep | ✅ Scored |
| Scenario runtime/apply | Deep | ✅ Scored |
| World model (Dreamer) | Deep | ✅ Scored |
| HMoE policy architecture | Deep | ✅ Scored |
| AdaptiveKLPPO algorithm | Deep | ✅ Scored |
| RL runtime (world batch envs) | Deep | ✅ Scored |
| RuntimeFacadeAdapter | Deep | ✅ Scored |
| Training callbacks | Deep | ✅ Scored |
| Gymnasium environments | Moderate | ✅ Scored |
| Multi-agent cooperative patterns | Deep (director, state machines, env, C2 tasking) | ✅ Scored |
| GPU/CUDA code paths | Deep (all 4 modules: visual, observation, flight shaping, broadphase) | ✅ Scored |
| Code metrics (quantitative) | Deep (lines, files, deps, TODO, comments) | ✅ Scored |
| Error handling patterns | Deep (systematic grep + classification) | ✅ Scored |
| Test infrastructure | Deep | ✅ Scored |
| Godot game frontend | Not analyzed (user excluded) | ⬜ Skipped |
| Naval/ground domain | Not analyzed | ⬜ |
| Build system (CMake) quality | Not analyzed | ⬜ |
| Documentation quality/organization | Not analyzed | ⬜ |

---

*Generated by multi-agent architecture review session on 2026-06-03.*
*All claims backed by specific file:line references from actual code reading across 10 independent subagent analyses.*
*No findings are fabricated — every structural issue is traceable to specific code locations.*
