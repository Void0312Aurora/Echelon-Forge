# Echelon Forge

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Echelon Forge is a semantic-causal simulation platform with an optional
learning layer for multi-domain mission research. It develops an architecture
for integrating scenario and content definitions, mission and tasking
semantics, domain models, agent interfaces, fidelity requirements, and
experiment protocols into reproducible simulation workflows. The maintained
repository admits a scoped native CPU composition and bounded domain/runtime
paths; full-fidelity composition and unrestricted external provider or plugin
admission remain separately governed.

## What the project contains

- A native C++ ECS simulation runtime built around `flecs`, with fixed-step CPU
  execution and deterministic reset seeds.
- A typed C++ runtime facade and `nanobind` Python bindings exposed as `ef_py`.
- Scenario compilation and realization, including content, unit, profile, and
  mission setup.
- Optional Gymnasium-style environment adapters, vectorized world-batch
  execution, and cooperative command/tasking surfaces for policy experiments.
- Domain model families for control, sensing, guidance, weapons, effects, and
  platform capabilities, connected through shared lifecycle contracts on
  admitted paths.
- Evaluation, diagnostics, replay/evidence exports, contract specifications,
  and architecture regression gates.

The maintained mainline currently has its deepest end-to-end coverage in
air/execution and cooperative execution. Naval and ground work is admitted in
bounded tasking, platform, movement, terrain, contact, fire, and evidence
surfaces; those domains do not yet represent complete production mission
runtimes.

## Core architecture at a glance

The architecture is organized around five questions rather than separate
vertical stacks:

| Face | Question | What it owns |
| --- | --- | --- |
| Semantic | What exists in the world? | Domain ontology, scenario/content compilation, capabilities, roles, tasks, and typed contracts. |
| Causal | What causes what? | State transitions, event ordering, stage dependencies, barriers, and replayable causal evidence. |
| Agentic | Who knows, decides, and acts? | Information state, authority scopes, command/tasking, policy interfaces, and coordination. |
| Learning | How does the system improve? | Evaluation, curriculum, capability profiles, scenario generation, policy, and world-model consumers. |
| Experiment | What exactly is being compared? | Scenario reference, configuration composition, seeds, evaluation protocol, and comparability rules. |

This five-face model is the maintained architecture direction; implementation
maturity is uneven. The admission table below identifies which domain paths are
currently exercised and which remain bounded or experimental.

Evidence is cross-cutting: traces, packet ancestry, snapshot versions, event
order, and validation verdicts explain why a run should be trusted. As an
architecture rule, domain features join these shared faces through explicit
model families, capability contracts, and stage contracts instead of creating
private `air`, `naval`, or `weapon` runtime stacks; each domain path still
requires its own stage, contract, and evidence admission.

The implementation follows this execution shape:

```text
scenario + content + profile + experiment settings
  -> content compilation and world setup
  -> tasking and command delivery
  -> control and physics state update
  -> sensing, tracks, links, fire/effects, and damage
  -> observation/result export
  -> policy, evaluation, diagnostics, and evidence consumers
```

P0-P10 defines the causal-temporal architecture model. The maintained CPU
runtime is currently fixed-step; explicit stage-node manifests and
dependency/clock-domain admission are being expanded incrementally. The model
allows different cadences and empty stages, but current bounded slices use
only the admitted contracts and do not claim that a full multi-rate scheduler
is operational. Where feedback is implemented, it crosses explicit state
versions, event timestamps, or barriers.

The complete P0-P10 stage vocabulary, graph-of-graphs model, and stage-contract
rules are maintained in the [Simulation System Architecture Design](docs/architecture/standards/simulation_system_architecture_design.md).

## Simulation and learning are separate layers

The simulation layer is independently usable. It owns authoritative world
state, state evolution, the currently admitted fixed-step execution order and
scheduling contracts, event ordering, facade-visible snapshots,
simulation-semantic termination, and compiled mission products. It does not
own a training loop, curriculum, policy state, or a frontend-specific
observation encoder.

The learning and policy layer is a consumer of that simulation. A learned
policy, scripted doctrine, human operator, or other decision model selects an
observation view and produces action or coordination intents through facade
contracts. An RL environment is an **Env-as-View** adapter: it consumes
`ObservationPacket` data, injects actions through the facade, and mirrors
episode state; it is not the owner of simulation truth or episode phase.

