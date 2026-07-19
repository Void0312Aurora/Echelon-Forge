# Tests README

`tests/` is being consolidated around a small set of reusable runners plus JSON contracts.

## Goals

- Reduce one-off Python regression scripts.
- Keep scenario/test intent explicit in data instead of re-encoding bootstrap logic in every file.
- Make it easier to batch-run related regressions from CI or local shells.

## Current Structure

- `runtime/`
  - Runtime-contract tests grouped by capability domain and shared surface
    under `air_combat/`, `bindings/`, `core/`, `engagement/`, `execution/`,
    `facade/`, `ground/`, `link/`, `mission/`, `multi_agent/`, `naval/`, and
    `navigation/`.
  - `air_combat/weapon_guidance_realism/` intentionally uses five
    `test_*.py` unittest wrappers around capability mixins. See
    `runtime/air_combat/weapon_guidance_realism/README.md` before changing its
    collection pattern or promoting it into a suite.
- `architecture/`
  - Source/documentation guardrails and governance checks that intentionally
    stay separate from runtime behavior tests.
  - One-level semantic subfolders keep guard ownership visible:
    `build_system/`, `causal_runtime/`, `command_tasking/`,
    `compatibility_quarantine/`, `damage_model/`, `governance/`, `ground/`,
    `platform_spawn/`, `policy_execution/`, `runtime_facade/`,
    `runtime_profiles/`, `runtime_spine/`, and `structural_boundaries/`.
  - File names should describe the architectural invariant first. Historical
    work-package labels such as WP/A2 belong in test names, comments, or task
    docs only when they are needed for traceability; residual/source labels
    such as `RES`, `TP21`, and `BECO` may remain when they are part of the
    guarded domain contract.
- `eval/`
  - Maintained evaluation CLI contracts for policy-loading, runtime-entry, and
    domain baseline probes.
- `training/`
  - Training bootstrap/CLI contracts, active-entry gates, diagnostics-callback
    contracts, and deterministic fault-localization probes.
- `policy/`
  - Policy routing, execution-policy surface, auxiliary training updates,
    event-timing labels, grouped-stopping loss, bootstrap, and control-config
    regression tests.
- `world_batch/`
  - Batch kernel and vec-env adapter tests.
- `scenario/`
  - Scenario compiler, environment substrate/projection contracts, scenario
    generation contracts, and spatial-query tests.
- `leader/`
  - Leader tasking profile, command-field projection, phase-control, and
    runtime-control tests.
- `runners/`
  - Batch runners for grouped JSON contract suites.
- `support/`
  - Shared paths, maintenance CLI runners, manifest assertions, fakes, and fixtures.
- `contracts/`
  - Maintained JSON specs for contract-driven regressions, grouped by category.
  - Historical specs retained only for provenance belong under `archive/contracts/`, not this root.
- `archive/`
  - Historical test assets retained for provenance only.
  - These files are not active pytest or JSON contract coverage until moved back into a maintained test surface and added to the relevant matrix or suite.
- `suites/`
  - Advisory suite governance metadata, including the draft test-system matrix and focused/local suite manifests.
  - These files do not change CI wiring on their own.
- `diagnostics/`
  - Temporary exploratory diagnostics only.
  - Stable diagnostics-derived regressions belong in the owning capability
    domain, for example runtime, training, world-batch, scenario, leader,
    bindings, link, or contracts.
- `gpu/`
  - GPU runtime binding and CUDA integration regression tests. Aligned with `src/gpu/` and Python GPU bindings.
  - GPU tests are gated behind `EF_ENABLE_CUDA_EXPERIMENTS` by default; they should skip gracefully when CUDA is unavailable.
- `scenarios/`
  - Reusable scenario fixtures when inline JSON is not practical, for example imported prefab dependencies.

Standalone Python tests should now be the exception, not the default.

Manual one-off probes should not live at the top level of `tests/`.
If a file is primarily for human inspection rather than automated regression,
prefer `tools/diagnostics/` for maintained diagnostics or `tools/archive/` for
legacy/manual probes kept only for reference.

When a standalone test is needed, prefer:

- one focused file per runtime or adapter boundary
- small internal support modules under `tests/` for shared fakes/builders
- direct package imports instead of single-file compatibility shims

