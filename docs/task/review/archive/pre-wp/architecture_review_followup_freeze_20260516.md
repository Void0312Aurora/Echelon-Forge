<!-- Machine-translated draft generated on 2026-05-18 from docs/task/review/architecture_review_followup_freeze_20260516.zh.md. Review before treating this file as authoritative. -->

# Architecture Review Follow-up Freeze Plan

Status: `2026-05-16` Frozen Execution Version.

Related Documents:

- [Project Structure and Architecture Design Review Report](architecture_review_20260516.zh.md)
- [Code Layer Map](../../../manual/src_layer_map.md)
- [src Layer Boundaries](../../../../src/README.md)
- [src Layer Refactoring Freeze Record](../../../plan/archive/src_layered_refactor_freeze.zh.md)

Document Positioning:

- This document consolidates "reasonable suggestions" from the architecture review into an actionable follow-up task list.
- It does not restate the full review; only genuinely adopted or partially adopted items suitable for continued progress are frozen.
- This document does not authorize directory renames, destructive rewrites of the `SimulationKernel` public API, complete CMake target splits, or dependency manager migration.

Verification Guidelines:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_env_summary
```

If subsequent work touches the Python / nanobind / runtime mainline, use by default:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q
```

If it touches C++ / binding / CI related scripts, at least one additional run should be:

```bash
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j4
```

## 1. Review Conclusions Translated to Execution Scope

### 1.1 Clearly Adopted in This Round

1. Add minimal CI automation.
2. Continue consolidating the workspace environment entry point, adding explicit validation capability on top of `cmo_env.sh`.
3. Clarify and fix the version policy and `.gitignore`/README conflict in `scenarios/`.

### 1.2 Partially Adopted in This Round, But Not as First Batch Execution

1. The entry point bloat issue for `train.py` / `world_model_train.py` is valid.
2. The direction of splitting CMake source groups into independent targets is valid.
3. The issue of an overly wide `SimulationKernel` public surface is valid.
4. `FetchContent` dependency governance needs strengthening.
5. Directory naming ambiguity needs future resolution.

These items do not negate the direction, but should not be mixed with the first batch of follow-ups.

### 1.3 Clearly Deferred in This Round

1. `src/interfaces/python -> src/bindings/python`
2. `src/gpu -> src/accelerators/gpu`
3. Directly introducing `vcpkg` / `Conan`
4. Destructive directory rename
5. One-time split of `SimulationKernel` into multiple public interface classes

## 2. Freeze Scope

This document freezes only four work packages:

1. `WP-A`: Minimal CI smoke baseline
2. `WP-B`: `cmo_env.sh` validation capability and documentation consolidation
3. `WP-C`: `scenarios/` version policy clarification and repository rule alignment
4. `WP-D`: First-stage entry point slimming for `train.py` and minimal implementation freeze

This document explicitly does not cover:

1. Full split of `world_model_train.py`
2. Complete CMake multi-target split
3. `SimulationKernel` API separation
4. Rename of `src/components/systems` / `src/systems/systems` / `src/core/engine`
5. GPU/exact runtime mainline expansion

## 3. Overall Strategy

Execution order is fixed as follows:

1. First, complete the "verification infrastructure", i.e., `WP-A` and `WP-B`.
2. Then handle "repository rule conflicts", i.e., `WP-C`.
3. Finally, start the first-stage entry point slimming for `train.py`, i.e., `WP-D`.

Reason:

1. CI and environment verification are the foundation for any subsequent structural work to proceed stably.
2. `scenarios/` currently has a conflict between documentation and ignore rules; not clarifying it first will pollute the boundaries of subsequent tasks.
3. While splitting `train.py` is reasonable, the regression cost is high without a CI/environment baseline.

## 4. Frozen Work Packages

### WP-A: Minimal CI Smoke Baseline

Objective:

- Establish the first automated quality gate for the main repository.
- Only cover CPU mainline, bindings build, and a small set of core tests.

Freeze scope:

- Add a minimal CI workflow under `.github/workflows/`
- Allow the addition of a very small number of CI bootstrap helpers if necessary
- Allow updates to the local reproduction instructions in [README.md](../../../../README.md)

Recommended first batch verification set:

1. `cmake --build build-workshop --target ef_core ef_py -j4`
2. `tests/architecture/runtime_facade`
3. `tests/architecture/build/test_cmake_target_readiness.py`
4. `tests/runtime/core/test_env_config.py`
5. `tests/runtime/facade/test_runtime_facade.py`
6. `tests/world_batch/test_world_batch_runtime.py`

Explicitly not to do:

1. Do not introduce CUDA matrices in the first batch of CI.
2. Do not put cooperative/HMoE long-running regressions into the first workflow.
3. Do not require the first batch of CI to cover all optional Python dependency paths.

Acceptance criteria:

1. A runnable minimal workflow exists at the repository root.
2. The README contains equivalent local reproduction commands.
3. The workflow only depends on the current mainline build and test entry points, without inventing additional bypass scripts.

Current execution record:

1. [ci-smoke.yml](../../../../.github/workflows/ci-smoke.yml) has been added.
2. The workflow currently covers:
   - `.venv` initialization
   - `cmake -S . -B build-workshop`
   - `cmake --build build-workshop --target ef_core ef_py`
   - `bash tools/maintenance/cmo_env.sh validate`
   - Core smoke pytest set
3. Local reproduction commands corresponding to the workflow have been added to [README.md](../../../../README.md).
4. Local equivalent smoke verification completed:
   - `source tools/maintenance/cmo_env.sh`
   - `cmo_env_validate`
   - `cmo_python -m pytest -q tests/architecture/runtime_facade tests/architecture/build/test_cmake_target_readiness.py tests/runtime/core/test_env_config.py tests/runtime/facade/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py`
   - Current result: `42 passed`

### WP-B: `cmo_env.sh` Validation Capability and Documentation Consolidation

Objective:

- Add explicit validation capability to the existing [tools/maintenance/cmo_env.sh](../../../../tools/maintenance/cmo_env.sh).
- Further consolidate scattered handwritten examples for `.venv` / `CMO_BUILD_DIR` / `PYTHONPATH`.

Freeze scope:

- [tools/maintenance/cmo_env.sh](../../../../tools/maintenance/cmo_env.sh)
- [tools/maintenance/README.md](../../../../tools/maintenance/README.md)
- [README.md](../../../../README.md)
- [tools/README.md](../../../../tools/README.md)
- [tests/README.md](../../../../tests/README.md)

Explicitly not to do:

1. Do not introduce a complex environment manager at this stage.
2. Do not rewrite all historical archived documents just to unify examples.
3. Do not change the behavior of training/evaluation code itself.

Acceptance criteria:

1. `cmo_env.sh` provides explicit validation capability that can distinguish common problems such as "missing `.venv`", "missing build", "missing `ef_py` artifacts".
2. Mainline README and maintenance README will not add new handwritten environment detection logic examples.
3. Shell workflows preferentially reuse the unified entry point instead of continuing to copy build directory detection code.

Current execution record:

1. Explicit `validate`/`summary`/`python` script modes have been added to [tools/maintenance/cmo_env.sh](../../../../tools/maintenance/cmo_env.sh).
2. `validate` can now distinguish the following common failures:
   - Missing `.venv/bin/python`
   - Missing a usable build directory
   - Build directory exists but lacks `ef_py` artifacts
3. Mainline training, evaluation, contract, and pytest examples in [README.md](../../../../README.md) have been consolidated to `source tools/maintenance/cmo_env.sh` + `cmo_env_validate` + `cmo_python ...`.
4. [tools/maintenance/README.md](../../../../tools/maintenance/README.md) has been updated to record the unified entry point and script modes.
5. The environment verification step in [.github/workflows/ci-smoke.yml](../../../../.github/workflows/ci-smoke.yml) has been switched to `bash tools/maintenance/cmo_env.sh validate`.

### WP-C: `scenarios/` Version Policy Clarification and Repository Rule Alignment

Objective:

- Resolve the conflict between `.gitignore` and README regarding the positioning of `scenarios/`.
- Clarify the differentiated strategies for `scenarios/`, `experiments/`, `datasets/`, `output/`.

Freeze scope:

- [.gitignore](../../../../.gitignore)
- [README.md](../../../../README.md)
- [scenarios/README.md](../../../../scenarios/README.md)
- Allow the addition of a brief artifact / scenario policy documentation if necessary

Default direction:

1. `scenarios/` as the mainline input should be consistent with the current documentation and traceable through version history.
2. `experiments/`, `datasets/`, `output/` remain ignored unless a separate plan is initiated.

Explicitly not to do:

1. Do not directly include training checkpoints and large-volume artifacts in the main repository.
2. Do not resolve all artifact management issues simultaneously at this stage.
3. Do not force Git LFS as a prerequisite.

Acceptance criteria:

1. README, `.gitignore`, and the role description of `scenarios/` are consistent with each other.
2. The repository has a clear statement on "what is mainline input" and "what is runtime artifact".
3. If the decision is to not cancel ignore, an external version strategy must be explicitly documented; the state "documentation says maintained, repository ignores" must not persist.

Current execution record:

1. [.gitignore](../../../../.gitignore) has been updated: removed ignore for `scenarios/`, retained `experiments/`, `datasets/`, `output/` as default ignored runtime artifact directories.
2. A repository retention policy summary has been added to [README.md](../../../../README.md), clarifying:
   - `scenarios/` and `examples/config/` are version-controlled mainline inputs.
   - `experiments/`, `datasets/`, `output/` are runtime/artifact workspaces.
3. [scenarios/README.md](../../../../scenarios/README.md) has been updated to explicitly define `scenarios/` as a git-tracked canonical input surface, and to add a retention boundary statement: "scenarios intended only for a single experiment should not be promoted to mainline scenarios".
4. [docs/reference_artifacts.md](../../../reference_artifacts.md) has been updated with boundary explanations between repo inputs and artifact workspaces to prevent future misidentification of runtime directories as long-term sources.

### WP-D: First-Stage Entry Point Slimming for `train.py`

Objective:

- First-stage slimming for [train.py](../../../../train.py).
- Separate CLI parsing/dispatching from the core logic of the training main loop and environment construction.

Freeze scope:

- [train.py](../../../../train.py)
- Allow the addition of `python/training/` or an equivalent mainline subpackage
- Allow updates to training entry point related README and minimal smoke tests

Explicitly not to do:

1. Do not rewrite [world_model_train.py](../../../../world_model_train.py) simultaneously at this stage.
2. Do not change the existing CLI parameter surface of `train.py`.
3. Do not fully refactor `python/rl/`, `gym_envs/`, callbacks through this effort.

Acceptance criteria:

1. `train.py` still maintains the existing CLI entry point and major parameter compatibility.
2. The new training subdomain takes clear responsibility for bootstrap/orchestration, rather than forming another large flat file.
3. At least one focused smoke test is added to prove that the original entry point can still complete parameter parsing and training bootstrap.

Stop condition:

- If the split starts to require large-scale simultaneous rewrites of `world_model_train.py`, `gym_envs/`, or cooperative runtime, stop and start a separate plan.

Current execution record:

1. A new subdomain [python/training/](../../../../python/training/README.md) has been added to host the first-stage entry point slimming of `train.py`.
2. The following entry point responsibilities of `train.py` have been moved down to the new subdomain:
   - CLI argument table
   - Scenario / train_config path validation
   - `agent_layer` parsing and leader entry class loading
   - Experiment directory, resume / interrupted checkpoint, backup, lock file handling
   - Seed and PyTorch runtime bootstrap
   - Unified runtime summary printing and execution visual rollout memory warning before training start
3. [train.py](../../../../train.py) now retains:
   - vec-env/backend construction
   - SB3/AdaptiveKLPPO model creation and checkpoint initialization
   - callback / probe / learn / save main loop
4. A focused smoke test [tests/training/test_train_bootstrap.py](../../../../tests/training/test_train_bootstrap.py) has been added.
5. Validated that `train.py` CLI surface compatibility remains usable:
   - `cmo_python train.py --help`
   - `cmo_python -m pytest -q tests/training/test_train_bootstrap.py`
   - `cmo_python -m pytest -q tests/training/test_train_entry_cooperative.py`

## 5. Follow-ups Not Executed Within This Document

The following items are retained as future candidates and are not within the implementation scope of this plan:

1. CMake multi-target progressive split
2. Extraction of a narrower `SimulationKernel` interface
3. Rename of directory naming ambiguities
4. Migrate from `FetchContent` to a package manager
5. Large file split of `world_model_train.py`

If these items are to proceed further, a new frozen task list must be initiated separately.