The repository therefore maintains two routes that meet at the same native
truth boundary:

```text
Direct simulation route (no RL dependency)
scenario compiler -> facade_batch -> RuntimeFacade -> native simulation
                                     -> snapshots / step results / replay

RL or policy route (optional consumer)
scenario loader + policy adapter -> explicit world_batch / WorldBatchVecEnv
                                  -> the same RuntimeFacade and native simulation
                                  -> observation/action bridge -> rollout data
```

`facade_batch` is the default no-RL scenario route. `world_batch` is selected
explicitly for maintained RL training and evaluation. The default maintained
composition is the repository-owned `builtin.default_compatibility` profile on
the `cpu_exact.reference` backend. Provider and plugin interfaces are governed
admission points; an external provider or plugin is not admitted merely
because the interface can load it. The two adapters share the native truth
boundary, but route-specific reward, termination, and autoreset behavior must
not be assumed identical without a corresponding parity gate. The lightweight
simulation path does not require Gymnasium, Stable-Baselines3, or PyTorch.

For a runnable no-RL example, see
[`python/simulation/air/demo.py`](python/simulation/air/demo.py); deterministic
replay coverage is in
[`tests/runtime/simulation/test_air_facade_demo.py`](tests/runtime/simulation/test_air_facade_demo.py).

## Why this architecture

- **Shared semantics:** the architecture gives new domain behavior a common
  lifecycle, so admitted cross-domain comparisons use the same task, state,
  observation, and evidence vocabulary.
- **Simulation independence:** scenarios, scripted runs, diagnostics, and
  facade clients can exercise the native runtime without importing an RL stack;
  learning remains a replaceable consumer.
- **Stable boundaries:** frontends depend on `src/runtime/facade` and typed
  packets instead of raw Flecs entities, kernel ordering, or backend details.
- **Authoritative truth:** the native CPU runtime owns world state and episode
  truth; Python mirrors and GPU helpers remain adapters or bounded capabilities.
- **Comparable experiments:** fixed-step execution, explicit seeds, profiles,
  scenario/config inputs, and evaluation protocols make runs easier to repeat
  and compare.
- **Explainable results:** observation provenance, diagnostics, contract tests,
  and regression gates make it possible to tell what a result used and which
  boundary has actually been validated.
- **Controlled extension:** a domain addition declares its lifecycle stages,
  packets, capability seams, and evidence before it becomes a maintained path.

## Scope and status

This repository is an active research/engineering codebase, not a polished
product release.

That means:

- active plans and forward notes live under `docs/`
- some training lines are frozen baselines, others are active experiments
- the CPU runtime remains the canonical world-step truth
- GPU helper paths exist, but are still treated conservatively
- community contribution is currently issue-first and owner-scoped; see
  [CONTRIBUTING.md](CONTRIBUTING.md)

## Project content and maturity

The repository is multi-domain, but the domains are not equally mature. Treat
the table below as an entry-map, not as a release promise.

| Area | Current status | Primary entrypoints |
| --- | --- | --- |
| Air / execution | Most mature runtime and training line; current best baseline for correctness hardening. | `scenarios/takeoff/`, `scenarios/cruise/`, `scenarios/landing/`, `examples/config/training/frozen/` |
| Cooperative / combined | Active integration line for multi-agent, leader/execution, and world-batch behavior. | `scenarios/combined/`, `python/rl/runtime/cooperative_world_batch_vec_env.py`, `gym_envs/leader_env.py` |
| Naval | Active domain with maintained N4-style pre-fire tasking, contact/reporting, screen/station, and evaluation gates. Weapon/damage outcome authority is still future work. | `scenarios/naval/`, `docs/domains/naval/` |
| Ground | Static tasking and bounded native single-infantry movement, Arnis terrain sampling, tracked-target rifle-fire and shared damage probes; general route planning, sensing, suppression and production Ground WorldBatch remain unadmitted. | `scenarios/ground/`, `docs/domains/ground/`, `docs/systems/environment/` |
| Air combat / A2 | Focused combat and high-fidelity damage-model workline with retained evidence gates. It is one domain line, not the whole project identity. | `scenarios/air_combat/`, `docs/domains/air/`, `docs/learning/work/active/`, `docs/systems/effects/reviews/` |
| Visualization / game | Exploratory operator and frontend surfaces backed by simulation runtime truth where maintained. | `examples/viz/`, `docs/operations/visualization/` |
| Model / world model | Planning and experimental policy/model work, including temporal HMoE and world-model utilities. | `docs/learning/`, `world_model_train.py` |