## Implementation Entry Points

- Contract execution logic now lives in [python/testing/contracts/](../python/testing/contracts).
- Scenario-side bootstrap logic used by tests now lives in `python/scenario/compiler/` and `python/scenario/runtime/`.
- Raw batch scenario setup diagnostics wrappers have been removed; tests should import maintained setup helpers from `python/scenario/runtime/` directly.

## Contract Types

- `loader_command_chain`
  - Validates `TaskOrder -> LeaderIntent -> PilotReport -> MissionCommand` initialization and kernel sync.
- `route_generator`
  - Validates generated waypoint routes, geometry, reachability budget, mode cycling, and world-yaw behavior.
- `unit_regression`
  - Validates pure-Python controller/config/loader/wrapper handoff logic without needing full scenario stepping.
  - Also hosts parameterized leader-task generalization checks that mutate C2 task inputs and validate emitted mission-command behavior.

Contract execution lives in [python/testing/contracts/](../python/testing/contracts).

## Contract Batch Failure Policy

`tests/runners/test_contract_batches.py` currently resolves batch groups by checked-in path globs. If a selected glob is empty or any selected contract fails, the batch exits non-zero. In other words, the current batch runner is an operational hard-fail mechanism for the selected files.

That execution behavior is separate from the intended semantic tier of a contract. Tiers such as `gating`, `frozen`, `supplemental`, `diagnostic`, and `archive` still need a metadata or manifest layer before the runner can enforce different failure policies. Until that layer exists, path location and README text are documentation only; they do not soften a selected batch failure.

For `unit/kernel` contracts, keep a practical split between stable gate checks and diagnostic or supplemental realism scans. The `sim_kernel` batch currently globs all `tests/contracts/unit/kernel/*.json`, so diagnostic scans selected by that glob still hard-fail operationally. Do not reinterpret that as a calibrated acceptance decision; promote a scan to a gate only through explicit metadata/manifest ownership.

## How To Run

Run one contract directly:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/chain/loader_command_chain_takeoff_to_landing.json
```

Run multiple contracts in one call:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py --spec \
  tests/contracts/route_generator/route_generator_v1.json \
  tests/contracts/route_generator/route_generator_waypoint_modes.json
```

Run the maintained contract smoke suite:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py --suite tests/smoke/ci_contract_suite.json
```

Run a batch runner:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_contract_batches.py --group chain --group route_generator

cmo_python tools/runners/run_contract_batches.py --group unit --group same_process

cmo_python tools/runners/run_contract_batches.py --group sim_kernel

cmo_python tools/runners/run_contract_batches.py --default-group sim_kernel
```

The `sim_kernel` default group is a convenience wrapper around `tests/contracts/unit/kernel/*.json`; it is not yet a semantic manifest that distinguishes gate, supplemental, and diagnostic contracts.

Run the maintained repository smoke suite:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
```

Pytest suite manifests may list directories, files, or pytest node IDs such as
`tests/architecture/runtime_facade/test_runtime_escape_hatches.py::test_runtime_facade_escape_hatch_is_documented`.
Use node IDs when only a smoke-safe subset of a broad guard file should gate CI.
CI smoke should prefer explicit files or node IDs over directory entries so new
tests are promoted intentionally.

Suite tiers:

- `smoke`
  - Fast, high-signal checks allowed to gate CI.
- `focused`
  - Small domain-oriented suites for local pre-merge checks and targeted ownership review.
- `local`
  - Developer-run suites that may be broader or more environment-sensitive than focused suites.
- `manual`
  - Human-invoked checks, diagnostics, or workflows that need judgment or special setup.
- `nightly`
  - Candidate long-running or broad regression coverage for scheduled automation after stabilization.

`tests/suites/` previously hosted advisory governance matrices
(`test_system_matrix.json`, `contract_system_matrix.json`) and a draft
`focused_runtime_suite.json`. These have been removed: they were not wired into
any runner or CI step, and their cross-file consistency was enforced by
meta-tests rather than behavior. Current CI runs the maintained pytest smoke
suite, C++ CTest smoke target, and the maintained JSON contract smoke suite.

If a smoke path is moved during a refactor, update
`tests/smoke/ci_smoke_suite.json` first. CI and top-level documentation should
reference the suite runner instead of duplicating individual test-file paths.

## Test System Audit

Use the audit runner before broad test-suite cleanup or promotion work:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/audit_test_system.py --format markdown --limit 30
```

