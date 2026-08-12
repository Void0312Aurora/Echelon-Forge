# Code Layer Map

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/operations/reference/src_layer_map.md`
Owner: `operations/code-navigation`
Last verified: `2026-08-08`
This document answers three questions:

1. How the current mainline code path connects the C++ runtime to the Python training entry points.
2. Which README files and design documents define the responsibility boundaries of each subsystem.
3. Which directory you should inspect first when something breaks, instead of searching the whole repository blindly.

If a historical task record, old plan, or archived document conflicts with this
map, trust current code and the owner-local architecture entries first.

## 1. Current Mainline Overview

The current C++ surface is multi-domain but not evenly mature. Air/execution is
the deepest maintained path. Naval has platform components, command/tasking
owner slices, ship/submarine/embarked-air token runtime, weapon-release hooks,
and engagement evidence exports, but not a complete naval mission runtime.
Ground is bootstrap/evidence-only: `UnitType::Ground` and typed platform
capability evidence exist, while land movement, sensing, terrain ownership,
fires, damage, and full ground runtime remain held.

The maintained dependency direction should be understood as:

```text
interfaces/python
  -> runtime/facade
    -> core/engine + core/mission
      -> systems
        -> models / components / content

gpu
  -> core/runtime-visible packets
  -> does not own the canonical CPU truth path
```

If you think about it as an execution chain instead, it is closer to:

```text
SimulationKernel / WorldBatchRuntime
  -> mission runtime / episode controller
    -> RuntimeFacade / Python bindings
      -> gym_envs / scenario loader / python runtime support
        -> training / evaluation / diagnostics / contracts