## Naming And Package Identity

The repository currently carries three related names. Use them deliberately:

- `Echelon Forge` is the human-facing project and repository name.
- `EchelonForge` is the CMake `project(...)` identifier and should remain
  stable unless a dedicated build-system migration is planned.
- `cmo` is the legacy Python distribution/install identifier in
  `pyproject.toml`, kept for compatibility with editable installs, local helper
  scripts, cached build artifacts, and downstream automation.

Do not treat `cmo` as a separate product name, and do not rename package ids,
CMake ids, helper names, or script paths opportunistically. A full naming
migration should be handled as its own scoped change with compatibility notes
and artifact/cache cleanup guidance.

## Build and development

Local validation is expected to run inside the repository virtual environment:

```bash
source .venv/bin/activate
```

The maintained workspace convention is:

- repository virtual environment: `.venv`
- Python metadata and dependency groups: `pyproject.toml`
- Linux/macOS env helper: `tools/maintenance/cmo_env.sh`
- Windows/PowerShell env helper: `tools/maintenance/cmo_env.ps1`
- Linux/macOS build selection: prefer `CMO_BUILD_DIR`, otherwise auto-detect `build-workshop`, `build-gpu`, `build`, `build-facade-local`
- Windows build selection: prefer `CMO_BUILD_DIR`, otherwise auto-detect `build-local-win`, `build-workshop`, `build-gpu`, `build`, `build-facade-local`

Linux/macOS example:

```bash
python -m pip install pytest numpy
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_env_summary
cmo_python -m pytest -q tests/runtime/core/test_env_config.py
```

Windows/PowerShell example:

```powershell
.\.venv\Scripts\python.exe -m pip install pytest numpy
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 summary
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\core\test_env_config.py
```

The current minimum smoke set used for repository validation is:

```bash
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py ef_test -j4
ctest --test-dir build-workshop -R ef_test_all --output-on-failure
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
cmo_python tools/runners/run_scenario_contract.py --suite tests/smoke/ci_contract_suite.json
```

On Windows, use the PowerShell helper and a Windows build directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pytest numpy
cmake -S . -B build-local-win -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-local-win --target ef_core ef_py ef_test -j2
ctest --test-dir build-local-win -R ef_test_all --output-on-failure
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_pytest_suite.py --suite tests\smoke\ci_smoke_suite.json
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_scenario_contract.py --suite tests\smoke\ci_contract_suite.json
```

The Windows path above is scoped to the current local development workflow:
smoke tests and focused regressions. It does not claim that Windows cannot run
RL training; training workflows should be enabled deliberately when the local
dependencies, runtime artifacts, and run-output policy are ready.

Optional dependency groups are declared in `pyproject.toml`:

- `.[test]` declares the lightweight smoke/regression dependency set.
- `.[rl]` adds Gymnasium, Stable-Baselines3, and PyTorch for environment/runtime imports.
- `.[train]` adds the training stack plus TensorBoard.
- `.[world-model]` covers the world-model utilities.
- `.[geometry]` adds SciPy and Shapely for the airframe geometry review tool's whole-airframe alpha-shape contour diagnostic.
- `.[dev]` is a convenience superset for local development, not a locked release environment.

Note: the maintained smoke workflow currently installs the small dependency set
directly and then uses `cmo_env.sh` / `cmo_env.ps1` to point Python at the
locally built extension. Because this is a scikit-build project,
`pip install -e ".[test]"` may attempt an editable package build; use it only
when you intentionally want to exercise package installation rather than the
fast local build loop.

No lockfile is checked in yet. Treat the optional dependency groups as minimum
capability declarations for smoke/runtime/training/world-model workflows, not as
reproducible experiment locks. Training result reproduction should record the
resolved package set with the run artifact until a dedicated lockfile policy is
introduced.

Configure and build the local extension:

```bash
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j2
```

When running Python-side tests or training on Linux/macOS, prefer the unified
repository helper:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_env_validate_rl  # Only needed before RL-capable runtime tests.
cmo_python -m pytest -q \
  tests/architecture/governance/test_cpp_include_direction.py \
  tests/architecture/build_system/test_cmake_target_readiness.py \
  tests/runtime/facade/test_runtime_facade_core.py \
  tests/world_batch/test_world_batch_runtime_surface.py \
  tests/gpu/test_gpu_runtime_bindings.py
```