The audit excludes `archive`/`Archive` paths and reports active pytest files,
JSON contracts, smoke-suite membership, hidden mixin tests, source-scan guards,
and oversized or literal-heavy tests. Treat the report as triage input:

- `oversized_file`, `oversized_test_item`, `assert_heavy`, and `literal_heavy`
  usually point to snapshot-style tests that should be converted to smaller
  invariant checks or data contracts.
- `source_scan_guard` belongs in architecture or governance tiers unless a
  small node-ID smoke subset is explicitly promoted.
- `hidden_mixin_tests` and `mixin_wrapper_file` are allowed only when the wrapper
  makes collection clearer than direct test modules; otherwise prefer semantic
  `test_*.py` files with local helpers.
  `tests/runtime/air_combat/weapon_guidance_realism/` is the current documented
  exception and remains local/focused until its package-level run is green.
- `not_smoke_gated` is not automatically a defect. It means the file should be
  deliberately assigned to smoke, focused, local, manual, or contract coverage
  before being treated as maintained gate evidence.

## Architecture Suite Governance

Architecture tests are split by execution intent, not just by directory name.
Only cheap, high-signal guardrails should enter `tests/smoke/ci_smoke_suite.json`.
Broad source scans, AST sweeps, release-package generation, retained-artifact
checks, and source-admission workflows belong in `focused`, `local`, or
`manual` tiers unless they are split into a small manifest-only smoke subset.

When promoting an architecture guard, add the file or node ID to
`tests/smoke/ci_smoke_suite.json`. The suite runner treats missing paths as
hard failures, so moved architecture files must keep the manifest in lockstep.
For node ID entries, the runner checks the base file path before handing the
full node ID to pytest.

The removed `UniversalEnv` raw-constructor surface is tracked by
`tests/architecture/fixtures/universal_env_runtime_compatibility_callers_20260612.json`
and guarded by
`tests/architecture/runtime_facade/test_universal_env_compatibility_caller_inventory.py`.
The expected active count is zero. New `runtime_compatibility_enabled=True` call
sites must not be introduced; use a maintained runtime/facade path instead.

## Dependency Notes

- `gymnasium` is optional in this workspace.
- Active maintained contract batches should avoid raw `UniversalEnv` construction. Historical raw-env specs were retired from the tree during test-system consolidation and remain recoverable from git history.
- Kernel-only contracts such as `loader_command_chain` and route-generator checks can run without `gymnasium`.

## Authoring Guidance

Prefer a JSON contract when the regression is mainly:

- one scenario
- one reset/step/check flow
- deterministic numeric or structural assertions
- repeated `repo_root/build/PYTHONPATH` bootstrap

Prefer a standalone Python test only when you truly need:

- custom iterative control flow
- heavy monkeypatching
- nontrivial mocking that cannot be captured by a small dummy contract harness
- richer diagnostics than a contract can reasonably encode

## Capability-Oriented Test File Standard

Test files are capability or contract containers, not receipts for subprojects,
work packages, stages, or one-time review processes. A new test file should
exist only when it owns a stable functional surface or a materially different
execution model.

Prefer one semantic file that covers a capability with multiple scenarios,
using test functions, parameterization, fixtures, and shared helpers inside the
file. Do not create a new file merely because a task, residual item, stage,
candidate, or archived work package needed an extra checkpoint.

A proposed standalone file should pass at least one of these tests:

- It guards a new capability boundary that does not naturally fit an existing
  file.
- It needs a different runner, environment tier, generated artifact lifecycle,
  or fixture shape from the existing capability files.
- Splitting it prevents an existing file from becoming a broad mixed-surface
  guard with unrelated setup or failure semantics.

Otherwise, add the scenario to the existing capability file. Small files with
fewer than three to five tests should be treated as merge candidates unless
they have a distinct execution tier, expensive setup, or intentionally isolated
failure policy.

Consolidate files when they share most of their imports, tool entry points,
artifact roots, retained-manifest logic, fail-closed semantics, or CI/local
suite tier. If a capability file grows too large, split it by capability
sub-surface, not by project code name or task number.