```

There are three primary authoritative entry points for this mainline:

- [README.md](../../README.md)
  - The top-level project entry point, covering mainline capabilities, common commands, and repository-level boundaries.
- [src/README.md](../../../src/README.md)
  - The layering boundaries and dependency directions inside `src/`.
- [Architecture owner](../../architecture/README.md)
  - The current architecture standards, references, reviews, and open issues.

## 2. Which Documents Are the Current Authoritative Entry Points

If you need to decide whether a subsystem's responsibility boundary has been documented, check these layers first:

- README files under each `src/` directory
  - These are the most direct boundary descriptions and the closest to the code.
- `docs/architecture/standards/`
  - These are the primary maintained explanations for why the layers and
    runtime contracts look this way.
- `tests/README.md`
  - This is the entry point for understanding which constraints are already enforced automatically.
- `python/README.md`, `gym_envs/README.md`, `tools/README.md`
  - These describe the responsibility boundaries for the Python runtime layer, environment wrappers, and tool surface.

Documents that should not be treated as authoritative by default:

- `docs/Archive/`
  - Historical discussions and retired plans. Useful for history, but not a default basis for the current implementation.
- `docs/temp/`
  - Drafts and temporary analysis. Not part of the maintained mainline.
- Implementation packs, progress reports, and checkpoints inside task-specific records
  - Useful for reconstructing context, but they should not replace the boundary statements in the README files of the corresponding directories.

## 3. The `src/` Layer

`src/` is the mainline C++ runtime. It already has comparatively complete layering and boundary documentation, making it the strongest evidence for whether subsystem responsibilities have been documented in detail.

Read these first:

- [src/README.md](../../../src/README.md)
- [src/core/README.md](../../../src/core/README.md)
- [src/runtime/README.md](../../../src/runtime/README.md)
- [src/interfaces/README.md](../../../src/interfaces/README.md)
- [src/interfaces/python/README.md](../../../src/interfaces/python/README.md)

### `src/components/`

Responsibilities:

- ECS components.
- Command / tasking DTOs.
- Naval platform state components.
- Lightweight value types that are bindable and persistable.

Boundary entry points:

- [src/components/README.md](../../../src/components/README.md)
- [src/components/domains/air/platform/README.md](../../../src/components/domains/air/platform/README.md)
- [src/components/command/README.md](../../../src/components/command/README.md)
- [src/components/command/common/README.md](../../../src/components/command/common/README.md)
- [src/components/domains/air/command/README.md](../../../src/components/domains/air/command/README.md)
- [src/components/domains/naval/command/README.md](../../../src/components/domains/naval/command/README.md)
- [src/components/domains/naval/platform/README.md](../../../src/components/domains/naval/platform/README.md)
- [src/components/tasking/README.md](../../../src/components/tasking/README.md)
- [src/components/tasking/common/README.md](../../../src/components/tasking/common/README.md)
- [src/components/domains/air/tasking/README.md](../../../src/components/domains/air/tasking/README.md)
- [src/components/domains/naval/tasking/README.md](../../../src/components/domains/naval/tasking/README.md)

Typical questions:

- Where the fields for `MissionCommand`, `PilotAction`, `TaskOrder`, and `LeaderIntent` are defined.
- Which fields belong to `common` versus `air` / `naval`.
- Where ship, submarine, and embarked-air operation state is stored.

### `src/systems/`

Responsibilities:

- Flecs system registration.
- Per-tick ECS mutation logic.
- Physics, combat, platform systems, and visual updates.
- Bounded naval ship/submarine/embarked-air token runtime and naval weapon-release hooks.

Boundary entry points:

- [src/systems/README.md](../../../src/systems/README.md)
- [src/systems/core/README.md](../../../src/systems/core/README.md)
- [src/systems/domains/air/README.md](../../../src/systems/domains/air/README.md)
- [src/systems/physics/README.md](../../../src/systems/physics/README.md)
- [src/systems/combat/README.md](../../../src/systems/combat/README.md)
- [src/systems/systems/README.md](../../../src/systems/systems/README.md)
- [src/systems/domains/naval/README.md](../../../src/systems/domains/naval/README.md)
- [src/systems/visual/README.md](../../../src/systems/visual/README.md)

Typical questions:

- How commands enter the runtime and take effect each frame.
- How aerodynamics, control, instruments, navigation, sensors, and data links advance over time.
- Where naval motion and token-level embarked-air behavior are advanced.

### `src/models/`

Responsibilities:

- Default implementations of replaceable domain models.
- Control / sensor / guidance / effects / unit-factory models.
- Naval weapon-mount helpers and typed platform capability evidence.

Boundary entry points:

- [src/models/README.md](../../../src/models/README.md)
- [src/models/core/README.md](../../../src/models/core/README.md)
- [src/models/domains/air/README.md](../../../src/models/domains/air/README.md)
- [src/models/environment/README.md](../../../src/models/environment/README.md)
- [src/models/systems/README.md](../../../src/models/systems/README.md)
- [src/models/weapons/README.md](../../../src/models/weapons/README.md)

Typical questions:

- Where the default control-law, sensor, guidance, and weapon-effects models live.
- Whether a behavior belongs to "system logic" or to a replaceable model implementation.
- Whether ground-related data is only capability evidence or an actual runtime model.

### `src/content/`

Responsibilities:

- Content schemas, unit definitions, and content loaders.
- Describing which static content exists, including naval platform definitions
  and ground-aware setup metadata, rather than owning runtime behavior.

Boundary entry points:

- [src/content/README.md](../../../src/content/README.md)

### `src/core/`

Responsibilities:

- Single-world kernel.
- Batch runtime.
- Mission runtime.
- Episode controller.
- Geometry queries.
- Engine-level transport for maintained command/tasking contracts and typed platform setup.

Boundary entry points:

- [src/core/README.md](../../../src/core/README.md)
- [src/core/engine/README.md](../../../src/core/engine/README.md)
- [src/core/geometry/README.md](../../../src/core/geometry/README.md)
- [src/core/mission/README.md](../../../src/core/mission/README.md)
- [src/core/mission/runtime/README.md](../../../src/core/mission/runtime/README.md)
- [src/core/mission/episode/README.md](../../../src/core/mission/episode/README.md)
- [src/core/mission/episode/detail/README.md](../../../src/core/mission/episode/detail/README.md)
- [src/core/interfaces/README.md](../../../src/core/interfaces/README.md)

Typical questions:

- Where ownership of `SimulationKernel` and `WorldBatchRuntime` resides.
- Where reward / objective / termination / episode-transition logic is computed.
- Which naval seams are engine/runtime transport or evidence exports rather than mission orchestration.

### `src/runtime/`

Responsibilities:

- The maintained C++ application-layer contract.
- Facade requests / results.
- The typed runtime API exposed to Python and future frontends.
- Tasking, observation, engagement, diagnostics, and typed platform setup contracts.

Boundary entry points:

- [src/runtime/README.md](../../../src/runtime/README.md)
- [src/runtime/contracts/README.md](../../../src/runtime/contracts/README.md)
- [src/runtime/facade/README.md](../../../src/runtime/facade/README.md)

Typical questions:

- What the long-term external C++ runtime surface should be.
- Why `SimulationKernel` should not be used directly as the upper-layer API.
- Which facade packets are evidence/export surfaces rather than domain owners.

### `src/interfaces/`

Responsibilities:

- Language bindings and external interface adapters.
- Lightweight type conversion and error mapping.

Boundary entry points:

- [src/interfaces/README.md](../../../src/interfaces/README.md)
- [src/interfaces/python/README.md](../../../src/interfaces/python/README.md)

Typical questions:

- How a particular C++ type is exposed to Python.
- Whether a piece of logic belongs in bindings or should be pushed back down into `runtime/facade` / `core`.

### `src/gpu/`

Responsibilities:

- GPU helpers.
- Packet runtime support.
- Explicit experimental probes.

Boundary entry points:

- [src/gpu/README.md](../../../src/gpu/README.md)
- [src/gpu/experimental/README.md](../../../src/gpu/experimental/README.md)

Typical questions:

- Which GPU paths have already entered the maintained surface.
- Which ones are still parity probes or experimental paths.

### `src/tools/`

Responsibilities:

- Development-time tools and experimental tooling.
- Allowed to call runtime APIs for probing, but not part of the maintained mainline contract.

Boundary entry points:

- [src/tools/README.md](../../../src/tools/README.md)
- [src/tools/experimental/README.md](../../../src/tools/experimental/README.md)
- [src/tools/experimental/gpu_phase0/README.md](../../../src/tools/experimental/gpu_phase0/README.md)

## 4. The `python/` Layer

`python/` is not a miscellaneous-scripts directory. It is the Python support layer that sits above the C++ runtime.

Read these first:

- [python/README.md](../../../python/README.md)
- [python/training/README.md](../../../python/training/README.md)

Current mainline subdomains:

- `scenario/`
  - Main implementation for scenario compilation and runtime.
- `rl/`
  - Mainline Python RL stack, including runtime, tasking, policy algorithms, planning, profile, and support.
- `training/`
  - Shared bootstrap, CLI, and runtime support reused by the `train.py` mainline entry point.
- `testing/`
  - Contract runners and runtime support for tests.
- `world_model/`
  - Support for world models and offline datasets.
- `models/`
  - Training-model helpers on the Python side.

Typical questions:

- Why a given training entry point reaches the world-batch runtime.
- Where the Python glue for leader / tasking / HMoE lives.
- Why the contract-runner layout, artifact paths, and training bootstrap are organized this way.

Implementation entry points:

- [python/scenario_compiler.py](../../../python/scenario_compiler.py)
  - Compatibility shim; the main implementation has moved to `python/scenario/compiler/`.
- [python/scenario/runtime/](../../../python/scenario/runtime)
  - Main scenario-runtime implementation. The older `python/scenario_runtime.py`
    shim is not present in the current checkout.
- [python/testing/contracts/](../../../python/testing/contracts/)
  - Compatibility shim; the main implementation has moved to `python/testing/contracts/`.

## 5. The `gym_envs/` Layer

`gym_envs/` is the environment-wrapper layer. It connects the C++ runtime, mission state, and training interfaces.

Read this first:

- [gym_envs/README.md](../../../gym_envs/README.md)

Primary entry points:

- [gym_envs/universal_env.py](../../../gym_envs/universal_env.py)
  - The execution-layer / single-process primary environment.
- [gym_envs/leader_env.py](../../../gym_envs/leader_env.py)
  - The leader-layer environment.

Key subdomains:

- `scenario_loader/`
  - Scenario-runtime glue, mission observation, and execution / navigation / reward / preparation / spatial runtime pieces.
- `leader_env_parts/`
  - Decision and execution glue extracted from the leader environment.

Typical questions:

- Why a given environment step lands in a particular reward or transition branch.
- How responsibilities are separated between the leader environment and the execution environment.

## 6. The `tests/` Layer

`tests/` is already converging toward "reusable runners + JSON contracts".

Read this first:

- [tests/README.md](../../../tests/README.md)

Current mainline test domains:

- `architecture/`
  - Layering guards and target readiness.
- `runtime/`
  - Regressions for mission / runtime / loader / facade behavior.
- `world_batch/`
  - Batch-kernel and vec-env adaptation.
- `leader/`
  - Leader / tasking / common-core / naval semantics.
- `scenario/`
  - Scenario compiler and spatial-query tests.
- `training/`
  - Regressions for training entry points and callbacks.
- `contracts/`
  - JSON contract specifications.
- `diagnostics/`
  - Still more exploratory, and should not replace stable regression coverage.

Maintained smoke entry point:

- `tests/smoke/ci_smoke_suite.json`
  - The repository-level smoke manifest used by CI and top-level docs.
- `tools/runners/run_pytest_suite.py`
  - The maintained runner that validates suite paths before invoking pytest.

This is also the main evidence surface for whether a boundary is merely documented or is actually being enforced. For example, architectural layering, runtime-facade consolidation, and parts of the contract boundary are already kept in place by automated tests.

## 7. The `tools/` Layer

`tools/` is the operator-facing tooling and runner surface, not the core runtime API.

Read these first:

- [tools/README.md](../../../tools/README.md)
- [tools/diagnostics/README.md](../../../tools/diagnostics/README.md)
- [tools/maintenance/README.md](../../../tools/maintenance/README.md)

Current mainline split:

- `tools/eval/`
  - The maintained evaluation entry points.
- `tools/diagnostics/`
  - Benchmark / probe / replay / operator-facing diagnostics.
- `tools/runners/`
  - Contract runners and batch runners.
- `tools/maintenance/`
  - Environment, workspace, and maintenance scripts.

## 8. Boundary Design Documents

If you want to understand why the layers look this way, not just read directory README files, start with:

1. [docs/architecture/work/issues/system_layering_and_engine_encapsulation_plan.zh.md](../../architecture/work/issues/system_layering_and_engine_encapsulation_plan.zh.md)
2. [docs/architecture/work/issues/architecture_and_performance_research_followup.zh.md](../../architecture/work/issues/architecture_and_performance_research_followup.zh.md)
3. [docs/architecture/work/issues/system_layering_and_engine_encapsulation_plan.md](../../architecture/work/issues/system_layering_and_engine_encapsulation_plan.md)
4. docs/plan/archive/architecture/src_layered_refactor_freeze.zh.md (`git show 3dc34673:docs/plan/archive/architecture/src_layered_refactor_freeze.zh.md`)

These documents answer:

- Why `runtime/facade` needs to exist.
- Why `interfaces/python` should no longer own domain logic.
- Why `core`, `systems`, `models`, and `components` should keep the current dependency direction.
- Which layering decisions are already frozen into the current mainline and which are still follow-up consolidation work.

## 9. Issue-Triage Suggestions

If the problem you are facing is:

- "Where is this field defined?"
  - Start from `src/components/`.
- "Why does this per-tick behavior change this way?"
  - Start from `src/systems/` and `src/models/`.
- "Why are mission / reward / termination computed this way?"
  - Start from `src/core/mission/`.
- "Why did Python receive this observation, reward, or phase transition?"
  - Start from `gym_envs/scenario_loader/`.
- "Why did leader / tasking emit this command?"
  - Start from `python/rl/tasking/` and `gym_envs/leader_env_parts/`.
- "Why is the binding surface inconsistent?"
  - Start from `src/interfaces/python/` and `tests/runtime/`.
- "Why is the facade contract designed this way?"
  - Start from `src/runtime/` and the [runtime facade issue](../../architecture/work/issues/runtime_facade_contract_plan.md).
- "Why is batch rollout / world-batch slow?"
  - Start from `src/core/engine/`, `python/rl/runtime/`, and `tools/diagnostics/`.

## 10. Recommended Reading Order

When entering the repository for the first time, read in this order:

1. [README.md](../../README.md)
2. [docs/README.md](../README.md)
3. [src/README.md](../../../src/README.md)
4. [src/core/README.md](../../../src/core/README.md)
5. [src/runtime/README.md](../../../src/runtime/README.md)
6. [src/interfaces/python/README.md](../../../src/interfaces/python/README.md)
7. [python/README.md](../../../python/README.md)
8. [gym_envs/README.md](../../../gym_envs/README.md)
9. [tests/README.md](../../../tests/README.md)
10. [tools/README.md](../../../tools/README.md)

If you are mainly working on architecture or boundary questions, continue with:

1. [Architecture owner](../../architecture/README.md)
2. [docs/architecture/work/issues/system_layering_and_engine_encapsulation_plan.zh.md](../../architecture/work/issues/system_layering_and_engine_encapsulation_plan.zh.md)
3. [src/runtime/facade/README.md](../../../src/runtime/facade/README.md)
4. [src/core/mission/README.md](../../../src/core/mission/README.md)
5. [tests/architecture/runtime_facade](../../../tests/architecture/runtime_facade)

## 11. Maintenance Notes

This map covers only the currently maintained mainline. It does not promise that:

- every historical task document has already been synchronized to the current paths
- archived plan/task packets are current operational entry points
- older designs in `Archive/` still match today's directory layout exactly

If an active README is later moved, renamed, or given a different responsibility, update that directory's README first and then return to this map to repair the navigation.