If you use a different build directory, export `CMO_BUILD_DIR=/path/to/build`
before sourcing `tools/maintenance/cmo_env.sh`, or set `$env:CMO_BUILD_DIR` before
calling `tools\maintenance\cmo_env.ps1` on Windows.

## Where to explore

- [src/](src/README.md): C++ kernel, mission runtime, runtime facade, Python bindings, GPU helpers.
- [python/](python/README.md): RL runtime, training helpers, scenario compiler/runtime, diagnostics support.
- [gym_envs/](gym_envs/README.md): shared environment helpers, cooperative/leader support, scenario loader.
- [scenarios/](scenarios/README.md): maintained scenario definitions grouped by task domain.
- [examples/](examples/README.md): config inputs, lightweight fixtures, visualization assets, and example-only surfaces.
- [tests/](tests/README.md): pytest suites, contract specs, runners, and fixtures.
- [tools/](tools/README.md): evaluation, diagnostics, runners, maintenance scripts.
- [scripts/](scripts/README.md): retained operator-facing wrappers and compatibility workflow shells.
- [docs/README.md](docs/README.md): manuals, plans, standards, forward notes, and artifact indexes.

Execution training uses `build_execution_world_batch_vec_env` and the canonical
`python.rl.runtime.world_batch.vec_env.WorldBatchVecEnv`; cooperative execution
uses `build_cooperative_world_batch_vec_env` and
`python.rl.runtime.cooperative_world_batch_vec_env.CooperativeWorldBatchVecEnv`.
`UniversalEnv` remains an importable compatibility name whose constructor fails
fast; it is unavailable as a training or evaluation backend.

## Implementation boundaries

For code-level navigation, the maintained path from an input scenario to a step
result is:

```text
scenario JSON + profile
  -> python/scenario/compiler and python/scenario/runtime
  -> python/simulation backend selection
       +-> facade_batch (default non-RL and scripted path)
       |   -> ef_py / src/runtime/facade
       |   -> src/core/mission and src/core/engine
       |   -> src/systems mutate the ECS world
       |   -> snapshots / step results / replay
       +-> explicit world_batch (training and evaluation path)
           -> ef_py / src/runtime/facade
           -> src/core/mission and src/core/engine
           -> src/systems mutate the ECS world
           -> observations and result packets
           -> gym_envs and python/rl
           -> train.py / evaluate.py / tools / tests
```

Both branches meet at the native truth boundary. Only the explicit
`world_batch` branch continues into Gym/RL and training consumers.

The native ownership boundaries are:

```text
src/runtime/facade
  -> src/core/mission
    -> src/core/engine
      -> src/systems
        -> src/models + src/components + src/content
```

- `src/core/engine` owns the canonical CPU `SimulationKernel`,
  `WorldBatchRuntime`, world stepping, and engine-level transport.
- `src/core/mission` owns mission objectives, reward and termination decisions,
  and episode orchestration around the engine.
- `src/systems` registers Flecs systems and applies per-tick state mutation.
- `src/models` contains replaceable control, sensor, guidance, and effects
  implementations; `src/components` stores ECS state and typed command/tasking
  data; `src/content` owns static schemas, unit definitions, and loaders.
- `src/runtime/facade` is the maintained typed C++ application contract above
  the core. `src/interfaces/python` exposes that contract through `ef_py` and
  should contain conversion and error mapping only.
- `python/scenario/` compiles and realizes scenarios. `python/simulation/`
  selects the backend, while `gym_envs/` adapts runtime results to
  Gymnasium-style interfaces and `python/rl/` owns training-side consumers.
- `tools/` and `tests/` provide evaluation, diagnostics, contract checks, and
  regression gates; they do not become alternate runtime authorities.

The CPU runtime remains the canonical world-step truth. GPU helpers may provide
packet support or experiments, but they do not replace the CPU path. The
`UniversalEnv` name remains an importable compatibility surface whose
constructor fails fast; maintained training and evaluation use the explicit
world-batch/facade adapters above.

See also:

- [src/README.md](src/README.md)
- [src/core/README.md](src/core/README.md)
- [python/README.md](python/README.md)
- [gym_envs/README.md](gym_envs/README.md)
- [Architecture owner](docs/architecture/README.md)
- [Code layer map](docs/operations/reference/src_layer_map.md)