Historical identifiers such as `A2`, `WP`, `RES`, `TP21`, `BEC-O`, and
`Stage B/C` belong in test names, parameter IDs, comments, fixtures, or task
docs only when traceability requires them. Filenames should stay semantic:
prefer forms such as
`test_<capability>_<contract|governance|admission|guardrails|validation|artifacts>.py`.

Promotion into CI or focused suites should happen through suite manifests or
node IDs. Do not create a new physical file just to make promotion or exclusion
easier.

## Naming Conventions

- `tests/contracts/route_generator/*.json`
  - Route generation and route geometry regressions.
- `tests/contracts/chain/*.json`
  - Command-chain and kernel-sync regressions that exercise maintained loader/runtime wiring.
- `tests/contracts/unit/**/*.json`
  - Pure logic, controller, loader, and config regressions.
- `tests/contracts/unit/comm/*.json`
  - Command-link, task-order, leader-intent, and leader-phase-manager regressions.
  - Includes common-core baseline contracts plus compatibility air-specific comm/tasking contracts.
- `tests/contracts/unit/kernel/*.json`
  - Kernel-driven flight regressions that step `SimulationKernel` directly with scripted pilot inputs.
  - Also hosts simulation guardrails for repeatability, sign consistency, coarse physical plausibility, and small parameter-scan realism checks.
  - Treat stable guardrails as gate candidates and compact realism scans as supplemental or diagnostic until metadata/manifest failure policy says otherwise.
- `tests/contracts/unit/env/*.json`
  - Environment helper and leader-training-env contracts that validate env-side setup, randomization, scripted/frozen model guards, and phase/curriculum behavior without living under a full scenario env tree.
- `tests/contracts/unit/ground/*.json`
  - Ground profile, common-core, task-order, and support-relationship contracts for the early ground tasking/bootstrap lane.
- `tests/contracts/unit/scenarios/*.json`
  - Scenario-template and geometry regressions that validate static JSON content without stepping an env.
- `tests/contracts/unit/training/*.json`
  - Training/bootstrap regressions such as safe action-bias initialization.
- `tests/contracts/unit/wrappers/*.json`
  - Scripted wrapper mode selection, controller handoff, and residual-cap regressions.
- `tests/contracts/unit/world_model/*.json`
  - Replay-buffer and world-model dataset regressions.

## Current Contract Folders

- `tests/contracts/chain/`
  - Command-chain and kernel-sync contracts.
- `tests/contracts/route_generator/`
  - Route generation geometry and budget contracts.
- `tests/contracts/unit/controllers/`
  - Scripted controller logic contracts.
- `tests/contracts/unit/comm/`
  - C2/tasking/command-link contracts for task orders, leader intent, pilot reports, and leader phase transitions.
  - Common-core baselines now live here alongside legacy air-specific contracts while the directory is being split into common-first families.
- `tests/contracts/unit/config/`
  - Config resolution contracts.
- `tests/contracts/unit/env/`
  - Environment-helper and leader-training-env unit contracts.
- `tests/contracts/unit/ground/`
  - Ground-specific profile/tasking/common-core contracts for the early ground lane.
- `tests/contracts/unit/kernel/`
  - Direct `SimulationKernel` flight regressions for takeoff, ground roll, and stable-flight control laws.
  - Also hosts core simulation guardrails for repeatability, sign consistency, coarse physical plausibility checks, and compact realism parameter scans.
  - Current batch execution does not distinguish gate and diagnostic semantics; selected `sim_kernel` contracts still hard-fail until a metadata/manifest layer exists.
- `tests/contracts/unit/naval/`
  - Naval-specific unit/runtime contracts that validate ship/domain semantics without relying on a separate env contract tree.
- `tests/contracts/unit/scenarios/`
  - Static scenario/template geometry checks that validate mission JSON assumptions.
- `tests/contracts/unit/training/`
  - Training-time helper contracts that do not need full scenario stepping.
  - Includes leader-task parameter generalization contracts that vary CAP-task inputs and check mission-code reasonableness.
- `tests/contracts/unit/wrappers/`
  - Wrapper/controller handoff contracts driven by dummy observations and loader phases.
- `tests/contracts/unit/world_model/`
  - Replay/dataset contracts for offline or imitation-learning support code.