## Scenarios and experiment inputs

Maintained scenarios live in [scenarios/](scenarios/README.md), grouped into:

- `takeoff/`
- `stable_flight/`
- `cruise/`
- `air_combat/`
- `naval/`
- `ground/`
- `landing/`
- `combined/`
- `templates/`
- `test/`

Training-config entrypoints:

- [examples/config/training/README.md](examples/config/training/README.md)
- [examples/config/training/active/README.md](examples/config/training/active/README.md)
- [examples/config/training/frozen/README.md](examples/config/training/frozen/README.md)

Other maintained config/content inputs live under:

- `examples/config/database/`
- `examples/config/diagnostics/`
- `examples/config/prefabs/`

Frozen configs are baseline/provenance references.
Active configs are where current training work continues.

Repository retention policy at a glance:

- `scenarios/` is versioned and treated as maintained repo input.
- `examples/config/` is versioned and keeps maintained plus frozen config entrypoints.
- `experiments/`, `datasets/`, and `output/` are runtime or artifact workspaces and remain ignored by default.
- Large run outputs should be preserved through reports, archived manifests, or retained diagnostics under documented artifact paths rather than by checking whole experiment directories into the main repo.

## Training and evaluation

Current root/operator entrypoints:

- `train.py`
  - Main execution-layer, cooperative, and leader-layer training entrypoint.
- `world_model_train.py`
  - Thin world-model training compatibility entrypoint; implementation lives
    under `_world_model_train_impl/` and `python/world_model/`.
- `evaluate.py`
  - Historical root evaluator kept as a compatibility/operator surface.
- `tools/eval/*.py`
  - Maintained evaluation CLIs.
- `tools/runners/*.py`
  - Maintained contract and grouped regression runners.
- `scripts/README.md`
  - Small retained wrapper surface for workflows still worth keeping as shells.

Implementation for those entrypoints mostly lives in [python/README.md](python/README.md),
[gym_envs/README.md](gym_envs/README.md), and the C++ runtime/binding layers
under [src/README.md](src/README.md).

Example training entry:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python train.py \
  --scenario scenarios/combined/takeoff_to_landing_c2_task_only_train_v1.json \
  --train_config examples/config/training/frozen/leader_task_only_retrain_smoke_v1.json \
  --run_name local_smoke \
  --output_base /tmp/cmo_smoke
```

Example policy evaluation:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python tools/eval/policy_execution_eval.py \
  --mode single \
  --scenario scenarios/combined/takeoff_to_landing_continuous_eval_v1.json \
  --train_config examples/config/training/frozen/execution/p5_continuous_retrain_v1.json \
  --model path/to/model.zip \
  --episodes 8
```

## Diagnostics and Regression

Contract runner example:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/chain/loader_command_chain_takeoff_to_landing.json
```

Typical pytest groups:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q \
  tests/runtime \
  tests/world_batch \
  tests/architecture
```

Diagnostic and benchmark scripts are centered under
[tools/diagnostics](tools/diagnostics).

## Current Reference Documents

- [docs/operations/reference/engine_capabilities.md](docs/operations/reference/engine_capabilities.md)
- [docs/operations/reference/physics_engine_inventory.md](docs/operations/reference/physics_engine_inventory.md)
- [docs/operations/reference/src_layer_map.md](docs/operations/reference/src_layer_map.md)
- [docs/reference_artifacts.md](docs/reference_artifacts.md)

## Planning And Open Issues

Unpromoted plans and unresolved gaps now live under their content owners. The
HMoE design direction is at
[docs/learning/work/issues/hierarchical_moe_execution_policy.md](docs/learning/work/issues/hierarchical_moe_execution_policy.md);
other routes start from the [documentation index](docs/README.md).

## License

Project code and maintained documentation are licensed under the
[Apache License 2.0](LICENSE).

Third-party assets and bundled third-party files keep their own licenses. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the current local notice
inventory.

## Working Conventions

- prefer `.venv` for repository-local validation
- prefer `tools/maintenance/cmo_env.sh` for maintained Linux/macOS shell workflows
- prefer `tools/maintenance/cmo_env.ps1` for maintained Windows/PowerShell workflows
- prefer repo-relative scenario paths
- keep new training configs in explicit subdirectories
- do not treat GPU helpers as canonical world-step truth without a dedicated freeze
- add README files when introducing new architectural directories
